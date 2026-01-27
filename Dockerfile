# Multi-stage Dockerfile 
FROM python:3.11-slim-bookworm AS base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

###########################################
# Builder stage - Install dependencies
###########################################
FROM base AS builder

# Copy uv binary from official image (pinned version for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.5.8 /uv /uvx /bin/

# Set uv environment variables for optimization
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/root/.cache/uv

# Set working directory
WORKDIR /app

# Copy dependency files first (for better layer caching)
COPY uv.lock pyproject.toml ./

# Install dependencies only (not the project itself yet)
# This creates a separate layer that can be cached
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY ./app ./app/

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

###########################################
# Production stage - Minimal runtime image
###########################################
FROM base AS production

# Copy uv binary to production stage
COPY --from=ghcr.io/astral-sh/uv:0.5.8 /uv /bin/

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy the virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app /app

# Switch to non-root user
USER appuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000