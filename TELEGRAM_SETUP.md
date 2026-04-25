# 🤖 Telegram Bot & Login Setup Guide

## 📋 Prerequisites

You need:
1. A Telegram account
2. Your bot token (already in `.env`)
3. Your bot username

## 🚀 Quick Setup

### Step 1: Get Your Bot Username

Your bot token is already configured:
```
TELEGRAM_BOT_TOKEN=8520329938:AAH6C1UeEcXRk1wslMq6KVwJUn39zQ-GsGk
```

Now you need to find your bot's username:

1. **Open Telegram**
2. **Search for** `@BotFather`
3. **Send** `/mybots`
4. **Select your bot**
5. **Look for the username** (it should end with `_bot`)

Example: If your bot is called "CryptoEscrow Bot", the username might be `cryptoescrow_bot`

### Step 2: Configure Frontend

Edit `frontend/.env.local`:

```env
# Replace 'your_bot_username' with your actual bot username (without @)
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username

# Example:
# NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=cryptoescrow_bot
```

### Step 3: Set Bot Domain (Important!)

1. **Open Telegram** and go to `@BotFather`
2. **Send** `/mybots`
3. **Select your bot**
4. **Click** "Bot Settings"
5. **Click** "Domain"
6. **Enter**: `localhost` (for development) or your domain (for production)

This allows the Telegram Login Widget to work on your domain.

### Step 4: Restart Frontend

```bash
cd frontend
npm run dev
```

## ✅ Testing the Setup

### Test 1: Telegram Bot Login Link

1. **Open Telegram**
2. **Find your bot** (search for the username)
3. **Send** `/start`
4. **You should see**:
   - Welcome message
   - Your balance
   - Button: "🌐 Login to Web App"
5. **Click the button**
   - Should open your browser
   - Should go to login page

### Test 2: Web Login Widget

1. **Open browser**: http://localhost:3000/login
2. **You should see**:
   - Telegram login widget (blue button)
   - Development login button (below)
3. **Click Telegram widget**:
   - Opens Telegram
   - Asks for permission
   - Redirects back to dashboard

### Test 3: Development Login

1. **Open browser**: http://localhost:3000/login
2. **Click** "Login with Telegram (Dev)" button
3. **Should**:
   - Show "Logging in..." spinner
   - Redirect to dashboard
   - Show your balance

## 🐛 Troubleshooting

### Issue 1: "your_bot" in Login Widget

**Problem**: Login widget shows "your_bot" instead of your bot name

**Solution**:
1. Check `frontend/.env.local` has correct bot username
2. Restart frontend: `npm run dev`
3. Clear browser cache (Ctrl+Shift+Delete)
4. Refresh page

### Issue 2: Telegram Widget Not Showing

**Problem**: No Telegram login button appears

**Causes & Solutions**:

**A. Bot username not configured**
```bash
# Check frontend/.env.local
cat frontend/.env.local

# Should show:
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_actual_bot_username
```

**B. Domain not set in BotFather**
1. Go to @BotFather
2. /mybots → Your Bot → Bot Settings → Domain
3. Add: `localhost`

**C. Script blocked by browser**
- Check browser console (F12)
- Look for script loading errors
- Try different browser

### Issue 3: Bot /start Button Does Nothing

**Problem**: Click "🌐 Login to Web App" but nothing happens

**Solution**:
1. Check `backend/.env` has correct `FRONTEND_URL`:
   ```
   FRONTEND_URL=http://localhost:3000
   ```
2. Restart bot:
   ```bash
   cd backend
   python manage.py run_telegram_bot
   ```
3. Try `/start` again

### Issue 4: Login Fails with Error

**Problem**: Click login but get error message

**Causes & Solutions**:

**A. Backend not running**
```bash
# Start backend
cd backend
python manage.py runserver
```

**B. Wrong API URL**
```bash
# Check frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**C. CORS issue**
```bash
# Check backend/.env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 📱 Complete Flow

### User Journey:

```
1. User opens Telegram
   ↓
2. User finds your bot
   ↓
3. User sends /start
   ↓
4. Bot shows welcome + "Login to Web App" button
   ↓
5. User clicks button
   ↓
6. Browser opens to login page
   ↓
7. User clicks Telegram login widget
   ↓
8. Telegram asks for permission
   ↓
9. User approves
   ↓
10. Backend creates/logs in user
   ↓
11. Frontend saves token
   ↓
12. User redirected to dashboard
   ↓
13. ✅ Success! User is logged in
```

## 🔐 Security Notes

### Development vs Production

**Development** (localhost):
- Use development login button for testing
- Telegram widget works but needs domain setup
- Bot links work locally

**Production** (your-domain.com):
- Remove development login button
- Configure proper domain in BotFather
- Use HTTPS (required by Telegram)
- Update all URLs in .env files

### Bot Token Security

⚠️ **IMPORTANT**: Never commit your bot token to Git!

```bash
# Make sure .env is in .gitignore
echo "backend/.env" >> .gitignore
echo "frontend/.env.local" >> .gitignore
```

## 📊 Configuration Checklist

- [ ] Bot token in `backend/.env`
- [ ] Bot username in `frontend/.env.local`
- [ ] Domain set in BotFather
- [ ] Frontend URL in `backend/.env`
- [ ] API URL in `frontend/.env.local`
- [ ] CORS configured in `backend/.env`
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Bot running (python manage.py run_telegram_bot)

## 🎯 Quick Commands

```bash
# Get bot info from BotFather
# Open Telegram → @BotFather → /mybots → Select your bot

# Check current configuration
cat backend/.env | grep TELEGRAM
cat frontend/.env.local | grep TELEGRAM

# Restart services
# Backend:
cd backend && python manage.py runserver

# Bot:
cd backend && python manage.py run_telegram_bot

# Frontend:
cd frontend && npm run dev
```

## ✨ Expected Behavior

### After Proper Setup:

**Telegram Bot**:
- `/start` shows welcome message
- "🌐 Login to Web App" button appears
- Clicking button opens browser to login page
- User info syncs between bot and web

**Web Login**:
- Telegram widget shows your bot name
- Clicking widget opens Telegram
- After approval, redirects to dashboard
- Token saved, user logged in

**Both Work Together**:
- Same account on bot and web
- Balance syncs
- Deals sync
- Real-time updates

## 🆘 Still Having Issues?

1. **Check all environment variables**:
   ```bash
   # Backend
   cat backend/.env
   
   # Frontend
   cat frontend/.env.local
   ```

2. **Verify bot is running**:
   ```bash
   # Should see: "Starting Telegram bot..."
   cd backend
   python manage.py run_telegram_bot
   ```

3. **Test bot manually**:
   - Open Telegram
   - Send `/start` to your bot
   - Check terminal for logs

4. **Test web login**:
   - Open http://localhost:3000/login
   - Click dev login button
   - Should work even if widget doesn't

5. **Check browser console**:
   - F12 → Console tab
   - Look for errors
   - Check Network tab for failed requests

## 🎉 Success!

Once everything is configured:
- ✅ Bot responds to `/start`
- ✅ Bot provides login link
- ✅ Web login widget works
- ✅ Users can login from both bot and web
- ✅ Data syncs between platforms

**You're all set! Start trading! 🚀**
