#!/bin/bash
# Quick setup script for Render deployment
# This script helps you prepare for deployment

set -e

echo "=========================================="
echo "Render Deployment Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 found${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js found${NC}"

# Generate secure keys
echo ""
echo "=========================================="
echo "Generating Secure Keys"
echo "=========================================="
echo ""

python3 scripts/generate_keys.py

# Check for required files
echo ""
echo "=========================================="
echo "Checking Required Files"
echo "=========================================="
echo ""

files=(
    "render.yaml"
    "backend/requirements.txt"
    "backend/runtime.txt"
    "backend/Procfile"
    "frontend/package.json"
    "RENDER_DEPLOYMENT.md"
    "DEPLOYMENT_CHECKLIST.md"
)

all_files_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file (missing)${NC}"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo ""
    echo -e "${RED}Some required files are missing. Please ensure all files are present.${NC}"
    exit 1
fi

# Check environment variable examples
echo ""
echo "=========================================="
echo "Checking Environment Examples"
echo "=========================================="
echo ""

env_files=(
    "backend/.env.example"
    "frontend/.env.local.example"
)

for file in "${env_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${YELLOW}⚠️  $file (missing - recommended)${NC}"
    fi
done

# Git status check
echo ""
echo "=========================================="
echo "Git Status"
echo "=========================================="
echo ""

if [ -d ".git" ]; then
    echo -e "${GREEN}✅ Git repository initialized${NC}"
    
    # Check for uncommitted changes
    if [[ -n $(git status -s) ]]; then
        echo -e "${YELLOW}⚠️  You have uncommitted changes:${NC}"
        git status -s
        echo ""
        echo -e "${YELLOW}Consider committing these changes before deployment${NC}"
    else
        echo -e "${GREEN}✅ No uncommitted changes${NC}"
    fi
    
    # Check remote
    if git remote -v | grep -q "origin"; then
        echo -e "${GREEN}✅ Git remote configured${NC}"
        git remote -v
    else
        echo -e "${RED}❌ No git remote configured${NC}"
        echo "   Add remote: git remote add origin <your-repo-url>"
    fi
else
    echo -e "${RED}❌ Not a git repository${NC}"
    echo "   Initialize: git init"
fi

# Summary and next steps
echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. 📝 Review RENDER_DEPLOYMENT.md for detailed instructions"
echo "2. 📋 Use DEPLOYMENT_CHECKLIST.md to track your progress"
echo "3. 🔑 Save the generated keys securely"
echo "4. 🌐 Sign up at https://render.com if you haven't already"
echo "5. 🔗 Connect your GitHub repository to Render"
echo "6. 📦 Create a new Blueprint in Render"
echo "7. ⚙️  Configure environment variables in Render"
echo "8. 🚀 Deploy!"
echo ""

echo "=========================================="
echo "Required API Keys"
echo "=========================================="
echo ""
echo "Before deploying, obtain these API keys:"
echo ""
echo "1. 🔷 TronGrid API Key"
echo "   Get from: https://www.trongrid.io/"
echo "   Used for: Blockchain transactions"
echo ""
echo "2. 🤖 Telegram Bot Token"
echo "   Get from: @BotFather on Telegram"
echo "   Used for: User authentication"
echo ""

echo "=========================================="
echo "Estimated Costs (Render)"
echo "=========================================="
echo ""
echo "Minimum Setup (Development):"
echo "  - PostgreSQL Starter: \$7/month"
echo "  - Redis Starter: \$10/month"
echo "  - Backend Web: \$7/month"
echo "  - Frontend Web: \$7/month"
echo "  Total: ~\$31/month"
echo ""
echo "Production Setup:"
echo "  - PostgreSQL Standard: \$20/month"
echo "  - Redis Standard: \$25/month"
echo "  - Backend Web: \$25/month"
echo "  - Celery Worker: \$7/month"
echo "  - Celery Beat: \$7/month"
echo "  - Frontend Web: \$25/month"
echo "  Total: ~\$109/month"
echo ""

echo "=========================================="
echo "Setup Complete! 🎉"
echo "=========================================="
echo ""
echo "Good luck with your deployment!"
echo ""
