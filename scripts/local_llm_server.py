#!/usr/bin/env python3
"""
Local LLM server for development - provides Ollama-compatible API without installation
"""
import json
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class OllamaCompatibleHandler(BaseHTTPRequestHandler):
    """Ollama API compatible handler"""

    def do_GET(self):
        if self.path == "/api/tags":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "models": [
                    {
                        "name": "mistral:latest",
                        "modified_at": datetime.now().isoformat(),
                    },
                    {
                        "name": "neural-chat:latest",
                        "modified_at": datetime.now().isoformat(),
                    },
                    {
                        "name": "codellama:latest",
                        "modified_at": datetime.now().isoformat(),
                    },
                ]
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            request = json.loads(body)

            # Simulate LLM response
            prompt = request.get("prompt", "")
            model = request.get("model", "mistral")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response = {
                "model": model,
                "created_at": datetime.now().isoformat(),
                "response": (
                    f"Response to: {prompt[:50]}..." if prompt else "Model ready"
                ),
                "done": True,
                "total_duration": 1000000000,
                "load_duration": 0,
                "prompt_eval_count": len(prompt.split()),
                "eval_count": 10,
                "eval_duration": 500000000,
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()


def start_server(port=11434):
    """Start local LLM server"""
    server = HTTPServer(("127.0.0.1", port), OllamaCompatibleHandler)
    print(f"✓ Local LLM server running on http://127.0.0.1:{port}")

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 11434
    server = start_server(port)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        server.shutdown()
