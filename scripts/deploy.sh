#!/bin/bash

# Crypto Escrow Platform - Deployment Script
# This script handles deployment to staging or production environments

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
BACKUP_DIR="/opt/escrow/backups"
DEPLOY_DIR="/opt/escrow"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Crypto Escrow Platform Deployment${NC}"
echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}========================================${NC}"

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo -e "${RED}Error: Environment must be 'staging' or 'production'${NC}"
    exit 1
fi

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root or with sudo${NC}"
   exit 1
fi

# Function to create backup
create_backup() {
    echo -e "${YELLOW}Creating database backup...${NC}"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"
    
    mkdir -p "$BACKUP_DIR"
    
    pg_dump -U escrow escrow_${ENVIRONMENT} > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backup created: ${BACKUP_FILE}${NC}"
        gzip "$BACKUP_FILE"
        echo -e "${GREEN}Backup compressed: ${BACKUP_FILE}.gz${NC}"
        
        # Keep only last 7 backups
        ls -t ${BACKUP_DIR}/db_backup_*.sql.gz | tail -n +8 | xargs -r rm
    else
        echo -e "${RED}Backup failed!${NC}"
        exit 1
    fi
}

# Function to pull latest code
pull_code() {
    echo -e "${YELLOW}Pulling latest code...${NC}"
    cd "$DEPLOY_DIR"
    
    if [ "$ENVIRONMENT" == "production" ]; then
        git fetch origin
        git checkout main
        git pull origin main
    else
        git fetch origin
        git checkout develop
        git pull origin develop
    fi
    
    echo -e "${GREEN}Code updated successfully${NC}"
}

# Function to update backend
update_backend() {
    echo -e "${YELLOW}Updating backend...${NC}"
    cd "$DEPLOY_DIR/backend"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install/update dependencies
    pip install -r requirements.txt
    
    echo -e "${GREEN}Backend dependencies updated${NC}"
}

# Function to run migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    cd "$DEPLOY_DIR/backend"
    source venv/bin/activate
    python manage.py migrate --noinput
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Migrations completed successfully${NC}"
    else
        echo -e "${RED}Migrations failed!${NC}"
        exit 1
    fi
}

# Function to collect static files
collect_static() {
    echo -e "${YELLOW}Collecting static files...${NC}"
    cd "$DEPLOY_DIR/backend"
    source venv/bin/activate
    python manage.py collectstatic --noinput
    echo -e "${GREEN}Static files collected${NC}"
}

# Function to update frontend
update_frontend() {
    echo -e "${YELLOW}Updating frontend...${NC}"
    cd "$DEPLOY_DIR/frontend"
    
    # Install/update dependencies
    npm install
    
    # Build frontend
    npm run build
    
    echo -e "${GREEN}Frontend built successfully${NC}"
}

# Function to restart services
restart_services() {
    echo -e "${YELLOW}Restarting services...${NC}"
    
    # Restart backend
    systemctl restart escrow-backend
    
    # Restart Celery
    systemctl restart escrow-celery-worker
    systemctl restart escrow-celery-beat
    
    # Restart frontend
    systemctl restart escrow-frontend
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Services restarted successfully${NC}"
    else
        echo -e "${RED}Service restart failed!${NC}"
        exit 1
    fi
}

# Function to health check
health_check() {
    echo -e "${YELLOW}Performing health check...${NC}"
    sleep 10  # Wait for services to start
    
    # Check backend
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health/)
    if [ "$BACKEND_STATUS" == "200" ]; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
    else
        echo -e "${RED}✗ Backend health check failed (Status: ${BACKEND_STATUS})${NC}"
        exit 1
    fi
    
    # Check frontend
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/)
    if [ "$FRONTEND_STATUS" == "200" ]; then
        echo -e "${GREEN}✓ Frontend is healthy${NC}"
    else
        echo -e "${RED}✗ Frontend health check failed (Status: ${FRONTEND_STATUS})${NC}"
        exit 1
    fi
    
    # Check Celery
    cd "$DEPLOY_DIR/backend"
    source venv/bin/activate
    CELERY_STATUS=$(celery -A config inspect ping)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Celery is healthy${NC}"
    else
        echo -e "${RED}✗ Celery health check failed${NC}"
        exit 1
    fi
}

# Main deployment flow
main() {
    echo -e "${YELLOW}Starting deployment process...${NC}"
    
    # Confirmation for production
    if [ "$ENVIRONMENT" == "production" ]; then
        echo -e "${RED}WARNING: You are about to deploy to PRODUCTION!${NC}"
        read -p "Are you sure you want to continue? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo -e "${YELLOW}Deployment cancelled${NC}"
            exit 0
        fi
    fi
    
    # Execute deployment steps
    create_backup
    pull_code
    update_backend
    update_frontend
    run_migrations
    collect_static
    restart_services
    health_check
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    # Show service status
    echo -e "\n${YELLOW}Service Status:${NC}"
    systemctl status escrow-backend --no-pager
    systemctl status escrow-celery-worker --no-pager
    systemctl status escrow-frontend --no-pager
}

# Run main function
main
