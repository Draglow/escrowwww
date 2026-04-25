#!/usr/bin/env python3
"""
Test script to check if coincurve can be imported.
Run this locally to verify the package works.
"""

import sys

print("=" * 60)
print("Testing coincurve installation")
print("=" * 60)
print()

# Check Python version
print(f"Python version: {sys.version}")
print()

# Try to import coincurve
try:
    import coincurve
    print("✅ coincurve imported successfully!")
    print(f"   Version: {coincurve.__version__ if hasattr(coincurve, '__version__') else 'unknown'}")
    print()
    
    # Try to create a private key
    try:
        from coincurve import PrivateKey
        private_key = PrivateKey()
        print("✅ Can create PrivateKey objects")
        print(f"   Public key: {private_key.public_key.format().hex()[:20]}...")
        print()
    except Exception as e:
        print(f"❌ Error creating PrivateKey: {e}")
        print()
        
except ImportError as e:
    print(f"❌ Failed to import coincurve: {e}")
    print()
    print("This means coincurve is not installed or cannot be loaded.")
    print()
    print("To fix:")
    print("1. Install system dependencies:")
    print("   - Ubuntu/Debian: sudo apt-get install build-essential libssl-dev libffi-dev python3-dev")
    print("   - macOS: brew install libsecp256k1")
    print()
    print("2. Install coincurve:")
    print("   pip install coincurve")
    print()
    sys.exit(1)

# Try to import tronpy
try:
    import tronpy
    print("✅ tronpy imported successfully!")
    print(f"   Version: {tronpy.__version__ if hasattr(tronpy, '__version__') else 'unknown'}")
    print()
except ImportError as e:
    print(f"❌ Failed to import tronpy: {e}")
    print()

print("=" * 60)
print("All checks passed! ✅")
print("=" * 60)
