"""
User admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, WebAuthnCredential
from .audit import AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = [
        'id',
        'telegram_id',
        'username',
        'full_name',
        'balance',
        'is_2fa_enabled',
        'is_verified',
        'is_active',
        'created_at',
    ]
    list_filter = ['is_active', 'is_verified', 'is_staff', 'is_2fa_enabled', 'created_at']
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Telegram Info', {
            'fields': ('telegram_id', 'username', 'first_name', 'last_name', 'photo_url')
        }),
        ('Balance', {
            'fields': ('balance',)
        }),
        ('Security', {
            'fields': ('is_2fa_enabled', 'totp_secret', 'backup_codes')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'last_login')
        }),
    )
    
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
    
    # Remove password-related fields
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('telegram_id', 'username', 'first_name', 'last_name'),
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""
    
    list_display = [
        'id',
        'user',
        'action',
        'ip_address',
        'success',
        'created_at',
    ]
    list_filter = ['action', 'success', 'created_at']
    search_fields = ['user__username', 'user__telegram_id', 'ip_address', 'action']
    ordering = ['-created_at']
    readonly_fields = ['id', 'user', 'action', 'ip_address', 'user_agent', 'details', 'success', 'created_at']
    
    def has_add_permission(self, request):
        """Disable adding audit logs manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit logs."""
        return request.user.is_superuser


@admin.register(WebAuthnCredential)
class WebAuthnCredentialAdmin(admin.ModelAdmin):
    """Admin interface for WebAuthnCredential model."""

    list_display = [
        'id',
        'user',
        'device_name',
        'aaguid',
        'sign_count',
        'is_active',
        'created_at',
        'last_used_at',
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__telegram_id', 'device_name']
    ordering = ['-created_at']
    readonly_fields = ['id', 'user', 'credential_id', 'public_key', 'sign_count', 'aaguid', 'created_at', 'last_used_at']

    def has_add_permission(self, request):
        """Credentials are created via the WebAuthn ceremony, not manually."""
        return False
