# Requirements Document

## Introduction

This feature introduces a unified authentication system that integrates the existing Telegram authentication with WebAuthn (Passkeys). The system handles two distinct entry points — the Telegram Bot and the Web Browser — and ensures that once a Passkey is established, it becomes the primary authentication method, eliminating redundant Telegram login prompts.

The backend is Django REST Framework with the existing `TelegramAuthentication` backend and `Token`-based sessions. The frontend is Next.js (TypeScript). The existing `User` model already has a `webauthn_credentials` JSON field and a `telegram_id` field, which form the foundation for this feature.

---

## Glossary

- **Auth_System**: The unified authentication system described in this document.
- **Telegram_Auth**: The existing Telegram Login Widget and bot-based identity verification mechanism.
- **WebAuthn_Service**: The backend service responsible for generating WebAuthn registration and authentication challenges and verifying WebAuthn responses.
- **Passkey**: A WebAuthn credential (public-key credential) registered to a user's device, stored as a record in the `WebAuthn_Credential` table.
- **Session_Manager**: The backend component responsible for issuing, validating, and revoking authentication tokens (currently DRF `Token`).
- **Registration_Flow**: The sequence of steps a user follows to create and verify a new Passkey.
- **Authentication_Flow**: The sequence of steps a user follows to prove identity using an existing Passkey.
- **Bot_Context**: An interaction originating from the Telegram bot (python-telegram-bot).
- **Web_Context**: An interaction originating from the Next.js web browser frontend.
- **Challenge**: A cryptographically random, single-use nonce issued by the `WebAuthn_Service` for a registration or authentication ceremony.
- **Credential_ID**: The unique identifier for a WebAuthn credential, returned by the authenticator during registration.
- **RP (Relying Party)**: The backend server acting as the WebAuthn relying party (identified by `rpId` and `rpName`).
- **Deep_Link**: A Telegram bot URL (`https://t.me/<bot>?start=<payload>`) that carries a signed token to bridge bot identity into the web browser.
- **Bridge_Token**: A short-lived, signed, single-use token embedded in a Deep_Link that proves Telegram identity to the Web_Context without re-running Telegram_Auth.
- **Pending_Registration**: A server-side record that holds an active Challenge and associates it with a user, valid for a limited time window.

---

## Requirements

### Requirement 1: WebAuthn Credential Storage

**User Story:** As a platform operator, I want WebAuthn credentials stored in a dedicated, normalized database table, so that each credential can be individually managed, revoked, and audited independently of other user data.

#### Acceptance Criteria

1. THE Auth_System SHALL store each WebAuthn credential in a dedicated `WebAuthn_Credential` table with the following fields: `id` (UUID primary key), `user` (foreign key to `User`), `credential_id` (bytes, unique, indexed), `public_key` (bytes), `sign_count` (integer), `device_name` (string, user-supplied, nullable), `aaguid` (UUID, nullable), `created_at` (datetime), `last_used_at` (datetime, nullable), and `is_active` (boolean, default true).
2. THE Auth_System SHALL enforce a unique constraint on `credential_id` across all users.
3. THE Auth_System SHALL allow one `User` to have multiple `WebAuthn_Credential` records (one per registered device).
4. WHEN a `WebAuthn_Credential` record is created, THE Auth_System SHALL set `sign_count` to the value returned by the authenticator during registration.
5. THE Auth_System SHALL NOT store the WebAuthn private key; only the public key and credential metadata SHALL be persisted.

---

### Requirement 2: WebAuthn Relying Party Configuration

**User Story:** As a platform operator, I want the WebAuthn relying party parameters to be centrally configured, so that all registration and authentication ceremonies use consistent, environment-specific settings.

#### Acceptance Criteria

1. THE Auth_System SHALL read the WebAuthn `rpId` from the `WEBAUTHN_RP_ID` environment variable.
2. THE Auth_System SHALL read the WebAuthn `rpName` from the `WEBAUTHN_RP_NAME` environment variable.
3. THE Auth_System SHALL read the allowed WebAuthn origin(s) from the `WEBAUTHN_ALLOWED_ORIGINS` environment variable (comma-separated list).
4. IF the `WEBAUTHN_RP_ID` environment variable is not set at application startup, THEN THE Auth_System SHALL raise a configuration error and prevent the application from starting.
5. THE Auth_System SHALL use `ES256` (COSE algorithm -7) and `RS256` (COSE algorithm -257) as the supported public key credential algorithms.

---

### Requirement 3: Passkey Registration — Challenge Issuance

**User Story:** As a user, I want the server to give me a unique challenge before I register a Passkey, so that my registration ceremony is cryptographically bound to this specific server request.

#### Acceptance Criteria

1. WHEN an authenticated user requests Passkey registration, THE WebAuthn_Service SHALL generate a cryptographically random Challenge of at least 32 bytes.
2. THE WebAuthn_Service SHALL store the Challenge server-side as a `Pending_Registration` record associated with the authenticated user, with a `created_at` timestamp.
3. THE WebAuthn_Service SHALL set the `Pending_Registration` expiry to 5 minutes from `created_at`.
4. THE WebAuthn_Service SHALL return a `PublicKeyCredentialCreationOptions` JSON object to the client, including: `challenge` (base64url-encoded), `rp` (id and name), `user` (id as base64url of user UUID, name, displayName), `pubKeyCredParams` (ES256 and RS256), `timeout` (300000 ms), `attestation` ("none"), and `authenticatorSelection` (residentKey: "preferred", userVerification: "preferred").
5. IF a `Pending_Registration` already exists for the user and has not expired, THEN THE WebAuthn_Service SHALL invalidate the previous `Pending_Registration` and issue a new one.

---

### Requirement 4: Passkey Registration — Verification and Storage

**User Story:** As a user, I want the server to verify my authenticator's response and save my Passkey, so that I can use it for future logins.

#### Acceptance Criteria

1. WHEN a client submits a registration response, THE WebAuthn_Service SHALL retrieve the matching `Pending_Registration` by user identity.
2. IF the `Pending_Registration` has expired (older than 5 minutes), THEN THE WebAuthn_Service SHALL reject the registration with an error indicating the challenge has expired.
3. THE WebAuthn_Service SHALL verify the registration response against the stored Challenge using the `py_webauthn` library, validating: origin, rpId, challenge match, attestation format, and client data type ("webauthn.create").
4. IF verification succeeds, THEN THE WebAuthn_Service SHALL create a `WebAuthn_Credential` record with the verified `credential_id`, `public_key`, `sign_count`, and `aaguid`.
5. IF verification succeeds, THEN THE WebAuthn_Service SHALL delete the consumed `Pending_Registration` record.
6. IF verification fails for any reason, THEN THE WebAuthn_Service SHALL return a 400 error with a descriptive message and SHALL NOT create a `WebAuthn_Credential` record.
7. THE WebAuthn_Service SHALL accept an optional `device_name` string (maximum 100 characters) submitted alongside the registration response and store it in the `WebAuthn_Credential` record.

---

### Requirement 5: Passkey Authentication — Challenge Issuance

**User Story:** As a returning user, I want the server to give me a challenge before I authenticate with my Passkey, so that my authentication ceremony is replay-attack resistant.

#### Acceptance Criteria

1. WHEN a client requests a Passkey authentication challenge, THE WebAuthn_Service SHALL generate a cryptographically random Challenge of at least 32 bytes.
2. THE WebAuthn_Service SHALL store the Challenge server-side with a `created_at` timestamp and a 5-minute expiry.
3. THE WebAuthn_Service SHALL return a `PublicKeyCredentialRequestOptions` JSON object including: `challenge` (base64url-encoded), `timeout` (300000 ms), `rpId`, `userVerification` ("preferred"), and `allowCredentials` (empty list, to support discoverable credentials / resident keys).
4. THE WebAuthn_Service SHALL NOT require the client to supply a username or user identifier at the challenge-request stage.

---

### Requirement 6: Passkey Authentication — Verification and Token Issuance

**User Story:** As a returning user, I want the server to verify my Passkey assertion and issue me an auth token, so that I am logged in without needing Telegram.

#### Acceptance Criteria

1. WHEN a client submits an authentication assertion, THE WebAuthn_Service SHALL look up the `WebAuthn_Credential` record by the `credential_id` contained in the assertion.
2. IF no matching `WebAuthn_Credential` record exists, THEN THE WebAuthn_Service SHALL return a 401 error.
3. THE WebAuthn_Service SHALL verify the assertion using the `py_webauthn` library, validating: origin, rpId, challenge match, signature against the stored public key, and client data type ("webauthn.get").
4. IF the authenticator-reported `sign_count` is greater than zero AND is less than or equal to the stored `sign_count`, THEN THE WebAuthn_Service SHALL reject the authentication with a 401 error indicating a possible cloned authenticator.
5. IF verification succeeds, THEN THE WebAuthn_Service SHALL update the `WebAuthn_Credential` record's `sign_count` and `last_used_at` fields.
6. IF verification succeeds, THEN THE Session_Manager SHALL issue a DRF `Token` for the associated `User` and return it in the response.
7. IF the `Pending_Authentication` challenge has expired (older than 5 minutes), THEN THE WebAuthn_Service SHALL reject the authentication with a 401 error.

---

### Requirement 7: Telegram Bot Flow — First-Time Registration

**User Story:** As a new user interacting with the Telegram bot, I want to be guided through Passkey setup immediately after my account is created, so that I can use a Passkey for future web logins without re-authenticating via Telegram.

#### Acceptance Criteria

1. WHEN a user sends `/start` to the Telegram bot and the user has zero active `WebAuthn_Credential` records, THE Auth_System SHALL present a "Set Up Passkey" button in the bot response.
2. WHEN the user taps "Set Up Passkey", THE Auth_System SHALL generate a `Bridge_Token` signed with `HMAC-SHA256` using `SECRET_KEY`, containing the user's `telegram_id` and an expiry timestamp of 10 minutes from generation.
3. THE Auth_System SHALL construct a Deep_Link URL in the format `{FRONTEND_URL}/auth/passkey-setup?bridge_token={Bridge_Token}` and present it to the user as a button labeled "Open Passkey Setup".
4. WHEN the user opens the Deep_Link in a browser, THE Auth_System SHALL validate the `Bridge_Token` signature and expiry before proceeding with the Registration_Flow.
5. IF the `Bridge_Token` is invalid or expired, THEN THE Auth_System SHALL redirect the user to the login page with an error message.
6. WHEN the Registration_Flow completes successfully via the Deep_Link, THE Auth_System SHALL issue a DRF `Token` for the user's session in the browser.

---

### Requirement 8: Telegram Bot Flow — Returning User Session

**User Story:** As a returning user who has already set up a Passkey, I want the Telegram bot to not prompt me for Telegram login again, so that my experience is seamless.

#### Acceptance Criteria

1. WHEN a user sends `/start` to the Telegram bot and the user has at least one active `WebAuthn_Credential` record, THE Auth_System SHALL NOT display the "Set Up Passkey" button.
2. WHEN a user sends `/start` to the Telegram bot and the user has at least one active `WebAuthn_Credential` record, THE Auth_System SHALL display a "Open Web App" button that links directly to the authenticated web application without requiring a new Telegram login.
3. THE Auth_System SHALL generate a `Bridge_Token` for the "Open Web App" link that, upon redemption in the browser, initiates the Passkey Authentication_Flow rather than the Registration_Flow.
4. WHILE a user's browser session token is valid, THE Auth_System SHALL accept API requests authenticated with that token without requiring re-authentication via Telegram_Auth.

---

### Requirement 9: Web Browser Flow — First-Time Login

**User Story:** As a new user on the web interface, I want to log in with the Telegram Login Widget and then be guided to set up a Passkey, so that future logins on this browser use the Passkey instead.

#### Acceptance Criteria

1. WHEN a user completes the Telegram Login Widget flow on the web interface, THE Auth_System SHALL verify the Telegram auth data hash using the existing `TelegramAuthentication` backend.
2. IF the Telegram auth data hash is invalid, THEN THE Auth_System SHALL return a 401 error and SHALL NOT create or update any user record.
3. WHEN Telegram authentication succeeds and the user has zero active `WebAuthn_Credential` records, THE Auth_System SHALL return a response with `passkey_setup_required: true` alongside the user data and a temporary session token.
4. WHEN the frontend receives `passkey_setup_required: true`, THE Auth_System's frontend component SHALL redirect the user to `/auth/passkey-setup`.
5. WHEN the Registration_Flow completes successfully, THE Auth_System SHALL update the session to reflect full authentication and redirect the user to the application dashboard.

---

### Requirement 10: Web Browser Flow — Returning Login

**User Story:** As a returning user on the web interface who has a registered Passkey, I want to authenticate using my Passkey directly, so that I do not need to use the Telegram Login Widget again.

#### Acceptance Criteria

1. WHEN a returning user visits the web login page and the browser has a previously issued valid session token, THE Auth_System SHALL automatically redirect the user to the dashboard without displaying the login form.
2. WHEN a returning user visits the web login page without a valid session token, THE Auth_System SHALL display a "Sign in with Passkey" button as the primary authentication option.
3. WHEN the user activates the "Sign in with Passkey" button, THE Auth_System SHALL initiate the Authentication_Flow (Requirement 5 and 6).
4. IF the Passkey authentication fails, THEN THE Auth_System SHALL display an error message and offer the Telegram Login Widget as a fallback authentication method.
5. THE Auth_System SHALL also display the Telegram Login Widget as a secondary option on the login page for users who do not have a Passkey registered on the current device.

---

### Requirement 11: Credential Management

**User Story:** As an authenticated user, I want to view, name, and revoke my registered Passkeys, so that I can maintain control over which devices can access my account.

#### Acceptance Criteria

1. WHEN an authenticated user requests their credential list, THE Auth_System SHALL return all `WebAuthn_Credential` records associated with that user, including: `id`, `device_name`, `aaguid`, `created_at`, `last_used_at`, and `is_active`.
2. WHEN an authenticated user submits a rename request for a credential, THE Auth_System SHALL update the `device_name` field of the specified `WebAuthn_Credential` record if the credential belongs to that user.
3. IF the credential does not belong to the requesting user, THEN THE Auth_System SHALL return a 403 error.
4. WHEN an authenticated user requests revocation of a credential, THE Auth_System SHALL set `is_active` to false on the specified `WebAuthn_Credential` record.
5. THE Auth_System SHALL NOT allow a user to revoke their last active `WebAuthn_Credential` if it would leave the account with no active credentials and no other authentication method available.
6. WHEN a revoked credential (`is_active = false`) is presented during an Authentication_Flow, THE WebAuthn_Service SHALL reject it with a 401 error.

---

### Requirement 12: Session Token Lifecycle

**User Story:** As a platform operator, I want session tokens to have a defined expiry and rotation policy, so that compromised tokens have a limited blast radius.

#### Acceptance Criteria

1. THE Session_Manager SHALL set a maximum lifetime of 30 days on all issued DRF `Token` records.
2. WHEN a token older than 30 days is presented, THE Session_Manager SHALL reject the request with a 401 error and invalidate the token.
3. WHEN a user successfully authenticates via Passkey, THE Session_Manager SHALL invalidate any previously issued token for that user and issue a new one.
4. WHEN a user logs out, THE Session_Manager SHALL immediately invalidate the current token.
5. THE Auth_System SHALL record a `LOGIN` audit log entry (using the existing `AuditLog` model) for every successful Passkey authentication, including the `credential_id` in the `details` JSON field.

---

### Requirement 13: Bridge Token Security

**User Story:** As a platform operator, I want Bridge Tokens to be cryptographically signed and single-use, so that they cannot be replayed or forged to gain unauthorized access.

#### Acceptance Criteria

1. THE Auth_System SHALL sign each `Bridge_Token` using `HMAC-SHA256` with the Django `SECRET_KEY`.
2. THE Auth_System SHALL embed the `telegram_id`, `user_id`, `issued_at` (Unix timestamp), and `expires_at` (Unix timestamp) in the `Bridge_Token` payload.
3. WHEN a `Bridge_Token` is redeemed, THE Auth_System SHALL mark it as consumed in a server-side store (Redis or database) and SHALL reject any subsequent redemption of the same token with a 401 error.
4. THE Auth_System SHALL reject `Bridge_Token` redemption if the current time is past `expires_at`.
5. THE Auth_System SHALL reject `Bridge_Token` redemption if the HMAC signature does not match.

---

### Requirement 14: API Endpoint Surface

**User Story:** As a frontend developer, I want a well-defined set of REST endpoints for the WebAuthn flows, so that I can implement the frontend without ambiguity.

#### Acceptance Criteria

1. THE Auth_System SHALL expose the following endpoints under `/api/v1/users/auth/`:
   - `POST /webauthn/register/begin/` — issues a registration Challenge (Requirement 3)
   - `POST /webauthn/register/complete/` — verifies registration response (Requirement 4)
   - `POST /webauthn/authenticate/begin/` — issues an authentication Challenge (Requirement 5)
   - `POST /webauthn/authenticate/complete/` — verifies authentication assertion (Requirement 6)
   - `POST /webauthn/bridge/redeem/` — redeems a Bridge_Token (Requirements 7, 8, 13)
2. THE Auth_System SHALL expose the following endpoints under `/api/v1/users/` (authenticated):
   - `GET /credentials/` — list credentials (Requirement 11.1)
   - `PATCH /credentials/{id}/` — rename a credential (Requirement 11.2)
   - `DELETE /credentials/{id}/` — revoke a credential (Requirement 11.4)
3. THE Auth_System SHALL apply the existing rate limiting middleware to all WebAuthn endpoints, with a limit of 10 requests per minute per user or IP for challenge endpoints.

---

### Requirement 15: Round-Trip Serialization of WebAuthn Data

**User Story:** As a developer, I want WebAuthn binary data (challenges, credential IDs, public keys) to be consistently serialized and deserialized, so that data is not corrupted between the client and server.

#### Acceptance Criteria

1. THE Auth_System SHALL encode all binary WebAuthn fields (challenge, credential_id, public_key, user_id) as base64url strings when transmitting to or from the client.
2. THE Auth_System SHALL decode base64url strings back to bytes before passing them to the `py_webauthn` library for verification.
3. FOR ALL valid base64url-encoded WebAuthn binary values, encoding then decoding SHALL produce the original byte sequence (round-trip property).
4. IF a client submits a malformed base64url value, THEN THE Auth_System SHALL return a 400 error with a descriptive message.
