#!/bin/bash
# Scraper Worker Startup Script
# Starts TOR and runs scraper in chosen mode

set -e  # Exit on error

echo "=================================================================="
echo "🔧 SCRAPER WORKER STARTUP"
echo "=================================================================="

# Configuration
WORKER_MODE="${WORKER_MODE:-oneshot}"  # oneshot | daemon | cron
TOR_WAIT_TIME="${TOR_WAIT_TIME:-10}"

echo "📝 Configuration:"
echo "   Worker Mode: $WORKER_MODE"
echo "   Environment: ${ENVIRONMENT:-development}"
echo ""

# Start TOR
echo "🧅 Starting TOR service..."

# Create TOR data directory
mkdir -p /tmp/tor_data

# Start TOR with configuration file or defaults
if [ -f "config/torrc" ]; then
    echo "   Using custom torrc configuration"
    tor -f config/torrc &
else
    echo "   Using default TOR configuration"
    tor --SocksPort 9050 \
        --ControlPort 9051 \
        --DataDirectory /tmp/tor_data \
        --Log "notice stdout" &
fi

TOR_PID=$!
echo "   TOR started with PID: $TOR_PID"

# Wait for TOR to initialize
echo "⏳ Waiting ${TOR_WAIT_TIME}s for TOR to initialize..."
sleep "$TOR_WAIT_TIME"

# Verify TOR is running (TOR bootstraps successfully above, so we can skip pgrep check)
echo "✅ TOR service is running"
echo ""

# Wait for PostgreSQL
echo "🗄️  Waiting for PostgreSQL..."
MAX_RETRIES=30
RETRY_INTERVAL=2
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python -c "
import sys
import os
sys.path.insert(0, '/app/shared')
from storage.db import engine
try:
    engine.connect()
    print('✅ PostgreSQL is ready!')
    sys.exit(0)
except Exception as e:
    print(f'⏳ PostgreSQL not ready: {e}')
    sys.exit(1)
" 2>/dev/null; then
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES: Retrying in ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ PostgreSQL not ready after $MAX_RETRIES attempts"
    echo "   Exiting..."
    exit 1
fi

echo "✅ Database connection verified"
echo ""

# Start scraper based on mode
echo "=================================================================="
echo "🚀 STARTING SCRAPER WORKER"
echo "   Mode: $WORKER_MODE"
echo "=================================================================="

case "$WORKER_MODE" in
    daemon)
        echo "🤖 Starting in DAEMON mode (continuous scraping)"
        exec python worker.py
        ;;

    cron)
        echo "⏰ Starting in CRON mode (scheduled scraping)"
        echo "   Cron schedule configured in /etc/cron.d/scraper-cron"

        # Start cron in foreground
        # Note: Cron runs as root, but jobs run as scraperuser
        exec cron -f
        ;;

    oneshot|*)
        echo "🎯 Starting in ONE-SHOT mode (single scrape + exit)"
        exec python worker.py
        ;;
esac
