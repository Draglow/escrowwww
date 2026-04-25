@echo off
echo ========================================
echo Fixing Django Migrations
echo ========================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Step 1: Creating migrations for users app...
python manage.py makemigrations users

echo.
echo Step 2: Creating migrations for wallets app...
python manage.py makemigrations wallets

echo.
echo Step 3: Creating migrations for deals app...
python manage.py makemigrations deals

echo.
echo Step 4: Creating migrations for ledger app...
python manage.py makemigrations ledger

echo.
echo Step 5: Creating any remaining migrations...
python manage.py makemigrations

echo.
echo Step 6: Applying all migrations...
python manage.py migrate

echo.
echo ========================================
echo Done!
echo ========================================
echo.
echo Next step: Create superuser
echo Run: python manage.py createsuperuser
echo.
pause
