"""
Bridge Token service for linking Telegram Bot identity to Web Browser sessions.

A Bridge Token is a short-lived, HMAC-SHA256 signed, single-use token that
proves Telegram identity to the web frontend without re-running the Telegram
Login Widget.  It is embedded in a Deep Link sent by the Telegram bot.

Token format:
    base64url(json_payload) + "." + base64url(hmac_sha256_signature)

Payload fields:
    telegram_id  – int   – Telegram user ID
    user_id      – str   – Django User UUID (string)
    flow         – str   – "register" | "authenticate"
    issued_at    – int   – Unix timestamp (seconds)
    expires_at   – int   – Unix timestamp (seconds, issued_at + 600)

Security properties:
    - Signed with HMAC-SHA256 keyed on Django SECRET_KEY (Req 13.1)
    - Payload contains issued_at / expires_at (Req 13.2)
    - Single-use: consumed token hash stored in Redis (Req 13.3)
    - Rejected if current time > expires_at (Req 13.4)
    - Rejected if HMAC signature does not match (Req 13.5)
"""
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Literal

from django.conf import settings
from django.core.cache import cache

from apps.users.webauthn_service import base64url_encode, base64url_decode

logger = logging.getLogger(__name__)

# Bridge Token lifetime in seconds (10 minutes)
BRIDGE_TOKEN_TTL = 600

FlowType = Literal["register", "authenticate"]


class InvalidBridgeToken(Exception):
    """Raised when a Bridge Token fails any validation check."""
    pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sign(payload_b64: str) -> str:
    """
    Compute HMAC-SHA256 of the base64url-encoded payload using SECRET_KEY.

    Args:
        payload_b64: Base64url-encoded JSON payload string.

    Returns:
        Base64url-encoded HMAC-SHA256 digest.
    """
    key = settings.SECRET_KEY.encode("utf-8")
    message = payload_b64.encode("utf-8")
    digest = hmac.new(key, message, hashlib.sha256).digest()
    return base64url_encode(digest)


def _consumed_cache_key(raw_token: str) -> str:
    """
    Return the Redis cache key used to mark a Bridge Token as consumed.

    Uses SHA-256 of the raw token string so the raw token is never stored
    in Redis.

    Args:
        raw_token: The full Bridge Token string (payload.signature).

    Returns:
        Cache key string: ``webauthn:bridge_used:{sha256_hex}``.
    """
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return f"webauthn:bridge_used:{token_hash}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(user, flow: FlowType) -> str:
    """
    Generate a signed Bridge Token for the given user and flow.

    Args:
        user: Django User instance.  Must have ``telegram_id`` and ``id``.
        flow: Either ``"register"`` (first-time Passkey setup) or
              ``"authenticate"`` (returning user Passkey login).

    Returns:
        A Bridge Token string in the format
        ``base64url(payload) + "." + base64url(signature)``.
    """
    now = int(time.time())
    payload = {
        "telegram_id": user.telegram_id,
        "user_id": str(user.id),
        "flow": flow,
        "issued_at": now,
        "expires_at": now + BRIDGE_TOKEN_TTL,
        "nonce": base64url_encode(os.urandom(16)),
    }

    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_b64 = base64url_encode(payload_json.encode("utf-8"))
    signature_b64 = _sign(payload_b64)

    token = f"{payload_b64}.{signature_b64}"
    logger.debug(
        "Bridge Token generated for user %s (flow=%s, expires_at=%s)",
        user.id,
        flow,
        payload["expires_at"],
    )
    return token


def redeem(token: str):
    """
    Validate and consume a Bridge Token.

    Performs the following checks in order:
    1. Token format (two dot-separated base64url parts).
    2. HMAC-SHA256 signature verification.
    3. Expiry check (``expires_at`` vs current time).
    4. Replay check (Redis key ``webauthn:bridge_used:{sha256(token)}``).
    5. User lookup by ``user_id`` in the payload.

    On success the token is marked as consumed in Redis with a TTL equal to
    the remaining lifetime of the token (so the key expires naturally).

    Args:
        token: The raw Bridge Token string.

    Returns:
        A ``(user, flow)`` tuple where ``user`` is the Django User instance
        and ``flow`` is ``"register"`` or ``"authenticate"``.

    Raises:
        InvalidBridgeToken: If any validation step fails.
    """
    # ------------------------------------------------------------------
    # 1. Parse token format
    # ------------------------------------------------------------------
    parts = token.split(".")
    if len(parts) != 2:
        raise InvalidBridgeToken("Invalid bridge token format")

    payload_b64, provided_signature_b64 = parts

    # ------------------------------------------------------------------
    # 2. Verify HMAC signature (constant-time comparison)
    # ------------------------------------------------------------------
    expected_signature_b64 = _sign(payload_b64)
    if not hmac.compare_digest(
        expected_signature_b64.encode("utf-8"),
        provided_signature_b64.encode("utf-8"),
    ):
        raise InvalidBridgeToken("Invalid bridge token")

    # ------------------------------------------------------------------
    # 3. Decode payload
    # ------------------------------------------------------------------
    try:
        payload_bytes = base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise InvalidBridgeToken(f"Invalid bridge token payload: {exc}") from exc

    required_fields = {"telegram_id", "user_id", "flow", "issued_at", "expires_at"}
    if not required_fields.issubset(payload.keys()):
        raise InvalidBridgeToken("Bridge token payload missing required fields")

    flow = payload["flow"]
    if flow not in ("register", "authenticate"):
        raise InvalidBridgeToken(f"Invalid bridge token flow: {flow!r}")

    # ------------------------------------------------------------------
    # 4. Expiry check
    # ------------------------------------------------------------------
    now = int(time.time())
    if now > payload["expires_at"]:
        raise InvalidBridgeToken("Bridge token has expired")

    # ------------------------------------------------------------------
    # 5. Replay check
    # ------------------------------------------------------------------
    consumed_key = _consumed_cache_key(token)
    if cache.get(consumed_key) is not None:
        raise InvalidBridgeToken("Bridge token has already been used")

    # ------------------------------------------------------------------
    # 6. User lookup
    # ------------------------------------------------------------------
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        user = User.objects.get(id=payload["user_id"])
    except (User.DoesNotExist, Exception) as exc:
        raise InvalidBridgeToken(f"Bridge token user not found: {exc}") from exc

    # Sanity-check that the telegram_id in the token matches the user record
    if user.telegram_id != payload["telegram_id"]:
        raise InvalidBridgeToken("Bridge token telegram_id mismatch")

    # ------------------------------------------------------------------
    # 7. Mark token as consumed (TTL = remaining lifetime)
    # ------------------------------------------------------------------
    remaining_ttl = max(1, payload["expires_at"] - now)
    cache.set(consumed_key, "1", timeout=remaining_ttl)

    logger.info(
        "Bridge Token redeemed for user %s (flow=%s)",
        user.id,
        flow,
    )

    return user, flow
