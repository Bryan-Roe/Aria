#!/usr/bin/env python3
"""Launch chat CLI with LM Studio auto-detection.

Falls back to the local provider when LM Studio is unavailable.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _normalize_base_url(raw: str) -> str:
    base = raw.strip().rstrip("/")
    if base.endswith("/v1"):
        return base
    if base.endswith("/v1/"):
        return base[:-1]
    return f"{base}/v1"


def _lmstudio_online(base_url: str, timeout: float = 2.0) -> bool:
    models_url = f"{_normalize_base_url(base_url)}/models"
    req = urllib.request.Request(
        models_url,
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return 200 <= getattr(response, "status", 0) < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _lmstudio_models(base_url: str, timeout: float = 2.0) -> list[str]:
    models_url = f"{_normalize_base_url(base_url)}/models"
    req = urllib.request.Request(
        models_url,
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if not (200 <= getattr(response, "status", 0) < 300):
                return []
            payload = json.loads(response.read().decode("utf-8"))
            data = payload.get("data", []) if isinstance(payload, dict) else []
            models = [m.get("id") for m in data if isinstance(m, dict)]
            return [m for m in models if isinstance(m, str) and m.strip()]
    except (
        json.JSONDecodeError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ):
        return []


def _build_chat_cli_path() -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "tools" / "talk-to-ai" / "src" / "chat_cli.py"


def _repo_python() -> str:
    repo_root = Path(__file__).resolve().parent.parent
    venv_python = repo_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Launch talk-to-ai chat CLI with LM Studio fallback "
            "to local provider"
        )
    )
    parser.add_argument(
        "--provider",
        choices=[
            "auto",
            "lmstudio",
            "local",
            "openai",
            "azure",
            "agi",
            "quantum",
            "lora",
        ],
        default="auto",
        help=(
            "Provider to use; default auto picks lmstudio when "
            "online, otherwise local."
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Optional model name; if omitted for lmstudio, "
            "LMSTUDIO_MODEL/default is used."
        ),
    )
    parser.add_argument(
        "--once",
        default=None,
        help="Send one prompt and exit (forwarded to chat_cli.py).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve provider and print command without launching chat.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="LM Studio probe timeout in seconds (default: 2.0).",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Exit if lmstudio is requested but unavailable.",
    )
    args = parser.parse_args()

    chat_cli_path = _build_chat_cli_path()
    if not chat_cli_path.exists():
        print(f"[chat-launcher] Could not find chat CLI at: {chat_cli_path}")
        return 1

    provider = args.provider
    lmstudio_base_url = os.getenv(
        "LMSTUDIO_BASE_URL",
        "http://127.0.0.1:1234/v1",
    )
    endpoint = _normalize_base_url(lmstudio_base_url)
    lmstudio_models = _lmstudio_models(endpoint, timeout=args.timeout)
    lmstudio_online = bool(lmstudio_models) or _lmstudio_online(
        endpoint,
        timeout=args.timeout,
    )

    if provider == "auto":
        provider = "lmstudio" if lmstudio_models else "local"
        if provider == "local":
            reason = (
                "LM Studio reachable but no models loaded"
                if lmstudio_online
                else "LM Studio unavailable"
            )
            print(f"[chat-launcher] Auto fallback to local: {reason}")
    elif provider == "lmstudio" and not lmstudio_online:
        if args.no_fallback:
            print(
                "[chat-launcher] LM Studio unavailable "
                "and fallback disabled."
            )
            return 3
        print("[chat-launcher] LM Studio unavailable; falling back to local.")
        provider = "local"

    cmd = [_repo_python(), str(chat_cli_path), "--provider", provider]

    resolved_model = args.model or os.getenv("LMSTUDIO_MODEL")
    if provider == "lmstudio" and not resolved_model and lmstudio_models:
        resolved_model = lmstudio_models[0]

    if provider == "lmstudio" and resolved_model:
        cmd.extend(["--model", resolved_model])

    if args.once:
        cmd.extend(["--once", args.once])

    print(f"[chat-launcher] Provider: {provider}")
    if provider == "lmstudio":
        print(f"[chat-launcher] Endpoint: {endpoint}")
        if resolved_model:
            print(f"[chat-launcher] Model: {resolved_model}")
    print(f"[chat-launcher] Python: {cmd[0]}")
    print("[chat-launcher] Interactive commands: /new, /save, /exit")

    if args.dry_run:
        print(f"[chat-launcher] Dry-run command: {shlex.join(cmd)}")
        return 0

    completed = subprocess.run(cmd, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
