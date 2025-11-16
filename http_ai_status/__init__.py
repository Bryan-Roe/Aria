import json
import os
import sys
import subprocess
from pathlib import Path
import importlib.util as _iu
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

    # In-process ML deps availability
    inproc_ml = {
        "torch": _iu.find_spec("torch") is not None,
        "transformers": _iu.find_spec("transformers") is not None,
        "peft": _iu.find_spec("peft") is not None,
    }

    # Repo root and venv python
    repo_root = Path(__file__).resolve().parents[1]
    venv_python = repo_root / "venv" / "Scripts" / "python.exe"
    venv_info = {
        "path": str(venv_python),
        "exists": venv_python.exists(),
        "packages": {},
        "error": None,
    }
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
            proc = subprocess.run([str(venv_python), "-c", code], capture_output=True, text=True, timeout=10)
            if proc.returncode == 0:
                data = json.loads(proc.stdout.strip() or "{}")
                venv_info["packages"] = data
            else:
                venv_info["error"] = proc.stderr.strip() or f"exit {proc.returncode}"
        except Exception as e:  # noqa: BLE001
            venv_info["error"] = str(e)

    # LoRA default adapter location and readiness
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
        "subprocess_ready": venv_info["exists"] and bool(venv_info.get("packages",{}).get("available",{}).get("torch"))
            and bool(venv_info.get("packages",{}).get("available",{}).get("transformers"))
            and bool(venv_info.get("packages",{}).get("available",{}).get("peft")),
    }
    if lora_info["adapter_config_exists"]:
        try:
            with open(adapter_cfg, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            lora_info["base_model"] = cfg.get("base_model_name_or_path")
        except Exception:
            pass

    try:
        provider, info = detect_provider(explicit="auto")
        temperature = os.getenv("CHAT_TEMPERATURE", "0.7")
        # Known endpoints and assets
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
            "temperature": temperature,
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
                "/api/ai/status",
            ],
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
