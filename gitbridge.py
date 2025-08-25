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


def run_cmd(cmd, cwd=None, env=None):
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        text=True,
        capture_output=True,
        env=env or os.environ.copy(),
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


@app.command()
def fetch():
    """Fetch/clone both repos into /data/repo1 and /data/repo2"""
    settings = load_settings()

    log.info(f"[Repo1] Fetching {settings.repo1.url}")
    ok, msg = clone_or_fetch("/data/repo1", settings.repo1.url)
    log.info(f"[Repo1] {msg}")

    log.info(f"[Repo2] Fetching {settings.repo2.url}")
    ok, msg = clone_or_fetch("/data/repo2", settings.repo2.url)
    log.info(f"[Repo2] {msg}")


@app.command()
def mirror(force: bool = typer.Option(False, "--force", help="Force push (overwrite target history)")):
    """Mirror Repo1 (source) into Repo2 (target)"""
    settings = load_settings()

    repo1_dir = "/data/repo1"
    repo2_dir = "/data/repo2"

    log.info(f"[Repo1] Cloning source repo: {settings.repo1.url}")
    ok, msg = clone_or_fetch(repo1_dir, settings.repo1.url)
    log.info(f"[Repo1] {msg}")

    log.info(f"[Repo2] Cloning target repo: {settings.repo2.url}")
    ok, msg = clone_or_fetch(repo2_dir, settings.repo2.url)
    log.info(f"[Repo2] {msg}")

    log.info("[Mirror] Adding target as remote to source")
    code, out, err = run_cmd(f"git remote add target {settings.repo2.url}", cwd=repo1_dir)
    if code != 0 and "already exists" not in err:
        log.error(f"[Mirror] Failed to add remote: {err}")
        raise typer.Exit(code)

    push_flags = "--mirror" if force else "--all target"
    log.info(f"[Mirror] Pushing branches (force={force})")
    run_cmd(f"git push {push_flags}", cwd=repo1_dir)
    run_cmd("git push --tags target", cwd=repo1_dir)

    log.info("[Mirror] Repo1 successfully mirrored into Repo2")


@app.command()
def run():
    """Run GitBridge once or on a schedule"""
    mode = os.getenv("GITBRIDGE_MODE", "fetch")
    schedule_expr = os.getenv("GITBRIDGE_SCHEDULE")

    def job():
        log.info(f"Running GitBridge in {mode} mode")
        if mode == "mirror":
            mirror()
        else:
            fetch()

    if schedule_expr:
        log.info(f"Scheduling GitBridge with cron expression: {schedule_expr}")
        base_time = datetime.now()
        itr = croniter(schedule_expr, base_time)

        while True:
            next_time = itr.get_next(datetime)
            sleep_seconds = (next_time - datetime.now()).total_seconds()
            if sleep_seconds > 0:
                log.info(f"Next run at {next_time} (sleeping {int(sleep_seconds)}s)")
                time.sleep(sleep_seconds)
            job()
    else:
        job()


if __name__ == "__main__":
    app()