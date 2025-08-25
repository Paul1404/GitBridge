FROM python:3.12-slim AS builder

# Install curl + git + ssh
RUN apt-get update && apt-get install -y curl git openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv (single binary)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /app

# Copy project files
COPY pyproject.toml /app/
COPY gitbridge.py git_utils.py logger.py settings.py /app/

# Install dependencies with uv
RUN uv sync --frozen

# Final runtime image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y git openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy uv environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# Ensure uv venv is used
ENV PATH="/app/.venv/bin:$PATH"

# Create data dir
RUN mkdir -p /data && chmod 777 /data
VOLUME ["/data"]

ENTRYPOINT ["python", "gitbridge.py"]