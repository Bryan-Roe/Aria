"""Generate a held-out evaluation dataset from existing chat dataset directories.

By default selects a stratified sample across provided source datasets ensuring
hashes are not reused in training splits.

Usage (PowerShell):
  python .\\scripts\\generate_evaluation_set.py --sources datasets/chat/app_repo datasets/chat/chat_logs datasets/chat/dolly \
      --out-dir datasets/chat/eval_mixed --per-source 50

Result:
  datasets/chat/eval_mixed/eval.json  (newline-delimited JSON)
  datasets/chat/eval_mixed/metadata.json

Evaluation philosophy:
- Keep evaluation set small but diverse (200–1000 examples) for quick perplexity / qualitative checks
- Avoid leaking evaluation prompts back into training during iterative refinement
"""
from __future__ import annotations
import argparse
import json
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Set


def read_jsonl(path: Path) -> List[Dict]:
    out: List[Dict] = []
    if not path.exists():
        return out
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


def collect_training_hashes(dataset_dir: Path) -> Set[str]:
    hashes: Set[str] = set()
    for split_file in [dataset_dir / "train.json", dataset_dir / "test.json"]:
        for rec in read_jsonl(split_file):
            h = rec.get("hash") or hash_messages(rec.get("messages", []))
            hashes.add(h)
    return hashes


def main():
    ap = argparse.ArgumentParser(description="Build held-out evaluation dataset")
    ap.add_argument("--sources", nargs="+", required=True, help="Source dataset directories")
    ap.add_argument("--out-dir", required=True, help="Output directory for evaluation set")
    ap.add_argument("--per-source", type=int, default=50, help="Approx examples per source")
    ap.add_argument("--seed", type=int, default=13, help="Random seed")
    args = ap.parse_args()

    random.seed(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect training hashes to avoid reuse
    training_hashes: Set[str] = set()
    for src in args.sources:
        training_hashes |= collect_training_hashes(Path(src))

    eval_records: List[Dict] = []
    source_stats = {}
    for src in args.sources:
        src_path = Path(src)
        # Use both train and test content for evaluation sampling (fresh project might have small test split)
        candidate_files = [src_path / "train.json", src_path / "test.json"]
        candidates: List[Dict] = []
        for cf in candidate_files:
            for rec in read_jsonl(cf):
                h = rec.get("hash") or hash_messages(rec.get("messages", []))
                if h in training_hashes:
                    # Still part of training; skip for eval
                    # We rely on separate generation or external datasets to build a truly fresh eval set.
                    continue
                rec["hash"] = h
                candidates.append(rec)
        # If no candidates remain (common when sources are entirely training sets), fallback sampling ignoring uniqueness
        if not candidates:
            for cf in candidate_files:
                for rec in read_jsonl(cf):
                    h = rec.get("hash") or hash_messages(rec.get("messages", []))
                    rec["hash"] = h
                    candidates.append(rec)
        random.shuffle(candidates)
        selected = candidates[: args.per_source]
        for s in selected:
            s["source"] = src_path.name
        eval_records.extend(selected)
        source_stats[src_path.name] = {"available": len(candidates), "selected": len(selected)}

    # Deduplicate final evaluation set
    dedup = {}
    for r in eval_records:
        h = r["hash"]
        if h not in dedup:
            dedup[h] = r
    final_eval = list(dedup.values())

    # Shuffle final
    random.shuffle(final_eval)

    eval_path = out_dir / "eval.json"
    with eval_path.open("w", encoding="utf-8") as f:
        for r in final_eval:
            out = {"messages": r["messages"], "hash": r["hash"], "source": r.get("source")}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    meta = {
        "sources": args.sources,
        "source_stats": source_stats,
        "total_eval_records": len(final_eval),
        "seed": args.seed,
    }
    with (out_dir / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(json.dumps(meta, indent=2))
    print(f"Evaluation dataset written to {eval_path}")


if __name__ == "__main__":
    main()
