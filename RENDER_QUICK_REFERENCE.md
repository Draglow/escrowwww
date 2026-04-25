# Render Quick Reference Guide

Quick reference for common Render operations and commands.

## 🚀 Deployment Commands

### Initial Deployment
```bash
# 1. Commit and push your code
git add .
git commit -m "Prepare for Render deployment"
git push origin main

# 2. In Render Dashboard:
# - New → Blueprint
# - Select repository
# - Configure environment variables
# - Click "Apply"
```

### Manual Redeploy
```bash
# In Render Dashboard:
# Service → Manual Deploy → Deploy latest commit
```

### Rollback
```bash
# In Render Dashboard:
# Service → Events → Find previous deploy → Rollback
```

---

## 🔧 Service Management

### View Logs
```bash
# In Render Dashboard:
# Service → Logs

# Or use Render CLI:
render logs <service-name>
```

### Access Shell
```bash
# In Render Dashboard:
# Service → Shell

# Common commands in shell:
cd backend
python manage.py shell
python manage.py dbshell
celery -A config inspect ping
```

### Restart Service
```bash
# In Render Dashboard:
# Service → Manual Deploy → Clear build cache & deploy
```

---

## 💾 Database Operations

### Run Migrations
```bash
# Migrations run automatically on deploy
# To run manually in shell:
cd backend
python manage.py migrate
```

### Create Superuser
```bash
# In backend shell:
cd backend
python manage.py createsuperuser
```

### Database Backup
```bash
# In Render Dashboard:
# Database → Backups → Create Backup
```

### Restore Database
```bash
# In Render Dashboard:
# Database → Backups → Select backup → Restore
```

### Connect to Database
```bash
# In Render Dashboard:
# Database → Connect → Copy connection string

# Or in backend shell:
cd backend
python manage.py dbshell
```

---

## 🔍 Debugging

### Check Service Health
```bash
# Backend health check:
curl https://your-backend.onrender.com/api/v1/health/

# Detailed health check:
curl https://your-backend.onrender.com/api/v1/health/detailed/
```

### View Environment Variables
```bash
# In service shell:
env | grep -i secret
env | grep -i database
env | grep -i redis
```

### Test Database Connection
```bash
# In backend shell:
cd backend
python manage.py check --database default
```

### Test Redis Connection
```bash
# In backend shell:
cd backend
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')
```

### Test Celery
```bash
# In backend shell:
cd backend
celery -A config inspect ping
celery -A config inspect active
celery -A config inspect stats
```

---

## 🔐 Security Operations

### Rotate Secret Keys
```bash
# 1. Generate new keys:
python scripts/generate_keys.py

# 2. Update in Render:
# Service → Environment → Update SECRET_KEY
# Service → Environment → Update WALLET_ENCRYPTION_KEY

# 3. Redeploy all services
```

### Update SSL Certificate
```bash
# Automatic with Render
# Certificates auto-renew every 90 days
```

### Configure Custom Domain
```bash
# In Render Dashboard:
# Service → Settings → Custom Domain
# Add domain: api.yourdomain.com
# Update DNS records as shown
# Wait for SSL certificate provisioning
```

---

## 📊 Monitoring

### View Metrics
```bash
# In Render Dashboard:
# Service → Metrics
# - CPU usage
# - Memory usage
# - Request count
# - Response times
```

### Set Up Alerts
```bash
# In Render Dashboard:
# Service → Notifications
# Add notification channels:
# - Email
# - Slack
# - Discord
```

### Check Service Status
```bash
# Status page:
https://status.render.com/

# Service uptime:
# Dashboard → Service → Metrics
```

---

## 🔄 Celery Management

### View Active Tasks
```bash
# In worker shell:
cd backend
celery -A config inspect active
```

### View Scheduled Tasks
```bash
# In backend shell:
cd backend
python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()
```

### Purge Queue
```bash
# In worker shell:
cd backend
celery -A config purge
```

### Restart Worker
```bash
# In Render Dashboard:
# escrow-celery-worker → Manual Deploy
```

---

## 🗄️ Data Management

### Export Data
```bash
# In backend shell:
cd backend
python manage.py dumpdata > backup.json
python manage.py dumpdata users > users.json
python manage.py dumpdata deals > deals.json
```

### Import Data
```bash
# In backend shell:
cd backend
python manage.py loaddata backup.json
```

### Clear Cache
```bash
# In backend shell:
cd backend
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## 🧪 Testing in Production

### Run Health Checks
```bash
# Basic health:
curl https://your-backend.onrender.com/api/v1/health/

# Detailed health:
curl https://your-backend.onrender.com/api/v1/health/detailed/

# Readiness:
curl https://your-backend.onrender.com/api/v1/health/ready/

# Liveness:
curl https://your-backend.onrender.com/api/v1/health/live/
```

### Test API Endpoints
```bash
# Get user profile (requires auth):
curl -H "Authorization: Telegram <auth-data>" \
  https://your-backend.onrender.com/api/v1/users/me/

# List deals:
curl -H "Authorization: Telegram <auth-data>" \
  https://your-backend.onrender.com/api/v1/deals/
```

### Test WebSocket
```javascript
// In browser console:
const ws = new WebSocket('wss://your-backend.onrender.com/ws/deals/');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
ws.onerror = (e) => console.error('Error:', e);
```

---

## 📦 Scaling

### Upgrade Service Plan
```bash
# In Render Dashboard:
# Service → Settings → Instance Type
# Select: Starter / Standard / Pro
```

### Add More Workers
```bash
# In Render Dashboard:
# New → Background Worker
# Use same configuration as existing worker
```

### Enable Autoscaling
```bash
# Available on Pro plans
# Service → Settings → Autoscaling
# Set min/max instances
```

---

## 🔧 Configuration Updates

### Update Environment Variable
```bash
# In Render Dashboard:
# Service → Environment
# Edit variable → Save
# Service auto-redeploys
```

### Update Build Command
```bash
# In Render Dashboard:
# Service → Settings → Build Command
# Update command → Save Changes
```

### Update Start Command
```bash
# In Render Dashboard:
# Service → Settings → Start Command
# Update command → Save Changes
```

---

## 🆘 Emergency Procedures

### Service Down
```bash
# 1. Check status:
https://status.render.com/

# 2. View logs:
Dashboard → Service → Logs

# 3. Check health:
curl https://your-backend.onrender.com/api/v1/health/

# 4. Restart service:
Dashboard → Service → Manual Deploy
```

### Database Issues
```bash
# 1. Check database status:
Dashboard → Database → Metrics

# 2. View database logs:
Dashboard → Database → Logs

# 3. Restore from backup:
Dashboard → Database → Backups → Restore
```

### High Memory Usage
```bash
# 1. Check metrics:
Dashboard → Service → Metrics

# 2. Restart service:
Dashboard → Service → Manual Deploy

# 3. Upgrade plan if needed:
Dashboard → Service → Settings → Instance Type
```

---

## 📱 Render CLI

### Install Render CLI
```bash
# macOS/Linux:
brew install render

# Or download from:
https://render.com/docs/cli
```

### Login
```bash
render login
```

### List Services
```bash
render services list
```

### View Logs
```bash
render logs <service-name>
```

### Deploy
```bash
render deploy <service-name>
```

---

## 🔗 Useful URLs

### Render Dashboard
```
https://dashboard.render.com/
```

### Service URLs (replace with yours)
```
Backend:  https://escrow-backend-xxxx.onrender.com
Frontend: https://escrow-frontend-xxxx.onrender.com
Admin:    https://escrow-backend-xxxx.onrender.com/admin/
```

### Documentation
```
Render Docs:     https://render.com/docs
Django Docs:     https://docs.djangoproject.com/
Next.js Docs:    https://nextjs.org/docs
Celery Docs:     https://docs.celeryproject.org/
```

---

## 💡 Pro Tips

### 1. Use Environment Groups
Create environment groups for shared variables across services.

### 2. Enable Preview Environments
Automatically deploy pull requests for testing.

### 3. Set Up Notifications
Get alerts for deploy failures and service issues.

### 4. Use Health Checks
Configure health check paths for automatic restarts.

### 5. Monitor Costs
Check billing dashboard regularly to avoid surprises.

### 6. Keep Logs
Download logs periodically for compliance.

### 7. Test Backups
Regularly test database restore procedures.

### 8. Document Changes
Keep a changelog of configuration updates.

### 9. Use Staging Environment
Deploy to staging before production.

### 10. Monitor Performance
Set up external monitoring (UptimeRobot, Pingdom).

---

## 📞 Support

### Render Support
- Email: support@render.com
- Community: https://community.render.com/
- Status: https://status.render.com/

### Documentation
- Render Docs: https://render.com/docs
- API Reference: https://api-docs.render.com/

---

**Last Updated**: [Current Date]
**Version**: 1.0
