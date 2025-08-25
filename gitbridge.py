import typer
from settings import load_settings
from git_utils import clone_or_fetch
from logger import setup_logger

app = typer.Typer()
log = setup_logger()

@app.command()
def fetch():
    settings = load_settings()

    log.info(f"[Repo1] Fetching {settings.repo1.url}")
    ok, msg = clone_or_fetch("/data/repo1", settings.repo1.url)
    log.info(f"[Repo1] {msg}")

    log.info(f"[Repo2] Fetching {settings.repo2.url}")
    ok, msg = clone_or_fetch("/data/repo2", settings.repo2.url)
    log.info(f"[Repo2] {msg}")

if __name__ == "__main__":
    app()