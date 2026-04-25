"""
Telegram Login Widget authentication backend.
Verifies hash signature from Telegram Login Widget.

Also provides ``ExpiringTokenAuthentication`` — a DRF TokenAuthentication
subclass that rejects tokens older than TOKEN_EXPIRY_DAYS (30 days) with a
401 response and deletes the expired token (Requirements 12.1, 12.2).
"""
import hashlib
import hmac
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import authentication, exceptions
from rest_framework.authtoken.models import Token

from .models import User


# ---------------------------------------------------------------------------
# Expiring token authentication (Requirements 12.1, 12.2)
# ---------------------------------------------------------------------------

class ExpiringTokenAuthentication(authentication.TokenAuthentication):
    """
    DRF TokenAuthentication that enforces a 30-day token lifetime.

    On every authenticated request the token's age is checked.  If it
    exceeds TOKEN_EXPIRY_DAYS the token is deleted and a 401 is raised so
    the client must re-authenticate (Requirement 12.2).

    This class is registered as the first entry in
    ``REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`` in settings.py,
    replacing the stock ``TokenAuthentication``.
    """

    def authenticate_credentials(self, key):
        """
        Validate the token key and enforce the expiry window.

        Raises:
            AuthenticationFailed: If the token does not exist, belongs to an
                inactive user, or has exceeded the 30-day lifetime.
        """
        from .tokens import TOKEN_EXPIRY_DAYS  # avoid circular import at module level

        try:
            token = Token.objects.select_related("user").get(key=key)
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token.")

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted.")

        token_age = timezone.now() - token.created
        if token_age > timedelta(days=TOKEN_EXPIRY_DAYS):
            token.delete()
            raise exceptions.AuthenticationFailed(
                "Token has expired. Please log in again."
            )

        return (token.user, token)


# ---------------------------------------------------------------------------
# Telegram Login Widget authentication
# ---------------------------------------------------------------------------

class TelegramAuthentication(authentication.BaseAuthentication):
    """
    Authenticate users via Telegram Login Widget.
    Verifies the data hash signature.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Telegram '):
            return None
        
        # Parse Telegram auth data
        try:
            auth_data = self._parse_auth_data(auth_header)
        except ValueError as e:
            raise exceptions.AuthenticationFailed(str(e))
        
        # Verify the hash
        if not self._verify_telegram_auth(auth_data):
            raise exceptions.AuthenticationFailed('Invalid Telegram authentication')
        
        # Check if auth is not too old (24 hours) - skip in DEBUG mode
        if not settings.DEBUG:
            auth_date = datetime.fromtimestamp(int(auth_data.get('auth_date', 0)))
            if datetime.now() - auth_date > timedelta(hours=24):
                raise exceptions.AuthenticationFailed('Authentication expired')
        
        # Get or create user
        telegram_id = int(auth_data['id'])
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': auth_data.get('username'),
                'first_name': auth_data.get('first_name'),
                'last_name': auth_data.get('last_name'),
                'photo_url': auth_data.get('photo_url'),
            }
        )
        
        # Update user info if not created
        if not created:
            user.username = auth_data.get('username') or user.username
            user.first_name = auth_data.get('first_name') or user.first_name
            user.last_name = auth_data.get('last_name') or user.last_name
            user.photo_url = auth_data.get('photo_url') or user.photo_url
            user.save(update_fields=['username', 'first_name', 'last_name', 'photo_url'])
        
        return (user, None)
    
    def _parse_auth_data(self, auth_header):
        """Parse Telegram auth data from Authorization header."""
        try:
            data_str = auth_header.replace('Telegram ', '')
            pairs = data_str.split('&')
            auth_data = {}
            for pair in pairs:
                key, value = pair.split('=', 1)
                auth_data[key] = value
            return auth_data
        except Exception:
            raise ValueError('Invalid authorization header format')
    
    def _verify_telegram_auth(self, auth_data):
        """
        Verify Telegram authentication data hash.
        In DEBUG mode, skip verification to allow dev/mock logins.
        """
        check_hash = auth_data.get('hash')
        if not check_hash:
            return False

        # Skip hash verification in development mode
        if settings.DEBUG:
            return True

        # Create data check string
        auth_data_copy = auth_data.copy()
        del auth_data_copy['hash']
        
        data_check_arr = [f'{k}={v}' for k, v in sorted(auth_data_copy.items())]
        data_check_string = '\n'.join(data_check_arr)
        
        # Calculate hash
        secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == check_hash
