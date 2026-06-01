#!/usr/bin/env python3
"""Fast smoke test for the legacy quantum-ai code LLM module.

Purpose:
- validate import surface (`api.py`)
- run a tiny train + generate cycle quickly
- provide a deterministic pass/fail signal for local checks and CI

Usage:
    python3 quantum-ai/scripts/smoke_quantum_code_llm.py
    python3 quantum-ai/scripts/smoke_quantum_code_llm.py --backend auto --epochs 1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow direct execution from repo root
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test for quantum-ai code LLM")
    parser.add_argument("--backend", default="classical", help="auto|qiskit.aer|default.qubit|classical")
    parser.add_argument("--epochs", type=int, default=1, help="Tiny epoch count for smoke run")
    parser.add_argument("--max-new-tokens", type=int, default=24)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        from api import generate, train  # noqa: E402
    except ModuleNotFoundError as exc:
        missing = getattr(exc, "name", "<unknown>")
        print(f"[smoke] FAIL: missing dependency '{missing}'")
        print("[smoke] Install minimum deps: python3 -m pip install -r quantum-ai/requirements-smoke.txt")
        print("[smoke] Then retry: python3 quantum-ai/scripts/smoke_quantum_code_llm.py")
        return 2

    model_cfg = {
        "n_qubits": 2,
        "d_model": 32,
        "n_heads": 4,
        "n_layers": 1,
        "n_var_layers": 1,
        "max_seq_len": 32,
        "dropout": 0.1,
        "backend": args.backend,
    }

    train_cfg = {
        "n_epochs": max(1, int(args.epochs)),
        "batch_size": 4,
        "lr": 3e-3,
        "seq_len": 32,
        "log_every": 200,
    }

    extra_snippets = [
        "def add(a, b):\n    return a + b\n",
        "def mul(a, b):\n    return a * b\n",
        "class Box:\n    def __init__(self, v):\n        self.v = v\n",
    ]

    print("[smoke] training tiny model...")
    model, tokenizer = train(
        model_cfg=model_cfg,
        train_cfg=train_cfg,
        extra_snippets=extra_snippets,
    )

    prompt = "def inc(x):"
    print(f"[smoke] generating from prompt: {prompt!r}")
    out = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_new_tokens=args.max_new_tokens,
        temperature=0.7,
        top_k=20,
    )

    if not isinstance(out, str) or len(out.strip()) == 0:
        print("[smoke] FAIL: generation output was empty", file=sys.stderr)
        return 1

    print("[smoke] PASS")
    print("[smoke] sample output:")
    print(out[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
