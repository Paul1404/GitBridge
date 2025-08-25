import os
import shutil
import tempfile
import subprocess
from logger import setup_logger

log = setup_logger()


def run_git_command(cmd, cwd=None, env=None):
    log.info(f"[GIT] Running: {cmd} (cwd={cwd})")
    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True,
        cwd=cwd,
        env=env or os.environ.copy(),
    )
    if result.returncode == 0:
        if result.stdout.strip():
            log.info(f"[GIT] Success: {result.stdout.strip()}")
        return True, result.stdout.strip() or "Success"
    else:
        log.error(f"[GIT] Failed (exit {result.returncode}): {result.stderr.strip()}")
        return False, result.stderr.strip() or "Unknown error"


def clone_or_fetch(target_dir, url, auth_type="none", user=None, password=None, ssh_key=None):
    """
    Clone or fetch a repo into target_dir with support for SSH, PAT, password, or none.
    Returns: (ok: bool, msg: str)
    """

    # If repo already exists → fetch
    if os.path.isdir(os.path.join(target_dir, ".git")):
        log.info(f"[GIT] Repo already exists at {target_dir}, fetching updates")
        return run_git_command("git fetch --all --prune", cwd=target_dir)

    # Clean up if dir exists but not a git repo
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)

    # Handle SSH auth
    if auth_type == "ssh" and ssh_key:
        log.info("[Auth] Using SSH key for authentication")
        with tempfile.NamedTemporaryFile(delete=False) as key_file:
            key_file.write(ssh_key.encode())
            key_file.flush()
            os.chmod(key_file.name, 0o600)
            env = os.environ.copy()
            env["GIT_SSH_COMMAND"] = f"ssh -i {key_file.name} -o StrictHostKeyChecking=no"
            return run_git_command(f"git clone {url} {target_dir}", env=env)

    # Handle PAT/password auth
    elif auth_type in ["pat", "password"] and password:
        user = user or "oauth2"  # default for GitLab PATs
        safe_url = url.replace("https://", f"https://{user}:{password}@")
        masked_url = url.replace("https://", f"https://{user}:******@")
        log.info(f"[Auth] Using HTTPS with credentials: {masked_url}")
        return run_git_command(f"git clone {safe_url} {target_dir}")

    # Handle no auth
    else:
        log.info("[Auth] Using no authentication")
        return run_git_command(f"git clone {url} {target_dir}")