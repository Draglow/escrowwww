"""
Serializers for chat messages.
"""
from rest_framework import serializers
from .chat_models import Message


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""
    
    sender_username = serializers.CharField(source='sender.telegram_username', read_only=True)
    sender_id = serializers.UUIDField(source='sender.id', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id',
            'deal',
            'sender_id',
            'sender_username',
            'content',
            'is_read',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'sender_id', 'sender_username', 'created_at', 'updated_at']


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat messages."""
    
    class Meta:
        model = Message
        fields = ['content']
    
    def validate_content(self, value):
        """Validate message content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        
        if len(value) > 5000:
            raise serializers.ValidationError("Message content is too long (max 5000 characters).")
        
        return value.strip()
