@echo off
echo ========================================
echo   Crypto Escrow Platform - Stopping
echo ========================================
echo.

echo Stopping all services...
echo.

REM Kill Node.js processes (Frontend)
echo [1/2] Stopping Next.js Frontend...
taskkill /F /IM node.exe /T >nul 2>&1
if errorlevel 1 (
    echo     No Node.js processes found
) else (
    echo     Stopped
)

REM Kill Python processes (Django + Celery)
echo [2/2] Stopping Django and Celery...
taskkill /F /IM python.exe /T >nul 2>&1
if errorlevel 1 (
    echo     No Python processes found
) else (
    echo     Stopped
)

echo.
echo ========================================
echo   All services stopped!
echo ========================================
echo.
echo Note: PostgreSQL and Redis are still running
echo       (they run as Windows services)
echo.
pause
