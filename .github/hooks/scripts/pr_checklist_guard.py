#!/usr/bin/env python3
"""PR checklist guard hook.

Ensures hook script path exists and can be executed by hook runners.
"""

import json
import os
import sys


def _event_name() -> str:
    return (
        os.environ.get("COPILOT_HOOK_EVENT")
        or os.environ.get("hook_event_name")
        or os.environ.get("HOOK_EVENT_NAME")
        or "unknown"
    )


def _load_payload() -> dict:
    payload_str = os.environ.get("COPILOT_HOOK_PAYLOAD", "")
    if payload_str:
        try:
            return json.loads(payload_str)
        except json.JSONDecodeError:
            return {}
    return {}


def main() -> int:
    _ = _event_name()
    _ = _load_payload()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
