#!/usr/bin/env python
"""
Shared JSON I/O utilities.

This module provides standardized JSON reading and writing functions
to reduce code duplication and ensure consistent formatting.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def load_json(path: Union[str, Path], default: Optional[Any] = None) -> Any:
    """
    Load JSON data from a file with optional default fallback.

    Args:
        path: Path to the JSON file
        default: Optional default value if file doesn't exist or is invalid.
                If None, exceptions are raised normally.

    Returns:
        Parsed JSON data (dict, list, or other JSON type)

    Raises:
        FileNotFoundError: If file doesn't exist and no default provided
        JSONDecodeError: If file is not valid JSON and no default provided

    Examples:
        # Load JSON file
        data = load_json("config.json")

        # Load with default fallback
        data = load_json("config.json", default={})
    """
    path = Path(path)

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        if default is not None:
            return default
        raise


def load_status_json(
    path: Union[str, Path],
    *,
    max_age_seconds: Optional[int] = None,
    default: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Load a status JSON file safely with optional staleness metadata.

    Always returns a dictionary and appends helper metadata keys:
      - _status_file_exists: bool
      - _status_file_age_seconds: Optional[float]
      - _status_file_stale: Optional[bool]
      - _status_file_error: Optional[str]

    Args:
        path: Path to status JSON file
        max_age_seconds: Optional staleness threshold
        default: Optional dict merged as fallback base

    Returns:
        Dictionary containing parsed JSON object (if valid) plus metadata.
    """
    file_path = Path(path)
    result: Dict[str, Any] = dict(default or {})

    exists = file_path.exists()
    age_seconds: Optional[float] = None
    stale: Optional[bool] = None
    error: Optional[str] = None

    if exists:
        try:
            age_seconds = max(0.0, time.time() - file_path.stat().st_mtime)
            if max_age_seconds is not None:
                stale = age_seconds > max_age_seconds

            with file_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)

            if isinstance(payload, dict):
                result.update(payload)
            else:
                error = "JSON root is not an object"
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    else:
        error = "File not found"

    result["_status_file_exists"] = exists
    result["_status_file_age_seconds"] = age_seconds
    result["_status_file_stale"] = stale
    result["_status_file_error"] = error
    return result


def save_json(
    data: Any,
    path: Union[str, Path],
    indent: int = 2,
    ensure_ascii: bool = False,
    create_parents: bool = True,
) -> None:
    """
    Save data to a JSON file with consistent formatting.

    Args:
        data: Data to serialize (must be JSON-serializable)
        path: Path where to save the JSON file
        indent: Number of spaces for indentation (default: 2)
        ensure_ascii: If True, escape non-ASCII characters (default: False)
        create_parents: If True, create parent directories (default: True)

    Examples:
        # Save dict to JSON
        save_json({"key": "value"}, "output.json")

        # Save without indentation (compact)
        save_json(data, "compact.json", indent=None)
    """
    path = Path(path)

    if create_parents:
        path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


def load_jsonl(
    path: Union[str, Path], max_lines: Optional[int] = None, skip_empty: bool = True
) -> List[Dict[str, Any]]:
    """
    Load JSONL file (one JSON object per line).

    Args:
        path: Path to the JSONL file
        max_lines: Optional limit on number of lines to read
        skip_empty: If True, skip empty lines (default: True)

    Returns:
        List of dictionaries parsed from the JSONL file

    Raises:
        FileNotFoundError: If the file doesn't exist
        JSONDecodeError: If a line is not valid JSON

    Examples:
        # Load all lines
        data = load_jsonl("data.jsonl")

        # Load first 100 lines
        data = load_jsonl("data.jsonl", max_lines=100)
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    data: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_lines is not None and i >= max_lines:
                break

            line = line.strip()
            if skip_empty and not line:
                continue

            data.append(json.loads(line))

    return data


def save_jsonl(
    data: List[Any],
    path: Union[str, Path],
    create_parents: bool = True,
    ensure_ascii: bool = False,
) -> None:
    """
    Save data to JSONL file (one JSON object per line).

    Args:
        data: List of objects to serialize (each must be JSON-serializable)
        path: Path where to save the JSONL file
        create_parents: If True, create parent directories (default: True)
        ensure_ascii: If True, escape non-ASCII characters (default: False)

    Examples:
        # Save list of dicts to JSONL
        data = [{"id": 1}, {"id": 2}]
        save_jsonl(data, "output.jsonl")
    """
    path = Path(path)

    if create_parents:
        path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for obj in data:
            f.write(json.dumps(obj, ensure_ascii=ensure_ascii) + "\n")


def merge_json_files(
    input_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
    merge_strategy: str = "extend",
) -> None:
    """
    Merge multiple JSON files into one.

    Args:
        input_paths: List of paths to JSON files to merge
        output_path: Path where to save the merged JSON
        merge_strategy: How to merge files:
            - "extend": Expect lists and concatenate them
            - "update": Expect dicts and merge them (later files override)

    Examples:
        # Merge multiple JSON array files
        merge_json_files(["file1.json", "file2.json"], "merged.json")

        # Merge dict files with update strategy
        merge_json_files(["base.json", "override.json"], "final.json", merge_strategy="update")
    """
    if merge_strategy == "extend":
        merged: List[Any] = []
        for path in input_paths:
            data = load_json(path)
            if isinstance(data, list):
                merged.extend(data)
            else:
                merged.append(data)
    elif merge_strategy == "update":
        merged: Dict[str, Any] = {}
        for path in input_paths:
            data = load_json(path)
            if isinstance(data, dict):
                merged.update(data)
            else:
                raise ValueError(f"Expected dict in {path} for update strategy")
    else:
        raise ValueError(f"Unknown merge strategy: {merge_strategy}")

    save_json(merged, output_path)
