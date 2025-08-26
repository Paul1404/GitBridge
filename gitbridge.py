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

    # Step 2: Clone/fetch Repo2 (just to validate access)
    ok, msg = clone_or_fetch(
        repo2_dir,
        settings.repo2.url,
        settings.repo2.auth,
        settings.repo2.user,
        settings.repo2.password,
        settings.repo2.ssh_key,
    )
    log.info(f"[Repo2] {msg}")

    # Step 3: Build authenticated URL for Repo2
    target_url = settings.repo2.url
    if settings.repo2.auth in ["pat", "password"] and settings.repo2.password:
        user = settings.repo2.user or "oauth2"
        target_url = target_url.replace("https://", f"https://{user}:{settings.repo2.password}@")
        masked_url = target_url.replace(settings.repo2.password, "******")
        log.info(f"[Mirror] Using authenticated target URL: {masked_url}")
    elif settings.repo2.auth == "ssh" and settings.repo2.ssh_key:
        log.info("[Mirror] Using SSH key for target remote")

    # Step 4: Add Repo2 as remote to Repo1 (with credentials)
    log.info("[Mirror] Adding target as remote to source")
    try:
        run_cmd(f"git remote remove target", cwd=repo1_dir)
    except Exception:
        pass  # ignore if it doesn't exist
    run_cmd(f"git remote add target {target_url}", cwd=repo1_dir, mask_output=True)

    # Step 5: Push all branches
    if force:
        push_cmd = "git push --mirror target"
    else:
        push_cmd = "git push --all target"

    log.info(f"[Mirror] Pushing branches (force={force}) with cmd: {push_cmd}")
    run_cmd(push_cmd, cwd=repo1_dir, mask_output=True)

    # Step 6: Push all tags
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