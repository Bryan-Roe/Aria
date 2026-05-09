"""
Model Evaluation Script

Delegates to evaluate_lora_model.py when available, otherwise provides a
lightweight fallback that can validate dataset format, compute simple text
metrics (BLEU, exact-match), and report structured JSON results.

Usage:
  python scripts/evaluate_model.py --model path/to/model --dataset path/to/data.jsonl
  python scripts/evaluate_model.py --model path/to/model --dataset path/to/data.jsonl --output results.json
  python scripts/evaluate_model.py --model path/to/model --dataset path/to/data.jsonl --metrics accuracy bleu
"""

import sys
from pathlib import Path

# Import the real evaluation logic from evaluate_lora_model
sys.path.insert(0, str(Path(__file__).parent))

try:
    from evaluate_lora_model import main as lora_main

    def main():
        """Delegate to evaluate_lora_model for actual implementation."""
        print("Note: Delegating to evaluate_lora_model.py for evaluation")
        print("For full control, use evaluate_lora_model.py directly\n")
        lora_main()

except ImportError:
    # Fallback with lightweight metrics —
    # no transformers/torch required
    import argparse
    import json
    from collections import Counter
    from datetime import datetime, timezone

    def _load_dataset(path: str) -> list[dict]:
        """Load JSONL or JSON dataset."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        text = p.read_text(encoding="utf-8").strip()
        if text.startswith("["):
            return json.loads(text)

        # JSONL
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    def _extract_pairs(records: list[dict]) -> list[tuple[str, str]]:
        """Extract (reference, candidate) pairs from chat-formatted records."""
        pairs: list[tuple[str, str]] = []
        for rec in records:
            msgs = rec.get("messages", [])
            for i, msg in enumerate(msgs):
                if msg.get("role") == "assistant":
                    # Use previous user message as input context
                    ref = msg.get("content", "")
                    pairs.append((ref, ""))  # candidate empty until model runs
        return pairs

    def _bleu_score(reference: str, candidate: str) -> float:
        """Simplified unigram BLEU (no external deps)."""
        ref_tokens = reference.lower().split()
        cand_tokens = candidate.lower().split()
        if not ref_tokens or not cand_tokens:
            return 0.0
        ref_counts = Counter(ref_tokens)
        match = sum(min(ref_counts[t], 1) for t in cand_tokens if t in ref_counts)
        precision = match / len(cand_tokens) if cand_tokens else 0.0
        brevity = min(1.0, len(cand_tokens) / len(ref_tokens)) if ref_tokens else 0.0
        return precision * brevity

    def evaluate(model_path: str, dataset_path: str, metrics: list[str]) -> dict:
        """Lightweight evaluation: validate dataset + compute format metrics."""
        results: dict = {}

        # Validate model path
        model_p = Path(model_path)
        results["model_exists"] = model_p.exists()
        results["model_path"] = str(model_p)

        if model_p.is_dir():
            has_config = (model_p / "adapter_config.json").exists()
            has_weights = (model_p / "adapter_model.safetensors").exists() or (
                model_p / "adapter_model.bin"
            ).exists()
            results["adapter_valid"] = has_config and has_weights
        else:
            results["adapter_valid"] = False

        # Load and validate dataset
        try:
            records = _load_dataset(dataset_path)
            results["dataset_records"] = len(records)
            results["dataset_valid"] = True
        except Exception as exc:
            results["dataset_records"] = 0
            results["dataset_valid"] = False
            results["dataset_error"] = str(exc)
            # Return early — can't compute actual metrics
            for m in metrics:
                results[m] = 0.0
            results["note"] = "Fallback evaluation — dataset load failed"
            return results

        # Validate chat format
        valid_format = 0
        for rec in records:
            msgs = rec.get("messages", [])
            if isinstance(msgs, list) and len(msgs) >= 2:
                roles = {m.get("role") for m in msgs}
                if "user" in roles and "assistant" in roles:
                    valid_format += 1
        results["valid_chat_format"] = valid_format
        results["format_rate"] = round(valid_format / max(len(records), 1), 4)

        # Compute requested metrics (stub values since we can't run the model)
        for m in metrics:
            if m == "format_rate":
                results[m] = results["format_rate"]
            elif m == "dataset_size":
                results[m] = len(records)
            else:
                # Mark as needing real inference
                results[m] = None

        results["note"] = (
            "Fallback evaluation — install transformers+torch for real metrics. "
            "Dataset format and adapter structure validated."
        )
        results["timestamp"] = datetime.now(timezone.utc).isoformat()
        return results

    def main():
        ap = argparse.ArgumentParser(description="Evaluate a trained model.")
        ap.add_argument(
            "--model", required=True, help="Path to trained model or adapter"
        )
        ap.add_argument(
            "--dataset", required=True, help="Path to evaluation dataset (JSONL/JSON)"
        )
        ap.add_argument(
            "--metrics",
            nargs="+",
            default=["accuracy", "format_rate"],
            help="Metrics to compute (accuracy, bleu, format_rate, dataset_size)",
        )
        ap.add_argument("--output", help="Path to write results JSON")
        args = ap.parse_args()

        results = evaluate(args.model, args.dataset, args.metrics)
        print(json.dumps(results, indent=2))

        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(results, indent=2), encoding="utf-8")
            print(f"\n📋 Results written to {args.output}")


if __name__ == "__main__":
    main()
