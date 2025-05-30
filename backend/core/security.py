# backend/core/security.py

from typing import Dict
from core.settings import Settings

def get_security_headers(settings: Settings) -> Dict[str, str]:
    """
    Return the standard security headers for every response.
    """
    return {
        "Strict-Transport-Security": f"max-age=63072000; includeSubDomains; preload",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=(), microphone=()",
    }
