#!/usr/bin/env python
"""
Script to reset and regenerate Django migrations.
Run this when migrations are broken or inconsistent.
"""

import os
import sys
import shutil
from pathlib import Path

# Add the backend directory to the path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.core.management import call_command
from django.db import connection

def reset_migrations():
    """Reset all migrations and regenerate them."""
    
    print("=" * 60)
    print("Django Migrations Reset Script")
    print("=" * 60)
    
    # List of apps to reset
    apps = ['users', 'wallets', 'deals', 'ledger']
    
    print("\n1. Cleaning up migration files...")
    for app in apps:
        migrations_dir = BASE_DIR / 'apps' / app / 'migrations'
        if migrations_dir.exists():
            # Keep __init__.py, delete everything else
            for file in migrations_dir.glob('*.py'):
                if file.name != '__init__.py':
                    print(f"   Deleting: {file}")
                    file.unlink()
            
            # Clean __pycache__
            pycache_dir = migrations_dir / '__pycache__'
            if pycache_dir.exists():
                print(f"   Cleaning: {pycache_dir}")
                shutil.rmtree(pycache_dir)
    
    print("\n2. Dropping all tables...")
    with connection.cursor() as cursor:
        # Get all tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            # Drop all tables
            for table in tables:
                table_name = table[0]
                print(f"   Dropping table: {table_name}")
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
    
    print("\n3. Creating fresh migrations...")
    call_command('makemigrations')
    
    print("\n4. Applying migrations...")
    call_command('migrate')
    
    print("\n" + "=" * 60)
    print("✅ Migrations reset complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Start the server: python manage.py runserver")
    print()

if __name__ == '__main__':
    try:
        reset_migrations()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nIf you see database connection errors, make sure:")
        print("1. PostgreSQL is running")
        print("2. Database 'escrow_dev' exists")
        print("3. .env file has correct DATABASE_URL")
        sys.exit(1)
