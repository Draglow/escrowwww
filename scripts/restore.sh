#!/bin/bash

# Crypto Escrow Platform - Restore Script
# Restore database and media files from backup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="/opt/escrow/backups"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Crypto Escrow Platform - Restore${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root or with sudo${NC}"
   exit 1
fi

# List available backups
echo -e "${YELLOW}Available database backups:${NC}"
ls -lh "${BACKUP_DIR}/db/" | grep "db_backup_" | nl

# Get backup selection
read -p "Enter the number of the backup to restore (or 'q' to quit): " SELECTION

if [ "$SELECTION" == "q" ]; then
    echo -e "${YELLOW}Restore cancelled${NC}"
    exit 0
fi

# Get the selected backup file
BACKUP_FILE=$(ls -1 "${BACKUP_DIR}/db/"db_backup_*.sql.gz | sed -n "${SELECTION}p")

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Invalid selection${NC}"
    exit 1
fi

echo -e "${YELLOW}Selected backup: ${BACKUP_FILE}${NC}"

# Confirmation
echo -e "${RED}WARNING: This will overwrite the current database!${NC}"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Restore cancelled${NC}"
    exit 0
fi

# Stop services
echo -e "${YELLOW}Stopping services...${NC}"
systemctl stop escrow-backend escrow-celery-worker escrow-celery-beat

# Decompress backup
echo -e "${YELLOW}Decompressing backup...${NC}"
TEMP_FILE="/tmp/restore_$(date +%s).sql"
gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"

# Drop existing database
echo -e "${YELLOW}Dropping existing database...${NC}"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS escrow_prod;"
sudo -u postgres psql -c "CREATE DATABASE escrow_prod;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE escrow_prod TO escrow;"

# Restore database
echo -e "${YELLOW}Restoring database...${NC}"
sudo -u postgres psql escrow_prod < "$TEMP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database restored successfully${NC}"
else
    echo -e "${RED}✗ Database restore failed${NC}"
    rm "$TEMP_FILE"
    exit 1
fi

# Clean up temp file
rm "$TEMP_FILE"

# Restore media files (optional)
read -p "Do you want to restore media files? (yes/no): " RESTORE_MEDIA

if [ "$RESTORE_MEDIA" == "yes" ]; then
    echo -e "${YELLOW}Available media backups:${NC}"
    ls -lh "${BACKUP_DIR}/media/" | grep "media_backup_" | nl
    
    read -p "Enter the number of the media backup to restore: " MEDIA_SELECTION
    MEDIA_BACKUP=$(ls -1 "${BACKUP_DIR}/media/"media_backup_*.tar.gz | sed -n "${MEDIA_SELECTION}p")
    
    if [ -n "$MEDIA_BACKUP" ]; then
        echo -e "${YELLOW}Restoring media files...${NC}"
        tar -xzf "$MEDIA_BACKUP" -C /opt/escrow/
        echo -e "${GREEN}✓ Media files restored${NC}"
    else
        echo -e "${RED}Invalid selection, skipping media restore${NC}"
    fi
fi

# Start services
echo -e "${YELLOW}Starting services...${NC}"
systemctl start escrow-backend escrow-celery-worker escrow-celery-beat

# Wait for services
sleep 10

# Health check
echo -e "${YELLOW}Performing health check...${NC}"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health/)

if [ "$BACKEND_STATUS" == "200" ]; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Restore completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
