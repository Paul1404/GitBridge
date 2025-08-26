import typer
import os
import time
import subprocess
import traceback
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


def sanitize_output(text: str) -> str:
    """Mask secrets in command output/logs."""
    if not text:
        return ""
    # Mask common secret patterns
    for keyword in ["glpat-", "token", "key", "pass", "oauth2:" ]:
        if keyword.lower() in text.lower():
            text = text.replace(text, "[******]")
    return text


def run_cmd(cmd, cwd=None, env=None, mask_output=False):
    """Run a shell command with logging and error handling."""
    log.info(f"[CMD] START: {cmd} (cwd={cwd})")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        text=True,
        capture_output=True,
        env=env or os.environ.copy(),
    )

    stdout = sanitize_output(result.stdout.strip())
    stderr = sanitize_output(result.stderr.strip())

    if result.returncode == 0:
        log.info(f"[CMD] SUCCESS (exit=0): {cmd}")
        if stdout:
            log.info(f"[CMD][STDOUT]: {stdout}")
    else:
        if mask_output:
            stderr = "[masked]"
        log.error(f"[CMD] FAILED (exit={result.returncode}): {cmd}")
        if stdout:
            log.error(f"[CMD][STDOUT]: {stdout}")
        if stderr:
            log.error(f"[CMD][STDERR]: {stderr}")
        raise typer.Exit(result.returncode)

    return result.returncode, stdout, stderr


@app.command()
def fetch():
    """Fetch/clone both repos into /data/repo1 and /data/repo2"""
    settings = load_settings()

    log.info("[STEP] Fetching repositories")

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

    log.info("[STEP] Fetch completed successfully")


@app.command()
def mirror():
    """Mirror Repo1 (source) into Repo2 (target) with bare clone + force push"""
    settings = load_settings()

    repo1_dir = "/data/repo1"

    log.info("[STEP] Starting mirror operation (bare clone + force push)")
    log.info(f"[Mirror] Source repo: {settings.repo1.url}")
    log.info(f"[Mirror] Target repo: {settings.repo2.url}")

    try:
        # Step 1: Ensure /data/repo1 is a bare clone of source
        if os.path.exists(repo1_dir):
            log.info(f"[Mirror] Removing existing repo1 at {repo1_dir}")
            subprocess.run(f"rm -rf {repo1_dir}", shell=True, check=False)

        log.info(f"[Mirror] Cloning source as bare repo into {repo1_dir}")
        run_cmd(
            f"git clone --bare {settings.repo1.url} {repo1_dir}",
            mask_output=True,
        )

        # Step 2: Build authenticated URL for Repo2
        target_url = settings.repo2.url
        if settings.repo2.auth in ["pat", "password"] and settings.repo2.password:
            user = settings.repo2.user or "oauth2"
            target_url = target_url.replace(
                "https://", f"https://{user}:{settings.repo2.password}@"
            )
            masked_url = target_url.replace(settings.repo2.password, "******")
            log.info(f"[Mirror] Using authenticated target URL: {masked_url}")
        elif settings.repo2.auth == "ssh" and settings.repo2.ssh_key:
            log.info("[Mirror] Using SSH key for target remote")

        # Step 3: Add target remote
        log.info("[Mirror] Adding target remote to bare repo")
        run_cmd(f"git remote add target {target_url}", cwd=repo1_dir, mask_output=True)

        # Step 4: Force push all branches and tags
        log.info("[Mirror] Force pushing all branches")
        run_cmd("git push --all target --force", cwd=repo1_dir, mask_output=False)

        log.info("[Mirror] Force pushing all tags")
        run_cmd("git push --tags target --force", cwd=repo1_dir, mask_output=False)

        log.info("[STEP] Mirror operation completed successfully (bare clone + force overwrite)")

    except Exception as e:
        log.error(f"[ERROR] Mirror operation failed: {e}")
        log.error(traceback.format_exc())
        raise typer.Exit(1)


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
            log.error(traceback.format_exc())
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
                    log.info(
                        f"[Scheduler] Next run at {next_time} "
                        f"(sleeping {int(sleep_seconds)}s)"
                    )
                    time.sleep(sleep_seconds)
                job()
            except Exception as e:
                log.error(f"[Scheduler] Exception in loop: {e}")
                log.error(traceback.format_exc())
                time.sleep(60)  # backoff before retry
    else:
        job()


if __name__ == "__main__":
    app()