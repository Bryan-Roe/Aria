#!/usr/bin/env python
"""Simple evaluation CLI that uses the evaluator utilities.

Usage examples
    python scripts/evaluate.py --mode tags \
            --dataset tests/evaluation/data/tags_test.jsonl
    python scripts/evaluate.py --mode actions \
            --dataset tests/evaluation/data/actions_test.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from scripts.eval.evaluator import evaluate_actions, evaluate_tags


def _tags_predictor_from_server(mode: str):
    # Try to import implementation from aria_web.server. If the module has
    # syntax errors or is missing, fall back to the small builtin predictor
    try:
        from aria_web.server import (
            generate_tags_fallback,
            generate_tags_ai,
        )  # type: ignore
    except Exception:
        # Local fallback implementation
        from scripts.eval.evaluator import fallback_tags_predictor

        return fallback_tags_predictor

    if mode == "fallback":
        return generate_tags_fallback

    def p_ai(cmd: str):
        res = generate_tags_ai(cmd)
        if isinstance(res, dict):
            return res.get("tags", [])
        return []

    return p_ai


def _action_parser_from_server(use_llm: bool):
    try:
        from aria_web.server import action_parser  # type: ignore

        def parse_fn(cmd: str) -> List[dict]:
            return action_parser.parse(cmd, use_llm=use_llm)

        return parse_fn
    except Exception:
        # fallback
        from scripts.eval.evaluator import fallback_action_parser

        return fallback_action_parser


def main():
    ap = argparse.ArgumentParser(description="Run small evaluations")
    ap.add_argument("--mode", choices=["tags", "actions"], required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--max-samples", type=int)
    ap.add_argument(
        "--provider",
        choices=["fallback", "ai"],
        default="fallback",
    )
    ap.add_argument(
        "--use-llm",
        action="store_true",
        help=(
            "For action parsing use LLM provider if available"
        ),
    )
    ap.add_argument(
        "--top-k",
        type=int,
        default=None,
        help=("Limit predicted tags to top K (for tag eval)"),
    )
    ap.add_argument(
        "--output",
        default=None,
        help=("Write JSON summary to file"),
    )

    args = ap.parse_args()
    ds = Path(args.dataset)
    if not ds.exists():
        raise SystemExit(f"Dataset not found: {ds}")

    if args.mode == "tags":
        predictor = _tags_predictor_from_server(args.provider)
        res = evaluate_tags(
            ds, predictor, max_samples=args.max_samples, top_k=args.top_k
        )
    else:
        parser = _action_parser_from_server(use_llm=args.use_llm)
        res = evaluate_actions(ds, parser, max_samples=args.max_samples)

    print(json.dumps(res, indent=2, ensure_ascii=False))
    if args.output:
        Path(args.output).write_text(
            json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
