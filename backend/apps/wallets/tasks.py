"""
Celery tasks for wallet and blockchain operations.
"""
import logging
from decimal import Decimal
from typing import List, Dict
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from .models import Wallet
from .services import WalletService
from apps.ledger.models import LedgerEntry

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def monitor_deposits(self):
    """
    Monitor all wallets for incoming USDT deposits.
    Runs periodically (e.g., every 30 seconds).
    """
    try:
        logger.info('Starting deposit monitoring task')
        
        wallets = Wallet.objects.select_related('user').all()
        deposits_found = 0
        
        for wallet in wallets:
            try:
                # Get recent transactions
                transactions = WalletService.get_trc20_transactions(
                    wallet.address,
                    limit=20
                )
                
                for tx in transactions:
                    # Check if transaction is incoming
                    if tx.get('to') != wallet.address:
                        continue
                    
                    tx_hash = tx.get('transaction_id')
                    
                    # Check if already processed
                    if LedgerEntry.objects.filter(
                        transaction_hash=tx_hash,
                        transaction_type='DEPOSIT'
                    ).exists():
                        continue
                    
                    # Get amount (convert from contract units)
                    amount_raw = tx.get('value', '0')
                    amount = Decimal(amount_raw) / Decimal('1000000')
                    
                    # Verify transaction is confirmed
                    confirmed = tx.get('confirmed', False)
                    if not confirmed:
                        logger.info(f'Transaction {tx_hash} not yet confirmed')
                        continue
                    
                    # Process deposit
                    logger.info(
                        f'Found deposit: {amount} USDT to {wallet.address} '
                        f'(tx: {tx_hash})'
                    )
                    
                    WalletService.process_deposit(wallet, amount, tx_hash)
                    deposits_found += 1
                    
            except Exception as e:
                logger.error(f'Error processing wallet {wallet.address}: {e}')
                continue
        
        logger.info(f'Deposit monitoring completed. Found {deposits_found} new deposits')
        return {
            'status': 'success',
            'deposits_found': deposits_found,
            'wallets_checked': wallets.count()
        }
        
    except Exception as exc:
        logger.error(f'Deposit monitoring task failed: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_withdrawal_request(self, wallet_id: int, to_address: str, amount: str):
    """
    Process a withdrawal request.
    
    Args:
        wallet_id: Wallet ID
        to_address: Destination address
        amount: Amount to withdraw (as string to preserve precision)
    """
    try:
        logger.info(f'Processing withdrawal: {amount} USDT to {to_address}')
        
        wallet = Wallet.objects.select_related('user').get(id=wallet_id)
        amount_decimal = Decimal(amount)
        
        # Validate address
        if not WalletService.validate_tron_address(to_address):
            raise ValueError(f'Invalid Tron address: {to_address}')
        
        # Process withdrawal
        tx_hash = WalletService.process_withdrawal(
            wallet,
            to_address,
            amount_decimal
        )
        
        logger.info(f'Withdrawal successful: {tx_hash}')
        return {
            'status': 'success',
            'tx_hash': tx_hash,
            'amount': str(amount_decimal),
            'to_address': to_address
        }
        
    except ValueError as e:
        logger.error(f'Withdrawal validation failed: {e}')
        return {
            'status': 'error',
            'error': str(e)
        }
    except Exception as exc:
        logger.error(f'Withdrawal processing failed: {exc}')
        # Retry on blockchain errors
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def sync_wallet_balances(self):
    """
    Synchronize all wallet balances with blockchain.
    Runs periodically (e.g., every hour) to detect discrepancies.
    """
    try:
        logger.info('Starting wallet balance synchronization')
        
        wallets = Wallet.objects.select_related('user').all()
        results = []
        discrepancies = []
        
        for wallet in wallets:
            try:
                result = WalletService.sync_wallet_balance(wallet)
                results.append(result)
                
                if result.get('status') == 'discrepancy':
                    discrepancies.append(result)
                    
            except Exception as e:
                logger.error(f'Error syncing wallet {wallet.address}: {e}')
                results.append({
                    'wallet_address': wallet.address,
                    'status': 'error',
                    'error': str(e)
                })
        
        logger.info(
            f'Balance sync completed. '
            f'Checked: {len(results)}, Discrepancies: {len(discrepancies)}'
        )
        
        # Alert if discrepancies found
        if discrepancies:
            logger.warning(f'Found {len(discrepancies)} balance discrepancies!')
            # TODO: Send alert to admin (email, Telegram, etc.)
        
        return {
            'status': 'success',
            'wallets_checked': len(results),
            'discrepancies_found': len(discrepancies),
            'discrepancies': discrepancies
        }
        
    except Exception as exc:
        logger.error(f'Balance sync task failed: {exc}')
        raise self.retry(exc=exc)


@shared_task
def check_pending_withdrawals():
    """
    Check status of pending withdrawal transactions.
    Verifies if transactions have been confirmed on blockchain.
    """
    try:
        logger.info('Checking pending withdrawals')
        
        # Get recent withdrawal ledger entries
        pending_withdrawals = LedgerEntry.objects.filter(
            transaction_type='WITHDRAWAL',
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).select_related('user')
        
        confirmed = 0
        failed = 0
        
        for entry in pending_withdrawals:
            try:
                # TODO: Check transaction status on blockchain
                # For now, we assume transactions are confirmed after creation
                # In production, implement actual blockchain verification
                pass
                
            except Exception as e:
                logger.error(f'Error checking withdrawal {entry.id}: {e}')
                failed += 1
        
        logger.info(
            f'Pending withdrawals check completed. '
            f'Confirmed: {confirmed}, Failed: {failed}'
        )
        
        return {
            'status': 'success',
            'checked': pending_withdrawals.count(),
            'confirmed': confirmed,
            'failed': failed
        }
        
    except Exception as e:
        logger.error(f'Check pending withdrawals task failed: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task
def generate_wallet_report():
    """
    Generate daily wallet and transaction report.
    Useful for monitoring and auditing.
    """
    try:
        logger.info('Generating wallet report')
        
        from django.db.models import Sum, Count
        
        # Get statistics
        total_wallets = Wallet.objects.count()
        total_balance = Wallet.objects.aggregate(
            total=Sum('user__balance')
        )['total'] or Decimal('0')
        
        # Get transaction counts
        today = timezone.now().date()
        today_start = timezone.datetime.combine(
            today,
            timezone.datetime.min.time()
        )
        
        deposits_today = LedgerEntry.objects.filter(
            transaction_type='DEPOSIT',
            created_at__gte=today_start
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        withdrawals_today = LedgerEntry.objects.filter(
            transaction_type='WITHDRAWAL',
            created_at__gte=today_start
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        report = {
            'date': today.isoformat(),
            'total_wallets': total_wallets,
            'total_balance': str(total_balance),
            'deposits_today': {
                'count': deposits_today['count'] or 0,
                'total': str(deposits_today['total'] or Decimal('0'))
            },
            'withdrawals_today': {
                'count': withdrawals_today['count'] or 0,
                'total': str(withdrawals_today['total'] or Decimal('0'))
            }
        }
        
        logger.info(f'Wallet report generated: {report}')
        
        # TODO: Send report to admin (email, store in database, etc.)
        
        return report
        
    except Exception as e:
        logger.error(f'Generate wallet report task failed: {e}')
        return {'status': 'error', 'error': str(e)}
