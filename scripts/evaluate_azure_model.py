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
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add shared directory to path for imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.evaluation_utils import compute_accuracy, load_jsonl, naive_predict

try:
    import openai  # type: ignore

    HAS_AZURE_OPENAI = True
except Exception:
    openai = None
    HAS_AZURE_OPENAI = False


def azure_call(example: Dict[str, Any], deployment: str | None) -> str:
    # If Azure OpenAI isn't configured, fall back to naive predictor
    if not HAS_AZURE_OPENAI or not os.getenv("AZURE_OPENAI_API_KEY"):
        return naive_predict(example)

    prompt = example.get("input") or " ".join(
        [m.get("content", "") for m in (example.get("messages") or [])]
    )
    try:
        # Minimal safe attempt – real deployments may differ in invocation
        resp = openai.ChatCompletion.create(
            deployment_id=deployment,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return naive_predict(example)


def run(
    dataset: Path,
    max_samples: int | None,
    metrics: List[str],
    deployment: str | None,
    save_dir: Path | None,
) -> Dict[str, Any]:
    data = load_jsonl(dataset, max_samples)
    preds: List[str] = []
    expects: List[str | None] = []
    timings: List[float] = []

    use_azure = (
        HAS_AZURE_OPENAI
        and os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    for ex in data:
        t0 = time.perf_counter()
        if use_azure:
            p = azure_call(ex, deployment)
        else:
            p = naive_predict(ex)
        timings.append((time.perf_counter() - t0) * 1000.0)
        preds.append(p)
        expects.append(ex.get("expected") or ex.get("label"))

    summary: Dict[str, Any] = {"samples": len(preds)}
    if "response_time" in metrics:
        summary["response_time_ms"] = (
            round(sum(timings) / len(timings), 3) if timings else 0.0
        )
    if "accuracy" in metrics:
        summary["accuracy"] = round(compute_accuracy(preds, expects), 4)

    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        out = {
            "summary": summary,
            "predictions": [{"pred": p, "expected": e} for p, e in zip(preds, expects)],
        }
        (save_dir / "results.json").write_text(
            json.dumps(out, indent=2), encoding="utf-8"
        )

    return summary


def parse_args():
    ap = argparse.ArgumentParser(
        description="Evaluate Azure OpenAI deployment (offline fallback for CI)"
    )
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
        summary = run(dataset, args.max_samples, metrics, args.deployment, save)
        print(json.dumps({"summary": summary}))
        return 0
    except Exception as e:
        print(f"[error] {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
