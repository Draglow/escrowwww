@echo off
REM Quick setup script for Render deployment (Windows)
REM This script helps you prepare for deployment

echo ==========================================
echo Render Deployment Setup Script
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3 is not installed
    exit /b 1
)
echo [OK] Python 3 found

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed
    exit /b 1
)
echo [OK] Node.js found

REM Generate secure keys
echo.
echo ==========================================
echo Generating Secure Keys
echo ==========================================
echo.

python scripts\generate_keys.py

REM Check for required files
echo.
echo ==========================================
echo Checking Required Files
echo ==========================================
echo.

set "all_files_exist=true"

if exist "render.yaml" (
    echo [OK] render.yaml
) else (
    echo [ERROR] render.yaml ^(missing^)
    set "all_files_exist=false"
)

if exist "backend\requirements.txt" (
    echo [OK] backend\requirements.txt
) else (
    echo [ERROR] backend\requirements.txt ^(missing^)
    set "all_files_exist=false"
)

if exist "backend\runtime.txt" (
    echo [OK] backend\runtime.txt
) else (
    echo [ERROR] backend\runtime.txt ^(missing^)
    set "all_files_exist=false"
)

if exist "backend\Procfile" (
    echo [OK] backend\Procfile
) else (
    echo [ERROR] backend\Procfile ^(missing^)
    set "all_files_exist=false"
)

if exist "frontend\package.json" (
    echo [OK] frontend\package.json
) else (
    echo [ERROR] frontend\package.json ^(missing^)
    set "all_files_exist=false"
)

if exist "RENDER_DEPLOYMENT.md" (
    echo [OK] RENDER_DEPLOYMENT.md
) else (
    echo [ERROR] RENDER_DEPLOYMENT.md ^(missing^)
    set "all_files_exist=false"
)

if exist "DEPLOYMENT_CHECKLIST.md" (
    echo [OK] DEPLOYMENT_CHECKLIST.md
) else (
    echo [ERROR] DEPLOYMENT_CHECKLIST.md ^(missing^)
    set "all_files_exist=false"
)

if "%all_files_exist%"=="false" (
    echo.
    echo [ERROR] Some required files are missing. Please ensure all files are present.
    exit /b 1
)

REM Check environment variable examples
echo.
echo ==========================================
echo Checking Environment Examples
echo ==========================================
echo.

if exist "backend\.env.example" (
    echo [OK] backend\.env.example
) else (
    echo [WARNING] backend\.env.example ^(missing - recommended^)
)

if exist "frontend\.env.local.example" (
    echo [OK] frontend\.env.local.example
) else (
    echo [WARNING] frontend\.env.local.example ^(missing - recommended^)
)

REM Git status check
echo.
echo ==========================================
echo Git Status
echo ==========================================
echo.

if exist ".git" (
    echo [OK] Git repository initialized
    
    REM Check for uncommitted changes
    git status --short >nul 2>&1
    if not errorlevel 1 (
        echo [WARNING] You have uncommitted changes
        git status --short
        echo.
        echo Consider committing these changes before deployment
    ) else (
        echo [OK] No uncommitted changes
    )
    
    REM Check remote
    git remote -v | findstr "origin" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Git remote configured
        git remote -v
    ) else (
        echo [ERROR] No git remote configured
        echo    Add remote: git remote add origin ^<your-repo-url^>
    )
) else (
    echo [ERROR] Not a git repository
    echo    Initialize: git init
)

REM Summary and next steps
echo.
echo ==========================================
echo Next Steps
echo ==========================================
echo.
echo 1. Review RENDER_DEPLOYMENT.md for detailed instructions
echo 2. Use DEPLOYMENT_CHECKLIST.md to track your progress
echo 3. Save the generated keys securely
echo 4. Sign up at https://render.com if you haven't already
echo 5. Connect your GitHub repository to Render
echo 6. Create a new Blueprint in Render
echo 7. Configure environment variables in Render
echo 8. Deploy!
echo.

echo ==========================================
echo Required API Keys
echo ==========================================
echo.
echo Before deploying, obtain these API keys:
echo.
echo 1. TronGrid API Key
echo    Get from: https://www.trongrid.io/
echo    Used for: Blockchain transactions
echo.
echo 2. Telegram Bot Token
echo    Get from: @BotFather on Telegram
echo    Used for: User authentication
echo.

echo ==========================================
echo Estimated Costs ^(Render^)
echo ==========================================
echo.
echo Minimum Setup ^(Development^):
echo   - PostgreSQL Starter: $7/month
echo   - Redis Starter: $10/month
echo   - Backend Web: $7/month
echo   - Frontend Web: $7/month
echo   Total: ~$31/month
echo.
echo Production Setup:
echo   - PostgreSQL Standard: $20/month
echo   - Redis Standard: $25/month
echo   - Backend Web: $25/month
echo   - Celery Worker: $7/month
echo   - Celery Beat: $7/month
echo   - Frontend Web: $25/month
echo   Total: ~$109/month
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Good luck with your deployment!
echo.

pause
