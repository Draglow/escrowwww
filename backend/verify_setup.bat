@echo off
echo.
echo ========================================
echo   Crypto Escrow - Setup Verification
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run verification script
python verify_setup.py

echo.
pause
