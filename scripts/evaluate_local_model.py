#!/usr/bin/env python
"""
Lightweight local evaluation script for offline testing and CI.

This evaluator is intentionally conservative and has zero external
dependencies so it can be used in smoke tests and CI environments.

Supported dataset formats:
- JSONL (one object per line)
- JSON array
- simple CSV (first column is input, second column is label)

Supported metrics (minimal, approximate):
- accuracy: exact string match against `expected` or `label`
- response_time: measured time to run the predictor (avg ms)
- determinism: fraction of identical predictions when invoking predictor twice
- basic_bleu: naive unigram overlap score (0..1)

The default predictor is a simple deterministic "echo" function which
returns "echo: <input>". This keeps tests fast and offline.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def load_dataset(path: Path, max_samples: int | None = None) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)

    data: List[Dict[str, Any]] = []
    # Try JSONL (one object per line)
    try:
        with path.open("r", encoding="utf-8") as f:
            # If file looks like a JSON array, parsing as JSON will succeed
            text = f.read().strip()
            if not text:
                return []
            if text.startswith("["):
                objs = json.loads(text)
                if isinstance(objs, list):
                    data = objs
                else:
                    data = [objs]
            else:
                # treat as JSONL
                f.seek(0)
                for i, line in enumerate(f):
                    if max_samples is not None and i >= max_samples:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    data.append(json.loads(line))
    except json.JSONDecodeError:
        # Fallback to CSV (simple) - first column input, second expected
        data = []
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if max_samples is not None and i >= max_samples:
                    break
                if not row:
                    continue
                inp = row[0]
                expected = row[1] if len(row) > 1 else None
                data.append({"input": inp, "expected": expected})

    if max_samples is not None:
        return data[:max_samples]
    return data


def naive_predict(example: Dict[str, Any]) -> str:
    # Extract text from common patterns
    if "input" in example and isinstance(example["input"], str):
        content = example["input"].strip()
        return f"echo: {content}"

    # Chat-style messages
    msgs = example.get("messages") or example.get("conversation") or []
    if isinstance(msgs, list) and msgs:
        # find last user message
        last_user = None
        for m in reversed(msgs):
            if isinstance(m, dict) and m.get("role") == "user":
                last_user = m.get("content", "")
                break
        if last_user is None:
            last_user = msgs[-1].get("content",
                                     "") if isinstance(msgs[-1], dict) else str(msgs[-1])
        return f"echo: {last_user.strip()}"

    # Fallback
    return "echo:"


def compute_accuracy(preds: List[str], expects: List[str]) -> float:
    if not preds:
        return 0.0
    match = 0
    for p, e in zip(preds, expects):
        if e is None:
            continue
        if p.strip() == e.strip():
            match += 1
    return match / len(preds)


def basic_bleu(preds: List[str], expects: List[str]) -> float:
    # Simple unigram overlap score averaged across samples
    def score_one(p: str, e: str) -> float:
        p_tokens = p.split()
        e_tokens = e.split()
        if not p_tokens or not e_tokens:
            return 0.0
        overlap = sum(1 for t in p_tokens if t in e_tokens)
        return overlap / len(p_tokens)

    if not preds:
        return 0.0
    total = 0.0
    count = 0
    for p, e in zip(preds, expects):
        if e is None:
            continue
        total += score_one(p, e)
        count += 1
    return total / count if count else 0.0


def run_evaluation(dataset_path: Path, max_samples: int | None, metrics: List[str], save_dir: Path | None) -> Dict[str, Any]:
    data = load_dataset(dataset_path, max_samples)
    if not data:
        raise ValueError("No data found for evaluation")

    preds: List[str] = []
    expects: List[str | None] = []

    # Warm run
    for ex in data:
        preds.append(naive_predict(ex))
        if "expected" in ex:
            expects.append(ex["expected"])
        elif "label" in ex:
            expects.append(str(ex["label"]))
        else:
            expects.append(None)

    results: Dict[str, Any] = {"samples": len(preds)}

    if "determinism" in metrics:
        # run predictor twice and compare
        preds2 = [naive_predict(ex) for ex in data]
        identical = sum(1 for a, b in zip(preds, preds2) if a == b)
        results["determinism"] = identical / len(preds)

    if "response_time" in metrics:
        times: List[float] = []
        for ex in data:
            t0 = time.time()
            _ = naive_predict(ex)
            times.append((time.time() - t0) * 1000.0)
        avg_ms = sum(times) / len(times)
        results["response_time_ms"] = round(avg_ms, 3)

    if "accuracy" in metrics:
        results["accuracy"] = round(compute_accuracy(preds, expects), 4)

    if "basic_bleu" in metrics or "bleu" in metrics:
        results["basic_bleu"] = round(basic_bleu(preds, expects), 4)

    # Save results
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        out = {
            "summary": results,
            "predictions": [
                {"pred": p, "expected": e} for p, e in zip(preds, expects)
            ],
        }
        path = save_dir / "results.json"
        path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    return results


def parse_args():
    ap = argparse.ArgumentParser(
        description="Evaluate a local model (lightweight, offline)")
    ap.add_argument("--dataset", required=True,
                    help="Path to dataset (json/jsonl/csv)")
    ap.add_argument("--max-samples", type=int, default=None,
                    help="Limit number of evaluation samples")
    ap.add_argument("--metric", dest="metrics", action="append",
                    help="Metric to compute (repeat)")
    ap.add_argument("--output-format", default="json",
                    choices=["json", "text"])
    ap.add_argument(
        "--save-dir", help="Directory to save results", default=None)
    return ap.parse_args()


def main():
    args = parse_args()
    metrics = args.metrics or ["accuracy", "determinism", "response_time"]
    dataset = Path(args.dataset)
    save = Path(args.save_dir) if args.save_dir else None

    try:
        results = run_evaluation(dataset, args.max_samples, metrics, save)
        if args.output_format == "json":
            print(json.dumps({"summary": results}))
        else:
            for k, v in results.items():
                print(f"{k}: {v}")
        return 0
    except Exception as e:
        print(f"[error] Evaluation failed: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
