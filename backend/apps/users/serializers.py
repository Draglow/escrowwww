"""
User serializers for API responses.
"""
from rest_framework import serializers
from .models import User, WebAuthnCredential


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.CharField(read_only=True)
    available_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'telegram_id',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'photo_url',
            'balance',
            'available_balance',
            'is_verified',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'telegram_id',
            'balance',
            'created_at',
            'updated_at',
        ]
    
    def get_available_balance(self, obj):
        """Get available balance (excluding locked funds)."""
        return str(obj.get_available_balance())


class WebAuthnCredentialSerializer(serializers.ModelSerializer):
    """Serializer for WebAuthnCredential model (credential management)."""

    class Meta:
        model = WebAuthnCredential
        fields = [
            'id',
            'device_name',
            'aaguid',
            'created_at',
            'last_used_at',
            'is_active',
        ]
        read_only_fields = [
            'id',
            'aaguid',
            'created_at',
            'last_used_at',
            'is_active',
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """Detailed user profile serializer."""
    
    full_name = serializers.CharField(read_only=True)
    available_balance = serializers.SerializerMethodField()
    total_deals = serializers.SerializerMethodField()
    completed_deals = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'telegram_id',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'photo_url',
            'balance',
            'available_balance',
            'is_verified',
            'total_deals',
            'completed_deals',
            'created_at',
        ]
    
    def get_available_balance(self, obj):
        return str(obj.get_available_balance())
    
    def get_total_deals(self, obj):
        from apps.deals.models import Deal
        from django.db.models import Q
        return Deal.objects.filter(
            Q(buyer=obj) | Q(seller=obj)
        ).count()
    
    def get_completed_deals(self, obj):
        from apps.deals.models import Deal
        from django.db.models import Q
        return Deal.objects.filter(
            Q(buyer=obj) | Q(seller=obj),
            status='COMPLETED'
        ).count()
