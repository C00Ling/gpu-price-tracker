# Multi-stage build for smaller image
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install TOR
RUN apt-get update && apt-get install -y \
    tor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 gpuservice && \
    mkdir -p /app/logs && \
    chown -R gpuservice:gpuservice /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/gpuservice/.local

# Copy application code
COPY --chown=gpuservice:gpuservice . .

# Switch to non-root user
USER gpuservice

# Add local packages to PATH
ENV PATH=/home/gpuservice/.local/bin:$PATH

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start TOR, run migrations, and start application
CMD ["sh", "-c", "tor & sleep 5 && alembic upgrade head && python -m ingest.pipeline && uvicorn main:app --host 0.0.0.0 --port 8000"]