import os
from git import Repo

def clone_or_fetch(target_dir: str, url: str):
    if not url:
        return False, "No URL provided"

    if os.path.isdir(os.path.join(target_dir, ".git")):
        repo = Repo(target_dir)
        for remote in repo.remotes:
            remote.fetch(prune=True)
        return True, "Fetched updates"
    else:
        Repo.clone_from(url, target_dir)
        return True, "Cloned fresh"