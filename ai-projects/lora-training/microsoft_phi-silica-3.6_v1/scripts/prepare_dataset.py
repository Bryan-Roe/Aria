import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# Minimal, robust dataset converter and splitter for chat-style SFT
# Input formats supported:
# - JSONL where each line is an object with a "messages" array
# - CSV with columns: prompt,response OR input,output
# Output:
# - JSONL files named train.json and test.json containing one JSON object per line
#   with the schema: {"messages": [{"role": "user"|"assistant", "content": "..."}, ...]}

Chat = List[Dict[str, Any]]


def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def read_csv(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Accept common column pairs
        col_pairs = [
            ("prompt", "response"),
            ("input", "output"),
            ("question", "answer"),
            ("user", "assistant"),
        ]
        chosen: Tuple[str, str] | None = None
        cols = [c.lower() for c in reader.fieldnames or []]
        for a, b in col_pairs:
            if a in cols and b in cols:
                chosen = (a, b)
                break
        if chosen is None:
            raise ValueError(
                f"CSV must have one of column pairs: {col_pairs}; got: {reader.fieldnames}"
            )
        a, b = chosen
        for row in reader:
            prompt = row.get(a) or ""
            resp = row.get(b) or ""
            yield {
                "messages": [
                    {"role": "user", "content": str(prompt).strip()},
                    {"role": "assistant", "content": str(resp).strip()},
                ]
            }


def normalize_record(obj: Dict[str, Any]) -> Dict[str, Any]:
    # If already has messages, validate minimal structure
    if "messages" in obj and isinstance(obj["messages"], list):
        msgs = []
        for m in obj["messages"]:
            role = (m.get("role") or "").strip().lower()
            content = (m.get("content") or "").strip()
            if not role or not content:
                # Skip malformed entries
                continue
            if role not in ("user", "assistant", "system"):
                # Map unknown roles to user
                role = "user"
            msgs.append({"role": role, "content": content})
        if len(msgs) >= 2:
            return {"messages": msgs}
        else:
            raise ValueError("Message list too short after normalization")
    # Otherwise, try simple prompt/completion keys
    for a, b in [("prompt", "completion"), ("input", "output"), ("question", "answer")]:
        if a in obj and b in obj:
            return {
                "messages": [
                    {"role": "user", "content": str(obj[a])},
                    {"role": "assistant", "content": str(obj[b])},
                ]
            }
    raise ValueError(
        "Unsupported record format; expected messages[] or prompt/completion-style fields"
    )


def discover_inputs(input_path: Path) -> List[Path]:
    if input_path.is_dir():
        candidates: List[Path] = []
        for pattern in ("*.jsonl", "*.json", "*.csv"):
            candidates.extend(sorted(input_path.rglob(pattern)))
        if not candidates:
            raise FileNotFoundError(f"No dataset files found under {input_path}")
        return candidates
    else:
        return [input_path]


def load_records(paths: List[Path]) -> Iterable[Dict[str, Any]]:
    for p in paths:
        if p.suffix.lower() == ".csv":
            for rec in read_csv(p):
                yield normalize_record(rec)
        elif p.suffix.lower() in (".jsonl", ".json"):
            for rec in read_jsonl(p):
                yield normalize_record(rec)
        else:
            raise ValueError(f"Unsupported file type: {p}")


def stream_split_and_write(
    records: Iterable[Dict[str, Any]],
    train_path: Path,
    test_path: Path,
    train_ratio: float,
    seed: int,
) -> Tuple[int, int]:
    rnd = random.Random(seed)
    train_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)
    n_train = 0
    n_test = 0
    with (
        train_path.open("w", encoding="utf-8") as ftrain,
        test_path.open("w", encoding="utf-8") as ftest,
    ):
        for obj in records:
            if rnd.random() < train_ratio:
                ftrain.write(json.dumps(obj, ensure_ascii=False) + "\n")
                n_train += 1
            else:
                ftest.write(json.dumps(obj, ensure_ascii=False) + "\n")
                n_test += 1
    # Ensure at least one test sample by moving last train to test if needed
    if n_test == 0 and n_train > 0:
        # Re-open and move last line
        lines: List[str] = []
        with train_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        if lines:
            with test_path.open("a", encoding="utf-8") as ftest:
                ftest.write(lines[-1])
            with train_path.open("w", encoding="utf-8") as ftrain:
                ftrain.writelines(lines[:-1])
            n_train -= 1
            n_test += 1
    return n_train, n_test


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for obj in records:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Prepare chat dataset for SFT (JSONL)")
    ap.add_argument(
        "--input", required=True, help="Path to source file or folder (jsonl/json/csv)"
    )
    ap.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[1] / "data"),
        help="Output folder for train/test JSONL",
    )
    ap.add_argument("--train-file", default="train.json", help="Output train file name")
    ap.add_argument("--test-file", default="test.json", help="Output test file name")
    ap.add_argument(
        "--train-ratio", type=float, default=0.98, help="Train split ratio (0-1)"
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.output_dir)
    train_path = out_dir / args.train_file
    test_path = out_dir / args.test_file

    files = discover_inputs(input_path)
    # Stream through input to avoid memory blow-up on huge datasets
    n_train, n_test = stream_split_and_write(
        load_records(files), train_path, test_path, args.train_ratio, args.seed
    )
    if n_train + n_test == 0:
        raise RuntimeError("No valid records parsed from input")
    print(f"Wrote {n_train} train and {n_test} test examples to {out_dir}")


if __name__ == "__main__":
    main()
