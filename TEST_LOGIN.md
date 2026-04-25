# 🧪 Testing Login & Authentication

## Quick Test Steps

### 1. Start Backend (if not running)
```bash
cd backend
python manage.py runserver
```

### 2. Start Frontend (if not running)
```bash
cd frontend
npm run dev
```

### 3. Test Login Flow

#### Option A: Development Login Button
1. Open http://localhost:3000
2. Click "Get Started" or "Login"
3. Click the blue "Login with Telegram (Dev)" button
4. You should be redirected to dashboard
5. Check browser console for any errors

#### Option B: Real Telegram Login
1. Configure your bot username in `frontend/.env.local`:
   ```
   NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username
   ```
2. Open http://localhost:3000/login
3. The Telegram widget should appear
4. Click it to login with real Telegram

### 4. Verify Authentication

After login, check:
- ✅ Redirected to `/dashboard`
- ✅ Dashboard shows your name
- ✅ Balance is displayed
- ✅ No 401 errors in console
- ✅ Token saved in localStorage

## 🔍 Debugging Authentication

### Check if Backend is Running
```bash
curl http://localhost:8000/api/v1/health/
```

Should return:
```json
{"status":"healthy","timestamp":"..."}
```

### Check if Frontend Can Reach Backend
Open browser console (F12) and run:
```javascript
fetch('http://localhost:8000/api/v1/health/')
  .then(r => r.json())
  .then(console.log)
```

Should print: `{status: "healthy", ...}`

### Check Authentication Token
After login, open browser console and run:
```javascript
localStorage.getItem('auth_token')
```

Should return a token string, not `null`

### Test API with Token
```javascript
const token = localStorage.getItem('auth_token');
fetch('http://localhost:8000/api/v1/users/me/', {
  headers: {
    'Authorization': `Token ${token}`
  }
})
  .then(r => r.json())
  .then(console.log)
```

Should return your user data

## 🐛 Common Issues

### Issue 1: "Login failed" Alert

**Cause**: Backend not running or wrong URL

**Solution**:
1. Check backend is running: http://localhost:8000
2. Check `.env.local` has correct API URL:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. Restart frontend: `npm run dev`

### Issue 2: Still Getting 401 After Login

**Cause**: Token not being sent with requests

**Solution**:
1. Check token exists:
   ```javascript
   localStorage.getItem('auth_token')
   ```
2. If null, login again
3. Clear cache and try again:
   - F12 > Application > Clear Storage > Clear site data

### Issue 3: CORS Errors

**Cause**: Backend CORS not configured for frontend

**Solution**:
1. Check `backend/.env`:
   ```
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
2. Restart backend

### Issue 4: "Backend not running" Alert

**Cause**: Backend is not started

**Solution**:
```bash
cd backend
python manage.py runserver
```

## 📊 Expected Behavior

### Before Login:
- Landing page loads
- Click "Get Started" → Login page
- See Telegram login button
- Console shows 401 errors (NORMAL)

### During Login:
- Click login button
- Console shows: "Telegram auth data: {...}"
- API call to `/api/v1/users/auth/login/`
- Response with user data and token

### After Login:
- Redirected to `/dashboard`
- Dashboard loads with your data
- No 401 errors
- All API calls return 200 OK

## 🧪 Manual API Test

### Test Login Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/users/auth/login/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Telegram id=123456789&first_name=Test&username=testuser&auth_date=1234567890&hash=test"
```

Should return:
```json
{
  "user": {...},
  "token": "..."
}
```

### Test Protected Endpoint
```bash
# Replace YOUR_TOKEN with actual token
curl http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Token YOUR_TOKEN"
```

Should return your user data

## ✅ Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can access login page
- [ ] Can click login button
- [ ] Login redirects to dashboard
- [ ] Dashboard shows user data
- [ ] No 401 errors after login
- [ ] Token saved in localStorage
- [ ] API calls work with token

## 🎯 Next Steps After Successful Login

1. **Explore Dashboard**
   - View balance
   - Check quick actions
   - See security status

2. **Test Wallet**
   - Go to Wallet page
   - View deposit address
   - Check transaction history

3. **Create Test Deal**
   - Click "Create Deal"
   - Fill in details
   - Submit and view

4. **Try Telegram Bot**
   - Open Telegram
   - Find your bot
   - Send `/start`
   - Compare with web app

## 💡 Pro Tips

1. **Keep DevTools Open**: F12 to see all API calls
2. **Check Network Tab**: See request/response details
3. **Check Console Tab**: See any JavaScript errors
4. **Check Application Tab**: View localStorage and cookies

## 🆘 Still Having Issues?

1. Run verification script:
   ```bash
   cd backend
   python verify_setup.py
   ```

2. Check all services are running:
   - Backend: http://localhost:8000
   - Frontend: http://localhost:3000
   - Redis: `redis-cli ping`

3. Check logs:
   - Backend: Terminal where `runserver` is running
   - Frontend: Browser console (F12)

4. Try clearing everything:
   ```bash
   # Clear browser cache
   F12 > Application > Clear Storage > Clear site data
   
   # Restart frontend
   cd frontend
   npm run dev
   
   # Restart backend
   cd backend
   python manage.py runserver
   ```

## 🎉 Success!

Once you can login and see the dashboard without 401 errors, you're all set!

The platform is working correctly, and you can start:
- Managing your wallet
- Creating deals
- Using the Telegram bot
- Exploring all features

**Happy trading! 🚀**
