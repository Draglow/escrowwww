# System Flow Diagrams

## User Registration & Wallet Creation

```
┌─────────────┐
│   User      │
│  Opens App  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Telegram Login      │
│ Widget              │
└──────┬──────────────┘
       │ (auth data + hash)
       ▼
┌─────────────────────┐
│ Backend Verifies    │
│ Telegram Hash       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Create/Get User     │
│ (telegram_id)       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Signal Triggers:    │
│ Create Wallet       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Generate Tron       │
│ Private Key         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Encrypt Private Key │
│ (Fernet)            │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Save Wallet to DB   │
│ (address + enc_key) │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Return JWT Token    │
│ to Frontend         │
└─────────────────────┘
```

## Deal Creation Flow

```
┌─────────────┐
│   Buyer     │
│ Creates Deal│
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ POST /api/v1/deals/         │
│ {                           │
│   seller: UUID,             │
│   title: "...",             │
│   description: "...",       │
│   amount: 100.00            │
│ }                           │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ DealService.create_deal()   │
│ - Calculate fee (2.5%)      │
│ - Status = DRAFT            │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Save Deal to Database       │
│ Status: DRAFT               │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Return Deal Object          │
│ to Frontend                 │
└─────────────────────────────┘
```

## Deal Funding Flow (Escrow Lock)

```
┌─────────────┐
│   Seller    │
│ Funds Deal  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ POST /api/v1/deals/{id}/fund│
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Check Deal Status = DRAFT   │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ BEGIN TRANSACTION           │
│ (Atomic Block)              │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Lock Seller Row             │
│ SELECT FOR UPDATE           │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Check Balance >= Amount     │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Deduct from Seller Balance  │
│ seller.balance -= amount    │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Update Deal Status          │
│ Status: FUNDED              │
│ funded_at: now()            │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Create Ledger Entry         │
│ Type: ESCROW_LOCK           │
│ balance_before, balance_after│
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ COMMIT TRANSACTION          │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Send WebSocket Update       │
│ (Deal Status Changed)       │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Return Success Response     │
└─────────────────────────────┘
```

## Deal Completion Flow

```
┌─────────────┐
│   Buyer     │
│ Confirms    │
│ Receipt     │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────┐
│ POST /api/v1/deals/{id}/     │
│      complete                │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Check Status = IN_PROGRESS   │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ BEGIN TRANSACTION            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Lock Buyer Row               │
│ SELECT FOR UPDATE            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Calculate Amounts:           │
│ - buyer_amount = amount      │
│ - platform_fee = fee         │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Add to Buyer Balance         │
│ buyer.balance += amount      │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Create Ledger Entries:       │
│ 1. ESCROW_RELEASE (buyer)    │
│ 2. FEE (seller)              │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Update Deal Status           │
│ Status: COMPLETED            │
│ completed_at: now()          │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ COMMIT TRANSACTION           │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Send WebSocket Updates       │
│ (to both parties)            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Return Success Response      │
└──────────────────────────────┘
```

## Deposit Flow (To Be Implemented)

```
┌─────────────┐
│   User      │
│ Sends USDT  │
│ to Wallet   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────┐
│ Tron Blockchain              │
│ (Transaction Confirmed)      │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Celery Task:                 │
│ Monitor Deposits             │
│ (Polls TronGrid API)         │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Detect New Transaction       │
│ to User Wallet               │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Verify Confirmations >= 19   │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ BEGIN TRANSACTION            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Lock User Row                │
│ SELECT FOR UPDATE            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Add to User Balance          │
│ user.balance += amount       │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Create Ledger Entry          │
│ Type: DEPOSIT                │
│ metadata: {tx_hash, ...}     │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ COMMIT TRANSACTION           │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Send WebSocket Update        │
│ (Balance Updated)            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Send Notification            │
│ (Telegram/Email)             │
└──────────────────────────────┘
```

## Withdrawal Flow (To Be Implemented)

```
┌─────────────┐
│   User      │
│ Requests    │
│ Withdrawal  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────┐
│ POST /api/v1/wallets/        │
│      withdraw                │
│ {                            │
│   address: "T...",           │
│   amount: 50.00              │
│ }                            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Validate Address             │
│ (TRC20 format)               │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ BEGIN TRANSACTION            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Lock User Row                │
│ SELECT FOR UPDATE            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Check Available Balance      │
│ (excluding locked funds)     │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Deduct from Balance          │
│ user.balance -= amount       │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Create Ledger Entry          │
│ Type: WITHDRAWAL             │
│ Status: PENDING              │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ COMMIT TRANSACTION           │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Queue Celery Task:           │
│ Process Withdrawal           │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Celery Worker:               │
│ 1. Decrypt Private Key       │
│ 2. Sign Transaction          │
│ 3. Broadcast to Tron         │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Update Ledger Entry          │
│ metadata: {tx_hash, status}  │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Send WebSocket Update        │
│ (Withdrawal Processed)       │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Send Notification            │
└──────────────────────────────┘
```

## State Machine Diagram

```
Deal Status Transitions:

    ┌─────────┐
    │  DRAFT  │ ◄─── Initial state (deal created)
    └────┬────┘
         │
         │ fund_deal()
         │ (seller locks balance)
         ▼
    ┌─────────┐
    │ FUNDED  │
    └────┬────┘
         │
         │ start_deal()
         │ (both parties ready)
         ▼
    ┌──────────────┐
    │ IN_PROGRESS  │
    └────┬─────┬───┘
         │     │
         │     │ dispute_deal()
         │     │ (issue raised)
         │     ▼
         │  ┌───────────┐
         │  │ DISPUTED  │
         │  └─────┬─────┘
         │        │
         │        │ resolve_dispute()
         │        │ (admin decision)
         │        ▼
         │  ┌────────────┐
         │  │ COMPLETED  │ ◄─── Final state (success)
         │  │     or     │
         │  │ CANCELLED  │ ◄─── Final state (refund)
         │  └────────────┘
         │
         │ complete_deal()
         │ (buyer confirms)
         ▼
    ┌────────────┐
    │ COMPLETED  │ ◄─── Final state (success)
    └────────────┘

    Any state can transition to:
    ┌────────────┐
    │ CANCELLED  │ ◄─── cancel_deal() (with refund)
    └────────────┘
```

## Database Locking Strategy

```
Concurrent Request Scenario:

Request A                    Request B
    │                            │
    ▼                            ▼
┌─────────────┐            ┌─────────────┐
│ BEGIN TRANS │            │ BEGIN TRANS │
└──────┬──────┘            └──────┬──────┘
       │                          │
       ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│ SELECT FOR UPDATE   │    │ SELECT FOR UPDATE   │
│ (Lock User Row)     │    │ (WAITS for lock)    │
└──────┬──────────────┘    └──────┬──────────────┘
       │                          │ (blocked)
       ▼                          │
┌─────────────────────┐          │
│ Check Balance       │          │
│ balance = 100       │          │
└──────┬──────────────┘          │
       │                          │
       ▼                          │
┌─────────────────────┐          │
│ Deduct 50           │          │
│ balance = 50        │          │
└──────┬──────────────┘          │
       │                          │
       ▼                          │
┌─────────────────────┐          │
│ COMMIT              │          │
│ (Release lock)      │          │
└──────┬──────────────┘          │
       │                          │
       │                          ▼
       │                   ┌─────────────────────┐
       │                   │ Lock Acquired       │
       │                   │ Check Balance       │
       │                   │ balance = 50 ✓      │
       │                   └──────┬──────────────┘
       │                          │
       │                          ▼
       │                   ┌─────────────────────┐
       │                   │ Deduct 30           │
       │                   │ balance = 20        │
       │                   └──────┬──────────────┘
       │                          │
       │                          ▼
       │                   ┌─────────────────────┐
       │                   │ COMMIT              │
       │                   └─────────────────────┘
       │
       ▼
   No Race Condition! ✓
   Final balance: 20 (correct)
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dashboard │  │  Deals   │  │  Wallet  │  │ Profile  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django Backend (DRF)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Users   │  │ Wallets  │  │  Deals   │  │  Ledger  │   │
│  │   API    │  │   API    │  │   API    │  │   API    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │              │          │
│       └─────────────┴──────────────┴──────────────┘          │
│                          │                                    │
│                          ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Service Layer                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │  Wallet  │  │   Deal   │  │  Ledger  │          │   │
│  │  │ Service  │  │ Service  │  │ Service  │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  PostgreSQL  │ │  Redis   │ │ Tron Network │
│   Database   │ │  Cache   │ │  (TronGrid)  │
└──────────────┘ └──────────┘ └──────────────┘
        │            │
        │            ▼
        │     ┌──────────────┐
        │     │    Celery    │
        │     │   Workers    │
        │     └──────────────┘
        │
        ▼
┌──────────────────┐
│  Immutable       │
│  Ledger          │
│  (Audit Trail)   │
└──────────────────┘
```

---

**These diagrams illustrate the complete system flow and architecture of the crypto escrow platform.**
