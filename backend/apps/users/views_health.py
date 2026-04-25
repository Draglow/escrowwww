"""
Health check endpoints for monitoring.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import redis
from django.conf import settings


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 if the service is running.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'escrow-backend',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_detailed(request):
    """
    Detailed health check with database and cache status.
    """
    health_status = {
        'status': 'healthy',
        'service': 'escrow-backend',
        'checks': {}
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
    
    # Check cache (Redis)
    try:
        cache.set('health_check', 'ok', 10)
        value = cache.get('health_check')
        if value == 'ok':
            health_status['checks']['cache'] = 'healthy'
        else:
            health_status['status'] = 'unhealthy'
            health_status['checks']['cache'] = 'unhealthy: cache read/write failed'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['cache'] = f'unhealthy: {str(e)}'
    
    # Check Celery (Redis broker)
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status['checks']['celery'] = 'healthy'
        else:
            health_status['status'] = 'degraded'
            health_status['checks']['celery'] = 'degraded: no workers available'
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['celery'] = f'degraded: {str(e)}'
    
    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check for Kubernetes/load balancers.
    Returns 200 only if all critical services are ready.
    """
    ready = True
    checks = {}
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = True
    except Exception:
        ready = False
        checks['database'] = False
    
    # Check cache
    try:
        cache.set('readiness_check', 'ok', 10)
        checks['cache'] = cache.get('readiness_check') == 'ok'
        if not checks['cache']:
            ready = False
    except Exception:
        ready = False
        checks['cache'] = False
    
    status_code = 200 if ready else 503
    
    return JsonResponse({
        'ready': ready,
        'checks': checks
    }, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check for Kubernetes.
    Returns 200 if the application is alive (even if not fully functional).
    """
    return JsonResponse({
        'alive': True,
        'service': 'escrow-backend'
    })
