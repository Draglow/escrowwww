# Telegram Bot Setup & Usage Guide

## 🤖 Overview

The Crypto Escrow Platform includes a fully-featured Telegram bot that allows users to manage their wallets, create deals, and perform transactions directly from Telegram.

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL database
- Redis server
- Telegram Bot Token (from @BotFather)
- All backend dependencies installed

## 🚀 Quick Start

### 1. Get Your Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Copy the bot token provided
5. Add the token to your `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 2. Configure Environment

Make sure your `backend/.env` file has all required settings:

```env
# Django Settings
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=8520329938:AAH6C1UeEcXRk1wslMq6KVwJUn39zQ-GsGk

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Platform Settings
PLATFORM_FEE_PERCENTAGE=2.5
MIN_DEAL_AMOUNT=10.00
MAX_DEAL_AMOUNT=100000.00
```

### 3. Start Required Services

#### Start PostgreSQL
```bash
# Windows (if using local PostgreSQL)
net start postgresql

# Or use your Railway/cloud database
```

#### Start Redis
```bash
# Windows
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

#### Start Django Backend
```bash
cd backend
python manage.py migrate
python manage.py runserver
```

#### Start Celery Worker (for background tasks)
```bash
cd backend
celery -A config worker -l info --pool=solo
```

### 4. Start the Telegram Bot

#### On Windows:
```bash
cd backend
python manage.py run_telegram_bot
```

Or use the batch file:
```bash
cd backend
start_telegram_bot.bat
```

#### On Linux/Mac:
```bash
cd backend
chmod +x start_telegram_bot.sh
./start_telegram_bot.sh
```

## 🎯 Bot Features

### Available Commands

- `/start` - Main menu and welcome message
- `/wallet` - View wallet balance and options
- `/deals` - View your deals
- `/help` - Show help information
- `/cancel` - Cancel current operation

### Main Features

#### 💰 Wallet Management
- **View Balance**: Check your USDT balance
- **Deposit**: Get your TRC20 address for deposits
- **Withdraw**: Send USDT to external addresses
- **Transaction History**: View all transactions

#### 📋 Deal Management
- **Create Deal**: Start a new escrow deal
- **View Deals**: See all your active and completed deals
- **Fund Deal**: Lock funds in escrow (seller)
- **Start Deal**: Begin the deal process (buyer)
- **Complete Deal**: Release funds (buyer)
- **Cancel Deal**: Cancel and refund

#### 🔐 Security Features
- **2FA Support**: Two-factor authentication for withdrawals
- **Secure Transactions**: All operations are logged
- **Real-time Updates**: Instant notifications

## 📱 Using the Bot

### 1. First Time Setup

1. Open Telegram and search for your bot
2. Send `/start` command
3. Your account will be created automatically
4. You'll see your wallet balance and main menu

### 2. Depositing Funds

1. Click "💰 My Wallet"
2. Click "💳 Deposit"
3. Copy your TRC20 address
4. Send USDT (TRC20 network only) to this address
5. Wait for blockchain confirmation
6. Your balance updates automatically

### 3. Creating a Deal

1. Click "➕ Create Deal" or use the web app
2. Enter deal details:
   - Title
   - Description
   - Amount
   - Buyer/Seller information
3. Share the deal with the other party
4. Seller funds the escrow
5. Buyer starts the deal
6. After delivery, buyer completes the deal

### 4. Withdrawing Funds

1. Click "💰 My Wallet"
2. Click "💸 Withdraw"
3. Enter TRC20 address
4. Enter amount
5. If 2FA is enabled, enter your code
6. Confirm withdrawal
7. Wait for processing

## 🔧 Troubleshooting

### Bot Not Responding

1. Check if the bot process is running
2. Verify your bot token is correct
3. Check Redis connection
4. Check database connection
5. Review logs for errors

### Deposits Not Showing

1. Ensure you sent USDT on TRC20 network
2. Wait for blockchain confirmation (usually 1-2 minutes)
3. Check if Celery worker is running
4. Check deposit monitoring task logs

### Withdrawals Failing

1. Verify you have sufficient available balance
2. Check if 2FA code is correct (if enabled)
3. Ensure TRC20 address is valid
4. Check if Celery worker is running
5. Review withdrawal task logs

## 📊 Monitoring

### Check Bot Status
```bash
# View bot logs
tail -f backend/logs/telegram_bot.log

# Check if process is running
ps aux | grep run_telegram_bot
```

### Check Celery Tasks
```bash
# View Celery logs
celery -A config inspect active

# Check task status
celery -A config inspect stats
```

### Database Queries
```python
# Check user count
python manage.py shell
>>> from apps.users.models import User
>>> User.objects.count()

# Check recent deals
>>> from apps.deals.models import Deal
>>> Deal.objects.order_by('-created_at')[:5]
```

## 🌐 Web App Integration

The bot seamlessly integrates with the web application:

1. **Open Web App Button**: Direct link to the web dashboard
2. **Shared Authentication**: Same account across bot and web
3. **Real-time Sync**: Changes in bot reflect in web and vice versa
4. **Unified Balance**: Single wallet for both interfaces

### Accessing Web App

1. From bot: Click "🌐 Open Web App"
2. Or visit: `http://localhost:3000`
3. Login with Telegram
4. All your data is synced

## 🔐 Security Best Practices

1. **Enable 2FA**: Always enable two-factor authentication
2. **Secure Bot Token**: Never share your bot token
3. **Use HTTPS**: In production, always use HTTPS
4. **Regular Backups**: Backup your database regularly
5. **Monitor Logs**: Check logs for suspicious activity
6. **Update Dependencies**: Keep all packages up to date

## 📝 Development Tips

### Testing the Bot Locally

```python
# Test bot commands
python manage.py shell
>>> from apps.telegram_bot.bot import bot
>>> # Test functions here
```

### Adding New Commands

1. Add handler method in `bot.py`
2. Register handler in `setup_handlers()`
3. Test thoroughly
4. Update documentation

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Production Deployment

### Environment Variables

```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com
TELEGRAM_BOT_TOKEN=your_production_token
DATABASE_URL=your_production_database
REDIS_URL=your_production_redis
FRONTEND_URL=https://your-domain.com
```

### Running as Service

#### Using systemd (Linux):

Create `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Crypto Escrow Telegram Bot
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python manage.py run_telegram_bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

#### Using PM2 (Node.js process manager):

```bash
pm2 start "python manage.py run_telegram_bot" --name telegram-bot
pm2 save
pm2 startup
```

## 📞 Support

For issues or questions:
- Check logs in `backend/logs/`
- Review error messages
- Check database connectivity
- Verify all services are running
- Contact support team

## 🎉 Success!

Your Telegram bot is now running! Users can:
- ✅ Create accounts automatically
- ✅ Manage wallets
- ✅ Create and manage deals
- ✅ Deposit and withdraw funds
- ✅ Access the web app
- ✅ Get real-time notifications

Enjoy your secure escrow platform! 🚀
