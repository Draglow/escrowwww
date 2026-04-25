"""
WebAuthn (Passkey) API views.

Endpoints:
  POST /api/v1/users/auth/webauthn/register/begin/       – issue registration challenge
  POST /api/v1/users/auth/webauthn/register/complete/    – verify registration response
  POST /api/v1/users/auth/webauthn/authenticate/begin/   – issue authentication challenge
  POST /api/v1/users/auth/webauthn/authenticate/complete/ – verify assertion, issue token
  POST /api/v1/users/auth/webauthn/bridge/redeem/        – redeem a Bridge Token

Requirements: 14.1, 14.3
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .bridge_token import InvalidBridgeToken, generate as bridge_generate, redeem as bridge_redeem
from .rate_limiting import rate_limit
from .serializers import UserProfileSerializer
from .tokens import create_auth_token
from .webauthn_service import (
    WebAuthnError,
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@rate_limit(max_requests=10, window=60)
def webauthn_register_begin(request):
    """
    Issue a WebAuthn registration challenge for the authenticated user.

    Request body (optional):
        { "device_name": "MacBook Touch ID" }

    Response:
        PublicKeyCredentialCreationOptions JSON (challenge base64url-encoded).

    Requirements: 3.1–3.5, 14.1, 14.3
    """
    try:
        options = generate_registration_options(request.user)
        return Response(options, status=status.HTTP_200_OK)
    except WebAuthnError as exc:
        logger.warning("register/begin failed for user %s: %s", request.user.id, exc)
        return Response(
            {"error": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        logger.exception("Unexpected error in register/begin for user %s", request.user.id)
        return Response(
            {"error": "Registration challenge generation failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def webauthn_register_complete(request):
    """
    Verify a WebAuthn registration response and persist the new credential.

    Request body:
        {
            "credential": <AttestationResponse JSON from @simplewebauthn/browser>,
            "device_name": "MacBook Touch ID"   // optional
        }

    Response:
        { "token": "<DRF token key>", "user": { ... } }

    Requirements: 4.1–4.7, 14.1
    """
    credential = request.data.get("credential")
    device_name = request.data.get("device_name") or None

    if not credential:
        return Response(
            {"error": "Missing 'credential' field"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if device_name and len(device_name) > 100:
        device_name = device_name[:100]

    try:
        verify_registration_response(
            user=request.user,
            response=credential,
            device_name=device_name,
        )
    except WebAuthnError as exc:
        logger.warning("register/complete failed for user %s: %s", request.user.id, exc)
        error_msg = str(exc)
        if "expired" in error_msg.lower():
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        logger.exception("Unexpected error in register/complete for user %s", request.user.id)
        return Response(
            {"error": "Registration verification failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    token = create_auth_token(request.user)
    serializer = UserProfileSerializer(request.user)
    return Response(
        {"token": token.key, "user": serializer.data},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([AllowAny])
@rate_limit(max_requests=10, window=60)
def webauthn_authenticate_begin(request):
    """
    Issue a WebAuthn authentication challenge (no user identity required).

    Request body: {} (empty)

    Response:
        PublicKeyCredentialRequestOptions JSON (challenge base64url-encoded,
        allowCredentials=[]).

    Requirements: 5.1–5.4, 14.1, 14.3
    """
    try:
        options = generate_authentication_options()
        return Response(options, status=status.HTTP_200_OK)
    except Exception as exc:
        logger.exception("Unexpected error in authenticate/begin")
        return Response(
            {"error": "Authentication challenge generation failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def webauthn_authenticate_complete(request):
    """
    Verify a WebAuthn authentication assertion and issue a DRF token.

    Request body:
        { "credential": <AssertionResponse JSON from @simplewebauthn/browser> }

    Response:
        { "token": "<DRF token key>", "user": { ... } }

    Requirements: 6.1–6.7, 12.3, 12.5, 14.1
    """
    credential = request.data.get("credential")

    if not credential:
        return Response(
            {"error": "Missing 'credential' field"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user, _credential_record = verify_authentication_response(credential)
    except WebAuthnError as exc:
        logger.warning("authenticate/complete failed: %s", exc)
        error_msg = str(exc)
        # Map specific errors to appropriate HTTP status codes
        if any(
            phrase in error_msg.lower()
            for phrase in ("not found", "revoked", "sign count", "expired", "cloned")
        ):
            return Response({"error": error_msg}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"error": error_msg}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as exc:
        logger.exception("Unexpected error in authenticate/complete")
        return Response(
            {"error": "Authentication verification failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # verify_authentication_response already rotates the token internally;
    # fetch the freshly created token.
    token = create_auth_token(user)
    serializer = UserProfileSerializer(user)
    return Response(
        {"token": token.key, "user": serializer.data},
        status=status.HTTP_200_OK,
    )


# ---------------------------------------------------------------------------
# Bridge Token redemption
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([AllowAny])
def webauthn_bridge_redeem(request):
    """
    Redeem a Bridge Token sent from the Telegram bot.

    For a ``register`` flow:
        - Returns a temporary session token + user data so the frontend can
          call register/begin and register/complete while authenticated.

    For an ``authenticate`` flow:
        - Returns authentication options (PublicKeyCredentialRequestOptions)
          so the frontend can call authenticate/complete directly.

    Request body:
        { "bridge_token": "<token string>" }

    Response (register flow):
        {
            "flow": "register",
            "token": "<temporary DRF token>",
            "user": { ... }
        }

    Response (authenticate flow):
        {
            "flow": "authenticate",
            "options": <PublicKeyCredentialRequestOptions>
        }

    Requirements: 7.3, 7.4, 7.5, 7.6, 8.3, 13.1–13.5, 14.1
    """
    raw_token = request.data.get("bridge_token")

    if not raw_token:
        return Response(
            {"error": "Missing 'bridge_token' field"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user, flow = bridge_redeem(raw_token)
    except InvalidBridgeToken as exc:
        logger.warning("bridge/redeem failed: %s", exc)
        error_msg = str(exc)
        return Response({"error": error_msg}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as exc:
        logger.exception("Unexpected error in bridge/redeem")
        return Response(
            {"error": "Bridge token redemption failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    serializer = UserProfileSerializer(user)

    if flow == "register":
        # Issue a temporary token so the frontend can call register/begin
        # (which requires IsAuthenticated) without a full Telegram login.
        token = create_auth_token(user)
        return Response(
            {
                "flow": "register",
                "token": token.key,
                "user": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # flow == "authenticate"
    try:
        options = generate_authentication_options()
    except Exception as exc:
        logger.exception("Failed to generate auth options after bridge redeem for user %s", user.id)
        return Response(
            {"error": "Failed to generate authentication options"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {
            "flow": "authenticate",
            "options": options,
            "user": serializer.data,
        },
        status=status.HTTP_200_OK,
    )
