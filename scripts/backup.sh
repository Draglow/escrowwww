#!/bin/bash

# Crypto Escrow Platform - Backup Script
# Automated backup script for database and media files

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="/opt/escrow/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y-%m-%d)

# Database backup
DB_BACKUP_FILE="${BACKUP_DIR}/db/db_backup_${TIMESTAMP}.sql"
# Media backup
MEDIA_BACKUP_FILE="${BACKUP_DIR}/media/media_backup_${TIMESTAMP}.tar.gz"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Backup Process${NC}"
echo -e "${GREEN}Timestamp: ${TIMESTAMP}${NC}"
echo -e "${GREEN}========================================${NC}"

# Create backup directories
mkdir -p "${BACKUP_DIR}/db"
mkdir -p "${BACKUP_DIR}/media"

# Backup database
echo -e "${YELLOW}Backing up database...${NC}"
pg_dumpall -U escrow > "$DB_BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database backup created${NC}"
    
    # Compress backup
    gzip "$DB_BACKUP_FILE"
    echo -e "${GREEN}✓ Database backup compressed${NC}"
    
    # Calculate size
    SIZE=$(du -h "${DB_BACKUP_FILE}.gz" | cut -f1)
    echo -e "${GREEN}  Size: ${SIZE}${NC}"
else
    echo -e "${RED}✗ Database backup failed${NC}"
    exit 1
fi

# Backup media files
echo -e "${YELLOW}Backing up media files...${NC}"
if [ -d "/opt/escrow/media" ]; then
    tar -czf "$MEDIA_BACKUP_FILE" -C /opt/escrow media/
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Media files backup created${NC}"
        SIZE=$(du -h "$MEDIA_BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}  Size: ${SIZE}${NC}"
    else
        echo -e "${RED}✗ Media backup failed${NC}"
    fi
else
    echo -e "${YELLOW}No media directory found, skipping...${NC}"
fi

# Backup configuration files
echo -e "${YELLOW}Backing up configuration files...${NC}"
CONFIG_BACKUP_FILE="${BACKUP_DIR}/config/config_backup_${TIMESTAMP}.tar.gz"
mkdir -p "${BACKUP_DIR}/config"

tar -czf "$CONFIG_BACKUP_FILE" \
    -C /opt/escrow \
    backend/.env \
    frontend/.env.local \
    2>/dev/null || true

if [ -f "$CONFIG_BACKUP_FILE" ]; then
    echo -e "${GREEN}✓ Configuration backup created${NC}"
else
    echo -e "${YELLOW}⚠ Configuration backup skipped${NC}"
fi

# Clean up old backups
echo -e "${YELLOW}Cleaning up old backups (older than ${RETENTION_DAYS} days)...${NC}"

# Clean database backups
find "${BACKUP_DIR}/db" -name "db_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
DB_DELETED=$(find "${BACKUP_DIR}/db" -name "db_backup_*.sql.gz" -mtime +${RETENTION_DAYS} | wc -l)

# Clean media backups
find "${BACKUP_DIR}/media" -name "media_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
MEDIA_DELETED=$(find "${BACKUP_DIR}/media" -name "media_backup_*.tar.gz" -mtime +${RETENTION_DAYS} | wc -l)

# Clean config backups
find "${BACKUP_DIR}/config" -name "config_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo -e "${GREEN}✓ Cleanup completed${NC}"

# Upload to remote storage (optional - uncomment and configure)
# echo -e "${YELLOW}Uploading to remote storage...${NC}"
# aws s3 sync ${BACKUP_DIR} s3://your-backup-bucket/escrow-backups/ --storage-class GLACIER
# echo -e "${GREEN}✓ Upload completed${NC}"

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Backup Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Database backup: ${DB_BACKUP_FILE}.gz"
echo -e "Media backup: ${MEDIA_BACKUP_FILE}"
echo -e "Config backup: ${CONFIG_BACKUP_FILE}"
echo -e "\nTotal backups in storage:"
echo -e "  Database: $(ls -1 ${BACKUP_DIR}/db/*.gz 2>/dev/null | wc -l) files"
echo -e "  Media: $(ls -1 ${BACKUP_DIR}/media/*.tar.gz 2>/dev/null | wc -l) files"
echo -e "  Config: $(ls -1 ${BACKUP_DIR}/config/*.tar.gz 2>/dev/null | wc -l) files"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
