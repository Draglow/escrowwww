# 🚀 Quick Start Guide - Get Running in 2 Minutes

## Understanding the 401 Errors

The errors you're seeing are **NORMAL** and expected! Here's why:

```
WARNING HTTP GET /api/v1/wallets/balance/ 401 [0.14, 127.0.0.1:3433]
```

**401 = Unauthorized** - This means:
- ✅ Backend server is running correctly
- ✅ Frontend is running correctly
- ⚠️ You just need to **login first**

## 🎯 Step-by-Step Solution

### Step 1: Make Sure Backend is Running

Your backend should be running on http://localhost:8000

Check by opening: http://localhost:8000/api/v1/health/

You should see:
```json
{
  "status": "healthy",
  "timestamp": "..."
}
```

### Step 2: Make Sure Frontend is Running

Your frontend should be running on http://localhost:3000

### Step 3: Login to Get Authentication Token

1. **Open your browser**: http://localhost:3000
2. **Click "Get Started"** or **"Login"**
3. **Click the Telegram Login button**
4. **Authorize the app** in Telegram
5. **You'll be redirected to dashboard** with authentication

### Step 4: After Login - Everything Works!

Once logged in:
- ✅ API calls will have authentication token
- ✅ No more 401 errors
- ✅ Dashboard loads with your data
- ✅ Wallet shows your balance
- ✅ You can create deals

## 🔧 If Backend Isn't Running

### Start Backend:
```bash
cd backend
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Start Celery (in another terminal):
```bash
cd backend
celery -A config worker -l info --pool=solo
```

### Start Telegram Bot (in another terminal):
```bash
cd backend
python manage.py run_telegram_bot
```

## 🌐 If Frontend Isn't Running

### Start Frontend:
```bash
cd frontend
npm run dev
```

You should see:
```
- Local:        http://localhost:3000
- Ready in 2.5s
```

## 🔐 How Authentication Works

1. **Before Login**:
   - No token in localStorage
   - API calls return 401 Unauthorized
   - You see login page

2. **After Login**:
   - Token saved in localStorage
   - Token sent with every API request
   - API returns your data
   - You see dashboard

## 🧪 Test Your Setup

### 1. Check Backend Health
```bash
curl http://localhost:8000/api/v1/health/
```

Should return:
```json
{"status": "healthy"}
```

### 2. Check Frontend
Open: http://localhost:3000

Should show the landing page with "Get Started" button

### 3. Login Flow
1. Click "Get Started"
2. Click Telegram login button
3. Authorize in Telegram
4. Get redirected to dashboard
5. See your balance and wallet

## 🐛 Troubleshooting

### Backend Not Starting?

**Error**: Port 8000 already in use
```bash
# Windows - Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Then start again
python manage.py runserver
```

**Error**: Database connection failed
- Check your `.env` file
- Verify `DATABASE_URL` is correct
- Test connection: `python verify_setup.py`

### Frontend Not Starting?

**Error**: Port 3000 already in use
```bash
# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Then start again
npm run dev
```

**Error**: Module not found
```bash
cd frontend
npm install
npm run dev
```

### Still Getting 401 Errors After Login?

1. **Clear browser cache and localStorage**:
   - Open DevTools (F12)
   - Go to Application tab
   - Clear Storage
   - Refresh page

2. **Check if token is saved**:
   - Open DevTools (F12)
   - Go to Application > Local Storage
   - Look for `auth_token`
   - If missing, login again

3. **Check API URL**:
   - Open `frontend/.env.local`
   - Verify: `NEXT_PUBLIC_API_URL=http://localhost:8000`

## 📱 Using Telegram Bot

While the web app is running, you can also use the Telegram bot:

1. **Open Telegram**
2. **Search for your bot** (the username from @BotFather)
3. **Send** `/start`
4. **Try commands**:
   - `/wallet` - View wallet
   - `/deals` - View deals
   - `/help` - Get help

## ✅ Success Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Can access landing page
- [ ] Can click "Get Started"
- [ ] Can see Telegram login button
- [ ] Can login with Telegram
- [ ] Redirected to dashboard after login
- [ ] Dashboard shows balance
- [ ] No more 401 errors in console

## 🎯 What to Do After Login

### 1. Explore Dashboard
- View your balance
- Check security status
- See quick actions

### 2. Get Your Deposit Address
- Click "Wallet" in navigation
- Click "Deposit" tab
- Copy your TRC20 address
- Send USDT to this address (testnet or mainnet)

### 3. Create a Test Deal
- Click "Create Deal" button
- Fill in deal details
- Submit the deal
- View in deals list

### 4. Try Telegram Bot
- Open Telegram
- Find your bot
- Send `/start`
- Explore bot features

## 🔥 Common Mistakes

### ❌ Mistake 1: Not Starting Backend
**Symptom**: ERR_CONNECTION_REFUSED
**Solution**: Start backend with `python manage.py runserver`

### ❌ Mistake 2: Not Starting Frontend
**Symptom**: Can't access http://localhost:3000
**Solution**: Start frontend with `npm run dev`

### ❌ Mistake 3: Trying to Access API Before Login
**Symptom**: 401 Unauthorized errors
**Solution**: Login first through the web app

### ❌ Mistake 4: Wrong API URL
**Symptom**: CORS errors or connection refused
**Solution**: Check `frontend/.env.local` has correct API URL

### ❌ Mistake 5: Forgot to Start Redis
**Symptom**: Celery or cache errors
**Solution**: Start Redis with `redis-server`

## 📊 Expected Behavior

### Before Login:
```
Browser Console:
❌ GET http://localhost:8000/api/v1/wallets/balance/ 401 (Unauthorized)
❌ GET http://localhost:8000/api/v1/deals/ 401 (Unauthorized)
```
**This is NORMAL!** You need to login first.

### After Login:
```
Browser Console:
✅ GET http://localhost:8000/api/v1/wallets/balance/ 200 (OK)
✅ GET http://localhost:8000/api/v1/deals/ 200 (OK)
✅ GET http://localhost:8000/api/v1/users/me/ 200 (OK)
```
**Perfect!** Everything is working.

## 🎉 You're All Set!

Once you login, you'll have:
- ✅ Full access to your dashboard
- ✅ Working wallet
- ✅ Ability to create deals
- ✅ Real-time updates
- ✅ Telegram bot access

## 💡 Pro Tips

1. **Keep terminals open** to see logs
2. **Use browser DevTools** (F12) to debug
3. **Check Network tab** to see API calls
4. **Check Console tab** for errors
5. **Clear cache** if things seem stuck

## 🆘 Need More Help?

1. Check [START_HERE.md](START_HERE.md) for detailed setup
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
3. Run `python verify_setup.py` to check configuration
4. Check backend logs in terminal
5. Check frontend logs in browser console

## 🚀 Ready to Go!

**Your platform is working correctly!**

The 401 errors are just telling you to login first. Once you login through Telegram, everything will work perfectly!

**Next Step**: Open http://localhost:3000 and click "Get Started" to login! 🎯
