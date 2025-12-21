#!/bin/bash

# ============================================
# GPU Market Service - Backup Script
# ============================================
# Creates timestamped backups of database and logs
# Keeps only last N backups to save space

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP_BACKUPS="${KEEP_BACKUPS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="gpu-market-$DATE"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "💾 GPU Market Service - Backup"
echo "================================"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo -e "${GREEN}Creating backup: $BACKUP_NAME${NC}"

# Create temporary directory for this backup
TEMP_DIR="$BACKUP_DIR/temp_$DATE"
mkdir -p "$TEMP_DIR"

# Backup database
if [ -f "gpu.db" ]; then
    echo "📦 Backing up database..."
    cp gpu.db "$TEMP_DIR/"
    echo "   ✓ Database backed up"
else
    echo "   ⚠️  Database not found, skipping"
fi

# Backup logs
if [ -d "logs" ]; then
    echo "📄 Backing up logs..."
    cp -r logs "$TEMP_DIR/"
    echo "   ✓ Logs backed up"
else
    echo "   ⚠️  Logs directory not found, skipping"
fi

# Backup config (without secrets)
echo "⚙️  Backing up config..."
if [ -f "config.yaml" ]; then
    cp config.yaml "$TEMP_DIR/"
fi
if [ -f ".env.example" ]; then
    cp .env.example "$TEMP_DIR/"
fi
echo "   ✓ Config backed up"

# Create tarball
echo "🗜️  Compressing backup..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" -C "temp_$DATE" .
cd - > /dev/null

# Remove temporary directory
rm -rf "$TEMP_DIR"

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
echo "   ✓ Backup created: ${BACKUP_NAME}.tar.gz ($BACKUP_SIZE)"

# Cleanup old backups
echo "🧹 Cleaning up old backups (keeping last $KEEP_BACKUPS)..."
cd "$BACKUP_DIR"
ls -t gpu-market-*.tar.gz 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm -f
REMAINING=$(ls -1 gpu-market-*.tar.gz 2>/dev/null | wc -l)
cd - > /dev/null
echo "   ✓ $REMAINING backup(s) remaining"

echo ""
echo -e "${GREEN}✓ Backup completed successfully!${NC}"
echo "   Location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo ""

# Optional: Upload to cloud storage
# Uncomment and configure for your cloud provider
# if [ -n "$AWS_S3_BUCKET" ]; then
#     echo "☁️  Uploading to S3..."
#     aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" "s3://$AWS_S3_BUCKET/backups/"
#     echo "   ✓ Uploaded to cloud"
# fi

exit 0