#!/usr/bin/env python3
"""Validate generated_sites bundle contract.

Default contract per bundle directory:
- index.html
- style.css
- script.js

Strict mode additionally requires:
- metadata.json

metadata.json required keys:
- name (str)
- pages (list)
- features (list)
- files (list)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FILES = {"index.html", "style.css", "script.js"}
REQUIRED_METADATA_KEYS = {
    "name": str,
    "pages": list,
    "features": list,
    "files": list,
}


def _is_bundle_dir(path: Path) -> bool:
    return path.is_dir() and not path.name.startswith(".")


def validate_bundle(bundle_dir: Path, *, strict_metadata: bool = False) -> list[str]:
    errors: list[str] = []

    present_files = {p.name for p in bundle_dir.iterdir() if p.is_file()}
    missing = REQUIRED_FILES - present_files
    if missing:
        errors.append(f"missing required files: {', '.join(sorted(missing))}")

    metadata_path = bundle_dir / "metadata.json"
    if not metadata_path.exists():
        if strict_metadata:
            errors.append("missing required file: metadata.json")
        return errors

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - simple CLI tool
        errors.append(f"invalid metadata.json: {exc}")
        return errors

    if not isinstance(metadata, dict):
        errors.append("metadata.json root must be an object")
        return errors

    for key, expected_type in REQUIRED_METADATA_KEYS.items():
        if key not in metadata:
            errors.append(f"metadata missing key: {key}")
            continue
        if not isinstance(metadata[key], expected_type):
            errors.append(
                f"metadata key '{key}' must be {expected_type.__name__}, got {type(metadata[key]).__name__}"
            )

    files_list = metadata.get("files")
    if isinstance(files_list, list):
        files_set = set(str(x) for x in files_list)
        required_meta_entries = set(REQUIRED_FILES)
        if strict_metadata:
            required_meta_entries.add("metadata.json")
        missing_in_files = sorted(required_meta_entries - files_set)
        if missing_in_files:
            errors.append(
                f"metadata.files missing required entries: {', '.join(missing_in_files)}"
            )

    return errors


def main() -> int:
    strict_metadata = "--strict-metadata" in sys.argv
    repo_root = Path(__file__).resolve().parents[1]
    bundles_root = repo_root / "generated_sites"

    if not bundles_root.exists():
        print("generated_sites/ not found; nothing to validate")
        return 0

    bundle_dirs = sorted([p for p in bundles_root.iterdir() if _is_bundle_dir(p)])
    if not bundle_dirs:
        print("No bundle directories found under generated_sites/")
        return 0

    total = len(bundle_dirs)
    failed = 0

    print(f"Validating {total} generated site bundle(s)...")
    for bundle in bundle_dirs:
        errors = validate_bundle(bundle, strict_metadata=strict_metadata)
        if errors:
            failed += 1
            print(f"❌ {bundle.name}")
            for err in errors:
                print(f"   - {err}")
        else:
            print(f"✅ {bundle.name}")

    if failed:
        print(f"\nValidation failed: {failed}/{total} bundle(s) have issues")
        return 1

    print(f"\nValidation passed: {total}/{total} bundle(s) valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
