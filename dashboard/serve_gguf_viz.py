#!/usr/bin/env python3
"""
Simple HTTP server for GGUF visualizer

Serves the GGUF visualizer web interface and GGUF model files.
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).parent

class GGUFHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve GGUF files with correct MIME type"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def guess_type(self, path):
        """Override to handle .gguf files"""
        mime_type = super().guess_type(path)
        
        # Set correct MIME type for GGUF files
        if path.endswith('.gguf'):
            return 'application/octet-stream'
        
        return mime_type
    
    def end_headers(self):
        """Add CORS headers to allow loading from filesystem"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.end_headers()


def main():
    """Start the server"""
    os.chdir(DIRECTORY)
    
    print("=" * 70)
    print("🔍 GGUF Visualizer Server")
    print("=" * 70)
    print(f"\n📂 Serving from: {DIRECTORY}")
    print(f"🌐 Server: http://localhost:{PORT}")
    print(f"📊 Visualizer: http://localhost:{PORT}/gguf_visualizer.html")
    print("\n📁 Available GGUF files:")
    
    # Find GGUF files
    data_out = DIRECTORY.parent / "data_out"
    if data_out.exists():
        gguf_files = list(data_out.glob("*.gguf"))
        if gguf_files:
            for f in gguf_files:
                size_kb = f.stat().st_size / 1024
                print(f"   • {f.name} ({size_kb:.1f} KB)")
        else:
            print("   (No GGUF files found in data_out/)")
    
    print("\n" + "=" * 70)
    print("Press Ctrl+C to stop the server")
    print("=" * 70 + "\n")
    
    with socketserver.TCPServer(("", PORT), GGUFHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Server stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
