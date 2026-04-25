# Quick Start Guide

## Prerequisites

1. **Python 3.11+**
2. **Node.js 18+**
3. **PostgreSQL 15+**
4. **Redis 7+**
5. **Telegram Bot** (create via @BotFather)
6. **TronGrid API Key** (get from https://www.trongrid.io/)

## Step-by-Step Setup

### 1. Install PostgreSQL

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Mac
brew install postgresql
brew services start postgresql
```

**Windows:** Download from https://www.postgresql.org/download/windows/

**Create Database:**
```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE escrow_dev;
CREATE USER escrow_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q
```

### 2. Install Redis

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# Mac
brew install redis
brew services start redis
```

**Windows:** Download from https://github.com/microsoftarchive/redis/releases or use Memurai

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 4. Generate Secret Keys

```bash
# Generate Django secret key
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Generate wallet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy these values into `backend/.env`

### 5. Configure Environment

Edit `backend/.env` with your values:
- `SECRET_KEY` - Generated Django secret key
- `WALLET_ENCRYPTION_KEY` - Generated Fernet key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `TELEGRAM_BOT_TOKEN` - From @BotFather
- `TRON_API_KEY` - From TronGrid

### 6. Run Migrations

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
```

### 7. Start Backend Services

**Terminal 1 - Django:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
source venv/bin/activate
celery -A config worker -l info --pool=solo  # Use --pool=solo on Windows
```

**Terminal 3 - Celery Beat:**
```bash
cd backend
source venv/bin/activate
celery -A config beat -l info
```

### 8. Setup Frontend

**Terminal 4 - Next.js:**
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with your API URL
npm run dev
```

### 9. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/v1/

## Testing the API

### 1. Create a Test User (via Django Shell)

```bash
cd backend
python manage.py shell
```

```python
from apps.users.models import User

# Create test user
user = User.objects.create_user(
    telegram_id=123456789,
    username='testuser',
    first_name='Test',
    last_name='User'
)

# Check wallet was created automatically
print(user.wallet.address)
```

### 2. Test API Endpoints (using curl)

```bash
# Note: In production, you'll use real Telegram auth
# For testing, you can temporarily disable authentication

# Get user profile
curl http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Telegram id=123456789&hash=test"

# Get wallet
curl http://localhost:8000/api/v1/wallets/my_wallet/ \
  -H "Authorization: Telegram id=123456789&hash=test"

# Create a deal
curl -X POST http://localhost:8000/api/v1/deals/ \
  -H "Authorization: Telegram id=123456789&hash=test" \
  -H "Content-Type: application/json" \
  -d '{
    "seller": "seller-user-uuid",
    "title": "Test Deal",
    "description": "Test escrow deal",
    "amount": "100.00"
  }'
```

## Common Commands

### Backend Commands

```bash
# Activate virtual environment
cd backend
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Django shell
python manage.py shell

# Run tests
python manage.py test

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### Database Commands

```bash
# Access PostgreSQL
psql -U escrow_user -d escrow_dev

# Backup database
pg_dump -U escrow_user escrow_dev > backup.sql

# Restore database
psql -U escrow_user escrow_dev < backup.sql
```

### Redis Commands

```bash
# Access Redis CLI
redis-cli

# Check Redis status
redis-cli ping

# Monitor Redis
redis-cli monitor
```

### Celery Commands

```bash
# Start worker
celery -A config worker -l info

# Start beat scheduler
celery -A config beat -l info

# Inspect active tasks
celery -A config inspect active
```

## Troubleshooting

### Services won't start

**PostgreSQL:**
```bash
# Check status
sudo systemctl status postgresql  # Linux
brew services list                # Mac

# Restart
sudo systemctl restart postgresql  # Linux
brew services restart postgresql   # Mac
```

**Redis:**
```bash
# Check status
sudo systemctl status redis  # Linux
brew services list           # Mac

# Restart
sudo systemctl restart redis  # Linux
brew services restart redis   # Mac
```

### Database connection errors

```bash
# Check PostgreSQL is running
psql -U escrow_user -d escrow_dev

# Check connection string in .env
# DATABASE_URL=postgresql://escrow_user:password@localhost:5432/escrow_dev
```

### Migration errors

```bash
# Reset database (WARNING: deletes all data)
psql -U postgres
DROP DATABASE escrow_dev;
CREATE DATABASE escrow_dev;
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;
\q

# Run migrations again
cd backend
python manage.py migrate
```

### Celery not processing tasks

```bash
# Check Redis is running
redis-cli ping

# Check Celery worker logs
# Look at the terminal where celery worker is running

# Restart Celery worker
# Stop with Ctrl+C and restart:
celery -A config worker -l info
```

### Port already in use

```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

## Next Steps

1. **Frontend Setup**: Create Next.js frontend (see ARCHITECTURE.md)
2. **Telegram Integration**: Implement Telegram Login Widget
3. **Blockchain Integration**: Implement deposit/withdrawal with TronPy
4. **WebSocket**: Add real-time updates for deals and chat
5. **Testing**: Write comprehensive tests
6. **Deployment**: Deploy to production (AWS, DigitalOcean, etc.)

## Security Reminders

- ⚠️ Never commit `.env` file to version control
- ⚠️ Use strong, unique encryption keys in production
- ⚠️ Enable HTTPS in production
- ⚠️ Regularly backup your database
- ⚠️ Monitor for suspicious activity
- ⚠️ Keep dependencies updated

## Support

For issues or questions:
1. Check the application logs in your terminal windows
2. Review ARCHITECTURE.md for design details
3. Check Django documentation: https://docs.djangoproject.com/
4. Check NATIVE_SETUP_GUIDE.md for detailed setup instructions
4. Check TronPy documentation: https://tronpy.readthedocs.io/
