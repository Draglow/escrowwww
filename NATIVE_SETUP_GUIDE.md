# Native Setup Guide - Windows (No Docker)

Complete guide to run the Crypto Escrow Platform natively on Windows without Docker.

**Last Updated:** April 22, 2026  
**Platform:** Windows 10/11  
**Estimated Setup Time:** 45-60 minutes

---

## 📋 Prerequisites

### Required Software

1. **Python 3.11+**
   - Download: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation
   - Verify: `python --version`

2. **Node.js 18+**
   - Download: https://nodejs.org/
   - Verify: `node --version` and `npm --version`

3. **PostgreSQL 15+**
   - Download: https://www.postgresql.org/download/windows/
   - Remember the password you set during installation
   - Verify: `psql --version`

4. **Redis for Windows**
   - Download: https://github.com/microsoftarchive/redis/releases
   - Or use Memurai (Redis alternative): https://www.memurai.com/
   - Verify: `redis-cli --version` or `memurai-cli --version`

5. **Git**
   - Download: https://git-scm.com/download/win
   - Verify: `git --version`

### Optional (Recommended)

6. **Visual Studio Code**
   - Download: https://code.visualstudio.com/

7. **Microsoft C++ Build Tools** (for some Python packages)
   - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++"

---

## 🚀 Step-by-Step Setup

### Step 1: Install PostgreSQL

1. **Download PostgreSQL 15** from https://www.postgresql.org/download/windows/

2. **Run the installer:**
   - Port: `5432` (default)
   - Password: Choose a strong password (remember it!)
   - Locale: Default

3. **Verify installation:**
   ```cmd
   psql --version
   ```

4. **Create database:**
   ```cmd
   # Open Command Prompt as Administrator
   psql -U postgres

   # In PostgreSQL prompt:
   CREATE DATABASE escrow_dev;
   CREATE USER escrow_user WITH PASSWORD 'your_password_here';
   GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
   \q
   ```

---

### Step 2: Install Redis

#### Option A: Redis (Official Port)

1. **Download** from https://github.com/microsoftarchive/redis/releases
2. **Extract** to `C:\Redis`
3. **Install as Windows Service:**
   ```cmd
   cd C:\Redis
   redis-server --service-install redis.windows.conf
   redis-server --service-start
   ```

4. **Verify:**
   ```cmd
   redis-cli ping
   # Should return: PONG
   ```

#### Option B: Memurai (Recommended for Windows)

1. **Download** from https://www.memurai.com/get-memurai
2. **Install** (it installs as a Windows service automatically)
3. **Verify:**
   ```cmd
   memurai-cli ping
   # Should return: PONG
   ```

---

### Step 3: Setup Backend

#### 3.1 Navigate to Backend Directory

```cmd
cd C:\Users\boob\Desktop\escrow\backend
```

#### 3.2 Create Virtual Environment

```cmd
# Create virtual environment
python -m venv venv

# Activate (Command Prompt)
venv\Scripts\activate.bat

# Or activate (PowerShell - if execution policy allows)
# venv\Scripts\Activate.ps1
```

#### 3.3 Upgrade pip

```cmd
python -m pip install --upgrade pip
```

#### 3.4 Install Dependencies

```cmd
# Install packages one by one to avoid build issues
pip install Django==4.2.11
pip install djangorestframework==3.14.0
pip install django-cors-headers==4.3.1
pip install python-dotenv==1.0.1

# Database
pip install psycopg2-binary==2.9.9

# Async & WebSockets
pip install channels==4.0.0
pip install channels-redis==4.2.0
pip install daphne==4.1.0

# Celery & Redis
pip install celery==5.3.6
pip install redis==5.0.1
pip install django-celery-beat==2.5.0

# Cryptography (may require build tools)
pip install cryptography==42.0.5
pip install pycryptodome==3.20.0
pip install PyJWT==2.8.0
pip install pyotp==2.9.0
pip install qrcode==7.4.2

# Try Pillow (skip if it fails)
pip install Pillow==10.2.0

# Blockchain
pip install tronpy==0.4.0

# API & Validation
pip install pydantic==2.6.4
pip install requests==2.31.0

# Production server
pip install gunicorn==21.2.0

# Monitoring
pip install sentry-sdk==1.40.6

# Development
pip install django-extensions==3.2.3
pip install ipython==8.22.2
```

**Note:** If Pillow fails, you can skip it. QR codes won't work, but everything else will.

#### 3.5 Configure Environment Variables

```cmd
# Copy example file
copy .env.example .env

# Edit the file
notepad .env
```

**Configure `.env` with these values:**

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here-generate-one
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://localhost:8000

# Database (PostgreSQL)
DATABASE_URL=postgresql://escrow_user:your_password_here@localhost:5432/escrow_dev

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Wallet Encryption Key (generate below)
WALLET_ENCRYPTION_KEY=your-fernet-key-here

# Tron Blockchain
TRON_API_KEY=
TRON_NETWORK=nile

# Platform Settings
PLATFORM_FEE_PERCENTAGE=2.5

# Telegram (optional for now)
TELEGRAM_BOT_TOKEN=
NEXT_PUBLIC_TELEGRAM_BOT_NAME=

# Monitoring (optional)
SENTRY_DSN=
```

#### 3.6 Generate Secret Keys

```cmd
# Generate Django SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate WALLET_ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy these values into your `.env` file.

#### 3.7 Run Migrations

```cmd
python manage.py migrate
```

#### 3.8 Create Superuser

```cmd
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

#### 3.9 Collect Static Files

```cmd
python manage.py collectstatic --noinput
```

#### 3.10 Start Django Development Server

```cmd
python manage.py runserver
```

**Backend is now running at:** http://localhost:8000

**Test it:**
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/
- Health: http://localhost:8000/api/v1/health/

---

### Step 4: Setup Celery (Background Tasks)

Open a **new Command Prompt** window:

```cmd
cd C:\Users\boob\Desktop\escrow\backend

# Activate virtual environment
venv\Scripts\activate.bat

# Start Celery worker
celery -A config worker -l info --pool=solo
```

**Note:** Use `--pool=solo` on Windows as it doesn't support the default pool.

Open **another Command Prompt** for Celery Beat (scheduler):

```cmd
cd C:\Users\boob\Desktop\escrow\backend

# Activate virtual environment
venv\Scripts\activate.bat

# Start Celery beat
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

### Step 5: Setup Frontend

Open a **new Command Prompt** window:

#### 5.1 Navigate to Frontend Directory

```cmd
cd C:\Users\boob\Desktop\escrow\frontend
```

#### 5.2 Install Dependencies

```cmd
npm install
```

#### 5.3 Configure Environment Variables

```cmd
# Copy example file
copy .env.local.example .env.local

# Edit the file
notepad .env.local
```

**Configure `.env.local`:**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_TELEGRAM_BOT_NAME=YourBotName
```

#### 5.4 Start Development Server

```cmd
npm run dev
```

**Frontend is now running at:** http://localhost:3000

---

## ✅ Verification

### Check All Services

You should now have **5 Command Prompt windows** running:

1. **Django** - `python manage.py runserver` - Port 8000
2. **Celery Worker** - `celery -A config worker` - Background tasks
3. **Celery Beat** - `celery -A config beat` - Scheduled tasks
4. **Frontend** - `npm run dev` - Port 3000
5. **PostgreSQL** - Running as Windows service
6. **Redis/Memurai** - Running as Windows service

### Test the Application

1. **Backend API:**
   ```cmd
   curl http://localhost:8000/api/v1/health/
   ```

2. **Frontend:**
   - Open browser: http://localhost:3000
   - Should see the landing page

3. **Admin Panel:**
   - Open browser: http://localhost:8000/admin/
   - Login with superuser credentials

---

## 🔧 Daily Development Workflow

### Starting the Application

Create a batch file `start-dev.bat` in the project root:

```batch
@echo off
echo Starting Crypto Escrow Platform...

REM Start PostgreSQL (if not running as service)
REM net start postgresql-x64-15

REM Start Redis (if not running as service)
REM net start Redis

REM Start Backend
start "Django Server" cmd /k "cd backend && venv\Scripts\activate.bat && python manage.py runserver"

REM Wait a bit
timeout /t 3

REM Start Celery Worker
start "Celery Worker" cmd /k "cd backend && venv\Scripts\activate.bat && celery -A config worker -l info --pool=solo"

REM Start Celery Beat
start "Celery Beat" cmd /k "cd backend && venv\Scripts\activate.bat && celery -A config beat -l info"

REM Wait a bit
timeout /t 3

REM Start Frontend
start "Next.js Frontend" cmd /k "cd frontend && npm run dev"

echo All services started!
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo Admin: http://localhost:8000/admin/
echo.
pause
```

**Usage:**
```cmd
# Double-click start-dev.bat or run:
start-dev.bat
```

### Stopping the Application

Create a batch file `stop-dev.bat`:

```batch
@echo off
echo Stopping all services...

REM Kill Node.js processes
taskkill /F /IM node.exe /T 2>nul

REM Kill Python processes
taskkill /F /IM python.exe /T 2>nul

echo All services stopped!
pause
```

---

## 🐛 Troubleshooting

### Issue: PostgreSQL Connection Failed

**Error:** `could not connect to server`

**Solution:**
```cmd
# Check if PostgreSQL is running
sc query postgresql-x64-15

# Start if not running
net start postgresql-x64-15

# Or restart
net stop postgresql-x64-15
net start postgresql-x64-15
```

### Issue: Redis Connection Failed

**Error:** `Error connecting to Redis`

**Solution:**
```cmd
# Check if Redis is running
sc query Redis

# Start if not running
net start Redis

# Test connection
redis-cli ping
```

### Issue: Port Already in Use

**Error:** `Port 8000 is already in use`

**Solution:**
```cmd
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

### Issue: Celery Won't Start on Windows

**Error:** `ValueError: not enough values to unpack`

**Solution:**
Always use `--pool=solo` on Windows:
```cmd
celery -A config worker -l info --pool=solo
```

### Issue: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```cmd
# Make sure virtual environment is activated
venv\Scripts\activate.bat

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: Pillow Installation Failed

**Solution:**
```cmd
# Install Visual C++ Build Tools
# Or skip Pillow and comment it out in requirements.txt

# Edit requirements.txt
notepad requirements.txt

# Comment out this line:
# Pillow==10.2.0
```

---

## 📊 Database Management

### Backup Database

```cmd
# Backup
pg_dump -U escrow_user -d escrow_dev > backup.sql

# Restore
psql -U escrow_user -d escrow_dev < backup.sql
```

### Reset Database

```cmd
# Drop and recreate
psql -U postgres
DROP DATABASE escrow_dev;
CREATE DATABASE escrow_dev;
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q

# Run migrations again
cd backend
venv\Scripts\activate.bat
python manage.py migrate
python manage.py createsuperuser
```

### View Database

```cmd
# Connect to database
psql -U escrow_user -d escrow_dev

# List tables
\dt

# Query users
SELECT * FROM users_user;

# Exit
\q
```

---

## 🔒 Security Notes

### For Development

- ✅ `DEBUG=True` is OK
- ✅ Simple passwords are OK
- ✅ `localhost` only is OK

### For Production

- ❌ Never use `DEBUG=True`
- ❌ Use strong passwords (20+ characters)
- ❌ Configure proper `ALLOWED_HOSTS`
- ❌ Use HTTPS
- ❌ Enable firewall
- ❌ Use environment-specific `.env` files

---

## 📚 Additional Resources

### Documentation
- **API Documentation:** `API_DOCUMENTATION.md`
- **Architecture:** `ARCHITECTURE.md`
- **Quick Reference:** `QUICK_REFERENCE.md`
- **Testing Guide:** `TESTING_GUIDE.md`

### External Resources
- **Django:** https://docs.djangoproject.com/
- **Next.js:** https://nextjs.org/docs
- **PostgreSQL:** https://www.postgresql.org/docs/
- **Redis:** https://redis.io/documentation
- **Celery:** https://docs.celeryproject.org/

---

## 🎯 Next Steps

1. ✅ **Test the Application**
   - Create a test user
   - Test wallet creation
   - Test deal creation

2. ✅ **Configure Telegram Bot**
   - Create bot via @BotFather
   - Add token to `.env`
   - Test Telegram login

3. ✅ **Configure Tron Network**
   - Get API key from TronGrid
   - Add to `.env`
   - Test deposit detection

4. ✅ **Explore the Admin Panel**
   - http://localhost:8000/admin/
   - View users, deals, transactions

---

## 🎉 Success!

You now have the Crypto Escrow Platform running natively on Windows without Docker!

**Access Points:**
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/v1/
- **Admin Panel:** http://localhost:8000/admin/
- **API Health:** http://localhost:8000/api/v1/health/

**Need Help?**
- Check `QUICK_REFERENCE.md` for common commands
- Review `TROUBLESHOOTING.md` for common issues
- Check logs in Command Prompt windows

---

**Last Updated:** April 22, 2026  
**Version:** 1.0.0  
**Platform:** Windows Native Setup
