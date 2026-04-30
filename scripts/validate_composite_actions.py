#!/usr/bin/env python3
"""Validate local composite GitHub actions under .github/actions/.

Checks:
- each action dir contains action.yml
- action.yml parses as mapping
- required keys exist: name, runs
- runs.using == 'composite'
- runs.steps is a non-empty list
- each step has at least one of: uses/run
- if step has run, it also defines shell
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


def validate_action(action_dir: Path) -> list[str]:
    errors: list[str] = []
    action_file = action_dir / "action.yml"

    if not action_file.exists():
        return ["missing action.yml"]

    try:
        content = yaml.safe_load(action_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid YAML: {exc}"]

    if not isinstance(content, dict):
        return ["action.yml root must be a mapping"]

    if not content.get("name"):
        errors.append("missing required key: name")

    runs = content.get("runs")
    if not isinstance(runs, dict):
        errors.append("missing required mapping: runs")
        return errors

    if runs.get("using") != "composite":
        errors.append("runs.using must be 'composite'")

    steps = runs.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("runs.steps must be a non-empty list")
        return errors

    for i, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"step #{i}: must be a mapping")
            continue

        has_uses = "uses" in step
        has_run = "run" in step
        if not (has_uses or has_run):
            errors.append(f"step #{i}: must contain 'uses' or 'run'")

        if has_run and "shell" not in step:
            errors.append(f"step #{i}: run step must define 'shell'")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    actions_root = repo_root / ".github" / "actions"

    if not actions_root.exists():
        print(".github/actions not found; nothing to validate")
        return 0

    action_dirs = sorted([p for p in actions_root.iterdir() if p.is_dir()])
    if not action_dirs:
        print("No local actions found under .github/actions")
        return 0

    print(f"Validating {len(action_dirs)} local composite action(s)...")
    failed = 0
    for action_dir in action_dirs:
        errors = validate_action(action_dir)
        if errors:
            failed += 1
            print(f"❌ {action_dir.name}")
            for err in errors:
                print(f"   - {err}")
        else:
            print(f"✅ {action_dir.name}")

    if failed:
        print(f"\nValidation failed: {failed}/{len(action_dirs)} action(s) have issues")
        return 1

    print(f"\nValidation passed: {len(action_dirs)}/{len(action_dirs)} actions valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
