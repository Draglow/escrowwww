"""
User model with Telegram authentication support.
"""
import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class UserManager(BaseUserManager):
    """Custom user manager for Telegram-based authentication."""
    
    def create_user(self, telegram_id, **extra_fields):
        """Create and save a regular user."""
        if not telegram_id:
            raise ValueError('The Telegram ID must be set')
        
        user = self.model(telegram_id=telegram_id, **extra_fields)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, telegram_id, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(telegram_id, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with Telegram authentication.
    Stores user balance and profile information.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)
    
    # Balance with high precision for USDT
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        default=Decimal('0.000000'),
        validators=[MinValueValidator(Decimal('0.000000'))]
    )
    
    # WebAuthn credentials (stored as JSON)
    webauthn_credentials = models.JSONField(default=list, blank=True)
    
    # Two-Factor Authentication
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    is_2fa_enabled = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list, blank=True)
    
    # User status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'telegram_id'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.username or self.telegram_id} ({self.id})"
    
    @property
    def full_name(self):
        """Return the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username or str(self.telegram_id)
    
    def get_available_balance(self):
        """
        Calculate available balance (total balance minus locked funds in active deals).
        """
        from apps.deals.models import Deal
        
        locked_as_seller = Deal.objects.filter(
            seller=self,
            status__in=['FUNDED', 'IN_PROGRESS', 'DISPUTED']
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.000000')
        
        return self.balance - locked_as_seller


class WebAuthnCredential(models.Model):
    """
    Stores a single WebAuthn (Passkey) credential for a user.

    Replaces the deprecated `webauthn_credentials` JSONField on User.
    The JSONField is kept in place for migration compatibility but is no
    longer written to by new code.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webauthn_credentials_set',
    )
    credential_id = models.BinaryField(unique=True, db_index=True)
    public_key = models.BinaryField()
    sign_count = models.PositiveIntegerField(default=0)
    device_name = models.CharField(max_length=100, blank=True, null=True)
    aaguid = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'webauthn_credentials'
        verbose_name = 'WebAuthn Credential'
        verbose_name_plural = 'WebAuthn Credentials'
        indexes = [
            models.Index(fields=['user', '-created_at'], name='webauthn_cred_user_created_idx'),
        ]

    def __str__(self):
        name = self.device_name or 'Unnamed device'
        return f"{name} ({self.user})"
