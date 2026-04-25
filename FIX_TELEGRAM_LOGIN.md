# 🔧 Fix Telegram Login - Quick Action Guide

## 🎯 What You Need to Do (3 Steps)

### Step 1: Find Your Bot Username

1. Open Telegram
2. Search for `@BotFather`
3. Send `/mybots`
4. Select your bot
5. Look for the username (ends with `_bot`)

**Example**: `cryptoescrow_bot` or `myescrow_bot`

### Step 2: Update Frontend Configuration

Edit `frontend/.env.local` and replace `your_bot_username`:

```env
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_actual_bot_username
```

**Example**:
```env
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=cryptoescrow_bot
```

### Step 3: Restart Frontend

```bash
cd frontend
npm run dev
```

## ✅ Test It Works

### Test Telegram Bot:
1. Open Telegram
2. Find your bot
3. Send `/start`
4. Click "🌐 Login to Web App" button
5. Should open browser to login page

### Test Web Login:
1. Open http://localhost:3000/login
2. Should see Telegram login widget
3. Click "Login with Telegram (Dev)" button
4. Should redirect to dashboard

## 🚀 Quick Fix Commands

```bash
# 1. Update .env.local with your bot username
# Edit: frontend/.env.local
# Change: NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username

# 2. Restart frontend
cd frontend
npm run dev

# 3. Restart bot (if needed)
cd backend
python manage.py run_telegram_bot
```

## 💡 Pro Tip

If you don't know your bot username:
1. Go to @BotFather in Telegram
2. Send `/mybots`
3. Select your bot
4. The username is shown at the top

## 🎉 Done!

After these 3 steps:
- ✅ Bot will show login link
- ✅ Web login will work
- ✅ Users can login from both

**See [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) for detailed guide**
