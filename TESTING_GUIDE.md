# Testing Guide — Crypto Escrow Platform

## Quick Start

```bash
# Install test dependencies (one-time)
cd backend
pip install -r requirements.txt

# Run all tests (fast, no coverage)
python -m pytest apps/ tests/ --no-cov -q

# Run with coverage report
python -m pytest apps/ tests/ --cov=apps --cov-report=term-missing

# Windows single-command runner
run_tests.bat

# Linux/Mac single-command runner
bash run_tests.sh
```

---

## Test Architecture

| Layer | Framework | Location |
|-------|-----------|----------|
| Backend unit + integration | pytest + pytest-django | `backend/apps/*/tests.py` |
| Test factories | factory-boy | `backend/tests/factories.py` |
| Test settings | Django settings override | `backend/config/settings_test.py` |

The test settings use:
- **SQLite** (file-based) instead of PostgreSQL — no external DB needed
- **In-memory cache** instead of Redis — no Redis needed
- **Synchronous Celery** — tasks run inline
- **DEBUG=True** — Telegram auth hash verification skipped

---

## Phase 7: Automated Tests (119 tests)

### Running Individual Test Suites

```bash
# Users (39 tests) — model, auth, 2FA, audit, API
python -m pytest apps/users/tests.py --no-cov -v

# Wallets (23 tests) — encryption, deposits, withdrawals, API
python -m pytest apps/wallets/tests.py --no-cov -v

# Deals (41 tests) — state machine, lifecycle, API, chat
python -m pytest apps/deals/tests.py --no-cov -v

# Ledger (16 tests) — immutability, service, API
python -m pytest apps/ledger/tests.py --no-cov -v
```

---

## Feature-by-Feature Testing Guide

### Feature 1: User Model & Authentication

#### Automated Tests
```bash
python -m pytest apps/users/tests.py::TestUserModel --no-cov -v
python -m pytest apps/users/tests.py::TestTokenManagement --no-cov -v
python -m pytest apps/users/tests.py::TestTelegramAuthentication --no-cov -v
```

#### Manual Testing

**Telegram Login (DEBUG mode)**
```bash
curl -X POST http://localhost:8000/api/v1/users/auth/login/ \
  -H "Authorization: Telegram id=123456789&first_name=Test&username=testuser&auth_date=1234567890&hash=fakehash"
```
Expected: `{"user": {...}, "token": "abc123..."}`

**Get Current User**
```bash
curl http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Token YOUR_TOKEN"
```
Expected: User profile JSON

**Logout**
```bash
curl -X POST http://localhost:8000/api/v1/users/auth/logout/ \
  -H "Authorization: Token YOUR_TOKEN"
```
Expected: `{"message": "Successfully logged out"}`

#### Edge Cases
- Login with expired auth_date (>24h) → 401 in production, passes in DEBUG
- Login with invalid hash → 401 in production, passes in DEBUG
- Access protected endpoint without token → 401
- Access with revoked token → 401

---

### Feature 2: Two-Factor Authentication (2FA)

#### Automated Tests
```bash
python -m pytest apps/users/tests.py::TestTwoFactorAuth --no-cov -v
```

#### Manual Testing

**Enable 2FA**
```bash
curl -X POST http://localhost:8000/api/v1/users/enable_2fa/ \
  -H "Authorization: Token YOUR_TOKEN"
```
Expected: `{"secret": "...", "qr_code": "base64...", "backup_codes": [...]}`

**Verify 2FA Setup**
```bash
curl -X POST http://localhost:8000/api/v1/users/verify_2fa_setup/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "123456"}'
```
Expected: `{"message": "2FA enabled successfully", "backup_codes": [...]}`

**Disable 2FA**
```bash
curl -X POST http://localhost:8000/api/v1/users/disable_2fa/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "123456"}'
```

#### Edge Cases
- Enable 2FA when already enabled → 400
- Verify with wrong token → 400
- Rate limit: 5 failed attempts in 15 minutes → 429
- Use backup code → code is consumed (single-use)

---

### Feature 3: Wallet Encryption

#### Automated Tests
```bash
python -m pytest apps/wallets/tests.py::TestWalletEncryption --no-cov -v
```

#### Manual Testing (Django Shell)
```python
from apps.wallets.encryption import WalletEncryption

private_key = 'a' * 64
encrypted = WalletEncryption.encrypt_private_key(private_key)
decrypted = WalletEncryption.decrypt_private_key(encrypted)
assert decrypted == private_key
print("Encryption roundtrip: OK")
```

#### Edge Cases
- Encrypted key is never exposed via API (check serializers)
- Different keys produce different ciphertext
- Decryption with wrong key fails

---

### Feature 4: Deposit Detection

#### Automated Tests
```bash
python -m pytest apps/wallets/tests.py::TestDepositProcessing --no-cov -v
```

#### Manual Testing (Django Shell)
```python
from decimal import Decimal
from apps.wallets.models import Wallet
from apps.wallets.services import WalletService

wallet = Wallet.objects.first()
tx_hash = '0x' + 'a' * 64

# Process deposit
WalletService.process_deposit(wallet, Decimal('100.000000'), tx_hash)

# Verify balance updated
wallet.user.refresh_from_db()
print(f"Balance: {wallet.user.balance}")

# Verify idempotency (same tx_hash)
result = WalletService.process_deposit(wallet, Decimal('100.000000'), tx_hash)
print(f"Duplicate deposit blocked: {not result}")
```

#### Edge Cases
- Same tx_hash processed twice → second call returns False, balance unchanged
- Deposit creates ledger entry with correct before/after balances
- Concurrent deposits with different tx_hashes → both processed correctly

---

### Feature 5: Withdrawal Processing

#### Automated Tests
```bash
python -m pytest apps/wallets/tests.py::TestWithdrawalProcessing --no-cov -v
```

#### Manual Testing via API
```bash
# Without 2FA
curl -X POST http://localhost:8000/api/v1/wallets/withdraw/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_address": "VALID_TRC20_ADDRESS", "amount": "10.000000"}'

# With 2FA enabled
curl -X POST http://localhost:8000/api/v1/wallets/withdraw/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_address": "VALID_TRC20_ADDRESS", "amount": "10.000000", "totp_token": "123456"}'
```

#### Edge Cases
- Insufficient balance → 400
- Invalid Tron address → 400
- Missing amount → 400
- 2FA enabled but no token → 400
- Invalid 2FA token → 400 with remaining_attempts
- Negative amount → 400

---

### Feature 6: Deal Lifecycle (State Machine)

#### Automated Tests
```bash
python -m pytest apps/deals/tests.py::TestDealStateMachine --no-cov -v
```

#### Manual Testing (Django Shell)
```python
from decimal import Decimal
from apps.users.models import User
from apps.deals.services import DealService

buyer = User.objects.get(username='buyer')
seller = User.objects.get(username='seller')
seller.balance = Decimal('500.000000')
seller.save()

# Full lifecycle
deal = DealService.create_deal(buyer, seller, 'Test', 'Description', Decimal('100.000000'))
print(f"Created: {deal.status}")  # DRAFT

deal = DealService.fund_deal(deal)
print(f"Funded: {deal.status}")   # FUNDED

deal = DealService.start_deal(deal)
print(f"Started: {deal.status}")  # IN_PROGRESS

deal = DealService.complete_deal(deal)
print(f"Completed: {deal.status}")  # COMPLETED

buyer.refresh_from_db()
print(f"Buyer received: {buyer.balance}")  # 97.5 (100 - 2.5% fee)
```

#### Edge Cases
- Fund deal with insufficient balance → ValueError
- Start deal not in FUNDED status → ValueError
- Complete deal not in IN_PROGRESS → ValueError
- Cancel COMPLETED deal → ValueError
- Cancel DISPUTED deal → ValueError
- Dispute deal not in IN_PROGRESS → ValueError
- Resolve dispute not in DISPUTED → ValueError

---

### Feature 7: Deal API Endpoints

#### Automated Tests
```bash
python -m pytest apps/deals/tests.py::TestDealAPI --no-cov -v
```

#### Manual Testing
```bash
# Create deal
curl -X POST http://localhost:8000/api/v1/deals/ \
  -H "Authorization: Token BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"seller": "SELLER_UUID", "title": "Test", "description": "Desc", "amount": "100.000000"}'

# Fund deal (seller)
curl -X POST http://localhost:8000/api/v1/deals/DEAL_ID/fund/ \
  -H "Authorization: Token SELLER_TOKEN"

# Start deal (buyer)
curl -X POST http://localhost:8000/api/v1/deals/DEAL_ID/start/ \
  -H "Authorization: Token BUYER_TOKEN"

# Complete deal (buyer)
curl -X POST http://localhost:8000/api/v1/deals/DEAL_ID/complete/ \
  -H "Authorization: Token BUYER_TOKEN"

# Dispute deal
curl -X POST http://localhost:8000/api/v1/deals/DEAL_ID/dispute/ \
  -H "Authorization: Token BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Seller did not deliver"}'

# Resolve dispute (admin only)
curl -X POST http://localhost:8000/api/v1/deals/DEAL_ID/resolve/ \
  -H "Authorization: Token ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resolution": "Buyer wins", "refund_to_seller": false}'
```

#### Authorization Edge Cases
- Buyer tries to fund → 403
- Seller tries to start → 403
- Seller tries to complete → 403
- Non-participant tries to dispute → 403
- Non-admin tries to resolve → 403
- User tries to access another user's deal → 404

---

### Feature 8: Deal Chat

#### Automated Tests
```bash
python -m pytest apps/deals/tests.py::TestDealAPI::test_send_message_in_deal --no-cov -v
python -m pytest apps/deals/tests.py::TestDealAPI::test_get_messages_in_deal --no-cov -v
```

#### Manual Testing
```bash
# Send message
curl -X POST http://localhost:8000/api/v1/deals/DEAL_ID/send_message/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!"}'

# Get messages
curl http://localhost:8000/api/v1/deals/DEAL_ID/messages/ \
  -H "Authorization: Token YOUR_TOKEN"

# Mark messages as read
curl -X POST http://localhost:8000/api/v1/deals/DEAL_ID/mark_messages_read/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message_ids": ["MSG_UUID_1", "MSG_UUID_2"]}'
```

---

### Feature 9: Ledger Immutability

#### Automated Tests
```bash
python -m pytest apps/ledger/tests.py --no-cov -v
```

#### Manual Testing (Django Shell)
```python
from apps.ledger.models import LedgerEntry

entry = LedgerEntry.objects.first()

# Try to modify
try:
    entry.amount = 999
    entry.save()
    print("ERROR: Should have raised!")
except ValueError as e:
    print(f"Correctly blocked: {e}")

# Try to delete
try:
    entry.delete()
    print("ERROR: Should have raised!")
except ValueError as e:
    print(f"Correctly blocked: {e}")
```

#### Edge Cases
- Modify existing entry → ValueError
- Delete entry → ValueError
- Create entry with same tx_hash → second deposit blocked by service layer
- Ledger entries ordered by -created_at

---

### Feature 10: Audit Logging

#### Automated Tests
```bash
python -m pytest apps/users/tests.py::TestAuditLog --no-cov -v
```

#### Manual Testing
```bash
# Get audit logs for current user
curl http://localhost:8000/api/v1/users/audit_logs/ \
  -H "Authorization: Token YOUR_TOKEN"
```

Expected: List of audit log entries with action, ip_address, success, created_at

---

### Feature 11: Race Condition Prevention

#### Automated Tests
```bash
python -m pytest apps/deals/tests.py::TestRaceConditions --no-cov -v
```

#### Manual Testing (Django Shell)
```python
from decimal import Decimal
from django.db import transaction
from apps.users.models import User
import threading

user = User.objects.first()
user.balance = Decimal('100.000000')
user.save()

def withdraw(amount):
    try:
        with transaction.atomic():
            u = User.objects.select_for_update().get(pk=user.pk)
            if u.balance >= amount:
                u.balance -= amount
                u.save()
                print(f"Withdrew {amount}, balance: {u.balance}")
            else:
                print(f"Insufficient for {amount}")
    except Exception as e:
        print(f"Error: {e}")

threads = [threading.Thread(target=withdraw, args=(Decimal('30'),)) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

user.refresh_from_db()
print(f"Final balance: {user.balance}")  # Should be >= 0
```

---

### Feature 12: Health Check Endpoints

#### Manual Testing
```bash
curl http://localhost:8000/api/v1/health/
curl http://localhost:8000/api/v1/health/detailed/
curl http://localhost:8000/api/v1/health/ready/
curl http://localhost:8000/api/v1/health/live/
```

Expected: JSON with status "ok" and service health details

---

## Wallet API Endpoints

```bash
# Get balance
curl http://localhost:8000/api/v1/wallets/balance/ \
  -H "Authorization: Token YOUR_TOKEN"

# Get deposit address
curl http://localhost:8000/api/v1/wallets/deposit_address/ \
  -H "Authorization: Token YOUR_TOKEN"

# Get transaction history
curl http://localhost:8000/api/v1/wallets/transactions/ \
  -H "Authorization: Token YOUR_TOKEN"

# Get blockchain balance (slow)
curl "http://localhost:8000/api/v1/wallets/balance/?check_blockchain=true" \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## Ledger API Endpoints

```bash
# Get transaction history
curl http://localhost:8000/api/v1/ledger/ \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## Common Issues

### Tests fail with "No module named pytest"
```bash
pip install pytest pytest-django pytest-cov factory-boy Faker responses
```

### Tests fail with database connection errors
The test settings use SQLite — no PostgreSQL needed. Ensure `DJANGO_SETTINGS_MODULE=config.settings_test`.

### Tests fail with "UNIQUE constraint failed: wallets.user_id"
This is a test isolation issue. Run tests fresh:
```bash
python -m pytest apps/ tests/ --no-cov -q --forked
```
Or delete the test DB file:
```bash
del backend\test_db.sqlite3
```

### Celery tasks not running in tests
Test settings set `CELERY_TASK_ALWAYS_EAGER=True` — tasks run synchronously.

### Blockchain API errors in tests
Blockchain calls are mocked in tests using `unittest.mock.patch`.

---

## CI/CD Integration

Tests run automatically via GitHub Actions on every push. See `.github/workflows/` for configuration.

To run locally in CI mode:
```bash
python -m pytest apps/ tests/ --no-cov -q --tb=short
```
