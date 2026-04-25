"""
Wallet service for creating and managing Tron wallets.
"""
import logging
from decimal import Decimal
from typing import Optional, Dict, List
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.exceptions import TransactionError, ValidationError as TronValidationError
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Wallet
from .encryption import WalletEncryption

logger = logging.getLogger(__name__)


class WalletService:
    """Service for wallet operations."""
    
    # USDT TRC20 contract address
    USDT_CONTRACT = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'  # Mainnet
    USDT_CONTRACT_TESTNET = 'TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf'  # Nile testnet
    
    @staticmethod
    def get_tron_client():
        """Get Tron client instance."""
        if settings.TRON_NETWORK == 'mainnet':
            return Tron(network='mainnet')
        else:
            return Tron(network='nile')  # Testnet
    
    @staticmethod
    def get_usdt_contract_address():
        """Get USDT contract address based on network."""
        if settings.TRON_NETWORK == 'mainnet':
            return WalletService.USDT_CONTRACT
        else:
            return WalletService.USDT_CONTRACT_TESTNET
    
    @staticmethod
    def create_wallet(user):
        """
        Create a new Tron wallet for a user.
        
        Args:
            user: User instance
            
        Returns:
            Wallet instance
        """
        try:
            # Generate new private key
            private_key = PrivateKey.random()
            address = private_key.public_key.to_base58check_address()
            
            # Encrypt private key
            encrypted_key = WalletEncryption.encrypt_private_key(
                private_key.hex()
            )
            
            # Create wallet record
            wallet = Wallet.objects.create(
                user=user,
                address=address,
                encrypted_private_key=encrypted_key
            )
            
            logger.info(f'Created wallet {address} for user {user.id}')
            return wallet
            
        except Exception as e:
            logger.error(f'Failed to create wallet for user {user.id}: {e}')
            raise
    
    @staticmethod
    def get_private_key(wallet):
        """
        Decrypt and return wallet private key.
        SECURITY: Only use internally, never expose via API.
        
        Args:
            wallet: Wallet instance
            
        Returns:
            PrivateKey instance
        """
        decrypted_hex = WalletEncryption.decrypt_private_key(
            wallet.encrypted_private_key
        )
        return PrivateKey(bytes.fromhex(decrypted_hex))
    
    @staticmethod
    def get_usdt_balance(address: str) -> Decimal:
        """
        Get USDT TRC20 balance for an address.
        
        Args:
            address: Tron address
            
        Returns:
            Balance in USDT (Decimal)
        """
        try:
            client = WalletService.get_tron_client()
            contract_address = WalletService.get_usdt_contract_address()
            
            # Get TRC20 contract
            contract = client.get_contract(contract_address)
            
            # Call balanceOf function
            balance = contract.functions.balanceOf(address)
            
            # USDT has 6 decimals
            balance_usdt = Decimal(balance) / Decimal('1000000')
            
            logger.info(f'Balance for {address}: {balance_usdt} USDT')
            return balance_usdt
            
        except Exception as e:
            logger.error(f'Failed to get balance for {address}: {e}')
            return Decimal('0')
    
    @staticmethod
    def get_trc20_transactions(address: str, limit: int = 50) -> List[Dict]:
        """
        Get TRC20 transactions for an address.
        
        Args:
            address: Tron address
            limit: Maximum number of transactions to fetch
            
        Returns:
            List of transaction dictionaries
        """
        try:
            client = WalletService.get_tron_client()
            contract_address = WalletService.get_usdt_contract_address()
            
            # Use TronGrid API to get TRC20 transfers
            # Note: This requires TronGrid API key in production
            url = f'https://api.trongrid.io/v1/accounts/{address}/transactions/trc20'
            params = {
                'limit': limit,
                'contract_address': contract_address
            }
            
            import requests
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                logger.error(f'TronGrid API error: {response.status_code}')
                return []
                
        except Exception as e:
            logger.error(f'Failed to get transactions for {address}: {e}')
            return []
    
    @staticmethod
    @transaction.atomic
    def process_deposit(wallet: Wallet, amount: Decimal, tx_hash: str) -> bool:
        """
        Process a deposit transaction.
        Updates user balance and creates ledger entry.
        
        Args:
            wallet: Wallet instance
            amount: Deposit amount in USDT
            tx_hash: Transaction hash
            
        Returns:
            True if successful
        """
        try:
            # Check if transaction already processed
            from apps.ledger.models import LedgerEntry
            if LedgerEntry.objects.filter(
                transaction_hash=tx_hash,
                transaction_type='DEPOSIT'
            ).exists():
                logger.warning(f'Deposit {tx_hash} already processed')
                return False
            
            # Lock user record
            user = wallet.user
            user = type(user).objects.select_for_update().get(pk=user.pk)
            
            # Update balance
            user.balance += amount
            user.save(update_fields=['balance'])
            
            # Create ledger entry
            from apps.ledger.services import LedgerService
            LedgerService.record_deposit(user, amount, tx_hash)
            
            logger.info(f'Processed deposit of {amount} USDT for user {user.id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to process deposit {tx_hash}: {e}')
            raise
    
    @staticmethod
    @transaction.atomic
    def process_withdrawal(wallet: Wallet, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Process a withdrawal request.
        Signs and broadcasts transaction, updates balance.
        
        Args:
            wallet: Wallet instance
            to_address: Destination address
            amount: Withdrawal amount in USDT
            
        Returns:
            Transaction hash if successful, None otherwise
        """
        try:
            user = wallet.user
            
            # Lock user record
            user = type(user).objects.select_for_update().get(pk=user.pk)
            
            # Validate balance
            if user.balance < amount:
                raise ValueError('Insufficient balance')
            
            # Get Tron client and contract
            client = WalletService.get_tron_client()
            contract_address = WalletService.get_usdt_contract_address()
            contract = client.get_contract(contract_address)
            
            # Get private key
            private_key = WalletService.get_private_key(wallet)
            
            # Convert amount to contract units (6 decimals)
            amount_units = int(amount * Decimal('1000000'))
            
            # Build transaction
            txn = (
                contract.functions.transfer(to_address, amount_units)
                .with_owner(wallet.address)
                .fee_limit(50_000_000)  # 50 TRX fee limit
                .build()
                .sign(private_key)
            )
            
            # Broadcast transaction
            result = txn.broadcast()
            tx_hash = result.get('txid')
            
            if not tx_hash:
                raise TransactionError('Failed to broadcast transaction')
            
            # Wait for confirmation (optional, can be done async)
            # result = txn.wait()
            
            # Update balance
            user.balance -= amount
            user.save(update_fields=['balance'])
            
            # Create ledger entry
            from apps.ledger.services import LedgerService
            LedgerService.record_withdrawal(user, amount, tx_hash, to_address)
            
            logger.info(f'Processed withdrawal of {amount} USDT for user {user.id}')
            return tx_hash
            
        except ValueError as e:
            logger.warning(f'Withdrawal validation failed: {e}')
            raise
        except (TransactionError, TronValidationError) as e:
            logger.error(f'Blockchain transaction failed: {e}')
            raise
        except Exception as e:
            logger.error(f'Failed to process withdrawal: {e}')
            raise
    
    @staticmethod
    def validate_tron_address(address: str) -> bool:
        """
        Validate a Tron address format.
        
        Args:
            address: Address to validate
            
        Returns:
            True if valid
        """
        try:
            client = WalletService.get_tron_client()
            # Try to convert to hex - will raise exception if invalid
            client.to_hex_address(address)
            return True
        except Exception:
            return False
    
    @staticmethod
    @transaction.atomic
    def sync_wallet_balance(wallet: Wallet) -> Dict:
        """
        Synchronize wallet balance with blockchain.
        Detects discrepancies and creates reconciliation report.
        
        Args:
            wallet: Wallet instance
            
        Returns:
            Dictionary with sync results
        """
        try:
            # Get blockchain balance
            blockchain_balance = WalletService.get_usdt_balance(wallet.address)
            
            # Get database balance
            user = wallet.user
            db_balance = user.balance
            
            # Calculate difference
            difference = blockchain_balance - db_balance
            
            result = {
                'wallet_address': wallet.address,
                'blockchain_balance': str(blockchain_balance),
                'database_balance': str(db_balance),
                'difference': str(difference),
                'synced_at': timezone.now().isoformat(),
                'status': 'ok' if difference == 0 else 'discrepancy'
            }
            
            if difference != 0:
                logger.warning(
                    f'Balance discrepancy for wallet {wallet.address}: '
                    f'Blockchain={blockchain_balance}, DB={db_balance}, '
                    f'Diff={difference}'
                )
            
            return result
            
        except Exception as e:
            logger.error(f'Failed to sync wallet {wallet.address}: {e}')
            return {
                'wallet_address': wallet.address,
                'status': 'error',
                'error': str(e)
            }
