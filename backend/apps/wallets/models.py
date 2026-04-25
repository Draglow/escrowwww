"""
Wallet model for storing user TRC20 addresses and encrypted private keys.
"""
import uuid
from django.db import models
from django.conf import settings


class Wallet(models.Model):
    """
    Custodial wallet for each user.
    Stores TRC20 address and encrypted private key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # TRC20 address (Tron)
    address = models.CharField(max_length=42, unique=True, db_index=True)
    
    # Encrypted private key (NEVER expose this in API)
    encrypted_private_key = models.BinaryField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
        indexes = [
            models.Index(fields=['address']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Wallet {self.address[:8]}... for {self.user}"
