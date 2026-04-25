"""
Wallet API views.
"""
from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Wallet
from .serializers import WalletSerializer
from .services import WalletService
from .tasks import process_withdrawal_request


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for wallet operations.
    """
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to only show current user's wallet."""
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """Get current user's wallet."""
        try:
            wallet = request.user.wallet
            serializer = self.get_serializer(wallet)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """
        Get current user's balance.
        Returns both database balance and blockchain balance.
        """
        try:
            wallet = request.user.wallet
            user = request.user
            
            # Get database balance
            db_balance = user.balance
            
            # Get blockchain balance (optional, can be slow)
            blockchain_balance = None
            if request.query_params.get('check_blockchain') == 'true':
                blockchain_balance = WalletService.get_usdt_balance(wallet.address)
            
            return Response({
                'address': wallet.address,
                'balance': str(db_balance),
                'blockchain_balance': str(blockchain_balance) if blockchain_balance else None,
                'currency': 'USDT'
            })
            
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """
        Request a withdrawal.
        
        Body:
            - to_address: Destination Tron address
            - amount: Amount to withdraw in USDT
            - totp_token: (optional) 2FA token if 2FA is enabled
        """
        try:
            from apps.users.two_factor import TwoFactorAuth
            from apps.users.audit import log_audit, get_client_ip, get_user_agent
            
            wallet = request.user.wallet
            to_address = request.data.get('to_address')
            amount_str = request.data.get('amount')
            totp_token = request.data.get('totp_token')
            
            # Validate input
            if not to_address:
                return Response(
                    {'error': 'to_address is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not amount_str:
                return Response(
                    {'error': 'amount is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate amount
            try:
                amount = Decimal(amount_str)
                if amount <= 0:
                    raise ValueError('Amount must be positive')
            except (InvalidOperation, ValueError) as e:
                return Response(
                    {'error': f'Invalid amount: {e}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate address
            if not WalletService.validate_tron_address(to_address):
                return Response(
                    {'error': 'Invalid Tron address'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check balance
            if request.user.balance < amount:
                return Response(
                    {'error': 'Insufficient balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify 2FA if enabled
            if request.user.is_2fa_enabled:
                if not totp_token:
                    return Response(
                        {'error': '2FA token is required for withdrawals'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Rate limit 2FA attempts
                allowed, remaining = TwoFactorAuth.rate_limit_2fa_attempts(request.user.id)
                if not allowed:
                    log_audit(
                        user=request.user,
                        action='WITHDRAWAL',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        details={
                            'amount': str(amount),
                            'to_address': to_address,
                            'error': 'Too many 2FA attempts'
                        },
                        success=False
                    )
                    return Response(
                        {'error': 'Too many failed 2FA attempts. Please try again later.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                
                # Verify TOTP token or backup code
                valid = False
                if TwoFactorAuth.verify_totp(request.user.totp_secret, totp_token):
                    valid = True
                elif totp_token in request.user.backup_codes:
                    valid = True
                    # Remove used backup code
                    request.user.backup_codes.remove(totp_token)
                    request.user.save(update_fields=['backup_codes'])
                
                if not valid:
                    log_audit(
                        user=request.user,
                        action='WITHDRAWAL',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        details={
                            'amount': str(amount),
                            'to_address': to_address,
                            'error': 'Invalid 2FA token'
                        },
                        success=False
                    )
                    return Response(
                        {
                            'error': 'Invalid 2FA token',
                            'remaining_attempts': remaining
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Log withdrawal request
            log_audit(
                user=request.user,
                action='WITHDRAWAL',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    'amount': str(amount),
                    'to_address': to_address
                },
                success=True
            )
            
            # Queue withdrawal task
            task = process_withdrawal_request.delay(
                wallet.id,
                to_address,
                str(amount)
            )
            
            return Response({
                'message': 'Withdrawal request submitted',
                'task_id': task.id,
                'amount': str(amount),
                'to_address': to_address
            }, status=status.HTTP_202_ACCEPTED)
            
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def deposit_address(self, request):
        """
        Get deposit address for current user.
        """
        try:
            wallet = request.user.wallet
            return Response({
                'address': wallet.address,
                'network': 'TRC20',
                'currency': 'USDT',
                'instructions': (
                    'Send USDT (TRC20) to this address. '
                    'Deposits will be credited after blockchain confirmation.'
                )
            })
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """
        Get transaction history for current user.
        """
        try:
            from apps.ledger.models import LedgerEntry
            from apps.ledger.serializers import LedgerEntrySerializer
            
            # Get ledger entries for user
            entries = LedgerEntry.objects.filter(
                user=request.user
            ).order_by('-created_at')
            
            # Pagination
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            entries = entries[offset:offset + limit]
            
            serializer = LedgerEntrySerializer(entries, many=True)
            
            return Response({
                'count': entries.count(),
                'transactions': serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
