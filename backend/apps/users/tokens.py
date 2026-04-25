"""
Token management for authentication.

Token lifecycle (Requirements 12.1 – 12.4):
  - Tokens expire after 30 days (TOKEN_EXPIRY_DAYS).
  - Expired tokens are deleted on first use and a 401 is returned.
  - Passkey authentication always rotates the token (revoke then create).
  - Logout immediately revokes the token.
"""
from datetime import timedelta

from django.utils import timezone
from rest_framework.authtoken.models import Token

TOKEN_EXPIRY_DAYS = 30


def create_auth_token(user):
    """
    Return a valid (non-expired) DRF Token for *user*.

    If a token already exists and is still within the 30-day window it is
    returned as-is.  If it has expired it is deleted and a fresh one is
    created.  This ensures ``create_auth_token`` is idempotent for active
    sessions while still enforcing the expiry policy.

    Args:
        user: Django User instance.

    Returns:
        Token instance with a valid ``key``.
    """
    token, created = Token.objects.get_or_create(user=user)

    if not created:
        token_age = timezone.now() - token.created
        if token_age > timedelta(days=TOKEN_EXPIRY_DAYS):
            token.delete()
            token = Token.objects.create(user=user)

    return token


def revoke_auth_token(user):
    """
    Immediately invalidate all tokens for *user* (Requirement 12.4).

    Args:
        user: Django User instance.
    """
    Token.objects.filter(user=user).delete()


def validate_token(token_key):
    """
    Look up *token_key* and return the associated user, or ``None``.

    Deletes the token and returns ``None`` if it has exceeded the 30-day
    expiry window (Requirement 12.2).

    Args:
        token_key: Raw token key string.

    Returns:
        User instance, or ``None`` if the token is missing or expired.
    """
    try:
        token = Token.objects.select_related("user").get(key=token_key)
    except Token.DoesNotExist:
        return None

    token_age = timezone.now() - token.created
    if token_age > timedelta(days=TOKEN_EXPIRY_DAYS):
        token.delete()
        return None

    return token.user
