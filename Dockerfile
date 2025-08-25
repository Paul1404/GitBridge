# Builder stage
FROM registry.access.redhat.com/ubi9/python-312:latest AS builder

USER root
RUN dnf install -y curl git openssh-clients \
    && dnf clean all

# Install uv (single binary)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock /app/
COPY gitbridge.py git_utils.py logger.py settings.py /app/

# Install dependencies with uv
RUN uv sync --frozen

# Runtime stage
FROM registry.access.redhat.com/ubi9/python-312:latest

USER root
RUN dnf install -y git openssh-clients \
    && dnf clean all

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