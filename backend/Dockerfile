# Backend Dockerfile for Money Map Manager
# Uses multi-stage build for smaller production image.

# ============================================
# Stage 1: Build
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv for fast dependency management.
RUN pip install --no-cache-dir uv

# Copy dependency files first for better caching.
# The uv.lock* wildcard allows build to proceed if lock file doesn't exist.
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv.
RUN uv sync --no-dev

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.12-slim AS production

WORKDIR /app

# Create non-root user for security.
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder.
COPY --from=builder /app/.venv /app/.venv

# Copy application code.
COPY app ./app

# Create data directory for SQLite database.
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to non-root user.
USER appuser

# Set environment variables.
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port.
EXPOSE 8000

# Health check.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
