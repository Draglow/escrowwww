"""
Rate limiting for API endpoints.
"""
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
import time


class RateLimitMiddleware:
    """
    Middleware for rate limiting API requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip rate limiting for non-API requests
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Get client identifier (IP or user ID)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_id, request.path):
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': 60
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        response = self.get_response(request)
        return response
    
    def _get_client_id(self, request):
        """Get client identifier for rate limiting."""
        # Use user ID if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f'user:{request.user.id}'
        
        # Otherwise use IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        return f'ip:{ip}'
    
    def _check_rate_limit(self, client_id, path):
        """
        Check if request is within rate limit.
        
        Default limits:
        - 100 requests per minute for general endpoints
        - 10 requests per minute for auth endpoints
        - 5 requests per minute for withdrawal endpoints
        """
        # Determine rate limit based on path
        if '/auth/' in path:
            max_requests = 10
            window = 60  # 1 minute
        elif '/withdraw' in path:
            max_requests = 5
            window = 60
        else:
            max_requests = 100
            window = 60
        
        # Create cache key
        cache_key = f'rate_limit:{client_id}:{path}'
        
        # Get current request count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= max_requests:
            return False
        
        # Increment count
        if current_count == 0:
            # First request in window
            cache.set(cache_key, 1, window)
        else:
            # Increment existing count
            cache.incr(cache_key)
        
        return True


def rate_limit(max_requests=60, window=60):
    """
    Decorator for rate limiting specific views.
    
    Args:
        max_requests: Maximum number of requests allowed
        window: Time window in seconds
    
    Usage:
        @rate_limit(max_requests=10, window=60)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            # Get client identifier
            if hasattr(request, 'user') and request.user.is_authenticated:
                client_id = f'user:{request.user.id}'
            else:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                client_id = f'ip:{ip}'
            
            # Create cache key
            cache_key = f'rate_limit:{client_id}:{view_func.__name__}'
            
            # Get current request count
            current_count = cache.get(cache_key, 0)
            
            if current_count >= max_requests:
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded. Please try again later.',
                        'retry_after': window
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Increment count
            if current_count == 0:
                cache.set(cache_key, 1, window)
            else:
                cache.incr(cache_key)
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator
