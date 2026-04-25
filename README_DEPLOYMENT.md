# Crypto Escrow Platform - Render Deployment

Complete deployment package for hosting your Crypto Escrow Platform on Render.com.

## 📦 What's Included

This deployment package includes everything you need to deploy to Render:

### Configuration Files
- ✅ `render.yaml` - Blueprint for all services
- ✅ `backend/runtime.txt` - Python version specification
- ✅ `backend/Procfile` - Process definitions
- ✅ `.renderignore` - Files to exclude from deployment

### Documentation
- 📘 `RENDER_DEPLOYMENT.md` - Complete deployment guide
- 📋 `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
- 📝 `RENDER_ENV_TEMPLATE.md` - Environment variables reference
- 🔍 `RENDER_QUICK_REFERENCE.md` - Common commands and operations
- 🆘 `RENDER_TROUBLESHOOTING.md` - Problem-solving guide

### Helper Scripts
- 🔑 `scripts/generate_keys.py` - Generate secure encryption keys
- 🚀 `scripts/render_setup.sh` - Setup script (Linux/Mac)
- 🚀 `scripts/render_setup.bat` - Setup script (Windows)

## 🚀 Quick Start

### 1. Run Setup Script

**Linux/Mac:**
```bash
chmod +x scripts/render_setup.sh
./scripts/render_setup.sh
```

**Windows:**
```bash
scripts\render_setup.bat
```

This will:
- Check prerequisites
- Generate secure keys
- Verify required files
- Show next steps

### 2. Get API Keys

Before deploying, obtain:

**TronGrid API Key:**
- Visit: https://www.trongrid.io/
- Sign up and create API key
- Save for later

**Telegram Bot Token:**
- Open Telegram, search `@BotFather`
- Send `/newbot` and follow prompts
- Save bot token and username

### 3. Deploy to Render

**Option A: Blueprint (Recommended)**
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render detects `render.yaml`
5. Configure environment variables (see `RENDER_ENV_TEMPLATE.md`)
6. Click "Apply"

**Option B: Manual**
Follow the detailed steps in `RENDER_DEPLOYMENT.md`

### 4. Configure Environment Variables

Use `RENDER_ENV_TEMPLATE.md` as your guide. Key variables:

**Backend:**
```bash
ALLOWED_HOSTS=your-backend.onrender.com,your-frontend.onrender.com
CORS_ALLOWED_ORIGINS=https://your-frontend.onrender.com
TRONGRID_API_KEY=your-api-key
TELEGRAM_BOT_TOKEN=your-bot-token
WEBAUTHN_RP_ID=your-frontend.onrender.com
```

**Frontend:**
```bash
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
NEXT_PUBLIC_WS_URL=wss://your-backend.onrender.com
NEXT_PUBLIC_TELEGRAM_BOT_NAME=your_bot_username
```

### 5. Verify Deployment

After deployment completes:

```bash
# Check backend health
curl https://your-backend.onrender.com/api/v1/health/

# Visit frontend
open https://your-frontend.onrender.com

# Access admin panel
open https://your-backend.onrender.com/admin/
```

## 📚 Documentation Guide

### For First-Time Deployment
1. Start with `RENDER_DEPLOYMENT.md` - Read the full guide
2. Use `DEPLOYMENT_CHECKLIST.md` - Track your progress
3. Reference `RENDER_ENV_TEMPLATE.md` - Set up variables
4. Keep `RENDER_QUICK_REFERENCE.md` - Handy for commands

### For Troubleshooting
1. Check `RENDER_TROUBLESHOOTING.md` - Common issues and solutions
2. Review service logs in Render Dashboard
3. Test with commands from `RENDER_QUICK_REFERENCE.md`

### For Ongoing Maintenance
1. Use `RENDER_QUICK_REFERENCE.md` - Daily operations
2. Follow `DEPLOYMENT_CHECKLIST.md` - For updates
3. Refer to `RENDER_TROUBLESHOOTING.md` - When issues arise

## 🏗️ Architecture on Render

Your deployment will create these services:

```
┌─────────────────────────────────────────────────────┐
│                   Render Platform                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────┐         ┌──────────────┐         │
│  │  PostgreSQL  │◄────────┤   Backend    │         │
│  │   Database   │         │  (Django +   │         │
│  └──────────────┘         │   Daphne)    │         │
│                            └──────▲───────┘         │
│  ┌──────────────┐                │                  │
│  │    Redis     │◄───────────────┤                  │
│  │   Instance   │                │                  │
│  └──────────────┘         ┌──────┴───────┐         │
│         ▲                 │    Celery    │         │
│         │                 │    Worker    │         │
│         │                 └──────────────┘         │
│         │                                           │
│         │                 ┌──────────────┐         │
│         └─────────────────┤    Celery    │         │
│                           │     Beat     │         │
│                           └──────────────┘         │
│                                                     │
│                           ┌──────────────┐         │
│                           │   Frontend   │         │
│                           │  (Next.js)   │         │
│                           └──────────────┘         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 💰 Cost Estimation

### Development/Testing (~$31/month)
- PostgreSQL Starter: $7
- Redis Starter: $10
- Backend Web: $7
- Frontend Web: $7

### Production (~$109/month)
- PostgreSQL Standard: $20
- Redis Standard: $25
- Backend Web: $25
- Celery Worker: $7
- Celery Beat: $7
- Frontend Web: $25

### Free Tier Option
- Available but not recommended for production
- Services sleep after 15 minutes of inactivity
- 750 hours/month limit

## ✅ Pre-Deployment Checklist

- [ ] Code committed and pushed to GitHub
- [ ] All tests passing
- [ ] Environment examples updated
- [ ] API keys obtained (TronGrid, Telegram)
- [ ] Render account created
- [ ] Repository connected to Render
- [ ] Secure keys generated
- [ ] Documentation reviewed

## 🔐 Security Checklist

- [ ] Strong `SECRET_KEY` generated
- [ ] Secure `WALLET_ENCRYPTION_KEY` generated
- [ ] All URLs using HTTPS/WSS
- [ ] CORS configured correctly
- [ ] ALLOWED_HOSTS set properly
- [ ] Debug mode disabled (`DEBUG=False`)
- [ ] Sensitive data not in Git
- [ ] Database backups enabled
- [ ] SSL certificates active

## 📊 Post-Deployment Tasks

### Immediate (Day 1)
- [ ] Create Django superuser
- [ ] Test all API endpoints
- [ ] Verify WebSocket connections
- [ ] Test Telegram authentication
- [ ] Create test deal
- [ ] Check logs for errors

### First Week
- [ ] Monitor service health
- [ ] Review error rates
- [ ] Test backup restoration
- [ ] Set up monitoring alerts
- [ ] Document any issues
- [ ] Optimize performance

### Ongoing
- [ ] Monitor costs weekly
- [ ] Review logs weekly
- [ ] Check database size monthly
- [ ] Update dependencies monthly
- [ ] Rotate keys quarterly
- [ ] Security audit quarterly

## 🆘 Getting Help

### Documentation
- **This Package**: All `.md` files in this repository
- **Render Docs**: https://render.com/docs
- **Django Docs**: https://docs.djangoproject.com/
- **Next.js Docs**: https://nextjs.org/docs

### Support
- **Render Support**: support@render.com
- **Community**: https://community.render.com/
- **Status**: https://status.render.com/

### Troubleshooting
1. Check `RENDER_TROUBLESHOOTING.md`
2. Review service logs
3. Test with health check endpoints
4. Search community forum
5. Contact support with details

## 🎯 Success Criteria

Your deployment is successful when:

✅ All services show "Healthy" status
✅ Backend health check returns 200 OK
✅ Frontend loads without errors
✅ API endpoints respond correctly
✅ WebSocket connections work
✅ Telegram authentication works
✅ Deals can be created and completed
✅ Database operations succeed
✅ Celery tasks execute
✅ No errors in logs

## 🚀 Next Steps After Deployment

1. **Custom Domain** (Optional)
   - Purchase domain
   - Configure DNS
   - Add to Render services
   - Update environment variables

2. **Monitoring**
   - Set up external monitoring (UptimeRobot)
   - Configure error tracking (Sentry)
   - Enable log aggregation
   - Set up alerts

3. **Optimization**
   - Add database indexes
   - Enable caching
   - Optimize queries
   - Configure CDN

4. **Documentation**
   - Update API documentation
   - Create user guide
   - Document admin procedures
   - Write runbooks

5. **Marketing**
   - Announce launch
   - Create landing page
   - Set up analytics
   - Gather feedback

## 📝 Notes

- Keep all documentation updated as you make changes
- Document any custom configurations
- Share knowledge with your team
- Maintain a changelog
- Regular backups are crucial
- Test disaster recovery procedures

## 🎉 Congratulations!

You now have everything needed to deploy your Crypto Escrow Platform to Render. Follow the guides, use the checklists, and don't hesitate to refer back to the documentation.

**Good luck with your deployment! 🚀**

---

**Package Version**: 1.0
**Last Updated**: April 2026
**Maintained By**: Crypto Escrow Team
