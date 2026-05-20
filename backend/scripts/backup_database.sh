#!/bin/bash
set -e

# BEFS3 KNOWME - Database Backup Script
# Run daily via cron or manually

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/database"
mkdir -p $BACKUP_DIR

echo "🔄 Starting database backup..."
echo "Date: $(date)"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL environment variable not set"
    echo "Please set DATABASE_URL before running this script"
    exit 1
fi

# Full database dump
echo "📦 Creating database dump..."
pg_dump $DATABASE_URL > $BACKUP_DIR/knowme_backup_$DATE.sql

if [ $? -eq 0 ]; then
    echo "✅ Database dump created successfully"
else
    echo "❌ Error creating database dump"
    exit 1
fi

# Compress
echo "🗜️  Compressing backup..."
gzip $BACKUP_DIR/knowme_backup_$DATE.sql

if [ $? -eq 0 ]; then
    echo "✅ Backup compressed successfully"
    BACKUP_FILE="$BACKUP_DIR/knowme_backup_$DATE.sql.gz"
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "📊 Backup size: $BACKUP_SIZE"
else
    echo "❌ Error compressing backup"
    exit 1
fi

# Keep only last 30 days of backups
echo "🧹 Cleaning up old backups (keeping last 30 days)..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
REMAINING=$(ls -1 $BACKUP_DIR/*.sql.gz 2>/dev/null | wc -l)
echo "📁 Backups remaining: $REMAINING"

echo ""
echo "✅ Backup completed successfully!"
echo "📂 Location: $BACKUP_FILE"
echo "📊 Size: $BACKUP_SIZE"
echo ""
echo "To restore this backup, run:"
echo "  gunzip -c $BACKUP_FILE | psql \$DATABASE_URL"
