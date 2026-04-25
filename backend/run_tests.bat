@echo off
REM ============================================================
REM run_tests.bat — Run all backend tests (Windows)
REM Usage: run_tests.bat [--fast] [--app <appname>]
REM ============================================================

cd /d "%~dp0"

echo ============================================
echo   Crypto Escrow Platform - Backend Tests
echo ============================================

REM Activate venv if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo.
echo ^>^>^> Applying migrations...
python manage.py migrate --run-syncdb 2>nul

echo.
echo ^>^>^> Running tests...

if "%1"=="--fast" (
    python -m pytest apps/ tests/ -v --no-cov -x
) else if "%1"=="--app" (
    python -m pytest apps/%2/tests.py -v --no-cov -x
) else (
    python -m pytest apps/ tests/ ^
        --cov=apps ^
        --cov-report=term-missing ^
        --cov-report=html:htmlcov ^
        -v
    echo.
    echo ^>^>^> Coverage report saved to: htmlcov\index.html
)

echo.
echo ^>^>^> Done!
