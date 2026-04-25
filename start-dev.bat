@echo off
echo ========================================
echo   Crypto Escrow Platform - Starting
echo ========================================
echo.

REM Check if PostgreSQL is running
sc query postgresql-x64-15 | find "RUNNING" >nul
if errorlevel 1 (
    echo [!] PostgreSQL is not running. Please start it first.
    echo     Run: net start postgresql-x64-15
    pause
    exit /b 1
)
echo [OK] PostgreSQL is running

REM Check if Redis is running
sc query Redis | find "RUNNING" >nul
if errorlevel 1 (
    echo [!] Redis is not running. Trying to start...
    net start Redis >nul 2>&1
    if errorlevel 1 (
        echo [!] Could not start Redis. Please start it manually.
        pause
        exit /b 1
    )
)
echo [OK] Redis is running

echo.
echo Starting services...
echo.

REM Start Backend
echo [1/4] Starting Django Server...
start "Django Server" cmd /k "cd /d %~dp0backend && venv\Scripts\activate.bat && python manage.py runserver"
timeout /t 3 /nobreak >nul

REM Start Celery Worker
echo [2/4] Starting Celery Worker...
start "Celery Worker" cmd /k "cd /d %~dp0backend && venv\Scripts\activate.bat && celery -A config worker -l info --pool=solo"
timeout /t 2 /nobreak >nul

REM Start Celery Beat
echo [3/4] Starting Celery Beat...
start "Celery Beat" cmd /k "cd /d %~dp0backend && venv\Scripts\activate.bat && celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
timeout /t 2 /nobreak >nul

REM Start Frontend
echo [4/4] Starting Next.js Frontend...
start "Next.js Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   All services started successfully!
echo ========================================
echo.
echo Access Points:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   Admin:     http://localhost:8000/admin/
echo   API Docs:  http://localhost:8000/api/v1/
echo.
echo Press any key to close this window...
echo (Services will continue running in separate windows)
pause >nul
