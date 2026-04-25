"""
Wallet admin configuration.
"""
from django.contrib import admin
from .models import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin interface for Wallet model."""
    
    list_display = ['id', 'user', 'address', 'created_at']
    list_filter = ['created_at']
    search_fields = ['address', 'user__username', 'user__telegram_id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'encrypted_private_key']
    
    fieldsets = (
        ('Wallet Info', {
            'fields': ('id', 'user', 'address')
        }),
        ('Security', {
            'fields': ('encrypted_private_key',),
            'classes': ('collapse',),
            'description': 'NEVER expose this field'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevent wallet deletion."""
        return False
