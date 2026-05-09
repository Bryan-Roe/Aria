#!/usr/bin/env python3
"""Validate .foundry deployment configuration.

Current contract:
- .foundry/.deployment.json exists
- JSON root is an object
- projectId exists and is a non-empty UUID string
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    cfg = repo_root / ".foundry" / ".deployment.json"

    if not cfg.exists():
        print(f"❌ missing foundry config: {cfg}")
        return 1

    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"❌ invalid JSON in {cfg}: {exc}")
        return 1

    if not isinstance(data, dict):
        print("❌ .deployment.json root must be an object")
        return 1

    project_id = data.get("projectId")
    if not isinstance(project_id, str) or not project_id.strip():
        print("❌ projectId must be a non-empty string")
        return 1

    if not UUID_RE.match(project_id):
        print("❌ projectId must be a valid UUID")
        return 1

    print("✅ Foundry deployment config valid")
    print(f"   projectId: {project_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
