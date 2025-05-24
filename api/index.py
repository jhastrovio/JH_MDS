from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Simple routing based on path
        if self.path == '/':
            response = {
                "message": "JH Market Data API is running",
                "status": "ok"
            }
        elif self.path == '/debug':
            response = {
                "status": "ok",
                "environment_vars": {
                    "JWT_SECRET": "SET" if os.environ.get("JWT_SECRET") else "NOT_SET",
                    "REDIS_URL": "SET" if os.environ.get("REDIS_URL") else "NOT_SET",
                    "SAXO_APP_KEY": "SET" if os.environ.get("SAXO_APP_KEY") else "NOT_SET",
                    "SAXO_APP_SECRET": "SET" if os.environ.get("SAXO_APP_SECRET") else "NOT_SET",
                    "SAXO_REDIRECT_URI": "SET" if os.environ.get("SAXO_REDIRECT_URI") else "NOT_SET",
                }
            }
        elif self.path == '/auth/status':
            response = {
                "authenticated": False,
                "message": "OAuth not configured in simple handler"
            }
        else:
            response = {
                "error": "Not found",
                "path": self.path,
                "message": "Available endpoints: /, /debug, /auth/status"
            }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return 