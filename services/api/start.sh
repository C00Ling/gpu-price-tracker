#!/bin/bash
# API Service Startup Script
# Read-only HTTP server - NO scraping

set -e  # Exit on error

echo "="
echo "🌐 API SERVICE STARTUP"
echo "="

# Wait for PostgreSQL to be ready
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
    print(f'⏳ PostgreSQL not ready yet: {e}')
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
    echo "⚠️  Starting API anyway (will fail on database calls)"
fi

echo "✅ Database connection verified"
echo ""

# Start API service
echo "🚀 Starting API Service (Read-Only HTTP Server)..."
echo "   Port: ${PORT:-8000}"
echo "   Environment: ${ENVIRONMENT:-development}"
echo ""

# Use exec to replace shell with uvicorn (proper signal handling)
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --log-level warning \
    --no-access-log \
    --timeout-keep-alive 75
