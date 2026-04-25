# 🚀 Quick Start Guide - Telegram Bot & Web Platform

## Complete Setup in 5 Minutes

This guide will get your Crypto Escrow Platform running with both the web interface and Telegram bot.

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Telegram account

## Step 1: Backend Setup (2 minutes)

### 1.1 Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 1.2 Configure Environment

Your `.env` file is already configured with:
- ✅ Database connection (Railway PostgreSQL)
- ✅ Redis connection
- ✅ Telegram bot token
- ✅ Tron network settings
- ✅ Encryption keys

### 1.3 Run Migrations

```bash
python manage.py migrate
```

### 1.4 Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

## Step 2: Start Backend Services (1 minute)

### Terminal 1: Django Server

```bash
cd backend
python manage.py runserver
```

Server will start at: `http://localhost:8000`

### Terminal 2: Celery Worker

```bash
cd backend
celery -A config worker -l info
```

### Terminal 3: Celery Beat (Scheduled Tasks)

```bash
cd backend
celery -A config beat -l info
```

### Terminal 4: Telegram Bot

**Windows:**
```bash
cd backend
start_telegram_bot.bat
```

**Linux/Mac:**
```bash
cd backend
chmod +x start_telegram_bot.sh
./start_telegram_bot.sh
```

## Step 3: Frontend Setup (2 minutes)

### 3.1 Install Dependencies

```bash
cd frontend
npm install
```

### 3.2 Configure Environment

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### 3.3 Start Development Server

```bash
npm run dev
```

Frontend will start at: `http://localhost:3000`

## Step 4: Test the Platform

### 4.1 Test Web Interface

1. Open browser: `http://localhost:3000`
2. Click "Get Started" or "Login"
3. Use Telegram Login Widget to authenticate
4. Explore dashboard, wallet, and deals

### 4.2 Test Telegram Bot

1. Open Telegram
2. Search for your bot: `@YourBotUsername`
3. Send `/start` command
4. Explore bot features:
   - View wallet
   - Check deals
   - Create new deal
   - Withdraw funds

## Step 5: Make Your First Transaction

### Deposit USDT

1. **Get Deposit Address:**
   - Web: Go to Dashboard → Wallet → Deposit
   - Bot: Send `/wallet` → Click "💳 Deposit"

2. **Send USDT (TRC20):**
   - Copy your deposit address
   - Send USDT from your wallet
   - Wait for blockchain confirmation (~1 minute)
   - Balance updates automatically

### Create a Deal

1. **On Web:**
   - Go to Dashboard → Deals → Create Deal
   - Fill in seller info, title, description, amount
   - Click "Create Deal"

2. **On Telegram:**
   - Send `/start`
   - Click "➕ Create Deal"
   - Follow the prompts

### Complete Deal Flow

1. **Seller Funds Deal:**
   - Web: Click "Fund Deal" button
   - Bot: Select deal → Click "💰 Fund Deal"

2. **Buyer Starts Deal:**
   - Web: Click "Start Deal" button
   - Bot: Select deal → Click "▶️ Start Deal"

3. **Seller Delivers Service/Product**

4. **Buyer Completes Deal:**
   - Web: Click "Complete Deal" button
   - Bot: Select deal → Click "✅ Complete Deal"

5. **Funds Released:**
   - Buyer receives funds (minus platform fee)
   - Deal marked as completed

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                          │
├──────────────────────────┬──────────────────────────────────┤
│   Web App (Next.js)      │   Telegram Bot (Python)          │
│   http://localhost:3000  │   @YourBotUsername               │
└──────────────┬───────────┴──────────────┬───────────────────┘
               │                          │
               └──────────┬───────────────┘
                          │
               ┌──────────▼──────────┐
               │   Django REST API    │
               │  localhost:8000/api  │
               └──────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │PostgreSQL│      │  Redis  │      │  Celery │
   │ Database │      │  Cache  │      │ Workers │
   └─────────┘      └─────────┘      └─────────┘
                          │
                    ┌─────▼─────┐
                    │   Tron    │
                    │ Blockchain│
                    └───────────┘
```

## Features Available

### ✅ Web Platform
- 🔐 Telegram authentication
- 💰 Wallet management
- 📋 Deal creation and management
- 💬 Real-time chat
- 📊 Transaction history
- 🔒 2FA setup and management
- 📈 Audit logs
- 🎨 Modern, responsive UI

### ✅ Telegram Bot
- 🤖 Interactive menu system
- 💰 Wallet operations
- 📋 Deal management
- 💸 Withdrawals with 2FA
- 🔔 Real-time notifications
- 📱 Mobile-first experience

### ✅ Security
- 🔐 Token-based authentication
- 🔒 2FA for withdrawals
- 🛡️ Rate limiting
- 📝 Audit logging
- 🔑 Encrypted private keys
- 🚫 CSRF protection

### ✅ Blockchain
- ⛓️ Tron (TRC20) integration
- 💵 USDT support
- 🔄 Automatic deposit detection
- 📤 Withdrawal processing
- ⚖️ Balance synchronization

## Common Commands

### Backend

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run Telegram bot
python manage.py run_telegram_bot

# Start Celery worker
celery -A config worker -l info

# Start Celery beat
celery -A config beat -l info

# Django shell
python manage.py shell
```

### Frontend

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Troubleshooting

### Backend Issues

**Database Connection Error:**
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Check DATABASE_URL in .env
cat backend/.env | grep DATABASE_URL
```

**Redis Connection Error:**
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

**Celery Not Processing Tasks:**
```bash
# Check Celery worker is running
ps aux | grep celery

# Restart Celery worker
pkill -f celery
celery -A config worker -l info
```

**Telegram Bot Not Responding:**
```bash
# Check bot is running
ps aux | grep run_telegram_bot

# Check bot token
cat backend/.env | grep TELEGRAM_BOT_TOKEN

# Restart bot
python manage.py run_telegram_bot
```

### Frontend Issues

**API Connection Error:**
```bash
# Check backend is running
curl http://localhost:8000/api/v1/users/health/

# Check .env.local
cat frontend/.env.local
```

**Build Errors:**
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run dev
```

## Environment Variables Reference

### Backend (.env)

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Tron
TRON_NETWORK=mainnet
TRONGRID_API_KEY=your-api-key
TRON_FULL_NODE=https://api.trongrid.io
TRON_SOLIDITY_NODE=https://api.trongrid.io
TRON_EVENT_SERVER=https://api.trongrid.io

# Security
WALLET_ENCRYPTION_KEY=your-encryption-key

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token

# Frontend
FRONTEND_URL=http://localhost:3000

# Platform
PLATFORM_FEE_PERCENTAGE=2.5
MIN_DEAL_AMOUNT=10.00
MAX_DEAL_AMOUNT=100000.00

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## Next Steps

1. **Customize Platform:**
   - Update branding in `frontend/src/app/layout.tsx`
   - Modify platform fee in `.env`
   - Add custom features

2. **Deploy to Production:**
   - See [DEPLOYMENT.md](DEPLOYMENT.md)
   - Configure production environment
   - Setup monitoring

3. **Add Features:**
   - Multi-currency support
   - Reputation system
   - Advanced analytics
   - Mobile apps

## Support

- 📖 [API Documentation](API_DOCUMENTATION.md)
- 🏗️ [Architecture Guide](ARCHITECTURE.md)
- 🤖 [Telegram Bot Guide](TELEGRAM_BOT_GUIDE.md)
- 🚀 [Deployment Guide](DEPLOYMENT.md)

## Success! 🎉

Your Crypto Escrow Platform is now running with:
- ✅ Web interface at `http://localhost:3000`
- ✅ API server at `http://localhost:8000`
- ✅ Telegram bot active
- ✅ Background tasks processing
- ✅ Blockchain integration ready

Start trading securely! 🔐💰
