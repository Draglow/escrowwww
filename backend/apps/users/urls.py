"""
User API URLs.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, telegram_login, logout
from .views_webauthn import (
    webauthn_register_begin,
    webauthn_register_complete,
    webauthn_authenticate_begin,
    webauthn_authenticate_complete,
    webauthn_bridge_redeem,
)

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # Telegram auth
    path('auth/login/', telegram_login, name='telegram-login'),
    path('auth/logout/', logout, name='logout'),

    # WebAuthn / Passkey endpoints (Requirements 14.1)
    path('auth/webauthn/register/begin/', webauthn_register_begin, name='webauthn-register-begin'),
    path('auth/webauthn/register/complete/', webauthn_register_complete, name='webauthn-register-complete'),
    path('auth/webauthn/authenticate/begin/', webauthn_authenticate_begin, name='webauthn-authenticate-begin'),
    path('auth/webauthn/authenticate/complete/', webauthn_authenticate_complete, name='webauthn-authenticate-complete'),
    path('auth/webauthn/bridge/redeem/', webauthn_bridge_redeem, name='webauthn-bridge-redeem'),

    # ViewSet routes (includes credential management added in Task 6)
    path('', include(router.urls)),
]
