# Database Setup Guide

Quick guide to set up PostgreSQL for local development.

---

## Step 1: Check if PostgreSQL is Running

**Windows:**
```cmd
sc query postgresql-x64-15
```

If not running:
```cmd
net start postgresql-x64-15
```

**Mac:**
```bash
brew services list
```

If not running:
```bash
brew services start postgresql@15
```

**Linux:**
```bash
sudo systemctl status postgresql
```

If not running:
```bash
sudo systemctl start postgresql
```

---

## Step 2: Create Database

### Option A: Using SQL Script (Recommended)

```bash
# Navigate to backend directory
cd backend

# Run the setup script
psql -U postgres -f setup_database.sql

# Enter password when prompted (default is usually empty or 'postgres')
```

### Option B: Manual Setup

**Windows (Command Prompt):**
```cmd
psql -U postgres
```

**Mac/Linux:**
```bash
sudo -u postgres psql
```

**Then run these commands in PostgreSQL:**
```sql
-- Create database
CREATE DATABASE escrow_dev;

-- Create user
CREATE USER escrow_user WITH PASSWORD 'dev_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;

-- Allow user to create databases (for tests)
ALTER USER escrow_user CREATEDB;

-- Exit
\q
```

---

## Step 3: Verify Database Connection

Test the connection:

```bash
psql -U escrow_user -d escrow_dev -h localhost

# Enter password: dev_password

# If successful, you'll see:
# escrow_dev=>

# Exit with:
\q
```

---

## Step 4: Run Django Migrations

```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Run migrations
python manage.py migrate

# You should see:
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ...
```

---

## Step 5: Create Superuser

```bash
python manage.py createsuperuser

# Follow the prompts:
# Username: admin
# Email: admin@example.com
# Password: (choose a password)
# Password (again): (repeat password)
```

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

The password in `.env` doesn't match PostgreSQL.

**Solution:**

1. Reset the password:
```bash
psql -U postgres
ALTER USER escrow_user WITH PASSWORD 'dev_password';
\q
```

2. Or update `.env` with the correct password:
```env
DATABASE_URL=postgresql://escrow_user:YOUR_PASSWORD@localhost:5432/escrow_dev
```

### Error: `database "escrow_dev" already exists`

The database already exists. You can either:

**Option 1: Use existing database**
```bash
# Just run migrations
python manage.py migrate
```

**Option 2: Drop and recreate**
```bash
psql -U postgres
DROP DATABASE escrow_dev;
CREATE DATABASE escrow_dev;
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q

# Run migrations
python manage.py migrate
```

### Error: `could not connect to server`

PostgreSQL is not running. See Step 1.

### Error: `role "escrow_user" does not exist`

The user hasn't been created. Run Step 2 again.

---

## Verify Everything Works

```bash
# 1. Check database connection
python manage.py check

# Should show: System check identified no issues (0 silenced).

# 2. Start Django
python manage.py runserver

# Should show: Starting development server at http://127.0.0.1:8000/

# 3. Test in browser
# Open: http://localhost:8000/admin/
# You should see the Django admin login page
```

---

## Database Credentials Summary

For local development, these are the default credentials:

```env
Database Name: escrow_dev
Username: escrow_user
Password: dev_password
Host: localhost
Port: 5432
```

**Full connection string:**
```
postgresql://escrow_user:dev_password@localhost:5432/escrow_dev
```

---

## Next Steps

After database setup:

1. ✅ Run migrations: `python manage.py migrate`
2. ✅ Create superuser: `python manage.py createsuperuser`
3. ✅ Start Django: `python manage.py runserver`
4. ✅ Start Celery: `celery -A config worker -l info --pool=solo`
5. ✅ Start Frontend: `cd frontend && npm run dev`

See **LOCAL_DEVELOPMENT.md** for complete setup instructions.

---

**Last Updated:** April 23, 2026
