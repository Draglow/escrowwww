"""
Deal service with state machine logic.
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from .models import Deal
from .websocket_utils import broadcast_deal_update, broadcast_deal_status_change

logger = logging.getLogger(__name__)


class DealService:
    """Service for deal operations with strict state machine."""
    
    @staticmethod
    def create_deal(buyer, seller, title, description, amount):
        """
        Create a new deal in DRAFT status.
        Calculate platform fee.
        """
        fee = amount * Decimal(settings.PLATFORM_FEE_PERCENTAGE) / Decimal('100')
        
        deal = Deal.objects.create(
            buyer=buyer,
            seller=seller,
            title=title,
            description=description,
            amount=amount,
            fee=fee,
            status='DRAFT'
        )
        
        logger.info(f'Created deal {deal.id} for {amount} USDT')
        return deal
    
    @staticmethod
    @transaction.atomic
    def fund_deal(deal):
        """
        Fund a deal by locking seller's balance.
        Transition: DRAFT -> FUNDED
        
        Args:
            deal: Deal instance
            
        Returns:
            Updated deal instance
            
        Raises:
            ValueError: If deal is not in DRAFT status or seller has insufficient balance
        """
        old_status = deal.status
        
        if deal.status != 'DRAFT':
            raise ValueError(f'Cannot fund deal in {deal.status} status')
        
        # Lock seller's balance using select_for_update
        seller = deal.seller
        seller = type(seller).objects.select_for_update().get(pk=seller.pk)
        
        if seller.balance < deal.amount:
            raise ValueError('Insufficient balance')
        
        # Deduct from seller balance
        seller.balance -= deal.amount
        seller.save(update_fields=['balance'])
        
        # Update deal status
        deal.status = 'FUNDED'
        deal.funded_at = timezone.now()
        deal.save(update_fields=['status', 'funded_at'])
        
        # Create ledger entry
        from apps.ledger.services import LedgerService
        LedgerService.record_escrow_lock(seller, deal, deal.amount)
        
        logger.info(f'Deal {deal.id} funded')
        
        # Broadcast WebSocket update
        broadcast_deal_status_change(deal, old_status, deal.status)
        broadcast_deal_update(deal)
        
        return deal
    
    @staticmethod
    @transaction.atomic
    def start_deal(deal):
        """
        Start a deal after both parties are ready.
        Transition: FUNDED -> IN_PROGRESS
        
        Args:
            deal: Deal instance
            
        Returns:
            Updated deal instance
            
        Raises:
            ValueError: If deal is not in FUNDED status
        """
        old_status = deal.status
        
        if deal.status != 'FUNDED':
            raise ValueError(f'Cannot start deal in {deal.status} status')
        
        # Update deal status
        deal.status = 'IN_PROGRESS'
        deal.started_at = timezone.now()
        deal.save(update_fields=['status', 'started_at'])
        
        logger.info(f'Deal {deal.id} started')
        
        # Broadcast WebSocket update
        broadcast_deal_status_change(deal, old_status, deal.status)
        broadcast_deal_update(deal)
        
        return deal
    
    @staticmethod
    @transaction.atomic
    def complete_deal(deal):
        """
        Complete a deal by releasing funds to buyer and deducting fee.
        Transition: IN_PROGRESS -> COMPLETED
        
        Args:
            deal: Deal instance
            
        Returns:
            Updated deal instance
            
        Raises:
            ValueError: If deal is not in IN_PROGRESS status
        """
        old_status = deal.status
        
        if deal.status != 'IN_PROGRESS':
            raise ValueError(f'Cannot complete deal in {deal.status} status')
        
        # Lock both users
        buyer = type(deal.buyer).objects.select_for_update().get(pk=deal.buyer.pk)
        seller = type(deal.seller).objects.select_for_update().get(pk=deal.seller.pk)
        
        # Calculate amounts
        amount_to_buyer = deal.amount - deal.fee
        
        # Release funds to buyer
        buyer.balance += amount_to_buyer
        buyer.save(update_fields=['balance'])
        
        # Update deal status
        deal.status = 'COMPLETED'
        deal.completed_at = timezone.now()
        deal.save(update_fields=['status', 'completed_at'])
        
        # Create ledger entries
        from apps.ledger.services import LedgerService
        
        # Record escrow release to buyer
        LedgerService.record_escrow_release(buyer, deal, amount_to_buyer)
        
        # Record platform fee (deducted from seller)
        LedgerService.record_fee(seller, deal, deal.fee)
        
        logger.info(f'Deal {deal.id} completed')
        
        # Broadcast WebSocket update
        broadcast_deal_status_change(deal, old_status, deal.status)
        broadcast_deal_update(deal)
        
        return deal
    
    @staticmethod
    @transaction.atomic
    def dispute_deal(deal, reason: str = None):
        """
        Dispute a deal and freeze funds.
        Transition: IN_PROGRESS -> DISPUTED
        
        Args:
            deal: Deal instance
            reason: Optional dispute reason
            
        Returns:
            Updated deal instance
            
        Raises:
            ValueError: If deal is not in IN_PROGRESS status
        """
        old_status = deal.status
        
        if deal.status != 'IN_PROGRESS':
            raise ValueError(f'Cannot dispute deal in {deal.status} status')
        
        # Update deal status
        deal.status = 'DISPUTED'
        deal.disputed_at = timezone.now()
        
        if reason:
            deal.description += f'\n\n[DISPUTE] {reason}'
        
        deal.save(update_fields=['status', 'disputed_at', 'description'])
        
        logger.warning(f'Deal {deal.id} disputed: {reason}')
        
        # TODO: Send notification to admin
        
        # Broadcast WebSocket update
        broadcast_deal_status_change(deal, old_status, deal.status)
        broadcast_deal_update(deal)
        
        return deal
    
    @staticmethod
    @transaction.atomic
    def cancel_deal(deal, refund: bool = True):
        """
        Cancel a deal and optionally refund locked funds.
        Transition: DRAFT/FUNDED/IN_PROGRESS -> CANCELLED
        
        Args:
            deal: Deal instance
            refund: Whether to refund locked funds (only if FUNDED or IN_PROGRESS)
            
        Returns:
            Updated deal instance
            
        Raises:
            ValueError: If deal is already completed or disputed
        """
        old_status = deal.status
        
        if deal.status in ['COMPLETED', 'DISPUTED']:
            raise ValueError(f'Cannot cancel deal in {deal.status} status')
        
        # Refund if deal was funded
        if refund and deal.status in ['FUNDED', 'IN_PROGRESS']:
            # Lock seller
            seller = type(deal.seller).objects.select_for_update().get(pk=deal.seller.pk)
            
            # Refund locked amount
            seller.balance += deal.amount
            seller.save(update_fields=['balance'])
            
            # Create ledger entry
            from apps.ledger.services import LedgerService
            LedgerService.record_refund(seller, deal, deal.amount)
            
            logger.info(f'Refunded {deal.amount} USDT to seller for deal {deal.id}')
        
        # Update deal status
        deal.status = 'CANCELLED'
        deal.cancelled_at = timezone.now()
        deal.save(update_fields=['status', 'cancelled_at'])
        
        logger.info(f'Deal {deal.id} cancelled')
        
        # Broadcast WebSocket update
        broadcast_deal_status_change(deal, old_status, deal.status)
        broadcast_deal_update(deal)
        
        return deal
    
    @staticmethod
    @transaction.atomic
    def resolve_dispute(deal, resolution: str, refund_to_seller: bool = False):
        """
        Resolve a disputed deal (admin action).
        Transition: DISPUTED -> COMPLETED or CANCELLED
        
        Args:
            deal: Deal instance
            resolution: Resolution description
            refund_to_seller: If True, refund to seller; otherwise release to buyer
            
        Returns:
            Updated deal instance
            
        Raises:
            ValueError: If deal is not in DISPUTED status
        """
        old_status = deal.status
        
        if deal.status != 'DISPUTED':
            raise ValueError(f'Cannot resolve deal in {deal.status} status')
        
        # Lock both users
        buyer = type(deal.buyer).objects.select_for_update().get(pk=deal.buyer.pk)
        seller = type(deal.seller).objects.select_for_update().get(pk=deal.seller.pk)
        
        from apps.ledger.services import LedgerService
        
        if refund_to_seller:
            # Refund to seller
            seller.balance += deal.amount
            seller.save(update_fields=['balance'])
            
            LedgerService.record_refund(seller, deal, deal.amount)
            
            deal.status = 'CANCELLED'
            logger.info(f'Dispute resolved: Refunded to seller for deal {deal.id}')
        else:
            # Release to buyer (minus fee)
            amount_to_buyer = deal.amount - deal.fee
            buyer.balance += amount_to_buyer
            buyer.save(update_fields=['balance'])
            
            LedgerService.record_escrow_release(buyer, deal, amount_to_buyer)
            LedgerService.record_fee(seller, deal, deal.fee)
            
            deal.status = 'COMPLETED'
            logger.info(f'Dispute resolved: Released to buyer for deal {deal.id}')
        
        # Update deal
        deal.description += f'\n\n[RESOLUTION] {resolution}'
        deal.completed_at = timezone.now()
        deal.save(update_fields=['status', 'description', 'completed_at'])
        
        # Broadcast WebSocket update
        broadcast_deal_status_change(deal, old_status, deal.status)
        broadcast_deal_update(deal)
        
        return deal
