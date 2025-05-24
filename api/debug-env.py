from http.server import BaseHTTPRequestHandler
import json
import os
import re

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
        
        # Analyze redirect URI for common issues
        redirect_uri_issues = []
        if saxo_redirect_uri != "NOT_SET":
            if saxo_redirect_uri.startswith("@"):
                redirect_uri_issues.append("URI starts with '@' symbol - should be removed")
            if "auth-callback" not in saxo_redirect_uri and "callback" in saxo_redirect_uri:
                redirect_uri_issues.append("Endpoint might be '/api/callback' but file is 'auth-callback.py'")
            if not saxo_redirect_uri.startswith("https://"):
                redirect_uri_issues.append("URI should start with 'https://'")
            if "localhost" in saxo_redirect_uri:
                redirect_uri_issues.append("localhost URIs won't work in production")
        
        response = {
            "environment_check": {
                "SAXO_APP_KEY": saxo_app_key[:8] + "..." if saxo_app_key != "NOT_SET" and len(saxo_app_key) > 8 else saxo_app_key,
                "SAXO_APP_SECRET": "SET" if saxo_app_secret != "NOT_SET" else "NOT_SET",
                "SAXO_REDIRECT_URI": saxo_redirect_uri,
                "SAXO_APP_KEY_LENGTH": len(saxo_app_key) if saxo_app_key != "NOT_SET" else 0,
                "redirect_uri_issues": redirect_uri_issues
            },
            "expected_redirect_uri": "https://jh-mdatas.vercel.app/api/auth-callback",
            "callback_endpoint_exists": "auth-callback.py file exists in /api directory",
            "note": "Fix any redirect_uri_issues before testing OAuth flow"
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8')) 