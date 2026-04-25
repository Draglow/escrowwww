"""
Immutable ledger for all financial transactions.
"""
import uuid
from django.db import models
from django.conf import settings
from decimal import Decimal


class LedgerEntry(models.Model):
    """
    Immutable transaction history.
    Records all balance changes for audit trail.
    """
    
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('ESCROW_LOCK', 'Escrow Lock'),
        ('ESCROW_RELEASE', 'Escrow Release'),
        ('FEE', 'Platform Fee'),
        ('REFUND', 'Refund'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User and deal references
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ledger_entries'
    )
    deal = models.ForeignKey(
        'deals.Deal',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ledger_entries'
    )
    
    # Transaction details
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        db_index=True
    )
    amount = models.DecimalField(max_digits=20, decimal_places=6)
    balance_before = models.DecimalField(max_digits=20, decimal_places=6)
    balance_after = models.DecimalField(max_digits=20, decimal_places=6)
    
    # Blockchain transaction hash (for deposits/withdrawals)
    transaction_hash = models.CharField(max_length=128, blank=True, null=True, db_index=True)

    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamp (immutable)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'ledger_entries'
        verbose_name = 'Ledger Entry'
        verbose_name_plural = 'Ledger Entries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['deal', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['transaction_hash']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} USDT"
    
    def save(self, *args, **kwargs):
        """Prevent updates to existing entries (only allow initial creation)."""
        if self.pk and LedgerEntry.objects.filter(pk=self.pk).exists():
            raise ValueError('Ledger entries are immutable')
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of ledger entries."""
        raise ValueError('Ledger entries cannot be deleted')
