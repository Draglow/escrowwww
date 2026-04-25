"""
WebSocket authentication middleware.
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    """Get user from token."""
    try:
        token = Token.objects.select_related('user').get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Middleware to authenticate WebSocket connections using token.
    Token can be passed via:
    1. Query parameter: ?token=<token>
    2. Header: Authorization: Token <token>
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        token_key = None
        
        # Parse query string for token
        if query_string:
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            token_key = params.get('token')
        
        # If no token in query string, check headers
        if not token_key:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            
            if auth_header.startswith('Token '):
                token_key = auth_header.split(' ')[1]
        
        # Authenticate user
        if token_key:
            scope['user'] = await get_user_from_token(token_key)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
