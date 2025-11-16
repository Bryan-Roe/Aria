import azure.functions as func
import json
import logging
import os
import sys
from pathlib import Path
import subprocess
import importlib.util as _iu

# Add talk-to-ai to path so we can import chat_providers
talk_to_ai_path = Path(__file__).resolve().parent / "talk-to-ai" / "src"
sys.path.insert(0, str(talk_to_ai_path))

from chat_providers import detect_provider, RoleMessage
from token_utils import prune_messages

app = func.FunctionApp()


# =============================================================================
# Chat Web Interface - Serves the HTML/JS frontend
# =============================================================================

@app.route(route="chat-web", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def serve_chat_web(req: func.HttpRequest) -> func.HttpResponse:
    """Serve the chat web interface HTML"""
    try:
        html_path = Path(__file__).resolve().parent / "chat-web" / "index.html"
        
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return func.HttpResponse(
                html_content,
                status_code=200,
                mimetype="text/html",
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
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
        js_path = Path(__file__).resolve().parent / "chat-web" / "chat.js"
        
        if js_path.exists():
            with open(js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            return func.HttpResponse(
                js_content,
                status_code=200,
                mimetype="application/javascript",
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
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


# =============================================================================
# Chat API - Backend for AI interactions
# =============================================================================

@app.route(route="chat", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def chat(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint for chat interactions.
    
    POST /api/chat
    Body: {
        "messages": [{"role": "user|assistant|system", "content": "..."}],
        "provider": "auto|openai|azure|local" (optional),
        "model": "model-name" (optional),
        "stream": false (optional, streaming not implemented in HTTP yet)
    }
    
    Response: {
        "response": "assistant's reply",
        "provider": "azure|openai|local",
        "model": "model-name"
    }
    """
    logging.info('Chat function invoked')

    try:
        # Parse request
        req_body = req.get_json()
        messages = req_body.get('messages', [])
        provider_choice = req_body.get('provider', 'auto')
        model_override = req_body.get('model')
        temperature = req_body.get('temperature')
        max_output_tokens = req_body.get('max_output_tokens')
        max_context_tokens = req_body.get('max_context_tokens')
        system_prompt = req_body.get('system_prompt')
        
        if not messages:
            return func.HttpResponse(
                json.dumps({"error": "No messages provided"}),
                status_code=400,
                mimetype="application/json",
                headers=_cors_headers()
            )

        # Validate messages format
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid message format. Expected {role, content}"}),
                    status_code=400,
                    mimetype="application/json",
                    headers=_cors_headers()
                )

        # Get provider (with overrides)
        provider, info = detect_provider(
            explicit=provider_choice,
            model_override=model_override,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        
        logging.info(f'Using provider: {info.name}, model: {info.model}')

        # Prune messages to fit context and reserve space for output tokens
        pruned_messages, stats, system_msg = prune_messages(
            messages=messages,
            provider=info.name,
            model=info.model,
            max_context_tokens=max_context_tokens,
            reserve_output_tokens=int(max_output_tokens) if max_output_tokens else 1024,
            system_prompt=system_prompt,
        )

        # Get completion (non-streaming for HTTP simplicity)
        result = provider.complete(pruned_messages, stream=False)
        
        # If result is still a generator, consume it
        if hasattr(result, '__iter__') and not isinstance(result, str):
            result = ''.join(result)

        response_data = {
            "response": result,
            "provider": info.name,
            "model": info.model,
            "pruning": {
                "original_tokens": stats.original_tokens,
                "pruned_tokens": stats.pruned_tokens,
                "removed_count": stats.removed_count,
                "budget": stats.budget,
                "reserve_output_tokens": stats.reserve_output_tokens,
            }
        }

        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json",
            headers=_cors_headers()
        )

    except ValueError as ve:
        logging.error(f'Validation error: {str(ve)}')
        return func.HttpResponse(
            json.dumps({"error": f"Validation error: {str(ve)}"}),
            status_code=400,
            mimetype="application/json",
            headers=_cors_headers()
        )
    except RuntimeError as re:
        logging.error(f'Runtime error: {str(re)}')
        return func.HttpResponse(
            json.dumps({"error": f"Configuration error: {str(re)}"}),
            status_code=500,
            mimetype="application/json",
            headers=_cors_headers()
        )
    except Exception as e:
        logging.error(f'Unexpected error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=_cors_headers()
        )


@app.route(route="chat", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def chat_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests"""
    return func.HttpResponse(
        "",
        status_code=200,
        headers=_cors_headers()
    )


def _cors_headers():
    """Common CORS headers for all responses"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }


# =============================================================================
# Streaming Chat API (Server-Sent Events compatible)
# =============================================================================

@app.route(route="chat/stream", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def chat_stream(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/chat/stream with JSON body similar to /api/chat.
    Returns text/event-stream; each event is a JSON object with a 'delta' field.
    """
    logging.info('Chat stream function invoked')
    try:
        body = req.get_json()
        messages = body.get('messages', [])
        provider_choice = body.get('provider', 'auto')
        model_override = body.get('model')
        temperature = body.get('temperature')
        max_output_tokens = body.get('max_output_tokens')
        max_context_tokens = body.get('max_context_tokens')
        system_prompt = body.get('system_prompt')

        if not messages:
            return func.HttpResponse(
                json.dumps({"error": "No messages provided"}),
                status_code=400,
                mimetype="application/json",
                headers=_cors_headers(),
            )

        provider, info = detect_provider(
            explicit=provider_choice,
            model_override=model_override,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        pruned_messages, stats, _ = prune_messages(
            messages=messages,
            provider=info.name,
            model=info.model,
            max_context_tokens=max_context_tokens,
            reserve_output_tokens=int(max_output_tokens) if max_output_tokens else 1024,
            system_prompt=system_prompt,
        )

        gen = provider.complete(pruned_messages, stream=True)

        def sse_iterable():  # generator yielding bytes
            try:
                # Send a prelude event with meta
                pre = {
                    "provider": info.name,
                    "model": info.model,
                    "pruning": {
                        "original_tokens": stats.original_tokens,
                        "pruned_tokens": stats.pruned_tokens,
                        "removed_count": stats.removed_count,
                        "budget": stats.budget,
                        "reserve_output_tokens": stats.reserve_output_tokens,
                    }
                }
                yield (f"event: meta\n" f"data: {json.dumps(pre)}\n\n").encode("utf-8")

                for chunk in gen:
                    if not chunk:
                        continue
                    payload = json.dumps({"delta": chunk})
                    yield (f"data: {payload}\n\n").encode("utf-8")

                yield b"event: done\ndata: {}\n\n"
            except Exception as e:
                err = json.dumps({"error": str(e)})
                yield (f"event: error\n" f"data: {err}\n\n").encode("utf-8")

        return func.HttpResponse(
            body=sse_iterable(),
            status_code=200,
            mimetype="text/event-stream",
            headers={**_cors_headers(), "Cache-Control": "no-cache"},
        )

    except Exception as e:  # noqa: BLE001
        logging.error(f"chat/stream error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers=_cors_headers(),
        )


# =============================================================================
# Backend Control - Start/Status
# =============================================================================

@app.route(route="start-backend", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def start_backend(req: func.HttpRequest) -> func.HttpResponse:
    """Start the Azure Functions backend (already running if this endpoint responds)"""
    logging.info('Backend start request received')
    
    # If this endpoint responds, the backend is already running
    return func.HttpResponse(
        json.dumps({
            'status': 'already_running',
            'message': 'Backend is already running (this endpoint is responding)'
        }),
        mimetype='application/json',
        status_code=200
    )


# =============================================================================
# Status API - Health and environment diagnostics
# =============================================================================

@app.route(route="ai/status", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ai_status(req: func.HttpRequest) -> func.HttpResponse:
    """Health / status endpoint for provider readiness and environment diagnostics.

    GET /api/ai/status

    Returns JSON describing:
      - active_provider: which provider auto-detect selects (azure|openai|local|lora)
      - model: resolved model/deployment or LoRA adapter path
      - env: presence of key environment variables for Azure/OpenAI
      - ml_inprocess: whether ML libraries are importable in-process
      - venv: path to local venv python and whether key ML libs are installed there
      - lora: default adapter path readiness indicators
      - assets and known endpoints
    """
    try:
        # Environment flags
        azure_env = {
            "AZURE_OPENAI_API_KEY": bool(os.getenv("AZURE_OPENAI_API_KEY")),
            "AZURE_OPENAI_ENDPOINT": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
            "AZURE_OPENAI_DEPLOYMENT": bool(os.getenv("AZURE_OPENAI_DEPLOYMENT")),
            "AZURE_OPENAI_API_VERSION": bool(os.getenv("AZURE_OPENAI_API_VERSION")),
        }
        openai_env = {
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "OPENAI_MODEL": bool(os.getenv("OPENAI_MODEL")),
        }

        # ML availability in-process
        inproc_ml = {
            "torch": _iu.find_spec("torch") is not None,
            "transformers": _iu.find_spec("transformers") is not None,
            "peft": _iu.find_spec("peft") is not None,
        }

        repo_root = Path(__file__).resolve().parent
        venv_python = repo_root / "venv" / "Scripts" / "python.exe"
        venv_info = {"path": str(venv_python), "exists": venv_python.exists(), "packages": {}, "error": None}

        if venv_info["exists"]:
            try:
                code = (
                    "import json, importlib.util, importlib.metadata as md;"
                    "mods=['torch','transformers','peft'];"
                    "avail={m:(importlib.util.find_spec(m) is not None) for m in mods};"
                    "vers={};"
                    "\nfor m in mods:\n\t"
                    "\n\ttry:\n\t\tvers[m]=md.version(m)\n\texcept Exception:\n\t\tvers[m]=None;"
                    "print(json.dumps({'available':avail,'versions':vers}))"
                )
                proc = subprocess.run([str(venv_python), "-c", code], capture_output=True, text=True, timeout=12)
                if proc.returncode == 0:
                    data = json.loads(proc.stdout.strip() or "{}")
                    venv_info["packages"] = data
                else:
                    venv_info["error"] = proc.stderr.strip() or f"exit {proc.returncode}"
            except Exception as e:  # noqa: BLE001
                venv_info["error"] = str(e)

        # LoRA adapter defaults
        lora_default = repo_root / "data_out" / "lora_training" / "lora_adapter"
        adapter_cfg = lora_default / "adapter_config.json"
        tokenizer_dir = lora_default.parent / "tokenizer"
        lora_info = {
            "default_adapter_path": str(lora_default),
            "exists": lora_default.exists(),
            "adapter_config_exists": adapter_cfg.exists(),
            "tokenizer_dir_exists": tokenizer_dir.exists(),
            "base_model": None,
            "inproc_ready": all(inproc_ml.values()),
            "subprocess_ready": (
                venv_info.get("exists")
                and bool(venv_info.get("packages", {}).get("available", {}).get("torch"))
                and bool(venv_info.get("packages", {}).get("available", {}).get("transformers"))
                and bool(venv_info.get("packages", {}).get("available", {}).get("peft"))
            ),
        }
        if lora_info["adapter_config_exists"]:
            try:
                with open(adapter_cfg, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                lora_info["base_model"] = cfg.get("base_model_name_or_path")
            except Exception:
                pass

        # Detect active provider
        provider, info = detect_provider(explicit="auto")

        # Assets
        chat_web_html = (repo_root / "chat-web" / "index.html").exists()
        chat_web_js = (repo_root / "chat-web" / "chat.js").exists()

        payload = {
            "active_provider": info.name,
            "model": info.model,
            "env": {
                "azure_openai": azure_env,
                "openai": openai_env,
                "local_fallback": True,
            },
            "ml_inprocess": inproc_ml,
            "lora": lora_info,
            "venv": venv_info,
            "temperature": os.getenv("CHAT_TEMPERATURE", "0.7"),
            "server": {
                "executable": sys.executable,
                "python_version": sys.version,
                "cwd": os.getcwd(),
            },
            "assets": {
                "chat_web_html": chat_web_html,
                "chat_web_js": chat_web_js,
            },
            "endpoints": [
                "/api/chat-web",
                "/api/chat-web/chat.js",
                "/api/chat",
                "/api/chat/stream",
                "/api/ai/status",
            ],
            "status": "ok",
        }

        return func.HttpResponse(
            json.dumps(payload),
            status_code=200,
            mimetype="application/json",
            headers=_cors_headers(),
        )

    except Exception as e:  # noqa: BLE001
        logging.error(f"ai/status error: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "error": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers=_cors_headers(),
        )
