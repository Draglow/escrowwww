# Quick Start Guide - Phase 2 Testing

## Get Started in 5 Minutes

### Step 1: Start Services
```bash
# Build and start all containers
make build
make up

# Check services are running
docker-compose ps
```

### Step 2: Run Migrations
```bash
# Run database migrations
make migrate

# Create superuser for admin access
make createsuperuser
```

### Step 3: Create Test Users and Wallets
```bash
make shell
```

```python
from decimal import Decimal
from apps.users.models import User
from apps.wallets.services import WalletService

# Create buyer
buyer = User.objects.create(
    telegram_id='111111111',
    username='buyer_test',
    first_name='Test',
    last_name='Buyer',
    balance=Decimal('0')
)
buyer_wallet = WalletService.create_wallet(buyer)
print(f"Buyer wallet: {buyer_wallet.address}")

# Create seller with initial balance
seller = User.objects.create(
    telegram_id='222222222',
    username='seller_test',
    first_name='Test',
    last_name='Seller',
    balance=Decimal('1000.000000')
)
seller_wallet = WalletService.create_wallet(seller)
print(f"Seller wallet: {seller_wallet.address}")

exit()
```

### Step 4: Test Deposit
```bash
make shell
```

```python
from decimal import Decimal
from apps.users.models import User
from apps.wallets.services import WalletService

# Get buyer
buyer = User.objects.get(username='buyer_test')
wallet = buyer.wallet

# Simulate deposit (in production, this happens automatically)
WalletService.process_deposit(
    wallet,
    Decimal('500.000000'),
    '0x' + 'a' * 64  # Fake tx hash for testing
)

print(f"Buyer balance: {buyer.balance}")

exit()
```

### Step 5: Test Complete Deal Flow
```bash
make shell
```

```python
from decimal import Decimal
from apps.users.models import User
from apps.deals.services import DealService

# Get users
buyer = User.objects.get(username='buyer_test')
seller = User.objects.get(username='seller_test')

print(f"Initial - Buyer: {buyer.balance}, Seller: {seller.balance}")

# Create deal
deal = DealService.create_deal(
    buyer=buyer,
    seller=seller,
    title='Website Development',
    description='Build a responsive website',
    amount=Decimal('100.000000')
)
print(f"1. Deal created: {deal.status}, Fee: {deal.fee}")

# Fund deal (seller)
deal = DealService.fund_deal(deal)
seller.refresh_from_db()
print(f"2. Deal funded: {deal.status}, Seller balance: {seller.balance}")

# Start deal (buyer)
deal = DealService.start_deal(deal)
print(f"3. Deal started: {deal.status}")

# Complete deal (buyer)
deal = DealService.complete_deal(deal)
buyer.refresh_from_db()
seller.refresh_from_db()
print(f"4. Deal completed: {deal.status}")
print(f"Final - Buyer: {buyer.balance}, Seller: {seller.balance}")

exit()
```

### Step 6: Check Ledger Entries
```bash
make shell
```

```python
from apps.ledger.models import LedgerEntry
from apps.users.models import User

buyer = User.objects.get(username='buyer_test')
seller = User.objects.get(username='seller_test')

print("\n=== Buyer Transactions ===")
for entry in LedgerEntry.objects.filter(user=buyer).order_by('created_at'):
    print(f"{entry.transaction_type}: {entry.amount} USDT")
    print(f"  Before: {entry.balance_before}, After: {entry.balance_after}")

print("\n=== Seller Transactions ===")
for entry in LedgerEntry.objects.filter(user=seller).order_by('created_at'):
    print(f"{entry.transaction_type}: {entry.amount} USDT")
    print(f"  Before: {entry.balance_before}, After: {entry.balance_after}")

exit()
```

### Step 7: Test Celery Tasks
```bash
# Check Celery is running
make celery-logs

# In another terminal, trigger tasks manually
make check-deposits
make sync-balances
```

### Step 8: Access Admin Panel
```
http://localhost:8000/admin/

Login with superuser credentials created in Step 2
```

---

## Quick Test Scenarios

### Scenario 1: Deposit and Withdrawal
```python
from decimal import Decimal
from apps.users.models import User
from apps.wallets.services import WalletService

user = User.objects.get(username='buyer_test')
wallet = user.wallet

# Deposit
WalletService.process_deposit(wallet, Decimal('100'), '0x' + 'b' * 64)
print(f"After deposit: {user.balance}")

# Withdrawal (will fail on testnet without real TRX for fees)
try:
    tx_hash = WalletService.process_withdrawal(
        wallet,
        'TYourTestAddress',
        Decimal('10')
    )
    print(f"Withdrawal tx: {tx_hash}")
except Exception as e:
    print(f"Withdrawal error (expected on testnet): {e}")
```

### Scenario 2: Deal Cancellation
```python
from decimal import Decimal
from apps.users.models import User
from apps.deals.services import DealService

buyer = User.objects.get(username='buyer_test')
seller = User.objects.get(username='seller_test')

# Create and fund deal
deal = DealService.create_deal(
    buyer=buyer,
    seller=seller,
    title='Test Cancellation',
    description='Testing cancel',
    amount=Decimal('50.000000')
)

initial_balance = seller.balance
deal = DealService.fund_deal(deal)
print(f"After funding: {seller.balance}")

# Cancel and refund
deal = DealService.cancel_deal(deal, refund=True)
seller.refresh_from_db()
print(f"After cancellation: {seller.balance}")
print(f"Refunded: {seller.balance == initial_balance}")
```

### Scenario 3: Deal Dispute
```python
from decimal import Decimal
from apps.users.models import User
from apps.deals.services import DealService

buyer = User.objects.get(username='buyer_test')
seller = User.objects.get(username='seller_test')

# Create, fund, and start deal
deal = DealService.create_deal(
    buyer=buyer,
    seller=seller,
    title='Disputed Deal',
    description='Testing dispute',
    amount=Decimal('75.000000')
)
deal = DealService.fund_deal(deal)
deal = DealService.start_deal(deal)

# Create dispute
deal = DealService.dispute_deal(deal, reason='Seller did not deliver')
print(f"Deal disputed: {deal.status}")

# Resolve (admin action - release to buyer)
deal = DealService.resolve_dispute(
    deal,
    resolution='After review, buyer was correct',
    refund_to_seller=False
)
buyer.refresh_from_db()
print(f"Resolved: {deal.status}, Buyer balance: {buyer.balance}")
```

---

## Useful Commands

### Check Balances
```bash
make wallet-balance
```

### View Logs
```bash
# All logs
make logs

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery
docker-compose logs -f db
```

### Database Access
```bash
docker-compose exec db psql -U escrow_user -d escrow_db
```

### Redis Access
```bash
docker-compose exec redis redis-cli
```

### Django Shell
```bash
make shell
```

---

## API Testing with curl

### Get Balance
```bash
curl -X GET http://localhost:8000/api/v1/wallets/balance/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Deposit Address
```bash
curl -X GET http://localhost:8000/api/v1/wallets/deposit_address/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Create Deal
```bash
curl -X POST http://localhost:8000/api/v1/deals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "seller": "SELLER_USER_ID",
    "title": "Test Deal",
    "description": "Testing API",
    "amount": "50.000000"
  }'
```

---

## Troubleshooting

### Services not starting
```bash
docker-compose down
docker-compose up -d
docker-compose ps
```

### Database errors
```bash
docker-compose restart db
make migrate
```

### Celery not running
```bash
docker-compose restart celery
make celery-logs
```

### Clear all data and restart
```bash
docker-compose down -v
docker-compose up -d
make migrate
make createsuperuser
```

---

## What to Test

- [x] User and wallet creation
- [x] Deposit processing
- [x] Balance updates
- [x] Deal creation
- [x] Deal funding (seller)
- [x] Deal start (buyer)
- [x] Deal completion (buyer)
- [x] Deal cancellation
- [x] Deal dispute
- [x] Dispute resolution (admin)
- [x] Ledger entry creation
- [x] Balance synchronization
- [x] Celery tasks
- [x] Admin panel access

---

## Expected Results

### After Complete Deal Flow:
- Buyer balance increases by (amount - fee)
- Seller balance decreases by amount
- Platform collects fee
- Ledger entries created for all transactions
- Deal status transitions correctly

### Ledger Entries for Complete Deal:
1. **Seller**: ESCROW_LOCK (balance decreases)
2. **Buyer**: ESCROW_RELEASE (balance increases)
3. **Seller**: FEE (fee deducted)

---

## Next Steps

1. ✅ Complete Phase 2 testing
2. 📝 Review API documentation
3. 🔧 Implement Phase 3 (WebSockets)
4. 🎨 Build frontend (Phase 4)
5. 🔐 Add authentication (Phase 5)
6. 🚀 Deploy to production

---

## Documentation

- Full API docs: `API_DOCUMENTATION.md`
- Detailed testing: `TESTING_GUIDE.md`
- Phase 2 summary: `PHASE2_SUMMARY.md`
- Architecture: `ARCHITECTURE.md`
- Project roadmap: `TODO.md`

---

## Support

If you encounter issues:
1. Check logs: `make logs`
2. Review error messages
3. Consult `TESTING_GUIDE.md`
4. Check `TODO.md` for known issues

---

**Happy Testing! 🚀**
