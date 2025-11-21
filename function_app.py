import azure.functions as func
import json
import logging
import os
import sys
from pathlib import Path
import subprocess
import importlib.util as _iu
import time
from typing import Optional

# -----------------------------------------------------------------------------
# Early Telemetry Initialization (non-fatal if unavailable)
# -----------------------------------------------------------------------------
try:  # pragma: no cover - defensive import
    from shared.telemetry import init_telemetry
    init_telemetry()
except Exception as _telemetry_err:  # noqa: BLE001
    logging.warning(f"[startup] Telemetry init skipped: {_telemetry_err}")

# -----------------------------------------------------------------------------
# Optional Cosmos Client import (lazy health + persistence)
# -----------------------------------------------------------------------------
try:  # pragma: no cover - defensive import
    from shared import cosmos_client
except Exception as _cosmos_err:  # noqa: BLE001
    cosmos_client = None  # type: ignore
    logging.info(f"[startup] Cosmos client unavailable: {_cosmos_err}")

# Memory / DB logging utilities (fault-tolerant)
try:
    from shared.db_logging import log_chat_message_safe
except Exception:  # pragma: no cover - if shared not on path
    log_chat_message_safe = None  # type: ignore
try:
    from shared.chat_memory import (
        generate_embedding,
        fetch_similar_messages,
        store_embedding,
    )
except Exception:
    # Provide graceful degradations so endpoint still works
    def generate_embedding(text: str):  # type: ignore
        return []
    def fetch_similar_messages(query_emb, top_k=5, session_id=None):  # type: ignore
        return []
    def store_embedding(message_id, embedding, model):  # type: ignore
        return False

# Add talk-to-ai to path so we can import chat_providers
talk_to_ai_path = Path(__file__).resolve().parent / "talk-to-ai" / "src"
sys.path.insert(0, str(talk_to_ai_path))

# Add quantum-ai to path
quantum_ai_path = Path(__file__).resolve().parent / "quantum-ai" / "src"
sys.path.insert(0, str(quantum_ai_path))

from chat_providers import detect_provider, RoleMessage
from token_utils import prune_messages

# OpenTelemetry tracer (optional)
try:  # pragma: no cover
    from opentelemetry import trace  # type: ignore
    _tracer = trace.get_tracer("qai.functions")
except Exception:  # pragma: no cover - library optional
    _tracer = None

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

    # Telemetry span setup (optional)
    span_ctx = (
        _tracer.start_as_current_span("chat_request") if _tracer is not None else None
    )
    try:
        if span_ctx:
            span_ctx.__enter__()
        # Parse request
        req_body = req.get_json()
        messages = req_body.get('messages', [])
        session_id = req_body.get('session_id')  # Optional client-provided session identifier
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

        # =============================
        # Memory Retrieval (SQL-backed)
        # =============================
        user_message_content = next((m['content'] for m in reversed(messages) if m.get('role') == 'user'), None)
        memory_messages: list[dict] = []
        user_embedding = None
        if user_message_content:
            try:
                user_embedding = generate_embedding(user_message_content)
                similar = fetch_similar_messages(user_embedding, top_k=5, session_id=session_id)
                for idx, sm in enumerate(similar):
                    # Inject prior memory as system messages (helps provider summarize past context)
                    memory_messages.append({
                        "role": "system",
                        "content": f"[Memory #{idx+1} | similarity={sm.get('similarity'):.3f}] {sm.get('content')}"
                    })
            except Exception as mem_err:  # noqa: BLE001
                logging.warning(f"Memory retrieval failed: {mem_err}")

        # Compose final message list with memory injected before existing system/user messages
        if memory_messages:
            messages = memory_messages + messages

        # Get provider (with overrides) AFTER memory injection so pruning sees augmented context
        provider, info = detect_provider(
            explicit=provider_choice,
            model_override=model_override,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        logging.info(f'Using provider: {info.name}, model: {info.model}')

        start_time = time.perf_counter()
        pruned_messages, stats, system_msg = prune_messages(
            messages=messages,
            provider=info.name,
            model=info.model,
            max_context_tokens=max_context_tokens,
            reserve_output_tokens=int(max_output_tokens) if max_output_tokens else 1024,
            system_prompt=system_prompt,
        )
        # Completion (non-streaming for HTTP simplicity)
        result = provider.complete(pruned_messages, stream=False)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # If result is still a generator, consume it
        if hasattr(result, '__iter__') and not isinstance(result, str):
            result = ''.join(result)

        # =============================
        # Logging + Embedding Storage
        # =============================
        if log_chat_message_safe:
            try:
                # Log user message first (so conversation exists), then assistant reply
                if user_message_content:
                    user_log = log_chat_message_safe(
                        session_id=session_id,
                        provider=info.name,
                        model=info.model,
                        role="user",
                        content=user_message_content,
                        execution_time_ms=None,
                        finish_reason=None,
                    )
                    if user_log.get("success") and user_embedding:
                        try:
                            store_embedding(user_log.get("message_id"), user_embedding, model=info.model)
                        except Exception as se:  # noqa: BLE001
                            logging.warning(f"Store embedding failed: {se}")
                # Log assistant message
                assistant_log = log_chat_message_safe(
                    session_id=session_id,
                    provider=info.name,
                    model=info.model,
                    role="assistant",
                    content=str(result),
                    execution_time_ms=duration_ms,
                    finish_reason="stop",
                )
            except Exception as log_err:  # noqa: BLE001
                logging.warning(f"Chat DB logging failed: {log_err}")

        # Cosmos persistence (feature-flagged)
        cosmos_written = False
        user_id = session_id or "anonymous"
        if cosmos_client and os.getenv("QAI_ENABLE_COSMOS", "false").lower() == "true":
            try:
                if os.getenv("QAI_COSMOS_PERSIST_STRATEGY", "messages") == "messages":
                    # Persist user and assistant messages separately
                    last_user_msg = next((m for m in reversed(messages) if m.get("role") == "user"), None)
                    if last_user_msg:
                        cosmos_client.record_chat_message(user_id, {
                            "role": "user",
                            "content": user_message_content,
                            "timestamp": time.time(),
                        }, provider=info.name, model=info.model)
                    cosmos_client.record_chat_message(user_id, {
                        "role": "assistant",
                        "content": str(result),
                        "timestamp": time.time(),
                    }, provider=info.name, model=info.model)
                    cosmos_written = True
                else:
                    # Session-level persistence
                    cosmos_client.record_chat_session(user_id, messages, provider=info.name, model=info.model)
                    cosmos_written = True
            except Exception as c_err:  # noqa: BLE001
                logging.warning(f"[cosmos] Persistence failed: {c_err}")

        response_data = {
            "response": result,
            "provider": info.name,
            "model": info.model,
            "memory_injected": len(memory_messages),
            "pruning": {
                "original_tokens": stats.original_tokens,
                "pruned_tokens": stats.pruned_tokens,
                "removed_count": stats.removed_count,
                "budget": stats.budget,
                "reserve_output_tokens": stats.reserve_output_tokens,
            },
            "telemetry_span": bool(_tracer),
            "duration_ms": duration_ms,
            "cosmos_persisted": cosmos_written,
        }

        if span_ctx and hasattr(span_ctx, "__exit__"):
            try:
                # Annotate span
                span = trace.get_current_span() if _tracer else None  # type: ignore
                if span:
                    span.set_attribute("provider", info.name)
                    span.set_attribute("model", info.model)
                    span.set_attribute("duration_ms", duration_ms)
                    span.set_attribute("memory_injected", len(memory_messages))
                    span.set_attribute("cosmos_persisted", cosmos_written)
            finally:
                span_ctx.__exit__(None, None, None)

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

        # Cosmos status (lazy health)
        cosmos_status = None
        if cosmos_client:
            try:
                cosmos_status = cosmos_client.health()
            except Exception as cs_err:  # noqa: BLE001
                cosmos_status = {"enabled": False, "error": str(cs_err)}

        # Telemetry status
        try:
            from shared.telemetry import is_enabled as _telemetry_is_enabled  # type: ignore
            telemetry_info = {"enabled": _telemetry_is_enabled()}
        except Exception:
            telemetry_info = {"enabled": False}

        # Quantum environment status (non-blocking, gated by optional env var)
        quantum_info = {
            "enabled": False,
            "qiskit": None,
            "pennylane": None,
            "azure_quantum": {
                "workspace_connected": False,
                "backends": [],
                "attempted": False,
                "error": None,
            },
            "conflict": None,
        }
        try:  # gather local versions
            import qiskit  # type: ignore
            quantum_info["qiskit"] = getattr(qiskit, "__version__", None)
            quantum_info["enabled"] = True
        except Exception as _qe:
            quantum_info["qiskit"] = f"error: {_qe}"  # noqa: BLE001
        try:
            import pennylane  # type: ignore
            quantum_info["pennylane"] = getattr(pennylane, "__version__", None)
        except Exception:
            pass
        # Conflict detection using validate script (import functions defensively)
        try:
            from quantum_ai.scripts.validate_qiskit_env import detect_conflict  # type: ignore
        except Exception:
            # Fallback manual conflict heuristic
            def detect_conflict(versions):
                groups = {"legacy": []}
                if versions.get("qiskit") and str(versions.get("qiskit")).startswith("1.") and versions.get("qiskit_aer"):
                    return {"conflict": True}
                return {"conflict": False}
        try:
            # Build synthetic versions map for conflict check
            versions_map = {}
            for name in ["qiskit", "qiskit_aer", "qiskit_machine_learning"]:
                try:
                    mod = __import__(name)
                    versions_map[name] = getattr(mod, "__version__", "unknown")
                except Exception as ie:  # noqa: BLE001
                    versions_map[name] = f"error: {ie}"
            conflict_meta = detect_conflict(versions_map)
            quantum_info["conflict"] = conflict_meta.get("conflict")
        except Exception as _ce:  # noqa: BLE001
            quantum_info["conflict"] = f"error: {_ce}"

        # Optional Azure Quantum backend probing (requires env flag to avoid latency)
        if os.getenv("QAI_STATUS_CONNECT_AZURE_QUANTUM", "false").lower() == "true":
            quantum_info["azure_quantum"]["attempted"] = True
            try:
                from quantum_ai.src.azure_quantum_integration import AzureQuantumIntegration  # type: ignore
                cfg_path = Path(__file__).resolve().parent / "quantum-ai" / "config" / "quantum_config.yaml"
                if cfg_path.exists():
                    aq = AzureQuantumIntegration(str(cfg_path))
                    aq.connect()
                    bnames = aq.list_backends()[:8]
                    quantum_info["azure_quantum"].update({
                        "workspace_connected": True,
                        "backends": bnames,
                    })
                else:
                    quantum_info["azure_quantum"]["error"] = "quantum_config.yaml missing"
            except Exception as aq_err:  # noqa: BLE001
                quantum_info["azure_quantum"]["error"] = str(aq_err)

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
            "cosmos": cosmos_status,
            "telemetry": telemetry_info,
            "quantum": quantum_info,
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


# =============================================================================
# Quantum AI Endpoints - Advanced quantum computing features
# =============================================================================

@app.route(route="quantum/classify", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def quantum_classify(req: func.HttpRequest) -> func.HttpResponse:
    """
    Quantum classification endpoint.
    
    POST /api/quantum/classify
    Body: {
        "features": [0.1, 0.5, 0.3, ...],  // Feature vector
        "n_qubits": 4,  // Optional
        "n_layers": 2   // Optional
    }
    
    Response: {
        "classification": "positive|negative|neutral",
        "confidence": 0.85,
        "quantum_state": {...}
    }
    """
    logging.info('Quantum classify endpoint invoked')
    
    try:
        # Import quantum modules
        try:
            from quantum_classifier import QuantumClassifier
            import torch
            import numpy as np
        except ImportError as e:
            return func.HttpResponse(
                json.dumps({"error": f"Quantum dependencies not available: {e}"}),
                status_code=500,
                mimetype="application/json",
                headers=_cors_headers()
            )
        
        # Parse request
        req_body = req.get_json()
        features = req_body.get('features', [])
        n_qubits = req_body.get('n_qubits', 4)
        n_layers = req_body.get('n_layers', 2)
        
        if not features:
            return func.HttpResponse(
                json.dumps({"error": "No features provided"}),
                status_code=400,
                mimetype="application/json",
                headers=_cors_headers()
            )
        
        # Initialize quantum classifier
        classifier = QuantumClassifier()
        
        # Prepare features
        feature_array = np.array(features[:n_qubits])
        if len(feature_array) < n_qubits:
            feature_array = np.pad(feature_array, (0, n_qubits - len(feature_array)))
        
        # Convert to torch tensor and scale to [0, 2π]
        inputs = torch.tensor(feature_array, dtype=torch.float32) * 2 * np.pi
        
        # Create random weights (in production, use trained weights)
        weights = torch.randn(n_layers, n_qubits, 2, dtype=torch.float32) * 0.1
        
        # Run quantum circuit
        output = classifier.forward(inputs.unsqueeze(0), weights)
        
        # Interpret results
        avg_value = float(output.mean())
        confidence = abs(avg_value)
        
        if avg_value > 0.3:
            classification = "positive"
        elif avg_value < -0.3:
            classification = "negative"
        else:
            classification = "neutral"
        
        response_data = {
            "classification": classification,
            "confidence": confidence,
            "quantum_state": {
                "expectation_values": output.tolist(),
                "average": avg_value,
                "n_qubits": n_qubits,
                "n_layers": n_layers
            }
        }
        
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json",
            headers=_cors_headers()
        )
        
    except Exception as e:
        logging.error(f'Quantum classify error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Quantum classification failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=_cors_headers()
        )


@app.route(route="quantum/circuit", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def quantum_circuit(req: func.HttpRequest) -> func.HttpResponse:
    """
    Create and visualize a quantum circuit.
    
    POST /api/quantum/circuit
    Body: {
        "n_qubits": 4,
        "n_layers": 2,
        "entanglement": "linear|circular|full"
    }
    
    Response: {
        "circuit_info": {...},
        "gates": [...],
        "visualization": "text representation"
    }
    """
    logging.info('Quantum circuit endpoint invoked')
    
    try:
        req_body = req.get_json()
        n_qubits = req_body.get('n_qubits', 4)
        n_layers = req_body.get('n_layers', 2)
        entanglement = req_body.get('entanglement', 'linear')
        
        # Create circuit description
        gates = []
        
        # Input encoding layer
        for i in range(n_qubits):
            gates.append({
                "type": "RY",
                "qubit": i,
                "layer": 0,
                "parameter": "input[i]"
            })
        
        # Variational layers
        for layer in range(n_layers):
            # Rotation gates
            for i in range(n_qubits):
                gates.append({
                    "type": "RY",
                    "qubit": i,
                    "layer": layer + 1,
                    "parameter": f"θ_{layer}_{i}_0"
                })
                gates.append({
                    "type": "RZ",
                    "qubit": i,
                    "layer": layer + 1,
                    "parameter": f"θ_{layer}_{i}_1"
                })
            
            # Entanglement gates
            if entanglement == 'linear':
                for i in range(n_qubits - 1):
                    gates.append({
                        "type": "CNOT",
                        "control": i,
                        "target": i + 1,
                        "layer": layer + 1
                    })
            elif entanglement == 'circular':
                for i in range(n_qubits):
                    gates.append({
                        "type": "CNOT",
                        "control": i,
                        "target": (i + 1) % n_qubits,
                        "layer": layer + 1
                    })
            elif entanglement == 'full':
                for i in range(n_qubits):
                    for j in range(i + 1, n_qubits):
                        gates.append({
                            "type": "CNOT",
                            "control": i,
                            "target": j,
                            "layer": layer + 1
                        })
        
        # Measurements
        for i in range(n_qubits):
            gates.append({
                "type": "Measure",
                "qubit": i,
                "layer": n_layers + 1,
                "observable": "PauliZ"
            })
        
        # Create text visualization
        visualization = f"Quantum Circuit ({n_qubits} qubits, {n_layers} layers, {entanglement} entanglement)\n"
        visualization += "=" * 60 + "\n\n"
        
        for layer in range(n_layers + 2):
            visualization += f"Layer {layer}:\n"
            layer_gates = [g for g in gates if g.get('layer') == layer]
            for gate in layer_gates:
                if gate['type'] in ['RY', 'RZ']:
                    visualization += f"  {gate['type']}({gate['parameter']}) on qubit {gate['qubit']}\n"
                elif gate['type'] == 'CNOT':
                    visualization += f"  CNOT: control={gate['control']}, target={gate['target']}\n"
                elif gate['type'] == 'Measure':
                    visualization += f"  Measure qubit {gate['qubit']} ({gate['observable']})\n"
            visualization += "\n"
        
        response_data = {
            "circuit_info": {
                "n_qubits": n_qubits,
                "n_layers": n_layers,
                "entanglement": entanglement,
                "total_gates": len(gates),
                "depth": n_layers + 2
            },
            "gates": gates,
            "visualization": visualization
        }
        
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json",
            headers=_cors_headers()
        )
        
    except Exception as e:
        logging.error(f'Quantum circuit error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Circuit creation failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=_cors_headers()
        )


@app.route(route="quantum/info", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def quantum_info(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get quantum computing capabilities and status.
    
    GET /api/quantum/info
    
    Response: {
        "available": true,
        "backends": [...],
        "capabilities": {...}
    }
    """
    logging.info('Quantum info endpoint invoked')
    
    try:
        # Check if quantum modules are available
        try:
            from quantum_classifier import QuantumClassifier
            import pennylane as qml
            quantum_available = True
            
            # Get available backends
            backends = [
                {"name": "default.qubit", "description": "PennyLane default simulator", "type": "simulator"},
                {"name": "lightning.qubit", "description": "Fast C++ simulator", "type": "simulator"},
                {"name": "qiskit.aer", "description": "Qiskit Aer simulator", "type": "simulator"}
            ]
            
            capabilities = {
                "max_qubits": 20,
                "supports_gpu": False,
                "variational_circuits": True,
                "hybrid_models": True,
                "azure_quantum_ready": True
            }
            
        except ImportError as e:
            quantum_available = False
            backends = []
            capabilities = {}
        
        response_data = {
            "available": quantum_available,
            "backends": backends,
            "capabilities": capabilities,
            "quantum_provider": "quantum-enhanced-local",
            "version": "1.0.0"
        }
        
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json",
            headers=_cors_headers()
        )
        
    except Exception as e:
        logging.error(f'Quantum info error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get quantum info: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=_cors_headers()
        )

