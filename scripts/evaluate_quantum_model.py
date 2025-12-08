#!/usr/bin/env python
"""
Simple evaluation wrapper for quantum model artifacts (lightweight).

This script is designed for CI-friendly evaluation of precomputed quantum model
results. It expects a model JSON file (model_path) containing a `predictions`
array aligned with the dataset entries, or a mapping object. The dataset may be
CSV or JSONL containing labels for evaluation.

Supported metrics: accuracy, precision, recall, f1_score
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_labels_from_dataset(path: Path, max_samples: Optional[int] = None) -> List[Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    labels: List[Any] = []

    # Try JSONL / JSON array first
    try:
        with path.open("r", encoding="utf-8") as f:
            txt = f.read().strip()
            if not txt:
                return []
            if txt.startswith("["):
                obj = json.loads(txt)
                if isinstance(obj, list):
                    for i, item in enumerate(obj):
                        if max_samples is not None and i >= max_samples:
                            break
                        labels.append(item.get("label")
                                      if isinstance(item, dict) else None)
                    return labels
            else:
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
        # Fallback to CSV
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if max_samples is not None and i >= max_samples:
                    break
                if not row:
                    continue
                # assume second column is label
                label = row[1] if len(row) > 1 else None
                labels.append(label)
        return labels


def load_model_predictions(model_path: Path, max_samples: Optional[int] = None) -> List[Any]:
    if not model_path.exists():
        raise FileNotFoundError(model_path)
    with model_path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    preds = obj.get("predictions") if isinstance(obj, dict) else None
    if preds is None:
        # If the model file contains a single scalar or mapping return a best-effort
        # representation: try 'labels' or 'prediction' keys
        preds = obj.get("labels") or obj.get("prediction") or []
    if max_samples is not None:
        preds = preds[:max_samples]
    return preds


def compute_binary_metrics(y_true: List[Any], y_pred: List[Any]) -> Dict[str, float]:
    # Convert to strings for stable comparison
    paired = list(zip(y_true, y_pred))
    if not paired:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0}

    tp = fp = tn = fn = 0
    for t, p in paired:
        if t is None:
            continue
        t_s = str(t).strip()
        p_s = str(p).strip()
        # assume binary labels '1'/'0' or 'true'/'false'
        if t_s == p_s:
            if t_s.lower() in ("1", "true", "yes"):
                tp += 1
            else:
                tn += 1
        else:
            if p_s.lower() in ("1", "true", "yes"):
                fp += 1
            else:
                fn += 1

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / \
        (precision + recall) if (precision + recall) else 0.0
    return {"accuracy": round(accuracy, 4), "precision": round(precision, 4), "recall": round(recall, 4), "f1_score": round(f1, 4)}


def run(dataset: Path, model: Path, max_samples: Optional[int], metrics: List[str], save_dir: Optional[Path]) -> Dict[str, Any]:
    y_true = load_labels_from_dataset(dataset, max_samples)
    y_pred = load_model_predictions(model, max_samples)

    if len(y_pred) < len(y_true):
        # pad with None
        y_pred += [None] * (len(y_true) - len(y_pred))

    # For now support binary metrics via compute_binary_metrics
    summary: Dict[str, float] = {}
    if any(m in ("accuracy", "precision", "recall", "f1_score") for m in metrics):
        mvals = compute_binary_metrics(y_true, y_pred)
        # include requested metrics
        for m in ("accuracy", "precision", "recall", "f1_score"):
            if m in metrics:
                summary[m] = mvals.get(m, 0.0)

    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        out = {"summary": summary, "predictions": [
            {"pred": p, "expected": t} for p, t in zip(y_pred, y_true)]}
        (save_dir / "results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    return summary


def parse_args():
    ap = argparse.ArgumentParser(
        description="Evaluate lightweight quantum model artifacts")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--max-samples", type=int, default=None)
    ap.add_argument("--metric", action="append", dest="metrics")
    ap.add_argument("--save-dir", default=None)
    return ap.parse_args()


def main():
    args = parse_args()
    metrics = args.metrics or ["accuracy"]
    dataset = Path(args.dataset)
    model = Path(args.model)
    savedir = Path(args.save_dir) if args.save_dir else None

    try:
        summary = run(dataset, model, args.max_samples, metrics, savedir)
        print(json.dumps({"summary": summary}))
        return 0
    except Exception as e:
        print(f"[error] {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
