import json
import os
import sys
from pathlib import Path

import azure.functions as func

# Add shared folder to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from chat_providers import detect_provider  # noqa: E402


def _parse_body(req: func.HttpRequest) -> dict:
    try:
        return req.get_json() or {}
    except ValueError:
        return {}


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Return provider selection diagnostics for a requested provider/model.

    Query/body params:
      provider: explicit provider choice ('auto', 'local', 'openai', 'azure', 'lmstudio', 'ollama', 'agi')
      model:    optional model/deployment override
    """
    params = {k.lower(): v for k, v in req.params.items()}
    body = _parse_body(req)

    provider_choice = params.get("provider") or body.get("provider") or os.getenv("DEFAULT_AI_PROVIDER", "auto")
    model = params.get("model") or body.get("model")

    try:
        provider, info = detect_provider(explicit=provider_choice, model_override=model)
        payload = {
            "requested_provider": provider_choice,
            "requested_model": model,
            "resolved_provider": info.name,
            "resolved_model": info.model,
            "provider_class": provider.__class__.__name__,
        }
        return func.HttpResponse(
            json.dumps(payload, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as exc:  # noqa: BLE001
        return func.HttpResponse(
            json.dumps(
                {
                    "requested_provider": provider_choice,
                    "requested_model": model,
                    "error": str(exc),
                },
                ensure_ascii=False,
            ),
            status_code=500,
            mimetype="application/json",
        )
