import azure.functions as func
import logging
from pathlib import Path

app = func.FunctionApp()

@app.route(route="chat-web", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def serve_chat_web(req: func.HttpRequest) -> func.HttpResponse:
    """Serve the chat web interface"""
    try:
        html_path = Path(__file__).resolve().parent.parent / "chat-web" / "index.html"
        
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return func.HttpResponse(
                html_content,
                status_code=200,
                mimetype="text/html"
            )
        else:
            return func.HttpResponse(
                f"<h1>Error</h1><p>Chat interface not found at {html_path}</p>",
                status_code=404,
                mimetype="text/html"
            )
    except Exception as e:
        logging.error(f'Error serving chat web: {str(e)}')
        return func.HttpResponse(
            f"<h1>Error</h1><p>{str(e)}</p>",
            status_code=500,
            mimetype="text/html"
        )


@app.route(route="chat-web/chat.js", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def serve_chat_js(req: func.HttpRequest) -> func.HttpResponse:
    """Serve the chat JavaScript file"""
    try:
        js_path = Path(__file__).resolve().parent.parent / "chat-web" / "chat.js"
        
        if js_path.exists():
            with open(js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            return func.HttpResponse(
                js_content,
                status_code=200,
                mimetype="application/javascript"
            )
        else:
            return func.HttpResponse(
                f"// Error: JavaScript file not found at {js_path}",
                status_code=404,
                mimetype="application/javascript"
            )
    except Exception as e:
        logging.error(f'Error serving chat.js: {str(e)}')
        return func.HttpResponse(
            f"// Error: {str(e)}",
            status_code=500,
            mimetype="application/javascript"
        )
