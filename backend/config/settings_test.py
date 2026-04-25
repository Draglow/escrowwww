"""
Test settings — overrides production settings for fast, isolated testing.
Uses SQLite in-memory DB, disables Celery/Redis/Channels, mocks blockchain.
"""
from .settings import *  # noqa: F401, F403

# Use SQLite for tests — no external DB required
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',  # noqa: F405
        'TEST': {
            'NAME': BASE_DIR / 'test_db.sqlite3',  # noqa: F405
        }
    }
}

# Disable Channels (no Redis needed)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# Use in-memory cache (no Redis needed for rate limiting / 2FA)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Run Celery tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable Daphne ASGI server in tests (causes issues with test runner)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'daphne']  # noqa: F405

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable rate limiting middleware in tests
MIDDLEWARE = [m for m in MIDDLEWARE if 'RateLimitMiddleware' not in m]  # noqa: F405

# Ensure DEBUG is True so Telegram auth skips hash verification
DEBUG = True

# Suppress logging noise during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {'class': 'logging.NullHandler'},
    },
    'root': {
        'handlers': ['null'],
    },
}
