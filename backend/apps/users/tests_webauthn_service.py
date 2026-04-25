"""
Property-based tests for WebAuthnService (Task 3).

Uses Hypothesis to verify universal properties of the base64url utilities,
challenge generation, and options structure functions.

Properties tested:
  - Property 1: Base64url Round-Trip (Validates: Requirements 15.3)
  - Property 2: Challenge Uniqueness and Minimum Length (Validates: Requirements 3.1, 5.1)
  - Property 4: Registration Options Structure (Validates: Requirements 3.4)
  - Property 5: Authentication Options Structure (Validates: Requirements 5.3)
"""
import pytest
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from django.test import TestCase, override_settings

from apps.users.webauthn_service import (
    base64url_encode,
    base64url_decode,
    generate_challenge,
    generate_registration_options,
    generate_authentication_options,
    WebAuthnError,
)
from tests.factories import UserFactory


# ---------------------------------------------------------------------------
# Property 1: Base64url Round-Trip
# Validates: Requirements 15.3
# ---------------------------------------------------------------------------

class TestBase64urlRoundTrip(HypothesisTestCase):
    """
    Feature: unified-auth-passkeys, Property 1: Base64url Round-Trip

    For any byte sequence of any length, encoding it with base64url and then
    decoding the result SHALL produce the original byte sequence.

    Validates: Requirements 15.3
    """

    @given(st.binary(min_size=0, max_size=1024))
    @h_settings(max_examples=20)
    def test_base64url_round_trip(self, data: bytes):
        """
        **Validates: Requirements 15.3**

        Encoding then decoding any byte sequence must return the original bytes.
        """
        assert base64url_decode(base64url_encode(data)) == data

    def test_base64url_encode_no_padding(self):
        """Encoded output must not contain '=' padding characters."""
        for length in range(0, 10):
            data = bytes(range(length))
            encoded = base64url_encode(data)
            assert "=" not in encoded

    def test_base64url_encode_url_safe_alphabet(self):
        """Encoded output must only use URL-safe characters (no '+' or '/')."""
        import os
        data = os.urandom(256)
        encoded = base64url_encode(data)
        assert "+" not in encoded
        assert "/" not in encoded

    def test_base64url_decode_handles_missing_padding(self):
        """Decoder must accept strings without padding."""
        # 'YQ' is 'a' without padding
        assert base64url_decode("YQ") == b"a"
        # 'YWI' is 'ab' without padding
        assert base64url_decode("YWI") == b"ab"

    def test_base64url_decode_raises_on_malformed_input(self):
        """Decoder must raise ValueError for non-base64url input."""
        with pytest.raises(ValueError):
            base64url_decode("!!!invalid!!!")

    def test_base64url_empty_bytes(self):
        """Empty bytes round-trip correctly."""
        assert base64url_decode(base64url_encode(b"")) == b""

    def test_base64url_single_byte(self):
        """Single byte round-trips correctly."""
        for byte_val in range(256):
            data = bytes([byte_val])
            assert base64url_decode(base64url_encode(data)) == data


# ---------------------------------------------------------------------------
# Property 2: Challenge Uniqueness and Minimum Length
# Validates: Requirements 3.1, 5.1
# ---------------------------------------------------------------------------

class TestChallengeUniquenessAndLength(HypothesisTestCase):
    """
    Feature: unified-auth-passkeys, Property 2: Challenge Uniqueness and Minimum Length

    For any two consecutive calls to the challenge generation function, the two
    challenges SHALL be distinct, and each SHALL have a byte length of at least 32.

    Validates: Requirements 3.1, 5.1
    """

    @given(st.integers(min_value=2, max_value=10))
    @h_settings(max_examples=10)
    def test_challenge_uniqueness_and_length(self, n: int):
        """
        **Validates: Requirements 3.1, 5.1**

        Generate N challenges; all must be at least 32 bytes and all must be distinct.
        """
        challenges = [generate_challenge() for _ in range(n)]
        # All challenges must be at least 32 bytes
        assert all(len(c) >= 32 for c in challenges), (
            f"Some challenges are shorter than 32 bytes: {[len(c) for c in challenges]}"
        )
        # All challenges must be distinct
        assert len(set(challenges)) == len(challenges), (
            "Duplicate challenges detected — challenge generation is not sufficiently random"
        )

    def test_challenge_minimum_length(self):
        """A single challenge must be at least 32 bytes."""
        challenge = generate_challenge()
        assert len(challenge) >= 32

    def test_challenge_is_bytes(self):
        """generate_challenge() must return bytes."""
        challenge = generate_challenge()
        assert isinstance(challenge, bytes)

    def test_two_challenges_are_distinct(self):
        """Two consecutive challenges must not be equal."""
        c1 = generate_challenge()
        c2 = generate_challenge()
        assert c1 != c2


# ---------------------------------------------------------------------------
# Property 4: Registration Options Structure
# Validates: Requirements 3.4
# ---------------------------------------------------------------------------

class TestRegistrationOptionsStructure(HypothesisTestCase):
    """
    Feature: unified-auth-passkeys, Property 4: Registration Options Structure

    For any authenticated user, the PublicKeyCredentialCreationOptions returned
    by generate_registration_options() SHALL contain all required fields with
    correct types/values.

    Validates: Requirements 3.4
    """

    @given(st.integers(min_value=0, max_value=99))
    @h_settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_registration_options_structure(self, _seed: int):
        """
        **Validates: Requirements 3.4**

        For any user, registration options must contain all required fields.
        """
        user = UserFactory()
        options = generate_registration_options(user)

        # Required top-level keys
        assert "challenge" in options, "Missing 'challenge' field"
        assert "rp" in options, "Missing 'rp' field"
        assert "user" in options, "Missing 'user' field"
        assert "pubKeyCredParams" in options, "Missing 'pubKeyCredParams' field"
        assert "timeout" in options, "Missing 'timeout' field"
        assert "attestation" in options, "Missing 'attestation' field"
        assert "authenticatorSelection" in options, "Missing 'authenticatorSelection' field"

        # challenge: base64url string, decodes to >= 32 bytes
        challenge_b64 = options["challenge"]
        assert isinstance(challenge_b64, str), "challenge must be a string"
        challenge_bytes = base64url_decode(challenge_b64)
        assert len(challenge_bytes) >= 32, (
            f"Challenge too short: {len(challenge_bytes)} bytes (minimum 32)"
        )

        # rp: must have id and name
        rp = options["rp"]
        assert "id" in rp, "Missing rp.id"
        assert "name" in rp, "Missing rp.name"
        assert isinstance(rp["id"], str), "rp.id must be a string"
        assert isinstance(rp["name"], str), "rp.name must be a string"

        # user: must have id, name, displayName
        user_field = options["user"]
        assert "id" in user_field, "Missing user.id"
        assert "name" in user_field, "Missing user.name"
        assert "displayName" in user_field, "Missing user.displayName"

        # pubKeyCredParams: must contain ES256 (-7) and RS256 (-257)
        params = options["pubKeyCredParams"]
        assert isinstance(params, list), "pubKeyCredParams must be a list"
        algs = [p["alg"] for p in params]
        assert -7 in algs, "ES256 (-7) missing from pubKeyCredParams"
        assert -257 in algs, "RS256 (-257) missing from pubKeyCredParams"
        for p in params:
            assert p["type"] == "public-key", "pubKeyCredParams type must be 'public-key'"

        # timeout: 300000 ms
        assert options["timeout"] == 300000, f"Expected timeout=300000, got {options['timeout']}"

        # attestation: "none"
        assert options["attestation"] == "none", (
            f"Expected attestation='none', got {options['attestation']!r}"
        )

        # authenticatorSelection
        auth_sel = options["authenticatorSelection"]
        assert "residentKey" in auth_sel, "Missing authenticatorSelection.residentKey"
        assert "userVerification" in auth_sel, "Missing authenticatorSelection.userVerification"
        assert auth_sel["residentKey"] == "preferred"
        assert auth_sel["userVerification"] == "preferred"

    def test_registration_options_stores_pending_in_cache(self):
        """generate_registration_options() must store a Pending_Registration in cache."""
        from django.core.cache import cache
        user = UserFactory()
        generate_registration_options(user)
        cache_key = f"webauthn:pending_reg:{user.id}"
        pending = cache.get(cache_key)
        assert pending is not None, "Pending_Registration not found in cache"
        assert "challenge" in pending
        assert "user_id" in pending
        assert pending["user_id"] == str(user.id)

    def test_registration_options_replaces_existing_pending(self):
        """Calling generate_registration_options() twice replaces the first pending."""
        from django.core.cache import cache
        user = UserFactory()
        options1 = generate_registration_options(user)
        options2 = generate_registration_options(user)

        # The cache should hold the second challenge, not the first
        cache_key = f"webauthn:pending_reg:{user.id}"
        pending = cache.get(cache_key)
        assert pending is not None
        assert pending["challenge"] == options2["challenge"]
        assert pending["challenge"] != options1["challenge"]


# ---------------------------------------------------------------------------
# Property 5: Authentication Options Structure
# Validates: Requirements 5.3
# ---------------------------------------------------------------------------

class TestAuthenticationOptionsStructure(HypothesisTestCase):
    """
    Feature: unified-auth-passkeys, Property 5: Authentication Options Structure

    For any call to generate_authentication_options(), the returned dict SHALL
    contain all required fields: challenge, timeout, rpId, userVerification,
    and allowCredentials (empty list).

    Validates: Requirements 5.3
    """

    @given(st.integers(min_value=0, max_value=99))
    @h_settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_authentication_options_structure(self, _seed: int):
        """
        **Validates: Requirements 5.3**

        Authentication options must contain all required fields with correct values.
        """
        options = generate_authentication_options()

        # Required fields
        assert "challenge" in options, "Missing 'challenge' field"
        assert "timeout" in options, "Missing 'timeout' field"
        assert "rpId" in options, "Missing 'rpId' field"
        assert "userVerification" in options, "Missing 'userVerification' field"
        assert "allowCredentials" in options, "Missing 'allowCredentials' field"

        # challenge: base64url string, decodes to >= 32 bytes
        challenge_b64 = options["challenge"]
        assert isinstance(challenge_b64, str), "challenge must be a string"
        challenge_bytes = base64url_decode(challenge_b64)
        assert len(challenge_bytes) >= 32, (
            f"Challenge too short: {len(challenge_bytes)} bytes (minimum 32)"
        )

        # timeout: 300000 ms
        assert options["timeout"] == 300000, f"Expected timeout=300000, got {options['timeout']}"

        # rpId: non-empty string
        assert isinstance(options["rpId"], str), "rpId must be a string"
        assert len(options["rpId"]) > 0, "rpId must not be empty"

        # userVerification: "preferred"
        assert options["userVerification"] == "preferred", (
            f"Expected userVerification='preferred', got {options['userVerification']!r}"
        )

        # allowCredentials: empty list (discoverable credentials / resident keys)
        assert options["allowCredentials"] == [], (
            f"Expected allowCredentials=[], got {options['allowCredentials']!r}"
        )

    def test_authentication_options_stores_pending_in_cache(self):
        """generate_authentication_options() must store a Pending_Authentication in cache."""
        from django.core.cache import cache
        options = generate_authentication_options()
        challenge_b64 = options["challenge"]
        cache_key = f"webauthn:pending_auth:{challenge_b64}"
        pending = cache.get(cache_key)
        assert pending is not None, "Pending_Authentication not found in cache"
        assert "challenge" in pending
        assert pending["challenge"] == challenge_b64

    def test_authentication_options_each_call_unique_challenge(self):
        """Each call to generate_authentication_options() must produce a unique challenge."""
        options1 = generate_authentication_options()
        options2 = generate_authentication_options()
        assert options1["challenge"] != options2["challenge"], (
            "Two consecutive authentication challenges must be distinct"
        )
