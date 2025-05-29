"""
Security utilities for production deployment.
"""
import os
import secrets
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .logger import logger


class SecurityValidator:
    """Security configuration validator for production readiness."""
    
    def __init__(self):
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    def validate_production_config(self) -> Dict[str, any]:
        """Validate security configuration for production deployment."""
        issues = []
        warnings = []
        
        # Check JWT secret strength
        jwt_secret = os.environ.get("JWT_SECRET")
        if not jwt_secret:
            issues.append("JWT_SECRET not set")
        elif len(jwt_secret) < 32:
            warnings.append("JWT_SECRET should be at least 32 characters")
        
        # Check HTTPS enforcement
        redirect_uri = os.environ.get("SAXO_REDIRECT_URI", "")
        if redirect_uri and not redirect_uri.startswith("https://"):
            if os.environ.get("NODE_ENV") == "production":
                issues.append("SAXO_REDIRECT_URI must use HTTPS in production")
            else:
                warnings.append("SAXO_REDIRECT_URI should use HTTPS for production")
        
        # Check Redis URL security
        redis_url = os.environ.get("REDIS_URL", "")
        if redis_url and not redis_url.startswith(("rediss://", "redis://localhost")):
            if "password" not in redis_url:
                warnings.append("Redis URL should include authentication")
        
        # Check environment
        node_env = os.environ.get("NODE_ENV", "development")
        if node_env != "production":
            warnings.append(f"NODE_ENV is '{node_env}', should be 'production' for production deployment")
        
        # Check CORS origins
        frontend_url = os.environ.get("NEXT_PUBLIC_API_BASE_URL", "")
        if frontend_url and not frontend_url.startswith("https://"):
            if node_env == "production":
                issues.append("Frontend URL must use HTTPS in production")
        
        return {
            "is_production_ready": len(issues) == 0,
            "critical_issues": issues,
            "warnings": warnings,
            "security_score": max(0, 100 - (len(issues) * 25) - (len(warnings) * 5)),
            "checked_at": datetime.utcnow().isoformat()
        }
    
    def generate_secure_jwt_secret(self) -> str:
        """Generate a cryptographically secure JWT secret."""
        return secrets.token_urlsafe(64)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers for production."""
        return self.security_headers.copy()
    
    def validate_environment_secrets(self) -> Dict[str, any]:
        """Validate that all secrets are properly configured."""
        required_secrets = [
            "SAXO_APP_KEY",
            "SAXO_APP_SECRET", 
            "REDIS_URL",
            "JWT_SECRET"
        ]
        
        optional_secrets = [
            "ONE_DRIVE_CLIENT_ID",
            "ONE_DRIVE_CLIENT_SECRET"
        ]
        
        missing_required = []
        missing_optional = []
        weak_secrets = []
        
        for secret in required_secrets:
            value = os.environ.get(secret)
            if not value:
                missing_required.append(secret)
            elif len(value) < 20 and secret == "JWT_SECRET":
                weak_secrets.append(f"{secret} (too short)")
        
        for secret in optional_secrets:
            if not os.environ.get(secret):
                missing_optional.append(secret)
        
        return {
            "all_required_present": len(missing_required) == 0,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "weak_secrets": weak_secrets,
            "total_secrets_configured": len(required_secrets) - len(missing_required),
            "security_rating": "HIGH" if len(missing_required) == 0 and len(weak_secrets) == 0 else 
                             "MEDIUM" if len(missing_required) == 0 else "LOW"
        }


# Global security validator instance
security_validator = SecurityValidator()
