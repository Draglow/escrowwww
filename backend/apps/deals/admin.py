"""
Deal admin configuration.
"""
from django.contrib import admin
from .models import Deal
from .chat_models import Message


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    """Admin interface for Deal model."""
    
    list_display = [
        'id',
        'title',
        'buyer',
        'seller',
        'amount',
        'fee',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'title',
        'buyer__username',
        'seller__username',
        'id',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'funded_at',
        'started_at',
        'completed_at',
        'disputed_at',
        'cancelled_at',
    ]
    
    fieldsets = (
        ('Deal Info', {
            'fields': ('id', 'title', 'description', 'status')
        }),
        ('Parties', {
            'fields': ('buyer', 'seller')
        }),
        ('Financial', {
            'fields': ('amount', 'fee')
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'funded_at',
                'started_at',
                'completed_at',
                'disputed_at',
                'cancelled_at',
            )
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Message model."""
    
    list_display = [
        'id',
        'deal',
        'sender',
        'content_preview',
        'is_read',
        'created_at',
    ]
    list_filter = ['is_read', 'created_at']
    search_fields = [
        'id',
        'deal__id',
        'sender__telegram_username',
        'content',
    ]
    readonly_fields = [
        'id',
        'deal',
        'sender',
        'content',
        'created_at',
        'updated_at',
    ]
    
    def content_preview(self, obj):
        """Show preview of message content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
