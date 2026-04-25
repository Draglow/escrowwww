"""
Ledger admin configuration.
"""
from django.contrib import admin
from .models import LedgerEntry


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    """Admin interface for LedgerEntry model."""
    
    list_display = [
        'id',
        'user',
        'transaction_type',
        'amount',
        'balance_after',
        'deal',
        'created_at',
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'deal__id', 'description']
    readonly_fields = [
        'id',
        'user',
        'deal',
        'transaction_type',
        'amount',
        'balance_before',
        'balance_after',
        'description',
        'metadata',
        'created_at',
    ]
    
    def has_add_permission(self, request):
        """Prevent manual creation."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion."""
        return False
