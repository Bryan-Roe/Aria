"""Shared evaluation utilities for dataset loading and naive prediction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_jsonl(path: Path, max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load records from a JSONL file.

    Args:
        path: Path to the ``.jsonl`` file.
        max_samples: If set, return at most this many records.

    Returns:
        List of parsed JSON objects.
    """
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
            if max_samples is not None and len(records) >= max_samples:
                break
    return records


def load_dataset(path: Path, max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load a dataset from either JSON array or JSONL format.

    Args:
        path: Path to the dataset file (``.json`` or ``.jsonl``).
        max_samples: If set, return at most this many records.

    Returns:
        List of dataset records.
    """
    suffix = Path(path).suffix.lower()
    if suffix == ".jsonl":
        return load_jsonl(path, max_samples=max_samples)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        if max_samples is not None:
            data = data[:max_samples]
        return data

    raise ValueError(f"Unsupported dataset format in {path}")


def naive_predict(example: Dict[str, Any]) -> str:
    """Return a naive echo prediction for an example.

    Extracts the input text from ``example["input"]`` or the last user
    message from ``example["messages"]`` and prefixes it with ``"echo: "``.

    Args:
        example: A dataset record with either an ``input`` key or a
            ``messages`` list.

    Returns:
        A string of the form ``"echo: <text>"``.
    """
    text = ""
    if "input" in example:
        text = example["input"]
    elif "messages" in example:
        user_msgs = [m for m in example["messages"] if m.get("role") == "user"]
        if user_msgs:
            text = user_msgs[-1].get("content", "")
    if text:
        return f"echo: {text}"
    return "echo:"


def load_labels_from_dataset(
    path: Path, max_samples: Optional[int] = None
) -> List[Any]:
    """Load ground-truth labels from a dataset file.

    Looks for a ``label`` key in each record. Falls back to the last
    assistant message content if ``messages`` is present.

    Args:
        path: Path to a ``.json`` or ``.jsonl`` dataset file.
        max_samples: If set, return at most this many labels.

    Returns:
        List of label values (strings or numbers).
    """
    records = load_dataset(path, max_samples=max_samples)
    labels: List[Any] = []
    for rec in records:
        if "label" in rec:
            labels.append(rec["label"])
        elif "expected" in rec:
            labels.append(rec["expected"])
        elif "messages" in rec:
            assistant_msgs = [
                m for m in rec["messages"] if m.get("role") == "assistant"
            ]
            if assistant_msgs:
                labels.append(assistant_msgs[-1].get("content", ""))
            else:
                labels.append(None)
        else:
            labels.append(None)
    return labels
