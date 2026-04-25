"""
Two-factor authentication for sensitive operations.
"""
import pyotp
import qrcode
import io
import base64
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


class TwoFactorAuth:
    """
    Two-factor authentication handler using TOTP.
    """
    
    @staticmethod
    def generate_secret():
        """Generate a new TOTP secret."""
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp_uri(user, secret):
        """
        Get TOTP provisioning URI for QR code.
        
        Args:
            user: User instance
            secret: TOTP secret
            
        Returns:
            Provisioning URI string
        """
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.username or str(user.id),
            issuer_name='Crypto Escrow Platform'
        )
    
    @staticmethod
    def generate_qr_code(uri):
        """
        Generate QR code image for TOTP URI.
        
        Args:
            uri: TOTP provisioning URI
            
        Returns:
            Base64 encoded QR code image
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer)
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_totp(secret, token):
        """
        Verify TOTP token.
        
        Args:
            secret: TOTP secret
            token: 6-digit TOTP token
            
        Returns:
            Boolean indicating if token is valid
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes(count=10):
        """
        Generate backup codes for 2FA recovery.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        return [pyotp.random_base32()[:8] for _ in range(count)]
    
    @staticmethod
    def create_withdrawal_challenge(user_id, withdrawal_id):
        """
        Create a 2FA challenge for withdrawal.
        
        Args:
            user_id: User ID
            withdrawal_id: Withdrawal request ID
            
        Returns:
            Challenge ID
        """
        challenge_id = pyotp.random_base32()
        cache_key = f'withdrawal_challenge:{challenge_id}'
        
        cache.set(
            cache_key,
            {
                'user_id': str(user_id),
                'withdrawal_id': str(withdrawal_id),
                'created_at': timezone.now().isoformat(),
            },
            timeout=300  # 5 minutes
        )
        
        return challenge_id
    
    @staticmethod
    def verify_withdrawal_challenge(challenge_id, user_id, withdrawal_id):
        """
        Verify withdrawal challenge.
        
        Args:
            challenge_id: Challenge ID
            user_id: User ID
            withdrawal_id: Withdrawal request ID
            
        Returns:
            Boolean indicating if challenge is valid
        """
        cache_key = f'withdrawal_challenge:{challenge_id}'
        challenge_data = cache.get(cache_key)
        
        if not challenge_data:
            return False
        
        if (challenge_data['user_id'] == str(user_id) and 
            challenge_data['withdrawal_id'] == str(withdrawal_id)):
            # Delete challenge after successful verification
            cache.delete(cache_key)
            return True
        
        return False
    
    @staticmethod
    def rate_limit_2fa_attempts(user_id, max_attempts=5, window_minutes=15):
        """
        Rate limit 2FA verification attempts.
        
        Args:
            user_id: User ID
            max_attempts: Maximum attempts allowed
            window_minutes: Time window in minutes
            
        Returns:
            Tuple of (allowed, remaining_attempts)
        """
        cache_key = f'2fa_attempts:{user_id}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= max_attempts:
            return False, 0
        
        # Increment attempts
        cache.set(cache_key, attempts + 1, timeout=window_minutes * 60)
        
        return True, max_attempts - attempts - 1
