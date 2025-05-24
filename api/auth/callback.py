from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse the callback URL parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Extract code and state from callback
            auth_code = query_params.get('code', [None])[0]
            state = query_params.get('state', [None])[0]
            error = query_params.get('error', [None])[0]
            
            if error:
                self._send_error_response(400, f"OAuth error: {error}")
                return
                
            if not auth_code or not state:
                self._send_error_response(400, "Missing authorization code or state")
                return
            
            # Get OAuth config
            client_id = os.environ.get("SAXO_APP_KEY")
            client_secret = os.environ.get("SAXO_APP_SECRET") 
            redirect_uri = os.environ.get("SAXO_REDIRECT_URI")
            
            if not all([client_id, client_secret, redirect_uri]):
                self._send_error_response(500, "OAuth configuration incomplete")
                return
            
            # Exchange code for token
            token_data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': redirect_uri,
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            # Make token request to SaxoBank
            token_url = "https://live.logonvalidation.net/token"
            data = urllib.parse.urlencode(token_data).encode('utf-8')
            
            req = urllib.request.Request(
                token_url,
                data=data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    token_response = json.loads(response.read().decode('utf-8'))
                    
                    # In a real app, you'd store the token securely
                    # For now, we'll return success and redirect to frontend
                    self._send_success_response(token_response)
                else:
                    error_text = response.read().decode('utf-8')
                    self._send_error_response(400, f"Token exchange failed: {error_text}")
                    
        except Exception as e:
            self._send_error_response(500, f"Callback processing failed: {str(e)}")
    
    def _send_success_response(self, token_data):
        """Send success response and redirect to frontend"""
        # Create a simple HTML page that closes the popup and notifies parent
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Success</title>
        </head>
        <body>
            <h2>Authentication Successful!</h2>
            <p>You can close this window and return to the application.</p>
            <script>
                // If this is a popup, close it and notify parent
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'SAXO_AUTH_SUCCESS',
                        token: true
                    }}, '*');
                    window.close();
                }} else {{
                    // If not a popup, redirect to main app
                    setTimeout(() => {{
                        window.location.href = '/';
                    }}, 2000);
                }}
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_response.encode('utf-8'))
    
    def _send_error_response(self, status_code, message):
        """Send error response"""
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
        </head>
        <body>
            <h2>Authentication Failed</h2>
            <p>{message}</p>
            <p><a href="/">Return to application</a></p>
            <script>
                // If this is a popup, notify parent of error
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'SAXO_AUTH_ERROR',
                        error: '{message}'
                    }}, '*');
                }}
            </script>
        </body>
        </html>
        """
        
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_response.encode('utf-8')) 