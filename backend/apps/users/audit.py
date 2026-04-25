"""
Audit logging for security-sensitive operations.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class AuditLog(models.Model):
    """
    Audit log for tracking security-sensitive operations.
    """
    
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('WITHDRAWAL', 'Withdrawal Request'),
        ('WITHDRAWAL_APPROVED', 'Withdrawal Approved'),
        ('WITHDRAWAL_REJECTED', 'Withdrawal Rejected'),
        ('DEAL_CREATED', 'Deal Created'),
        ('DEAL_FUNDED', 'Deal Funded'),
        ('DEAL_COMPLETED', 'Deal Completed'),
        ('DEAL_DISPUTED', 'Deal Disputed'),
        ('DEAL_CANCELLED', 'Deal Cancelled'),
        ('PROFILE_UPDATED', 'Profile Updated'),
        ('PASSWORD_CHANGED', 'Password Changed'),
        ('2FA_ENABLED', '2FA Enabled'),
        ('2FA_DISABLED', '2FA Disabled'),
        ('ADMIN_ACTION', 'Admin Action'),
        ('PASSKEY_LOGIN', 'Passkey Login'),
        ('PASSKEY_REGISTERED', 'Passkey Registered'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    user_agent = models.TextField(blank=True, null=True)
    
    details = models.JSONField(default=dict, blank=True)
    
    success = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"


def log_audit(user, action, ip_address=None, user_agent=None, details=None, success=True):
    """
    Create an audit log entry.
    
    Args:
        user: User instance or None
        action: Action type (from ACTION_CHOICES)
        ip_address: IP address string
        user_agent: User agent string
        details: Additional details dict
        success: Whether the action was successful
    """
    AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
        success=success
    )


def get_client_ip(request):
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
        
    Returns:
        IP address string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    Get user agent from request.
    
    Args:
        request: Django request object
        
    Returns:
        User agent string
    """
    return request.META.get('HTTP_USER_AGENT', '')
