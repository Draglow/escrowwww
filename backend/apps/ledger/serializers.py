"""
Ledger serializers for API responses.
"""
from rest_framework import serializers
from .models import LedgerEntry


class LedgerEntrySerializer(serializers.ModelSerializer):
    """Serializer for LedgerEntry model."""
    
    class Meta:
        model = LedgerEntry
        fields = [
            'id',
            'user',
            'transaction_type',
            'amount',
            'balance_before',
            'balance_after',
            'description',
            'transaction_hash',
            'deal',
            'created_at',
        ]
        read_only_fields = (
            'id', 'user', 'transaction_type', 'amount', 'balance_before',
            'balance_after', 'description', 'transaction_hash', 'deal', 'created_at',
        )
