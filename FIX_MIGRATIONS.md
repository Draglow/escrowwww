# Fix Migrations Guide

This guide will help you fix the migration error and get your database working.

**Error:** `NodeNotFoundError: Migration users.0002_add_2fa_and_audit dependencies reference nonexistent parent node ('users', '0001_initial')`

---

## Quick Fix (Recommended)

### Option 1: Automated Script (Easiest)

I've created a script that will automatically fix everything:

**Windows:**
```cmd
cd backend
reset_migrations.bat
```

**Mac/Linux:**
```bash
cd backend
source venv/bin/activate
python reset_migrations.py
```

This script will:
1. ✅ Delete all broken migration files
2. ✅ Drop all database tables
3. ✅ Generate fresh migrations
4. ✅ Apply migrations to database

---

## Manual Fix (If Script Doesn't Work)

### Step 1: Activate Virtual Environment

**Windows:**
```cmd
cd backend
venv\Scripts\activate
```

**Mac/Linux:**
```bash
cd backend
source venv/bin/activate
```

### Step 2: Delete Broken Migration Files

The problematic migrations have already been deleted, but if you see more errors, delete them:

```bash
# Delete all migration files except __init__.py
# Windows (PowerShell):
Get-ChildItem -Path apps\*/migrations\*.py -Exclude __init__.py | Remove-Item

# Mac/Linux:
find apps/*/migrations -name "*.py" ! -name "__init__.py" -delete
```

### Step 3: Drop All Database Tables

**Option A - Using psql:**
```bash
psql -U escrow_user -d escrow_dev -h localhost

# In psql, run:
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO escrow_user;
GRANT ALL ON SCHEMA public TO public;
\q
```

**Option B - Drop and recreate database:**
```bash
psql -U postgres

# In psql:
DROP DATABASE escrow_dev;
CREATE DATABASE escrow_dev;
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q
```

### Step 4: Generate Fresh Migrations

```bash
python manage.py makemigrations
```

You should see:
```
Migrations for 'users':
  apps/users/migrations/0001_initial.py
    - Create model User
    - Create model AuditLog
Migrations for 'wallets':
  apps/wallets/migrations/0001_initial.py
    - Create model Wallet
...
```

### Step 5: Apply Migrations

```bash
python manage.py migrate
```

You should see:
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying users.0001_initial... OK
  Applying wallets.0001_initial... OK
  ...
```

### Step 6: Create Superuser

```bash
python manage.py createsuperuser

# Enter:
# Username: admin
# Email: admin@example.com
# Password: (your choice)
```

### Step 7: Verify Everything Works

```bash
# Check for issues
python manage.py check

# Start server
python manage.py runserver
```

---

## Understanding the Problem

### What Happened?

The project had migration files like:
- `users/migrations/0002_add_2fa_and_audit.py` (exists)
- `users/migrations/0001_initial.py` (missing!)

Migration `0002` depends on `0001`, but `0001` doesn't exist, causing the error.

### Why Did This Happen?

This typically happens when:
1. Migration files were deleted manually
2. Git operations removed files
3. Switching between Docker and native setup
4. Database and migration files got out of sync

### The Solution

We need to:
1. Delete all migration files (except `__init__.py`)
2. Clear the database
3. Generate fresh migrations from models
4. Apply migrations to create tables

---

## Troubleshooting

### Error: `psql: command not found`

PostgreSQL is not in your PATH.

**Windows:**
Add to PATH: `C:\Program Files\PostgreSQL\15\bin`

**Mac:**
```bash
brew install postgresql@15
```

**Linux:**
```bash
sudo apt install postgresql-client
```

### Error: `FATAL: password authentication failed`

Wrong password in `.env` file.

**Fix:**
```bash
# Reset password
psql -U postgres
ALTER USER escrow_user WITH PASSWORD 'dev_password';
\q

# Or update .env with correct password
```

### Error: `database "escrow_dev" does not exist`

Database wasn't created.

**Fix:**
```bash
psql -U postgres
CREATE DATABASE escrow_dev;
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q
```

### Error: `permission denied for schema public`

User doesn't have schema permissions.

**Fix:**
```bash
psql -U postgres -d escrow_dev
GRANT ALL ON SCHEMA public TO escrow_user;
\q
```

### Script Fails with Import Error

Virtual environment not activated or dependencies not installed.

**Fix:**
```bash
# Activate venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## After Fixing Migrations

Once migrations are fixed, you need to:

### 1. Create Superuser
```bash
python manage.py createsuperuser
```

### 2. Start All Services

**Terminal 1 - Django:**
```bash
cd backend
venv\Scripts\activate
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
venv\Scripts\activate
celery -A config worker -l info --pool=solo
```

**Terminal 3 - Celery Beat:**
```bash
cd backend
venv\Scripts\activate
celery -A config beat -l info
```

**Terminal 4 - Frontend:**
```bash
cd frontend
npm run dev
```

### 3. Test Everything

- Backend: http://localhost:8000/admin/
- Frontend: http://localhost:3000
- API: http://localhost:8000/api/v1/health/

---

## Prevention

To avoid this issue in the future:

1. **Never delete migration files manually**
   - Use `python manage.py migrate app_name zero` to unapply
   - Then delete if really needed

2. **Keep migrations in version control**
   - Commit migration files to Git
   - Don't add `migrations/` to `.gitignore`

3. **Use migration squashing for cleanup**
   ```bash
   python manage.py squashmigrations app_name 0001 0005
   ```

4. **Backup database before major changes**
   ```bash
   pg_dump -U escrow_user escrow_dev > backup.sql
   ```

---

## Quick Reference

**Reset everything:**
```bash
cd backend
python reset_migrations.py
```

**Manual reset:**
```bash
# 1. Delete migrations
find apps/*/migrations -name "*.py" ! -name "__init__.py" -delete

# 2. Drop database
psql -U postgres -c "DROP DATABASE escrow_dev;"
psql -U postgres -c "CREATE DATABASE escrow_dev;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;"

# 3. Regenerate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

---

## Need More Help?

- See **SETUP_DATABASE.md** for database setup
- See **LOCAL_DEVELOPMENT.md** for complete guide
- See **TROUBLESHOOTING.md** for common issues

---

**Last Updated:** April 23, 2026
