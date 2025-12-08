#!/usr/bin/env python
"""
Evaluation script for Azure OpenAI deployments with a local offline fallback.

Works similarly to evaluate_openai_model.py but accepts --deployment to
choose the Azure deployment name. If Azure credentials are missing the script
falls back to a deterministic local predictor (echo) and still produces
machine-readable evaluation outputs which are useful for CI smoke tests.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

try:
    import openai  # type: ignore
    HAS_AZURE_OPENAI = True
except Exception:
    openai = None
    HAS_AZURE_OPENAI = False


def load_jsonl(path: Path, max_samples: int | None = None) -> List[Dict[str, Any]]:
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


def naive_predict(example: Dict[str, Any]) -> str:
    if "input" in example and isinstance(example["input"], str):
        return f"echo: {example['input'].strip()}"
    msgs = example.get("messages") or []
    if msgs and isinstance(msgs, list):
        for m in reversed(msgs):
            if isinstance(m, dict) and m.get("role") == "user":
                return f"echo: {m.get('content', '').strip()}"
    return "echo:"


def azure_call(example: Dict[str, Any], deployment: str | None) -> str:
    # If Azure OpenAI isn't configured, fall back to naive predictor
    if not HAS_AZURE_OPENAI or not os.getenv("AZURE_OPENAI_API_KEY"):
        return naive_predict(example)

    prompt = example.get("input") or " ".join(
        [m.get("content", "") for m in (example.get("messages") or [])])
    try:
        # Minimal safe attempt – real deployments may differ in invocation
        resp = openai.ChatCompletion.create(deployment_id=deployment, messages=[
                                            {"role": "user", "content": prompt}], max_tokens=200)
        return resp.choices[0].message.content.strip()
    except Exception:
        return naive_predict(example)


def compute_accuracy(preds: List[str], expects: List[str | None]) -> float:
    if not preds:
        return 0.0
    matched = 0
    for p, e in zip(preds, expects):
        if e is None:
            continue
        if p.strip() == e.strip():
            matched += 1
    return matched / len(preds)


def run(dataset: Path, max_samples: int | None, metrics: List[str], deployment: str | None, save_dir: Path | None) -> Dict[str, Any]:
    data = load_jsonl(dataset, max_samples)
    preds: List[str] = []
    expects: List[str | None] = []
    timings: List[float] = []

    use_azure = HAS_AZURE_OPENAI and os.getenv(
        "AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT")

    for ex in data:
        t0 = time.time()
        if use_azure:
            p = azure_call(ex, deployment)
        else:
            p = naive_predict(ex)
        timings.append((time.time() - t0) * 1000.0)
        preds.append(p)
        expects.append(ex.get("expected") or ex.get("label"))

    summary: Dict[str, Any] = {"samples": len(preds)}
    if "response_time" in metrics:
        summary["response_time_ms"] = round(
            sum(timings) / len(timings), 3) if timings else 0.0
    if "accuracy" in metrics:
        summary["accuracy"] = round(compute_accuracy(preds, expects), 4)

    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        out = {"summary": summary, "predictions": [
            {"pred": p, "expected": e} for p, e in zip(preds, expects)]}
        (save_dir / "results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    return summary


def parse_args():
    ap = argparse.ArgumentParser(
        description="Evaluate Azure OpenAI deployment (offline fallback for CI)")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--max-samples", type=int, default=None)
    ap.add_argument("--metric", action="append", dest="metrics")
    ap.add_argument("--deployment", default=None)
    ap.add_argument("--save-dir", default=None)
    return ap.parse_args()


def main():
    args = parse_args()
    metrics = args.metrics or ["accuracy", "response_time"]
    dataset = Path(args.dataset)
    save = Path(args.save_dir) if args.save_dir else None

    try:
        summary = run(dataset, args.max_samples,
                      metrics, args.deployment, save)
        print(json.dumps({"summary": summary}))
        return 0
    except Exception as e:
        print(f"[error] {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
