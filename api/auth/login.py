from http.server import BaseHTTPRequestHandler
import json
import os
import secrets
from urllib.parse import urlencode

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get OAuth config from environment
            client_id = os.environ.get("SAXO_APP_KEY")
            redirect_uri = os.environ.get("SAXO_REDIRECT_URI")
            
            if not client_id or not redirect_uri:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "error": "OAuth configuration missing",
                    "message": "SAXO_APP_KEY and SAXO_REDIRECT_URI must be set"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Generate OAuth URL
            state = secrets.token_urlsafe(32)
            
            auth_params = {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "scope": "openapi"
            }
            
            auth_url = f"https://live.logonvalidation.net/authorize?{urlencode(auth_params)}"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "auth_url": auth_url,
                "state": state,
                "message": "Redirect to auth_url to begin authentication"
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "error": "Authentication failed",
                "message": str(e)
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return 