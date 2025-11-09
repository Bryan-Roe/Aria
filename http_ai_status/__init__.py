import json
import os
import sys
from pathlib import Path
import azure.functions as func

# Reuse shared chat providers (already copied for performance)
shared_path = Path(__file__).resolve().parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from chat_providers import detect_provider  # noqa: E402


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Health / status endpoint for AI provider readiness.

    Returns JSON describing:
      - active_provider: which provider auto-detect selects (azure|openai|local)
      - model: resolved model/deployment name
      - env: boolean flags indicating if required env vars are present for each cloud provider
      - temperature: current CHAT_TEMPERATURE setting

    This helps verify cloud configuration after deploying to Azure.
    """
    # Collect environment info
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

    try:
        provider, info = detect_provider(explicit="auto")
        temperature = os.getenv("CHAT_TEMPERATURE", "0.7")
        payload = {
            "active_provider": info.name,
            "model": info.model,
            "env": {
                "azure_openai": azure_env,
                "openai": openai_env,
                "local_fallback": True,
            },
            "temperature": temperature,
            "status": "ok",
        }
        return func.HttpResponse(json.dumps(payload), status_code=200, mimetype="application/json")
    except Exception as e:  # noqa: BLE001
        payload = {
            "status": "error",
            "error": str(e),
            "env": {
                "azure_openai": azure_env,
                "openai": openai_env,
            },
        }
        return func.HttpResponse(json.dumps(payload), status_code=500, mimetype="application/json")
