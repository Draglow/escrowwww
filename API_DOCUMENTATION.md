# Crypto Escrow Platform - API Documentation

## Base URL
```
http://localhost:8000/api/v1/
```

## Authentication

### Token-Based Authentication
All endpoints require authentication using tokens obtained via Telegram Login.

Headers:
```
Authorization: Token <token>
```

### Telegram Login
```http
POST /api/v1/users/auth/login/
```

**Headers:**
```
Authorization: Telegram id=123456&first_name=John&username=johndoe&auth_date=1234567890&hash=abc123...
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "telegram_id": 123456,
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "balance": "0.000000",
    "is_2fa_enabled": false,
    "is_verified": false,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "token": "abc123token456def789"
}
```

### Logout
```http
POST /api/v1/users/auth/logout/
```

**Headers:**
```
Authorization: Token <token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

---

## User Endpoints

### Get Current User Profile
```http
GET /api/v1/users/me/
```

**Response:**
```json
{
  "id": "uuid",
  "telegram_id": 123456,
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "balance": "100.500000",
  "available_balance": "50.250000",
  "is_2fa_enabled": true,
  "is_verified": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Update Profile
```http
PATCH /api/v1/users/update_profile/
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:** Same as profile response

---

## Two-Factor Authentication (2FA)

### Enable 2FA
```http
POST /api/v1/users/enable_2fa/
```

**Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KG...",
  "backup_codes": [
    "ABCD1234",
    "EFGH5678",
    "IJKL9012",
    "MNOP3456",
    "QRST7890",
    "UVWX1234",
    "YZAB5678",
    "CDEF9012",
    "GHIJ3456",
    "KLMN7890"
  ],
  "message": "Scan the QR code with your authenticator app and verify with a code"
}
```

### Verify 2FA Setup
```http
POST /api/v1/users/verify_2fa_setup/
```

**Request Body:**
```json
{
  "token": "123456"
}
```

**Response:**
```json
{
  "message": "2FA enabled successfully",
  "backup_codes": ["ABCD1234", "EFGH5678", ...]
}
```

### Disable 2FA
```http
POST /api/v1/users/disable_2fa/
```

**Request Body:**
```json
{
  "token": "123456"
}
```

**Response:**
```json
{
  "message": "2FA disabled successfully"
}
```

### Verify 2FA Token
```http
POST /api/v1/users/verify_2fa/
```

**Request Body:**
```json
{
  "token": "123456"
}
```

**Response:**
```json
{
  "message": "Token verified successfully"
}
```

**Error Response (Rate Limited):**
```json
{
  "error": "Invalid token",
  "remaining_attempts": 3
}
```

### Get Audit Logs
```http
GET /api/v1/users/audit_logs/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "action": "LOGIN",
    "ip_address": "192.168.1.1",
    "success": true,
    "created_at": "2024-01-01T10:30:00Z",
    "details": {}
  },
  {
    "id": "uuid",
    "action": "WITHDRAWAL",
    "ip_address": "192.168.1.1",
    "success": true,
    "created_at": "2024-01-01T10:35:00Z",
    "details": {
      "amount": "100.50",
      "to_address": "TXYZabc123..."
    }
  },
  {
    "id": "uuid",
    "action": "2FA_ENABLED",
    "ip_address": "192.168.1.1",
    "success": true,
    "created_at": "2024-01-01T10:40:00Z",
    "details": {}
  }
]
```

---

## Wallet Endpoints

### Get My Wallet
```http
GET /api/v1/wallets/my_wallet/
```

**Response:**
```json
{
  "id": "uuid",
  "address": "TRC20_ADDRESS",
  "user": {
    "id": "uuid",
    "telegram_id": "123456789",
    "username": "user123"
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Get Balance
```http
GET /api/v1/wallets/balance/
```

**Query Parameters:**
- `check_blockchain` (optional): Set to `true` to fetch real-time blockchain balance

**Response:**
```json
{
  "address": "TRC20_ADDRESS",
  "balance": "100.500000",
  "blockchain_balance": "100.500000",
  "currency": "USDT"
}
```

---

### Get Deposit Address
```http
GET /api/v1/wallets/deposit_address/
```

**Response:**
```json
{
  "address": "TRC20_ADDRESS",
  "network": "TRC20",
  "currency": "USDT",
  "instructions": "Send USDT (TRC20) to this address. Deposits will be credited after blockchain confirmation."
}
```

---

### Request Withdrawal
```http
POST /api/v1/wallets/withdraw/
```

**Request Body:**
```json
{
  "to_address": "TRC20_DESTINATION_ADDRESS",
  "amount": "50.000000",
  "totp_token": "123456"
}
```

**Note:** `totp_token` is required if 2FA is enabled for the user.

**Response:**
```json
{
  "message": "Withdrawal request submitted",
  "task_id": "celery-task-id",
  "amount": "50.000000",
  "to_address": "TRC20_DESTINATION_ADDRESS"
}
```

**Status Codes:**
- `202 Accepted`: Withdrawal queued for processing
- `400 Bad Request`: Invalid input, insufficient balance, or invalid 2FA token
- `404 Not Found`: Wallet not found
- `429 Too Many Requests`: Too many failed 2FA attempts

---

### Get Transaction History
```http
GET /api/v1/wallets/transactions/
```

**Query Parameters:**
- `limit` (optional, default: 50): Number of transactions to return
- `offset` (optional, default: 0): Pagination offset

**Response:**
```json
{
  "count": 10,
  "transactions": [
    {
      "id": "uuid",
      "transaction_type": "DEPOSIT",
      "amount": "100.000000",
      "balance_before": "0.000000",
      "balance_after": "100.000000",
      "transaction_hash": "0x...",
      "description": "Deposit of 100.000000 USDT",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

## Deal Endpoints

### List Deals
```http
GET /api/v1/deals/
```

Returns all deals where the authenticated user is either buyer or seller.

**Response:**
```json
[
  {
    "id": "uuid",
    "buyer": {
      "id": "uuid",
      "username": "buyer123"
    },
    "seller": {
      "id": "uuid",
      "username": "seller456"
    },
    "title": "Website Development",
    "description": "Build a responsive website",
    "amount": "500.000000",
    "fee": "25.000000",
    "status": "IN_PROGRESS",
    "created_at": "2024-01-01T00:00:00Z",
    "funded_at": "2024-01-01T01:00:00Z",
    "started_at": "2024-01-01T02:00:00Z",
    "completed_at": null
  }
]
```

---

### Create Deal
```http
POST /api/v1/deals/
```

**Request Body:**
```json
{
  "seller": "seller_user_id",
  "title": "Website Development",
  "description": "Build a responsive website with React",
  "amount": "500.000000"
}
```

**Response:**
```json
{
  "id": "uuid",
  "buyer": {...},
  "seller": {...},
  "title": "Website Development",
  "description": "Build a responsive website with React",
  "amount": "500.000000",
  "fee": "25.000000",
  "status": "DRAFT",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Get Deal Details
```http
GET /api/v1/deals/{deal_id}/
```

**Response:** Same as deal object in list response.

---

### Fund Deal (Seller Action)
```http
POST /api/v1/deals/{deal_id}/fund/
```

Locks seller's balance and transitions deal from `DRAFT` to `FUNDED`.

**Response:**
```json
{
  "id": "uuid",
  "status": "FUNDED",
  "funded_at": "2024-01-01T01:00:00Z",
  ...
}
```

**Status Codes:**
- `200 OK`: Deal funded successfully
- `400 Bad Request`: Invalid state transition or insufficient balance
- `403 Forbidden`: User is not the seller

---

### Start Deal (Buyer Action)
```http
POST /api/v1/deals/{deal_id}/start/
```

Transitions deal from `FUNDED` to `IN_PROGRESS`.

**Response:**
```json
{
  "id": "uuid",
  "status": "IN_PROGRESS",
  "started_at": "2024-01-01T02:00:00Z",
  ...
}
```

**Status Codes:**
- `200 OK`: Deal started successfully
- `400 Bad Request`: Invalid state transition
- `403 Forbidden`: User is not the buyer

---

### Complete Deal (Buyer Action)
```http
POST /api/v1/deals/{deal_id}/complete/
```

Releases funds to buyer (minus platform fee) and transitions deal from `IN_PROGRESS` to `COMPLETED`.

**Response:**
```json
{
  "id": "uuid",
  "status": "COMPLETED",
  "completed_at": "2024-01-01T03:00:00Z",
  ...
}
```

**Status Codes:**
- `200 OK`: Deal completed successfully
- `400 Bad Request`: Invalid state transition
- `403 Forbidden`: User is not the buyer

---

### Dispute Deal (Buyer or Seller Action)
```http
POST /api/v1/deals/{deal_id}/dispute/
```

Freezes funds and transitions deal from `IN_PROGRESS` to `DISPUTED`.

**Request Body:**
```json
{
  "reason": "Seller did not deliver as promised"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "DISPUTED",
  "disputed_at": "2024-01-01T03:00:00Z",
  ...
}
```

**Status Codes:**
- `200 OK`: Dispute created successfully
- `400 Bad Request`: Invalid state transition
- `403 Forbidden`: User is not a participant

---

### Cancel Deal (Buyer or Seller Action)
```http
POST /api/v1/deals/{deal_id}/cancel/
```

Cancels deal and refunds locked funds if applicable. Only allowed in `DRAFT` or `FUNDED` status.

**Response:**
```json
{
  "id": "uuid",
  "status": "CANCELLED",
  "cancelled_at": "2024-01-01T03:00:00Z",
  ...
}
```

**Status Codes:**
- `200 OK`: Deal cancelled successfully
- `400 Bad Request`: Invalid state transition
- `403 Forbidden`: User is not a participant

---

### Resolve Dispute (Admin Only)
```http
POST /api/v1/deals/{deal_id}/resolve/
```

Resolves a disputed deal by either refunding to seller or releasing to buyer.

**Request Body:**
```json
{
  "resolution": "After review, buyer was correct. Releasing funds to buyer.",
  "refund_to_seller": false
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "COMPLETED",
  "completed_at": "2024-01-01T04:00:00Z",
  ...
}
```

**Status Codes:**
- `200 OK`: Dispute resolved successfully
- `400 Bad Request`: Invalid state transition
- `403 Forbidden`: User is not an admin

---

## Deal State Machine

```
DRAFT
  ↓ (seller funds)
FUNDED
  ↓ (buyer starts)
IN_PROGRESS
  ↓ (buyer completes OR dispute)
COMPLETED / DISPUTED
```

### State Transitions

| From | To | Action | Who |
|------|-----|--------|-----|
| DRAFT | FUNDED | fund | Seller |
| FUNDED | IN_PROGRESS | start | Buyer |
| IN_PROGRESS | COMPLETED | complete | Buyer |
| IN_PROGRESS | DISPUTED | dispute | Buyer or Seller |
| DISPUTED | COMPLETED/CANCELLED | resolve | Admin |
| DRAFT/FUNDED | CANCELLED | cancel | Buyer or Seller |

---

## Ledger Transaction Types

- `DEPOSIT`: User deposits USDT to their wallet
- `WITHDRAWAL`: User withdraws USDT from their wallet
- `ESCROW_LOCK`: Funds locked when seller funds a deal
- `ESCROW_RELEASE`: Funds released to buyer when deal completes
- `FEE`: Platform fee deducted from seller

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

### Common Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `202 Accepted`: Request accepted for processing
- `400 Bad Request`: Invalid input or business logic error
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Blockchain Integration

### Deposit Flow

1. User gets their deposit address via `/api/v1/wallets/deposit_address/`
2. User sends USDT (TRC20) to that address
3. Celery task monitors blockchain every 30 seconds
4. When transaction is confirmed, balance is updated automatically
5. Ledger entry is created with transaction hash

### Withdrawal Flow

1. User submits withdrawal request via `/api/v1/wallets/withdraw/`
2. Request is queued as Celery task
3. Task validates balance and address
4. Transaction is signed and broadcast to blockchain
5. Balance is updated and ledger entry is created
6. Transaction hash is returned

### Balance Synchronization

- Runs every hour via Celery Beat
- Compares database balance with blockchain balance
- Logs discrepancies for admin review
- Generates daily wallet reports

---

## Security Features

### Authentication & Authorization
- **Token-based authentication**: Secure token generation and validation
- **Telegram Login Widget**: Hash verification for Telegram authentication
- **Session management**: Token rotation and expiration
- **Two-factor authentication (2FA)**: TOTP-based 2FA with backup codes

### Rate Limiting
- **General API endpoints**: 100 requests per minute
- **Authentication endpoints**: 10 requests per minute
- **Withdrawal endpoints**: 5 requests per minute
- **2FA verification**: 5 attempts per 15 minutes
- **Identification**: By user ID (authenticated) or IP address (anonymous)

### Audit Logging
- All security-sensitive operations are logged
- Tracked events:
  - User login/logout
  - Withdrawal requests
  - Deal operations (created, funded, completed, disputed, cancelled)
  - Profile updates
  - 2FA enable/disable
  - Admin actions
- Logged information:
  - User ID
  - Action type
  - IP address
  - User agent
  - Additional details (JSON)
  - Success/failure status
  - Timestamp

### Balance Mutations
- All balance changes use database-level row locking (`select_for_update()`)
- Wrapped in atomic transactions to prevent race conditions
- Immutable ledger entries for audit trail

### Private Key Security
- Private keys encrypted with AES-256
- Encryption key stored in environment variables
- Keys never exposed via API
- Only decrypted in memory for transaction signing

### State Machine Enforcement
- Strict validation of state transitions
- Cannot skip states or move backwards
- Business logic enforced at service layer

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (HSTS) in production
- Secure cookie flags in production

---

## Rate Limiting

### Rate Limit Rules
- **General API endpoints**: 100 requests per minute per user/IP
- **Authentication endpoints** (`/auth/*`): 10 requests per minute per user/IP
- **Withdrawal endpoints** (`/withdraw`): 5 requests per minute per user/IP
- **2FA verification**: 5 attempts per 15 minutes per user

### Rate Limit Response
```json
{
  "error": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

**Status Code:** `429 Too Many Requests`

---

## WebSocket Events

(To be implemented in Phase 4)

### Deal Updates
```
ws://localhost:8000/ws/deals/{deal_id}/
```

Events:
- `deal.status_changed`
- `deal.message_received`
- `deal.typing`

### Balance Updates
```
ws://localhost:8000/ws/wallet/
```

Events:
- `balance.updated`
- `transaction.confirmed`

---

## Testing

### Test Credentials
(Use Telegram Login Widget for authentication)

### Test Network
- Network: Nile Testnet (Tron)
- USDT Contract: `TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf`

### Get Test USDT
1. Get test TRX from Nile faucet
2. Use test USDT contract for transactions

---

## Support

For issues or questions:
- Check application logs in your terminal windows
- Check Celery logs in the Celery worker terminal
- Admin panel: `http://localhost:8000/admin/`
