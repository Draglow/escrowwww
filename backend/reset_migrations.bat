@echo off
echo ========================================
echo Django Migrations Reset Script
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo 1. Running reset script...
python reset_migrations.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Success! Migrations have been reset.
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Create superuser: python manage.py createsuperuser
    echo 2. Start server: python manage.py runserver
) else (
    echo.
    echo ========================================
    echo Error occurred during reset.
    echo ========================================
    echo.
    echo Please check:
    echo 1. PostgreSQL is running
    echo 2. Database exists
    echo 3. .env file is configured correctly
)

echo.
pause
