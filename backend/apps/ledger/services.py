"""
Ledger service for recording transactions.
"""
import logging
from typing import Optional
from .models import LedgerEntry

logger = logging.getLogger(__name__)


class LedgerService:
    """Service for creating immutable ledger entries."""
    
    @staticmethod
    def record_deposit(user, amount, transaction_hash: str):
        """
        Record deposit transaction.
        
        Args:
            user: User instance
            amount: Deposit amount
            transaction_hash: Blockchain transaction hash
        """
        entry = LedgerEntry.objects.create(
            user=user,
            transaction_type='DEPOSIT',
            amount=amount,
            balance_before=user.balance - amount,
            balance_after=user.balance,
            transaction_hash=transaction_hash,
            description=f'Deposit of {amount} USDT'
        )
        logger.info(f'Recorded deposit: {entry.id} - {transaction_hash}')
        return entry
    
    @staticmethod
    def record_withdrawal(user, amount, transaction_hash: str, to_address: str):
        """
        Record withdrawal transaction.
        
        Args:
            user: User instance
            amount: Withdrawal amount
            transaction_hash: Blockchain transaction hash
            to_address: Destination address
        """
        entry = LedgerEntry.objects.create(
            user=user,
            transaction_type='WITHDRAWAL',
            amount=amount,
            balance_before=user.balance + amount,
            balance_after=user.balance,
            transaction_hash=transaction_hash,
            description=f'Withdrawal of {amount} USDT to {to_address}'
        )
        logger.info(f'Recorded withdrawal: {entry.id} - {transaction_hash}')
        return entry
    
    @staticmethod
    def record_escrow_lock(user, deal, amount):
        """Record escrow lock transaction."""
        entry = LedgerEntry.objects.create(
            user=user,
            deal=deal,
            transaction_type='ESCROW_LOCK',
            amount=amount,
            balance_before=user.balance + amount,
            balance_after=user.balance,
            description=f'Locked {amount} USDT for deal {deal.id}'
        )
        logger.info(f'Recorded escrow lock: {entry.id}')
        return entry
    
    @staticmethod
    def record_escrow_release(user, deal, amount):
        """Record escrow release transaction."""
        entry = LedgerEntry.objects.create(
            user=user,
            deal=deal,
            transaction_type='ESCROW_RELEASE',
            amount=amount,
            balance_before=user.balance - amount,
            balance_after=user.balance,
            description=f'Released {amount} USDT from deal {deal.id}'
        )
        logger.info(f'Recorded escrow release: {entry.id}')
        return entry
    
    @staticmethod
    def record_fee(user, deal, amount):
        """Record platform fee transaction."""
        entry = LedgerEntry.objects.create(
            user=user,
            deal=deal,
            transaction_type='FEE',
            amount=amount,
            balance_before=user.balance + amount,
            balance_after=user.balance,
            description=f'Platform fee for deal {deal.id}'
        )
        logger.info(f'Recorded fee: {entry.id}')
        return entry
    
    @staticmethod
    def record_refund(user, deal, amount):
        """Record refund transaction."""
        entry = LedgerEntry.objects.create(
            user=user,
            deal=deal,
            transaction_type='ESCROW_RELEASE',  # Reuse ESCROW_RELEASE for refunds
            amount=amount,
            balance_before=user.balance - amount,
            balance_after=user.balance,
            description=f'Refund of {amount} USDT from cancelled deal {deal.id}'
        )
        logger.info(f'Recorded refund: {entry.id}')
        return entry
