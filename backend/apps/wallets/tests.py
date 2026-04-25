"""
Tests for wallets app: encryption, wallet creation, balance, deposit/withdrawal.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient

from apps.wallets.models import Wallet
from apps.wallets.encryption import WalletEncryption
from apps.wallets.services import WalletService
from apps.ledger.models import LedgerEntry
from tests.factories import UserFactory, WalletFactory


# ---------------------------------------------------------------------------
# Encryption Tests
# ---------------------------------------------------------------------------

class TestWalletEncryption(TestCase):
    """Tests for private key encryption/decryption."""

    def test_encrypt_decrypt_roundtrip(self):
        private_key = 'a' * 64  # 64-char hex string
        encrypted = WalletEncryption.encrypt_private_key(private_key)
        decrypted = WalletEncryption.decrypt_private_key(encrypted)
        self.assertEqual(decrypted, private_key)

    def test_encrypted_key_is_bytes(self):
        encrypted = WalletEncryption.encrypt_private_key('b' * 64)
        self.assertIsInstance(encrypted, bytes)

    def test_encrypted_key_differs_from_plaintext(self):
        private_key = 'c' * 64
        encrypted = WalletEncryption.encrypt_private_key(private_key)
        self.assertNotEqual(encrypted, private_key.encode())

    def test_different_keys_produce_different_ciphertext(self):
        key1 = 'a' * 64
        key2 = 'b' * 64
        enc1 = WalletEncryption.encrypt_private_key(key1)
        enc2 = WalletEncryption.encrypt_private_key(key2)
        self.assertNotEqual(enc1, enc2)


# ---------------------------------------------------------------------------
# Wallet Creation Tests
# ---------------------------------------------------------------------------

class TestWalletCreation(TestCase):
    """Tests for wallet creation service."""

    @patch('apps.wallets.services.PrivateKey')
    def test_create_wallet_success(self, mock_pk_class):
        """Wallet is created with encrypted key and valid address."""
        from apps.wallets.models import Wallet
        mock_private_key = MagicMock()
        mock_private_key.hex.return_value = 'a' * 64
        mock_private_key.public_key.to_base58check_address.return_value = 'TTestAddress123456789012345678901234'
        mock_pk_class.random.return_value = mock_private_key

        user = UserFactory()
        # Ensure no existing wallet
        Wallet.objects.filter(user=user).delete()
        wallet = WalletService.create_wallet(user)

        self.assertEqual(wallet.user, user)
        self.assertEqual(wallet.address, 'TTestAddress123456789012345678901234')
        self.assertIsNotNone(wallet.encrypted_private_key)

    @patch('apps.wallets.services.PrivateKey')
    def test_create_wallet_one_per_user(self, mock_pk_class):
        """OneToOne constraint: second wallet creation raises."""
        from apps.wallets.models import Wallet
        mock_private_key = MagicMock()
        mock_private_key.hex.return_value = 'a' * 64
        mock_private_key.public_key.to_base58check_address.return_value = 'TAddr1234567890123456789012345678901'
        mock_pk_class.random.return_value = mock_private_key

        user = UserFactory()
        # Ensure no existing wallet
        Wallet.objects.filter(user=user).delete()
        WalletService.create_wallet(user)

        # Second wallet for same user should raise (OneToOne constraint)
        with self.assertRaises(Exception):
            WalletService.create_wallet(user)


# ---------------------------------------------------------------------------
# Deposit Processing Tests
# ---------------------------------------------------------------------------

class TestDepositProcessing(TestCase):
    """Tests for deposit detection and processing."""

    def setUp(self):
        self.user = UserFactory(balance=Decimal('0.000000'))
        self.wallet = WalletFactory(user=self.user)

    def test_process_deposit_updates_balance(self):
        tx_hash = '0x' + 'a' * 64
        WalletService.process_deposit(self.wallet, Decimal('100.000000'), tx_hash)
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal('100.000000'))

    def test_process_deposit_creates_ledger_entry(self):
        tx_hash = '0x' + 'b' * 64
        WalletService.process_deposit(self.wallet, Decimal('50.000000'), tx_hash)
        entry = LedgerEntry.objects.get(transaction_hash=tx_hash)
        self.assertEqual(entry.transaction_type, 'DEPOSIT')
        self.assertEqual(entry.amount, Decimal('50.000000'))
        self.assertEqual(entry.user, self.user)

    def test_process_deposit_idempotent(self):
        """Same tx_hash should not be processed twice."""
        tx_hash = '0x' + 'c' * 64
        result1 = WalletService.process_deposit(self.wallet, Decimal('100.000000'), tx_hash)
        result2 = WalletService.process_deposit(self.wallet, Decimal('100.000000'), tx_hash)
        self.assertTrue(result1)
        self.assertFalse(result2)
        # Balance should only be updated once
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal('100.000000'))

    def test_process_deposit_ledger_balance_tracking(self):
        """Ledger entry records correct before/after balances."""
        tx_hash = '0x' + 'd' * 64
        WalletService.process_deposit(self.wallet, Decimal('75.000000'), tx_hash)
        entry = LedgerEntry.objects.get(transaction_hash=tx_hash)
        self.assertEqual(entry.balance_before, Decimal('0.000000'))
        self.assertEqual(entry.balance_after, Decimal('75.000000'))


# ---------------------------------------------------------------------------
# Withdrawal Processing Tests
# ---------------------------------------------------------------------------

class TestWithdrawalProcessing(TestCase):
    """Tests for withdrawal service."""

    def setUp(self):
        self.user = UserFactory(balance=Decimal('200.000000'))
        self.wallet = WalletFactory(user=self.user)

    @patch('apps.wallets.services.WalletService.get_tron_client')
    @patch('apps.wallets.services.WalletService.get_private_key')
    def test_process_withdrawal_success(self, mock_get_key, mock_get_client):
        """Successful withdrawal deducts balance and creates ledger entry."""
        mock_private_key = MagicMock()
        mock_get_key.return_value = mock_private_key

        mock_contract = MagicMock()
        mock_txn = MagicMock()
        mock_txn.broadcast.return_value = {'txid': '0x' + 'e' * 64}
        mock_contract.functions.transfer.return_value.with_owner.return_value \
            .fee_limit.return_value.build.return_value.sign.return_value = mock_txn
        mock_client = MagicMock()
        mock_client.get_contract.return_value = mock_contract
        mock_get_client.return_value = mock_client

        to_address = 'TRecipient12345678901234567890123456'
        tx_hash = WalletService.process_withdrawal(
            self.wallet, to_address, Decimal('50.000000')
        )

        self.assertEqual(tx_hash, '0x' + 'e' * 64)
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal('150.000000'))

        entry = LedgerEntry.objects.filter(
            user=self.user, transaction_type='WITHDRAWAL'
        ).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.amount, Decimal('50.000000'))

    def test_process_withdrawal_insufficient_balance(self):
        """Withdrawal with insufficient balance raises ValueError."""
        with self.assertRaises(ValueError, msg='Insufficient balance'):
            WalletService.process_withdrawal(
                self.wallet, 'TAddr1234567890123456789012345678901', Decimal('999.000000')
            )

    def test_process_withdrawal_balance_unchanged_on_error(self):
        """Balance is not changed if withdrawal fails."""
        initial_balance = self.user.balance
        try:
            WalletService.process_withdrawal(
                self.wallet, 'TAddr1234567890123456789012345678901', Decimal('999.000000')
            )
        except ValueError:
            pass
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, initial_balance)


# ---------------------------------------------------------------------------
# Wallet API Tests
# ---------------------------------------------------------------------------

class TestWalletAPI(TestCase):
    """Tests for wallet REST API endpoints."""

    def setUp(self):
        from apps.users.tokens import create_auth_token
        self.client = APIClient()
        self.user = UserFactory(balance=Decimal('100.000000'))
        self.wallet = WalletFactory(user=self.user)
        token = create_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_get_balance(self):
        response = self.client.get('/api/v1/wallets/balance/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['balance'], '100.000000')
        self.assertEqual(response.data['currency'], 'USDT')

    def test_get_deposit_address(self):
        response = self.client.get('/api/v1/wallets/deposit_address/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['address'], self.wallet.address)
        self.assertEqual(response.data['network'], 'TRC20')

    def test_get_transactions_empty(self):
        response = self.client.get('/api/v1/wallets/transactions/')
        self.assertEqual(response.status_code, 200)

    def test_get_balance_unauthenticated(self):
        self.client.credentials()
        response = self.client.get('/api/v1/wallets/balance/')
        self.assertEqual(response.status_code, 401)

    def test_withdraw_missing_address(self):
        response = self.client.post(
            '/api/v1/wallets/withdraw/',
            {'amount': '10.000000'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('to_address', response.data['error'])

    def test_withdraw_missing_amount(self):
        response = self.client.post(
            '/api/v1/wallets/withdraw/',
            {'to_address': 'TAddr1234567890123456789012345678901'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_withdraw_invalid_amount(self):
        response = self.client.post(
            '/api/v1/wallets/withdraw/',
            {'to_address': 'TAddr1234567890123456789012345678901', 'amount': 'notanumber'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_withdraw_insufficient_balance(self):
        with patch('apps.wallets.views.WalletService.validate_tron_address', return_value=True):
            response = self.client.post(
                '/api/v1/wallets/withdraw/',
                {'to_address': 'TAddr1234567890123456789012345678901', 'amount': '9999.000000'},
                format='json'
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Insufficient', response.data['error'])

    def test_withdraw_requires_2fa_when_enabled(self):
        self.user.is_2fa_enabled = True
        self.user.totp_secret = 'JBSWY3DPEHPK3PXP'
        self.user.save()
        with patch('apps.wallets.views.WalletService.validate_tron_address', return_value=True):
            response = self.client.post(
                '/api/v1/wallets/withdraw/',
                {'to_address': 'TAddr1234567890123456789012345678901', 'amount': '10.000000'},
                format='json'
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn('2FA', response.data['error'])

    def test_no_wallet_returns_404(self):
        """A user with no wallet gets 404 on balance endpoint."""
        from apps.users.tokens import create_auth_token
        from apps.wallets.models import Wallet
        user_no_wallet = UserFactory()
        # Ensure this user has no wallet
        Wallet.objects.filter(user=user_no_wallet).delete()
        token = create_auth_token(user_no_wallet)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = client.get('/api/v1/wallets/balance/')
        self.assertEqual(response.status_code, 404)
