@echo off
echo ========================================
echo  Crypto Escrow Platform - Start All
echo ========================================
echo.

REM Check if running in correct directory
if not exist "backend" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ERROR: Frontend directory not found
    pause
    exit /b 1
)

echo Starting all services...
echo.

REM Start Django Server
echo [1/5] Starting Django Server...
start "Django Server" cmd /k "cd backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && python manage.py runserver"
timeout /t 2 /nobreak >nul

REM Start Celery Worker
echo [2/5] Starting Celery Worker...
start "Celery Worker" cmd /k "cd backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && celery -A config worker -l info"
timeout /t 2 /nobreak >nul

REM Start Celery Beat
echo [3/5] Starting Celery Beat...
start "Celery Beat" cmd /k "cd backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && celery -A config beat -l info"
timeout /t 2 /nobreak >nul

REM Start Telegram Bot
echo [4/5] Starting Telegram Bot...
start "Telegram Bot" cmd /k "cd backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && python manage.py run_telegram_bot"
timeout /t 2 /nobreak >nul

REM Start Frontend
echo [5/5] Starting Frontend...
start "Frontend Server" cmd /k "cd frontend && npm run dev"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  All Services Started!
echo ========================================
echo.
echo Services running:
echo   - Django Server:    http://localhost:8000
echo   - Frontend:         http://localhost:3000
echo   - Celery Worker:    Processing tasks
echo   - Celery Beat:      Scheduled tasks
echo   - Telegram Bot:     Active
echo.
echo Press any key to open the web interface...
pause >nul

start http://localhost:3000

echo.
echo To stop all services, close all terminal windows.
echo.
pause
