# Production Deployment Guide - Native Setup

Complete guide for deploying the Crypto Escrow Platform to production without Docker.

**Last Updated:** April 23, 2026  
**Deployment Type:** Native (No Docker)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Install Dependencies](#install-dependencies)
4. [Database Setup](#database-setup)
5. [Application Setup](#application-setup)
6. [Systemd Services](#systemd-services)
7. [Nginx Configuration](#nginx-configuration)
8. [SSL Certificate](#ssl-certificate)
9. [Deployment](#deployment)
10. [Monitoring](#monitoring)
11. [Backup & Recovery](#backup--recovery)

---

## Prerequisites

### Server Requirements

**Minimum (Small Scale):**
- CPU: 2 cores
- RAM: 4 GB
- Storage: 50 GB SSD
- OS: Ubuntu 22.04 LTS

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 8+ GB
- Storage: 100+ GB SSD
- OS: Ubuntu 22.04 LTS

### Domain Names

You'll need:
- `escrow.example.com` - Frontend
- `api.escrow.example.com` - Backend API

---

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install basic tools
sudo apt install -y curl git ufw fail2ban build-essential

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Create application user
sudo useradd -m -s /bin/bash escrow
sudo usermod -aG sudo escrow
```

---

## Install Dependencies

### 2. Install Python 3.11

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### 3. Install PostgreSQL 15

```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# Install PostgreSQL
sudo apt install -y postgresql-15 postgresql-contrib-15

# Start and enable
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 4. Install Redis

```bash
sudo apt install -y redis-server

# Configure Redis
sudo sed -i 's/supervised no/supervised systemd/' /etc/redis/redis.conf
sudo sed -i 's/# requirepass foobared/requirepass your-strong-redis-password/' /etc/redis/redis.conf

# Restart Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

### 5. Install Node.js 18

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version
npm --version
```

### 6. Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## Database Setup

### 7. Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE escrow_prod;
CREATE USER escrow WITH PASSWORD 'your-strong-database-password';
GRANT ALL PRIVILEGES ON DATABASE escrow_prod TO escrow;
ALTER USER escrow CREATEDB;
\q
```

### 8. Configure PostgreSQL for Production

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/15/main/postgresql.conf

# Recommended settings:
# max_connections = 100
# shared_buffers = 256MB
# effective_cache_size = 1GB
# maintenance_work_mem = 64MB
# checkpoint_completion_target = 0.9
# wal_buffers = 16MB
# default_statistics_target = 100
# random_page_cost = 1.1
# effective_io_concurrency = 200
# work_mem = 2621kB
# min_wal_size = 1GB
# max_wal_size = 4GB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## Application Setup

### 9. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/escrow
sudo chown escrow:escrow /opt/escrow

# Switch to escrow user
sudo su - escrow
cd /opt/escrow

# Clone repository
git clone https://github.com/yourusername/escrow-platform.git .
git checkout main
```

### 10. Setup Backend

```bash
cd /opt/escrow/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file
cp .env.example .env
nano .env
```

**Configure `.env`:**
```env
DEBUG=False
SECRET_KEY=your-generated-secret-key
ALLOWED_HOSTS=api.escrow.example.com
DATABASE_URL=postgresql://escrow:your-password@localhost:5432/escrow_prod
REDIS_URL=redis://:your-redis-password@localhost:6379/0
# ... (see .env.production.example for all settings)
```

### 11. Run Migrations

```bash
cd /opt/escrow/backend
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 12. Setup Frontend

```bash
cd /opt/escrow/frontend

# Install dependencies
npm install

# Create .env.local
cp .env.local.example .env.local
nano .env.local
```

**Configure `.env.local`:**
```env
NEXT_PUBLIC_API_URL=https://api.escrow.example.com
NEXT_PUBLIC_WS_URL=wss://api.escrow.example.com
NEXT_PUBLIC_TELEGRAM_BOT_NAME=YourBotName
```

### 13. Build Frontend

```bash
cd /opt/escrow/frontend
npm run build
```

---

## Systemd Services

### 14. Create Backend Service

```bash
sudo nano /etc/systemd/system/escrow-backend.service
```

```ini
[Unit]
Description=Escrow Backend (Gunicorn)
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=escrow
Group=escrow
WorkingDirectory=/opt/escrow/backend
Environment="PATH=/opt/escrow/backend/venv/bin"
EnvironmentFile=/opt/escrow/backend/.env
ExecStart=/opt/escrow/backend/venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 60 \
    --access-logfile /var/log/escrow/backend-access.log \
    --error-logfile /var/log/escrow/backend-error.log \
    --log-level info
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

### 15. Create Celery Worker Service

```bash
sudo nano /etc/systemd/system/escrow-celery-worker.service
```

```ini
[Unit]
Description=Escrow Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=escrow
Group=escrow
WorkingDirectory=/opt/escrow/backend
Environment="PATH=/opt/escrow/backend/venv/bin"
EnvironmentFile=/opt/escrow/backend/.env
ExecStart=/opt/escrow/backend/venv/bin/celery -A config worker \
    --loglevel=info \
    --logfile=/var/log/escrow/celery-worker.log \
    --pidfile=/var/run/celery/worker.pid
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

### 16. Create Celery Beat Service

```bash
sudo nano /etc/systemd/system/escrow-celery-beat.service
```

```ini
[Unit]
Description=Escrow Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=escrow
Group=escrow
WorkingDirectory=/opt/escrow/backend
Environment="PATH=/opt/escrow/backend/venv/bin"
EnvironmentFile=/opt/escrow/backend/.env
ExecStart=/opt/escrow/backend/venv/bin/celery -A config beat \
    --loglevel=info \
    --logfile=/var/log/escrow/celery-beat.log \
    --pidfile=/var/run/celery/beat.pid \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=always

[Install]
WantedBy=multi-user.target
```

### 17. Create Frontend Service

```bash
sudo nano /etc/systemd/system/escrow-frontend.service
```

```ini
[Unit]
Description=Escrow Frontend (Next.js)
After=network.target

[Service]
Type=simple
User=escrow
Group=escrow
WorkingDirectory=/opt/escrow/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
EnvironmentFile=/opt/escrow/frontend/.env.local
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

### 18. Create Log Directories

```bash
sudo mkdir -p /var/log/escrow
sudo mkdir -p /var/run/celery
sudo chown -R escrow:escrow /var/log/escrow
sudo chown -R escrow:escrow /var/run/celery
```

### 19. Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable escrow-backend
sudo systemctl enable escrow-celery-worker
sudo systemctl enable escrow-celery-beat
sudo systemctl enable escrow-frontend

# Start services
sudo systemctl start escrow-backend
sudo systemctl start escrow-celery-worker
sudo systemctl start escrow-celery-beat
sudo systemctl start escrow-frontend

# Check status
sudo systemctl status escrow-backend
sudo systemctl status escrow-celery-worker
sudo systemctl status escrow-celery-beat
sudo systemctl status escrow-frontend
```

---

## Nginx Configuration

### 20. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/escrow
```

```nginx
# Backend API
server {
    listen 80;
    server_name api.escrow.example.com;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /opt/escrow/backend/staticfiles/;
    }
    
    location /media/ {
        alias /opt/escrow/backend/media/;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Frontend
server {
    listen 80;
    server_name escrow.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 21. Enable Nginx Site

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/escrow /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## SSL Certificate

### 22. Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 23. Obtain SSL Certificates

```bash
# For backend API
sudo certbot --nginx -d api.escrow.example.com

# For frontend
sudo certbot --nginx -d escrow.example.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

---

## Deployment

### 24. Automated Deployment Script

The `scripts/deploy.sh` script handles deployments:

```bash
# Deploy to production
sudo bash /opt/escrow/scripts/deploy.sh production
```

The script will:
1. Create database backup
2. Pull latest code
3. Update backend dependencies
4. Update frontend dependencies
5. Run migrations
6. Collect static files
7. Restart all services
8. Perform health checks

---

## Monitoring

### 25. View Logs

```bash
# Backend logs
sudo journalctl -u escrow-backend -f

# Celery worker logs
sudo journalctl -u escrow-celery-worker -f

# Celery beat logs
sudo journalctl -u escrow-celery-beat -f

# Frontend logs
sudo journalctl -u escrow-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 26. Health Checks

```bash
# Backend health
curl https://api.escrow.example.com/api/v1/health/

# Frontend
curl https://escrow.example.com/
```

### 27. Service Status

```bash
# Check all services
sudo systemctl status escrow-backend
sudo systemctl status escrow-celery-worker
sudo systemctl status escrow-celery-beat
sudo systemctl status escrow-frontend
sudo systemctl status postgresql
sudo systemctl status redis
sudo systemctl status nginx
```

---

## Backup & Recovery

### 28. Automated Backups

Setup automated daily backups:

```bash
# Make backup script executable
sudo chmod +x /opt/escrow/scripts/backup.sh

# Add to crontab
sudo crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /opt/escrow/scripts/backup.sh >> /var/log/escrow-backup.log 2>&1
```

### 29. Manual Backup

```bash
sudo bash /opt/escrow/scripts/backup.sh
```

### 30. Restore from Backup

```bash
sudo bash /opt/escrow/scripts/restore.sh
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable firewall (UFW)
- [ ] Setup fail2ban
- [ ] Enable SSL/TLS
- [ ] Configure CORS properly
- [ ] Setup automated backups
- [ ] Enable monitoring (Sentry)
- [ ] Regular security updates
- [ ] Review audit logs regularly
- [ ] Implement rate limiting
- [ ] Use environment variables for secrets
- [ ] Restrict database access
- [ ] Enable 2FA for admin accounts

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u escrow-backend -n 50

# Check configuration
sudo nginx -t
python manage.py check --deploy
```

### Database Connection Issues

```bash
# Check PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"

# Test connection
psql -U escrow -d escrow_prod -h localhost
```

### High Memory Usage

```bash
# Check memory
free -h
htop

# Restart services
sudo systemctl restart escrow-backend
sudo systemctl restart escrow-celery-worker
```

---

## Performance Optimization

### Database

```bash
# Vacuum database
sudo -u postgres psql escrow_prod -c "VACUUM ANALYZE;"

# Check slow queries
sudo -u postgres psql escrow_prod -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Nginx Caching

Add to Nginx config:

```nginx
# Cache static files
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## Scaling

### Horizontal Scaling

1. Add load balancer (HAProxy/Nginx)
2. Scale backend workers (increase Gunicorn workers)
3. Scale Celery workers (multiple instances)
4. Setup PostgreSQL replication
5. Setup Redis cluster

### Vertical Scaling

1. Increase server resources
2. Optimize database queries
3. Add database indexes
4. Implement caching (Redis)

---

**Last Updated:** April 23, 2026  
**Version:** 2.0.0 (Native Deployment)
