"""
WebAuthn service for Passkey registration and authentication ceremonies.

Implements challenge generation, registration options, registration verification,
authentication options, and authentication verification using the py_webauthn library.
"""
import os
import base64
import logging
from datetime import datetime, timezone

import webauthn
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone as django_timezone

from apps.users.models import WebAuthnCredential
from apps.users.tokens import revoke_auth_token, create_auth_token
from apps.users.audit import log_audit, AuditLog

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class WebAuthnError(Exception):
    """Raised for all WebAuthn ceremony failures."""
    pass


# ---------------------------------------------------------------------------
# Base64url helpers
# ---------------------------------------------------------------------------

def base64url_encode(data: bytes) -> str:
    """
    Encode bytes to a base64url string without padding.

    Uses the URL-safe alphabet (RFC 4648 §5) and strips trailing '=' characters.

    Args:
        data: Raw bytes to encode.

    Returns:
        Base64url-encoded string without padding.
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(s: str) -> bytes:
    """
    Decode a base64url string (with or without padding) to bytes.

    Handles missing padding by adding the required '=' characters before
    decoding.

    Args:
        s: Base64url-encoded string (padding optional).

    Returns:
        Decoded bytes.

    Raises:
        ValueError: If the input is not valid base64url.
    """
    # Normalise: accept both str and bytes input
    if isinstance(s, bytes):
        s = s.decode("ascii")

    # Strip any existing padding then re-add the correct amount
    s = s.rstrip("=")
    padding_needed = (4 - len(s) % 4) % 4
    s = s + "=" * padding_needed

    # Validate that the string only contains valid base64url characters
    import re as _re
    if not _re.fullmatch(r"[A-Za-z0-9_\-=]*", s):
        raise ValueError(f"Invalid base64url input: contains illegal characters")

    try:
        return base64.urlsafe_b64decode(s)
    except Exception as exc:
        raise ValueError(f"Invalid base64url input: {exc}") from exc


# ---------------------------------------------------------------------------
# Challenge generation
# ---------------------------------------------------------------------------

def generate_challenge() -> bytes:
    """
    Generate a cryptographically random challenge of at least 32 bytes.

    Returns:
        32 random bytes suitable for use as a WebAuthn challenge.
    """
    return os.urandom(32)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def generate_registration_options(user) -> dict:
    """
    Generate a ``PublicKeyCredentialCreationOptions`` dict for the given user.

    Stores a ``Pending_Registration`` record in the Django cache under the key
    ``webauthn:pending_reg:{user.id}`` with a 300-second TTL.  If a pending
    registration already exists for the user it is deleted first.

    Args:
        user: Authenticated Django User instance.

    Returns:
        A dict matching the ``PublicKeyCredentialCreationOptions`` JSON shape
        expected by the browser's ``navigator.credentials.create()`` API.
    """
    challenge = generate_challenge()
    challenge_b64 = base64url_encode(challenge)

    cache_key = f"webauthn:pending_reg:{user.id}"

    # Invalidate any pre-existing pending registration for this user (Req 3.5)
    if cache.get(cache_key) is not None:
        cache.delete(cache_key)

    pending = {
        "challenge": challenge_b64,
        "user_id": str(user.id),
        "created_at": django_timezone.now().isoformat(),
    }
    cache.set(cache_key, pending, timeout=300)

    # Build user.id as base64url of the UTF-8 encoded UUID string
    user_id_b64 = base64url_encode(str(user.id).encode("utf-8"))

    # Determine display name: prefer full name, fall back to username
    display_name = ""
    if user.first_name and user.last_name:
        display_name = f"{user.first_name} {user.last_name}".strip()
    elif user.first_name:
        display_name = user.first_name
    display_name = display_name or user.username or str(user.telegram_id)

    username = user.username or str(user.telegram_id)

    return {
        "challenge": challenge_b64,
        "rp": {
            "id": settings.WEBAUTHN_RP_ID,
            "name": settings.WEBAUTHN_RP_NAME,
        },
        "user": {
            "id": user_id_b64,
            "name": username,
            "displayName": display_name,
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},    # ES256
            {"type": "public-key", "alg": -257},  # RS256
        ],
        "timeout": 300000,
        "attestation": "none",
        "authenticatorSelection": {
            "residentKey": "preferred",
            "userVerification": "preferred",
        },
    }


def verify_registration_response(
    user,
    response: dict,
    device_name: str | None = None,
) -> WebAuthnCredential:
    """
    Verify a WebAuthn registration response and persist the new credential.

    Retrieves and deletes the ``Pending_Registration`` from the cache, then
    calls ``webauthn.verify_registration_response()`` from py_webauthn.  On
    success a ``WebAuthnCredential`` record is created and returned.

    Args:
        user: Authenticated Django User instance.
        response: The ``AttestationResponse`` dict submitted by the client.
        device_name: Optional human-readable label for the credential.

    Returns:
        The newly created ``WebAuthnCredential`` instance.

    Raises:
        WebAuthnError: If the challenge has expired/is missing, or if
            py_webauthn verification fails.
    """
    cache_key = f"webauthn:pending_reg:{user.id}"
    pending = cache.get(cache_key)

    if pending is None:
        raise WebAuthnError("Registration challenge expired or not found")

    # Consume the pending registration immediately (Req 4.5)
    cache.delete(cache_key)

    expected_challenge = base64url_decode(pending["challenge"])

    # Determine the expected origin(s)
    allowed_origins = getattr(settings, "WEBAUTHN_ALLOWED_ORIGINS", [])
    expected_origin = allowed_origins[0] if allowed_origins else f"https://{settings.WEBAUTHN_RP_ID}"

    try:
        verification = webauthn.verify_registration_response(
            credential=response,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=expected_origin,
        )
    except Exception as exc:
        raise WebAuthnError(f"WebAuthn verification failed: {exc}") from exc

    # Truncate device_name to the model's max_length (Req 4.7)
    if device_name and len(device_name) > 100:
        device_name = device_name[:100]

    # Parse aaguid — py_webauthn returns it as a string or UUID-like object
    aaguid = None
    if verification.aaguid:
        try:
            import uuid as _uuid
            aaguid = _uuid.UUID(str(verification.aaguid))
        except (ValueError, AttributeError):
            aaguid = None

    credential = WebAuthnCredential.objects.create(
        user=user,
        credential_id=bytes(verification.credential_id),
        public_key=bytes(verification.credential_public_key),
        sign_count=verification.sign_count,
        device_name=device_name,
        aaguid=aaguid,
    )

    logger.info(
        "WebAuthn credential registered for user %s (device: %s)",
        user.id,
        device_name or "unnamed",
    )

    return credential


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def generate_authentication_options() -> dict:
    """
    Generate a ``PublicKeyCredentialRequestOptions`` dict.

    Stores a ``Pending_Authentication`` record in the Django cache under the
    key ``webauthn:pending_auth:{challenge_b64}`` with a 300-second TTL.

    Returns:
        A dict matching the ``PublicKeyCredentialRequestOptions`` JSON shape
        expected by the browser's ``navigator.credentials.get()`` API.
    """
    challenge = generate_challenge()
    challenge_b64 = base64url_encode(challenge)

    cache_key = f"webauthn:pending_auth:{challenge_b64}"
    pending = {
        "challenge": challenge_b64,
        "created_at": django_timezone.now().isoformat(),
    }
    cache.set(cache_key, pending, timeout=300)

    return {
        "challenge": challenge_b64,
        "timeout": 300000,
        "rpId": settings.WEBAUTHN_RP_ID,
        "userVerification": "preferred",
        "allowCredentials": [],
    }


def verify_authentication_response(response: dict):
    """
    Verify a WebAuthn authentication assertion and return the authenticated user.

    Steps:
    1. Extract ``credential_id`` from the response and look up the matching
       ``WebAuthnCredential`` record.
    2. Retrieve and delete the ``Pending_Authentication`` from the cache.
    3. Call ``webauthn.verify_authentication_response()`` from py_webauthn.
    4. Enforce sign-count anti-cloning (Req 6.4).
    5. Update ``sign_count`` and ``last_used_at`` on the credential.
    6. Rotate the DRF Token for the user (Req 12.3).
    7. Write an ``AuditLog`` entry with ``action='PASSKEY_LOGIN'`` (Req 12.5).

    Args:
        response: The ``AssertionResponse`` dict submitted by the client.

    Returns:
        A ``(User, WebAuthnCredential)`` tuple.

    Raises:
        WebAuthnError: On any verification failure.
    """
    # ------------------------------------------------------------------
    # 1. Look up the credential by credential_id
    # ------------------------------------------------------------------
    raw_id = response.get("rawId") or response.get("id")
    if not raw_id:
        raise WebAuthnError("Missing credential id in authentication response")

    try:
        credential_id_bytes = base64url_decode(raw_id)
    except ValueError as exc:
        raise WebAuthnError(f"Invalid credential id encoding: {exc}") from exc

    try:
        credential_record = WebAuthnCredential.objects.select_related("user").get(
            credential_id=credential_id_bytes
        )
    except WebAuthnCredential.DoesNotExist:
        raise WebAuthnError("Credential not found")

    if not credential_record.is_active:
        raise WebAuthnError("Credential has been revoked")

    # ------------------------------------------------------------------
    # 2. Retrieve and delete the Pending_Authentication from cache
    # ------------------------------------------------------------------
    # The challenge is embedded in the clientDataJSON; we also need to find
    # the matching cache entry.  The client echoes the challenge back in the
    # response's clientDataJSON, but the cache key uses the challenge we
    # issued.  We extract the challenge from the response to locate the key.
    client_data_json_b64 = (
        response.get("response", {}).get("clientDataJSON", "")
    )
    try:
        import json as _json
        client_data = _json.loads(base64url_decode(client_data_json_b64))
        challenge_from_client = client_data.get("challenge", "")
    except Exception:
        challenge_from_client = ""

    cache_key = f"webauthn:pending_auth:{challenge_from_client}"
    pending = cache.get(cache_key)

    if pending is None:
        raise WebAuthnError("Authentication challenge expired or not found")

    # Consume the pending authentication immediately
    cache.delete(cache_key)

    expected_challenge = base64url_decode(pending["challenge"])

    # ------------------------------------------------------------------
    # 3. Verify the assertion with py_webauthn
    # ------------------------------------------------------------------
    allowed_origins = getattr(settings, "WEBAUTHN_ALLOWED_ORIGINS", [])
    expected_origin = allowed_origins[0] if allowed_origins else f"https://{settings.WEBAUTHN_RP_ID}"

    try:
        verification = webauthn.verify_authentication_response(
            credential=response,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=expected_origin,
            credential_public_key=bytes(credential_record.public_key),
            credential_current_sign_count=credential_record.sign_count,
        )
    except Exception as exc:
        raise WebAuthnError(f"WebAuthn verification failed: {exc}") from exc

    # ------------------------------------------------------------------
    # 4. Sign-count anti-cloning check (Req 6.4)
    # ------------------------------------------------------------------
    new_sign_count = verification.new_sign_count
    stored_sign_count = credential_record.sign_count

    if stored_sign_count > 0 and new_sign_count <= stored_sign_count:
        raise WebAuthnError(
            "Authenticator sign count invalid — possible cloned authenticator"
        )

    # ------------------------------------------------------------------
    # 5. Update credential record
    # ------------------------------------------------------------------
    credential_record.sign_count = new_sign_count
    credential_record.last_used_at = django_timezone.now()
    credential_record.save(update_fields=["sign_count", "last_used_at"])

    user = credential_record.user

    # ------------------------------------------------------------------
    # 6. Rotate DRF Token (Req 12.3)
    # ------------------------------------------------------------------
    revoke_auth_token(user)
    create_auth_token(user)

    # ------------------------------------------------------------------
    # 7. Write AuditLog entry (Req 12.5)
    # ------------------------------------------------------------------
    credential_id_hex = credential_id_bytes.hex()
    log_audit(
        user=user,
        action="PASSKEY_LOGIN",
        details={"credential_id": credential_id_hex},
    )

    logger.info(
        "WebAuthn authentication successful for user %s (credential: %s)",
        user.id,
        credential_id_hex,
    )

    return user, credential_record
