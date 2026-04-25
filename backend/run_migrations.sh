#!/bin/bash
# Script to run Django migrations

set -e

echo "=== Running Django Migrations ==="

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
until python manage.py dbshell --command="SELECT 1" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing migrations"

# Make migrations
python manage.py makemigrations users
python manage.py makemigrations wallets
python manage.py makemigrations deals
python manage.py makemigrations ledger

# Run migrations
python manage.py migrate

echo "=== Migrations completed successfully ==="
