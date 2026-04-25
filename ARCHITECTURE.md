# Crypto Escrow Platform - Architecture Documentation

## Overview
This is a secure, high-performance crypto escrow platform for USDT (TRC20) transactions, built with Django backend and designed for Next.js frontend integration.

## Core Security Principles

### 1. Private Key Security
- All wallet private keys are encrypted using Fernet (symmetric encryption)
- Encryption key stored in environment variables
- Private keys NEVER exposed via API endpoints
- Decryption only happens internally for transaction signing

### 2. Race Condition Prevention
- All balance mutations use `select_for_update()` for database-level row locking
- All financial operations wrapped in `@transaction.atomic` blocks
- Prevents double-spending and concurrent modification issues

### 3. Immutable Audit Trail
- Ledger entries cannot be modified or deleted
- Complete transaction history for compliance
- Balance snapshots (before/after) for every transaction

### 4. State Machine Integrity
- Strict deal status transitions enforced at service layer
- Invalid state transitions raise exceptions
- Status: DRAFT → FUNDED → IN_PROGRESS → COMPLETED

## Database Schema

### User Model
```python
- id: UUID (primary key)
- telegram_id: BigInteger (unique, indexed)
- username, first_name, last_name: String
- balance: Decimal(20,6) - USDT balance
- webauthn_credentials: JSON
- is_verified, is_active: Boolean
```

### Wallet Model
```python
- id: UUID (primary key)
- user: OneToOne → User
- address: String(42) - TRC20 address
- encrypted_private_key: Binary (NEVER exposed)
```

### Deal Model
```python
- id: UUID (primary key)
- buyer, seller: ForeignKey → User
- amount: Decimal(20,6)
- fee: Decimal(20,6) - calculated from PLATFORM_FEE_PERCENTAGE
- status: Choice (DRAFT, FUNDED, IN_PROGRESS, DISPUTED, COMPLETED, CANCELLED)
- title, description: String/Text
- funded_at, completed_at: DateTime
```

### LedgerEntry Model
```python
- id: UUID (primary key)
- user: ForeignKey → User
- deal: ForeignKey → Deal (nullable)
- transaction_type: Choice (DEPOSIT, WITHDRAWAL, ESCROW_LOCK, etc.)
- amount: Decimal(20,6)
- balance_before, balance_after: Decimal(20,6)
- metadata: JSON
- created_at: DateTime (immutable)
```

## API Architecture

### Authentication
- **Telegram Login Widget**: Hash verification using HMAC-SHA256
- Authorization header format: `Authorization: Telegram id=123&hash=abc...`
- WebAuthn support for passkey authentication (future)

### REST Endpoints

#### Users (`/api/v1/users/`)
- `GET /me/` - Current user profile
- `PATCH /update_profile/` - Update profile

#### Wallets (`/api/v1/wallets/`)
- `GET /my_wallet/` - Get user's wallet address

#### Deals (`/api/v1/deals/`)
- `GET /` - List user's deals
- `POST /` - Create new deal
- `GET /{id}/` - Deal details
- `POST /{id}/fund/` - Fund deal (lock seller balance)
- `POST /{id}/complete/` - Complete deal (release to buyer)

#### Ledger (`/api/v1/ledger/`)
- `GET /` - User's transaction history

### WebSocket Endpoints (Future)
- `/ws/deals/{deal_id}/` - Real-time deal updates
- `/ws/chat/{deal_id}/` - Deal chat messages

## Service Layer

### WalletService
- `create_wallet(user)` - Generate new Tron wallet
- `get_private_key(wallet)` - Decrypt private key (internal only)

### DealService
- `create_deal(...)` - Create deal in DRAFT status
- `fund_deal(deal)` - Lock seller balance (DRAFT → FUNDED)
- `complete_deal(deal)` - Release to buyer (IN_PROGRESS → COMPLETED)

### LedgerService
- `record_escrow_lock(user, deal, amount)`
- `record_escrow_release(user, deal, amount)`
- `record_fee(user, deal, amount)`

## Celery Tasks (Future Implementation)

### Blockchain Monitoring
- Monitor incoming USDT deposits to user wallets
- Detect confirmations and update balances
- Process withdrawal requests

### Scheduled Tasks
- Check for expired deals
- Send notifications
- Generate reports

## Frontend Integration (Next.js)

### Recommended Structure
```
frontend/
├── app/
│   ├── (auth)/
│   │   └── login/
│   ├── (dashboard)/
│   │   ├── deals/
│   │   ├── wallet/
│   │   └── transactions/
│   └── layout.tsx
├── components/
│   ├── ui/ (shadcn)
│   ├── deals/
│   └── wallet/
├── lib/
│   ├── api.ts
│   ├── websocket.ts
│   └── telegram-auth.ts
└── stores/
    ├── user.ts
    └── deals.ts
```

### State Management (Zustand)
```typescript
// stores/user.ts
interface UserStore {
  user: User | null
  balance: string
  fetchUser: () => Promise<void>
  updateBalance: (balance: string) => void
}
```

### API Client (React Query)
```typescript
// lib/api.ts
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Authorization': `Telegram ${telegramAuthData}`
  }
})
```

## Deployment Considerations

### Environment Variables
- `SECRET_KEY` - Django secret
- `WALLET_ENCRYPTION_KEY` - Fernet key for wallet encryption
- `TELEGRAM_BOT_TOKEN` - For auth verification
- `TRONGRID_API_KEY` - Tron network access
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection

### Security Checklist
- [ ] Use HTTPS in production
- [ ] Enable HSTS headers
- [ ] Set secure cookie flags
- [ ] Rotate encryption keys regularly
- [ ] Enable database backups
- [ ] Set up monitoring and alerts
- [ ] Rate limiting on API endpoints
- [ ] CORS configuration for frontend domain

### Scaling Considerations
- PostgreSQL read replicas for queries
- Redis cluster for high availability
- Celery workers for async processing
- CDN for frontend assets
- Load balancer for multiple backend instances

## Testing Strategy

### Unit Tests
- Model methods and properties
- Service layer logic
- Encryption/decryption
- State machine transitions

### Integration Tests
- API endpoints
- Authentication flow
- Deal lifecycle
- Balance mutations

### Security Tests
- Race condition scenarios
- Invalid state transitions
- Private key exposure attempts
- SQL injection prevention

## Monitoring & Logging

### Key Metrics
- Transaction volume and value
- Deal completion rate
- API response times
- Error rates
- Wallet balance discrepancies

### Logging
- All balance mutations
- Deal status changes
- Authentication attempts
- Blockchain transactions
- Error stack traces

## Future Enhancements

1. **Multi-currency Support**: Add BTC, ETH, other tokens
2. **Dispute Resolution**: Admin panel for dispute handling
3. **Reputation System**: User ratings and reviews
4. **Escrow Templates**: Pre-configured deal types
5. **Mobile Apps**: React Native for iOS/Android
6. **KYC Integration**: Identity verification
7. **Advanced Analytics**: Dashboard with charts
8. **Referral Program**: User acquisition incentives
