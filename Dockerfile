# Build stage: install dependencies and package
FROM python:3.13-slim AS builder

WORKDIR /build

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package into a virtual environment
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python .

# Final stage: minimal runtime image
FROM python:3.13-slim

# Copy the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash elasticode
USER elasticode
WORKDIR /home/elasticode

ENTRYPOINT ["elasticode"]
