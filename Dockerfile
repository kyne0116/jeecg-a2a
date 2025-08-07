# JEECG A2A Platform - Docker Image

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Copy pyproject.toml first for better caching
COPY pyproject.toml .

# Create virtual environment and install dependencies
RUN uv venv \
    && uv sync

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs data uploads ui/static/uploads

# Create non-root user
RUN groupadd -r a2a && useradd -r -g a2a a2a

# Change ownership of app directory
RUN chown -R a2a:a2a /app

# Switch to non-root user
USER a2a

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uv", "run", "main.py"]
