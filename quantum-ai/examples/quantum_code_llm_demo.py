#!/usr/bin/env python3
"""quantum_code_llm_demo.py — Quick demo: train the Quantum Code LLM and generate code.

Usage
-----
    python ai-projects/quantum-ml/examples/quantum_code_llm_demo.py

Options (set via env vars or edit the CONFIG dicts below):
    QLCM_EPOCHS    number of training epochs    (default 3)
    QLCM_QUBITS    number of qubits             (default 4)
    QLCM_DMODEL    model hidden dim             (default 64)
    QLCM_BACKEND   quantum backend              (default auto)
"""

from __future__ import annotations

import os
import sys

# Allow running from repo root as well as from examples/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from quantum_code_llm import generate, train  # noqa: E402

# ── Configuration ──────────────────────────────────────────────────────────
MODEL_CFG = {
    "n_qubits": int(os.environ.get("QLCM_QUBITS", "4")),
    "d_model": int(os.environ.get("QLCM_DMODEL", "64")),
    "n_heads": 4,
    "n_layers": 2,
    "n_var_layers": 2,
    "max_seq_len": 64,
    "dropout": 0.1,
    "backend": os.environ.get("QLCM_BACKEND", "auto"),
}

TRAIN_CFG = {
    "n_epochs": int(os.environ.get("QLCM_EPOCHS", "3")),
    "batch_size": 8,
    "lr": 3e-3,
    "seq_len": 64,
    "log_every": 30,
}

# Optional extra code snippets to add to the training corpus
EXTRA_SNIPPETS = [
    "def power(base, exp):\n    return base ** exp\n",
    "def absolute(n):\n    return abs(n)\n",
    "def concat(a, b):\n    return str(a) + str(b)\n",
]

# Prompts used for generation after training
PROMPTS = [
    "def ",
    "class ",
    "def factorial(n):",
    "def is_prime(n):",
    "class Stack:",
]

# ── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    print("=" * 60)
    print("  Quantum Code LLM — Demo")
    print("=" * 60)

    model, tokenizer = train(
        model_cfg=MODEL_CFG,
        train_cfg=TRAIN_CFG,
        extra_snippets=EXTRA_SNIPPETS,
    )

    print("\n" + "=" * 60)
    print("  Code Generation Samples")
    print("=" * 60)

    for prompt in PROMPTS:
        print(f"\nPrompt: {prompt!r}")
        print("-" * 40)
        result = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_new_tokens=80,
            temperature=0.8,
            top_k=40,
        )
        print(result)

    print("\n✓ Demo complete.")


if __name__ == "__main__":
    main()
