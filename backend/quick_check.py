#!/usr/bin/env python
"""
Quick Setup Check - No Django required
Verifies basic configuration without loading Django
"""
import os
import sys
from pathlib import Path

def print_status(check_name, status, message=""):
    """Print colored status message"""
    if status:
        print(f"✅ {check_name}: OK {message}")
    else:
        print(f"❌ {check_name}: FAILED {message}")
    return status

def check_env_file():
    """Check if .env file exists"""
    env_path = Path('.env')
    if env_path.exists():
        return print_status(".env File", True, "(Found)")
    else:
        return print_status(".env File", False, "(Not found - copy .env.example)")

def check_env_variables():
    """Check critical environment variables"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'TELEGRAM_BOT_TOKEN',
        'TRONGRID_API_KEY',
        'WALLET_ENCRYPTION_KEY',
        'FRONTEND_URL'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if not missing:
        return print_status("Environment Variables", True, f"(All {len(required_vars)} configured)")
    else:
        return print_status("Environment Variables", False, f"(Missing: {', '.join(missing)})")

def check_redis_connection():
    """Check Redis connection"""
    try:
        import redis
        from dotenv import load_dotenv
        load_dotenv()
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        return print_status("Redis Connection", True, f"({redis_url})")
    except ImportError:
        return print_status("Redis Connection", False, "(redis package not installed)")
    except Exception as e:
        return print_status("Redis Connection", False, f"({str(e)})")

def check_database_connection():
    """Check database connection"""
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            return print_status("Database Connection", False, "(DATABASE_URL not set)")
        
        # Parse DATABASE_URL
        # Format: postgresql://user:password@host:port/database
        conn = psycopg2.connect(db_url)
        conn.close()
        return print_status("Database Connection", True, "(Connected)")
    except ImportError:
        return print_status("Database Connection", False, "(psycopg2 not installed)")
    except Exception as e:
        return print_status("Database Connection", False, f"({str(e)})")

def check_telegram_bot_token():
    """Check Telegram bot token format"""
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token and ':' in token and len(token) > 40:
        # Mask token
        parts = token.split(':')
        masked = f"{parts[0]}:***"
        return print_status("Telegram Bot Token", True, f"({masked})")
    else:
        return print_status("Telegram Bot Token", False, "(Invalid format or not set)")

def check_python_packages():
    """Check if critical packages are installed"""
    packages = [
        'django',
        'djangorestframework',
        'celery',
        'redis',
        'telegram',
        'tronpy',
        'cryptography'
    ]
    
    missing = []
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if not missing:
        return print_status("Python Packages", True, f"(All {len(packages)} installed)")
    else:
        return print_status("Python Packages", False, f"(Missing: {', '.join(missing)})")

def check_frontend():
    """Check if frontend is set up"""
    frontend_path = Path('../frontend')
    package_json = frontend_path / 'package.json'
    node_modules = frontend_path / 'node_modules'
    
    if not package_json.exists():
        return print_status("Frontend Setup", False, "(package.json not found)")
    
    if not node_modules.exists():
        return print_status("Frontend Setup", False, "(node_modules not found - run npm install)")
    
    return print_status("Frontend Setup", True, "(Ready)")

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("🔍 Crypto Escrow Platform - Quick Setup Check")
    print("="*60 + "\n")
    
    checks = [
        ("Environment File", check_env_file),
        ("Environment Variables", check_env_variables),
        ("Python Packages", check_python_packages),
        ("Redis", check_redis_connection),
        ("Database", check_database_connection),
        ("Telegram Token", check_telegram_bot_token),
        ("Frontend", check_frontend),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print_status(name, False, f"(Exception: {str(e)})")
            results.append(False)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All checks passed! ({passed}/{total})")
        print("\n🚀 Your platform is ready to launch!")
        print("\nNext steps:")
        print("1. Start Redis: redis-server")
        print("2. Migrate database: python manage.py migrate")
        print("3. Start Backend: python manage.py runserver")
        print("4. Start Celery: celery -A config worker -l info --pool=solo")
        print("5. Start Bot: python manage.py run_telegram_bot")
        print("6. Start Frontend: cd ../frontend && npm run dev")
    else:
        print(f"⚠️  Some checks failed ({passed}/{total} passed)")
        print("\n📝 Please fix the failed checks before launching.")
        print("\nCommon fixes:")
        print("- Install packages: pip install -r requirements.txt")
        print("- Configure .env: copy .env.example .env")
        print("- Start Redis: redis-server")
        print("- Install frontend: cd ../frontend && npm install")
        print("\nRefer to START_HERE.md for detailed setup instructions.")
    
    print("="*60 + "\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
