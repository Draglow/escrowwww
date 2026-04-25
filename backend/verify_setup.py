#!/usr/bin/env python
"""
Setup Verification Script
Checks if all required services and configurations are ready
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.db import connection
from django.core.cache import cache
import redis

def print_status(check_name, status, message=""):
    """Print colored status message"""
    if status:
        print(f"✅ {check_name}: OK {message}")
    else:
        print(f"❌ {check_name}: FAILED {message}")
    return status

def check_database():
    """Check database connection"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return print_status("Database Connection", True, f"({settings.DATABASES['default']['ENGINE']})")
    except Exception as e:
        return print_status("Database Connection", False, f"({str(e)})")

def check_redis():
    """Check Redis connection"""
    try:
        cache.set('test_key', 'test_value', 10)
        value = cache.get('test_key')
        if value == 'test_value':
            return print_status("Redis Connection", True)
        else:
            return print_status("Redis Connection", False, "(Cache test failed)")
    except Exception as e:
        return print_status("Redis Connection", False, f"({str(e)})")

def check_telegram_bot():
    """Check Telegram bot token"""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if token and len(token) > 20:
        # Mask token for security
        masked = f"{token[:10]}...{token[-10:]}"
        return print_status("Telegram Bot Token", True, f"({masked})")
    else:
        return print_status("Telegram Bot Token", False, "(Not configured)")

def check_tron_config():
    """Check Tron network configuration"""
    api_key = getattr(settings, 'TRONGRID_API_KEY', None)
    network = getattr(settings, 'TRON_NETWORK', None)
    if api_key and network:
        return print_status("Tron Configuration", True, f"(Network: {network})")
    else:
        return print_status("Tron Configuration", False, "(Not configured)")

def check_encryption_key():
    """Check wallet encryption key"""
    key = getattr(settings, 'WALLET_ENCRYPTION_KEY', None)
    if key and len(key) > 20:
        return print_status("Wallet Encryption Key", True)
    else:
        return print_status("Wallet Encryption Key", False, "(Not configured)")

def check_frontend_url():
    """Check frontend URL"""
    url = getattr(settings, 'FRONTEND_URL', None)
    if url:
        return print_status("Frontend URL", True, f"({url})")
    else:
        return print_status("Frontend URL", False, "(Not configured)")

def check_models():
    """Check if models are migrated"""
    try:
        from apps.users.models import User
        from apps.wallets.models import Wallet
        from apps.deals.models import Deal
        
        user_count = User.objects.count()
        wallet_count = Wallet.objects.count()
        deal_count = Deal.objects.count()
        
        print_status("Database Models", True, f"(Users: {user_count}, Wallets: {wallet_count}, Deals: {deal_count})")
        return True
    except Exception as e:
        return print_status("Database Models", False, f"({str(e)})")

def check_celery():
    """Check Celery configuration"""
    broker = getattr(settings, 'CELERY_BROKER_URL', None)
    backend = getattr(settings, 'CELERY_RESULT_BACKEND', None)
    if broker and backend:
        return print_status("Celery Configuration", True)
    else:
        return print_status("Celery Configuration", False, "(Not configured)")

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("🔍 Crypto Escrow Platform - Setup Verification")
    print("="*60 + "\n")
    
    checks = [
        ("Database", check_database),
        ("Redis", check_redis),
        ("Telegram Bot", check_telegram_bot),
        ("Tron Network", check_tron_config),
        ("Encryption", check_encryption_key),
        ("Frontend", check_frontend_url),
        ("Models", check_models),
        ("Celery", check_celery),
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
        print("2. Start Backend: python manage.py runserver")
        print("3. Start Celery: celery -A config worker -l info --pool=solo")
        print("4. Start Bot: python manage.py run_telegram_bot")
        print("5. Start Frontend: cd ../frontend && npm run dev")
    else:
        print(f"⚠️  Some checks failed ({passed}/{total} passed)")
        print("\n📝 Please fix the failed checks before launching.")
        print("\nRefer to START_HERE.md for detailed setup instructions.")
    
    print("="*60 + "\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
