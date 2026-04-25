@echo off
echo Starting Telegram Bot...

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the Telegram bot
python manage.py run_telegram_bot

pause
