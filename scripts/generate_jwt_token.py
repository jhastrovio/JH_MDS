#!/usr/bin/env python3
"""
Generate a JWT token for testing internal API endpoints.

Usage:
    python scripts/generate_jwt_token.py

This will generate a JWT token that can be used to test:
- /api/auth/price?symbol=EUR-USD 
- /api/auth/ticks?symbol=EUR-USD
- /api/auth/snapshot

The token will be valid for 1 hour by default.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from jose import jwt
except ImportError:
    print("❌ Error: 'python-jose' not installed")
    print("Install it with: pip install python-jose[cryptography]")
    sys.exit(1)

def generate_jwt_token(secret: str = None, expires_in_hours: int = 1) -> str:
    """Generate a JWT token for internal API authentication."""
    
    # Use provided secret or generate a default one
    if not secret:
        secret = os.environ.get("JWT_SECRET")
        if not secret:
            # Generate a default secret for testing
            secret = "test-jwt-secret-for-local-development-only"
            print(f"⚠️  Using default test secret. Set JWT_SECRET environment variable for production.")
    
    # Create payload
    payload = {
        "exp": time.time() + (expires_in_hours * 3600),  # Expires in X hours
        "iat": time.time(),  # Issued at
        "sub": "test-user",  # Subject (optional)
        "purpose": "api-testing"  # Custom claim for identification
    }
    
    # Generate token
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    # Decode expiration for display
    expires_at = datetime.fromtimestamp(payload["exp"])
    
    return token, expires_at, secret

def main():
    print("🔐 JWT Token Generator for JH Market Data Service")
    print("=" * 60)
    
    # Generate token
    token, expires_at, secret = generate_jwt_token()
    
    print(f"✅ JWT Token Generated Successfully!")
    print(f"📅 Expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Secret used: {secret[:20]}..." if len(secret) > 20 else f"🔑 Secret used: {secret}")
    print()
    print("🎫 Your JWT Token:")
    print("-" * 60)
    print(token)
    print("-" * 60)
    print()
    print("📋 Test Commands:")
    print()
    print("# Test price endpoint:")
    print(f'curl -H "Authorization: Bearer {token}" \\')
    print('     "http://localhost:8000/api/auth/price?symbol=EUR-USD"')
    print()
    print("# Test ticks endpoint:")
    print(f'curl -H "Authorization: Bearer {token}" \\')
    print('     "http://localhost:8000/api/auth/ticks?symbol=EUR-USD"')
    print()
    print("# Test snapshot endpoint:")
    print(f'curl -H "Authorization: Bearer {token}" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -X POST \\')
    print('     -d \'{"symbols": ["EUR-USD", "USD-JPY"]}\' \\')
    print('     "http://localhost:8000/api/auth/snapshot"')
    print()
    print("💡 Note: These endpoints use internal JWT authentication, not SaxoBank OAuth.")
    print("💡 For SaxoBank OAuth endpoints (/api/auth/market/*), use the OAuth flow instead.")

if __name__ == "__main__":
    main()
