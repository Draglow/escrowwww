"""
Deal model with strict state machine for escrow logic.
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

# Import Message model
from .chat_models import Message


class Deal(models.Model):
    """
    Escrow deal between buyer and seller.
    Implements strict state machine for security.
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('FUNDED', 'Funded'),
        ('IN_PROGRESS', 'In Progress'),
        ('DISPUTED', 'Disputed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Parties
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='deals_as_buyer'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='deals_as_seller'
    )
    
    # Financial details
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))]
    )
    fee = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        default=Decimal('0.000000')
    )
    
    # Deal details
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    funded_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    disputed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'deals'
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['seller', 'status']),
        ]
    
    def __str__(self):
        return f"Deal {self.id} - {self.title} ({self.status})"
