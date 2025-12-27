#!/bin/bash
# Startup script for Railway with TOR support

echo "🔧 Starting TOR service..."

# Create TOR data directory
mkdir -p /tmp/tor_data

# Start TOR in background with configuration file
if [ -f "config/torrc" ]; then
    tor -f config/torrc &
else
    # Fallback to Railway-compatible settings (matching scraper expectations)
    tor --SocksPort 9050 --ControlPort 9151 --DataDirectory /tmp/tor_data &
fi

echo "⏳ Waiting for TOR to initialize..."
sleep 10
echo "✅ TOR service started"

# Wait for PostgreSQL to be ready
echo "🗄️  Checking PostgreSQL connection..."
python wait_for_db.py
if [ $? -ne 0 ]; then
    echo "⚠️ PostgreSQL not ready, but continuing with migrations anyway..."
fi

# Run database migrations
echo "📦 Running database migrations..."

# Try to run migrations
alembic upgrade head 2>&1 | tee /tmp/migration.log

# Check if migration failed due to table already existing
if grep -q "relation \"listings\" already exists" /tmp/migration.log; then
    echo "⚠️ Table already exists, marking initial migration as complete..."
    # Mark the first migration as applied
    alembic stamp bedc9c8b7145
    # Now run the url column migration
    echo "📦 Running remaining migrations..."
    alembic upgrade head
    if [ $? -eq 0 ]; then
        echo "✅ Database migrations completed successfully"
    else
        echo "⚠️ Remaining migrations failed, but continuing..."
    fi
elif [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "⚠️ Database migrations failed, but continuing..."
fi

# Start the web application
echo "🚀 Starting web application..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT --log-level warning
