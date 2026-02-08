#!/usr/bin/env python3
"""
Brutus Coding Agent API
Lightweight HTTP server for Qwen code generation
Runs on brutus-8gb (8GB RAM)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import re

PORT = 8080
AUTH_TOKEN = "brutus-coding-agent-2025"  # Change this!

def generate_code(prompt, language="python"):
    """Call local Ollama Qwen model"""
    full_prompt = f"Write {language} code for this task:\n\n{prompt}\n\nProvide clean, well-commented code with brief explanation:\n\nCode:"
    
    try:
        result = subprocess.run(
            ["ollama", "run", "qwen2.5-coder:7b", full_prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
        return {"success": True, "code": result.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}

def explain_code(code_snippet):
    """Explain what code does"""
    prompt = f"Explain this code in simple terms:\n```\n{code_snippet}\n```\n\nExplanation:"
    
    try:
        result = subprocess.run(
            ["ollama", "run", "qwen2.5-coder:7b", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        return {"success": True, "explanation": result.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}

class CodingHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Quiet logging
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _check_auth(self):
        auth = self.headers.get('Authorization', '')
        return auth == f"Bearer {AUTH_TOKEN}"
    
    def do_GET(self):
        if self.path == "/health":
            self._send_json({"status": "ok", "model": "qwen2.5-coder:7b"})
            return
        self._send_json({"error": "Use POST /code or /explain"}, 404)
    
    def do_POST(self):
        if not self._check_auth():
            self._send_json({"error": "Unauthorized"}, 401)
            return
        
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode()
        
        try:
            data = json.loads(body)
        except:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        if self.path == "/code":
            prompt = data.get('prompt', '')
            lang = data.get('language', 'python')
            if not prompt:
                self._send_json({"error": "Missing 'prompt'"}, 400)
                return
            result = generate_code(prompt, lang)
            self._send_json(result)
        
        elif self.path == "/explain":
            code = data.get('code', '')
            if not code:
                self._send_json({"error": "Missing 'code'"}, 400)
                return
            result = explain_code(code)
            self._send_json(result)
        
        else:
            self._send_json({"error": "Unknown endpoint. Use /code or /explain"}, 404)

if __name__ == '__main__':
    print(f"🦞 Brutus Coding Agent starting on port {PORT}")
    print(f"   Model: qwen2.5-coder:7b")
    print(f"   Endpoints: POST /code, POST /explain, GET /health")
    
    server = HTTPServer(('0.0.0.0', PORT), CodingHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down")
