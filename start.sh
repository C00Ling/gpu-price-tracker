#!/bin/bash
# Startup script for Railway with TOR support

echo "🔧 Starting TOR service..."

# Start TOR in background
tor --SocksPort 9050 --ControlPort 9051 &
TOR_PID=$!

echo "⏳ Waiting for TOR to initialize..."
sleep 10

# Check if TOR is running
if ps -p $TOR_PID > /dev/null; then
    echo "✅ TOR service started successfully (PID: $TOR_PID)"
else
    echo "⚠️ TOR failed to start, continuing without TOR..."
fi

# Start the web application
echo "🚀 Starting web application..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT
