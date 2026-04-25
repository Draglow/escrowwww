# Quick Reference Guide - Crypto Escrow Platform

Quick commands and references for common operations.

---

## 🚀 Development

### Start Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Backend Commands

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Django shell
docker-compose exec backend python manage.py shell

# Collect static files
docker-compose exec backend python manage.py collectstatic

# Run Celery worker (manual)
docker-compose exec backend celery -A config worker -l info

# Check Celery status
docker-compose exec backend celery -A config inspect ping
```

### Frontend Commands

```bash
# Install dependencies
cd frontend && npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint

# Type check
npx tsc --noEmit
```

### Database Commands

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U escrow escrow_dev

# Backup database
docker-compose exec postgres pg_dump -U escrow escrow_dev > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U escrow escrow_dev

# Check database size
docker-compose exec postgres psql -U escrow -c "SELECT pg_size_pretty(pg_database_size('escrow_dev'));"
```

### Redis Commands

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check Redis info
docker-compose exec redis redis-cli INFO

# Monitor Redis commands
docker-compose exec redis redis-cli MONITOR

# Flush all data (DANGER!)
docker-compose exec redis redis-cli FLUSHALL
```

---

## 🚀 Production Deployment

### Initial Deployment

```bash
# 1. Clone repository
git clone https://github.com/yourusername/escrow-platform.git
cd escrow-platform

# 2. Configure environment
cp .env.production.example .env
nano .env

# 3. Deploy
sudo bash scripts/deploy.sh production
```

### Update Deployment

```bash
# Pull latest changes
git pull origin main

# Deploy
sudo bash scripts/deploy.sh production
```

### Service Management

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

---

## 🔍 Monitoring

### Health Checks

```bash
# Basic health check
curl https://api.escrow.example.com/api/v1/health/

# Detailed health check
curl https://api.escrow.example.com/api/v1/health/detailed/

# Readiness check
curl https://api.escrow.example.com/api/v1/health/ready/

# Liveness check
curl https://api.escrow.example.com/api/v1/health/live/
```

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

# Follow logs with timestamp
docker-compose -f docker-compose.prod.yml logs -f -t backend
```

### Resource Monitoring

```bash
# Container stats
docker stats

# Disk usage
df -h
docker system df

# Memory usage
free -h

# CPU usage
top
htop
```

---

## 💾 Backup & Restore

### Backup

```bash
# Manual backup
sudo bash scripts/backup.sh

# Setup automated daily backups
sudo crontab -e
# Add: 0 2 * * * /opt/escrow/scripts/backup.sh >> /var/log/escrow-backup.log 2>&1

# List backups
ls -lh /opt/escrow/backups/db/
ls -lh /opt/escrow/backups/media/
```

### Restore

```bash
# Interactive restore
sudo bash scripts/restore.sh

# Manual database restore
gunzip -c /opt/escrow/backups/db/db_backup_TIMESTAMP.sql.gz | \
  docker-compose -f docker-compose.prod.yml exec -T postgres psql -U escrow escrow_prod
```

---

## 🔒 Security

### SSL Certificate Management

```bash
# Check certificate expiry
sudo certbot certificates

# Renew certificates manually
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run

# Restart nginx after renewal
docker-compose -f docker-compose.prod.yml restart nginx
```

### User Management

```bash
# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Change user password
docker-compose exec backend python manage.py changepassword username

# List users
docker-compose exec backend python manage.py shell
>>> from apps.users.models import User
>>> User.objects.all()
```

### Audit Logs

```bash
# View audit logs via API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.escrow.example.com/api/v1/users/audit_logs/

# View in database
docker-compose exec postgres psql -U escrow escrow_prod \
  -c "SELECT * FROM users_auditlog ORDER BY created_at DESC LIMIT 10;"
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Check if port is in use
sudo lsof -i :8000
sudo lsof -i :5432

# Restart service
docker-compose restart backend

# Rebuild if needed
docker-compose up -d --build backend
```

### Database Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U escrow escrow_dev

# Check connections
docker-compose exec postgres psql -U escrow -c \
  "SELECT count(*) FROM pg_stat_activity;"
```

### Celery Issues

```bash
# Check Celery worker status
docker-compose logs celery

# Restart Celery
docker-compose restart celery celery-beat

# Check Redis connection
docker-compose exec redis redis-cli ping

# Purge Celery queue
docker-compose exec backend celery -A config purge
```

### Frontend Issues

```bash
# Check build errors
cd frontend && npm run build

# Clear Next.js cache
rm -rf frontend/.next

# Reinstall dependencies
cd frontend && rm -rf node_modules && npm install

# Check environment variables
cat frontend/.env.local
```

### Nginx Issues

```bash
# Test nginx configuration
docker-compose exec nginx nginx -t

# Reload nginx
docker-compose exec nginx nginx -s reload

# Check nginx logs
docker-compose logs nginx

# Check SSL certificates
docker-compose exec nginx ls -la /etc/letsencrypt/live/
```

---

## 📊 Database Queries

### User Statistics

```sql
-- Total users
SELECT COUNT(*) FROM users_user;

-- Users with 2FA enabled
SELECT COUNT(*) FROM users_user WHERE is_2fa_enabled = true;

-- Recent registrations
SELECT id, telegram_username, created_at 
FROM users_user 
ORDER BY created_at DESC 
LIMIT 10;
```

### Deal Statistics

```sql
-- Total deals
SELECT COUNT(*) FROM deals_deal;

-- Deals by status
SELECT status, COUNT(*) 
FROM deals_deal 
GROUP BY status;

-- Recent deals
SELECT id, title, status, amount, created_at 
FROM deals_deal 
ORDER BY created_at DESC 
LIMIT 10;

-- Total volume
SELECT SUM(amount) FROM deals_deal WHERE status = 'COMPLETED';
```

### Transaction Statistics

```sql
-- Total transactions
SELECT COUNT(*) FROM ledger_ledgerentry;

-- Transactions by type
SELECT transaction_type, COUNT(*) 
FROM ledger_ledgerentry 
GROUP BY transaction_type;

-- Recent transactions
SELECT id, transaction_type, amount, created_at 
FROM ledger_ledgerentry 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## 🔧 Maintenance

### Daily Tasks

```bash
# Check health
curl https://api.escrow.example.com/api/v1/health/detailed/

# Check disk space
df -h

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=100 | grep -i error
```

### Weekly Tasks

```bash
# Review audit logs
# Check backup integrity
ls -lh /opt/escrow/backups/db/

# Update dependencies (if needed)
cd backend && pip list --outdated
cd frontend && npm outdated

# Check resource usage
docker stats --no-stream
```

### Monthly Tasks

```bash
# Database optimization
docker-compose exec postgres psql -U escrow escrow_prod -c "VACUUM ANALYZE;"

# Clean old Docker images
docker image prune -a

# Review and rotate logs
sudo logrotate -f /etc/logrotate.conf

# Security updates
sudo apt update && sudo apt upgrade
```

---

## 📝 API Quick Reference

### Authentication

```bash
# Login
curl -X POST https://api.escrow.example.com/api/v1/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"telegram_data": "..."}'

# Get current user
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.escrow.example.com/api/v1/users/me/
```

### Wallet Operations

```bash
# Get balance
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.escrow.example.com/api/v1/wallets/balance/

# Get deposit address
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.escrow.example.com/api/v1/wallets/deposit_address/

# Withdraw
curl -X POST https://api.escrow.example.com/api/v1/wallets/withdraw/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_address": "...", "amount": "100.00", "totp_code": "123456"}'
```

### Deal Operations

```bash
# List deals
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.escrow.example.com/api/v1/deals/

# Create deal
curl -X POST https://api.escrow.example.com/api/v1/deals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "...", "description": "...", "amount": "100.00", "buyer_id": "..."}'

# Fund deal
curl -X POST https://api.escrow.example.com/api/v1/deals/{id}/fund/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🌐 Environment Variables

### Required Variables

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=api.escrow.example.com

# Database
POSTGRES_PASSWORD=your-db-password
DATABASE_URL=postgresql://...

# Redis
REDIS_PASSWORD=your-redis-password

# Tron
TRON_API_KEY=your-tron-api-key
TRON_NETWORK=mainnet

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
```

### Optional Variables

```bash
# Monitoring
SENTRY_DSN=your-sentry-dsn

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password

# AWS S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

---

## 🔗 Useful Links

### Documentation
- API Documentation: `/API_DOCUMENTATION.md`
- Deployment Guide: `/DEPLOYMENT.md`
- Architecture: `/ARCHITECTURE.md`
- Project Status: `/PROJECT_STATUS.md`

### Admin Panels
- Django Admin: `https://api.escrow.example.com/admin/`
- Frontend: `https://escrow.example.com/`

### Monitoring
- Health Check: `https://api.escrow.example.com/api/v1/health/`
- Sentry: `https://sentry.io/`

### External Services
- TronGrid: `https://www.trongrid.io/`
- Telegram Bot: `https://t.me/BotFather`
- Let's Encrypt: `https://letsencrypt.org/`

---

## 📞 Support

### Getting Help

1. Check logs: `docker-compose logs -f`
2. Review documentation in `/docs`
3. Check health endpoints
4. Review audit logs in admin panel

### Common Issues

- **Service won't start**: Check logs and environment variables
- **Database connection failed**: Verify PostgreSQL is running
- **Celery not processing**: Check Redis connection
- **SSL certificate expired**: Run `certbot renew`
- **High memory usage**: Restart services or increase resources

---

**Last Updated:** April 22, 2026  
**Version:** 1.0.0
