#!/usr/bin/env python3
"""Task completion guard hook.

Ensures hook script path exists and can be executed by hook runners.
"""

import json
import os
from pathlib import Path


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


def _load_transcript() -> list:
    transcript_path = os.environ.get("transcript_path")
    if not transcript_path:
        return []

    path = Path(transcript_path)
    if not path.exists():
        return []

    rows: list = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []

    return rows


def main() -> int:
    _ = _event_name()
    _ = _load_payload()
    _ = _load_transcript()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
