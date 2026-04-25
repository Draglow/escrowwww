"""
Utility functions for WebSocket broadcasting.
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


def broadcast_deal_update(deal):
    """
    Broadcast deal update to all connected clients.
    
    Args:
        deal: Deal instance
    """
    channel_layer = get_channel_layer()
    
    if not channel_layer:
        logger.warning("Channel layer not configured, skipping WebSocket broadcast")
        return
    
    deal_group_name = f'deal_{deal.id}'
    
    deal_data = {
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
    
    try:
        async_to_sync(channel_layer.group_send)(
            deal_group_name,
            {
                'type': 'deal_update',
                'data': deal_data
            }
        )
        logger.info(f"Broadcasted update for deal {deal.id}")
    except Exception as e:
        logger.error(f"Failed to broadcast deal update: {str(e)}")


def broadcast_deal_status_change(deal, old_status, new_status):
    """
    Broadcast deal status change to all connected clients.
    
    Args:
        deal: Deal instance
        old_status: Previous status
        new_status: New status
    """
    channel_layer = get_channel_layer()
    
    if not channel_layer:
        logger.warning("Channel layer not configured, skipping WebSocket broadcast")
        return
    
    deal_group_name = f'deal_{deal.id}'
    
    status_data = {
        'deal_id': str(deal.id),
        'old_status': old_status,
        'new_status': new_status,
        'timestamp': deal.updated_at.isoformat(),
    }
    
    try:
        async_to_sync(channel_layer.group_send)(
            deal_group_name,
            {
                'type': 'deal_status_changed',
                'data': status_data
            }
        )
        logger.info(f"Broadcasted status change for deal {deal.id}: {old_status} -> {new_status}")
    except Exception as e:
        logger.error(f"Failed to broadcast status change: {str(e)}")
