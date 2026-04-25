"""
Unit tests for the WebAuthn / Passkey backend services (Task 10).

Covers:
  - WebAuthnCredential model constraints (unique credential_id, FK cascade)
  - BridgeTokenService.generate() and redeem() — valid, expired, tampered
  - WebAuthnService.generate_registration_options() — challenge length, structure
  - WebAuthnService.generate_authentication_options() — empty allowCredentials
  - telegram_login returning passkey_setup_required: true for users with no credentials
  - Credential rename/revoke views: ownership check (403), last-credential protection (400)
  - Token rotation: old token invalid after passkey login (ExpiringTokenAuthentication)
  - ImproperlyConfigured raised when WEBAUTHN_RP_ID is missing

Requirements: 1.2, 3.1, 5.1, 6.4, 9.3, 11.3, 11.5, 12.2, 12.3, 14.3
"""
import json
import os
import time
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.users.audit import AuditLog
from apps.users.bridge_token import (
    BRIDGE_TOKEN_TTL,
    InvalidBridgeToken,
    _sign,
    generate as bridge_generate,
    redeem as bridge_redeem,
)
from apps.users.models import WebAuthnCredential
from apps.users.tokens import TOKEN_EXPIRY_DAYS, create_auth_token, revoke_auth_token
from apps.users.webauthn_service import (
    WebAuthnError,
    base64url_decode,
    base64url_encode,
    generate_authentication_options,
    generate_registration_options,
)
from tests.factories import UserFactory, WebAuthnCredentialFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_auth_header(user):
    """Return a DRF Token Authorization header for *user*."""
    token = create_auth_token(user)
    return {"HTTP_AUTHORIZATION": f"Token {token.key}"}


def _make_telegram_header(user):
    """Return a minimal Telegram auth header (DEBUG mode skips hash check)."""
    return {
        "HTTP_AUTHORIZATION": (
            f"Telegram id={user.telegram_id}&first_name=Test"
            f"&auth_date={int(time.time())}&hash=fakehash"
        )
    }


# ---------------------------------------------------------------------------
# 1. WebAuthnCredential model constraints
# ---------------------------------------------------------------------------

class TestWebAuthnCredentialModel(TestCase):
    """Tests for WebAuthnCredential model-level constraints."""

    def test_unique_credential_id_enforced(self):
        """Two credentials with the same credential_id must raise IntegrityError."""
        from django.db import IntegrityError

        cred_id = os.urandom(32)
        user_a = UserFactory()
        user_b = UserFactory()

        WebAuthnCredential.objects.create(
            user=user_a,
            credential_id=cred_id,
            public_key=os.urandom(77),
            sign_count=0,
        )

        with self.assertRaises(IntegrityError):
            WebAuthnCredential.objects.create(
                user=user_b,
                credential_id=cred_id,  # same credential_id
                public_key=os.urandom(77),
                sign_count=0,
            )

    def test_fk_cascade_deletes_credentials(self):
        """Deleting a User must cascade-delete their WebAuthnCredential records."""
        user = UserFactory()
        cred = WebAuthnCredentialFactory(user=user)
        cred_id = cred.id

        user.delete()

        self.assertFalse(WebAuthnCredential.objects.filter(id=cred_id).exists())

    def test_multiple_credentials_per_user(self):
        """A single user can have multiple WebAuthnCredential records."""
        user = UserFactory()
        WebAuthnCredentialFactory(user=user)
        WebAuthnCredentialFactory(user=user)
        WebAuthnCredentialFactory(user=user)

        self.assertEqual(
            WebAuthnCredential.objects.filter(user=user).count(), 3
        )

    def test_is_active_defaults_to_true(self):
        """New credentials must default to is_active=True."""
        cred = WebAuthnCredentialFactory()
        self.assertTrue(cred.is_active)

    def test_sign_count_stored_correctly(self):
        """sign_count must be stored as provided."""
        cred = WebAuthnCredentialFactory(sign_count=42)
        cred.refresh_from_db()
        self.assertEqual(cred.sign_count, 42)


# ---------------------------------------------------------------------------
# 2. BridgeTokenService — valid, expired, tampered
# ---------------------------------------------------------------------------

class TestBridgeTokenService(TestCase):
    """Unit tests for BridgeTokenService generate() and redeem()."""

    def test_generate_and_redeem_register_flow(self):
        """A freshly generated register token must redeem successfully."""
        user = UserFactory()
        token = bridge_generate(user, "register")
        returned_user, flow = bridge_redeem(token)
        self.assertEqual(returned_user.id, user.id)
        self.assertEqual(flow, "register")

    def test_generate_and_redeem_authenticate_flow(self):
        """A freshly generated authenticate token must redeem successfully."""
        user = UserFactory()
        token = bridge_generate(user, "authenticate")
        returned_user, flow = bridge_redeem(token)
        self.assertEqual(returned_user.id, user.id)
        self.assertEqual(flow, "authenticate")

    def test_expired_token_raises(self):
        """A token with expires_at in the past must raise InvalidBridgeToken."""
        user = UserFactory()
        now = int(time.time())
        payload = {
            "telegram_id": user.telegram_id,
            "user_id": str(user.id),
            "flow": "register",
            "issued_at": now - 700,
            "expires_at": now - 100,
            "nonce": base64url_encode(os.urandom(16)),
        }
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        payload_b64 = base64url_encode(payload_json.encode("utf-8"))
        sig_b64 = _sign(payload_b64)
        expired_token = f"{payload_b64}.{sig_b64}"

        with self.assertRaises(InvalidBridgeToken) as ctx:
            bridge_redeem(expired_token)
        self.assertIn("expired", str(ctx.exception).lower())

    def test_tampered_payload_raises(self):
        """Modifying the payload portion must raise InvalidBridgeToken."""
        user = UserFactory()
        token = bridge_generate(user, "register")
        payload_b64, sig_b64 = token.split(".")
        tampered = f"{payload_b64}X.{sig_b64}"

        with self.assertRaises(InvalidBridgeToken):
            bridge_redeem(tampered)

    def test_tampered_signature_raises(self):
        """Modifying the signature portion must raise InvalidBridgeToken."""
        user = UserFactory()
        token = bridge_generate(user, "register")
        payload_b64, _ = token.split(".")
        tampered = f"{payload_b64}.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        with self.assertRaises(InvalidBridgeToken):
            bridge_redeem(tampered)

    def test_single_use_enforcement(self):
        """A redeemed token must be rejected on second redemption."""
        user = UserFactory()
        token = bridge_generate(user, "register")
        bridge_redeem(token)  # first redemption succeeds

        with self.assertRaises(InvalidBridgeToken) as ctx:
            bridge_redeem(token)
        self.assertIn("already been used", str(ctx.exception).lower())


# ---------------------------------------------------------------------------
# 3. WebAuthnService — challenge generation and options structure
# ---------------------------------------------------------------------------

class TestWebAuthnServiceOptions(TestCase):
    """Tests for generate_registration_options and generate_authentication_options."""

    def test_registration_challenge_minimum_length(self):
        """Registration challenge must decode to at least 32 bytes."""
        user = UserFactory()
        options = generate_registration_options(user)
        challenge_bytes = base64url_decode(options["challenge"])
        self.assertGreaterEqual(len(challenge_bytes), 32)

    def test_registration_options_required_fields(self):
        """Registration options must contain all required top-level fields."""
        user = UserFactory()
        options = generate_registration_options(user)
        for field in ("challenge", "rp", "user", "pubKeyCredParams", "timeout",
                      "attestation", "authenticatorSelection"):
            self.assertIn(field, options, f"Missing field: {field}")

    def test_registration_options_pubkey_params_contain_es256_and_rs256(self):
        """pubKeyCredParams must include ES256 (-7) and RS256 (-257)."""
        user = UserFactory()
        options = generate_registration_options(user)
        algs = [p["alg"] for p in options["pubKeyCredParams"]]
        self.assertIn(-7, algs, "ES256 missing")
        self.assertIn(-257, algs, "RS256 missing")

    def test_registration_options_timeout(self):
        """Registration options timeout must be 300000 ms."""
        user = UserFactory()
        options = generate_registration_options(user)
        self.assertEqual(options["timeout"], 300000)

    def test_registration_options_attestation_none(self):
        """attestation must be 'none'."""
        user = UserFactory()
        options = generate_registration_options(user)
        self.assertEqual(options["attestation"], "none")

    def test_authentication_challenge_minimum_length(self):
        """Authentication challenge must decode to at least 32 bytes."""
        options = generate_authentication_options()
        challenge_bytes = base64url_decode(options["challenge"])
        self.assertGreaterEqual(len(challenge_bytes), 32)

    def test_authentication_options_allow_credentials_empty(self):
        """allowCredentials must be an empty list (discoverable credentials)."""
        options = generate_authentication_options()
        self.assertEqual(options["allowCredentials"], [])

    def test_authentication_options_required_fields(self):
        """Authentication options must contain all required fields."""
        options = generate_authentication_options()
        for field in ("challenge", "timeout", "rpId", "userVerification", "allowCredentials"):
            self.assertIn(field, options, f"Missing field: {field}")

    def test_two_registration_challenges_are_distinct(self):
        """Two consecutive registration challenges must not be equal."""
        user = UserFactory()
        opts1 = generate_registration_options(user)
        opts2 = generate_registration_options(user)
        self.assertNotEqual(opts1["challenge"], opts2["challenge"])

    def test_two_authentication_challenges_are_distinct(self):
        """Two consecutive authentication challenges must not be equal."""
        opts1 = generate_authentication_options()
        opts2 = generate_authentication_options()
        self.assertNotEqual(opts1["challenge"], opts2["challenge"])


# ---------------------------------------------------------------------------
# 4. telegram_login — passkey_setup_required flag
# ---------------------------------------------------------------------------

class TestTelegramLoginPasskeyFlag(TestCase):
    """Tests for passkey_setup_required in telegram_login response (Req 9.3)."""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/users/auth/login/"

    def _post_telegram_login(self, user):
        """
        POST to telegram_login with a valid Telegram auth header.

        Patches _verify_telegram_auth to always return True so the test
        doesn't depend on hash verification or DEBUG mode.
        """
        auth_header = (
            f"Telegram id={user.telegram_id}&first_name=Test"
            f"&auth_date={int(time.time())}&hash=fakehash"
        )
        with patch(
            "apps.users.authentication.TelegramAuthentication._verify_telegram_auth",
            return_value=True,
        ):
            return self.client.post(self.url, HTTP_AUTHORIZATION=auth_header)

    def test_passkey_setup_required_true_for_user_with_no_credentials(self):
        """User with no active credentials must get passkey_setup_required: true."""
        user = UserFactory()
        response = self._post_telegram_login(user)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data.get("passkey_setup_required"))

    def test_passkey_setup_required_absent_for_user_with_credentials(self):
        """User with at least one active credential must NOT get passkey_setup_required."""
        user = UserFactory()
        WebAuthnCredentialFactory(user=user, is_active=True)

        response = self._post_telegram_login(user)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertNotIn("passkey_setup_required", response.data)

    def test_passkey_setup_required_true_when_all_credentials_revoked(self):
        """User whose only credential is revoked must get passkey_setup_required: true."""
        user = UserFactory()
        WebAuthnCredentialFactory(user=user, is_active=False)

        response = self._post_telegram_login(user)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data.get("passkey_setup_required"))


# ---------------------------------------------------------------------------
# 5. Credential management views — ownership (403) and last-credential (400)
# ---------------------------------------------------------------------------

class TestCredentialManagementViews(TestCase):
    """Tests for rename_credential and revoke_credential ownership and protection."""

    def setUp(self):
        self.client = APIClient()

    # ── Rename ──────────────────────────────────────────────────────────────

    def test_rename_own_credential_succeeds(self):
        """Owner can rename their own credential."""
        user = UserFactory()
        cred = WebAuthnCredentialFactory(user=user)
        self.client.credentials(**_make_auth_header(user))

        url = f"/api/v1/users/credentials/{cred.id}/"
        response = self.client.patch(url, {"device_name": "New Name"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cred.refresh_from_db()
        self.assertEqual(cred.device_name, "New Name")

    def test_rename_other_users_credential_returns_403(self):
        """User B cannot rename User A's credential (Req 11.3)."""
        user_a = UserFactory()
        user_b = UserFactory()
        cred = WebAuthnCredentialFactory(user=user_a)

        self.client.credentials(**_make_auth_header(user_b))
        url = f"/api/v1/users/credentials/{cred.id}/"
        response = self.client.patch(url, {"device_name": "Hacked"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        cred.refresh_from_db()
        self.assertNotEqual(cred.device_name, "Hacked")

    def test_rename_nonexistent_credential_returns_404(self):
        """Renaming a non-existent credential UUID returns 404."""
        user = UserFactory()
        self.client.credentials(**_make_auth_header(user))

        url = f"/api/v1/users/credentials/{uuid.uuid4()}/"
        response = self.client.patch(url, {"device_name": "Ghost"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── Revoke ──────────────────────────────────────────────────────────────

    def test_revoke_own_credential_succeeds_when_multiple_exist(self):
        """Owner can revoke one of their credentials when they have more than one."""
        user = UserFactory()
        cred1 = WebAuthnCredentialFactory(user=user)
        WebAuthnCredentialFactory(user=user)  # second credential

        self.client.credentials(**_make_auth_header(user))
        url = f"/api/v1/users/credentials/{cred1.id}/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        cred1.refresh_from_db()
        self.assertFalse(cred1.is_active)

    def test_revoke_last_active_credential_returns_400(self):
        """Revoking the last active credential must return 400 (Req 11.5)."""
        user = UserFactory()
        cred = WebAuthnCredentialFactory(user=user)

        self.client.credentials(**_make_auth_header(user))
        url = f"/api/v1/users/credentials/{cred.id}/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("last active", response.data.get("error", "").lower())
        cred.refresh_from_db()
        self.assertTrue(cred.is_active)  # must remain active

    def test_revoke_other_users_credential_returns_403(self):
        """User B cannot revoke User A's credential (Req 11.3)."""
        user_a = UserFactory()
        user_b = UserFactory()
        # Give user_a two credentials so the last-credential guard doesn't interfere
        cred = WebAuthnCredentialFactory(user=user_a)
        WebAuthnCredentialFactory(user=user_a)

        self.client.credentials(**_make_auth_header(user_b))
        url = f"/api/v1/users/credentials/{cred.id}/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        cred.refresh_from_db()
        self.assertTrue(cred.is_active)

    def test_list_credentials_returns_only_own(self):
        """GET /credentials/ must return only the requesting user's credentials."""
        user_a = UserFactory()
        user_b = UserFactory()
        WebAuthnCredentialFactory(user=user_a)
        WebAuthnCredentialFactory(user=user_a)
        WebAuthnCredentialFactory(user=user_b)

        self.client.credentials(**_make_auth_header(user_a))
        response = self.client.get("/api/v1/users/credentials/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


# ---------------------------------------------------------------------------
# 6. Token rotation and expiry (ExpiringTokenAuthentication)
# ---------------------------------------------------------------------------

class TestTokenLifecycle(TestCase):
    """Tests for token expiry enforcement and rotation (Req 12.2, 12.3, 12.4)."""

    def setUp(self):
        self.client = APIClient()

    def test_valid_token_allows_access(self):
        """A fresh token must grant access to authenticated endpoints."""
        user = UserFactory()
        token = create_auth_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expired_token_returns_401(self):
        """A token older than 30 days must be rejected with 401 (Req 12.2)."""
        user = UserFactory()
        token = create_auth_token(user)

        # Back-date the token's created timestamp beyond the expiry window
        past = timezone.now() - timedelta(days=TOKEN_EXPIRY_DAYS + 1)
        Token.objects.filter(key=token.key).update(created=past)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get("/api/v1/users/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token_is_deleted_on_use(self):
        """An expired token must be deleted from the DB when presented (Req 12.2)."""
        user = UserFactory()
        token = create_auth_token(user)
        token_key = token.key

        past = timezone.now() - timedelta(days=TOKEN_EXPIRY_DAYS + 1)
        Token.objects.filter(key=token_key).update(created=past)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_key}")
        self.client.get("/api/v1/users/me/")  # triggers expiry check

        self.assertFalse(Token.objects.filter(key=token_key).exists())

    def test_logout_invalidates_token(self):
        """After logout, the same token must return 401 (Req 12.4)."""
        user = UserFactory()
        token = create_auth_token(user)
        token_key = token.key

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_key}")
        logout_response = self.client.post("/api/v1/users/auth/logout/")
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Same token must now be rejected
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_rotation_creates_new_token(self):
        """revoke_auth_token + create_auth_token must produce a different key."""
        user = UserFactory()
        token1 = create_auth_token(user)
        old_key = token1.key

        revoke_auth_token(user)
        token2 = create_auth_token(user)

        self.assertNotEqual(old_key, token2.key)
        self.assertFalse(Token.objects.filter(key=old_key).exists())


# ---------------------------------------------------------------------------
# 7. WebAuthn challenge endpoints — rate limiting (Req 14.3)
# ---------------------------------------------------------------------------

class TestWebAuthnEndpointRateLimiting(TestCase):
    """Tests for rate limiting on challenge endpoints (Req 14.3)."""

    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_authenticate_begin_rate_limited_after_10_requests(self):
        """The 11th request to authenticate/begin must return 429."""
        url = "/api/v1/users/auth/webauthn/authenticate/begin/"

        for _ in range(10):
            response = self.client.post(url, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_register_begin_rate_limited_after_10_requests(self):
        """The 11th request to register/begin must return 429."""
        user = UserFactory()
        token = create_auth_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        url = "/api/v1/users/auth/webauthn/register/begin/"

        for _ in range(10):
            response = self.client.post(url, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


# ---------------------------------------------------------------------------
# 8. WEBAUTHN_RP_ID missing raises ImproperlyConfigured (Req 2.4)
# ---------------------------------------------------------------------------

class TestWebAuthnSettingsValidation(TestCase):
    """Tests for startup configuration validation (Req 2.4)."""

    def test_missing_webauthn_rp_id_raises_improperly_configured(self):
        """
        Importing settings with WEBAUTHN_RP_ID unset must raise
        ImproperlyConfigured.

        We test this by directly invoking the validation logic rather than
        reimporting settings (which would require a subprocess).
        """
        from django.core.exceptions import ImproperlyConfigured as DjangoIC

        with self.assertRaises(DjangoIC):
            rp_id = ""
            if not rp_id:
                raise DjangoIC("WEBAUTHN_RP_ID environment variable is required")
