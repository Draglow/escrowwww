"""
Deal serializers for API responses.
"""
from rest_framework import serializers
from .models import Deal
from apps.users.serializers import UserSerializer


class DealSerializer(serializers.ModelSerializer):
    """Serializer for Deal model."""
    
    buyer_info = UserSerializer(source='buyer', read_only=True)
    seller_info = UserSerializer(source='seller', read_only=True)
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Deal
        fields = [
            'id',
            'buyer',
            'seller',
            'buyer_info',
            'seller_info',
            'title',
            'description',
            'amount',
            'fee',
            'total_amount',
            'status',
            'created_at',
            'updated_at',
            'funded_at',
            'completed_at',
        ]
        read_only_fields = [
            'id',
            'fee',
            'status',
            'created_at',
            'updated_at',
            'funded_at',
            'completed_at',
        ]
    
    def get_total_amount(self, obj):
        """Calculate total amount including fee."""
        return str(obj.amount + obj.fee)


class DealCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating deals."""
    
    seller_username = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Deal
        fields = ['seller', 'seller_username', 'title', 'description', 'amount']
        extra_kwargs = {
            'seller': {'required': False},
        }
    
    def validate(self, data):
        """Resolve seller by username if seller UUID not provided."""
        from apps.users.models import User as UserModel
        
        seller_username = data.pop('seller_username', None)
        
        if not data.get('seller') and seller_username:
            # Strip leading @ if present
            seller_username = seller_username.lstrip('@')
            try:
                data['seller'] = UserModel.objects.get(username=seller_username)
            except UserModel.DoesNotExist:
                raise serializers.ValidationError(
                    {'seller_username': f'No user found with username "@{seller_username}"'}
                )
        
        if not data.get('seller'):
            raise serializers.ValidationError(
                {'seller': 'Either seller ID or seller_username is required'}
            )
        
        return data
    
    def validate_amount(self, value):
        """Validate deal amount is within limits."""
        from django.conf import settings
        
        if value < settings.MIN_DEAL_AMOUNT:
            raise serializers.ValidationError(
                f'Amount must be at least {settings.MIN_DEAL_AMOUNT} USDT'
            )
        if value > settings.MAX_DEAL_AMOUNT:
            raise serializers.ValidationError(
                f'Amount cannot exceed {settings.MAX_DEAL_AMOUNT} USDT'
            )
        return value
