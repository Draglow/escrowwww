"""
Wallet serializers for API responses.
"""
from rest_framework import serializers
from .models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer for Wallet model.
    NEVER expose encrypted_private_key.
    """
    
    class Meta:
        model = Wallet
        fields = [
            'id',
            'address',
            'created_at',
        ]
        read_only_fields = ['id', 'address', 'created_at']
