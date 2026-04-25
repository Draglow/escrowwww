# Deployment Guide - Crypto Escrow Platform

This guide covers deploying the Crypto Escrow Platform to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [SSL Certificate Setup](#ssl-certificate-setup)
4. [Environment Configuration](#environment-configuration)
5. [Initial Deployment](#initial-deployment)
6. [Continuous Deployment](#continuous-deployment)
7. [Monitoring](#monitoring)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Server Requirements

**Minimum Specifications:**
- **CPU:** 4 cores
- **RAM:** 8 GB
- **Storage:** 100 GB SSD
- **OS:** Ubuntu 22.04 LTS or later

**Recommended Specifications (Production):**
- **CPU:** 8 cores
- **RAM:** 16 GB
- **Storage:** 200 GB SSD
- **OS:** Ubuntu 22.04 LTS

### Required Software

- Docker 24.0+
- Docker Compose 2.20+
- Git
- Nginx (handled by Docker)
- Certbot (for SSL)

### Domain Names

You'll need two domain names:
- `escrow.example.com` - Frontend
- `api.escrow.example.com` - Backend API

---

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl git ufw fail2ban

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### 2. Create Application Directory

```bash
sudo mkdir -p /opt/escrow
sudo chown $USER:$USER /opt/escrow
cd /opt/escrow
```

### 3. Clone Repository

```bash
# For production
git clone https://github.com/yourusername/escrow-platform.git .
git checkout main

# For staging
git checkout develop
```

---

## SSL Certificate Setup

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot

# Stop nginx if running
docker-compose -f docker-compose.prod.yml stop nginx

# Obtain certificates
sudo certbot certonly --standalone -d escrow.example.com
sudo certbot certonly --standalone -d api.escrow.example.com

# Certificates will be stored in:
# /etc/letsencrypt/live/escrow.example.com/
# /etc/letsencrypt/live/api.escrow.example.com/

# Copy certificates to project directory
sudo mkdir -p /opt/escrow/certbot/conf
sudo cp -r /etc/letsencrypt/* /opt/escrow/certbot/conf/

# Set up auto-renewal
sudo crontab -e
# Add this line:
0 0 * * * certbot renew --quiet && docker-compose -f /opt/escrow/docker-compose.prod.yml restart nginx
```

### Using Custom SSL Certificates

If you have your own SSL certificates:

```bash
sudo mkdir -p /opt/escrow/certbot/conf/live/escrow.example.com
sudo mkdir -p /opt/escrow/certbot/conf/live/api.escrow.example.com

# Copy your certificates
sudo cp your-cert.pem /opt/escrow/certbot/conf/live/escrow.example.com/fullchain.pem
sudo cp your-key.pem /opt/escrow/certbot/conf/live/escrow.example.com/privkey.pem
# Repeat for api.escrow.example.com
```

---

## Environment Configuration

### 1. Create Production Environment File

```bash
cd /opt/escrow
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with production values:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=api.escrow.example.com,escrow.example.com
CORS_ALLOWED_ORIGINS=https://escrow.example.com
CSRF_TRUSTED_ORIGINS=https://escrow.example.com,https://api.escrow.example.com

# Database
POSTGRES_DB=escrow_prod
POSTGRES_USER=escrow
POSTGRES_PASSWORD=your-strong-database-password

# Redis
REDIS_PASSWORD=your-strong-redis-password

# Tron Blockchain
TRON_API_KEY=your-trongrid-api-key
TRON_NETWORK=mainnet

# Platform Settings
PLATFORM_FEE_PERCENTAGE=2.5

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
NEXT_PUBLIC_TELEGRAM_BOT_NAME=YourBotName

# Frontend
NEXT_PUBLIC_API_URL=https://api.escrow.example.com
NEXT_PUBLIC_WS_URL=wss://api.escrow.example.com

# Docker Registry
DOCKER_USERNAME=your-dockerhub-username

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
```

### 3. Generate Secret Key

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Initial Deployment

### 1. Update Nginx Configuration

Edit `nginx/conf.d/escrow.conf` and replace `escrow.example.com` and `api.escrow.example.com` with your actual domain names.

### 2. Build and Start Services

```bash
cd /opt/escrow

# Pull latest images (if using Docker Hub)
docker-compose -f docker-compose.prod.yml pull

# Or build locally
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 3. Run Database Migrations

```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### 4. Create Superuser

```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### 5. Collect Static Files

```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### 6. Verify Deployment

```bash
# Check backend health
curl https://api.escrow.example.com/api/v1/health/

# Check frontend
curl https://escrow.example.com/

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Continuous Deployment

### Using GitHub Actions

The project includes a CI/CD pipeline (`.github/workflows/ci-cd.yml`) that automatically:

1. Runs tests on push/PR
2. Builds Docker images
3. Deploys to staging (develop branch)
4. Deploys to production (main branch)

**Setup GitHub Secrets:**

Go to your repository → Settings → Secrets and add:

```
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-password
STAGING_HOST=staging.escrow.example.com
STAGING_USER=deploy
STAGING_SSH_KEY=<your-ssh-private-key>
PRODUCTION_HOST=escrow.example.com
PRODUCTION_USER=deploy
PRODUCTION_SSH_KEY=<your-ssh-private-key>
NEXT_PUBLIC_API_URL=https://api.escrow.example.com
SLACK_WEBHOOK=<your-slack-webhook-url>
```

### Manual Deployment

Use the deployment script:

```bash
# Deploy to staging
sudo bash scripts/deploy.sh staging

# Deploy to production
sudo bash scripts/deploy.sh production
```

The script will:
1. Create database backup
2. Pull latest code
3. Pull Docker images
4. Restart services
5. Run migrations
6. Collect static files
7. Perform health checks
8. Clean up old images

---

## Monitoring

### Health Check Endpoints

- **Basic:** `https://api.escrow.example.com/api/v1/health/`
- **Detailed:** `https://api.escrow.example.com/api/v1/health/detailed/`
- **Readiness:** `https://api.escrow.example.com/api/v1/health/ready/`
- **Liveness:** `https://api.escrow.example.com/api/v1/health/live/`

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f celery
docker-compose -f docker-compose.prod.yml logs -f nginx

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Monitor Resources

```bash
# Container stats
docker stats

# Disk usage
df -h
docker system df

# Database size
docker-compose -f docker-compose.prod.yml exec postgres psql -U escrow -c "SELECT pg_size_pretty(pg_database_size('escrow_prod'));"
```

### Setup Monitoring Tools (Optional)

**Prometheus + Grafana:**

```bash
# Add to docker-compose.prod.yml
# See monitoring/docker-compose.monitoring.yml for full setup
```

**Sentry for Error Tracking:**

1. Sign up at https://sentry.io
2. Create a new project
3. Add SENTRY_DSN to `.env`
4. Restart services

---

## Backup & Recovery

### Automated Backups

Setup automated daily backups:

```bash
# Make backup script executable
chmod +x scripts/backup.sh

# Add to crontab
sudo crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /opt/escrow/scripts/backup.sh >> /var/log/escrow-backup.log 2>&1
```

### Manual Backup

```bash
sudo bash scripts/backup.sh
```

Backups are stored in `/opt/escrow/backups/`:
- `db/` - Database backups
- `media/` - Media files
- `config/` - Configuration files

### Restore from Backup

```bash
sudo bash scripts/restore.sh
```

Follow the prompts to select and restore a backup.

### Remote Backup (Recommended)

Configure AWS S3 or similar:

```bash
# Install AWS CLI
sudo apt install -y awscli

# Configure AWS credentials
aws configure

# Modify scripts/backup.sh to enable S3 sync
# Uncomment the S3 upload section
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check specific service
docker-compose -f docker-compose.prod.yml logs backend

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Rebuild if needed
docker-compose -f docker-compose.prod.yml up -d --build
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U escrow escrow_prod
```

### Celery Not Processing Tasks

```bash
# Check Celery worker status
docker-compose -f docker-compose.prod.yml logs celery

# Restart Celery
docker-compose -f docker-compose.prod.yml restart celery celery-beat

# Check Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### SSL Certificate Issues

```bash
# Check certificate expiry
sudo certbot certificates

# Renew certificates manually
sudo certbot renew

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### High Memory Usage

```bash
# Check container memory
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Clear Docker cache
docker system prune -a
```

### Database Performance Issues

```bash
# Check database size
docker-compose -f docker-compose.prod.yml exec postgres psql -U escrow -c "\l+"

# Vacuum database
docker-compose -f docker-compose.prod.yml exec postgres psql -U escrow escrow_prod -c "VACUUM ANALYZE;"

# Check slow queries (if logging enabled)
docker-compose -f docker-compose.prod.yml exec postgres psql -U escrow escrow_prod -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
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
- [ ] Enable monitoring
- [ ] Regular security updates
- [ ] Review audit logs regularly
- [ ] Implement rate limiting
- [ ] Use environment variables for secrets
- [ ] Restrict database access
- [ ] Enable 2FA for admin accounts

---

## Performance Optimization

### Database Optimization

```bash
# Add indexes (already in migrations)
# Increase shared_buffers in PostgreSQL config
# Enable query logging for slow queries
```

### Redis Optimization

```bash
# Configure maxmemory policy
# Enable persistence if needed
# Monitor memory usage
```

### Nginx Optimization

```bash
# Enable gzip compression (already configured)
# Configure caching headers
# Increase worker_connections if needed
```

---

## Scaling

### Horizontal Scaling

1. **Load Balancer:** Add HAProxy or AWS ELB
2. **Multiple Backend Instances:** Scale backend and celery workers
3. **Database Replication:** Setup PostgreSQL read replicas
4. **Redis Cluster:** Setup Redis cluster for high availability

### Vertical Scaling

1. Increase server resources (CPU, RAM)
2. Optimize database queries
3. Add database indexes
4. Implement caching strategies

---

## Support

For issues and questions:
- Check logs: `docker-compose -f docker-compose.prod.yml logs`
- Review documentation: `README.md`, `API_DOCUMENTATION.md`
- Check health endpoints
- Review audit logs in admin panel

---

**Last Updated:** April 22, 2026  
**Version:** 1.0.0
