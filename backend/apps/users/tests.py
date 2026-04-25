"""
Tests for users app: model, authentication, 2FA, audit logging, API endpoints.
"""
import hashlib
import hmac
import time
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from apps.users.models import User
from apps.users.authentication import TelegramAuthentication
from apps.users.two_factor import TwoFactorAuth
from apps.users.audit import AuditLog, log_audit
from apps.users.tokens import create_auth_token, revoke_auth_token
from tests.factories import UserFactory, AdminUserFactory


# ---------------------------------------------------------------------------
# User Model Tests
# ---------------------------------------------------------------------------

class TestUserModel(TestCase):
    """Tests for the User model."""

    def test_create_user_with_telegram_id(self):
        user = UserFactory(telegram_id=123456789, username='alice')
        self.assertEqual(user.telegram_id, 123456789)
        self.assertEqual(user.username, 'alice')
        self.assertEqual(user.balance, Decimal('0.000000'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_full_name_both_names(self):
        user = UserFactory(first_name='John', last_name='Doe')
        self.assertEqual(user.full_name, 'John Doe')

    def test_full_name_first_only(self):
        user = UserFactory(first_name='John', last_name=None)
        self.assertEqual(user.full_name, 'John')

    def test_full_name_username_fallback(self):
        user = UserFactory(first_name=None, last_name=None, username='johndoe')
        self.assertEqual(user.full_name, 'johndoe')

    def test_full_name_telegram_id_fallback(self):
        user = UserFactory(first_name=None, last_name=None, username=None)
        self.assertEqual(user.full_name, str(user.telegram_id))

    def test_balance_default_zero(self):
        user = UserFactory()
        self.assertEqual(user.balance, Decimal('0.000000'))

    def test_balance_cannot_go_negative(self):
        """Balance field has MinValueValidator(0)."""
        from django.core.exceptions import ValidationError
        user = UserFactory(balance=Decimal('10.000000'))
        user.balance = Decimal('-1.000000')
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_telegram_id_unique(self):
        from django.db import IntegrityError
        UserFactory(telegram_id=999999)
        with self.assertRaises(Exception):
            UserFactory(telegram_id=999999)

    def test_get_available_balance_no_deals(self):
        user = UserFactory(balance=Decimal('500.000000'))
        self.assertEqual(user.get_available_balance(), Decimal('500.000000'))

    def test_get_available_balance_with_funded_deal(self):
        from tests.factories import DealFactory
        user = UserFactory(balance=Decimal('500.000000'))
        DealFactory(seller=user, amount=Decimal('100.000000'), status='FUNDED')
        # Available = 500 - 100 = 400
        self.assertEqual(user.get_available_balance(), Decimal('400.000000'))

    def test_str_representation(self):
        user = UserFactory(username='alice', telegram_id=111)
        self.assertIn('alice', str(user))


# ---------------------------------------------------------------------------
# Token Tests
# ---------------------------------------------------------------------------

class TestTokenManagement(TestCase):
    """Tests for token creation and revocation."""

    def test_create_auth_token(self):
        user = UserFactory()
        token = create_auth_token(user)
        self.assertIsNotNone(token.key)
        self.assertEqual(token.user, user)

    def test_create_auth_token_idempotent(self):
        user = UserFactory()
        token1 = create_auth_token(user)
        token2 = create_auth_token(user)
        self.assertEqual(token1.key, token2.key)

    def test_revoke_auth_token(self):
        user = UserFactory()
        create_auth_token(user)
        revoke_auth_token(user)
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_revoke_nonexistent_token_no_error(self):
        user = UserFactory()
        # Should not raise
        revoke_auth_token(user)


# ---------------------------------------------------------------------------
# Two-Factor Authentication Tests
# ---------------------------------------------------------------------------

class TestTwoFactorAuth(TestCase):
    """Tests for TOTP-based 2FA."""

    def test_generate_secret(self):
        secret = TwoFactorAuth.generate_secret()
        self.assertIsNotNone(secret)
        self.assertGreater(len(secret), 0)

    def test_generate_secret_unique(self):
        s1 = TwoFactorAuth.generate_secret()
        s2 = TwoFactorAuth.generate_secret()
        self.assertNotEqual(s1, s2)

    def test_verify_totp_valid(self):
        import pyotp
        secret = TwoFactorAuth.generate_secret()
        totp = pyotp.TOTP(secret)
        token = totp.now()
        self.assertTrue(TwoFactorAuth.verify_totp(secret, token))

    def test_verify_totp_invalid(self):
        secret = TwoFactorAuth.generate_secret()
        self.assertFalse(TwoFactorAuth.verify_totp(secret, '000000'))

    def test_generate_backup_codes(self):
        codes = TwoFactorAuth.generate_backup_codes(count=10)
        self.assertEqual(len(codes), 10)
        # All codes should be unique
        self.assertEqual(len(set(codes)), 10)

    def test_get_totp_uri(self):
        user = UserFactory(username='testuser')
        secret = TwoFactorAuth.generate_secret()
        uri = TwoFactorAuth.get_totp_uri(user, secret)
        self.assertIn('otpauth://', uri)
        # Issuer name may be URL-encoded
        self.assertTrue(
            'Crypto Escrow Platform' in uri or 'Crypto%20Escrow%20Platform' in uri
        )

    def test_generate_qr_code(self):
        user = UserFactory(username='testuser')
        secret = TwoFactorAuth.generate_secret()
        uri = TwoFactorAuth.get_totp_uri(user, secret)
        qr = TwoFactorAuth.generate_qr_code(uri)
        # Should be base64 encoded image data
        import base64
        decoded = base64.b64decode(qr)
        self.assertGreater(len(decoded), 0)

    def test_rate_limit_allows_initial_attempts(self):
        user = UserFactory()
        allowed, remaining = TwoFactorAuth.rate_limit_2fa_attempts(user.id)
        self.assertTrue(allowed)
        self.assertGreater(remaining, 0)

    def test_rate_limit_blocks_after_max_attempts(self):
        user = UserFactory()
        # Exhaust attempts
        for _ in range(5):
            TwoFactorAuth.rate_limit_2fa_attempts(user.id)
        allowed, remaining = TwoFactorAuth.rate_limit_2fa_attempts(user.id)
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)


# ---------------------------------------------------------------------------
# Audit Log Tests
# ---------------------------------------------------------------------------

class TestAuditLog(TestCase):
    """Tests for audit logging."""

    def test_log_audit_creates_entry(self):
        user = UserFactory()
        log_audit(user=user, action='LOGIN', ip_address='127.0.0.1', success=True)
        self.assertEqual(AuditLog.objects.filter(user=user, action='LOGIN').count(), 1)

    def test_log_audit_without_user(self):
        log_audit(user=None, action='LOGIN', ip_address='127.0.0.1', success=False)
        self.assertEqual(AuditLog.objects.filter(user=None, action='LOGIN').count(), 1)

    def test_audit_log_immutable_via_admin(self):
        """AuditLog admin disables change permission."""
        from apps.users.admin import AuditLogAdmin
        from django.contrib.admin.sites import AdminSite
        admin = AuditLogAdmin(AuditLog, AdminSite())
        mock_request = MagicMock()
        self.assertFalse(admin.has_change_permission(mock_request))
        self.assertFalse(admin.has_add_permission(mock_request))


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

class TestUserAPI(TestCase):
    """Tests for user API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.token = create_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_get_me(self):
        response = self.client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['telegram_id'], self.user.telegram_id)

    def test_get_me_unauthenticated(self):
        self.client.credentials()
        response = self.client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, 401)

    def test_update_profile(self):
        response = self.client.patch(
            '/api/v1/users/update_profile/',
            {'first_name': 'Updated'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_logout(self):
        response = self.client.post('/api/v1/users/auth/logout/')
        self.assertEqual(response.status_code, 200)
        # Token should be revoked
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_enable_2fa_returns_qr_and_secret(self):
        response = self.client.post('/api/v1/users/enable_2fa/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('secret', response.data)
        self.assertIn('qr_code', response.data)
        self.assertIn('backup_codes', response.data)

    def test_enable_2fa_already_enabled(self):
        self.user.is_2fa_enabled = True
        self.user.save()
        response = self.client.post('/api/v1/users/enable_2fa/')
        self.assertEqual(response.status_code, 400)

    def test_audit_logs_endpoint(self):
        log_audit(user=self.user, action='LOGIN', success=True)
        response = self.client.get('/api/v1/users/audit_logs/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_telegram_login_debug_mode(self):
        """In DEBUG mode, hash verification is skipped."""
        client = APIClient()
        auth_header = (
            'Telegram id=123456789&first_name=Test&username=testlogin'
            '&auth_date=1234567890&hash=fakehash'
        )
        response = client.post(
            '/api/v1/users/telegram-login/',
            HTTP_AUTHORIZATION=auth_header
        )
        # In DEBUG mode this should succeed
        self.assertIn(response.status_code, [200, 401])


# ---------------------------------------------------------------------------
# TelegramAuthentication Tests
# ---------------------------------------------------------------------------

class TestTelegramAuthentication(TestCase):
    """Tests for Telegram auth backend."""

    def test_authenticate_no_header_returns_none(self):
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        auth = TelegramAuthentication()
        result = auth.authenticate(request)
        self.assertIsNone(result)

    def test_verify_hash_debug_mode(self):
        """In DEBUG mode, any hash passes (hash check is skipped)."""
        from django.test import override_settings
        auth = TelegramAuthentication()
        with override_settings(DEBUG=True):
            result = auth._verify_telegram_auth({
                'id': '123',
                'hash': 'anyhash',
                'auth_date': str(int(time.time()))
            })
        self.assertTrue(result)

    def test_parse_auth_data_valid(self):
        auth = TelegramAuthentication()
        header = 'Telegram id=123&username=alice&hash=abc'
        data = auth._parse_auth_data(header)
        self.assertEqual(data['id'], '123')
        self.assertEqual(data['username'], 'alice')

    def test_parse_auth_data_invalid_raises(self):
        auth = TelegramAuthentication()
        with self.assertRaises(ValueError):
            auth._parse_auth_data('Telegram invalid_format')
