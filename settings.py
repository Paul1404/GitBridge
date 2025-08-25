from pydantic import BaseModel
import os

class RepoConfig(BaseModel):
    url: str
    auth: str = "none"
    user: str | None = None
    password: str | None = None
    ssh_key: str | None = None

class Settings(BaseModel):
    repo1: RepoConfig
    repo2: RepoConfig
    log_level: str = "INFO"

def load_settings() -> Settings:
    return Settings(
        repo1=RepoConfig(
            url=os.getenv("GITBRIDGE_REPO1_URL", ""),
            auth=os.getenv("GITBRIDGE_REPO1_AUTH", "none"),
            user=os.getenv("GITBRIDGE_REPO1_USER"),
            password=os.getenv("GITBRIDGE_REPO1_PASS"),
            ssh_key=os.getenv("GITBRIDGE_REPO1_SSH_KEY"),
        ),
        repo2=RepoConfig(
            url=os.getenv("GITBRIDGE_REPO2_URL", ""),
            auth=os.getenv("GITBRIDGE_REPO2_AUTH", "none"),
            user=os.getenv("GITBRIDGE_REPO2_USER"),
            password=os.getenv("GITBRIDGE_REPO2_PASS"),
            ssh_key=os.getenv("GITBRIDGE_REPO2_SSH_KEY"),
        ),
        log_level=os.getenv("GITBRIDGE_LOG_LEVEL", "INFO"),
    )