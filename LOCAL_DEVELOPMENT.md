# Local Development Guide

Complete guide to run the Crypto Escrow Platform on your local machine for development.

**Last Updated:** April 23, 2026  
**Estimated Setup Time:** 30-45 minutes

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Running the Application](#running-the-application)
5. [Development Workflow](#development-workflow)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Tips & Tricks](#tips--tricks)

---

## Prerequisites

### Required Software

Install these before starting:

#### 1. Python 3.11+
- **Windows:** Download from https://www.python.org/downloads/
  - ✅ Check "Add Python to PATH" during installation
- **Mac:** `brew install python@3.11`
- **Linux:** `sudo apt install python3.11 python3.11-venv`

**Verify:**
```bash
python --version  # Should show 3.11 or higher
```

#### 2. Node.js 18+
- **Windows/Mac:** Download from https://nodejs.org/
- **Linux:** 
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  sudo apt install -y nodejs
  ```

**Verify:**
```bash
node --version  # Should show v18 or higher
npm --version
```

#### 3. PostgreSQL 15+
- **Windows:** Download from https://www.postgresql.org/download/windows/
- **Mac:** `brew install postgresql@15 && brew services start postgresql`
- **Linux:** 
  ```bash
  sudo apt install postgresql postgresql-contrib
  sudo systemctl start postgresql
  ```

**Verify:**
```bash
psql --version  # Should show 15 or higher
```

#### 4. Redis 7+
- **Windows:** Download from https://github.com/microsoftarchive/redis/releases
  - Or use Memurai: https://www.memurai.com/
- **Mac:** `brew install redis && brew services start redis`
- **Linux:** 
  ```bash
  sudo apt install redis-server
  sudo systemctl start redis
  ```

**Verify:**
```bash
redis-cli ping  # Should return PONG
```

#### 5. Git
- **All platforms:** https://git-scm.com/downloads

**Verify:**
```bash
git --version
```

---

## Quick Start

For experienced developers who want to get started quickly:

```bash
# 1. Clone repository
git clone https://github.com/yourusername/escrow-platform.git
cd escrow-platform

# 2. Setup database
psql -U postgres
CREATE DATABASE escrow_dev;
CREATE USER escrow_user WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q

# 3. Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python manage.py migrate
python manage.py createsuperuser

# 4. Setup frontend
cd ../frontend
npm install
cp .env.local.example .env.local
# Edit .env.local

# 5. Run (in separate terminals)
# Terminal 1: cd backend && source venv/bin/activate && python manage.py runserver
# Terminal 2: cd backend && source venv/bin/activate && celery -A config worker -l info --pool=solo
# Terminal 3: cd backend && source venv/bin/activate && celery -A config beat -l info
# Terminal 4: cd frontend && npm run dev
```

---

## Detailed Setup

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/escrow-platform.git
cd escrow-platform

# Or if you already have it
cd /path/to/escrow-platform
git pull origin main
```

### Step 2: Database Setup

#### Create PostgreSQL Database

**Windows (Command Prompt):**
```cmd
psql -U postgres
```

**Mac/Linux:**
```bash
sudo -u postgres psql
```

**In PostgreSQL prompt:**
```sql
-- Create database
CREATE DATABASE escrow_dev;

-- Create user
CREATE USER escrow_user WITH PASSWORD 'dev_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;

-- Allow user to create databases (for tests)
ALTER USER escrow_user CREATEDB;

-- Exit
\q
```

#### Configure Redis (if needed)

**Check if Redis is running:**
```bash
redis-cli ping
```

If it returns `PONG`, you're good to go!

**If Redis requires password (optional for development):**
```bash
# Edit Redis config
# Linux: sudo nano /etc/redis/redis.conf
# Mac: nano /usr/local/etc/redis.conf
# Windows: Edit redis.windows.conf

# Find and uncomment:
# requirepass your_password
```

### Step 3: Backend Setup

#### Create Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Mac/Linux:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

#### Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# If you're on Windows and some packages fail, try:
pip install -r requirements-windows.txt
```

#### Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit the file
# Windows: notepad .env
# Mac/Linux: nano .env
```

**Minimal `.env` configuration for local development:**

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://localhost:8000

# Database
DATABASE_URL=postgresql://escrow_user:dev_password@localhost:5432/escrow_dev

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Wallet Encryption (generate below)
WALLET_ENCRYPTION_KEY=your-fernet-key-here

# Tron Blockchain (optional for now)
TRON_API_KEY=
TRON_NETWORK=nile

# Platform Settings
PLATFORM_FEE_PERCENTAGE=2.5

# Telegram (optional for now)
TELEGRAM_BOT_TOKEN=
NEXT_PUBLIC_TELEGRAM_BOT_NAME=
```

#### Generate Secret Keys

**Generate Django SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Generate WALLET_ENCRYPTION_KEY:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy these values into your `.env` file.

#### Run Migrations

```bash
# Make sure virtual environment is activated
python manage.py migrate
```

#### Create Superuser

```bash
python manage.py createsuperuser

# Follow the prompts:
# Username: admin
# Email: admin@example.com
# Password: (choose a password)
```

#### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 4: Frontend Setup

Open a **new terminal** window:

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Edit the file
# Windows: notepad .env.local
# Mac/Linux: nano .env.local
```

**Configure `.env.local`:**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_TELEGRAM_BOT_NAME=YourBotName
```

---

## Running the Application

You need to run **4 services** in separate terminal windows:

### Terminal 1: Django Backend

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python manage.py runserver
```

**Output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

✅ Backend running at: http://localhost:8000

### Terminal 2: Celery Worker

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate

# Windows:
celery -A config worker -l info --pool=solo

# Mac/Linux:
celery -A config worker -l info
```

**Output:**
```
[tasks]
  . apps.wallets.tasks.monitor_deposits
  . apps.wallets.tasks.sync_wallet_balances
```

✅ Celery worker running

### Terminal 3: Celery Beat (Scheduler)

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
celery -A config beat -l info
```

**Output:**
```
celery beat v5.3.6 is starting.
```

✅ Celery beat running

### Terminal 4: Next.js Frontend

```bash
cd frontend
npm run dev
```

**Output:**
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
- event compiled client and server successfully
```

✅ Frontend running at: http://localhost:3000

---

## Access Points

Once all services are running:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main application |
| **Backend API** | http://localhost:8000/api/v1/ | REST API |
| **Admin Panel** | http://localhost:8000/admin/ | Django admin |
| **API Docs** | http://localhost:8000/api/v1/ | API documentation |
| **Health Check** | http://localhost:8000/api/v1/health/ | System health |

### Test the Setup

**1. Check Backend:**
```bash
curl http://localhost:8000/api/v1/health/
```

**2. Check Frontend:**
Open browser: http://localhost:3000

**3. Check Admin:**
Open browser: http://localhost:8000/admin/
Login with superuser credentials

---

## Development Workflow

### Making Changes

#### Backend Changes

1. Edit Python files in `backend/apps/`
2. Django auto-reloads (no restart needed)
3. If you change models:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

#### Frontend Changes

1. Edit files in `frontend/src/`
2. Next.js auto-reloads (no restart needed)
3. Changes appear instantly in browser

#### Database Changes

```bash
# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate

# Rollback migration
python manage.py migrate app_name previous_migration_name
```

### Common Commands

#### Backend

```bash
# Django shell
python manage.py shell

# Create app
python manage.py startapp app_name

# Run tests
python manage.py test

# Check for issues
python manage.py check

# Create superuser
python manage.py createsuperuser

# Clear cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

#### Frontend

```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check
```

#### Database

```bash
# Access PostgreSQL
psql -U escrow_user -d escrow_dev

# In psql:
\dt              # List tables
\d table_name    # Describe table
SELECT * FROM users_user LIMIT 5;
\q               # Quit
```

#### Redis

```bash
# Access Redis CLI
redis-cli

# In redis-cli:
PING             # Test connection
KEYS *           # List all keys
GET key_name     # Get value
FLUSHALL         # Clear all data (careful!)
EXIT             # Quit
```

---

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
python manage.py test

# Run specific app tests
python manage.py test apps.users

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend Tests

```bash
cd frontend

# Run tests (when added)
npm test

# Run with coverage
npm test -- --coverage
```

### Manual Testing

#### Create Test User

```bash
cd backend
python manage.py shell
```

```python
from apps.users.models import User

# Create user
user = User.objects.create_user(
    telegram_id=123456789,
    username='testuser',
    first_name='Test',
    last_name='User'
)

# Check wallet was created
print(f"Wallet address: {user.wallet.address}")
print(f"Balance: {user.balance}")
```

#### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Get user (requires auth)
curl http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Telegram id=123456789&hash=test"
```

---

## Troubleshooting

### Logging Configuration Error

**Error:** `ValueError: Unable to configure handler 'file'`

**Solution:**

This error occurs when Django tries to write logs to a directory that doesn't exist. The latest version of settings.py fixes this automatically, but if you still see this error:

```bash
# Create logs directory manually
cd backend
mkdir logs

# Or on Windows:
cd backend
md logs
```

The updated settings.py now:
- Creates the logs directory automatically
- Only uses file logging in production (DEBUG=False)
- Uses console logging in development

### Port Already in Use

**Error:** `Error: That port is already in use.`

**Solution:**

**Windows:**
```cmd
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

**Mac/Linux:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### PostgreSQL Connection Failed

**Error:** `could not connect to server`

**Solution:**

**Windows:**
```cmd
# Check if PostgreSQL is running
sc query postgresql-x64-15

# Start if not running
net start postgresql-x64-15
```

**Mac:**
```bash
brew services start postgresql@15
```

**Linux:**
```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

### Redis Connection Failed

**Error:** `Error connecting to Redis`

**Solution:**

**Windows:**
```cmd
# Check if Redis is running
sc query Redis

# Start if not running
net start Redis
```

**Mac:**
```bash
brew services start redis
```

**Linux:**
```bash
sudo systemctl start redis
sudo systemctl status redis
```

### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Celery Won't Start (Windows)

**Error:** `ValueError: not enough values to unpack`

**Solution:**
Always use `--pool=solo` on Windows:
```bash
celery -A config worker -l info --pool=solo
```

### Migration Errors

**Error:** `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solution:**
```bash
# Reset database (WARNING: deletes all data)
psql -U postgres
DROP DATABASE escrow_dev;
CREATE DATABASE escrow_dev;
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q

# Run migrations again
python manage.py migrate
python manage.py createsuperuser
```

### Frontend Build Errors

**Error:** `Module not found` or `Cannot find module`

**Solution:**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json  # Windows: rmdir /s node_modules
npm install
```

---

## Tips & Tricks

### Use Batch Files (Windows)

Create `start-dev.bat` in project root:

```batch
@echo off
echo Starting Crypto Escrow Platform...

start "Django" cmd /k "cd backend && venv\Scripts\activate && python manage.py runserver"
timeout /t 2
start "Celery Worker" cmd /k "cd backend && venv\Scripts\activate && celery -A config worker -l info --pool=solo"
timeout /t 2
start "Celery Beat" cmd /k "cd backend && venv\Scripts\activate && celery -A config beat -l info"
timeout /t 2
start "Frontend" cmd /k "cd frontend && npm run dev"

echo All services started!
pause
```

Create `stop-dev.bat`:

```batch
@echo off
echo Stopping all services...
taskkill /F /IM node.exe /T 2>nul
taskkill /F /IM python.exe /T 2>nul
echo All services stopped!
pause
```

### Use Shell Scripts (Mac/Linux)

Create `start-dev.sh`:

```bash
#!/bin/bash

echo "Starting Crypto Escrow Platform..."

# Start backend
cd backend
source venv/bin/activate
python manage.py runserver &
DJANGO_PID=$!

# Start Celery worker
celery -A config worker -l info &
CELERY_PID=$!

# Start Celery beat
celery -A config beat -l info &
BEAT_PID=$!

# Start frontend
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "All services started!"
echo "Django PID: $DJANGO_PID"
echo "Celery PID: $CELERY_PID"
echo "Beat PID: $BEAT_PID"
echo "Frontend PID: $FRONTEND_PID"

# Save PIDs
echo $DJANGO_PID > /tmp/escrow-django.pid
echo $CELERY_PID > /tmp/escrow-celery.pid
echo $BEAT_PID > /tmp/escrow-beat.pid
echo $FRONTEND_PID > /tmp/escrow-frontend.pid
```

Create `stop-dev.sh`:

```bash
#!/bin/bash

echo "Stopping all services..."

kill $(cat /tmp/escrow-django.pid) 2>/dev/null
kill $(cat /tmp/escrow-celery.pid) 2>/dev/null
kill $(cat /tmp/escrow-beat.pid) 2>/dev/null
kill $(cat /tmp/escrow-frontend.pid) 2>/dev/null

rm /tmp/escrow-*.pid 2>/dev/null

echo "All services stopped!"
```

### VS Code Configuration

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true
  }
}
```

### Database GUI Tools

- **pgAdmin:** https://www.pgadmin.org/
- **DBeaver:** https://dbeaver.io/
- **TablePlus:** https://tableplus.com/

### API Testing Tools

- **Postman:** https://www.postman.com/
- **Insomnia:** https://insomnia.rest/
- **HTTPie:** https://httpie.io/

### Hot Reload Issues

If changes aren't reflecting:

**Backend:**
```bash
# Restart Django
Ctrl+C
python manage.py runserver
```

**Frontend:**
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

---

## Next Steps

1. ✅ **Explore the Admin Panel**
   - http://localhost:8000/admin/
   - Create test users, deals, wallets

2. ✅ **Test the API**
   - Use Postman or curl
   - See API_DOCUMENTATION.md

3. ✅ **Configure Telegram Bot**
   - Create bot via @BotFather
   - Add token to `.env`

4. ✅ **Configure Tron Network**
   - Get API key from TronGrid
   - Test wallet creation

5. ✅ **Read Documentation**
   - ARCHITECTURE.md - System design
   - API_DOCUMENTATION.md - API reference
   - TESTING_GUIDE.md - Testing guide

---

## Getting Help

### Documentation

- **QUICKSTART.md** - Quick setup guide
- **NATIVE_SETUP_GUIDE.md** - Detailed Windows setup
- **ARCHITECTURE.md** - System architecture
- **API_DOCUMENTATION.md** - API reference
- **TROUBLESHOOTING.md** - Common issues

### Check Logs

**Backend:**
- Look at the Django terminal window
- Check for error messages

**Frontend:**
- Look at the Next.js terminal window
- Check browser console (F12)

**Database:**
```bash
# Check PostgreSQL logs
# Linux: sudo tail -f /var/log/postgresql/postgresql-15-main.log
# Mac: tail -f /usr/local/var/log/postgres.log
```

### Community

- GitHub Issues: Report bugs
- Stack Overflow: Ask questions
- Django Docs: https://docs.djangoproject.com/
- Next.js Docs: https://nextjs.org/docs

---

## Summary

You now have a fully functional local development environment! 🎉

**Running Services:**
- ✅ Django Backend (Port 8000)
- ✅ Celery Worker (Background tasks)
- ✅ Celery Beat (Scheduled tasks)
- ✅ Next.js Frontend (Port 3000)
- ✅ PostgreSQL Database
- ✅ Redis Cache

**Access Points:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Admin: http://localhost:8000/admin

**Happy Coding! 🚀**

---

**Last Updated:** April 23, 2026  
**Version:** 1.0.0
