from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get OAuth environment variables (mask sensitive data)
        saxo_app_key = os.environ.get("SAXO_APP_KEY", "NOT_SET")
        saxo_redirect_uri = os.environ.get("SAXO_REDIRECT_URI", "NOT_SET")
        saxo_app_secret = os.environ.get("SAXO_APP_SECRET", "NOT_SET")
        
        # Analyze configuration for common issues
        issues = []
        warnings = []
        
        # Check SAXO_APP_KEY
        if saxo_app_key == "NOT_SET":
            issues.append("SAXO_APP_KEY is not set")
        elif saxo_app_key == "5bf52bb532774f9974e900d3faf2ff":
            issues.append("SAXO_APP_KEY appears to be placeholder value from example file")
        elif not saxo_app_key.startswith("5bf5"):
            warnings.append("SAXO_APP_KEY doesn't start with expected prefix '5bf5'")
        
        # Check SAXO_APP_SECRET
        if saxo_app_secret == "NOT_SET":
            issues.append("SAXO_APP_SECRET is not set")
        elif saxo_app_secret == "your-app-secret-from-saxobank":
            issues.append("SAXO_APP_SECRET appears to be placeholder value")
        
        # Check SAXO_REDIRECT_URI
        if saxo_redirect_uri == "NOT_SET":
            issues.append("SAXO_REDIRECT_URI is not set")
        else:
            if saxo_redirect_uri.startswith("@"):
                issues.append("SAXO_REDIRECT_URI starts with '@' symbol - remove it")
            if "localhost" in saxo_redirect_uri:
                warnings.append("localhost redirect URI won't work in production")
            if not saxo_redirect_uri.startswith("https://"):
                issues.append("SAXO_REDIRECT_URI should start with 'https://'")
            if "auth-callback" not in saxo_redirect_uri:
                warnings.append("Redirect URI should end with '/api/auth-callback'")
        
        # Configuration status
        config_status = "✅ Ready" if not issues else "❌ Issues Found"
        if warnings and not issues:
            config_status = "⚠️ Warnings"
        
        response = {
            "status": config_status,
            "configuration": {
                "SAXO_APP_KEY": saxo_app_key[:8] + "..." if saxo_app_key != "NOT_SET" and len(saxo_app_key) > 8 else saxo_app_key,
                "SAXO_APP_SECRET": "SET" if saxo_app_secret != "NOT_SET" else "NOT_SET",
                "SAXO_REDIRECT_URI": saxo_redirect_uri,
                "app_key_length": len(saxo_app_key) if saxo_app_key != "NOT_SET" else 0
            },
            "expected_values": {
                "SAXO_APP_KEY": "Should start with '5bf5...' (from your SaxoBank app)",
                "SAXO_APP_SECRET": "Should start with '83ce...' (from your SaxoBank app)",
                "SAXO_REDIRECT_URI": "https://jh-mdatas.vercel.app/api/auth-callback"
            },
            "issues": issues,
            "warnings": warnings,
            "endpoints": {
                "auth_login": "/api/auth-login",
                "auth_callback": "/api/auth-callback", 
                "auth_status": "/api/auth-status"
            },
            "next_steps": [
                "Fix any issues listed above",
                "Test OAuth flow at /api/auth-login",
                "Check SaxoBank app registration matches redirect URI"
            ]
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8')) 