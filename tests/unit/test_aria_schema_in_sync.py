"""Verify apps/aria/action_schema.json stays in sync with apps/aria/server.py.

If this test fails, run: ``python scripts/generate_aria_schema.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps" / "aria"))

import server as aria_server  # type: ignore  # noqa: E402

SCHEMA_PATH = REPO_ROOT / "apps" / "aria" / "action_schema.json"


def test_static_schema_matches_server():
    assert SCHEMA_PATH.exists(), "apps/aria/action_schema.json missing"
    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    # Action types must match exactly (any drift means the static file is stale)
    assert set(data["actions"].keys()) == set(aria_server.ARIA_ACTIONS.keys()), (
        "Static schema action types out of sync with server.py — "
        "regenerate with: python scripts/generate_aria_schema.py"
    )

    # Valid gestures must match exactly
    assert set(data["valid_gestures"]) == set(aria_server.VALID_GESTURES), (
        "Static schema valid_gestures out of sync with server.py — "
        "regenerate with: python scripts/generate_aria_schema.py"
    )

    # Limits sanity (matches what /api/aria/schema returns)
    assert data["limits"]["max_actions_per_sequence"] == 25
    assert data["limits"]["coordinate_range"] == [0, 100]
    assert data["limits"]["max_say_text_chars"] == 200
    assert data["limits"]["max_wait_seconds"] == 30
