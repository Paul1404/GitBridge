import typer
import os
import time
import subprocess
from datetime import datetime
from croniter import croniter
from settings import load_settings
from git_utils import clone_or_fetch
from logger import setup_logger

app = typer.Typer()
log = setup_logger()


def mask_secret(value: str, keep_start: int = 4, keep_end: int = 2) -> str:
    """Mask sensitive values like PATs or passwords for logging."""
    if not value:
        return ""
    if len(value) <= (keep_start + keep_end):
        return "*" * len(value)
    return value[:keep_start] + "*" * (len(value) - (keep_start + keep_end)) + value[-keep_end:]


def run_cmd(cmd, cwd=None, env=None, mask_output=False):
    """Run a shell command with logging and error handling."""
    log.info(f"[CMD] Running: {cmd} (cwd={cwd})")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        text=True,
        capture_output=True,
        env=env or os.environ.copy(),
    )
    if result.returncode == 0:
        if result.stdout.strip():
            log.info(f"[CMD] Success: {result.stdout.strip()}")
    else:
        err = result.stderr.strip()
        if mask_output:
            err = "[masked]"
        log.error(f"[CMD] Failed (exit {result.returncode}): {err}")
        raise typer.Exit(result.returncode)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


@app.command()
def fetch():
    """Fetch/clone both repos into /data/repo1 and /data/repo2"""
    settings = load_settings()

    log.info(f"[Repo1] Fetching {settings.repo1.url}")
    ok, msg = clone_or_fetch(
        "/data/repo1",
        settings.repo1.url,
        settings.repo1.auth,
        settings.repo1.user,
        settings.repo1.password,
        settings.repo1.ssh_key,
    )
    log.info(f"[Repo1] {msg}")

    log.info(f"[Repo2] Fetching {settings.repo2.url}")
    ok, msg = clone_or_fetch(
        "/data/repo2",
        settings.repo2.url,
        settings.repo2.auth,
        settings.repo2.user,
        settings.repo2.password,
        settings.repo2.ssh_key,
    )
    log.info(f"[Repo2] {msg}")


@app.command()
def mirror(force: bool = typer.Option(False, "--force", help="Force push (overwrite target history)")):
    """Mirror Repo1 (source) into Repo2 (target)"""
    settings = load_settings()

    repo1_dir = "/data/repo1"
    repo2_dir = "/data/repo2"

    log.info(f"[Mirror] Starting mirror operation (force={force})")
    log.info(f"[Mirror] Source repo: {settings.repo1.url}")
    log.info(f"[Mirror] Target repo: {settings.repo2.url}")

    # Step 1: Clone/fetch Repo1
    ok, msg = clone_or_fetch(
        repo1_dir,
        settings.repo1.url,
        settings.repo1.auth,
        settings.repo1.user,
        settings.repo1.password,
        settings.repo1.ssh_key,
    )
    log.info(f"[Repo1] {msg}")

    # Step 2: Clone/fetch Repo2
    ok, msg = clone_or_fetch(
        repo2_dir,
        settings.repo2.url,
        settings.repo2.auth,
        settings.repo2.user,
        settings.repo2.password,
        settings.repo2.ssh_key,
    )
    log.info(f"[Repo2] {msg}")

    # Step 3: Add Repo2 as remote to Repo1
    log.info("[Mirror] Adding target as remote to source")
    try:
        run_cmd(f"git remote add target {settings.repo2.url}", cwd=repo1_dir)
    except typer.Exit:
        log.warning("[Mirror] Remote already exists, continuing")

    # Step 4: Push all branches
    push_flags = "--mirror" if force else "--all target"
    log.info(f"[Mirror] Pushing branches (force={force}) with flags: {push_flags}")
    run_cmd(f"git push {push_flags}", cwd=repo1_dir, mask_output=True)

    # Step 5: Push all tags
    log.info("[Mirror] Pushing tags")
    run_cmd("git push --tags target", cwd=repo1_dir, mask_output=True)

    log.info("[Mirror] Repo1 successfully mirrored into Repo2")


@app.command()
def run():
    """Run GitBridge once or on a schedule"""
    mode = os.getenv("GITBRIDGE_MODE", "fetch")
    schedule_expr = os.getenv("GITBRIDGE_SCHEDULE")

    # Debug log environment (mask secrets)
    log.info("[Env] Loaded environment variables:")
    for key, val in os.environ.items():
        if "PASS" in key or "TOKEN" in key or "KEY" in key:
            log.info(f"  {key} = {mask_secret(val)}")
        elif key.startswith("GITBRIDGE_"):
            log.info(f"  {key} = {val}")

    def job():
        log.info(f"[Job] Running GitBridge in {mode} mode")
        try:
            if mode == "mirror":
                mirror()
            else:
                fetch()
        except Exception as e:
            log.error(f"[Job] Exception during {mode}: {e}")
            # Don’t crash scheduler, just log and continue

    if schedule_expr:
        log.info(f"[Scheduler] Using cron expression: {schedule_expr}")
        base_time = datetime.now()
        itr = croniter(schedule_expr, base_time)

        while True:
            try:
                next_time = itr.get_next(datetime)
                sleep_seconds = (next_time - datetime.now()).total_seconds()
                if sleep_seconds > 0:
                    log.info(f"[Scheduler] Next run at {next_time} (sleeping {int(sleep_seconds)}s)")
                    time.sleep(sleep_seconds)
                job()
            except Exception as e:
                log.error(f"[Scheduler] Exception in loop: {e}")
                time.sleep(60)  # backoff before retry
    else:
        job()


if __name__ == "__main__":
    app()