"""Backward-compatible shim for lora_infer_bridge.

Delegates to talk_to_ai.providers.lora_infer_bridge for legacy imports.
"""
from talk_to_ai.providers.lora_infer_bridge import *  # noqa: F401,F403

if __name__ == "__main__":
    from talk_to_ai.providers.lora_infer_bridge import main
    raise SystemExit(main())
