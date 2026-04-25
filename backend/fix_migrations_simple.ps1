# Django Migrations Fix Script (PowerShell)
# Run this with: .\fix_migrations_simple.ps1

Write-Host "========================================" -ForegroundColor Green
Write-Host "Fixing Django Migrations" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "Step 1: Creating migrations for users app..." -ForegroundColor Cyan
python manage.py makemigrations users

Write-Host ""
Write-Host "Step 2: Creating migrations for wallets app..." -ForegroundColor Cyan
python manage.py makemigrations wallets

Write-Host ""
Write-Host "Step 3: Creating migrations for deals app..." -ForegroundColor Cyan
python manage.py makemigrations deals

Write-Host ""
Write-Host "Step 4: Creating migrations for ledger app..." -ForegroundColor Cyan
python manage.py makemigrations ledger

Write-Host ""
Write-Host "Step 5: Creating any remaining migrations..." -ForegroundColor Cyan
python manage.py makemigrations

Write-Host ""
Write-Host "Step 6: Applying all migrations..." -ForegroundColor Cyan
python manage.py migrate

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Done!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next step: Create superuser" -ForegroundColor Yellow
Write-Host "Run: python manage.py createsuperuser" -ForegroundColor White
Write-Host ""
