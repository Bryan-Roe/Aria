#!/usr/bin/env python3
"""Configure and validate local LLM (Ollama or LM Studio) for Aria development.

Usage:
    uv run python scripts/setup_local_llm.py --dry-run
    uv run python scripts/setup_local_llm.py
    uv run python scripts/setup_local_llm.py --provider ollama --pull-model qwen2.5-coder:7b
    uv run python scripts/setup_local_llm.py --write   # persist discovered model to local.settings.json

(Python is not required on PATH when using ``uv run`` from the repo root.)

Requires one of:
    - Ollama: https://ollama.ai — install, then ``ollama serve`` (often auto-starts)
    - LM Studio: https://lmstudio.ai — load a model and enable the local server
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_SETTINGS = REPO_ROOT / "local.settings.json"
LOCAL_SETTINGS_EXAMPLE = REPO_ROOT / "local.settings.json.example"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.local_settings import apply_local_settings, load_local_settings  # noqa: E402


def _ensure_utf8_stdio() -> None:
    """Windows consoles often use cp1252; probe helpers print emoji."""
    if sys.platform != "win32" or not hasattr(sys.stdout, "buffer"):
        return
    import io

    for stream in (sys.stdout, sys.stderr):
        enc = getattr(stream, "encoding", None) or ""
        if enc.lower().replace("-", "") == "utf8":
            continue
        wrapper = io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
        if stream is sys.stdout:
            sys.stdout = wrapper
        else:
            sys.stderr = wrapper


def _load_generate_ai_tokens():
    module_path = REPO_ROOT / "scripts" / "generate_ai_tokens.py"
    module_name = "_generate_ai_tokens"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _ensure_local_settings() -> None:
    if LOCAL_SETTINGS.exists():
        return
    if not LOCAL_SETTINGS_EXAMPLE.exists():
        print("ERROR: local.settings.json missing and no example template found.", file=sys.stderr)
        sys.exit(2)
    LOCAL_SETTINGS.write_text(LOCAL_SETTINGS_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Created {LOCAL_SETTINGS.name} from example template.")


def _write_settings_patch(patch: dict[str, str]) -> None:
    data = json.loads(LOCAL_SETTINGS.read_text(encoding="utf-8"))
    values = data.setdefault("Values", {})
    values.update(patch)
    LOCAL_SETTINGS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {LOCAL_SETTINGS.name}: {', '.join(patch)}")


def _start_ollama_if_needed() -> bool:
    import urllib.error
    import urllib.request

    probe_url = "http://127.0.0.1:11434/api/tags"
    try:
        urllib.request.urlopen(probe_url, timeout=2)  # noqa: S310
        return True
    except Exception:
        pass

    if not shutil.which("ollama"):
        return False

    print("Starting Ollama server in background...")
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    import time

    for _ in range(20):
        try:
            urllib.request.urlopen(probe_url, timeout=2)  # noqa: S310
            print("Ollama server is running.")
            return True
        except Exception:
            time.sleep(1)
    return False


def _print_dry_run_status(
    gat: object,
    *,
    providers: list[str],
    settings: dict,
    env: dict[str, str],
    pull_model: str,
) -> int:
    """Probe local runtimes without writes, pulls, or server startup."""
    print("\nDry run — probing local LLM (no file writes, no model pulls)\n")

    effective_pull = ""  # never pull during dry-run
    results = gat.run(
        providers=providers,
        settings=settings,
        rotate=False,
        write=False,
        interactive=False,
        use_az_cli=False,
        pull_model=effective_pull,
    )

    gat._render_summary(results)

    print("\nEffective env (local.settings.json + os.environ):")
    keys = [
        "DEFAULT_AI_PROVIDER",
        "ARIA_LLM_PROVIDER",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "LMSTUDIO_BASE_URL",
        "LMSTUDIO_MODEL",
        "LM_API_TOKEN",
    ]
    for key in keys:
        val = env.get(key, "")
        if val:
            display = val if key != "LM_API_TOKEN" else f"{val[:12]}…"
            print(f"  {key}={display}")

    if pull_model:
        print(f"\nWith --pull-model {pull_model!r}, a full run would attempt to pull if missing.")
    else:
        print("\nNo --pull-model set; a full run would not pull Ollama models.")

    healthy = [r for r in results if r.status == "ok"]
    if not healthy:
        print("\nNo local LLM runtime is reachable.")
        print("Install options (non-interactive where possible):")
        print("  winget install Ollama.Ollama          # Ollama (recommended)")
        print("  choco install ollama                  # Ollama via Chocolatey")
        print("  https://ollama.ai/download            # manual Ollama install")
        print("  https://lmstudio.ai                   # LM Studio (GUI, load model + start server)")
        print("\nAfter install:")
        print("  ollama serve          # if not auto-started")
        print("  ollama pull qwen2.5-coder:7b")
        return 1

    winner = healthy[0]
    print(f"\nWould use: provider={winner.name}, model={winner.model or env.get('OLLAMA_MODEL', '?')}")
    print("Re-run without --dry-run to validate completions; add --write to persist settings.")
    return 0


def main() -> int:
    _ensure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Configure and validate local LLM for Aria.",
        epilog="Tip: use `uv run python scripts/setup_local_llm.py` when python is not on PATH.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--provider",
        choices=("auto", "ollama", "lmstudio"),
        default="auto",
        help="Preferred local runtime (default: auto-detect)",
    )
    parser.add_argument(
        "--pull-model",
        default="",
        help="Ollama model to pull if missing (e.g. llama3.2, qwen2.5-coder:7b)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write discovered provider/model back to local.settings.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Probe providers and print status without writing files or pulling models",
    )
    args = parser.parse_args()

    if args.dry_run and args.write:
        print("ERROR: --dry-run and --write are mutually exclusive.", file=sys.stderr)
        return 2

    if not args.dry_run:
        _ensure_local_settings()
    apply_local_settings(override=True)

    if not args.dry_run and args.provider in ("auto", "ollama"):
        _start_ollama_if_needed()

    # Reuse the existing token/probe helpers (no token writes unless --write).
    gat = _load_generate_ai_tokens()

    settings = gat._load_settings() if LOCAL_SETTINGS.exists() else {"IsEncrypted": False, "Values": {}}
    env = gat._effective_env(settings)
    if not args.dry_run:
        apply_local_settings(override=True)

    pull_model = args.pull_model or env.get("OLLAMA_MODEL", "")

    providers = []
    if args.provider == "auto":
        providers = ["ollama", "lmstudio"]
    else:
        providers = [args.provider]

    if args.dry_run:
        return _print_dry_run_status(
            gat,
            providers=providers,
            settings=settings,
            env=env,
            pull_model=pull_model,
        )

    results = gat.run(
        providers=providers,
        settings=settings,
        rotate=False,
        write=False,
        interactive=False,
        use_az_cli=False,
        pull_model=pull_model,
    )

    healthy = [r for r in results if r.status == "ok"]
    if not healthy:
        print("\nNo local LLM runtime is ready yet.")
        print("Install and start one of:")
        print("  Ollama     — https://ollama.ai/download  then: ollama pull llama3.2")
        print("  LM Studio  — https://lmstudio.ai         then: load model + start server")
        print("\nQuick install (Windows):")
        print("  winget install Ollama.Ollama")
        return 1

    winner = healthy[0]
    provider_name = winner.name
    model_name = (
        winner.model
        or load_local_settings().get("OLLAMA_MODEL")
        or load_local_settings().get("LMSTUDIO_MODEL", "local-model")
    )

    patch = {
        "DEFAULT_AI_PROVIDER": provider_name,
        "ARIA_LLM_PROVIDER": provider_name,
    }
    if provider_name == "ollama":
        patch["OLLAMA_BASE_URL"] = env.get("OLLAMA_BASE_URL") or "http://127.0.0.1:11434/v1"
        patch["OLLAMA_MODEL"] = model_name
    elif provider_name == "lmstudio":
        patch["LMSTUDIO_BASE_URL"] = env.get("LMSTUDIO_BASE_URL") or "http://127.0.0.1:1234/v1"
        patch["LMSTUDIO_MODEL"] = model_name

    if args.write:
        _write_settings_patch(patch)
    apply_local_settings(override=True)

    from shared.chat_providers import detect_provider

    provider, info = detect_provider(explicit=provider_name, model_override=model_name)
    preview = ""
    if hasattr(provider, "complete"):
        try:
            preview = str(
                provider.complete([{"role": "user", "content": "Say hello in one short sentence."}], stream=False)
            )
            preview = preview[:160]
        except Exception as exc:
            preview = f"(completion failed: {exc})"

    print("\nLocal LLM is ready.")
    print(f"  Provider : {info.name}")
    print(f"  Model    : {info.model}")
    print(f"  Preview  : {preview}")
    print("\nUse it:")
    print(f'  uv run python ai-projects/chat-cli/src/chat_cli.py --provider {info.name} --once "Hello"')
    print("  uv run python apps/aria/server.py")
    print("  func host start   # Azure Functions (loads local.settings.json automatically)")
    if not args.write:
        print("\nTip: re-run with --write to persist provider/model in local.settings.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
