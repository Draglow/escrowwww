# Implementation Plan: Unified Authentication with Passkeys

## Overview

Integrate WebAuthn (Passkeys) into the existing Telegram-based authentication system. The backend is Django REST Framework (Python); the frontend is Next.js (TypeScript). Implementation proceeds in layers: data model → backend services → API endpoints → bot update → frontend flows → credential management UI.

## Tasks

- [x] 1. Backend: Add `WebAuthnCredential` model and database migration
  - Create `WebAuthnCredential` model in `backend/apps/users/models.py` with fields: `id` (UUID PK), `user` (FK → User, CASCADE), `credential_id` (BinaryField, unique, indexed), `public_key` (BinaryField), `sign_count` (PositiveIntegerField, default=0), `device_name` (CharField max_length=100, nullable), `aaguid` (UUIDField, nullable), `created_at` (auto_now_add), `last_used_at` (nullable), `is_active` (BooleanField, default=True)
  - Keep the existing `webauthn_credentials` JSONField on `User` in place (deprecated, not removed) for migration compatibility
  - Generate and apply Django migration for the new table
  - Register `WebAuthnCredential` in `backend/apps/users/admin.py`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Backend: Add `py_webauthn` dependency and WebAuthn settings
  - Add `webauthn==2.1.0` (py_webauthn) to `backend/requirements.txt`
  - Add `WEBAUTHN_RP_ID`, `WEBAUTHN_RP_NAME`, and `WEBAUTHN_ALLOWED_ORIGINS` to `backend/config/settings.py`, reading from environment variables via `django-environ`
  - Raise `django.core.exceptions.ImproperlyConfigured` at startup if `WEBAUTHN_RP_ID` is not set
  - Add example values to `backend/.env.example`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Backend: Implement `WebAuthnService` with challenge generation and base64url utilities
  - Create `backend/apps/users/webauthn_service.py`
  - Implement `base64url_encode(data: bytes) -> str` and `base64url_decode(s: str) -> bytes` helpers (no padding, URL-safe alphabet)
  - Implement `generate_challenge() -> bytes` — `os.urandom(32)` minimum
  - Implement `generate_registration_options(user) -> dict` — stores `Pending_Registration` in Django cache under key `webauthn:pending_reg:{user.id}` with 300-second TTL; returns `PublicKeyCredentialCreationOptions` dict with all required fields (challenge base64url-encoded, rp, user, pubKeyCredParams ES256 + RS256, timeout 300000, attestation "none", authenticatorSelection)
  - Implement `verify_registration_response(user, response: dict, device_name: str | None) -> WebAuthnCredential` — retrieves and deletes `Pending_Registration` from cache, calls `py_webauthn.verify_registration_response()`, creates and returns `WebAuthnCredential`
  - Implement `generate_authentication_options() -> dict` — stores `Pending_Authentication` in cache under key `webauthn:pending_auth:{challenge_b64}` with 300-second TTL; returns `PublicKeyCredentialRequestOptions` with empty `allowCredentials`
  - Implement `verify_authentication_response(response: dict) -> tuple[User, WebAuthnCredential]` — retrieves and deletes `Pending_Authentication`, looks up `WebAuthnCredential` by `credential_id`, calls `py_webauthn.verify_authentication_response()`, enforces sign-count anti-cloning check, updates `sign_count` and `last_used_at`, rotates DRF Token, writes `AuditLog`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 12.3, 12.5, 15.1, 15.2, 15.4_

  - [ ]* 3.1 Write property test: base64url round-trip (Property 1)
    - **Property 1: Base64url Round-Trip** — `@given(st.binary(min_size=0, max_size=1024))` — `assert base64url_decode(base64url_encode(data)) == data`
    - **Validates: Requirements 15.3**

  - [ ]* 3.2 Write property test: challenge uniqueness and minimum length (Property 2)
    - **Property 2: Challenge Uniqueness and Minimum Length** — `@given(st.integers(min_value=2, max_value=10))` — generate N challenges, assert all `len >= 32` and all distinct
    - **Validates: Requirements 3.1, 5.1**

  - [ ]* 3.3 Write property test: registration options structure (Property 4)
    - **Property 4: Registration Options Structure** — for any authenticated user, assert returned dict contains all required keys with correct types/values
    - **Validates: Requirements 3.4**

  - [ ]* 3.4 Write property test: authentication options structure (Property 5)
    - **Property 5: Authentication Options Structure** — assert returned dict contains `challenge`, `timeout`, `rpId`, `userVerification`, `allowCredentials` (empty list)
    - **Validates: Requirements 5.3**

- [x] 4. Backend: Implement `BridgeTokenService`
  - Create `backend/apps/users/bridge_token.py`
  - Implement `generate(user, flow: Literal['register', 'authenticate']) -> str` — builds JSON payload `{telegram_id, user_id, flow, issued_at, expires_at}`, signs with `HMAC-SHA256(SECRET_KEY, base64url(json))`, returns `base64url(json) + "." + base64url(signature)`
  - Implement `redeem(token: str) -> tuple[User, str]` — splits token, verifies HMAC signature, checks `expires_at`, checks Redis key `webauthn:bridge_used:{sha256(token)}` for replay, marks token consumed (TTL = `expires_at - now`), returns `(user, flow)`
  - Raise `InvalidBridgeToken` (custom exception) on any failure
  - _Requirements: 7.2, 7.4, 7.5, 8.3, 13.1, 13.2, 13.3, 13.4, 13.5_

  - [ ]* 4.1 Write property test: bridge token integrity (Property 11)
    - **Property 11: Bridge Token Integrity** — `@given(st.binary(min_size=1, max_size=100))` — generate valid token, tamper any byte, assert `redeem()` raises `InvalidBridgeToken`
    - **Validates: Requirements 13.1, 13.5**

  - [ ]* 4.2 Write property test: bridge token single-use (Property 12)
    - **Property 12: Bridge Token Single-Use** — generate and redeem a valid token once (succeeds), redeem same token again, assert raises `InvalidBridgeToken`
    - **Validates: Requirements 13.3**

- [x] 5. Backend: Create WebAuthn API views and wire up URLs
  - Create `backend/apps/users/views_webauthn.py` with the following function-based views:
    - `webauthn_register_begin` (`POST`, `IsAuthenticated`) — calls `WebAuthnService.generate_registration_options()`
    - `webauthn_register_complete` (`POST`, `IsAuthenticated`) — calls `WebAuthnService.verify_registration_response()`; returns `{token, user}`
    - `webauthn_authenticate_begin` (`POST`, `AllowAny`) — calls `WebAuthnService.generate_authentication_options()`
    - `webauthn_authenticate_complete` (`POST`, `AllowAny`) — calls `WebAuthnService.verify_authentication_response()`; returns `{token, user}`
    - `webauthn_bridge_redeem` (`POST`, `AllowAny`) — calls `BridgeTokenService.redeem()`; for `register` flow returns temporary token + user; for `authenticate` flow returns authentication options
  - Update `backend/apps/users/urls.py` to add the five new paths under `auth/webauthn/`
  - Apply the existing `rate_limit` decorator (10 req/min) to `webauthn_register_begin` and `webauthn_authenticate_begin`
  - _Requirements: 14.1, 14.3_

- [x] 6. Backend: Add credential management actions to `UserViewSet`
  - Add `WebAuthnCredentialSerializer` to `backend/apps/users/serializers.py` exposing: `id`, `device_name`, `aaguid`, `created_at`, `last_used_at`, `is_active`
  - Add three new `@action` methods to `UserViewSet` in `backend/apps/users/views.py`:
    - `list_credentials` (`GET /credentials/`, `IsAuthenticated`) — returns all `WebAuthnCredential` records for `request.user`
    - `rename_credential` (`PATCH /credentials/{id}/`, `IsAuthenticated`) — updates `device_name`; returns 403 if credential belongs to another user
    - `revoke_credential` (`DELETE /credentials/{id}/`, `IsAuthenticated`) — sets `is_active = False`; returns 400 if it is the user's last active credential
  - Register the new URL patterns in `backend/apps/users/urls.py`
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 14.2_

  - [ ]* 6.1 Write property test: credential ownership isolation (Property 8)
    - **Property 8: Credential Ownership Isolation** — for any two distinct users A and B, user B's rename/revoke request on A's credential returns 403
    - **Validates: Requirements 11.3**

  - [ ]* 6.2 Write property test: last credential protection (Property 9)
    - **Property 9: Last Credential Protection** — for any user with exactly one active credential, revoke request returns error and credential remains active
    - **Validates: Requirements 11.5**

  - [ ]* 6.3 Write property test: credential list completeness (Property 16)
    - **Property 16: Credential List Completeness** — for any user with N active credentials, `GET /credentials/` returns exactly N records each with required fields
    - **Validates: Requirements 11.1**

- [x] 7. Backend: Update `telegram_login` view and `AuditLog` for passkey flows
  - In `backend/apps/users/views.py`, update `telegram_login` to check `request.user.webauthn_credentials_set.filter(is_active=True).exists()` after successful Telegram auth; if zero active credentials, include `passkey_setup_required: true` in the response
  - Add `'PASSKEY_LOGIN'` and `'PASSKEY_REGISTERED'` to `AuditLog.ACTION_CHOICES` in `backend/apps/users/audit.py`
  - Ensure `verify_authentication_response` in `WebAuthnService` writes an `AuditLog` entry with `action='PASSKEY_LOGIN'` and `details={'credential_id': <hex>}`
  - _Requirements: 9.1, 9.2, 9.3, 12.5_

  - [ ]* 7.1 Write property test: passkey setup required flag (Property 15)
    - **Property 15: Passkey Setup Required Flag** — for any user with zero active credentials, successful Telegram login response includes `passkey_setup_required: true`
    - **Validates: Requirements 9.3**

  - [ ]* 7.2 Write property test: audit log on passkey authentication (Property 17)
    - **Property 17: Audit Log on Passkey Authentication** — after any successful passkey authentication, an `AuditLog` record exists with `action='PASSKEY_LOGIN'`, correct `user`, and `credential_id` in `details`
    - **Validates: Requirements 12.5**

- [x] 8. Backend: Update Telegram bot `/start` handler for Bridge Token flow
  - In `backend/apps/telegram_bot/bot.py`, update `start_command` to:
    - Query `WebAuthnCredential.objects.filter(user=user, is_active=True).exists()` (via `sync_to_async`)
    - If no active credentials: show "🔑 Set Up Passkey" button with Deep Link `{FRONTEND_URL}/auth/passkey-setup?bridge_token={token}` (flow=`register`)
    - If active credentials exist: show "🌐 Open Web App" button with Deep Link `{FRONTEND_URL}/auth/passkey-login?bridge_token={token}` (flow=`authenticate`) instead of the current plain login URL
  - Add `get_active_credential_count` helper (sync_to_async) to `EscrowBot`
  - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_

- [x] 9. Backend: Implement `Session_Manager` token expiry enforcement
  - Update `backend/apps/users/authentication.py` (TokenAuthentication) or `backend/apps/users/tokens.py` to reject tokens older than 30 days with a 401 response and delete the expired token
  - Ensure `revoke_auth_token` is called before `create_auth_token` in the passkey authentication path (token rotation)
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [ ]* 9.1 Write property test: token rotation on passkey login (Property 13)
    - **Property 13: Token Rotation on Passkey Login** — after successful passkey authentication, old token T1 is rejected (401) and new token T2 is returned and accepted
    - **Validates: Requirements 12.3**

  - [ ]* 9.2 Write property test: token invalidation on logout (Property 14)
    - **Property 14: Token Invalidation on Logout** — after logout, the previously valid token returns 401 on any authenticated endpoint
    - **Validates: Requirements 12.4**

- [x] 10. Backend: Write unit tests for backend services
  - Create `backend/apps/users/tests_webauthn.py` with pytest-django tests covering:
    - `WebAuthnCredential` model constraints (unique `credential_id`, FK cascade)
    - `BridgeTokenService.generate()` and `redeem()` with valid, expired, and tampered tokens
    - `WebAuthnService.generate_registration_options()` — challenge length ≥ 32, correct structure
    - `WebAuthnService.generate_authentication_options()` — empty `allowCredentials`
    - `telegram_login` returning `passkey_setup_required: true` for users with no credentials
    - Credential rename/revoke views: ownership check (403), last-credential protection (400)
    - Token rotation: old token invalid after passkey login
    - Rate limiting: 11th request to challenge endpoint returns 429
    - `ImproperlyConfigured` raised when `WEBAUTHN_RP_ID` is missing
  - Use `factory_boy` factories for `User` and `WebAuthnCredential`
  - _Requirements: 1.2, 3.1, 5.1, 6.4, 9.3, 11.3, 11.5, 12.2, 12.3, 14.3_

- [x] 11. Checkpoint — backend complete
  - Ensure all backend tests pass: `pytest backend/apps/users/tests_webauthn.py -v`
  - Ensure existing test suite still passes: `pytest backend/ -v`
  - Ask the user if any questions arise before proceeding to the frontend.

- [x] 12. Frontend: Install `@simplewebauthn/browser` and create `lib/webauthn.ts`
  - Add `@simplewebauthn/browser@^10.0.0` to `frontend/package.json` dependencies
  - Create `frontend/src/lib/webauthn.ts`:
    - Export `isWebAuthnSupported(): boolean` — checks `!!window.PublicKeyCredential`
    - Export `startPasskeyRegistration(options: PublicKeyCredentialCreationOptionsJSON): Promise<RegistrationResponseJSON>` — wraps `startRegistration()` from `@simplewebauthn/browser`
    - Export `startPasskeyAuthentication(options: PublicKeyCredentialRequestOptionsJSON): Promise<AuthenticationResponseJSON>` — wraps `startAuthentication()` from `@simplewebauthn/browser`
  - _Requirements: 15.1, 15.2_

- [x] 13. Frontend: Update `store/auth.ts` for passkey state
  - Add `passkeySetupRequired: boolean` field to `AuthState`
  - Add `setPasskeySetupRequired(value: boolean)` action
  - Add `available_balance` and `photo_url` to the `User` interface to match `UserProfileSerializer`
  - _Requirements: 9.3, 9.4_

- [x] 14. Frontend: Update login page (`app/login/page.tsx`) for passkey-first flow
  - Add "Sign in with Passkey" button as the primary CTA (above the Telegram widget); hide it when `!isWebAuthnSupported()`
  - When "Sign in with Passkey" is clicked: call `POST /api/v1/users/auth/webauthn/authenticate/begin/`, pass options to `startPasskeyAuthentication()`, call `POST /api/v1/users/auth/webauthn/authenticate/complete/`, store token via `setAuth()`, redirect to `/dashboard`
  - On passkey authentication failure: show toast error and reveal the Telegram Login Widget as fallback
  - After Telegram login: if response contains `passkey_setup_required: true`, call `setPasskeySetupRequired(true)` and redirect to `/auth/passkey-setup` (store temporary token in `sessionStorage`, not `localStorage`)
  - If a valid session token already exists in the store, redirect immediately to `/dashboard` without showing the login form
  - Keep the Telegram Login Widget and dev-login button as secondary options
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 9.4_

- [x] 15. Frontend: Create passkey setup page (`app/auth/passkey-setup/page.tsx`)
  - Create `frontend/src/app/auth/passkey-setup/page.tsx`
  - On mount: read `bridge_token` from URL query params (if present) and call `POST /api/v1/users/auth/webauthn/bridge/redeem/`; on error redirect to `/login?error=bridge_token_invalid`
  - After bridge redemption (or if arriving with a session token from Telegram login): call `POST /api/v1/users/auth/webauthn/register/begin/`, pass options to `startPasskeyRegistration()`, call `POST /api/v1/users/auth/webauthn/register/complete/` with optional `device_name`
  - On success: call `setAuth()` with the returned token, clear `sessionStorage`, redirect to `/dashboard`
  - On WebAuthn API error (user cancel, no authenticator): show toast and offer a "Skip for now" link back to `/dashboard` (if a session token exists)
  - _Requirements: 7.3, 7.4, 7.5, 7.6, 9.4, 9.5_

- [x] 16. Frontend: Create passkey login page (`app/auth/passkey-login/page.tsx`)
  - Create `frontend/src/app/auth/passkey-login/page.tsx` to handle Bridge Token deep links for returning users (flow=`authenticate`)
  - On mount: read `bridge_token` from URL, call `POST /api/v1/users/auth/webauthn/bridge/redeem/`; the response returns authentication options
  - Pass options to `startPasskeyAuthentication()`, call `POST /api/v1/users/auth/webauthn/authenticate/complete/`, store token, redirect to `/dashboard`
  - On any error: redirect to `/login?error=bridge_token_invalid`
  - _Requirements: 8.3_

- [x] 17. Frontend: Create `components/auth/PasskeyButton.tsx`
  - Reusable button component that accepts `onSuccess: (token: string) => void` and `onError: (err: Error) => void` props
  - Internally runs the full authenticate begin → `startPasskeyAuthentication` → authenticate complete flow
  - Shows loading spinner during ceremony; shows error message on failure
  - Hidden (returns `null`) when `!isWebAuthnSupported()`
  - _Requirements: 10.2, 10.3_

- [x] 18. Frontend: Create `components/auth/CredentialManager.tsx` and integrate into profile settings
  - Create `frontend/src/components/auth/CredentialManager.tsx`:
    - Fetches `GET /api/v1/users/credentials/` on mount using the auth token
    - Renders a list of credentials showing `device_name` (or "Unnamed device"), `created_at`, `last_used_at`, `is_active`
    - Inline rename: click pencil icon → editable input → `PATCH /api/v1/users/credentials/{id}/`
    - Revoke button: `DELETE /api/v1/users/credentials/{id}/`; disabled and shows tooltip if it is the last active credential
    - Shows toast on success/error for each operation
  - Import and render `<CredentialManager />` inside `frontend/src/components/profile/profile-settings.tsx` in a new "Passkeys" card section
  - _Requirements: 11.1, 11.2, 11.4, 11.5_

- [x] 19. Frontend: Add environment variables and update API client
  - Add `NEXT_PUBLIC_WEBAUTHN_RP_ID` to `frontend/.env.local.example`
  - Ensure all new API calls use the existing `NEXT_PUBLIC_API_URL` base URL and include the `Authorization: Token <token>` header where required (authenticated endpoints)
  - _Requirements: 2.1_

- [x] 20. Checkpoint — full integration
  - Verify the frontend builds without TypeScript errors: `npm run build` (run manually in `frontend/`)
  - Verify all backend tests pass: `pytest backend/ -v`
  - Ask the user if any questions arise before marking the feature complete.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Property tests use **Hypothesis** (`hypothesis`, `hypothesis[django]`) — add to `backend/requirements.txt` if not already present
- The existing `webauthn_credentials` JSONField on `User` is kept but not written to by new code; it can be removed in a follow-up migration once the feature is stable
- All binary WebAuthn fields are transmitted as base64url strings; the `py_webauthn` library handles CBOR/COSE internally
- Bridge Token expiry is 10 minutes; challenge expiry is 5 minutes — both enforced server-side via Redis TTL and explicit timestamp checks
- The `ConsumedBridgeToken` Redis key uses `sha256(raw_token)` as the key suffix to avoid storing the raw token in Redis
