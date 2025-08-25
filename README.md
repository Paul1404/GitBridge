# 📖 GitBridge

**GitBridge** is a lightweight containerized tool that **fetches two Git repositories** into mounted volumes, with support for multiple authentication methods (SSH, PAT, password, or none).  

It is designed for **production use** with:  
- Built on **Red Hat UBI 9 Python 3.12**  
- Dependencies managed with **uv**  
- Automated **CI/CD pipeline** with **semantic‑release**  
- **Multi‑arch images** (amd64 + arm64) published to [Quay.io](https://quay.io/repository/scaling4840/gitbridge)  
- **Trivy vulnerability scan** + **SBOMs (CycloneDX + SPDX)** attached to every GitHub Release  

---

## 🚀 Features

- 🔑 Supports **SSH keys, PATs, passwords, or no auth**  
- 📦 Fetches/clones into `/data/repo1` and `/data/repo2`  
- 📝 Structured logging with **Rich**  
- ⚡ Multi‑arch builds (x86_64 + ARM64)  
- 🔒 Security scanning with **Trivy**  
- 📑 SBOM generation (CycloneDX + SPDX) for compliance and visibility  

---

## 🛠️ Environment Variables

### Repo 1
- `GITBRIDGE_REPO1_URL` → Git URL (required)  
- `GITBRIDGE_REPO1_AUTH` → `ssh|pat|password|none` (default: `none`)  
- `GITBRIDGE_REPO1_USER` → Username (if PAT/password)  
- `GITBRIDGE_REPO1_PASS` → Password or PAT  
- `GITBRIDGE_REPO1_SSH_KEY` → Private SSH key  

### Repo 2
- `GITBRIDGE_REPO2_URL` → Git URL (required)  
- `GITBRIDGE_REPO2_AUTH` → `ssh|pat|password|none` (default: `none`)  
- `GITBRIDGE_REPO2_USER` → Username (if PAT/password)  
- `GITBRIDGE_REPO2_PASS` → Password or PAT  
- `GITBRIDGE_REPO2_SSH_KEY` → Private SSH key  

### Logging
- `GITBRIDGE_LOG_LEVEL` → `info|debug|warn|error` (default: `info`)  

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

### Run with Docker

```bash
docker run --rm \
  -v $(pwd)/data:/data \
  -e GITBRIDGE_REPO1_URL=git@github.com:paul/repo1.git \
  -e GITBRIDGE_REPO1_AUTH=ssh \
  -e GITBRIDGE_REPO1_SSH_KEY="$(cat ~/.ssh/id_rsa)" \
  -e GITBRIDGE_REPO2_URL=https://github.com/paul/repo2.git \
  -e GITBRIDGE_REPO2_AUTH=pat \
  -e GITBRIDGE_REPO2_USER=paul \
  -e GITBRIDGE_REPO2_PASS=ghp_xxx \
  quay.io/scaling4840/gitbridge:latest fetch
```

After running, you’ll have:

```
./data/repo1/.git
./data/repo2/.git
```

---

### Run with Docker Compose

Create a `docker-compose.yml`:

```yaml
services:
  gitbridge:
    image: quay.io/scaling4840/gitbridge:latest
    container_name: gitbridge
    volumes:
      - ./data:/data
    environment:
      # Repo 1
      GITBRIDGE_REPO1_URL: git@github.com:paul/repo1.git
      GITBRIDGE_REPO1_AUTH: ssh
      GITBRIDGE_REPO1_SSH_KEY: |
        -----BEGIN OPENSSH PRIVATE KEY-----
        MIIEogIBAAKCAQEAw...
        -----END OPENSSH PRIVATE KEY-----

      # Repo 2
      GITBRIDGE_REPO2_URL: https://github.com/paul/repo2.git
      GITBRIDGE_REPO2_AUTH: pat
      GITBRIDGE_REPO2_USER: paul
      GITBRIDGE_REPO2_PASS: ghp_xxx

      # Logging
      GITBRIDGE_LOG_LEVEL: info
    command: ["fetch"]
```

---

### Example `.env`

```dotenv
# Repo 1
GITBRIDGE_REPO1_URL=git@github.com:paul/repo1.git
GITBRIDGE_REPO1_AUTH=ssh
GITBRIDGE_REPO1_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
MIIEogIBAAKCAQEAw...
-----END OPENSSH PRIVATE KEY-----

# Repo 2
GITBRIDGE_REPO2_URL=https://github.com/paul/repo2.git
GITBRIDGE_REPO2_AUTH=pat
GITBRIDGE_REPO2_USER=paul
GITBRIDGE_REPO2_PASS=ghp_xxx

# Logging
GITBRIDGE_LOG_LEVEL=info
```

⚠️ **Important:**  
- Never commit `.env` files with secrets to Git!  
- Add `.env` to your `.gitignore`.  

---

### Run with Compose

```bash
docker compose up
```

This will:  
- Load secrets from `.env`  
- Fetch both repos into `./data/repo1` and `./data/repo2`  

---

## 🔒 Security & Compliance

- Built on **Red Hat UBI 9** (long‑term supported base image)  
- Dependencies pinned via `uv.lock`  
- Every release includes:  
  - 📑 `CHANGELOG.md`  
  - 🔒 Trivy vulnerability scan results (SARIF)  
  - 📦 SBOMs in **CycloneDX** and **SPDX** formats  

---

## ✅ Summary

- **GitBridge** fetches two Git repos into `/data/repo1` and `/data/repo2`  
- **Automated pipeline** ensures every commit → new release → new Quay image  
- **Security built‑in**: Trivy scans + SBOMs for compliance and visibility  
- **Easy to run**: via `docker run` or `docker compose` with `.env` support  