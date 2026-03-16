import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

import azure.functions as func

# Add shared folder to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from chat_providers import detect_provider  # noqa: E402


def _parse_body(req: func.HttpRequest) -> Dict[str, Any]:
    try:
        return req.get_json() or {}
    except ValueError:
        return {}


def main(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP trigger to run AI one-shot.

    Query/body params:
      prompt:   User prompt (required).
      provider: Provider ('local', 'openai', 'azure', 'auto').
      model:    Model/deployment override.
    """
    params = {k.lower(): v for k, v in req.params.items()}
    body = _parse_body(req)

    prompt = params.get("prompt") or body.get("prompt")
    provider_choice = params.get("provider") or body.get("provider") or os.getenv("DEFAULT_AI_PROVIDER", "local")
    model = params.get("model") or body.get("model")

    if not prompt:
        return func.HttpResponse(
            json.dumps({"error": "Missing 'prompt'"}), status_code=400, mimetype="application/json"
        )

    try:
        provider, info = detect_provider(explicit=provider_choice, model_override=model)
        messages = [{"role": "user", "content": prompt}]
        reply = provider.complete(messages, stream=False)
        payload = {
            "prompt": prompt,
            "reply": reply,
            "provider": info.name,
            "model": info.model,
        }
        return func.HttpResponse(json.dumps(payload, ensure_ascii=False), status_code=200, mimetype="application/json")
    except Exception as e:  # noqa: BLE001
        logging.exception("AI HTTP run failed")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")
