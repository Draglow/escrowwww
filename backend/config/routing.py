"""
WebSocket URL routing configuration.
"""
from django.urls import path
from apps.deals.consumers import DealConsumer, ChatConsumer

websocket_urlpatterns = [
    path('ws/deals/<uuid:deal_id>/', DealConsumer.as_asgi()),
    path('ws/chat/<uuid:deal_id>/', ChatConsumer.as_asgi()),
]
