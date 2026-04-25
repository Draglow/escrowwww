# Quick Migration Fix

**Error:** `ValueError: Dependency on app with no migrations: users`

This means migrations need to be created in the correct order.

---

## 🚀 Quick Fix (Windows)

Open Command Prompt in the `backend` folder and run:

```cmd
fix_migrations_simple.bat
```

That's it! The script will create all migrations in the correct order.

---

## 📝 Manual Fix (Step by Step)

If the batch file doesn't work, follow these steps:

### Step 1: Open Command Prompt

```cmd
cd C:\Users\boob\Desktop\escrow\backend
```

### Step 2: Activate Virtual Environment

```cmd
venv\Scripts\activate
```

You should see `(venv)` in your prompt.

### Step 3: Create Migrations in Order

Run these commands **one by one**:

```cmd
python manage.py makemigrations users
```

Wait for it to finish, then:

```cmd
python manage.py makemigrations wallets
```

Then:

```cmd
python manage.py makemigrations deals
```

Then:

```cmd
python manage.py makemigrations ledger
```

Finally:

```cmd
python manage.py makemigrations
```

### Step 4: Apply Migrations

```cmd
python manage.py migrate
```

You should see:
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying users.0001_initial... OK
  Applying wallets.0001_initial... OK
  Applying deals.0001_initial... OK
  Applying ledger.0001_initial... OK
  ...
```

### Step 5: Create Superuser

```cmd
python manage.py createsuperuser
```

Enter:
- Username: `admin`
- Email: `admin@example.com`
- Password: (your choice)

### Step 6: Start Django

```cmd
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

✅ **Success!** Open http://localhost:8000/admin/ in your browser.

---

## 🐧 For Mac/Linux Users

```bash
cd backend
source venv/bin/activate

# Create migrations in order
python manage.py makemigrations users
python manage.py makemigrations wallets
python manage.py makemigrations deals
python manage.py makemigrations ledger
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

---

## ❓ Why This Order?

Django apps have dependencies:

1. **users** - No dependencies (must be first)
2. **wallets** - Depends on users
3. **deals** - Depends on users and wallets
4. **ledger** - Depends on users and deals

We create migrations in this order so each app's dependencies already exist.

---

## 🔍 Verify Everything Works

After migrations are applied:

### 1. Check for Issues
```cmd
python manage.py check
```

Should show: `System check identified no issues (0 silenced).`

### 2. Check Database Tables
```cmd
python manage.py dbshell
```

In the database prompt:
```sql
\dt
```

You should see tables like:
- `users_user`
- `wallets_wallet`
- `deals_deal`
- `ledger_transaction`

Type `\q` to exit.

### 3. Test Admin Panel

1. Start server: `python manage.py runserver`
2. Open: http://localhost:8000/admin/
3. Login with superuser credentials
4. You should see Users, Wallets, Deals, etc.

---

## 🆘 Still Having Issues?

### Error: `No module named 'apps'`

Make sure you're in the `backend` directory:
```cmd
cd C:\Users\boob\Desktop\escrow\backend
```

### Error: `django.core.exceptions.ImproperlyConfigured`

Check your `.env` file exists and has:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://escrow_user:dev_password@localhost:5432/escrow_dev
WALLET_ENCRYPTION_KEY=your-fernet-key
```

### Error: `could not connect to server`

PostgreSQL is not running:
```cmd
net start postgresql-x64-15
```

### Error: `database "escrow_dev" does not exist`

Create the database:
```cmd
psql -U postgres
CREATE DATABASE escrow_dev;
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q
```

---

## 📚 Next Steps

After migrations are working:

1. ✅ **Start all services** (see LOCAL_DEVELOPMENT.md)
   - Terminal 1: Django backend
   - Terminal 2: Celery worker
   - Terminal 3: Celery beat
   - Terminal 4: Frontend

2. ✅ **Test the application**
   - Backend: http://localhost:8000/admin/
   - Frontend: http://localhost:3000
   - API: http://localhost:8000/api/v1/health/

3. ✅ **Read the documentation**
   - LOCAL_DEVELOPMENT.md - Complete setup guide
   - API_DOCUMENTATION.md - API reference
   - TROUBLESHOOTING.md - Common issues

---

**Last Updated:** April 23, 2026

**Quick Command Reference:**
```cmd
cd backend
venv\Scripts\activate
fix_migrations_simple.bat
python manage.py createsuperuser
python manage.py runserver
```
