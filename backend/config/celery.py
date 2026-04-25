"""
Celery configuration for async task processing.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('escrow_platform')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Monitor deposits every 30 seconds
    'monitor-deposits': {
        'task': 'apps.wallets.tasks.monitor_deposits',
        'schedule': 30.0,  # seconds
    },
    # Sync wallet balances every hour
    'sync-wallet-balances': {
        'task': 'apps.wallets.tasks.sync_wallet_balances',
        'schedule': crontab(minute=0),  # Every hour
    },
    # Check pending withdrawals every 5 minutes
    'check-pending-withdrawals': {
        'task': 'apps.wallets.tasks.check_pending_withdrawals',
        'schedule': 300.0,  # 5 minutes
    },
    # Generate daily wallet report at midnight
    'generate-wallet-report': {
        'task': 'apps.wallets.tasks.generate_wallet_report',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
