"""Extract chat conversation logs from ai-projects/chat-cli/logs into Phi-3 style dataset.

Each log file is JSONL with entries: {"role": "user|assistant", "content": "...", "timestamp": "..."}
We transform these into training records with a messages list.

Strategy:
- For each assistant reply, pair it with the most recent user message (basic turn pair dataset)
- Additionally build rolling window examples (up to --context-window messages) when available
- Deduplicate by hash of concatenated message contents
- Provide fallback synthetic record if no logs are found (to keep structure testable)

Outputs:
  datasets/chat/chat_logs/train.json
  datasets/chat/chat_logs/test.json
  datasets/chat/chat_logs/metadata.json

Usage (PowerShell):
  python .\\scripts\\extract_chat_logs_dataset.py --max-records 500
  python AI\\microsoft_phi-silica-3.6_v1\\scripts\\train_lora.py --dataset .\\datasets\\chat\\chat_logs --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Dict, List

LOGS_DIR = Path("ai-projects/chat-cli/logs")
OUTPUT_DIR = Path("datasets/chat/chat_logs")


def iter_logs() -> List[Path]:
    if not LOGS_DIR.exists():
        return []
    return sorted([p for p in LOGS_DIR.glob("*.jsonl") if p.is_file()])


def read_jsonl(path: Path) -> List[Dict]:
    records: List[Dict] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "role" in obj and "content" in obj:
                    records.append(obj)
            except Exception:
                continue
    return records


def build_examples(messages: List[Dict], context_window: int) -> List[Dict]:
    # Simple user->assistant pairs - build list directly
    pairs = []
    last_user = None
    for m in messages:
        if m.get("role") == "user":
            last_user = m
        elif m.get("role") == "assistant" and last_user:
            pairs.append({"messages": [last_user, m]})

    # Rolling windows - use list comprehension for better performance
    windows = []
    if context_window > 2:
        for i in range(len(messages)):
            if messages[i].get("role") == "assistant":
                start = max(0, i - context_window + 1)
                window = messages[start : i + 1]
                # Must contain at least one user+assistant
                if any(x.get("role") == "user" for x in window) and any(
                    x.get("role") == "assistant" for x in window
                ):
                    windows.append({"messages": window})

    # Combine lists efficiently with extend
    pairs.extend(windows)
    return pairs


def hash_example(example: Dict) -> str:
    concat = "\n".join(
        [
            f"{m.get('role', '')}: {m.get('content', '')[:400]}"
            for m in example.get("messages", [])
        ]
    )
    return hashlib.sha256(concat.encode("utf-8")).hexdigest()[:24]


def main():
    ap = argparse.ArgumentParser(description="Extract chat logs into training dataset")
    ap.add_argument(
        "--max-records", type=int, default=1000, help="Maximum examples to output"
    )
    ap.add_argument("--train-ratio", type=float, default=0.9, help="Train split ratio")
    ap.add_argument(
        "--context-window",
        type=int,
        default=6,
        help="Max messages in rolling window examples",
    )
    ap.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = ap.parse_args()

    random.seed(args.seed)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    log_files = iter_logs()
    all_examples: List[Dict] = []
    for lf in log_files:
        msgs = read_jsonl(lf)
        if not msgs:
            continue
        exs = build_examples(msgs, args.context_window)
        # Add metadata and hash in batch using list comprehension
        enriched_exs = [
            {**e, "source_file": lf.name, "hash": hash_example(e)} for e in exs
        ]
        all_examples.extend(enriched_exs)

    # Deduplicate by hash - keeps first occurrence (Python 3.7+ dict is ordered)
    # Explicit iteration ensures first occurrence is preserved
    uniq = {}
    for e in all_examples:
        h = e["hash"]
        if h not in uniq:
            uniq[h] = e
    examples = list(uniq.values())

    if not examples:
        # Fallback synthetic example
        fallback = {
            "messages": [
                {
                    "role": "user",
                    "content": "How does the local chat provider respond to a greeting?",
                },
                {
                    "role": "assistant",
                    "content": "The local provider generates a concise heuristic reply; this synthetic example exists because no real logs were found.",
                },
            ],
            "hash": hash_example(
                {
                    "messages": [
                        {"role": "user", "content": "fallback"},
                        {"role": "assistant", "content": "fallback"},
                    ]
                }
            ),
            "source_file": "<fallback>",
        }
        examples = [fallback]

    # Limit
    if len(examples) > args.max_records:
        examples = examples[: args.max_records]

    random.shuffle(examples)
    n_train = int(len(examples) * args.train_ratio)
    # Ensure at least one training example if any examples exist
    if n_train == 0 and examples:
        n_train = 1
    train = examples[:n_train]
    test = examples[n_train:] or examples[:1]

    def write(path: Path, recs: List[Dict]):
        with path.open("w", encoding="utf-8") as f:
            for r in recs:
                out = {
                    "messages": r["messages"],
                    "hash": r["hash"],
                    "source_file": r.get("source_file"),
                }
                f.write(json.dumps(out, ensure_ascii=False) + "\n")

    write(OUTPUT_DIR / "train.json", train)
    write(OUTPUT_DIR / "test.json", test)
    meta = {
        "log_files": [lf.name for lf in log_files],
        "total_examples": len(examples),
        "train_examples": len(train),
        "test_examples": len(test),
        "seed": args.seed,
        "context_window": args.context_window,
    }
    with (OUTPUT_DIR / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(json.dumps(meta, indent=2))
    print(f"Dataset written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
