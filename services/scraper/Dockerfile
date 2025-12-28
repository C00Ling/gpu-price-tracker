# Scraper Worker Dockerfile
# Autonomous cron-based worker for GPU data collection

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY services/scraper/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies (TOR + cron + curl + procps)
RUN apt-get update && apt-get install -y \
    tor \
    cron \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 scraperuser && \
    mkdir -p /app/logs /tmp/tor_data && \
    chown -R scraperuser:scraperuser /app /tmp/tor_data

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/scraperuser/.local

# Copy shared libraries
COPY --chown=scraperuser:scraperuser services/shared ./shared

# Copy configuration file
COPY --chown=scraperuser:scraperuser config.yaml .

# Copy scraper worker code
COPY --chown=scraperuser:scraperuser services/scraper .

# Copy TOR configuration (optional - start.sh will use defaults if missing)
# COPY --chown=scraperuser:scraperuser config/torrc ./config/torrc

# Copy crontab file (if using cron mode)
COPY --chown=scraperuser:scraperuser services/scraper/crontab /etc/cron.d/scraper-cron
RUN chmod 0644 /etc/cron.d/scraper-cron && \
    crontab -u scraperuser /etc/cron.d/scraper-cron

# Switch to non-root user
USER scraperuser

# Add local packages to PATH
ENV PATH=/home/scraperuser/.local/bin:$PATH
ENV PYTHONPATH=/app:/app/shared:$PYTHONPATH

# Health check (checks if TOR is running)
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep tor > /dev/null || exit 1

# Start scraper worker
CMD ["./start.sh"]
