#!/usr/bin/env python
"""
Evaluation harness for OpenAI / remote API-backed models.

This script will try to call the OpenAI API if credentials are available.
When running in CI or offline, the script falls back to a local deterministic
predictor so it remains useful for smoke tests.

Supported metrics: accuracy, response_time, basic_bleu
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure repository root is on sys.path before importing local shared modules.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.evaluation_utils import compute_metrics, load_jsonl, naive_predict

try:
    import openai  # type: ignore

    HAS_OPENAI = True
except Exception:
    openai = None
    HAS_OPENAI = False


def call_openai_completion(
    example: Dict[str, Any], deployment: str | None = None
) -> str:
    # Minimal safe wrapper; default to naive_predict when API unavailable
    if not HAS_OPENAI or not os.getenv("OPENAI_API_KEY"):
        return naive_predict(example)

    prompt = None
    if "input" in example:
        prompt = example["input"]
    else:
        msgs = example.get("messages") or []
        # join user messages
        prompt = (
            " ".join([m.get("content", "") for m in msgs if m.get("role") == "user"])
            or ""
        )

    if not prompt:
        return naive_predict(example)

    # Use chat completion if available or fallback to completion
    try:
        if deployment:
            resp = openai.ChatCompletion.create(
                model=deployment,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.0,
            )
            return resp.choices[0].message.content.strip()
        else:
            # best-effort fallback when only older API present
            resp = openai.Completion.create(
                model="text-davinci-003", prompt=prompt, max_tokens=200, temperature=0.0
            )
            return str(resp.choices[0].text).strip()
    except Exception:
        # When the API call fails, fall back (useful for CI)
        return naive_predict(example)


def run(
    dataset: Path,
    max_samples: int | None,
    metrics: List[str],
    deployment: str | None,
    save_dir: Path | None,
) -> Dict[str, Any]:
    data = load_jsonl(dataset, max_samples)
    preds = []
    expects = []

    # prefer OpenAI call when available
    use_openai = HAS_OPENAI and os.getenv("OPENAI_API_KEY")

    timings: List[float] = []
    for ex in data:
        t0 = time.perf_counter()
        if use_openai:
            p = call_openai_completion(ex, deployment)
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
        summary.update(compute_metrics(preds, expects))

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
        description="Evaluate via OpenAI API (with local fallback for CI)"
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
