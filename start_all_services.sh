#!/bin/bash

echo "========================================"
echo " Crypto Escrow Platform - Start All"
echo "========================================"
echo ""

# Check if running in correct directory
if [ ! -d "backend" ]; then
    echo "ERROR: Please run this script from the project root directory"
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo "ERROR: Frontend directory not found"
    exit 1
fi

echo "Starting all services..."
echo ""

# Function to start service in new terminal
start_service() {
    local name=$1
    local command=$2
    
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$name" -- bash -c "$command; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -title "$name" -e "$command; bash" &
    elif command -v konsole &> /dev/null; then
        konsole --title "$name" -e bash -c "$command; exec bash" &
    else
        echo "No supported terminal found. Please install gnome-terminal, xterm, or konsole"
        exit 1
    fi
    
    sleep 2
}

# Activate virtual environment command
VENV_CMD="if [ -d venv ]; then source venv/bin/activate; fi"

# Start Django Server
echo "[1/5] Starting Django Server..."
start_service "Django Server" "cd backend && $VENV_CMD && python manage.py runserver"

# Start Celery Worker
echo "[2/5] Starting Celery Worker..."
start_service "Celery Worker" "cd backend && $VENV_CMD && celery -A config worker -l info"

# Start Celery Beat
echo "[3/5] Starting Celery Beat..."
start_service "Celery Beat" "cd backend && $VENV_CMD && celery -A config beat -l info"

# Start Telegram Bot
echo "[4/5] Starting Telegram Bot..."
start_service "Telegram Bot" "cd backend && $VENV_CMD && python manage.py run_telegram_bot"

# Start Frontend
echo "[5/5] Starting Frontend..."
start_service "Frontend Server" "cd frontend && npm run dev"

echo ""
echo "========================================"
echo " All Services Started!"
echo "========================================"
echo ""
echo "Services running:"
echo "  - Django Server:    http://localhost:8000"
echo "  - Frontend:         http://localhost:3000"
echo "  - Celery Worker:    Processing tasks"
echo "  - Celery Beat:      Scheduled tasks"
echo "  - Telegram Bot:     Active"
echo ""
echo "Opening web interface..."

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v open &> /dev/null; then
    open http://localhost:3000
fi

echo ""
echo "To stop all services, close all terminal windows."
echo ""
