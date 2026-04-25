"""
WebSocket consumers for real-time deal updates and chat.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Deal
from .chat_models import Message

logger = logging.getLogger(__name__)
User = get_user_model()


class DealConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time deal status updates.
    Users can subscribe to a specific deal to receive updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.deal_id = self.scope['url_route']['kwargs']['deal_id']
        self.deal_group_name = f'deal_{self.deal_id}'
        self.user = self.scope.get('user')
        
        # Verify user is authenticated
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Verify user is part of the deal
        is_participant = await self.is_deal_participant()
        if not is_participant:
            await self.close(code=4003)
            return
        
        # Join deal group
        await self.channel_layer.group_add(
            self.deal_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current deal status
        deal_data = await self.get_deal_data()
        await self.send(text_data=json.dumps({
            'type': 'deal.status',
            'data': deal_data
        }))
        
        logger.info(f"User {self.user.id} connected to deal {self.deal_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'deal_group_name'):
            await self.channel_layer.group_discard(
                self.deal_group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.id} disconnected from deal {self.deal_id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def deal_update(self, event):
        """Handle deal update events from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'deal.update',
            'data': event['data']
        }))
    
    async def deal_status_changed(self, event):
        """Handle deal status change events."""
        await self.send(text_data=json.dumps({
            'type': 'deal.status_changed',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def is_deal_participant(self):
        """Check if user is buyer or seller of the deal."""
        try:
            deal = Deal.objects.get(id=self.deal_id)
            return deal.buyer_id == self.user.id or deal.seller_id == self.user.id
        except Deal.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_deal_data(self):
        """Get current deal data."""
        try:
            deal = Deal.objects.select_related('buyer', 'seller').get(id=self.deal_id)
            return {
                'id': str(deal.id),
                'title': deal.title,
                'amount': str(deal.amount),
                'fee': str(deal.fee),
                'status': deal.status,
                'buyer': {
                    'id': str(deal.buyer.id),
                    'telegram_username': deal.buyer.telegram_username,
                },
                'seller': {
                    'id': str(deal.seller.id),
                    'telegram_username': deal.seller.telegram_username,
                },
                'created_at': deal.created_at.isoformat(),
                'updated_at': deal.updated_at.isoformat(),
            }
        except Deal.DoesNotExist:
            return None


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat between buyer and seller.
    Includes typing indicators and read receipts.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.deal_id = self.scope['url_route']['kwargs']['deal_id']
        self.chat_group_name = f'chat_{self.deal_id}'
        self.user = self.scope.get('user')
        
        # Verify user is authenticated
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Verify user is part of the deal
        is_participant = await self.is_deal_participant()
        if not is_participant:
            await self.close(code=4003)
            return
        
        # Join chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_joined',
                'user_id': str(self.user.id),
                'username': self.user.telegram_username,
            }
        )
        
        logger.info(f"User {self.user.id} connected to chat for deal {self.deal_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'chat_group_name'):
            # Notify others that user left
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'user_left',
                    'user_id': str(self.user.id),
                    'username': self.user.telegram_username,
                }
            )
            
            await self.channel_layer.group_discard(
                self.chat_group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.id} disconnected from chat for deal {self.deal_id}")
    
    async def receive(self, text_data):
        """Handle incoming chat messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat.message':
                # Save message to database
                message = await self.save_message(data.get('content'))
                
                # Broadcast message to group
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': str(message.id),
                            'content': message.content,
                            'sender_id': str(message.sender_id),
                            'sender_username': message.sender.telegram_username,
                            'created_at': message.created_at.isoformat(),
                            'is_read': message.is_read,
                        }
                    }
                )
            
            elif message_type == 'chat.typing':
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': str(self.user.id),
                        'username': self.user.telegram_username,
                        'is_typing': data.get('is_typing', True),
                    }
                )
            
            elif message_type == 'chat.read':
                # Mark messages as read
                message_ids = data.get('message_ids', [])
                await self.mark_messages_read(message_ids)
                
                # Broadcast read receipt
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'read_receipt',
                        'user_id': str(self.user.id),
                        'message_ids': message_ids,
                    }
                )
            
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to process message'
            }))
    
    async def chat_message(self, event):
        """Handle chat message events from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Handle typing indicator events."""
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'chat.typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))
    
    async def read_receipt(self, event):
        """Handle read receipt events."""
        # Don't send read receipt to the user who read the messages
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'chat.read',
                'user_id': event['user_id'],
                'message_ids': event['message_ids'],
            }))
    
    async def user_joined(self, event):
        """Handle user joined events."""
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user.joined',
                'user_id': event['user_id'],
                'username': event['username'],
            }))
    
    async def user_left(self, event):
        """Handle user left events."""
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user.left',
                'user_id': event['user_id'],
                'username': event['username'],
            }))
    
    @database_sync_to_async
    def is_deal_participant(self):
        """Check if user is buyer or seller of the deal."""
        try:
            deal = Deal.objects.get(id=self.deal_id)
            return deal.buyer_id == self.user.id or deal.seller_id == self.user.id
        except Deal.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """Save chat message to database."""
        message = Message.objects.create(
            deal_id=self.deal_id,
            sender=self.user,
            content=content
        )
        return message
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Mark messages as read."""
        Message.objects.filter(
            id__in=message_ids,
            deal_id=self.deal_id
        ).exclude(
            sender=self.user
        ).update(is_read=True)
