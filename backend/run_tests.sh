#!/usr/bin/env bash
# ============================================================
# run_tests.sh — Run all backend tests with coverage report
# Usage: bash run_tests.sh [--fast] [--app <appname>]
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

FAST=false
APP=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --fast) FAST=true ;;
        --app) APP="$2"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

echo "============================================"
echo "  Crypto Escrow Platform - Backend Tests"
echo "============================================"

# Activate venv if present
if [ -d "venv/Scripts" ]; then
    source venv/Scripts/activate
elif [ -d "venv/bin" ]; then
    source venv/bin/activate
fi

# Run migrations on test DB first
echo ""
echo ">>> Applying migrations..."
python manage.py migrate --run-syncdb 2>/dev/null || true

echo ""
echo ">>> Running tests..."

if [ -n "$APP" ]; then
    TARGET="apps/$APP/tests.py"
else
    TARGET="apps/ tests/"
fi

if [ "$FAST" = true ]; then
    python -m pytest $TARGET -v --no-cov -x
else
    python -m pytest $TARGET \
        --cov=apps \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        -v
    echo ""
    echo ">>> Coverage report saved to: htmlcov/index.html"
fi

echo ""
echo ">>> All tests passed!"
