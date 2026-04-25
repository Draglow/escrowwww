# Manual Render Deployment Guide

This guide is for deploying services manually (one by one) instead of using Blueprint.

## 🔧 Fix for coincurve Build Error

The `coincurve` package (required by `tronpy`) needs system libraries to compile. Here's how to fix it:

### Solution 1: Using render.yaml in backend folder (Recommended)

A `backend/render.yaml` file has been created with the required system packages:

```yaml
packages:
  - build-essential
  - libssl-dev
  - libffi-dev
  - python3-dev
  - pkg-config
  - libsecp256k1-dev
```

**This file must be committed to your repository.** Render will automatically detect it and install these packages.

### Solution 2: Alternative Build Command

If the render.yaml doesn't work, use this build command in Render dashboard:

```bash
pip install --upgrade pip setuptools wheel && pip install coincurve --no-binary coincurve && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

### Solution 3: Install via Render Dashboard

In your Render service settings:
1. Go to **Environment** tab
2. Add environment variable:
   - Key: `PYTHON_VERSION`
   - Value: `3.11.9`

Then use this build command:
```bash
apt-get update && apt-get install -y build-essential libssl-dev libffi-dev python3-dev pkg-config libsecp256k1-dev && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

---

## 📋 Step-by-Step Manual Deployment

### 1. Create PostgreSQL Database

1. Go to Render Dashboard
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: `escrow-postgres`
   - **Database**: `escrow_db`
   - **User**: `escrow_user`
   - **Region**: Oregon (or your preferred)
   - **Plan**: Starter ($7/month)
4. Click **Create Database**
5. **Save the Internal Database URL** (you'll need it later)

---

### 2. Create Redis Instance

1. Click **New** → **Redis**
2. Configure:
   - **Name**: `escrow-redis`
   - **Region**: Oregon (same as database)
   - **Plan**: Starter ($10/month)
   - **Maxmemory Policy**: `allkeys-lru`
3. Click **Create Redis**
4. **Save the Internal Redis URL**

---

### 3. Create Backend Web Service

1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:

**Basic Settings:**
- **Name**: `escrow-backend`
- **Region**: Oregon
- **Branch**: `main` (or your default branch)
- **Root Directory**: `backend`
- **Runtime**: Python 3
- **Build Command**:
  ```bash
  pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
  ```
- **Start Command**:
  ```bash
  daphne -b 0.0.0.0 -p $PORT config.asgi:application
  ```

**Advanced Settings:**
- **Health Check Path**: `/api/v1/health/`
- **Plan**: Starter ($7/month)

4. Click **Create Web Service** (don't deploy yet)

---

### 4. Configure Backend Environment Variables

In the backend service, go to **Environment** tab and add these variables:

#### Auto-Generated Keys
```bash
SECRET_KEY=<click "Generate" button>
WALLET_ENCRYPTION_KEY=<click "Generate" button>
```

#### Database & Redis (from step 1 & 2)
```bash
DATABASE_URL=<paste Internal Database URL from step 1>
REDIS_URL=<paste Internal Redis URL from step 2>
CELERY_BROKER_URL=<paste Internal Redis URL from step 2>
CELERY_RESULT_BACKEND=<paste Internal Redis URL from step 2>
```

#### Django Settings
```bash
DEBUG=False
PYTHON_VERSION=3.11.9
ALLOWED_HOSTS=<your-backend-url>.onrender.com
```

#### Tron Blockchain
```bash
TRON_NETWORK=mainnet
TRONGRID_API_KEY=<your-trongrid-api-key>
TRON_FULL_NODE=https://api.trongrid.io
TRON_SOLIDITY_NODE=https://api.trongrid.io
TRON_EVENT_SERVER=https://api.trongrid.io
```

#### Telegram
```bash
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
```

#### Platform Settings
```bash
PLATFORM_FEE_PERCENTAGE=2.5
MIN_DEAL_AMOUNT=10.00
MAX_DEAL_AMOUNT=100000.00
```

#### CORS & Frontend (update after frontend is deployed)
```bash
CORS_ALLOWED_ORIGINS=https://<your-frontend-url>.onrender.com
FRONTEND_URL=https://<your-frontend-url>.onrender.com
```

#### WebAuthn (update after frontend is deployed)
```bash
WEBAUTHN_RP_ID=<your-frontend-url>.onrender.com
WEBAUTHN_RP_NAME=Escrow Platform
WEBAUTHN_ALLOWED_ORIGINS=https://<your-frontend-url>.onrender.com
```

5. Click **Save Changes**
6. **Manual Deploy** → **Deploy latest commit**

---

### 5. Create Celery Worker

1. Click **New** → **Background Worker**
2. Connect same repository
3. Configure:

**Basic Settings:**
- **Name**: `escrow-celery-worker`
- **Region**: Oregon
- **Branch**: `main`
- **Root Directory**: `backend`
- **Build Command**:
  ```bash
  pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  celery -A config worker -l info
  ```

**Environment Variables** (same as backend):
```bash
SECRET_KEY=<copy from backend>
WALLET_ENCRYPTION_KEY=<copy from backend>
DATABASE_URL=<copy from backend>
REDIS_URL=<copy from backend>
CELERY_BROKER_URL=<copy from backend>
CELERY_RESULT_BACKEND=<copy from backend>
DEBUG=False
PYTHON_VERSION=3.11.9
TRON_NETWORK=mainnet
TRONGRID_API_KEY=<your-api-key>
TELEGRAM_BOT_TOKEN=<your-bot-token>
```

4. Click **Create Background Worker**

---

### 6. Create Celery Beat (Optional)

1. Click **New** → **Background Worker**
2. Connect same repository
3. Configure:

**Basic Settings:**
- **Name**: `escrow-celery-beat`
- **Region**: Oregon
- **Branch**: `main`
- **Root Directory**: `backend`
- **Build Command**:
  ```bash
  pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
  ```

**Environment Variables** (minimal set):
```bash
SECRET_KEY=<copy from backend>
DATABASE_URL=<copy from backend>
REDIS_URL=<copy from backend>
CELERY_BROKER_URL=<copy from backend>
CELERY_RESULT_BACKEND=<copy from backend>
DEBUG=False
PYTHON_VERSION=3.11.9
```

4. Click **Create Background Worker**

---

### 7. Create Frontend Web Service

1. Click **New** → **Web Service**
2. Connect same repository
3. Configure:

**Basic Settings:**
- **Name**: `escrow-frontend`
- **Region**: Oregon
- **Branch**: `main`
- **Root Directory**: `frontend`
- **Runtime**: Node
- **Build Command**:
  ```bash
  npm install && npm run build
  ```
- **Start Command**:
  ```bash
  npm start
  ```

**Environment Variables:**
```bash
NODE_VERSION=18.17.0
NEXT_PUBLIC_API_URL=https://<your-backend-url>.onrender.com
NEXT_PUBLIC_WS_URL=wss://<your-backend-url>.onrender.com
NEXT_PUBLIC_TELEGRAM_BOT_NAME=<your-bot-username>
NEXT_PUBLIC_APP_NAME=CryptoEscrow
NEXT_PUBLIC_APP_URL=https://<your-frontend-url>.onrender.com
NEXT_PUBLIC_WEBAUTHN_RP_ID=<your-frontend-url>.onrender.com
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_SENTRY=false
```

4. Click **Create Web Service**

---

### 8. Update Backend Environment Variables

Now that you have the frontend URL, go back to backend service and update:

```bash
ALLOWED_HOSTS=<backend-url>.onrender.com,<frontend-url>.onrender.com
CORS_ALLOWED_ORIGINS=https://<frontend-url>.onrender.com
FRONTEND_URL=https://<frontend-url>.onrender.com
WEBAUTHN_RP_ID=<frontend-url>.onrender.com
WEBAUTHN_ALLOWED_ORIGINS=https://<frontend-url>.onrender.com
```

Then **Manual Deploy** → **Deploy latest commit**

---

## ✅ Verification

### 1. Check Backend Health
```bash
curl https://<your-backend>.onrender.com/api/v1/health/
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Check Frontend
Visit: `https://<your-frontend>.onrender.com`

### 3. Check Admin Panel
Visit: `https://<your-backend>.onrender.com/admin/`

### 4. Create Superuser
In backend service shell:
```bash
python manage.py createsuperuser
```

---

## 🆘 Troubleshooting coincurve Error

If you still get the coincurve error after following the steps above:

### Option 1: Check render.yaml exists
```bash
# Make sure this file exists and is committed:
backend/render.yaml
```

### Option 2: Use pre-built wheel
Update your build command to:
```bash
pip install --upgrade pip setuptools wheel && pip install --prefer-binary coincurve && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

### Option 3: Install system packages manually
Use this build command:
```bash
apt-get update && apt-get install -y build-essential libssl-dev libffi-dev python3-dev pkg-config && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

### Option 4: Use different Python version
Try Python 3.11.9 or 3.10.x:
```bash
PYTHON_VERSION=3.11.9
```

### Option 5: Check build logs
Look for specific error messages about missing libraries and install them:
```bash
# If you see "fatal error: secp256k1.h: No such file or directory"
apt-get install -y libsecp256k1-dev

# If you see "fatal error: openssl/opensslv.h: No such file or directory"
apt-get install -y libssl-dev
```

---

## 📝 Important Notes

1. **Commit backend/render.yaml**: This file must be in your repository
2. **Wait for builds**: Each service takes 5-10 minutes to build
3. **Check logs**: If deployment fails, check the logs for specific errors
4. **Update URLs**: After each service is deployed, update environment variables with actual URLs
5. **Restart services**: After updating environment variables, manually redeploy affected services

---

## 💰 Cost Summary

- PostgreSQL: $7/month
- Redis: $10/month
- Backend: $7/month
- Celery Worker: $7/month
- Celery Beat: $7/month
- Frontend: $7/month
- **Total: $45/month**

---

## 🎉 Success!

Once all services show "Healthy" status:
1. ✅ Backend health check returns 200
2. ✅ Frontend loads without errors
3. ✅ Can create superuser
4. ✅ Can log in to admin panel
5. ✅ API endpoints work
6. ✅ WebSocket connections work

You're ready to use your deployed application!
