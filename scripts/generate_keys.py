#!/usr/bin/env python3
"""
Generate secure keys for production deployment.
Run this script to generate SECRET_KEY and WALLET_ENCRYPTION_KEY.
"""

import secrets
import string
from cryptography.fernet import Fernet


def generate_django_secret_key(length=50):
    """Generate a secure Django SECRET_KEY."""
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_fernet_key():
    """Generate a secure Fernet encryption key."""
    return Fernet.generate_key().decode()


def main():
    print("=" * 70)
    print("SECURE KEY GENERATOR FOR CRYPTO ESCROW PLATFORM")
    print("=" * 70)
    print()
    
    print("🔐 Django SECRET_KEY:")
    print("-" * 70)
    secret_key = generate_django_secret_key()
    print(secret_key)
    print()
    
    print("🔐 WALLET_ENCRYPTION_KEY (Fernet):")
    print("-" * 70)
    encryption_key = generate_fernet_key()
    print(encryption_key)
    print()
    
    print("=" * 70)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 70)
    print("1. Store these keys securely in your password manager")
    print("2. Add them to Render environment variables")
    print("3. NEVER commit these keys to version control")
    print("4. Use different keys for development and production")
    print("5. Rotate keys periodically (requires data migration)")
    print()
    
    print("📋 Copy these to your Render environment variables:")
    print("-" * 70)
    print(f"SECRET_KEY={secret_key}")
    print(f"WALLET_ENCRYPTION_KEY={encryption_key}")
    print()
    
    print("✅ Keys generated successfully!")
    print()


if __name__ == "__main__":
    main()
