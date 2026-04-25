"""
Tests for BridgeTokenService (Task 4).

Covers:
  - Property 11: Bridge Token Integrity (Validates: Requirements 13.1, 13.5)
  - Property 12: Bridge Token Single-Use (Validates: Requirements 13.3)
  - Unit tests for generate() and redeem() covering valid, expired, and
    tampered tokens.
"""
import hashlib
import time

import pytest
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from django.test import TestCase, override_settings

from apps.users.bridge_token import (
    generate,
    redeem,
    InvalidBridgeToken,
    BRIDGE_TOKEN_TTL,
)
from tests.factories import UserFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tamper_token(token: str, tamper_bytes: bytes) -> str:
    """
    XOR the first N bytes of the payload portion of a Bridge Token with
    ``tamper_bytes``, producing a token with a corrupted payload.

    If ``tamper_bytes`` is all-zero the token is returned unchanged; the
    property test strategy ensures at least one non-zero byte.
    """
    parts = token.split(".")
    if len(parts) != 2:
        return token + "X"  # already malformed

    payload_b64, sig_b64 = parts
    payload_chars = list(payload_b64)

    for i, b in enumerate(tamper_bytes):
        if i >= len(payload_chars):
            break
        # XOR the ordinal of the character with the tamper byte, then map
        # back to a printable ASCII character in the base64url alphabet.
        original_ord = ord(payload_chars[i])
        new_ord = (original_ord ^ b) % 128
        # Ensure the result is a printable ASCII character (avoid control chars)
        if new_ord < 32:
            new_ord += 32
        payload_chars[i] = chr(new_ord)

    tampered_payload = "".join(payload_chars)
    # If the tamper produced the same payload (all XOR bytes were 0), append
    # an extra character to guarantee the payload differs.
    if tampered_payload == payload_b64:
        tampered_payload = payload_b64 + "X"

    return f"{tampered_payload}.{sig_b64}"


# ---------------------------------------------------------------------------
# Property 11: Bridge Token Integrity
# Validates: Requirements 13.1, 13.5
# ---------------------------------------------------------------------------

class TestBridgeTokenIntegrity(HypothesisTestCase):
    """
    Feature: unified-auth-passkeys, Property 11: Bridge Token Integrity

    For any generated Bridge Token, modifying any byte of the payload or
    signature portion SHALL cause signature verification to fail and the
    token SHALL be rejected.

    Validates: Requirements 13.1, 13.5
    """

    @given(st.binary(min_size=1, max_size=50))
    @h_settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    def test_tampered_payload_is_rejected(self, tamper_bytes: bytes):
        """
        **Validates: Requirements 13.1, 13.5**

        Any modification to the payload portion must cause redeem() to raise
        InvalidBridgeToken.
        """
        user = UserFactory()
        token = generate(user, "register")
        tampered = _tamper_token(token, tamper_bytes)

        # Only test if the tamper actually changed the token
        if tampered == token:
            return  # skip — tamper was a no-op

        with self.assertRaises(InvalidBridgeToken):
            redeem(tampered)

    @given(st.binary(min_size=1, max_size=50))
    @h_settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    def test_tampered_signature_is_rejected(self, tamper_bytes: bytes):
        """
        **Validates: Requirements 13.1, 13.5**

        Any modification to the signature portion must cause redeem() to raise
        InvalidBridgeToken.
        """
        user = UserFactory()
        token = generate(user, "authenticate")
        parts = token.split(".")
        payload_b64, sig_b64 = parts

        # Tamper the signature
        sig_chars = list(sig_b64)
        for i, b in enumerate(tamper_bytes):
            if i >= len(sig_chars):
                break
            original_ord = ord(sig_chars[i])
            new_ord = (original_ord ^ b) % 128
            if new_ord < 32:
                new_ord += 32
            sig_chars[i] = chr(new_ord)

        tampered_sig = "".join(sig_chars)
        if tampered_sig == sig_b64:
            tampered_sig = sig_b64 + "X"

        tampered = f"{payload_b64}.{tampered_sig}"

        with self.assertRaises(InvalidBridgeToken):
            redeem(tampered)


# ---------------------------------------------------------------------------
# Property 12: Bridge Token Single-Use
# Validates: Requirements 13.3
# ---------------------------------------------------------------------------

class TestBridgeTokenSingleUse(HypothesisTestCase):
    """
    Feature: unified-auth-passkeys, Property 12: Bridge Token Single-Use

    For any valid Bridge Token, redeeming it a second time SHALL return a 401
    error, regardless of whether the token is still within its expiry window.

    Validates: Requirements 13.3
    """

    @given(st.sampled_from(["register", "authenticate"]))
    @h_settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    def test_token_cannot_be_redeemed_twice(self, flow: str):
        """
        **Validates: Requirements 13.3**

        A valid token redeemed once must be rejected on the second redemption.
        """
        user = UserFactory()
        token = generate(user, flow)

        # First redemption must succeed
        returned_user, returned_flow = redeem(token)
        assert returned_user.id == user.id
        assert returned_flow == flow

        # Second redemption must fail
        with self.assertRaises(InvalidBridgeToken):
            redeem(token)


# ---------------------------------------------------------------------------
# Unit tests: generate()
# ---------------------------------------------------------------------------

class TestBridgeTokenGenerate(TestCase):
    """Unit tests for BridgeTokenService.generate()."""

    def test_generate_returns_two_part_token(self):
        """Token must have exactly two dot-separated parts."""
        user = UserFactory()
        token = generate(user, "register")
        parts = token.split(".")
        self.assertEqual(len(parts), 2)

    def test_generate_register_flow(self):
        """Token generated with flow='register' must decode to flow='register'."""
        user = UserFactory()
        token = generate(user, "register")
        returned_user, flow = redeem(token)
        self.assertEqual(flow, "register")
        self.assertEqual(returned_user.id, user.id)

    def test_generate_authenticate_flow(self):
        """Token generated with flow='authenticate' must decode to flow='authenticate'."""
        user = UserFactory()
        token = generate(user, "authenticate")
        returned_user, flow = redeem(token)
        self.assertEqual(flow, "authenticate")
        self.assertEqual(returned_user.id, user.id)

    def test_generate_embeds_telegram_id(self):
        """Token payload must contain the user's telegram_id."""
        import json, base64
        user = UserFactory()
        token = generate(user, "register")
        payload_b64 = token.split(".")[0]
        # Add padding
        padding = (4 - len(payload_b64) % 4) % 4
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * padding))
        self.assertEqual(payload["telegram_id"], user.telegram_id)

    def test_generate_embeds_user_id(self):
        """Token payload must contain the user's UUID as a string."""
        import json, base64
        user = UserFactory()
        token = generate(user, "register")
        payload_b64 = token.split(".")[0]
        padding = (4 - len(payload_b64) % 4) % 4
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * padding))
        self.assertEqual(payload["user_id"], str(user.id))

    def test_generate_sets_expires_at_10_minutes_from_now(self):
        """expires_at must be approximately issued_at + 600 seconds."""
        import json, base64
        user = UserFactory()
        before = int(time.time())
        token = generate(user, "register")
        after = int(time.time())

        payload_b64 = token.split(".")[0]
        padding = (4 - len(payload_b64) % 4) % 4
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * padding))

        self.assertGreaterEqual(payload["expires_at"], before + BRIDGE_TOKEN_TTL)
        self.assertLessEqual(payload["expires_at"], after + BRIDGE_TOKEN_TTL + 1)

    def test_two_tokens_for_same_user_are_distinct(self):
        """Two tokens generated for the same user must not be identical."""
        user = UserFactory()
        t1 = generate(user, "register")
        t2 = generate(user, "register")
        self.assertNotEqual(t1, t2)


# ---------------------------------------------------------------------------
# Unit tests: redeem() — error cases
# ---------------------------------------------------------------------------

class TestBridgeTokenRedeem(TestCase):
    """Unit tests for BridgeTokenService.redeem() error paths."""

    def test_redeem_valid_token_succeeds(self):
        """A freshly generated token must be redeemable."""
        user = UserFactory()
        token = generate(user, "register")
        returned_user, flow = redeem(token)
        self.assertEqual(returned_user.id, user.id)
        self.assertEqual(flow, "register")

    def test_redeem_expired_token_raises(self):
        """A token with expires_at in the past must raise InvalidBridgeToken."""
        import json
        from apps.users.webauthn_service import base64url_encode, base64url_decode
        from apps.users.bridge_token import _sign

        user = UserFactory()
        now = int(time.time())
        payload = {
            "telegram_id": user.telegram_id,
            "user_id": str(user.id),
            "flow": "register",
            "issued_at": now - 700,
            "expires_at": now - 100,  # already expired
        }
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        payload_b64 = base64url_encode(payload_json.encode("utf-8"))
        sig_b64 = _sign(payload_b64)
        expired_token = f"{payload_b64}.{sig_b64}"

        with self.assertRaises(InvalidBridgeToken) as ctx:
            redeem(expired_token)
        self.assertIn("expired", str(ctx.exception).lower())

    def test_redeem_wrong_format_raises(self):
        """A token without exactly one dot must raise InvalidBridgeToken."""
        with self.assertRaises(InvalidBridgeToken):
            redeem("nodothere")

        with self.assertRaises(InvalidBridgeToken):
            redeem("too.many.dots.here")

    def test_redeem_invalid_signature_raises(self):
        """A token with a forged signature must raise InvalidBridgeToken."""
        user = UserFactory()
        token = generate(user, "register")
        payload_b64 = token.split(".")[0]
        forged = f"{payload_b64}.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        with self.assertRaises(InvalidBridgeToken):
            redeem(forged)

    def test_redeem_nonexistent_user_raises(self):
        """A token referencing a non-existent user_id must raise InvalidBridgeToken."""
        import json, uuid
        from apps.users.webauthn_service import base64url_encode
        from apps.users.bridge_token import _sign

        now = int(time.time())
        payload = {
            "telegram_id": 999999999,
            "user_id": str(uuid.uuid4()),  # random UUID — no matching user
            "flow": "register",
            "issued_at": now,
            "expires_at": now + BRIDGE_TOKEN_TTL,
        }
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        payload_b64 = base64url_encode(payload_json.encode("utf-8"))
        sig_b64 = _sign(payload_b64)
        token = f"{payload_b64}.{sig_b64}"

        with self.assertRaises(InvalidBridgeToken):
            redeem(token)

    def test_redeem_telegram_id_mismatch_raises(self):
        """A token where telegram_id doesn't match the user record must be rejected."""
        import json
        from apps.users.webauthn_service import base64url_encode
        from apps.users.bridge_token import _sign

        user = UserFactory()
        now = int(time.time())
        payload = {
            "telegram_id": user.telegram_id + 1,  # wrong telegram_id
            "user_id": str(user.id),
            "flow": "register",
            "issued_at": now,
            "expires_at": now + BRIDGE_TOKEN_TTL,
        }
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        payload_b64 = base64url_encode(payload_json.encode("utf-8"))
        sig_b64 = _sign(payload_b64)
        token = f"{payload_b64}.{sig_b64}"

        with self.assertRaises(InvalidBridgeToken):
            redeem(token)

    def test_redeem_invalid_flow_raises(self):
        """A token with an unrecognised flow value must raise InvalidBridgeToken."""
        import json
        from apps.users.webauthn_service import base64url_encode
        from apps.users.bridge_token import _sign

        user = UserFactory()
        now = int(time.time())
        payload = {
            "telegram_id": user.telegram_id,
            "user_id": str(user.id),
            "flow": "hack",  # invalid flow
            "issued_at": now,
            "expires_at": now + BRIDGE_TOKEN_TTL,
        }
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        payload_b64 = base64url_encode(payload_json.encode("utf-8"))
        sig_b64 = _sign(payload_b64)
        token = f"{payload_b64}.{sig_b64}"

        with self.assertRaises(InvalidBridgeToken):
            redeem(token)
