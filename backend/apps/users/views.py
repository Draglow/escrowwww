"""
User API views.
"""
import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from .models import User, WebAuthnCredential
from .serializers import UserSerializer, UserProfileSerializer, WebAuthnCredentialSerializer
from .tokens import create_auth_token, revoke_auth_token
from .two_factor import TwoFactorAuth
from .audit import log_audit, get_client_ip, get_user_agent, AuditLog
from .authentication import TelegramAuthentication


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_login(request):
    """
    Authenticate user via Telegram Login Widget and return token.
    
    Request body should contain Telegram auth data:
    {
        "id": "123456789",
        "first_name": "John",
        "username": "johndoe",
        "photo_url": "https://...",
        "auth_date": "1234567890",
        "hash": "abc123..."
    }
    """
    # Use TelegramAuthentication to verify and get/create user
    auth = TelegramAuthentication()
    
    try:
        result = auth.authenticate(request)
        
        if not result:
            return Response(
                {'error': 'Authentication failed', 'detail': 'No auth header or unrecognized format'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user, _ = result
        
        if not user:
            return Response(
                {'error': 'Authentication failed'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Create auth token
        token = create_auth_token(user)
        
        # Log successful login
        log_audit(
            user=user,
            action='LOGIN',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            success=True
        )
        
        # Check whether the user needs to set up a Passkey (Req 9.3)
        passkey_setup_required = not user.webauthn_credentials_set.filter(
            is_active=True
        ).exists()

        # Return user data and token
        serializer = UserProfileSerializer(user)
        response_data = {
            'user': serializer.data,
            'token': token.key,
        }
        if passkey_setup_required:
            response_data['passkey_setup_required'] = True

        return Response(response_data)
        
    except Exception as e:
        import traceback
        print(f"[LOGIN ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        # Log failed login attempt
        log_audit(
            user=None,
            action='LOGIN',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={'error': str(e), 'type': type(e).__name__},
            success=False
        )
        
        return Response(
            {'error': 'Authentication failed', 'detail': str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by revoking their auth token.
    """
    # Log logout
    log_audit(
        user=request.user,
        action='LOGOUT',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=True
    )
    
    # Revoke token
    revoke_auth_token(request.user)
    
    return Response({'message': 'Successfully logged out'})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user operations.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to only show active users."""
        return User.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user profile."""
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Log profile update
        log_audit(
            user=request.user,
            action='PROFILE_UPDATED',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={'updated_fields': list(request.data.keys())},
            success=True
        )
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def enable_2fa(self, request):
        """
        Enable two-factor authentication for the user.
        Returns QR code for TOTP setup.
        """
        user = request.user
        
        if user.is_2fa_enabled:
            return Response(
                {'error': '2FA is already enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate TOTP secret
        secret = TwoFactorAuth.generate_secret()
        
        # Generate QR code
        uri = TwoFactorAuth.get_totp_uri(user, secret)
        qr_code = TwoFactorAuth.generate_qr_code(uri)
        
        # Generate backup codes
        backup_codes = TwoFactorAuth.generate_backup_codes()
        
        # Store temporarily (user must verify before enabling)
        request.session['pending_2fa_secret'] = secret
        request.session['pending_2fa_backup_codes'] = backup_codes
        
        return Response({
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': backup_codes,
            'message': 'Scan the QR code with your authenticator app and verify with a code'
        })
    
    @action(detail=False, methods=['post'])
    def verify_2fa_setup(self, request):
        """
        Verify 2FA setup by checking TOTP token.
        """
        user = request.user
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get pending secret from session
        secret = request.session.get('pending_2fa_secret')
        backup_codes = request.session.get('pending_2fa_backup_codes')
        
        if not secret:
            return Response(
                {'error': 'No pending 2FA setup found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify token
        if not TwoFactorAuth.verify_totp(secret, token):
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enable 2FA
        user.totp_secret = secret
        user.is_2fa_enabled = True
        user.backup_codes = backup_codes
        user.save(update_fields=['totp_secret', 'is_2fa_enabled', 'backup_codes'])
        
        # Clear session
        del request.session['pending_2fa_secret']
        del request.session['pending_2fa_backup_codes']
        
        # Log 2FA enabled
        log_audit(
            user=user,
            action='2FA_ENABLED',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            success=True
        )
        
        return Response({
            'message': '2FA enabled successfully',
            'backup_codes': backup_codes
        })
    
    @action(detail=False, methods=['post'])
    def disable_2fa(self, request):
        """
        Disable two-factor authentication.
        Requires current 2FA token or backup code.
        """
        user = request.user
        token = request.data.get('token')
        
        if not user.is_2fa_enabled:
            return Response(
                {'error': '2FA is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify token or backup code
        valid = False
        if TwoFactorAuth.verify_totp(user.totp_secret, token):
            valid = True
        elif token in user.backup_codes:
            valid = True
            # Remove used backup code
            user.backup_codes.remove(token)
        
        if not valid:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Disable 2FA
        user.totp_secret = None
        user.is_2fa_enabled = False
        user.backup_codes = []
        user.save(update_fields=['totp_secret', 'is_2fa_enabled', 'backup_codes'])
        
        # Log 2FA disabled
        log_audit(
            user=user,
            action='2FA_DISABLED',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            success=True
        )
        
        return Response({'message': '2FA disabled successfully'})
    
    @action(detail=False, methods=['post'])
    def verify_2fa(self, request):
        """
        Verify 2FA token for sensitive operations.
        """
        user = request.user
        token = request.data.get('token')
        
        if not user.is_2fa_enabled:
            return Response(
                {'error': '2FA is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Rate limit attempts
        allowed, remaining = TwoFactorAuth.rate_limit_2fa_attempts(user.id)
        if not allowed:
            return Response(
                {'error': 'Too many failed attempts. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Verify token or backup code
        valid = False
        if TwoFactorAuth.verify_totp(user.totp_secret, token):
            valid = True
        elif token in user.backup_codes:
            valid = True
            # Remove used backup code
            user.backup_codes.remove(token)
            user.save(update_fields=['backup_codes'])
        
        if not valid:
            return Response(
                {
                    'error': 'Invalid token',
                    'remaining_attempts': remaining
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({'message': 'Token verified successfully'})
    
    @action(detail=False, methods=['get'])
    def audit_logs(self, request):
        """
        Get audit logs for the current user.
        """
        logs = AuditLog.objects.filter(user=request.user).order_by('-created_at')[:50]
        
        data = [{
            'id': str(log.id),
            'action': log.action,
            'ip_address': log.ip_address,
            'success': log.success,
            'created_at': log.created_at.isoformat(),
            'details': log.details,
        } for log in logs]
        
        return Response(data)

    # ------------------------------------------------------------------
    # Credential management (Requirements 11.1 – 11.5, 14.2)
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='credentials', permission_classes=[IsAuthenticated])
    def list_credentials(self, request):
        """
        GET /credentials/ — list all WebAuthn credentials for the current user.

        Validates: Requirements 11.1, 14.2
        """
        credentials = request.user.webauthn_credentials_set.all().order_by('-created_at')
        serializer = WebAuthnCredentialSerializer(credentials, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['patch', 'delete'], url_path=r'credentials/(?P<pk>[^/.]+)', permission_classes=[IsAuthenticated])
    def manage_credential(self, request, pk=None):
        """
        PATCH /credentials/{id}/ — rename a WebAuthn credential.
        DELETE /credentials/{id}/ — revoke (soft-delete) a WebAuthn credential.

        Returns 404 if the UUID is malformed or the credential does not exist.
        Returns 403 if the credential belongs to another user.
        Returns 400 (DELETE only) if this is the user's last active credential.

        Validates: Requirements 11.2, 11.3, 11.4, 11.5, 14.2
        """
        try:
            credential_uuid = uuid.UUID(pk)
        except (ValueError, AttributeError):
            return Response({'error': 'Credential not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            credential = WebAuthnCredential.objects.get(id=credential_uuid)
        except WebAuthnCredential.DoesNotExist:
            return Response({'error': 'Credential not found'}, status=status.HTTP_404_NOT_FOUND)

        if credential.user_id != request.user.id:
            return Response({'error': 'Credential not found'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'PATCH':
            serializer = WebAuthnCredentialSerializer(credential, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        # DELETE
        if credential.is_active:
            active_count = request.user.webauthn_credentials_set.filter(is_active=True).count()
            if active_count == 1:
                return Response(
                    {'error': 'Cannot revoke last active credential'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        credential.is_active = False
        credential.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)
