#!/bin/bash

#
# Database Backup Script for Stock Screener Platform
#
# This script creates automated PostgreSQL backups with:
# - Timestamped backup files
# - Gzip compression for space efficiency
# - Automatic retention (keeps last 7 days)
# - Error handling and logging
#
# Usage:
#   ./scripts/backup_database.sh
#
# Cron setup (daily at 2 AM):
#   0 2 * * * /path/to/screener/scripts/backup_database.sh >> /path/to/screener/logs/backup.log 2>&1
#

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups"
DB_CONTAINER="screener_postgres"
DB_USER="screener_user"
DB_NAME="screener_db"
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/screener_db_${TIMESTAMP}.sql.gz"

echo "=================================================="
echo "Database Backup - $(date)"
echo "=================================================="

# Check if PostgreSQL container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    echo "ERROR: PostgreSQL container '${DB_CONTAINER}' is not running"
    exit 1
fi

# Create backup
echo "Creating backup: $(basename $BACKUP_FILE)"
if docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ Backup created successfully: $BACKUP_SIZE"
else
    echo "✗ Backup failed"
    rm -f "$BACKUP_FILE"  # Remove partial backup
    exit 1
fi

# Remove old backups (keep last N days)
echo "Cleaning up old backups (keeping last ${RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "screener_db_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "screener_db_*.sql.gz" -type f | wc -l)
echo "✓ Current backups: $REMAINING_BACKUPS files"

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "✓ Total backup directory size: $TOTAL_SIZE"

echo "=================================================="
echo "Backup completed successfully at $(date)"
echo "=================================================="
