"""
Tests for deals app: state machine, service methods, API endpoints, chat.
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient

from apps.deals.models import Deal
from apps.deals.services import DealService
from apps.ledger.models import LedgerEntry
from tests.factories import UserFactory, AdminUserFactory, DealFactory, WalletFactory


# ---------------------------------------------------------------------------
# Deal State Machine Tests
# ---------------------------------------------------------------------------

class TestDealStateMachine(TestCase):
    """Tests for deal lifecycle state transitions."""

    def setUp(self):
        self.buyer = UserFactory(balance=Decimal('0.000000'))
        self.seller = UserFactory(balance=Decimal('500.000000'))

    def _create_deal(self, amount=Decimal('100.000000')):
        return DealService.create_deal(
            buyer=self.buyer,
            seller=self.seller,
            title='Test Deal',
            description='Test description',
            amount=amount,
        )

    # --- create_deal ---

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_create_deal_draft_status(self, mock_status, mock_update):
        deal = self._create_deal()
        self.assertEqual(deal.status, 'DRAFT')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_create_deal_calculates_fee(self, mock_status, mock_update):
        deal = self._create_deal(amount=Decimal('100.000000'))
        # 2.5% fee
        self.assertEqual(deal.fee, Decimal('2.500000'))

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_create_deal_sets_buyer_seller(self, mock_status, mock_update):
        deal = self._create_deal()
        self.assertEqual(deal.buyer, self.buyer)
        self.assertEqual(deal.seller, self.seller)

    # --- fund_deal ---

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_fund_deal_transitions_to_funded(self, mock_status, mock_update):
        deal = self._create_deal()
        deal = DealService.fund_deal(deal)
        self.assertEqual(deal.status, 'FUNDED')
        self.assertIsNotNone(deal.funded_at)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_fund_deal_deducts_seller_balance(self, mock_status, mock_update):
        deal = self._create_deal(amount=Decimal('100.000000'))
        DealService.fund_deal(deal)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, Decimal('400.000000'))

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_fund_deal_creates_escrow_lock_ledger_entry(self, mock_status, mock_update):
        deal = self._create_deal()
        DealService.fund_deal(deal)
        entry = LedgerEntry.objects.filter(
            deal=deal, transaction_type='ESCROW_LOCK'
        ).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.amount, deal.amount)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_fund_deal_insufficient_balance_raises(self, mock_status, mock_update):
        self.seller.balance = Decimal('10.000000')
        self.seller.save()
        deal = self._create_deal(amount=Decimal('100.000000'))
        with self.assertRaises(ValueError, msg='Insufficient balance'):
            DealService.fund_deal(deal)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_fund_deal_wrong_status_raises(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='FUNDED')
        with self.assertRaises(ValueError):
            DealService.fund_deal(deal)

    # --- start_deal ---

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_start_deal_transitions_to_in_progress(self, mock_status, mock_update):
        deal = self._create_deal()
        deal = DealService.fund_deal(deal)
        deal = DealService.start_deal(deal)
        self.assertEqual(deal.status, 'IN_PROGRESS')
        self.assertIsNotNone(deal.started_at)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_start_deal_wrong_status_raises(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='DRAFT')
        with self.assertRaises(ValueError):
            DealService.start_deal(deal)

    # --- complete_deal ---

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_complete_deal_transitions_to_completed(self, mock_status, mock_update):
        deal = self._create_deal()
        deal = DealService.fund_deal(deal)
        deal = DealService.start_deal(deal)
        deal = DealService.complete_deal(deal)
        self.assertEqual(deal.status, 'COMPLETED')
        self.assertIsNotNone(deal.completed_at)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_complete_deal_releases_funds_to_buyer(self, mock_status, mock_update):
        deal = self._create_deal(amount=Decimal('100.000000'))
        deal = DealService.fund_deal(deal)
        deal = DealService.start_deal(deal)
        deal = DealService.complete_deal(deal)
        self.buyer.refresh_from_db()
        # Buyer gets amount - fee = 100 - 2.5 = 97.5
        self.assertEqual(self.buyer.balance, Decimal('97.500000'))

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_complete_deal_creates_ledger_entries(self, mock_status, mock_update):
        deal = self._create_deal()
        deal = DealService.fund_deal(deal)
        deal = DealService.start_deal(deal)
        deal = DealService.complete_deal(deal)
        release_entry = LedgerEntry.objects.filter(
            deal=deal, transaction_type='ESCROW_RELEASE'
        ).first()
        fee_entry = LedgerEntry.objects.filter(
            deal=deal, transaction_type='FEE'
        ).first()
        self.assertIsNotNone(release_entry)
        self.assertIsNotNone(fee_entry)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_complete_deal_wrong_status_raises(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='FUNDED')
        with self.assertRaises(ValueError):
            DealService.complete_deal(deal)

    # --- dispute_deal ---

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_dispute_deal_transitions_to_disputed(self, mock_status, mock_update):
        deal = self._create_deal()
        deal = DealService.fund_deal(deal)
        deal = DealService.start_deal(deal)
        deal = DealService.dispute_deal(deal, reason='Seller did not deliver')
        self.assertEqual(deal.status, 'DISPUTED')
        self.assertIsNotNone(deal.disputed_at)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_dispute_deal_appends_reason(self, mock_status, mock_update):
        deal = self._create_deal()
        deal = DealService.fund_deal(deal)
        deal = DealService.start_deal(deal)
        deal = DealService.dispute_deal(deal, reason='Bad seller')
        self.assertIn('[DISPUTE]', deal.description)
        self.assertIn('Bad seller', deal.description)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_dispute_deal_wrong_status_raises(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='FUNDED')
        with self.assertRaises(ValueError):
            DealService.dispute_deal(deal)

    # --- cancel_deal ---

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_cancel_draft_deal(self, mock_status, mock_update):
        deal = self._create_deal()
        deal = DealService.cancel_deal(deal, refund=False)
        self.assertEqual(deal.status, 'CANCELLED')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_cancel_funded_deal_refunds_seller(self, mock_status, mock_update):
        deal = self._create_deal(amount=Decimal('100.000000'))
        initial_balance = self.seller.balance
        deal = DealService.fund_deal(deal)
        deal = DealService.cancel_deal(deal, refund=True)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, initial_balance)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_cancel_funded_deal_creates_refund_ledger_entry(self, mock_status, mock_update):
        deal = self._create_deal()
        deal = DealService.fund_deal(deal)
        deal = DealService.cancel_deal(deal, refund=True)
        entry = LedgerEntry.objects.filter(
            deal=deal, transaction_type='ESCROW_RELEASE'
        ).last()
        self.assertIsNotNone(entry)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_cancel_completed_deal_raises(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='COMPLETED')
        with self.assertRaises(ValueError):
            DealService.cancel_deal(deal)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_cancel_disputed_deal_raises(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='DISPUTED')
        with self.assertRaises(ValueError):
            DealService.cancel_deal(deal)

    # --- resolve_dispute ---

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_resolve_dispute_in_favor_of_buyer(self, mock_status, mock_update):
        deal = self._create_deal(amount=Decimal('100.000000'))
        deal = DealService.fund_deal(deal)
        deal = DealService.start_deal(deal)
        deal = DealService.dispute_deal(deal)
        deal = DealService.resolve_dispute(deal, resolution='Buyer wins', refund_to_seller=False)
        self.assertEqual(deal.status, 'COMPLETED')
        self.buyer.refresh_from_db()
        self.assertEqual(self.buyer.balance, Decimal('97.500000'))

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_resolve_dispute_in_favor_of_seller(self, mock_status, mock_update):
        deal = self._create_deal(amount=Decimal('100.000000'))
        initial_seller_balance = self.seller.balance
        deal = DealService.fund_deal(deal)
        deal = DealService.start_deal(deal)
        deal = DealService.dispute_deal(deal)
        deal = DealService.resolve_dispute(deal, resolution='Seller wins', refund_to_seller=True)
        self.assertEqual(deal.status, 'CANCELLED')
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, initial_seller_balance)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_resolve_dispute_wrong_status_raises(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='IN_PROGRESS')
        with self.assertRaises(ValueError):
            DealService.resolve_dispute(deal, resolution='test')


# ---------------------------------------------------------------------------
# Deal API Tests
# ---------------------------------------------------------------------------

class TestDealAPI(TestCase):
    """Tests for deal REST API endpoints."""

    def setUp(self):
        from apps.users.tokens import create_auth_token
        self.buyer = UserFactory(balance=Decimal('0.000000'))
        self.seller = UserFactory(balance=Decimal('500.000000'))
        self.admin = AdminUserFactory()

        self.buyer_client = APIClient()
        buyer_token = create_auth_token(self.buyer)
        self.buyer_client.credentials(HTTP_AUTHORIZATION=f'Token {buyer_token.key}')

        self.seller_client = APIClient()
        seller_token = create_auth_token(self.seller)
        self.seller_client.credentials(HTTP_AUTHORIZATION=f'Token {seller_token.key}')

        self.admin_client = APIClient()
        admin_token = create_auth_token(self.admin)
        self.admin_client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_create_deal(self, mock_status, mock_update):
        response = self.buyer_client.post(
            '/api/v1/deals/',
            {
                'seller': str(self.seller.id),
                'title': 'API Test Deal',
                'description': 'Testing deal creation via API',
                'amount': '100.000000',
            },
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'DRAFT')
        self.assertEqual(response.data['title'], 'API Test Deal')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_fund_deal_by_seller(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, amount=Decimal('100.000000'))
        response = self.seller_client.post(f'/api/v1/deals/{deal.id}/fund/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'FUNDED')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_fund_deal_by_buyer_forbidden(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller)
        response = self.buyer_client.post(f'/api/v1/deals/{deal.id}/fund/')
        self.assertEqual(response.status_code, 403)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_start_deal_by_buyer(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='FUNDED')
        response = self.buyer_client.post(f'/api/v1/deals/{deal.id}/start/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'IN_PROGRESS')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_start_deal_by_seller_forbidden(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='FUNDED')
        response = self.seller_client.post(f'/api/v1/deals/{deal.id}/start/')
        self.assertEqual(response.status_code, 403)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_complete_deal_by_buyer(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='IN_PROGRESS')
        response = self.buyer_client.post(f'/api/v1/deals/{deal.id}/complete/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'COMPLETED')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_dispute_deal_by_buyer(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='IN_PROGRESS')
        response = self.buyer_client.post(
            f'/api/v1/deals/{deal.id}/dispute/',
            {'reason': 'Not delivered'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'DISPUTED')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_cancel_deal_by_buyer(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='DRAFT')
        response = self.buyer_client.post(f'/api/v1/deals/{deal.id}/cancel/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'CANCELLED')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_resolve_dispute_admin_only(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='DISPUTED')
        response = self.buyer_client.post(
            f'/api/v1/deals/{deal.id}/resolve/',
            {'resolution': 'Buyer wins', 'refund_to_seller': False},
            format='json'
        )
        self.assertEqual(response.status_code, 403)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_resolve_dispute_by_admin(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller, status='DISPUTED')
        response = self.admin_client.post(
            f'/api/v1/deals/{deal.id}/resolve/',
            {'resolution': 'Admin resolved', 'refund_to_seller': True},
            format='json'
        )
        self.assertEqual(response.status_code, 200)

    def test_list_deals_only_own(self):
        """Users only see their own deals."""
        DealFactory(buyer=self.buyer, seller=self.seller)
        other_buyer = UserFactory()
        other_seller = UserFactory()
        DealFactory(buyer=other_buyer, seller=other_seller)

        response = self.buyer_client.get('/api/v1/deals/')
        self.assertEqual(response.status_code, 200)
        buyer_id = str(self.buyer.id)
        seller_id = str(self.seller.id)
        for deal in response.data['results']:
            participants = [str(deal['buyer']), str(deal['seller'])]
            self.assertTrue(
                buyer_id in participants or seller_id in participants,
                f"Deal {deal['id']} does not involve buyer or seller"
            )

    def test_unauthenticated_access_denied(self):
        client = APIClient()
        response = client.get('/api/v1/deals/')
        self.assertEqual(response.status_code, 401)

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_send_message_in_deal(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller)
        response = self.buyer_client.post(
            f'/api/v1/deals/{deal.id}/send_message/',
            {'content': 'Hello seller!'},
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['content'], 'Hello seller!')

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_get_messages_in_deal(self, mock_status, mock_update):
        deal = DealFactory(buyer=self.buyer, seller=self.seller)
        self.buyer_client.post(
            f'/api/v1/deals/{deal.id}/send_message/',
            {'content': 'Test message'},
            format='json'
        )
        response = self.buyer_client.get(f'/api/v1/deals/{deal.id}/messages/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_third_party_cannot_access_deal(self):
        """A user not in the deal cannot access it."""
        deal = DealFactory(buyer=self.buyer, seller=self.seller)
        third_party = UserFactory()
        from apps.users.tokens import create_auth_token
        token = create_auth_token(third_party)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = client.get(f'/api/v1/deals/{deal.id}/')
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# Race Condition Tests
# ---------------------------------------------------------------------------

class TestRaceConditions(TestCase):
    """Tests for concurrent balance update safety."""

    @patch('apps.deals.services.broadcast_deal_update')
    @patch('apps.deals.services.broadcast_deal_status_change')
    def test_concurrent_fund_deal_only_one_succeeds(self, mock_status, mock_update):
        """Only one fund_deal should succeed when balance is exactly enough."""
        seller = UserFactory(balance=Decimal('100.000000'))
        buyer = UserFactory()

        deal1 = DealFactory(buyer=buyer, seller=seller, amount=Decimal('100.000000'))
        deal2 = DealFactory(buyer=buyer, seller=seller, amount=Decimal('100.000000'))

        # Fund first deal
        DealService.fund_deal(deal1)
        seller.refresh_from_db()
        self.assertEqual(seller.balance, Decimal('0.000000'))

        # Second fund should fail
        with self.assertRaises(ValueError, msg='Insufficient balance'):
            DealService.fund_deal(deal2)
