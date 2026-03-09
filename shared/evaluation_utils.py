#!/usr/bin/env python
"""
Shared evaluation utilities for model evaluation scripts.

This module contains common functions used across multiple evaluation scripts
to avoid code duplication. Functions include:
- Dataset loading (JSONL, JSON array, CSV formats)
- Label extraction from datasets
- Naive prediction fallback for offline/CI testing
- Metrics computation (accuracy, etc.)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_jsonl(path: Path, max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load a JSONL file (one JSON object per line).
    
    Args:
        path: Path to the JSONL file
        max_samples: Optional limit on number of samples to load
        
    Returns:
        List of dictionaries parsed from the JSONL file
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(path)
    data: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_samples is not None and i >= max_samples:
                break
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def load_dataset(path: Path, max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load a dataset from JSONL, JSON array, or CSV format.
    
    This function attempts to parse the file as:
    1. JSON array (if starts with '[')
    2. JSONL (one JSON object per line)
    3. CSV (fallback - first column is input, second is label/expected)
    
    Args:
        path: Path to the dataset file
        max_samples: Optional limit on number of samples to load
        
    Returns:
        List of dictionaries with dataset entries
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(path)

    data: List[Dict[str, Any]] = []
    
    # Try JSON/JSONL first
    try:
        with path.open("r", encoding="utf-8") as f:
            text = f.read().strip()
            if not text:
                return []
            
            if text.startswith("["):
                # Parse as JSON array
                objs = json.loads(text)
                if isinstance(objs, list):
                    data = objs[:max_samples] if max_samples else objs
                else:
                    data = [objs]
            else:
                # Parse as JSONL
                f.seek(0)
                for i, line in enumerate(f):
                    if max_samples is not None and i >= max_samples:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    data.append(json.loads(line))
    except json.JSONDecodeError:
        # Fallback to CSV - first column input, second expected/label
        data = []
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if max_samples is not None and i >= max_samples:
                    break
                if not row:
                    continue
                # Create dictionary from CSV row
                input_val = row[0] if len(row) > 0 else ""
                expected_val = row[1] if len(row) > 1 else None
                data.append({"input": input_val, "expected": expected_val})
    
    return data


def load_labels_from_dataset(path: Path, max_samples: Optional[int] = None) -> List[Any]:
    """
    Extract labels from a dataset file.
    
    Supports JSONL, JSON array, and CSV formats. Looks for 'label' key in JSON
    objects, or uses second column for CSV files.
    
    Args:
        path: Path to the dataset file
        max_samples: Optional limit on number of samples to load
        
    Returns:
        List of labels (can be any type - strings, integers, etc.)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(path)
    
    labels: List[Any] = []

    # Try JSON/JSONL first
    try:
        with path.open("r", encoding="utf-8") as f:
            txt = f.read().strip()
            if not txt:
                return []
            
            if txt.startswith("["):
                # Parse as JSON array
                obj = json.loads(txt)
                if isinstance(obj, list):
                    for i, item in enumerate(obj):
                        if max_samples is not None and i >= max_samples:
                            break
                        labels.append(item.get("label") if isinstance(item, dict) else None)
                    return labels
            else:
                # Parse as JSONL
                f.seek(0)
                for i, line in enumerate(f):
                    if max_samples is not None and i >= max_samples:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    labels.append(obj.get("label"))
                return labels
    except json.JSONDecodeError:
        # Fallback to CSV - second column is label
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if max_samples is not None and i >= max_samples:
                    break
                if not row:
                    continue
                label = row[1] if len(row) > 1 else None
                labels.append(label)
        return labels
    
    return labels


def naive_predict(example: Dict[str, Any]) -> str:
    """
    Simple deterministic fallback predictor for offline/CI testing.
    
    Returns "echo: <content>" based on the input. This is useful when
    external APIs are unavailable or for smoke testing.
    
    Args:
        example: Dictionary with 'input' or 'messages' field
        
    Returns:
        Echo string with the input content
    """
    # Check for direct input field
    if "input" in example and isinstance(example["input"], str):
        return f"echo: {example['input'].strip()}"
    
    # Check for messages array (chat format)
    msgs = example.get("messages") or []
    if msgs and isinstance(msgs, list):
        for m in reversed(msgs):
            if isinstance(m, dict) and m.get("role") == "user":
                return f"echo: {m.get('content', '').strip()}"
    
    return "echo:"


def compute_accuracy(preds: List[str], expects: List[Optional[str]]) -> float:
    """
    Compute accuracy as fraction of exact string matches.
    
    Args:
        preds: List of predicted strings
        expects: List of expected strings (can contain None values to skip)
        
    Returns:
        Accuracy as a float between 0.0 and 1.0
    """
    if not preds:
        return 0.0
    
    matched = 0
    total = 0
    for p, e in zip(preds, expects):
        if e is None:
            continue
        total += 1
        if p.strip() == e.strip():
            matched += 1
    
    return matched / total if total > 0 else 0.0


def compute_metrics(preds: List[str], expects: List[Optional[str]]) -> Dict[str, float]:
    """
    Compute evaluation metrics for predictions.
    
    Currently computes accuracy. Can be extended with additional metrics
    like BLEU, F1, etc.
    
    Args:
        preds: List of predicted strings
        expects: List of expected strings (can contain None values to skip)
        
    Returns:
        Dictionary of metric names to values
    """
    if not preds:
        return {}
    
    metrics = {
        "accuracy": compute_accuracy(preds, expects)
    }
    
    return metrics
