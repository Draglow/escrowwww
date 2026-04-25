# Troubleshooting Guide

Common issues and solutions for the Crypto Escrow Platform.

**Last Updated:** April 23, 2026

---

## Table of Contents

1. [Logging Errors](#logging-errors)
2. [Database Issues](#database-issues)
3. [Redis Issues](#redis-issues)
4. [Port Conflicts](#port-conflicts)
5. [Python/Django Issues](#pythondjango-issues)
6. [Node.js/Frontend Issues](#nodejsfrontend-issues)
7. [Celery Issues](#celery-issues)
8. [Migration Issues](#migration-issues)
9. [Authentication Issues](#authentication-issues)
10. [Performance Issues](#performance-issues)

---

## Logging Errors

### Error: `ValueError: Unable to configure handler 'file'`

**Cause:** Django is trying to write logs to a directory that doesn't exist.

**Solution:**

The latest `settings.py` fixes this automatically, but if you still see this error:

```bash
# Create logs directory
cd backend
mkdir logs

# Windows:
cd backend
md logs
```

**Permanent Fix:**

The updated `backend/config/settings.py` now:
- Creates the logs directory automatically with `os.makedirs(LOGS_DIR, exist_ok=True)`
- Only uses file logging in production (when `DEBUG=False`)
- Uses console logging in development

**Verify the fix:**
```bash
cd backend
python manage.py check
```

---

## Database Issues

### Error: `could not connect to server`

**Cause:** PostgreSQL is not running.

**Solution:**

**Windows:**
```cmd
# Check status
sc query postgresql-x64-15

# Start service
net start postgresql-x64-15

# Or restart
net stop postgresql-x64-15
net start postgresql-x64-15
```

**Mac:**
```bash
# Check status
brew services list

# Start PostgreSQL
brew services start postgresql@15

# Or restart
brew services restart postgresql@15
```

**Linux:**
```bash
# Check status
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Restart
sudo systemctl restart postgresql

# Enable on boot
sudo systemctl enable postgresql
```

### Error: `FATAL: password authentication failed`

**Cause:** Incorrect database credentials.

**Solution:**

1. Check your `.env` file:
```env
DATABASE_URL=postgresql://escrow_user:dev_password@localhost:5432/escrow_dev
```

2. Reset PostgreSQL password:
```bash
sudo -u postgres psql
ALTER USER escrow_user WITH PASSWORD 'new_password';
\q
```

3. Update `.env` with the new password.

### Error: `database "escrow_dev" does not exist`

**Cause:** Database hasn't been created.

**Solution:**

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE escrow_dev;
CREATE USER escrow_user WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
ALTER USER escrow_user CREATEDB;
\q

# Run migrations
cd backend
python manage.py migrate
```

### Error: `too many connections`

**Cause:** PostgreSQL connection limit reached.

**Solution:**

```bash
# Check current connections
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# Increase max connections (edit postgresql.conf)
# max_connections = 200
sudo systemctl restart postgresql
```

---

## Redis Issues

### Error: `Error connecting to Redis`

**Cause:** Redis is not running.

**Solution:**

**Windows:**
```cmd
# Check status
sc query Redis

# Start service
net start Redis

# Or restart
net stop Redis
net start Redis
```

**Mac:**
```bash
# Check status
brew services list

# Start Redis
brew services start redis

# Or restart
brew services restart redis
```

**Linux:**
```bash
# Check status
sudo systemctl status redis

# Start Redis
sudo systemctl start redis

# Restart
sudo systemctl restart redis

# Enable on boot
sudo systemctl enable redis
```

### Error: `NOAUTH Authentication required`

**Cause:** Redis requires a password but none was provided.

**Solution:**

1. Check Redis configuration:
```bash
# Linux/Mac
cat /etc/redis/redis.conf | grep requirepass

# Windows
type C:\Redis\redis.windows.conf | findstr requirepass
```

2. Update `.env`:
```env
REDIS_URL=redis://:your_password@localhost:6379/0
```

3. Or disable password (development only):
```bash
# Edit redis.conf
# Comment out: # requirepass your_password
sudo systemctl restart redis
```

---

## Port Conflicts

### Error: `Error: That port is already in use`

**Cause:** Another process is using the port.

**Solution:**

**Windows:**
```cmd
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace <PID> with actual PID)
taskkill /PID <PID> /F

# For port 3000 (frontend)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Mac/Linux:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use one command
lsof -ti :8000 | xargs kill -9

# For port 3000 (frontend)
lsof -ti :3000 | xargs kill -9
```

**Alternative:** Use different ports:

```bash
# Backend (different port)
python manage.py runserver 8001

# Frontend (different port)
PORT=3001 npm run dev
```

---

## Python/Django Issues

### Error: `ModuleNotFoundError: No module named 'xxx'`

**Cause:** Missing Python package or virtual environment not activated.

**Solution:**

```bash
# Make sure virtual environment is activated
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate

# You should see (venv) in your prompt

# Reinstall dependencies
pip install -r requirements.txt

# If specific package is missing
pip install package_name
```

### Error: `ImportError: cannot import name 'xxx'`

**Cause:** Circular import or incorrect import path.

**Solution:**

1. Check import statements in your code
2. Look for circular dependencies
3. Restart Django server:
```bash
# Stop with Ctrl+C
# Start again
python manage.py runserver
```

### Error: `django.core.exceptions.ImproperlyConfigured`

**Cause:** Missing or incorrect configuration in settings.

**Solution:**

1. Check `.env` file exists:
```bash
ls backend/.env  # Should exist
```

2. Verify required variables:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...
WALLET_ENCRYPTION_KEY=your-fernet-key
```

3. Generate missing keys:
```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(50))"

# WALLET_ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Error: `CommandError: You must set settings.ALLOWED_HOSTS`

**Cause:** ALLOWED_HOSTS not configured.

**Solution:**

Add to `.env`:
```env
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Node.js/Frontend Issues

### Error: `Module not found: Can't resolve 'xxx'`

**Cause:** Missing npm package.

**Solution:**

```bash
cd frontend

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json  # Windows: rmdir /s node_modules
npm install

# Or install specific package
npm install package_name
```

### Error: `Error: ENOSPC: System limit for number of file watchers reached`

**Cause:** Linux file watcher limit reached.

**Solution (Linux only):**

```bash
# Increase file watcher limit
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Error: `TypeError: Cannot read property 'xxx' of undefined`

**Cause:** JavaScript runtime error.

**Solution:**

1. Check browser console (F12)
2. Look for the exact line causing the error
3. Clear Next.js cache:
```bash
cd frontend
rm -rf .next
npm run dev
```

### Error: `Failed to compile`

**Cause:** TypeScript or ESLint errors.

**Solution:**

```bash
# Check for errors
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix

# Type check
npx tsc --noEmit
```

---

## Celery Issues

### Error: `ValueError: not enough values to unpack` (Windows)

**Cause:** Celery doesn't support the default pool on Windows.

**Solution:**

Always use `--pool=solo` on Windows:

```bash
celery -A config worker -l info --pool=solo
```

### Error: `consumer: Cannot connect to redis://localhost:6379/1`

**Cause:** Redis is not running or wrong URL.

**Solution:**

1. Start Redis (see [Redis Issues](#redis-issues))

2. Check `.env`:
```env
CELERY_BROKER_URL=redis://localhost:6379/1
```

3. Test Redis connection:
```bash
redis-cli ping  # Should return PONG
```

### Error: `Received unregistered task`

**Cause:** Task not imported or Celery not restarted.

**Solution:**

1. Restart Celery worker (Ctrl+C and start again)

2. Check task is imported in `config/celery.py`:
```python
app.autodiscover_tasks()
```

3. Verify task decorator:
```python
from config.celery import app

@app.task
def my_task():
    pass
```

---

## Migration Issues

### Error: `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Cause:** Migration history mismatch.

**Solution:**

**Option 1: Reset database (development only):**

```bash
# Backup data first if needed
python manage.py dumpdata > backup.json

# Drop and recreate database
psql -U postgres
DROP DATABASE escrow_dev;
CREATE DATABASE escrow_dev;
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q

# Run migrations
python manage.py migrate

# Restore data
python manage.py loaddata backup.json
```

**Option 2: Fake migrations:**

```bash
# Show migrations
python manage.py showmigrations

# Fake specific migration
python manage.py migrate app_name migration_name --fake
```

### Error: `django.db.utils.ProgrammingError: relation "xxx" does not exist`

**Cause:** Migrations not applied.

**Solution:**

```bash
# Run migrations
python manage.py migrate

# If that fails, try:
python manage.py migrate --run-syncdb
```

### Error: `You have unapplied migrations`

**Cause:** New migrations need to be applied.

**Solution:**

```bash
# Apply migrations
python manage.py migrate

# Create migrations if you changed models
python manage.py makemigrations
python manage.py migrate
```

---

## Authentication Issues

### Error: `Invalid token` or `Authentication credentials were not provided`

**Cause:** Missing or invalid authentication token.

**Solution:**

1. For API testing, create a token:
```bash
python manage.py shell
```

```python
from apps.users.models import User
from rest_framework.authtoken.models import Token

user = User.objects.get(username='admin')
token, created = Token.objects.get_or_create(user=user)
print(f"Token: {token.key}")
```

2. Use token in requests:
```bash
curl http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Error: `Telegram authentication failed`

**Cause:** Invalid Telegram credentials or bot not configured.

**Solution:**

1. Check `.env`:
```env
TELEGRAM_BOT_TOKEN=your-bot-token
```

2. Create bot via @BotFather on Telegram

3. For development, you can temporarily disable authentication in views

---

## Performance Issues

### Slow Database Queries

**Solution:**

1. Enable query logging:
```python
# In settings.py
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}
```

2. Use Django Debug Toolbar:
```bash
pip install django-debug-toolbar
```

3. Optimize queries:
```python
# Use select_related for foreign keys
User.objects.select_related('wallet').all()

# Use prefetch_related for many-to-many
Deal.objects.prefetch_related('messages').all()
```

### High Memory Usage

**Solution:**

1. Check for memory leaks:
```bash
# Install memory profiler
pip install memory-profiler

# Profile code
python -m memory_profiler script.py
```

2. Limit query results:
```python
# Use pagination
queryset = Model.objects.all()[:100]

# Use iterator for large datasets
for obj in Model.objects.iterator():
    process(obj)
```

3. Clear cache:
```bash
python manage.py shell
```
```python
from django.core.cache import cache
cache.clear()
```

### Slow Frontend Loading

**Solution:**

1. Clear Next.js cache:
```bash
cd frontend
rm -rf .next
npm run dev
```

2. Optimize images:
```jsx
import Image from 'next/image'

<Image src="/image.jpg" width={500} height={300} />
```

3. Use production build:
```bash
npm run build
npm start
```

---

## General Debugging Tips

### Enable Debug Mode

**Backend:**
```env
# .env
DEBUG=True
```

**Frontend:**
```bash
# Check browser console (F12)
# Check terminal output
```

### Check Logs

**Django:**
```bash
# Terminal output shows all logs
# Or check logs/django.log (production)
```

**Celery:**
```bash
# Terminal output shows task execution
```

**PostgreSQL:**
```bash
# Linux
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Mac
tail -f /usr/local/var/log/postgres.log
```

**Redis:**
```bash
# Monitor Redis commands
redis-cli monitor
```

### Test Individual Components

**Database:**
```bash
psql -U escrow_user -d escrow_dev -c "SELECT 1;"
```

**Redis:**
```bash
redis-cli ping
```

**Django:**
```bash
python manage.py check
python manage.py check --deploy
```

**Celery:**
```bash
celery -A config inspect ping
```

---

## Getting Help

If you're still stuck:

1. **Check Documentation:**
   - LOCAL_DEVELOPMENT.md
   - QUICKSTART.md
   - API_DOCUMENTATION.md

2. **Search Error Message:**
   - Google the exact error
   - Check Stack Overflow
   - Check Django/Next.js docs

3. **Enable Verbose Logging:**
   ```python
   # settings.py
   LOGGING['root']['level'] = 'DEBUG'
   ```

4. **Create Minimal Reproduction:**
   - Isolate the issue
   - Test with minimal code

5. **Ask for Help:**
   - GitHub Issues
   - Django Forum
   - Stack Overflow

---

**Last Updated:** April 23, 2026  
**Version:** 1.0.0
