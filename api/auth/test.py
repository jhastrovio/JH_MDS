from http.server import BaseHTTPRequestHandler
import json
import os
import secrets
from urllib.parse import urlencode

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get OAuth config
        client_id = os.environ.get("SAXO_APP_KEY")
        redirect_uri = os.environ.get("SAXO_REDIRECT_URI")
        
        # Generate test authorization URL
        state = secrets.token_urlsafe(32)
        
        auth_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openapi"
        }
        
        auth_url = f"https://live.logonvalidation.net/authorize?{urlencode(auth_params)}"
        
        response = {
            "test_info": "This endpoint helps diagnose SaxoBank OAuth issues",
            "configuration": {
                "auth_endpoint": "https://live.logonvalidation.net/authorize",
                "environment": "LIVE (production)",
                "client_id_preview": client_id[:8] + "..." if client_id else "NOT_SET",
                "redirect_uri": redirect_uri,
                "scope": "openapi"
            },
            "generated_auth_url": auth_url,
            "troubleshooting": {
                "if_access_denied": [
                    "1. Check if your SaxoBank account has API access enabled",
                    "2. Verify your account is fully verified and active",
                    "3. Contact SaxoBank support to enable API access",
                    "4. Check if your app needs approval in Developer Portal",
                    "5. Ensure you're using a Live account (not demo/simulation)"
                ],
                "next_steps": [
                    "1. Copy the generated_auth_url above",
                    "2. Open it in a new browser tab",
                    "3. Note exactly where the error occurs",
                    "4. Check SaxoBank Developer Portal for app status"
                ]
            },
            "saxobank_support": {
                "developer_portal": "https://www.developer.saxo/",
                "contact": "Contact SaxoBank support for API access issues"
            }
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8')) 