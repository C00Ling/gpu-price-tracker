# API Service Dockerfile
# Read-only HTTP server for web UI and REST API

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 apiuser && \
    mkdir -p /app/logs && \
    chown -R apiuser:apiuser /app

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/apiuser/.local

# Copy shared libraries
COPY --chown=apiuser:apiuser services/shared ./shared

# Copy data directory (GPU benchmarks)
COPY --chown=apiuser:apiuser data ./data

# Copy configuration file
COPY --chown=apiuser:apiuser config.yaml .

# Copy API service code
COPY --chown=apiuser:apiuser services/api .

# Copy static files (frontend build)
COPY --chown=apiuser:apiuser static ./static

# Switch to non-root user
USER apiuser

# Add local packages to PATH
ENV PATH=/home/apiuser/.local/bin:$PATH
ENV PYTHONPATH=/app:/app/shared:$PYTHONPATH

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start API service
# Use PORT environment variable from Railway, default to 8000 for local
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level warning"
