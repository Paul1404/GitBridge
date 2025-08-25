import typer
import os
import subprocess
from settings import load_settings
from git_utils import clone_or_fetch
from logger import setup_logger

app = typer.Typer()
log = setup_logger()


def run_cmd(cmd, cwd=None, env=None):
    """Run a shell command and return (exit_code, stdout, stderr)."""
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
def mirror():
    """Mirror Repo1 (source) into Repo2 (target)"""
    settings = load_settings()

    repo1_dir = "/data/repo1"
    repo2_dir = "/data/repo2"

    # Step 1: Clone/fetch Repo1
    log.info(f"[Repo1] Cloning source repo: {settings.repo1.url}")
    ok, msg = clone_or_fetch(repo1_dir, settings.repo1.url)
    log.info(f"[Repo1] {msg}")

    # Step 2: Clone/fetch Repo2 (target)
    log.info(f"[Repo2] Cloning target repo: {settings.repo2.url}")
    ok, msg = clone_or_fetch(repo2_dir, settings.repo2.url)
    log.info(f"[Repo2] {msg}")

    # Step 3: Add Repo2 as remote to Repo1
    log.info("[Mirror] Adding target as remote to source")
    code, out, err = run_cmd(f"git remote add target {settings.repo2.url}", cwd=repo1_dir)
    if code != 0 and "already exists" not in err:
        log.error(f"[Mirror] Failed to add remote: {err}")
        raise typer.Exit(code)

    # Step 4: Push all branches
    log.info("[Mirror] Pushing all branches from source to target")
    code, out, err = run_cmd("git push --all target", cwd=repo1_dir)
    if code != 0:
        log.error(f"[Mirror] Failed to push branches: {err}")
        raise typer.Exit(code)

    # Step 5: Push all tags
    log.info("[Mirror] Pushing all tags from source to target")
    code, out, err = run_cmd("git push --tags target", cwd=repo1_dir)
    if code != 0:
        log.error(f"[Mirror] Failed to push tags: {err}")
        raise typer.Exit(code)

    log.info("[Mirror] Repo1 successfully mirrored into Repo2")


if __name__ == "__main__":
    app()