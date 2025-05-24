from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Simple auth status check
        # In a real implementation, you'd check for stored tokens
        response = {
            "authenticated": False,
            "message": "Not authenticated - please authenticate with SaxoBank"
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return 