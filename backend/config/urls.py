"""
URL configuration for escrow platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.users.views_health import health_check, health_check_detailed, readiness_check, liveness_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/wallets/', include('apps.wallets.urls')),
    path('api/v1/deals/', include('apps.deals.urls')),
    path('api/v1/ledger/', include('apps.ledger.urls')),
    
    # Health check endpoints
    path('api/v1/health/', health_check, name='health_check'),
    path('api/v1/health/detailed/', health_check_detailed, name='health_check_detailed'),
    path('api/v1/health/ready/', readiness_check, name='readiness_check'),
    path('api/v1/health/live/', liveness_check, name='liveness_check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
