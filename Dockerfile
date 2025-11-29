# Dockerfile for Hyperbot - Telegram Trading Bot
# Multi-stage build for smaller final image

# Stage 1: Build stage
FROM python:3.11-slim AS builder

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install dependencies to a virtual environment
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install only runtime dependencies (not dev dependencies)
RUN uv pip install --no-cache .

# Stage 2: Runtime stage
FROM python:3.11-slim

# Install curl for healthchecks (optional)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/
COPY run.py ./

# Create logs directory
RUN mkdir -p logs

# Create non-root user for security
RUN useradd -m -u 1000 hyperbot && \
    chown -R hyperbot:hyperbot /app
USER hyperbot

# Expose port for FastAPI (if running API server)
EXPOSE 8000

# Default command: Run Telegram bot
# Override with docker run command to run API server or other services
CMD ["python", "-m", "src.bot.main"]

# Health check for bot (checks if process is running)
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD pgrep -f "src.bot.main" || exit 1
