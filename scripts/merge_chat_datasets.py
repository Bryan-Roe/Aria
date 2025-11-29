"""Merge multiple chat dataset directories into a single combined dataset.

Input directories must each contain train.json and test.json in Phi-3 style
({"messages": [...]} newline-delimited JSON). The script deduplicates by a
hash of concatenated message text.

Usage (PowerShell):
  python .\\scripts\\merge_chat_datasets.py --out-dir datasets/chat/mixed_chat \
      --source datasets/chat/app_repo datasets/chat/chat_logs datasets/chat/dolly

Optional:
  --max-per-source 200  (limit examples drawn from each source)
  --train-ratio 0.92    (adjust train split)

Result:
  datasets/chat/mixed_chat/train.json
  datasets/chat/mixed_chat/test.json
  datasets/chat/mixed_chat/metadata.json

Why merge?
- Build a richer fine-tuning corpus that mixes internal awareness (app_repo & chat_logs)
  with broader instruction-following (public datasets) while controlling size and overfitting.
"""
from __future__ import annotations
import argparse
import json
import hashlib
import random
from pathlib import Path
from typing import List, Dict


def read_jsonl(path: Path) -> List[Dict]:
    out: List[Dict] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "messages" in obj:
                    out.append(obj)
            except Exception:
                continue
    return out


def hash_messages(msgs: List[Dict]) -> str:
    concat = "\n".join([f"{m.get('role','')}: {m.get('content','')[:500]}" for m in msgs])
    return hashlib.sha256(concat.encode("utf-8")).hexdigest()[:32]


def main():
    ap = argparse.ArgumentParser(description="Merge multiple chat datasets")
    ap.add_argument("--source", nargs="+", required=True, help="Source dataset directories")
    ap.add_argument("--out-dir", required=True, help="Output merged dataset directory")
    ap.add_argument("--max-per-source", type=int, default=None, help="Cap examples drawn from each source")
    ap.add_argument("--train-ratio", type=float, default=0.9, help="Train split ratio")
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    args = ap.parse_args()

    random.seed(args.seed)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_records: List[Dict] = []
    source_stats = {}
    for src in args.source:
        src_path = Path(src)
        train_path = src_path / "train.json"
        test_path = src_path / "test.json"
        if not train_path.exists() or not test_path.exists():
            print(f"⚠️ Skipping {src}: missing train.json/test.json")
            continue
        train_recs = read_jsonl(train_path)
        test_recs = read_jsonl(test_path)
        combined = train_recs + test_recs
        if args.max_per_source and len(combined) > args.max_per_source:
            combined = combined[: args.max_per_source]
        for rec in combined:
            h = rec.get("hash") or hash_messages(rec.get("messages", []))
            rec["hash"] = h
            rec["_source_dir"] = src_path.name
            all_records.append(rec)
        source_stats[src_path.name] = {
            "train_loaded": len(train_recs),
            "test_loaded": len(test_recs),
            "used": len(combined),
        }

    # Deduplicate by hash
    dedup = {}
    for r in all_records:
        h = r["hash"]
        if h not in dedup:
            dedup[h] = r
    merged = list(dedup.values())

    random.shuffle(merged)
    n_train = int(len(merged) * args.train_ratio)
    train = merged[:n_train]
    test = merged[n_train:] or merged[:1]

    def write_jsonl(path: Path, recs: List[Dict]):
        with path.open("w", encoding="utf-8") as f:
            for r in recs:
                out = {"messages": r["messages"], "hash": r["hash"], "source": r.get("_source_dir")}
                f.write(json.dumps(out, ensure_ascii=False) + "\n")

    write_jsonl(out_dir / "train.json", train)
    write_jsonl(out_dir / "test.json", test)

    meta = {
        "sources": args.source,
        "source_stats": source_stats,
        "total_unique_records": len(merged),
        "train_records": len(train),
        "test_records": len(test),
        "train_ratio": args.train_ratio,
        "seed": args.seed,
    }
    with (out_dir / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(json.dumps(meta, indent=2))
    print(f"Merged dataset written to {out_dir}")


if __name__ == "__main__":
    main()
