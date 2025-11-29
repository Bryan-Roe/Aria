"""Generate synthetic chat fine-tuning dataset from the current repository.

Creates a dataset suitable for Phi-3.6 LoRA training (`train_lora.py`).
Output format:
  datasets/chat/app_repo/train.json  (newline-delimited JSON objects)
  datasets/chat/app_repo/test.json   (newline-delimited JSON objects)
Each line: {"messages": [ {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."} ], ...metadata }

Design principles:
- Purely synthetic Q/A derived from code & docs (no external IP).
- Avoid leaking secrets: skips .env, config with keys, binary files.
- Chunk long files to keep each example < ~1500 chars before tokenization.
- Provide diverse prompt templates (summaries, listing functions/classes, usage guidance).
- Deterministic with --seed for reproducibility.

Usage (PowerShell):
  python .\\scripts\\generate_repo_training_dataset.py --max-records 300

Then train (CPU-friendly smoke test):
  cd AI\\microsoft_phi-silica-3.6_v1
  python .\\scripts\\train_lora.py --dataset ..\\..\\datasets\\chat\\app_repo --dry-run
  python .\\scripts\\train_lora.py --dataset ..\\..\\datasets\\chat\\app_repo --max-train-samples 64 --max-eval-samples 16

"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

TEXT_EXTS = {".py", ".md", ".ps1", ".txt", ".yaml", ".yml", ".json", ".js", ".ts", ".html", ".css"}
EXCLUDE_DIRS = {"venv", "__pycache__", "node_modules", "results", "outputs", "dist", "build", "lora_adapter", "__blobstorage__", "mount"}
EXCLUDE_FILES = {"local.settings.json"}  # contains connection strings (use dev storage only)
MAX_CHUNK_CHARS = 1500
DEFAULT_OUTPUT = Path("datasets/chat/app_repo")

FUNC_OR_CLASS_RE = re.compile(r"^(?:def|class)\s+(\w+)\s*", re.MULTILINE)
ENV_VAR_RE = re.compile(r"(KEY|SECRET|TOKEN|PASSWORD|API|ENDPOINT)", re.IGNORECASE)

@dataclass
class Chunk:
    rel_path: str
    content: str
    file_lang: str


def iter_files(root: Path) -> Iterable[Path]:
    """Yield candidate text files using os.walk to allow directory pruning before stat/scandir.

    This avoids Windows WinError 1920 on inaccessible symlink-like entries (e.g., venv/lib64).
    """
    for dirpath, dirnames, filenames in os.walk(root):
        # Normalize path parts for exclusion
        path_obj = Path(dirpath)
        parts_lower = {p.lower() for p in path_obj.parts}
        # Prune directories in-place to prevent descent
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and d.lower() != "lib64"]
        if any(ex.lower() in parts_lower for ex in EXCLUDE_DIRS):
            continue
        for fname in filenames:
            if fname in EXCLUDE_FILES:
                continue
            suffix = Path(fname).suffix.lower()
            if suffix in TEXT_EXTS:
                yield path_obj / fname


def load_text(path: Path) -> str | None:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    # Skip if appears to contain secrets (heuristic) – we don't want to fine-tune on them.
    if ENV_VAR_RE.search(raw) and path.suffix.lower() in {".json", ".yaml", ".yml"}:
        return None
    # Limit extremely large files – we will chunk anyway, but if > 200k chars likely vendor/binary text.
    if len(raw) > 200_000:
        return None
    return raw


def chunk_text(rel_path: str, text: str) -> List[Chunk]:
    # Split on double newlines to respect logical blocks
    blocks = re.split(r"\n{2,}", text)
    chunks: List[Chunk] = []
    buf = []
    total = 0
    for b in blocks:
        b_stripped = b.strip()
        if not b_stripped:
            continue
        if sum(len(x) for x in buf) + len(b_stripped) + 1 > MAX_CHUNK_CHARS and buf:
            combined = "\n\n".join(buf).strip()
            if combined:
                chunks.append(Chunk(rel_path=rel_path, content=combined, file_lang=Path(rel_path).suffix.lower().lstrip(".")))
            buf = [b_stripped]
        else:
            buf.append(b_stripped)
        total += len(b_stripped)
    if buf:
        combined = "\n\n".join(buf).strip()
        if combined:
            chunks.append(Chunk(rel_path=rel_path, content=combined, file_lang=Path(rel_path).suffix.lower().lstrip(".")))
    return chunks


def summarize_chunk(chunk: Chunk) -> str:
    lines = chunk.content.splitlines()
    first_lines = [l for l in lines[:20] if l.strip()]
    funcs = FUNC_OR_CLASS_RE.findall(chunk.content) if chunk.file_lang == "py" else []
    summary_parts = []
    summary_parts.append(f"File: {chunk.rel_path}\nLanguage: {chunk.file_lang}")
    if funcs:
        summary_parts.append("Key symbols: " + ", ".join(funcs[:12]))
    # Heuristic responsibilities: look for keywords
    keywords = []
    for kw in ["quantum", "dataset", "train", "chat", "azure", "function", "api", "config", "model", "web", "cli", "script"]:
        if kw in chunk.content.lower():
            keywords.append(kw)
    if keywords:
        summary_parts.append("Detected themes: " + ", ".join(sorted(set(keywords))))
    summary_parts.append("Brief excerpt:\n" + "\n".join(first_lines[:10]))
    summary_parts.append("Purpose (synthetic): This chunk represents part of the repository used for building multi-project AI (quantum, chat, fine-tuning). It includes code or documentation that supports those features.")
    return "\n\n".join(summary_parts)


def list_functions(chunk: Chunk) -> str:
    funcs = FUNC_OR_CLASS_RE.findall(chunk.content)
    if not funcs:
        return "No top-level Python functions or classes detected in this chunk."
    out = [f"{name}: Synthetic summary – handles logic related to {name.lower()} in context of the app." for name in funcs[:25]]
    return "\n".join(out)


def usage_guidance(chunk: Chunk) -> str:
    guidance = [
        "When modifying this file chunk, maintain existing abstractions and configuration-driven patterns.",
        "Add new features by extending functions rather than rewriting core logic.",
        "Prefer YAML/JSON config over hardcoding values.",
        "Ensure any Azure or Quantum integration code is tested locally before incurring cloud costs.",
    ]
    if chunk.file_lang == "py":
        guidance.append("Run unit tests or dry-run training scripts after changes to validate integrity.")
    return "\n".join(guidance)

PROMPT_TEMPLATES = {
    "summary": lambda c: (f"Summarize the following repository chunk: {c.rel_path}. Provide purpose and key elements.", summarize_chunk(c)),
    "functions": lambda c: (f"List important functions/classes in {c.rel_path} with one-line purpose each.", list_functions(c)),
    "guidance": lambda c: (f"How should a developer safely extend {c.rel_path}?", usage_guidance(c)),
}


def build_records(chunks: List[Chunk], max_records: int, seed: int) -> List[dict]:
    random.seed(seed)
    records: List[dict] = []
    for chunk in chunks:
        # Randomize template order per chunk
        keys = list(PROMPT_TEMPLATES.keys())
        random.shuffle(keys)
        for k in keys:
            user_prompt, assistant_answer = PROMPT_TEMPLATES[k](chunk)
            h = hashlib.sha256((chunk.rel_path + k + assistant_answer[:200]).encode("utf-8")).hexdigest()[:16]
            rec = {
                "messages": [
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": assistant_answer},
                ],
                "source_path": chunk.rel_path,
                "template": k,
                "hash": h,
            }
            records.append(rec)
            if len(records) >= max_records:
                break
        if len(records) >= max_records:
            break
    return records


def write_jsonl(path: Path, records: List[dict]):
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Generate synthetic repo Q/A chat dataset")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="Repository root to scan")
    ap.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Output dataset directory")
    ap.add_argument("--max-records", type=int, default=500, help="Maximum total records (train+test)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    ap.add_argument("--train-ratio", type=float, default=0.9, help="Train split ratio")
    ap.add_argument("--min-chars", type=int, default=50, help="Minimum chunk characters to include")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    all_chunks: List[Chunk] = []
    for f in iter_files(root):
        rel = str(f.relative_to(root))
        text = load_text(f)
        if text is None:
            continue
        chunks = chunk_text(rel, text)
        for ch in chunks:
            if len(ch.content) >= args.min_chars:
                all_chunks.append(ch)
    # Deterministic order
    all_chunks.sort(key=lambda c: c.rel_path)

    records = build_records(all_chunks, max_records=args.max_records, seed=args.seed)

    # Train/test split
    random.seed(args.seed)
    random.shuffle(records)
    n_train = int(len(records) * args.train_ratio)
    train_recs = records[:n_train]
    test_recs = records[n_train:] or records[: max(1, len(records)//10) ]

    write_jsonl(out_dir / "train.json", train_recs)
    write_jsonl(out_dir / "test.json", test_recs)

    meta = {
        "total_records": len(records),
        "train_records": len(train_recs),
        "test_records": len(test_recs),
        "generation_seed": args.seed,
        "source_root": str(root),
        "excluded_dirs": sorted(EXCLUDE_DIRS),
        "extensions": sorted(TEXT_EXTS),
    }
    with (out_dir / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(json.dumps(meta, indent=2))
    print(f"Dataset generated at: {out_dir}")


if __name__ == "__main__":
    main()
