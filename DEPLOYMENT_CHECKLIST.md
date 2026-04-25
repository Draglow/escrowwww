# Deployment Checklist for Render

Use this checklist to ensure a smooth deployment to Render.

## Pre-Deployment

### 1. Code Preparation
- [ ] All code committed and pushed to GitHub
- [ ] `.env` files are in `.gitignore`
- [ ] No sensitive data in repository
- [ ] All tests passing locally
- [ ] Database migrations created and tested

### 2. API Keys & Credentials
- [ ] TronGrid API key obtained from [trongrid.io](https://www.trongrid.io/)
- [ ] Telegram bot created via [@BotFather](https://t.me/botfather)
- [ ] Telegram bot token saved securely
- [ ] Generated strong `SECRET_KEY` for Django
- [ ] Generated `WALLET_ENCRYPTION_KEY` using Fernet

### 3. Domain Setup (Optional)
- [ ] Domain purchased and DNS configured
- [ ] Subdomain for API (e.g., `api.yourdomain.com`)
- [ ] Subdomain for frontend (e.g., `app.yourdomain.com`)

## Deployment Steps

### 1. Render Account Setup
- [ ] Signed up at [render.com](https://render.com)
- [ ] Connected GitHub account
- [ ] Repository access granted to Render

### 2. Blueprint Deployment
- [ ] Created new Blueprint in Render
- [ ] Selected correct repository
- [ ] `render.yaml` detected successfully
- [ ] Reviewed service configuration

### 3. Environment Variables Configuration

#### Backend Service
- [ ] `ALLOWED_HOSTS` - Set to backend and frontend URLs
- [ ] `CORS_ALLOWED_ORIGINS` - Set to frontend URL
- [ ] `TRONGRID_API_KEY` - Your TronGrid API key
- [ ] `TELEGRAM_BOT_TOKEN` - Your bot token
- [ ] `WEBAUTHN_RP_ID` - Frontend domain (without https://)
- [ ] `WEBAUTHN_ALLOWED_ORIGINS` - Frontend URL with https://
- [ ] `FRONTEND_URL` - Full frontend URL
- [ ] `SECRET_KEY` - Auto-generated (verify it exists)
- [ ] `WALLET_ENCRYPTION_KEY` - Auto-generated (verify it exists)
- [ ] `DATABASE_URL` - Auto-linked from PostgreSQL
- [ ] `REDIS_URL` - Auto-linked from Redis

#### Frontend Service
- [ ] `NEXT_PUBLIC_API_URL` - Backend URL (https://...)
- [ ] `NEXT_PUBLIC_WS_URL` - Backend WebSocket URL (wss://...)
- [ ] `NEXT_PUBLIC_TELEGRAM_BOT_NAME` - Your bot username
- [ ] `NEXT_PUBLIC_APP_URL` - Frontend URL
- [ ] `NEXT_PUBLIC_WEBAUTHN_RP_ID` - Frontend domain

#### Celery Worker
- [ ] `TRONGRID_API_KEY` - Same as backend
- [ ] `TELEGRAM_BOT_TOKEN` - Same as backend
- [ ] All other variables auto-synced from backend

### 4. Service Deployment
- [ ] PostgreSQL database created and running
- [ ] Redis instance created and running
- [ ] Backend service deployed successfully
- [ ] Celery worker deployed successfully
- [ ] Celery beat deployed successfully (if using scheduled tasks)
- [ ] Frontend service deployed successfully

## Post-Deployment

### 1. Database Setup
- [ ] Migrations applied automatically
- [ ] Django superuser created via shell
- [ ] Test data created (optional)

### 2. Service Verification
- [ ] Backend health check: `https://your-backend.onrender.com/api/v1/health/`
- [ ] Backend admin panel accessible: `https://your-backend.onrender.com/admin/`
- [ ] Frontend loads: `https://your-frontend.onrender.com`
- [ ] API endpoints responding correctly
- [ ] WebSocket connections working

### 3. Telegram Bot Configuration
- [ ] Bot webhook set to backend URL
- [ ] Bot commands configured
- [ ] Test authentication flow
- [ ] Verify bot responds to messages

### 4. Security Verification
- [ ] All URLs using HTTPS
- [ ] WebSocket using WSS
- [ ] CORS configured correctly
- [ ] CSRF protection enabled
- [ ] Rate limiting working
- [ ] No sensitive data in logs

### 5. Functionality Testing
- [ ] User registration works
- [ ] Telegram login works
- [ ] Passkey registration works (if enabled)
- [ ] Wallet creation works
- [ ] Deal creation works
- [ ] Deal funding works
- [ ] Deal completion works
- [ ] Transaction history displays
- [ ] WebSocket notifications work

### 6. Monitoring Setup
- [ ] Logs accessible in Render dashboard
- [ ] Error tracking configured (Sentry, optional)
- [ ] Database backups enabled
- [ ] Uptime monitoring configured (optional)

### 7. Performance Optimization
- [ ] Static files served correctly
- [ ] Database queries optimized
- [ ] Redis caching working
- [ ] Response times acceptable
- [ ] No memory leaks detected

## Production Readiness

### 1. Documentation
- [ ] API documentation updated with production URLs
- [ ] User guide created
- [ ] Admin guide created
- [ ] Deployment documentation complete

### 2. Backup & Recovery
- [ ] Database backup schedule configured
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented

### 3. Scaling Preparation
- [ ] Service plans appropriate for expected load
- [ ] Autoscaling configured (if needed)
- [ ] CDN configured for static assets (optional)
- [ ] Load testing performed

### 4. Legal & Compliance
- [ ] Terms of service created
- [ ] Privacy policy created
- [ ] Cookie policy created (if applicable)
- [ ] GDPR compliance verified (if applicable)
- [ ] KYC/AML requirements addressed

## Maintenance

### Regular Tasks
- [ ] Monitor service health daily
- [ ] Review logs weekly
- [ ] Check database size weekly
- [ ] Review error rates weekly
- [ ] Update dependencies monthly
- [ ] Security audit quarterly

### Emergency Contacts
- [ ] Render support: support@render.com
- [ ] Team contact list created
- [ ] Escalation procedures documented

## Rollback Plan

In case of deployment issues:

1. **Immediate Actions**:
   - [ ] Identify the issue from logs
   - [ ] Determine if rollback needed
   - [ ] Notify team members

2. **Rollback Steps**:
   - [ ] Revert to previous Git commit
   - [ ] Trigger manual deploy in Render
   - [ ] Verify services are healthy
   - [ ] Check database integrity

3. **Post-Rollback**:
   - [ ] Document what went wrong
   - [ ] Fix issues in development
   - [ ] Test thoroughly before redeploying

## Notes

- Keep this checklist updated as your deployment process evolves
- Document any custom steps specific to your setup
- Share with team members involved in deployment
- Review and update after each deployment

## Useful Commands

### Create Django Superuser
```bash
# In Render Shell
cd backend
python manage.py createsuperuser
```

### Check Service Status
```bash
# In Render Shell
cd backend
python manage.py check --deploy
```

### View Database Migrations
```bash
# In Render Shell
cd backend
python manage.py showmigrations
```

### Test Celery Connection
```bash
# In Render Shell
cd backend
celery -A config inspect ping
```

### Generate Encryption Key
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Generate Django Secret Key
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## Support Resources

- **Render Docs**: https://render.com/docs
- **Django Docs**: https://docs.djangoproject.com/
- **Next.js Docs**: https://nextjs.org/docs
- **Celery Docs**: https://docs.celeryproject.org/
- **TronGrid Docs**: https://developers.tron.network/

---

**Last Updated**: [Add date when you complete deployment]
**Deployed By**: [Your name]
**Production URL**: [Your production URL]
