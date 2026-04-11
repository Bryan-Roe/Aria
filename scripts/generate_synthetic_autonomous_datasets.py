#!/usr/bin/env python3
"""Generate synthetic training datasets for autonomous demo cycles.

Writes JSONL chat-style datasets under data_out/autonomous_datasets/ so the
main read-only datasets/ tree remains untouched.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = REPO_ROOT / "data_out" / "autonomous_datasets"

SAMPLES = {
    "quantum": [
        (
            "Explain superposition in one sentence.",
            "Superposition means a qubit can represent multiple states until measured.",
        ),
        (
            "What is entanglement?",
            "Entanglement links qubits so the state of one is correlated with the state of another.",
        ),
        (
            "When should I use a quantum simulator?",
            "Use a simulator first for fast debugging and deterministic iteration before running real hardware jobs.",
        ),
    ],
    "aria_commands": [
        (
            "Move left and wave.",
            "Sure — moving left now [aria:walk:left] and waving [aria:wave].",
        ),
        (
            "Jump then idle.",
            "Jumping now [aria:jump], then returning to idle [aria:idle].",
        ),
        ("Dance for me.", "Absolutely! Starting dance animation [aria:dance]."),
    ],
    "python_help": [
        (
            "How do I read JSON from a file in Python?",
            "Use json.load() with an open file handle in a with-statement for safe IO.",
        ),
        (
            "Why use type hints?",
            "Type hints improve readability and enable static analysis tools to catch bugs earlier.",
        ),
        (
            "How can I avoid KeyError?",
            "Use dict.get(key, default) or check key existence with 'in' before access.",
        ),
    ],
}


def write_dataset(category: str, count: int) -> Path:
    category_dir = OUT_ROOT / category
    category_dir.mkdir(parents=True, exist_ok=True)
    train_path = category_dir / "train.jsonl"

    base = SAMPLES[category]
    rows = []
    for i in range(count):
        user, assistant = base[i % len(base)]
        rows.append(
            {
                "messages": [
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": assistant},
                ]
            }
        )

    with open(train_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return train_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic autonomous datasets"
    )
    parser.add_argument(
        "--samples-per-category",
        type=int,
        default=20,
        help="Number of JSONL rows per category",
    )
    args = parser.parse_args()

    created = []
    for category in SAMPLES:
        created.append(write_dataset(category, args.samples_per_category))

    print("✅ Synthetic autonomous datasets generated:")
    for p in created:
        print(f"  - {p.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
