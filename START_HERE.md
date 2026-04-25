# 🚀 Crypto Escrow Platform - Complete Startup Guide

## 📖 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Running the Services](#running-the-services)
5. [Accessing the Platform](#accessing-the-platform)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

## ⚡ Quick Start

Get everything running in 5 minutes:

```bash
# 1. Start Redis
redis-server

# 2. Start Backend (Terminal 1)
cd backend
python manage.py migrate
python manage.py runserver

# 3. Start Celery (Terminal 2)
cd backend
celery -A config worker -l info --pool=solo

# 4. Start Telegram Bot (Terminal 3)
cd backend
python manage.py run_telegram_bot

# 5. Start Frontend (Terminal 4)
cd frontend
npm install
npm run dev
```

**Access the platform:**
- Web App: http://localhost:3000
- API: http://localhost:8000
- Admin: http://localhost:8000/admin
- Telegram Bot: Search for your bot in Telegram

## 📋 Prerequisites

### Required Software

- **Python 3.10+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **PostgreSQL 14+** - Database
- **Redis 6+** - Cache and message broker
- **Git** - Version control

### Optional but Recommended

- **VS Code** - Code editor
- **Postman** - API testing
- **pgAdmin** - Database management
- **Redis Commander** - Redis GUI

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd escrow
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env with your settings
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
copy .env.local.example .env.local  # Windows
cp .env.local.example .env.local    # Linux/Mac

# Edit .env.local with your settings
```

### 4. Database Setup

#### Option A: Use Railway (Recommended for Development)

Your current setup already uses Railway PostgreSQL:
```env
DATABASE_URL=postgresql://postgres:uHmfzuOpaneqYnKHlSgfEozPbiuaOTju@shinkansen.proxy.rlwy.net:36514/railway
```

#### Option B: Local PostgreSQL

```bash
# Create database
createdb crypto_escrow

# Update .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/crypto_escrow
```

### 5. Redis Setup

#### Option A: Local Redis

```bash
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
# Mac: brew install redis

# Start Redis
redis-server
```

#### Option B: Docker Redis

```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

### 6. Environment Configuration

#### Backend `.env`:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Tron Network
TRON_NETWORK=mainnet
TRONGRID_API_KEY=your-trongrid-api-key
TRON_FULL_NODE=https://api.trongrid.io
TRON_SOLIDITY_NODE=https://api.trongrid.io
TRON_EVENT_SERVER=https://api.trongrid.io

# Encryption
WALLET_ENCRYPTION_KEY=your-encryption-key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token

# Frontend
FRONTEND_URL=http://localhost:3000

# Platform Settings
PLATFORM_FEE_PERCENTAGE=2.5
MIN_DEAL_AMOUNT=10.00
MAX_DEAL_AMOUNT=100000.00

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### Frontend `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_TELEGRAM_BOT_NAME=your_bot_name
```

## 🏃 Running the Services

### Development Mode (All Services)

#### Terminal 1: Backend Server
```bash
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
python manage.py runserver
```

#### Terminal 2: Celery Worker
```bash
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
celery -A config worker -l info --pool=solo
```

#### Terminal 3: Telegram Bot
```bash
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
python manage.py run_telegram_bot
```

#### Terminal 4: Frontend
```bash
cd frontend
npm run dev
```

### Using Batch/Shell Scripts

#### Windows:
```bash
# Start backend
cd backend
python manage.py runserver

# Start Celery (new terminal)
cd backend
start_celery.bat

# Start Telegram bot (new terminal)
cd backend
start_telegram_bot.bat

# Start frontend (new terminal)
cd frontend
npm run dev
```

#### Linux/Mac:
```bash
# Make scripts executable
chmod +x backend/*.sh

# Start services
./backend/run_migrations.sh
./backend/start_celery.sh
./backend/start_telegram_bot.sh
```

## 🌐 Accessing the Platform

### Web Application

1. **Open Browser**: http://localhost:3000
2. **Click "Get Started"** or **"Login"**
3. **Login with Telegram**: Click the Telegram login button
4. **Authorize**: Allow the app to access your Telegram info
5. **Dashboard**: You'll be redirected to your dashboard

### Telegram Bot

1. **Open Telegram**
2. **Search** for your bot (use the bot username from @BotFather)
3. **Send** `/start` command
4. **Explore** the menu options

### Admin Panel

1. **Create Superuser**:
```bash
cd backend
python manage.py createsuperuser
```

2. **Access Admin**: http://localhost:8000/admin
3. **Login** with superuser credentials

### API Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **API Root**: http://localhost:8000/api/v1/

## 🧪 Testing

### Test User Registration

1. Open web app
2. Click "Login"
3. Use Telegram login
4. Check if user is created in admin panel

### Test Wallet Creation

```bash
cd backend
python manage.py shell
```

```python
from apps.users.models import User
from apps.wallets.models import Wallet

# Check users
users = User.objects.all()
print(f"Total users: {users.count()}")

# Check wallets
wallets = Wallet.objects.all()
print(f"Total wallets: {wallets.count()}")

# View a wallet
wallet = Wallet.objects.first()
print(f"Address: {wallet.address}")
print(f"Balance: {wallet.user.balance}")
```

### Test Telegram Bot

1. Send `/start` to your bot
2. Click "💰 My Wallet"
3. Click "💳 Deposit"
4. Verify you see your TRC20 address
5. Click "📋 My Deals"
6. Verify the deals list appears

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Get user info (requires auth token)
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/v1/users/me/
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

#### 2. Database Connection Error

**Error**: `could not connect to server`

**Solution**:
- Check if PostgreSQL is running
- Verify DATABASE_URL in .env
- Test connection:
```bash
psql $DATABASE_URL
```

#### 3. Redis Connection Error

**Error**: `Error connecting to Redis`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start it
redis-server
```

#### 4. Module Not Found

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

#### 5. Migration Errors

**Error**: `No migrations to apply` or migration conflicts

**Solution**:
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

#### 6. Telegram Bot Not Responding

**Solution**:
- Verify TELEGRAM_BOT_TOKEN in .env
- Check if bot process is running
- Review logs for errors
- Test token with @BotFather

#### 7. Frontend Build Errors

**Solution**:
```bash
cd frontend
rm -rf .next node_modules
npm install
npm run dev
```

### Checking Logs

#### Backend Logs
```bash
# Django logs
cd backend
tail -f logs/django.log

# Celery logs
tail -f logs/celery.log

# Telegram bot logs
tail -f logs/telegram_bot.log
```

#### Frontend Logs
```bash
# Check terminal output where npm run dev is running
# Or check browser console (F12)
```

### Database Issues

```bash
# Reset database (WARNING: Deletes all data)
cd backend
python manage.py flush

# Or drop and recreate
dropdb crypto_escrow
createdb crypto_escrow
python manage.py migrate
```

## 📚 Next Steps

1. **Read Documentation**:
   - [API Documentation](API_DOCUMENTATION.md)
   - [Architecture](ARCHITECTURE.md)
   - [Telegram Bot Guide](TELEGRAM_BOT_GUIDE.md)

2. **Explore Features**:
   - Create a test deal
   - Test deposit flow
   - Enable 2FA
   - Try the chat feature

3. **Development**:
   - Review the codebase
   - Check TODO.md for pending tasks
   - Run tests
   - Add new features

4. **Deployment**:
   - Read [DEPLOYMENT.md](DEPLOYMENT.md)
   - Set up production environment
   - Configure CI/CD
   - Monitor services

## 🎯 Quick Reference

### Essential Commands

```bash
# Backend
python manage.py runserver          # Start Django
python manage.py migrate            # Run migrations
python manage.py createsuperuser    # Create admin
python manage.py shell              # Django shell
python manage.py run_telegram_bot   # Start bot

# Celery
celery -A config worker -l info --pool=solo  # Start worker
celery -A config beat -l info                # Start scheduler
celery -A config inspect active              # Check tasks

# Frontend
npm run dev      # Development server
npm run build    # Production build
npm run start    # Production server
npm run lint     # Lint code

# Database
python manage.py makemigrations  # Create migrations
python manage.py migrate         # Apply migrations
python manage.py dbshell         # Database shell

# Redis
redis-cli        # Redis CLI
redis-cli ping   # Test connection
redis-cli flushall  # Clear all data
```

### Default Ports

- Frontend: 3000
- Backend: 8000
- PostgreSQL: 5432
- Redis: 6379

### Important URLs

- Web App: http://localhost:3000
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/
- API Docs: http://localhost:8000/api/docs/

## ✅ Checklist

Before starting development:

- [ ] All prerequisites installed
- [ ] Environment files configured
- [ ] Database created and migrated
- [ ] Redis running
- [ ] Backend server running
- [ ] Celery worker running
- [ ] Telegram bot running
- [ ] Frontend running
- [ ] Can access web app
- [ ] Can login with Telegram
- [ ] Bot responds to commands
- [ ] Admin panel accessible

## 🎉 Success!

If you've completed all steps, you should have:

✅ A fully functional web application
✅ A responsive Telegram bot
✅ Real-time deal management
✅ Secure wallet system
✅ Admin panel access
✅ API endpoints working

**Happy coding! 🚀**

For support or questions, check the documentation or create an issue.
