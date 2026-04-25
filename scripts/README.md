# Deployment Scripts

This directory contains scripts for deploying, backing up, and restoring the Crypto Escrow Platform.

## Scripts

### 1. deploy.sh
Automated deployment script for staging and production environments.

**Usage:**
```bash
# Make executable (Linux/Mac)
chmod +x scripts/deploy.sh

# Deploy to staging
sudo bash scripts/deploy.sh staging

# Deploy to production
sudo bash scripts/deploy.sh production
```

**Features:**
- Database backup before deployment
- Code pulling from Git
- Backend dependency updates
- Frontend build
- Service restart (systemd)
- Database migrations
- Static file collection
- Health checks

### 2. backup.sh
Automated backup script for database, media files, and configuration.

**Usage:**
```bash
# Make executable (Linux/Mac)
chmod +x scripts/backup.sh

# Run backup
sudo bash scripts/backup.sh

# Setup automated daily backups (cron)
sudo crontab -e
# Add: 0 2 * * * /opt/escrow/scripts/backup.sh >> /var/log/escrow-backup.log 2>&1
```

**Features:**
- Database backup (pg_dumpall)
- Media files backup
- Configuration backup
- Compression (gzip)
- Retention policy (30 days)
- Remote storage support (S3)

**Backup Locations:**
- Database: `/opt/escrow/backups/db/`
- Media: `/opt/escrow/backups/media/`
- Config: `/opt/escrow/backups/config/`

### 3. restore.sh
Interactive restore script for database and media files.

**Usage:**
```bash
# Make executable (Linux/Mac)
chmod +x scripts/restore.sh

# Run restore
sudo bash scripts/restore.sh
```

**Features:**
- List available backups
- Interactive selection
- Database restoration
- Media files restoration
- Service restart (systemd)
- Health verification

## Requirements

- Bash shell
- Root or sudo access
- PostgreSQL installed
- Redis installed
- Git installed
- Running services (for backup/restore)

## Notes

### For Linux/Mac Users
Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### For Windows Users
Run scripts using Git Bash or WSL:
```bash
bash scripts/deploy.sh production
```

Or use PowerShell:
```powershell
bash -c "./scripts/deploy.sh production"
```

## Security

- Scripts require root/sudo access
- Production deployments require confirmation
- Backups are compressed and stored securely
- Sensitive data is never logged
- All operations are logged for audit

## Troubleshooting

### Permission Denied
```bash
chmod +x scripts/*.sh
```

### Script Not Found
```bash
# Ensure you're in the project root
cd /opt/escrow
bash scripts/deploy.sh production
```

### Service Command Failed
```bash
# Check systemd services
sudo systemctl status escrow-backend
sudo systemctl status escrow-celery-worker
sudo systemctl status escrow-frontend

# Restart services
sudo systemctl restart escrow-backend
```

## Support

For issues:
1. Check script logs
2. Review service logs: `sudo journalctl -u escrow-backend -f`
3. Verify environment variables in `.env`
4. Check PRODUCTION_DEPLOYMENT.md for detailed instructions

---

**Last Updated:** April 23, 2026  
**Version:** 2.0.0 (Native Deployment)
