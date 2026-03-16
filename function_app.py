# =============================================================================
# QAI Azure Functions Application
# =============================================================================
from token_utils import prune_messages
from chat_providers import detect_provider, RoleMessage
import azure.functions as func
import json
import logging
import os
import re
import sys
from pathlib import Path
import subprocess
import importlib.util as _iu
import time
from typing import Optional
from datetime import datetime

# Pre-compiled word split regex used in token/word counting hot paths.
_RE_WORD_SPLIT = re.compile(r"\S+")

# Import defensive import helper
from shared.import_helpers import safe_import, create_stub_function

# -----------------------------------------------------------------------------
# Optional unified SQL engine health + pool metrics (multi-database support)
# -----------------------------------------------------------------------------
sql_funcs = safe_import(
    'shared.sql_engine',
    import_names=('sql_health', 'engine_stats'),
    fallback_factory=create_stub_function
)
sql_health = sql_funcs['sql_health']
engine_stats = sql_funcs['engine_stats']

# -----------------------------------------------------------------------------
# Early Telemetry Initialization (non-fatal if unavailable)
# -----------------------------------------------------------------------------
telemetry_module = safe_import('shared.telemetry', log_failure=False)
if telemetry_module and hasattr(telemetry_module, 'init_telemetry'):
    try:
        telemetry_module.init_telemetry()
    except Exception as _telemetry_err:  # noqa: BLE001
        logging.warning(f"[startup] Telemetry init skipped: {_telemetry_err}")
else:
    logging.warning("[startup] Telemetry init skipped: module unavailable")

# Try to initialize generic OpenTelemetry tracing (best-effort)
tracing_module = safe_import('shared.tracing', log_failure=False)
if tracing_module and hasattr(tracing_module, 'init_tracing'):
    try:
        tracing_module.init_tracing(service_name="qai.functions")
    except Exception as _trace_err:  # noqa: BLE001 - don't fail on missing libs
        logging.debug(f"[startup] Tracing init skipped: {_trace_err}")
else:
    logging.debug("[startup] Tracing init skipped: module unavailable")

# -----------------------------------------------------------------------------
# Optional Cosmos Client import (lazy health + persistence)
# -----------------------------------------------------------------------------
cosmos_client = safe_import('shared.cosmos_client', log_failure=True)
if not cosmos_client:
    logging.info("[startup] Cosmos client unavailable")

# Memory / DB logging utilities (fault-tolerant)
db_logging = safe_import(
    'shared.db_logging',
    import_names=('log_chat_message_safe',),
    fallback_factory=lambda name: None
)
log_chat_message_safe = db_logging['log_chat_message_safe']

# Chat memory functions with graceful degradation
chat_memory_funcs = safe_import(
    'shared.chat_memory',
    import_names=('generate_embedding', 'fetch_similar_messages', 'store_embedding'),
    fallback_factory=lambda name: {
        'generate_embedding': lambda text: [],
        'fetch_similar_messages': lambda query_emb, top_k=5, session_id=None: [],
        'store_embedding': lambda message_id, embedding, model: False,
    }.get(name, lambda *args, **kwargs: None)
)
generate_embedding = chat_memory_funcs['generate_embedding']
fetch_similar_messages = chat_memory_funcs['fetch_similar_messages']
store_embedding = chat_memory_funcs['store_embedding']
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
        pass

# File caching for repeated JSON reads
try:
    from shared.file_cache import read_json_cached
except Exception:  # pragma: no cover
    # Fallback if file_cache not available
    def read_json_cached(file_path, ttl_seconds=60):  # type: ignore
        import json
        with open(file_path, 'r') as f:
            return json.load(f)
        return False

# Add talk-to-ai to path so we can import chat_providers
talk_to_ai_path = Path(__file__).resolve().parent / "ai-projects" / "chat-cli" / "src"
sys.path.insert(0, str(talk_to_ai_path))

# Add quantum-ai to path
quantum_ai_path = Path(__file__).resolve().parent / "ai-projects" / "quantum-ml" / "src"
sys.path.insert(0, str(quantum_ai_path))

# Add scripts to path for vision inference
scripts_path = Path(__file__).resolve().parent / "scripts"
sys.path.insert(0, str(scripts_path))

# -----------------------------------------------------------------------------
# Subscription Manager (optional)
# -----------------------------------------------------------------------------
try:  # pragma: no cover - defensive import
    from shared.subscription_manager import (
        get_subscription_manager,
        SubscriptionTier,
        Feature,
    )
    subscription_manager_available = True
except Exception as _sub_err:  # noqa: BLE001
    logging.info(f"[startup] Subscription manager unavailable: {_sub_err}")
    subscription_manager_available = False
    get_subscription_manager = None  # type: ignore


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
        html_path = Path(__file__).resolve().parent / "apps" / "chat" / "index.html"

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
        js_path = Path(__file__).resolve().parent / "apps" / "chat" / "chat.js"

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
        _tracer.start_as_current_span(
            "chat_request") if _tracer is not None else None
    )
    try:
        if span_ctx:
            span_ctx.__enter__()
        # Parse request
        req_body = req.get_json()
        messages = req_body.get('messages', [])
        # Optional client-provided session identifier
        session_id = req_body.get('session_id')
        provider_choice = req_body.get(
            'provider', os.getenv('QAI_PROVIDER', 'auto'))
        model_override = req_body.get('model', os.getenv('QAI_LORA_MODEL'))
        temperature = req_body.get('temperature')
        max_output_tokens = req_body.get('max_output_tokens')
        max_context_tokens = req_body.get('max_context_tokens')
        system_prompt = req_body.get('system_prompt')

        if not messages:
            return func.HttpResponse(
                json.dumps({"error": "No messages provided"}),
                status_code=400,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )

        # Validate messages format
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                return func.HttpResponse(
                    json.dumps(
                        {"error": "Invalid message format. Expected {role, content}"}),
                    status_code=400,
                    mimetype="application/json",
                    headers=create_cors_response_headers()
                )

        # =============================
        # Memory Retrieval (SQL-backed)
        # =============================
        user_message_content = next(
            (m['content'] for m in reversed(messages) if m.get('role') == 'user'), None)
        memory_messages: list[dict] = []
        user_embedding = None
        if user_message_content:
            try:
                user_embedding = generate_embedding(user_message_content)
                similar = fetch_similar_messages(
                    user_embedding, top_k=5, session_id=session_id)
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
            reserve_output_tokens=int(
                max_output_tokens) if max_output_tokens else 1024,
            system_prompt=system_prompt,
        )
        # Completion (non-streaming for HTTP simplicity)
        result = provider.complete(pruned_messages, stream=False)
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # If result is still a generator, consume it
        if hasattr(result, '__iter__') and not isinstance(result, str):
            result = ''.join(result)

        # =============================
        # Self-Learning: Log conversation for training
        # =============================
        try:
            logs_dir = Path(__file__).resolve().parent / "talk-to-ai" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)

            # Create timestamped log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = logs_dir / \
                f"chat_{timestamp}_{session_id or 'anonymous'}.jsonl"

            # Append conversation to log
            with open(log_file, "a", encoding="utf-8") as f:
                # Log user message
                if user_message_content:
                    f.write(json.dumps({
                        "role": "user",
                        "content": user_message_content,
                        "timestamp": datetime.now().isoformat(),
                        "provider": info.name,
                        "model": info.model
                    }) + "\n")
                # Log assistant response
                f.write(json.dumps({
                    "role": "assistant",
                    "content": str(result),
                    "timestamp": datetime.now().isoformat(),
                    "provider": info.name,
                    "model": info.model
                }) + "\n")
        except Exception as log_err:
            logging.warning(
                f"Self-learning conversation logging failed: {log_err}")

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
                            store_embedding(user_log.get(
                                "message_id"), user_embedding, model=info.model)
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
                    last_user_msg = next((m for m in reversed(
                        messages) if m.get("role") == "user"), None)
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
                    cosmos_client.record_chat_session(
                        user_id, messages, provider=info.name, model=info.model)
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
            headers=create_cors_response_headers()
        )

    except ValueError as ve:
        logging.error(f'Validation error: {str(ve)}')
        return func.HttpResponse(
            json.dumps({"error": f"Validation error: {str(ve)}"}),
            status_code=400,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    except RuntimeError as re:
        logging.error(f'Runtime error: {str(re)}')
        return func.HttpResponse(
            json.dumps({"error": f"Configuration error: {str(re)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    except Exception as e:
        logging.error(f'Unexpected error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="chat", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def chat_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests"""
    return func.HttpResponse(
        "",
        status_code=200,
        headers=create_cors_response_headers()
    )


def create_cors_response_headers():
    """Create common CORS headers for all responses."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }


# =============================================================================
# Automation Tool Endpoints: Resource Monitor, Model Deployer, Results Exporter, Evaluation
# =============================================================================

@app.route(route="resource-monitor", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def resource_monitor_status(req: func.HttpRequest) -> func.HttpResponse:
    """Return latest resource monitor snapshot."""
    try:
        snap_path = Path(__file__).resolve().parent / \
            "data_out" / "resource_monitor_snapshot.json"
        if snap_path.exists():
            # Use cached read with 60s TTL (resource snapshots change infrequently)
            data = read_json_cached(snap_path, ttl_seconds=60)
            if data:
                return func.HttpResponse(json.dumps(data), status_code=200, mimetype="application/json", headers=create_cors_response_headers())
            else:
                return func.HttpResponse(json.dumps({"error": "Failed to load snapshot"}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())
        else:
            return func.HttpResponse(json.dumps({"error": "No snapshot found"}), status_code=404, mimetype="application/json", headers=create_cors_response_headers())
    except Exception as e:
        logging.error(f"Error reading resource snapshot: {e}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())


@app.route(route="model-deployer/status", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def model_deployer_status(req: func.HttpRequest) -> func.HttpResponse:
    """Return model deployer registry status."""
    try:
        reg_path = Path(__file__).resolve().parent / \
            "deployed_models" / "model_registry.json"
        if reg_path.exists():
            with open(reg_path, "r") as f:
                data = json.load(f)
            return func.HttpResponse(json.dumps(data), status_code=200, mimetype="application/json", headers=create_cors_response_headers())
        else:
            return func.HttpResponse(json.dumps({"error": "No registry found"}), status_code=404, mimetype="application/json", headers=create_cors_response_headers())
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())


@app.route(route="results-export", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def results_export(req: func.HttpRequest) -> func.HttpResponse:
    """Return latest results export (all orchestrators)."""
    try:
        res_path = Path(__file__).resolve().parent / \
            "exports" / "all_orchestrators.json"
        if res_path.exists():
            with open(res_path, "r") as f:
                data = json.load(f)
            return func.HttpResponse(json.dumps(data), status_code=200, mimetype="application/json", headers=create_cors_response_headers())
        else:
            return func.HttpResponse(json.dumps({"error": "No results found"}), status_code=404, mimetype="application/json", headers=create_cors_response_headers())
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())


@app.route(route="evaluation-results", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def evaluation_results(req: func.HttpRequest) -> func.HttpResponse:
    """Return latest batch evaluation results."""
    try:
        eval_path = Path(__file__).resolve().parent / \
            "data_out" / "evaluation_results.json"
        if eval_path.exists():
            with open(eval_path, "r") as f:
                data = json.load(f)
            return func.HttpResponse(json.dumps(data), status_code=200, mimetype="application/json", headers=create_cors_response_headers())
        else:
            return func.HttpResponse(json.dumps({"error": "No evaluation results found"}), status_code=404, mimetype="application/json", headers=create_cors_response_headers())
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())


# =============================================================================
# Streaming Chat API (Server-Sent Events compatible)
# =============================================================================

# Movement command patterns - optimized with frozensets for O(1) lookups
_WALK_LEFT = frozenset(['[aria:walk:left]', 'walk left'])
_WALK_RIGHT = frozenset(['[aria:walk:right]', 'walk right'])
_WALK_UP = frozenset(['[aria:walk:up]', 'walk up'])
_WALK_DOWN = frozenset(['[aria:walk:down]', 'walk down'])
_MOVE_LEFT = frozenset(['[aria:move:left]', 'aria move left'])
_MOVE_RIGHT = frozenset(['[aria:move:right]', 'aria move right'])
_MOVE_UP = frozenset(['[aria:move:up]', 'aria move up'])
_MOVE_DOWN = frozenset(['[aria:move:down]', 'aria move down'])
_CENTER = frozenset(['[aria:center]', 'go to center', 'move to center'])
_WAVE = frozenset(['[aria:wave]', 'aria wave'])
_JUMP = frozenset(['[aria:jump]', 'aria jump'])
_DANCE = frozenset(['[aria:dance]', 'aria dance'])

# Distance constants for movement commands
WALK_DISTANCE = 200  # pixels
MOVE_DISTANCE = 100  # pixels


def parse_movement_commands(text: str) -> dict:
    """Parse movement commands from AI response text.
    
    Uses pre-compiled frozensets for O(1) keyword matching.
    
    Args:
        text: AI response text to parse
        
    Returns:
        dict with 'commands' list, or empty dict if no commands found
    """
    lower_text = text.lower()
    commands = []

    # Movement commands - using frozenset intersection for fast matching
    if any(cmd in lower_text for cmd in _WALK_LEFT):
        commands.append(
            {'action': 'walk', 'direction': 'left', 'distance': WALK_DISTANCE})
    if any(cmd in lower_text for cmd in _WALK_RIGHT):
        commands.append(
            {'action': 'walk', 'direction': 'right', 'distance': WALK_DISTANCE})
    if any(cmd in lower_text for cmd in _WALK_UP):
        commands.append({'action': 'walk', 'direction': 'up', 'distance': WALK_DISTANCE})
    if any(cmd in lower_text for cmd in _WALK_DOWN):
        commands.append(
            {'action': 'walk', 'direction': 'down', 'distance': WALK_DISTANCE})

    if any(cmd in lower_text for cmd in _MOVE_LEFT):
        commands.append(
            {'action': 'move', 'direction': 'left', 'distance': MOVE_DISTANCE})
    if any(cmd in lower_text for cmd in _MOVE_RIGHT):
        commands.append(
            {'action': 'move', 'direction': 'right', 'distance': MOVE_DISTANCE})
    if any(cmd in lower_text for cmd in _MOVE_UP):
        commands.append({'action': 'move', 'direction': 'up', 'distance': MOVE_DISTANCE})
    if any(cmd in lower_text for cmd in _MOVE_DOWN):
        commands.append(
            {'action': 'move', 'direction': 'down', 'distance': MOVE_DISTANCE})

    # Position commands
    if any(cmd in lower_text for cmd in _CENTER):
        commands.append({'action': 'center'})

    # Action commands
    if any(cmd in lower_text for cmd in _WAVE):
        commands.append({'action': 'wave'})
    if any(cmd in lower_text for cmd in _JUMP):
        commands.append({'action': 'jump'})
    if any(cmd in lower_text for cmd in _DANCE):
        commands.append({'action': 'dance'})

    return {'commands': commands} if commands else {}


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
                headers=create_cors_response_headers(),
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
            reserve_output_tokens=int(
                max_output_tokens) if max_output_tokens else 1024,
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

                # We'll stream both textual deltas and token-level events when possible
                import re

                # Try to use tiktoken for token-level tokenization when available
                enc = None
                try:
                    import tiktoken as _tt
                    try:
                        from tiktoken import encoding_for_model
                        enc = encoding_for_model(info.model or "gpt-4o-mini")
                    except Exception:
                        enc = _tt.get_encoding("cl100k_base")
                except Exception:
                    enc = None

                cumulative_text = ""
                prev_token_count = 0
                prev_word_count = 0
                token_index = 0
                movement_commands_sent = False

                for chunk in gen:
                    if not chunk:
                        continue

                    # Raw textual delta (keep for compatibility)
                    payload = json.dumps({"delta": chunk})
                    yield (f"data: {payload}\n\n").encode("utf-8")

                    # Accumulate for tokenization; note: chunk may be partial
                    cumulative_text += chunk

                    # Check for movement commands periodically
                    if not movement_commands_sent and len(cumulative_text) > 20:
                        movement_data = parse_movement_commands(
                            cumulative_text)
                        if movement_data.get('commands'):
                            movement_event = json.dumps(movement_data)
                            yield (f"event: movement\ndata: {movement_event}\n\n").encode("utf-8")
                            movement_commands_sent = True

                    # Token-level events: prefer byte tokenization (tiktoken) when available
                    if enc is not None:
                        try:
                            tok_ids = enc.encode(cumulative_text)
                            new_ids = tok_ids[prev_token_count:]
                            if new_ids:
                                for tid in new_ids:
                                    try:
                                        txt = enc.decode([tid])
                                    except Exception:
                                        txt = ''
                                    evt = json.dumps(
                                        {"token_index": token_index, "token": txt, "cumulative": cumulative_text})
                                    yield (f"event: token\n" f"data: {evt}\n\n").encode("utf-8")
                                    token_index += 1
                                prev_token_count = len(tok_ids)
                        except Exception:
                            # degrade to word-level if full tokenization fails
                            enc = None

                    if enc is None:
                        # fallback: emit word-level token events (split by whitespace)
                        words = list(re.finditer(r"\S+", cumulative_text))
                        if len(words) > prev_word_count:
                            for w in words[prev_word_count:]:
                                token_text = w.group(0)
                                evt = json.dumps(
                                    {"token_index": token_index, "token": token_text, "cumulative": cumulative_text})
                                yield (f"event: token\n" f"data: {evt}\n\n").encode("utf-8")
                                token_index += 1
                            prev_word_count = len(words)

                yield b"event: done\ndata: {}\n\n"
            except Exception as e:
                err = json.dumps({"error": str(e)})
                yield (f"event: error\n" f"data: {err}\n\n").encode("utf-8")

        return func.HttpResponse(
            body=sse_iterable(),
            status_code=200,
            mimetype="text/event-stream",
            headers={**create_cors_response_headers(),
                     "Cache-Control": "no-cache"},
        )

    except Exception as e:  # noqa: BLE001
        logging.error(f"chat/stream error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers(),
        )


@app.route(route="tts", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def tts(req: func.HttpRequest) -> func.HttpResponse:
    """Synthesize text to audio using a remote TTS provider (Azure Speech preferred).

    POST /api/tts
    Body: { "text": "...", "voice": "Name", "rate": 1.0, "pitch": 1.0, "format": "wav" }

    Response: { "audio_base64": "...", "format": "wav", "timepoints": [{"word":"...","start_ms":0,"end_ms":123}, ...] }
    If remote TTS provider isn't available, returns 501 with explanation.
    """
    try:
        body = req.get_json() or {}
        text = (body.get('text') or '').strip()
        if not text:
            return func.HttpResponse(json.dumps({"error": "No text provided"}), status_code=400, mimetype="application/json", headers=create_cors_response_headers())

        # Optional voice/rate/pitch params
        voice = body.get('voice')
        rate = float(body.get('rate') or 1.0)
        pitch = float(body.get('pitch') or 1.0)
        out_format = (body.get('format') or 'wav').lower()

        # Prefer Azure Speech if configured
        az_key = os.getenv('AZURE_SPEECH_KEY') or os.getenv(
            'AZURE_SPEECH_API_KEY') or os.getenv('AZURE_SPEECH_SUBSCRIPTION')
        az_region = os.getenv(
            'AZURE_SPEECH_REGION') or os.getenv('AZURE_REGION')

        if az_key and az_region:
            try:
                import io
                import base64
                import wave
                import re
                try:
                    import azure.cognitiveservices.speech as speechsdk
                except Exception as e:
                    return func.HttpResponse(json.dumps({"error": "Azure Speech SDK not available on server (install azure-cognitiveservices-speech)"}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())

                # Configure speech
                scfg = speechsdk.SpeechConfig(
                    subscription=az_key, region=az_region)
                # force WAV output for simpler handling
                scfg.set_speech_synthesis_output_format(
                    speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
                if voice:
                    try:
                        scfg.speech_synthesis_voice_name = voice
                    except Exception:
                        pass

                synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=scfg, audio_config=None)

                # Do the synthesis
                result = synthesizer.speak_text_async(text).get()

                if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                    # Could be 'Canceled' with details
                    detail = getattr(result, 'error_details',
                                     None) or str(result.reason)
                    return func.HttpResponse(json.dumps({"error": "Synthesis failed", "detail": str(detail)}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())

                # Extract audio bytes
                stream = speechsdk.AudioDataStream(result)
                audio_bytes = stream.readall()

                # Compute approximate word timings by splitting text and sizing by character counts
                try:
                    f = io.BytesIO(audio_bytes)
                    with wave.open(f, 'rb') as wr:
                        framerate = wr.getframerate()
                        frames = wr.getnframes()
                    duration_s = frames / \
                        float(framerate) if framerate and frames else max(
                            0.2, len(text) * 0.02)
                except Exception:
                    duration_s = max(0.2, len(text) * 0.02)

                words = re.findall(r"\S+", text)
                total_chars = sum(len(w) for w in words) or 1
                timepoints = []
                cursor = 0.0
                for w in words:
                    proportion = len(w) / total_chars
                    dur = duration_s * proportion
                    start_ms = int(cursor * 1000)
                    end_ms = int((cursor + dur) * 1000)
                    timepoints.append(
                        {"word": w, "start_ms": start_ms, "end_ms": end_ms})
                    cursor += dur

                import base64 as _b64
                audio_b64 = _b64.b64encode(audio_bytes).decode('ascii')

                return func.HttpResponse(json.dumps({"audio_base64": audio_b64, "format": "wav", "timepoints": timepoints}), status_code=200, mimetype="application/json", headers=create_cors_response_headers())
            except Exception as e:
                logging.exception(f"TTS (Azure) synth failed: {e}")
                return func.HttpResponse(json.dumps({"error": f"TTS provider error: {e}"}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())

        # No remote TTS provider is configured. Attempt optional local fallbacks if enabled.
        enable_local = os.getenv('QAI_ENABLE_LOCAL_TTS', 'true').lower() in (
            'true', '1', 'yes', 'y')

        if enable_local:
            # Try pyttsx3 (offline, best on Windows) first
            try:
                try:
                    import tempfile
                    import base64
                    import io
                    import wave
                    import re
                    import pyttsx3
                except Exception:  # pyttsx3 not available
                    pyttsx3 = None

                if pyttsx3 is not None:
                    tmp = None
                    try:
                        tmp = tempfile.NamedTemporaryFile(
                            delete=False, suffix='.wav')
                        tmp_path = tmp.name
                        tmp.close()

                        engine = pyttsx3.init()
                        # Try to set rate (pyttsx3 rate is an int; we scale from given rate)
                        try:
                            engine.setProperty(
                                'rate', int(200 * (rate or 1.0)))
                        except Exception:
                            pass
                        # Try to select voice by name if provided
                        try:
                            if voice:
                                voices = engine.getProperty('voices') or []
                                for v in voices:
                                    try:
                                        if voice.lower() in (v.name or '').lower():
                                            engine.setProperty('voice', v.id)
                                            break
                                    except Exception:
                                        continue
                        except Exception:
                            pass

                        engine.save_to_file(text, tmp_path)
                        engine.runAndWait()

                        with open(tmp_path, 'rb') as fh:
                            audio_bytes = fh.read()

                        # compute approximate duration using wave reader
                        try:
                            f = io.BytesIO(audio_bytes)
                            with wave.open(f, 'rb') as wr:
                                framerate = wr.getframerate()
                                frames = wr.getnframes()
                            duration_s = frames / \
                                float(framerate) if framerate and frames else max(
                                    0.2, len(text) * 0.02)
                        except Exception:
                            duration_s = max(0.2, len(text) * 0.02)

                        words = re.findall(r"\S+", text)
                        total_chars = sum(len(w) for w in words) or 1
                        timepoints = []
                        cursor = 0.0
                        for w in words:
                            proportion = len(w) / total_chars
                            dur = duration_s * proportion
                            start_ms = int(cursor * 1000)
                            end_ms = int((cursor + dur) * 1000)
                            timepoints.append(
                                {"word": w, "start_ms": start_ms, "end_ms": end_ms})
                            cursor += dur

                        audio_b64 = base64.b64encode(
                            audio_bytes).decode('ascii')
                        return func.HttpResponse(json.dumps({"audio_base64": audio_b64, "format": "wav", "timepoints": timepoints}), status_code=200, mimetype="application/json", headers=create_cors_response_headers())
                    finally:
                        try:
                            if tmp is not None and tmp_path and os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                        except Exception:
                            pass

                # If pyttsx3 not available or failed, try gTTS (mp3 output)
                try:
                    import tempfile
                    import base64
                    import re
                    from gtts import gTTS
                except Exception:
                    gTTS = None

                if gTTS is not None:
                    tmp = None
                    try:
                        tmp = tempfile.NamedTemporaryFile(
                            delete=False, suffix='.mp3')
                        tmp_path = tmp.name
                        tmp.close()

                        tts_obj = gTTS(text=text)
                        tts_obj.save(tmp_path)

                        with open(tmp_path, 'rb') as fh:
                            audio_bytes = fh.read()

                        # approximate duration: fallback to char-count based estimate
                        duration_s = max(0.2, len(text) * 0.02)
                        words = re.findall(r"\S+", text)
                        total_chars = sum(len(w) for w in words) or 1
                        timepoints = []
                        cursor = 0.0
                        for w in words:
                            proportion = len(w) / total_chars
                            dur = duration_s * proportion
                            start_ms = int(cursor * 1000)
                            end_ms = int((cursor + dur) * 1000)
                            timepoints.append(
                                {"word": w, "start_ms": start_ms, "end_ms": end_ms})
                            cursor += dur

                        audio_b64 = base64.b64encode(
                            audio_bytes).decode('ascii')
                        return func.HttpResponse(json.dumps({"audio_base64": audio_b64, "format": "mp3", "timepoints": timepoints}), status_code=200, mimetype="application/json", headers=create_cors_response_headers())
                    finally:
                        try:
                            if tmp is not None and tmp_path and os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                        except Exception:
                            pass

            except Exception as e:
                logging.exception(f"Local fallback TTS failed: {e}")
                return func.HttpResponse(json.dumps({"error": f"Local TTS provider failed: {e}"}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())

        # If we reach here remote + local TTS are unavailable
        return func.HttpResponse(
            json.dumps({
                "error": "No remote TTS provider configured and no local fallback available.",
                "help": "Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION to enable Azure speech, or install pyttsx3 or gTTS and set QAI_ENABLE_LOCAL_TTS=true in local.settings.json/.env to enable local fallback. See local.settings.json.example and .env.example in the repo for templates."
            }),
            status_code=501,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )

    except Exception as e:  # noqa: BLE001
        logging.exception(f"/tts error: {e}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())


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
        venv_info = {"path": str(
            venv_python), "exists": venv_python.exists(), "packages": {}, "error": None}

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
                proc = subprocess.run(
                    [str(venv_python), "-c", code], capture_output=True, text=True, timeout=12)
                if proc.returncode == 0:
                    data = json.loads(proc.stdout.strip() or "{}")
                    venv_info["packages"] = data
                else:
                    venv_info["error"] = proc.stderr.strip(
                    ) or f"exit {proc.returncode}"
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
        chat_web_html = (repo_root / "apps" / "chat" / "index.html").exists()
        chat_web_js = (repo_root / "apps" / "chat" / "chat.js").exists()

        # Cosmos status (lazy health)
        cosmos_status = None
        if cosmos_client:
            try:
                cosmos_status = cosmos_client.health()
            except Exception as cs_err:  # noqa: BLE001
                cosmos_status = {"enabled": False, "error": str(cs_err)}

        # Unified SQL status (may reflect Azure SQL, PostgreSQL, MySQL, SQLite)
        sql_info = None
        try:
            sql_info = sql_health()
            try:  # augment with pool metrics + saturation alerts
                pool_info = engine_stats()
                sql_info["pool"] = pool_info
                # Surface critical alerts at top level for visibility
                if pool_info.get("saturation_alert"):
                    sql_info["alert"] = pool_info["saturation_alert"]
                if pool_info.get("slow_queries_1min", 0) > 10:
                    freq_alert = f"{pool_info['slow_queries_1min']} slow queries in last 60s (threshold={pool_info.get('slow_query_threshold_ms')}ms)"
                    sql_info["slow_query_alert"] = freq_alert
                    logging.warning(f"[ai_status] {freq_alert}")
            except Exception as _ps:  # noqa: BLE001
                sql_info["pool"] = {"enabled": False, "error": str(_ps)}
        except Exception as _se:  # noqa: BLE001
            sql_info = {"enabled": False, "error": str(_se)}

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
                cfg_path = Path(__file__).resolve().parent / \
                    "quantum-ai" / "config" / "quantum_config.yaml"
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

        # Self-Learning System Status
        learning_info = {
            "enabled": False,
            "training_cycles": 0,
            "total_conversations": 0,
            "new_conversations": 0,
            "last_training": None,
            "best_model_path": None,
            "model_history": []
        }
        try:
            learning_status_file = Path(__file__).resolve(
            ).parent / "data_out" / "self_learning" / "status.json"
            if learning_status_file.exists():
                with open(learning_status_file, "r") as lf:
                    learning_status = json.load(lf)
                    learning_info["enabled"] = learning_status.get(
                        "learning_enabled", True)
                    learning_info["training_cycles"] = learning_status.get(
                        "training_cycles", 0)
                    learning_info["total_conversations"] = learning_status.get(
                        "total_conversations", 0)
                    learning_info["new_conversations"] = learning_status.get(
                        "conversations_since_last_train", 0)
                    learning_info["last_training"] = learning_status.get(
                        "last_training")
                    learning_info["best_model_path"] = learning_status.get(
                        "best_model_path")
                    learning_info["model_history"] = learning_status.get(
                        "model_history", [])[-3:]  # Last 3
        except Exception as _le:  # noqa: BLE001
            learning_info["error"] = str(_le)

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
            "sql": sql_info,
            "telemetry": telemetry_info,
            "quantum": quantum_info,
            "self_learning": learning_info,
            "temperature": float(os.getenv("CHAT_TEMPERATURE", "0.7")),
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
                "/api/vision/infer",
                "/api/vision/batch-infer",
                "/api/image/generate",
            ],
            "status": "ok",
        }

        return func.HttpResponse(
            json.dumps(payload),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers(),
        )

    except Exception as e:  # noqa: BLE001
        logging.error(f"ai/status error: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "error": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers(),
        )


# =============================================================================
# Vision AI Endpoints - Expression/emotion classification
# =============================================================================

@app.route(route="vision/infer", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def vision_infer(req: func.HttpRequest) -> func.HttpResponse:
    """
    Vision inference endpoint for expression/emotion classification.

    POST /api/vision/infer
    Body (option 1 - base64):
    {
        "image": "base64_encoded_image_string",
        "format": "base64"
    }

    Body (option 2 - URL):
    {
        "image_url": "https://example.com/image.jpg",
        "format": "url"
    }

    Response:
    {
        "label": "happy",
        "confidence": 0.92,
        "scores": {
            "happy": 0.92,
            "sad": 0.05,
            "neutral": 0.03
        },
        "model_info": {
            "checkpoint": "...",
            "classes": ["happy", "sad", "neutral"],
            "device": "cpu"
        }
    }
    """
    logging.info('Vision infer endpoint invoked')

    try:
        # Lazy import vision inference (only loaded when needed)
        try:
            from vision_inference import VisionInference
        except ImportError as e:
            return func.HttpResponse(
                json.dumps({"error": f"Vision inference not available: {e}"}),
                status_code=500,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )

        # Parse request
        req_body = req.get_json()
        image_data = req_body.get('image')
        image_url = req_body.get('image_url')
        format_type = req_body.get('format', 'base64')

        if not image_data and not image_url:
            return func.HttpResponse(
                json.dumps(
                    {"error": "No image provided. Include 'image' (base64) or 'image_url' in request body."}),
                status_code=400,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )

        # Initialize vision inference (loads latest checkpoint)
        # Cache the instance for performance (singleton pattern)
        if not hasattr(vision_infer, '_vision_model'):
            logging.info('Initializing vision model (first request)...')
            try:
                vision_infer._vision_model = VisionInference()
            except FileNotFoundError as e:
                return func.HttpResponse(
                    json.dumps({
                        "error": "No trained model found",
                        "detail": str(e),
                        "help": "Train a model first using: python scripts/train_vision.py"
                    }),
                    status_code=404,
                    mimetype="application/json",
                    headers=create_cors_response_headers()
                )

        vi = vision_infer._vision_model

        # Run inference based on input format
        if image_url:
            # Fetch image from URL
            try:
                import requests
                from PIL import Image
                import io
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
                result = vi.predict(img)
            except Exception as e:
                return func.HttpResponse(
                    json.dumps(
                        {"error": f"Failed to fetch image from URL: {e}"}),
                    status_code=400,
                    mimetype="application/json",
                    headers=create_cors_response_headers()
                )
        elif format_type == 'base64':
            # Decode base64 image
            try:
                result = vi.predict_base64(image_data)
            except Exception as e:
                return func.HttpResponse(
                    json.dumps(
                        {"error": f"Failed to decode base64 image: {e}"}),
                    status_code=400,
                    mimetype="application/json",
                    headers=create_cors_response_headers()
                )
        else:
            return func.HttpResponse(
                json.dumps(
                    {"error": f"Unsupported format: {format_type}. Use 'base64' or provide 'image_url'."}),
                status_code=400,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )

        # Add model metadata to response
        response_data = {
            **result,
            "model_info": vi.get_model_info()
        }

        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )

    except Exception as e:
        logging.error(f'Vision infer error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Vision inference failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="vision/infer", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def vision_infer_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight for vision inference"""
    return func.HttpResponse(
        "",
        status_code=200,
        headers=create_cors_response_headers()
    )


@app.route(route="vision/batch-infer", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def vision_batch_infer(req: func.HttpRequest) -> func.HttpResponse:
    """
    Batch vision inference endpoint for multiple images.

    POST /api/vision/batch-infer
    Body:
    {
        "images": [
            {"data": "base64_1", "id": "img1"},
            {"data": "base64_2", "id": "img2"},
            ...
        ]
    }

    Response:
    {
        "results": [
            {"id": "img1", "label": "happy", "confidence": 0.92, ...},
            {"id": "img2", "label": "sad", "confidence": 0.85, ...}
        ],
        "total": 2,
        "model_info": {...}
    }
    """
    logging.info('Vision batch infer endpoint invoked')

    try:
        from vision_inference import VisionInference
        from PIL import Image
        import io
        import base64
    except ImportError as e:
        return func.HttpResponse(
            json.dumps({"error": f"Vision inference not available: {e}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )

    try:
        req_body = req.get_json()
        images_data = req_body.get('images', [])

        if not images_data:
            return func.HttpResponse(
                json.dumps({"error": "No images provided"}),
                status_code=400,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )

        # Limit batch size to prevent overload
        max_batch_size = 50
        if len(images_data) > max_batch_size:
            return func.HttpResponse(
                json.dumps(
                    {"error": f"Batch size exceeds limit of {max_batch_size} images"}),
                status_code=400,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )

        # Initialize vision model
        if not hasattr(vision_batch_infer, '_vision_model'):
            try:
                vision_batch_infer._vision_model = VisionInference()
            except FileNotFoundError as e:
                return func.HttpResponse(
                    json.dumps(
                        {"error": "No trained model found", "detail": str(e)}),
                    status_code=404,
                    mimetype="application/json",
                    headers=create_cors_response_headers()
                )

        vi = vision_batch_infer._vision_model

        # Decode all images
        pil_images = []
        image_ids = []
        for idx, img_data in enumerate(images_data):
            try:
                img_id = img_data.get('id', f'image_{idx}')
                b64_data = img_data.get('data')

                img_bytes = base64.b64decode(b64_data)
                pil_img = Image.open(io.BytesIO(img_bytes))

                pil_images.append(pil_img)
                image_ids.append(img_id)
            except Exception as e:
                logging.warning(f'Failed to decode image {idx}: {e}')
                continue

        if not pil_images:
            return func.HttpResponse(
                json.dumps({"error": "No valid images could be decoded"}),
                status_code=400,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )

        # Run batch inference
        predictions = vi.predict_batch(pil_images)

        # Combine predictions with IDs
        results = []
        for img_id, pred in zip(image_ids, predictions):
            results.append({
                'id': img_id,
                **pred
            })

        response_data = {
            'results': results,
            'total': len(results),
            'model_info': vi.get_model_info()
        }

        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )

    except Exception as e:
        logging.error(f'Vision batch infer error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Batch inference failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="image/generate", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def image_generate(req: func.HttpRequest) -> func.HttpResponse:
    """
    AI Image generation endpoint using OpenAI DALL-E.

    POST /api/image/generate
    Body:
    {
        "prompt": "description of image to generate",
        "size": "512x512",
        "style": "anime"
    }

    Response:
    {
        "image_url": "https://...",
        "image_data": "base64_encoded_image",
        "prompt": "original prompt",
        "model": "dall-e-2"
    }
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=200, headers=create_cors_response_headers())

    logging.info('Image generation endpoint invoked')

    try:
        req_body = req.get_json()
        prompt = req_body.get('prompt', '')
        size = req_body.get('size', '512x512')
        style_hint = req_body.get('style', '')

        if not prompt:
            return func.HttpResponse(
                json.dumps({"error": "Prompt is required"}),
                status_code=400,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )

        if style_hint:
            prompt = f"{prompt}, {style_hint} style"

        try:
            from openai import OpenAI
            import os

            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                api_key = os.getenv('AZURE_OPENAI_API_KEY')
                endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')

                if api_key and endpoint:
                    client = OpenAI(
                        api_key=api_key, base_url=f"{endpoint}/openai/deployments")
                else:
                    raise ValueError("No OpenAI API key configured")
            else:
                client = OpenAI(api_key=api_key)

            response = client.images.generate(model="dall-e-2", prompt=prompt, size=size if size in [
                                              "256x256", "512x512", "1024x1024"] else "512x512", n=1, response_format="url")

            image_url = response.data[0].url

            response_data = {'image_url': image_url,
                             'prompt': prompt, 'model': 'dall-e-2', 'size': size}

            return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json", headers=create_cors_response_headers())

        except Exception as openai_error:
            logging.warning(
                f'OpenAI image generation failed: {openai_error}')
            # Detect Azure/OpenAI quota/premium allowance errors and provide
            # a clearer fallback message for users.
            try:
                from shared.azure_utils import is_quota_error, format_quota_message
            except Exception:
                is_quota_error = None
                format_quota_message = None

            placeholder_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
                <defs>
                    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                        <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#f093fb;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <rect width="512" height="512" fill="url(#grad)"/>
                <text x="256" y="220" font-size="120" text-anchor="middle" fill="white">✨</text>
                <text x="256" y="300" font-size="32" text-anchor="middle" fill="white" font-weight="bold">Aria</text>
                <text x="256" y="340" font-size="20" text-anchor="middle" fill="rgba(255,255,255,0.9)">AI Assistant</text>
                <text x="256" y="380" font-size="16" text-anchor="middle" fill="rgba(255,255,255,0.7)">Image generation unavailable</text>
                <text x="256" y="410" font-size="14" text-anchor="middle" fill="rgba(255,255,255,0.6)">{openai_error.__class__.__name__}</text>
            </svg>'''

            import base64
            svg_base64 = base64.b64encode(
                placeholder_svg.encode()).decode()

            # Prefer a helpful quota message when available
            err_text = str(openai_error)
            if is_quota_error is not None and is_quota_error(openai_error):
                if format_quota_message is not None:
                    err_text = format_quota_message(
                        openai_error, service_name="OpenAI / Azure Images API")

            response_data = {'image_data': svg_base64, 'prompt': prompt,
                             'model': 'fallback-svg', 'size': '512x512', 'fallback': True, 'error': err_text}

            return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json", headers=create_cors_response_headers())

    except Exception as e:
        logging.error(f'Image generation error: {str(e)}')
        return func.HttpResponse(json.dumps({"error": f"Image generation failed: {str(e)}"}), status_code=500, mimetype="application/json", headers=create_cors_response_headers())


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
                json.dumps(
                    {"error": f"Quantum dependencies not available: {e}"}),
                status_code=500,
                mimetype="application/json",
                headers=create_cors_response_headers()
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
                headers=create_cors_response_headers()
            )

        # Initialize quantum classifier
        classifier = QuantumClassifier()

        # Prepare features
        feature_array = np.array(features[:n_qubits])
        if len(feature_array) < n_qubits:
            feature_array = np.pad(
                feature_array, (0, n_qubits - len(feature_array)))

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
            headers=create_cors_response_headers()
        )

    except Exception as e:
        logging.error(f'Quantum classify error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Quantum classification failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
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

        # Create text visualization using list for efficiency (avoids O(n²) string concatenation)
        viz_parts = [
            f"Quantum Circuit ({n_qubits} qubits, {n_layers} layers, {entanglement} entanglement)\n",
            "=" * 60 + "\n\n"
        ]

        for layer in range(n_layers + 2):
            viz_parts.append(f"Layer {layer}:\n")
            layer_gates = [g for g in gates if g.get('layer') == layer]
            for gate in layer_gates:
                if gate['type'] in ['RY', 'RZ']:
                    viz_parts.append(f"  {gate['type']}({gate['parameter']}) on qubit {gate['qubit']}\n")
                elif gate['type'] == 'CNOT':
                    viz_parts.append(f"  CNOT: control={gate['control']}, target={gate['target']}\n")
                elif gate['type'] == 'Measure':
                    viz_parts.append(f"  Measure qubit {gate['qubit']} ({gate['observable']})\n")
            viz_parts.append("\n")
        
        visualization = "".join(viz_parts)

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
            headers=create_cors_response_headers()
        )

    except Exception as e:
        logging.error(f'Quantum circuit error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Circuit creation failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
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
                {"name": "default.qubit",
                    "description": "PennyLane default simulator", "type": "simulator"},
                {"name": "lightning.qubit",
                    "description": "Fast C++ simulator", "type": "simulator"},
                {"name": "qiskit.aer", "description": "Qiskit Aer simulator",
                    "type": "simulator"}
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
            headers=create_cors_response_headers()
        )

    except Exception as e:
        logging.error(f'Quantum info error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get quantum info: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


# =============================================================================
# SUBSCRIPTION & MONETIZATION ENDPOINTS
# =============================================================================

@app.route(route="subscription/pricing", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def subscription_pricing(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get pricing information for all subscription tiers.
    
    GET /api/subscription/pricing
    
    Response: {
        "tiers": {
            "free": {...},
            "pro": {...},
            "enterprise": {...}
        }
    }
    """
    logging.info('Pricing endpoint invoked')
    
    try:
        from shared.subscription_manager import TIER_PRICING, TIER_FEATURES, TIER_LIMITS, SubscriptionTier
        
        pricing_info = {
            "tiers": {}
        }
        
        for tier in SubscriptionTier:
            pricing_info["tiers"][tier.value] = {
                "name": tier.name,
                "price": TIER_PRICING[tier],
                "currency": "USD",
                "billing_period": "monthly",
                "features": {f.value: enabled for f, enabled in TIER_FEATURES[tier].items()},
                "limits": TIER_LIMITS[tier]
            }
        
        return func.HttpResponse(
            json.dumps(pricing_info),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Pricing endpoint error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get pricing: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="subscription/status", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def subscription_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get subscription status for a user.
    
    GET /api/subscription/status?user_id=<user_id>
    
    Response: {
        "user_id": "...",
        "tier": "pro",
        "is_active": true,
        "usage": {...},
        "limits": {...}
    }
    """
    logging.info('Subscription status endpoint invoked')
    
    try:
        if not subscription_manager_available:
            return func.HttpResponse(
                json.dumps({"error": "Subscription manager not available"}),
                status_code=503,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )
        
        user_id = req.params.get('user_id', 'demo_user')
        
        manager = get_subscription_manager()
        subscription = manager.get_subscription(user_id)
        
        return func.HttpResponse(
            json.dumps(subscription.to_dict()),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Subscription status error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get subscription status: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="subscription/upgrade", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def subscription_upgrade(req: func.HttpRequest) -> func.HttpResponse:
    """
    Upgrade a user's subscription.
    
    POST /api/subscription/upgrade
    Body: {
        "user_id": "...",
        "tier": "pro" | "enterprise",
        "duration_days": 30,
        "payment_method": "stripe",
        "stripe_subscription_id": "..."
    }
    
    Response: {
        "success": true,
        "subscription": {...}
    }
    """
    logging.info('Subscription upgrade endpoint invoked')
    
    try:
        if not subscription_manager_available:
            return func.HttpResponse(
                json.dumps({"error": "Subscription manager not available"}),
                status_code=503,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )
        
        body = json.loads(req.get_body().decode('utf-8'))
        user_id = body.get('user_id', 'demo_user')
        tier_str = body.get('tier', 'pro')
        duration_days = body.get('duration_days', 30)
        payment_method = body.get('payment_method')
        stripe_subscription_id = body.get('stripe_subscription_id')
        
        tier = SubscriptionTier(tier_str)
        
        manager = get_subscription_manager()
        subscription = manager.upgrade_subscription(
            user_id=user_id,
            tier=tier,
            duration_days=duration_days,
            payment_method=payment_method,
            stripe_subscription_id=stripe_subscription_id
        )
        
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "subscription": subscription.to_dict()
            }),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Subscription upgrade error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to upgrade subscription: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="subscription/revenue", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def subscription_revenue(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get revenue statistics and projections.
    
    GET /api/subscription/revenue
    
    Response: {
        "total_subscribers": 15,
        "active_subscribers": 15,
        "by_tier": {...},
        "monthly_recurring_revenue": 2235,
        "annual_recurring_revenue": 26820
    }
    """
    logging.info('Revenue stats endpoint invoked')
    
    try:
        if not subscription_manager_available:
            return func.HttpResponse(
                json.dumps({"error": "Subscription manager not available"}),
                status_code=503,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )
        
        manager = get_subscription_manager()
        stats = manager.get_revenue_stats()
        
        return func.HttpResponse(
            json.dumps(stats),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Revenue stats error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get revenue stats: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="subscription/usage", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def subscription_track_usage(req: func.HttpRequest) -> func.HttpResponse:
    """
    Track resource usage for a user.
    
    POST /api/subscription/usage
    Body: {
        "user_id": "...",
        "resource": "chat_messages" | "quantum_jobs" | "training_hours" | "api_requests" | "websites_created",
        "amount": 1
    }
    
    Response: {
        "success": true,
        "allowed": true,
        "current_usage": {...}
    }
    """
    logging.info('Usage tracking endpoint invoked')
    
    try:
        if not subscription_manager_available:
            return func.HttpResponse(
                json.dumps({"error": "Subscription manager not available"}),
                status_code=503,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )
        
        body = json.loads(req.get_body().decode('utf-8'))
        user_id = body.get('user_id', 'demo_user')
        resource = body.get('resource', 'api_requests')
        amount = body.get('amount', 1)
        
        manager = get_subscription_manager()
        allowed = manager.track_usage(user_id, resource, amount)
        
        subscription = manager.get_subscription(user_id)
        
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "allowed": allowed,
                "current_usage": subscription.usage,
                "limits": subscription.to_dict()["limits"]
            }),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Usage tracking error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to track usage: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


# -----------------------------------------------------------------------------
# Stripe Webhook Handler
# -----------------------------------------------------------------------------
@app.route(route="webhook/stripe", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def stripe_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle Stripe webhook events.
    
    POST /api/webhook/stripe
    Headers: Stripe-Signature
    Body: Stripe event payload
    
    Response: {
        "status": "success" | "error",
        "message": "..."
    }
    """
    logging.info('Stripe webhook endpoint invoked')
    
    try:
        from shared.stripe_webhooks import get_webhook_handler
        
        payload = req.get_body().decode('utf-8')
        signature = req.headers.get('Stripe-Signature', '')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        handler = get_webhook_handler()
        result = handler.handle_webhook(payload, signature, webhook_secret)
        
        status_code = 200 if result["status"] in ["success", "ignored"] else 500
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=status_code,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Stripe webhook error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


# -----------------------------------------------------------------------------
# Email Notifications Test Endpoint
# -----------------------------------------------------------------------------
@app.route(route="notifications/test", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def test_notifications(req: func.HttpRequest) -> func.HttpResponse:
    """
    Test email notification system.
    
    POST /api/notifications/test
    Body: {
        "email": "user@example.com",
        "type": "usage_warning" | "payment_succeeded" | "subscription_activated"
    }
    
    Response: {
        "success": true,
        "message": "Notification sent"
    }
    """
    logging.info('Test notification endpoint invoked')
    
    try:
        from shared.email_notifications import get_email_system
        
        body = json.loads(req.get_body().decode('utf-8'))
        email = body.get('email', 'test@example.com')
        notification_type = body.get('type', 'usage_warning')
        
        email_system = get_email_system()
        
        # Send test notification based on type
        if notification_type == 'usage_warning':
            success = email_system.notify_usage_warning(
                user_email=email,
                resource='chat_messages',
                percentage=85.0,
                current=850,
                limit=1000
            )
        elif notification_type == 'payment_succeeded':
            success = email_system.notify_payment_succeeded(
                user_email=email,
                amount=49.00,
                invoice_id='inv_test123'
            )
        elif notification_type == 'subscription_activated':
            success = email_system.notify_subscription_activated(
                user_email=email,
                tier='Pro',
                price=49.00
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unknown notification type: {notification_type}"}),
                status_code=400,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )
        
        return func.HttpResponse(
            json.dumps({
                "success": success,
                "message": f"Test notification sent to {email}",
                "type": notification_type
            }),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Test notification error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to send test notification: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


# -----------------------------------------------------------------------------
# Notifications Log Endpoint
# -----------------------------------------------------------------------------
@app.route(route="notifications/log", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def notifications_log(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get email notification log.
    
    GET /api/notifications/log?user_email=user@example.com
    
    Response: {
        "notifications": [...]
    }
    """
    logging.info('Notifications log endpoint invoked')
    
    try:
        from shared.email_notifications import get_email_system
        
        user_email = req.params.get('user_email')
        
        email_system = get_email_system()
        notifications = email_system.get_sent_emails(user_email)
        
        return func.HttpResponse(
            json.dumps({
                "notifications": notifications,
                "count": len(notifications)
            }),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Notifications log error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get notifications log: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


# -----------------------------------------------------------------------------
# Referral System Endpoints
# -----------------------------------------------------------------------------
@app.route(route="referrals/code", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def referral_code(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get or generate referral code for a user.
    
    GET /api/referrals/code?user_id=...
    POST /api/referrals/code with {"user_id": "..."}
    
    Response: {
        "referral_code": "ABC123DEF",
        "user_id": "..."
    }
    """
    logging.info('Referral code endpoint invoked')
    
    try:
        from shared.referral_system import get_referral_system
        
        if req.method == "GET":
            user_id = req.params.get('user_id', 'demo_user')
        else:
            body = json.loads(req.get_body().decode('utf-8'))
            user_id = body.get('user_id', 'demo_user')
        
        referral_system = get_referral_system()
        
        # Get existing or generate new code
        code = referral_system.get_referral_code(user_id)
        if not code:
            code = referral_system.generate_referral_code(user_id)
        
        return func.HttpResponse(
            json.dumps({
                "referral_code": code,
                "user_id": user_id
            }),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Referral code error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get referral code: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="referrals/stats", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def referral_stats(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get referral statistics for a user.
    
    GET /api/referrals/stats?user_id=...
    
    Response: {
        "referral_code": "...",
        "referral_count": 5,
        "total_commission": 100.00,
        "pending_commission": 50.00,
        "paid_commission": 50.00,
        "referrals": [...]
    }
    """
    logging.info('Referral stats endpoint invoked')
    
    try:
        from shared.referral_system import get_referral_system
        
        user_id = req.params.get('user_id', 'demo_user')
        
        referral_system = get_referral_system()
        stats = referral_system.get_referral_stats(user_id)
        
        return func.HttpResponse(
            json.dumps(stats),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Referral stats error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get referral stats: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="referrals/record", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def record_referral(req: func.HttpRequest) -> func.HttpResponse:
    """
    Record a new referral.
    
    POST /api/referrals/record
    Body: {
        "referrer_code": "ABC123",
        "new_user_id": "user123",
        "tier": "pro",
        "subscription_value": 49.00
    }
    
    Response: {
        "success": true,
        "commission": 9.80,
        "referral_count": 5
    }
    """
    logging.info('Record referral endpoint invoked')
    
    try:
        from shared.referral_system import get_referral_system
        
        body = json.loads(req.get_body().decode('utf-8'))
        referrer_code = body.get('referrer_code')
        new_user_id = body.get('new_user_id')
        tier = body.get('tier')
        subscription_value = body.get('subscription_value')
        
        if not all([referrer_code, new_user_id, tier, subscription_value]):
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields"}),
                status_code=400,
                mimetype="application/json",
                headers=create_cors_response_headers()
            )
        
        referral_system = get_referral_system()
        result = referral_system.record_referral(
            referrer_code=referrer_code,
            new_user_id=new_user_id,
            tier=tier,
            subscription_value=subscription_value
        )
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200 if result.get('success') else 400,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Record referral error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to record referral: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )


@app.route(route="referrals/leaderboard", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def referral_leaderboard(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get referral leaderboard.
    
    GET /api/referrals/leaderboard?limit=10
    
    Response: {
        "leaderboard": [
            {"rank": 1, "user_id": "...", "referral_count": 50, "total_commission": 500}
        ]
    }
    """
    logging.info('Referral leaderboard endpoint invoked')
    
    try:
        from shared.referral_system import get_referral_system
        
        limit = int(req.params.get('limit', '10'))
        
        referral_system = get_referral_system()
        leaderboard = referral_system.get_leaderboard(limit)
        
        return func.HttpResponse(
            json.dumps({"leaderboard": leaderboard}),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )
    
    except Exception as e:
        logging.error(f'Referral leaderboard error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get leaderboard: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=create_cors_response_headers()
        )

