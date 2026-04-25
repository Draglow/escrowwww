#!/bin/bash

echo "=== Crypto Escrow Platform Setup ==="
echo ""

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "Creating .env file from template..."
    cp backend/.env.example backend/.env
    
    # Generate encryption key
    echo "Generating wallet encryption key..."
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # Generate secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    
    # Update .env file
    sed -i "s/your-32-byte-base64-encryption-key/$ENCRYPTION_KEY/" backend/.env
    sed -i "s/your-secret-key-change-in-production/$SECRET_KEY/" backend/.env
    
    echo "✓ Environment file created"
    echo ""
    echo "⚠️  Please update the following in backend/.env:"
    echo "   - DATABASE_URL (PostgreSQL connection string)"
    echo "   - REDIS_URL (Redis connection string)"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - TRON_API_KEY"
    echo ""
else
    echo "✓ .env file already exists"
fi

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
    echo "✓ Virtual environment created"
fi

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..
echo "✓ Backend dependencies installed"

# Install frontend dependencies
if [ -d "frontend" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✓ Frontend dependencies installed"
fi

# Run migrations
echo "Running database migrations..."
cd backend
source venv/bin/activate
python manage.py migrate
cd ..
echo "✓ Migrations completed"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Ensure PostgreSQL is running"
echo "  2. Ensure Redis is running"
echo "  3. Create superuser: cd backend && python manage.py createsuperuser"
echo "  4. Start backend: cd backend && python manage.py runserver"
echo "  5. Start Celery worker: cd backend && celery -A config worker -l info"
echo "  6. Start Celery beat: cd backend && celery -A config beat -l info"
echo "  7. Start frontend: cd frontend && npm run dev"
echo ""
echo "Access points:"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - Admin Panel: http://localhost:8000/admin"
echo ""
