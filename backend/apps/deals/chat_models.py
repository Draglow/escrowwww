"""
Chat message models for deal communication.
"""
import uuid
from django.db import models
from django.conf import settings


class Message(models.Model):
    """
    Chat message between buyer and seller in a deal.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    deal = models.ForeignKey(
        'deals.Deal',
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sent_messages'
    )
    
    content = models.TextField()
    
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'messages'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['deal', 'created_at']),
            models.Index(fields=['deal', 'is_read']),
        ]
    
    def __str__(self):
        return f"Message {self.id} in Deal {self.deal_id} from {self.sender.telegram_username}"
