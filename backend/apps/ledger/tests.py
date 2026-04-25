"""
Tests for ledger app: immutability, service methods, API endpoints.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.ledger.models import LedgerEntry
from apps.ledger.services import LedgerService
from tests.factories import UserFactory, DealFactory, LedgerEntryFactory

User = get_user_model()


# ---------------------------------------------------------------------------
# LedgerEntry Model Tests
# ---------------------------------------------------------------------------

class TestLedgerEntryModel(TestCase):
    """Tests for LedgerEntry immutability and constraints."""

    def test_create_ledger_entry(self):
        user = UserFactory()
        entry = LedgerEntryFactory(user=user)
        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.user, user)

    def test_ledger_entry_immutable_on_update(self):
        """Updating an existing entry should raise ValueError."""
        entry = LedgerEntryFactory()
        entry.amount = Decimal('999.000000')
        with self.assertRaises(ValueError, msg='Ledger entries are immutable'):
            entry.save()

    def test_ledger_entry_cannot_be_deleted(self):
        """Deleting a ledger entry should raise ValueError."""
        entry = LedgerEntryFactory()
        with self.assertRaises(ValueError, msg='Ledger entries cannot be deleted'):
            entry.delete()

    def test_ledger_entry_str(self):
        entry = LedgerEntryFactory(transaction_type='DEPOSIT', amount=Decimal('50.000000'))
        self.assertIn('DEPOSIT', str(entry))
        self.assertIn('50', str(entry))

    def test_transaction_hash_stored(self):
        tx_hash = '0x' + 'f' * 64
        entry = LedgerEntryFactory(transaction_hash=tx_hash)
        entry.refresh_from_db()
        self.assertEqual(entry.transaction_hash, tx_hash)

    def test_transaction_hash_nullable(self):
        """Escrow entries don't have blockchain hashes."""
        entry = LedgerEntryFactory(transaction_hash=None)
        entry.refresh_from_db()
        self.assertIsNone(entry.transaction_hash)


# ---------------------------------------------------------------------------
# LedgerService Tests
# ---------------------------------------------------------------------------

class TestLedgerService(TestCase):
    """Tests for LedgerService methods."""

    def setUp(self):
        self.user = UserFactory(balance=Decimal('100.000000'))

    def test_record_deposit(self):
        tx_hash = '0x' + 'a' * 64
        entry = LedgerService.record_deposit(self.user, Decimal('50.000000'), tx_hash)
        self.assertEqual(entry.transaction_type, 'DEPOSIT')
        self.assertEqual(entry.amount, Decimal('50.000000'))
        self.assertEqual(entry.transaction_hash, tx_hash)
        self.assertEqual(entry.balance_before, Decimal('50.000000'))
        self.assertEqual(entry.balance_after, Decimal('100.000000'))

    def test_record_withdrawal(self):
        tx_hash = '0x' + 'b' * 64
        to_address = 'TRecipient12345678901234567890123456'
        entry = LedgerService.record_withdrawal(
            self.user, Decimal('30.000000'), tx_hash, to_address
        )
        self.assertEqual(entry.transaction_type, 'WITHDRAWAL')
        self.assertEqual(entry.amount, Decimal('30.000000'))
        self.assertEqual(entry.transaction_hash, tx_hash)
        self.assertIn(to_address, entry.description)

    def test_record_escrow_lock(self):
        deal = DealFactory()
        entry = LedgerService.record_escrow_lock(self.user, deal, Decimal('100.000000'))
        self.assertEqual(entry.transaction_type, 'ESCROW_LOCK')
        self.assertEqual(entry.deal, deal)

    def test_record_escrow_release(self):
        deal = DealFactory()
        entry = LedgerService.record_escrow_release(self.user, deal, Decimal('97.500000'))
        self.assertEqual(entry.transaction_type, 'ESCROW_RELEASE')
        self.assertEqual(entry.amount, Decimal('97.500000'))

    def test_record_fee(self):
        deal = DealFactory()
        entry = LedgerService.record_fee(self.user, deal, Decimal('2.500000'))
        self.assertEqual(entry.transaction_type, 'FEE')
        self.assertEqual(entry.amount, Decimal('2.500000'))

    def test_record_refund(self):
        deal = DealFactory()
        entry = LedgerService.record_refund(self.user, deal, Decimal('100.000000'))
        # Refunds use ESCROW_RELEASE type
        self.assertEqual(entry.transaction_type, 'ESCROW_RELEASE')
        self.assertIn('Refund', entry.description)

    def test_duplicate_deposit_hash_raises(self):
        """Two deposits with same tx_hash should not be processed twice."""
        from apps.wallets.services import WalletService
        from apps.wallets.models import Wallet
        import uuid
        # Use a completely independent user with no wallet
        unique_id = int(str(uuid.uuid4().int)[:9])
        fresh_user = User.objects.create(
            telegram_id=unique_id,
            username=f'fresh_{unique_id}',
            balance=Decimal('0.000000')
        )
        # Check if user already has a wallet (from test isolation issues)
        if not Wallet.objects.filter(user=fresh_user).exists():
            wallet = Wallet.objects.create(
                user=fresh_user,
                address='T' + str(uuid.uuid4()).replace('-', '')[:33],
                encrypted_private_key=b'fake_key'
            )
        else:
            wallet = Wallet.objects.get(user=fresh_user)
        tx_hash = '0x' + 'c' * 64
        result1 = WalletService.process_deposit(wallet, Decimal('50.000000'), tx_hash)
        result2 = WalletService.process_deposit(wallet, Decimal('50.000000'), tx_hash)
        self.assertTrue(result1)
        self.assertFalse(result2)
        fresh_user.refresh_from_db()
        self.assertEqual(fresh_user.balance, Decimal('50.000000'))


# ---------------------------------------------------------------------------
# Ledger API Tests
# ---------------------------------------------------------------------------

class TestLedgerAPI(TestCase):
    """Tests for ledger REST API endpoints."""

    def setUp(self):
        from apps.users.tokens import create_auth_token
        self.client = APIClient()
        self.user = UserFactory()
        token = create_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_list_ledger_entries(self):
        LedgerEntryFactory(user=self.user, transaction_type='DEPOSIT')
        LedgerEntryFactory(user=self.user, transaction_type='WITHDRAWAL')
        response = self.client.get('/api/v1/ledger/')
        self.assertEqual(response.status_code, 200)

    def test_ledger_entries_filtered_to_own_user(self):
        """Users only see their own ledger entries."""
        other_user = UserFactory()
        LedgerEntryFactory(user=self.user)
        LedgerEntryFactory(user=other_user)
        response = self.client.get('/api/v1/ledger/')
        self.assertEqual(response.status_code, 200)
        # All returned entries should belong to self.user
        for entry in response.data.get('results', response.data):
            self.assertEqual(str(entry['user']), str(self.user.id))

    def test_ledger_unauthenticated_denied(self):
        self.client.credentials()
        response = self.client.get('/api/v1/ledger/')
        self.assertEqual(response.status_code, 401)
