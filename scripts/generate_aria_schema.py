#!/usr/bin/env python3
"""Regenerate apps/aria/action_schema.json from apps/aria/server.py.

This makes the canonical Aria action contract available as a static file
for AI agents and tools that cannot hit the live /api/aria/schema endpoint.

Run from repo root:
    python scripts/generate_aria_schema.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "aria"))

import server as aria_server  # type: ignore  # noqa: E402

OUTPUT = REPO_ROOT / "apps" / "aria" / "action_schema.json"

FALLBACK_TAG_FORMS = [
    "[aria:position:X:Y]",
    "[aria:position:NAME]   # center, left, right, front, back, top, bottom",
    "[aria:gesture:NAME]",
    "[aria:animation:NAME]",
    "[aria:say:TEXT]",
    "[aria:expression:NAME]",
    "[aria:pickup:OBJ]",
    "[aria:drop]",
    "[aria:drop:OBJ]",
    "[aria:look:TARGET]",
    "[aria:throw:X:Y]",
    "[aria:wait:SECONDS]",
    "[aria:effect:NAME:...]",
]


def build_schema() -> dict:
    return {
        "actions": aria_server.ARIA_ACTIONS,
        "valid_gestures": sorted(aria_server.VALID_GESTURES),
        "limits": {
            "max_actions_per_sequence": 25,
            "coordinate_range": [0, 100],
            "max_say_text_chars": 200,
            "max_wait_seconds": 30,
        },
        "fallback_tag_forms": FALLBACK_TAG_FORMS,
    }


def main() -> int:
    schema = build_schema()
    OUTPUT.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)} ({OUTPUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
