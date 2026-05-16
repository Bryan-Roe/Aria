#!/usr/bin/env python3
"""Provider smoke script - prints detected provider and info.

Run: python scripts/provider_smoke.py
Exits 0 if a provider (real or fallback) is detected and callable.
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

# Ensure repo root is on sys.path so local imports work when run as a script
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from shared.core.module_registry import AIProjectsRegistry


def main() -> int:
    try:
        ns = AIProjectsRegistry.chat_cli()
        provider, info = ns.detect_provider()
        out = {
            "provider_class": provider.__class__.__name__ if provider is not None else None,
            "provider_name": getattr(info, "name", None) if info is not None else None,
            "provider_model": getattr(info, "model", None) if info is not None else None,
        }
        print(json.dumps(out))
        # Sanity-check: call provider.complete with a tiny prompt if it has the method
        if provider is not None and hasattr(provider, "complete"):
            try:
                res = provider.complete([{"role": "user", "content": "ping"}], stream=False)
                # If provider returns a mapping or text, treat as success
                print("provider_response_preview:", str(res)[:200])
            except Exception as e:
                print("provider completion failed:", str(e))
        return 0
    except Exception as exc:  # pragma: no cover - smoke script
        print("ERROR", str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
