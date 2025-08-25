# 📖 GitBridge

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/downloads/release/python-3120/)
[![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)](https://www.docker.com/)
[![Red Hat UBI](https://img.shields.io/badge/Red_Hat_UBI-9-red?logo=redhat)](https://www.redhat.com/en/technologies/containers/ubi)
[![License](https://img.shields.io/github/license/Paul1404/GitBridge?logo=github)](./LICENSE)
[![Quay](https://img.shields.io/badge/Quay.io-GitBridge-blue?logo=redhat)](https://quay.io/repository/scaling4840/gitbridge)
[![Latest Release](https://img.shields.io/github/v/release/Paul1404/GitBridge?logo=github)](https://github.com/Paul1404/GitBridge/releases)
[![SBOM](https://img.shields.io/badge/SBOM-Available-success?logo=dependabot)](https://github.com/Paul1404/GitBridge/releases/latest)

**GitBridge** is a containerized tool for working with two Git repositories.  
It supports:  

- **Fetch mode** → clone/fetch both repositories into `/data/repo1` and `/data/repo2`.  
- **Mirror mode** → treat **Repo1 as the source** and **push all branches and tags into Repo2**.  
- **Scheduled mode** → run fetch or mirror on a cron‑like schedule (`GITBRIDGE_SCHEDULE`).  

---

## 🚀 Features

- 🔑 Supports **SSH keys, PATs, passwords, or no auth**  
- 📦 Fetches/clones into `/data/repo1` and `/data/repo2`  
- 🔄 Mirror mode: push all branches + tags from Repo1 → Repo2  
- ⏰ Built‑in scheduler with **full cron expression support** (`0 2 * * *`)  
- 📝 Structured logging with **Rich**  
- ⚡ Multi‑arch images (x86_64 + ARM64) published to [Quay.io](https://quay.io/repository/scaling4840/gitbridge)  
- 📑 SBOMs (CycloneDX + SPDX) attached to every GitHub Release  

---

## 🛠️ Environment Variables

### Repo 1 (Source)
- `GITBRIDGE_REPO1_URL` → Git URL (required)  
- `GITBRIDGE_REPO1_AUTH` → `ssh|pat|password|none` (default: `none`)  
- `GITBRIDGE_REPO1_USER` → Username (if PAT/password)  
- `GITBRIDGE_REPO1_PASS` → Password or PAT  
- `GITBRIDGE_REPO1_SSH_KEY` → Private SSH key  

### Repo 2 (Target)
- `GITBRIDGE_REPO2_URL` → Git URL (required)  
- `GITBRIDGE_REPO2_AUTH` → `ssh|pat|password|none` (default: `none`)  
- `GITBRIDGE_REPO2_USER` → Username (if PAT/password)  
- `GITBRIDGE_REPO2_PASS` → Password or PAT  
- `GITBRIDGE_REPO2_SSH_KEY` → Private SSH key  

### Logging
- `GITBRIDGE_LOG_LEVEL` → `info|debug|warn|error` (default: `info`)  

### Scheduling
- `GITBRIDGE_MODE` → `fetch` or `mirror` (default: `fetch`)  
- `GITBRIDGE_SCHEDULE` → cron expression (e.g. `0 2 * * *` for daily at 2 AM).  
  - If unset → runs once and exits.  
  - If set → runs continuously on schedule.  

---

## 📦 Installation

Pull the latest image from Quay:

```bash
docker pull quay.io/scaling4840/gitbridge:latest
```

Or a specific version:

```bash
docker pull quay.io/scaling4840/gitbridge:v1.0.0
```

---

## ▶️ Usage

### Fetch Mode (default)

Clone/fetch both repos into `/data/repo1` and `/data/repo2`:

```bash
docker run --rm \
  -v $(pwd)/data:/data \
  -e GITBRIDGE_REPO1_URL=git@github.com:paul/repo1.git \
  -e GITBRIDGE_REPO2_URL=https://github.com/paul/repo2.git \
  quay.io/scaling4840/gitbridge:latest fetch
```

---

### Mirror Mode (Repo1 → Repo2)

Treat Repo1 as the **source** and push all branches + tags into Repo2:

```bash
docker run --rm \
  -v $(pwd)/data:/data \
  -e GITBRIDGE_REPO1_URL=git@github.com:paul/repo1.git \
  -e GITBRIDGE_REPO2_URL=https://github.com/paul/repo2.git \
  quay.io/scaling4840/gitbridge:latest mirror
```

---

### Scheduled Mode (with cron expression)

Run mirror every day at 2 AM:

```bash
docker run -d \
  -v $(pwd)/data:/data \
  -e GITBRIDGE_MODE=mirror \
  -e GITBRIDGE_REPO1_URL=git@github.com:paul/repo1.git \
  -e GITBRIDGE_REPO2_URL=https://github.com/paul/repo2.git \
  -e GITBRIDGE_SCHEDULE="0 2 * * *" \
  quay.io/scaling4840/gitbridge:latest run
```

---

### Docker Compose Example (Inline Environment Variables)

```yaml
version: "3.9"
services:
  gitbridge:
    image: quay.io/scaling4840/gitbridge:latest
    container_name: gitbridge
    volumes:
      - ./data:/data
    environment:
      # Source repo
      GITBRIDGE_REPO1_URL: git@github.com:paul/repo1.git
      GITBRIDGE_REPO1_AUTH: ssh
      GITBRIDGE_REPO1_SSH_KEY: |
        -----BEGIN OPENSSH PRIVATE KEY-----
        MIIEogIBAAKCAQEAw...
        -----END OPENSSH PRIVATE KEY-----

      # Target repo
      GITBRIDGE_REPO2_URL: https://github.com/paul/repo2.git
      GITBRIDGE_REPO2_AUTH: pat
      GITBRIDGE_REPO2_USER: paul
      GITBRIDGE_REPO2_PASS: ghp_xxx

      # Logging
      GITBRIDGE_LOG_LEVEL: info

      # Scheduling
      GITBRIDGE_MODE: mirror
      GITBRIDGE_SCHEDULE: "0 2 * * *"
    command: ["run"]
```

Run it:

```bash
docker compose up -d
```

---

## 🔒 Security & Compliance

- Built on **Red Hat UBI 9** (long‑term supported base image)  
- Dependencies pinned via `uv.lock`  
- Every release includes:  
  - 📑 `CHANGELOG.md`  
  - 📦 SBOMs in **CycloneDX** and **SPDX** formats  

---

## ✅ Summary

- **Fetch mode** → clone/fetch both repos into `/data/repo1` and `/data/repo2`  
- **Mirror mode** → push all branches + tags from Repo1 into Repo2  
- **Scheduled mode** → run fetch/mirror on a cron schedule (`GITBRIDGE_SCHEDULE`)  
- **Images published to Quay** with `latest`, `vX.Y.Z`, and `sha-<commit>` tags  
- **SBOMs included** in every GitHub Release  