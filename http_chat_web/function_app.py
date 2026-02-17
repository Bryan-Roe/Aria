import azure.functions as func
import logging
from pathlib import Path
import sys

# Ensure repository root is on sys.path so shared utilities can be imported as a package
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from shared.http_utils import serve_static_file

app = func.FunctionApp()

@app.route(route="chat-web", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def serve_chat_web(req: func.HttpRequest) -> func.HttpResponse:
    """Serve the chat web interface"""
    html_path = Path(__file__).resolve().parent.parent / "chat-web" / "index.html"
    content, status_code, headers = serve_static_file(html_path, "text/html", use_cache_headers=True)
    
    return func.HttpResponse(
        content,
        status_code=status_code,
        mimetype="text/html",
        headers=headers
    )


@app.route(route="chat-web/chat.js", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def serve_chat_js(req: func.HttpRequest) -> func.HttpResponse:
    """Serve the chat JavaScript file"""
    js_path = Path(__file__).resolve().parent.parent / "chat-web" / "chat.js"
    content, status_code, headers = serve_static_file(js_path, "application/javascript", use_cache_headers=True)
    
    return func.HttpResponse(
        content,
        status_code=status_code,
        mimetype="application/javascript",
        headers=headers
    )
