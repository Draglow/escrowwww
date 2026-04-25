"""
Wallet encryption utilities using Fernet (symmetric encryption).
"""
import base64
from cryptography.fernet import Fernet
from django.conf import settings


class WalletEncryption:
    """
    Handles encryption and decryption of wallet private keys.
    Uses Fernet symmetric encryption with a key from settings.
    """
    
    @staticmethod
    def _get_cipher():
        """Get Fernet cipher instance."""
        key = settings.WALLET_ENCRYPTION_KEY.encode()
        # Ensure key is properly formatted for Fernet
        if len(key) != 44:  # Fernet keys are 44 bytes when base64 encoded
            key = base64.urlsafe_b64encode(key[:32].ljust(32, b'0'))
        return Fernet(key)
    
    @staticmethod
    def encrypt_private_key(private_key: str) -> bytes:
        """
        Encrypt a private key.
        
        Args:
            private_key: Hex string of private key
            
        Returns:
            Encrypted private key as bytes
        """
        cipher = WalletEncryption._get_cipher()
        return cipher.encrypt(private_key.encode())
    
    @staticmethod
    def decrypt_private_key(encrypted_key: bytes) -> str:
        """
        Decrypt a private key.
        
        Args:
            encrypted_key: Encrypted private key bytes
            
        Returns:
            Decrypted private key as hex string
        """
        cipher = WalletEncryption._get_cipher()
        return cipher.decrypt(encrypted_key).decode()
