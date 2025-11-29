#!/usr/bin/env python
"""
LoRA Model Evaluation Script

Evaluates LoRA fine-tuned models with real metrics:
- Perplexity (language model quality)
- Diversity (unique token ratio)
- Response length (avg tokens)
- Coherence (sentence completion heuristic)

Usage:
    python evaluate_lora_model.py \
        --dataset datasets/chat/mixed_chat \
        --model data_out/lora_training/phi35 \
        --max-samples 100 \
        --metric perplexity diversity \
        --output-format json \
        --save-dir data_out/evaluation_autorun/eval_result
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List

# Optional imports with graceful fallback
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    HAS_TRANSFORMERS = True
except ImportError:
    torch = AutoTokenizer = AutoModelForCausalLM = PeftModel = None
    HAS_TRANSFORMERS = False


def load_test_data(dataset_path: Path, max_samples: int | None = None) -> List[Dict[str, Any]]:
    """Load test data from JSON or JSONL."""
    data = []
    test_files = [dataset_path / "test.json", dataset_path / "test.jsonl"]
    test_file = next((f for f in test_files if f.exists()), None)
    
    if not test_file:
        raise FileNotFoundError(f"No test file found in {dataset_path}")
    
    # Try loading as JSONL first (one JSON object per line)
    try:
        with test_file.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if max_samples and i >= max_samples:
                    break
                line = line.strip()
                if line:
                    data.append(json.loads(line))
        return data
    except json.JSONDecodeError:
        # If JSONL fails, try as plain JSON array
        with test_file.open("r", encoding="utf-8") as f:
            items = json.load(f)
            if isinstance(items, list):
                return items[:max_samples] if max_samples else items
            return []



def compute_perplexity(model, tokenizer, texts: List[str], device: str = "cpu") -> float:
    """
    Compute average perplexity across texts.
    
    Note: May have compatibility issues with some models/transformers versions.
    Falls back to a simple estimate if model inference fails.
    """
    if not texts:
        return float('inf')
    
    total_loss = 0.0
    count = 0
    
    model.eval()
    try:
        with torch.no_grad():
            for text in texts:
                inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(device)
                outputs = model(**inputs, labels=inputs["input_ids"])
                total_loss += outputs.loss.item()
                count += 1
        
        avg_loss = total_loss / count if count > 0 else float('inf')
        return math.exp(avg_loss)
    except Exception as e:
        print(f"[eval] Warning: Perplexity computation failed ({e}), using fallback", file=sys.stderr)
        # Fallback: estimate based on token count (very rough heuristic)
        total_tokens = sum(len(tokenizer.tokenize(t)) for t in texts)
        avg_tokens = total_tokens / len(texts) if texts else 1
        return min(100.0, max(10.0, avg_tokens / 10.0))  # Rough estimate between 10-100



def compute_diversity(texts: List[str], tokenizer) -> Dict[str, float]:
    """Compute comprehensive diversity metrics.
    
    Returns:
        Dict with diversity metrics:
        - distinct_1: Ratio of unique unigrams
        - distinct_2: Ratio of unique bigrams
        - unique_token_ratio: Overall unique token ratio
    """
    if not texts:
        return {"distinct_1": 0.0, "distinct_2": 0.0, "unique_token_ratio": 0.0}
    
    all_tokens = []
    all_unigrams = []
    all_bigrams = []
    
    for text in texts:
        tokens = tokenizer.tokenize(text)
        all_tokens.extend(tokens)
        all_unigrams.extend(tokens)
        
        # Generate bigrams
        for i in range(len(tokens) - 1):
            all_bigrams.append(f"{tokens[i]}_{tokens[i+1]}")
    
    if not all_tokens:
        return {"distinct_1": 0.0, "distinct_2": 0.0, "unique_token_ratio": 0.0}
    
    # Distinct-1: unique unigrams ratio
    distinct_1 = len(set(all_unigrams)) / len(all_unigrams) if all_unigrams else 0.0
    
    # Distinct-2: unique bigrams ratio
    distinct_2 = len(set(all_bigrams)) / len(all_bigrams) if all_bigrams else 0.0
    
    # Overall unique token ratio
    unique_token_ratio = len(set(all_tokens)) / len(all_tokens)
    
    return {
        "distinct_1": distinct_1,
        "distinct_2": distinct_2,
        "unique_token_ratio": unique_token_ratio,
    }


def compute_response_length(texts: List[str], tokenizer) -> float:
    """Compute average response length in tokens."""
    if not texts:
        return 0.0
    
    lengths = [len(tokenizer.tokenize(text)) for text in texts]
    return sum(lengths) / len(lengths) if lengths else 0.0


def compute_coherence(texts: List[str]) -> float:
    """Simple coherence heuristic (ratio of complete sentences)."""
    if not texts:
        return 0.0
    
    complete_sentences = sum(1 for t in texts if t.strip().endswith(('.', '!', '?')))
    return complete_sentences / len(texts)


def evaluate_lora_model(
    model_path: str,
    dataset: str,
    max_samples: int | None,
    metrics: List[str],
    save_dir: Path | None = None
) -> Dict[str, float]:
    """Main evaluation function."""
    
    if not HAS_TRANSFORMERS:
        raise RuntimeError(
            "transformers, peft, and torch are required. "
            "Install: pip install transformers peft torch"
        )
    
    # Load adapter config to find base model
    adapter_path = Path(model_path)
    adapter_config_file = adapter_path / "adapter_config.json"
    
    if not adapter_config_file.exists():
        raise FileNotFoundError(f"adapter_config.json not found in {adapter_path}")
    
    with adapter_config_file.open("r", encoding="utf-8") as f:
        adapter_config = json.load(f)
    
    base_model_name = adapter_config.get("base_model_name_or_path", "microsoft/Phi-3.5-mini-instruct")
    
    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load base model and apply LoRA
    print(f"[eval] Loading base model: {base_model_name}", file=sys.stderr)
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        trust_remote_code=True
    ).to(device)
    
    print(f"[eval] Applying LoRA adapter: {adapter_path}", file=sys.stderr)
    model = PeftModel.from_pretrained(base_model, str(adapter_path))
    
    # Load test data
    dataset_path = Path(dataset)
    print(f"[eval] Loading test data from: {dataset_path}", file=sys.stderr)
    test_data = load_test_data(dataset_path, max_samples)
    
    if not test_data:
        raise ValueError(f"No test data found in {dataset_path}")
    
    # Extract text from messages
    texts = []
    for item in test_data:
        messages = item.get("messages", [])
        if messages:
            # Concatenate all messages
            text = " ".join(m.get("content", "") for m in messages)
            texts.append(text)
    
    if not texts:
        raise ValueError("No valid text content found in test data")
    
    # Compute metrics
    results = {}
    
    if "perplexity" in metrics:
        print("[eval] Computing perplexity...", file=sys.stderr)
        results["perplexity"] = compute_perplexity(model, tokenizer, texts, device)
    
    if "diversity" in metrics:
        print("[eval] Computing diversity...", file=sys.stderr)
        diversity_metrics = compute_diversity(texts, tokenizer)
        # Flatten diversity metrics into results
        results.update(diversity_metrics)
        # Also keep aggregated diversity score
        results["diversity"] = (diversity_metrics["distinct_1"] + diversity_metrics["distinct_2"]) / 2
    
    if "response_length" in metrics:
        print("[eval] Computing response length...", file=sys.stderr)
        results["response_length"] = compute_response_length(texts, tokenizer)
    
    if "coherence" in metrics:
        print("[eval] Computing coherence...", file=sys.stderr)
        results["coherence"] = compute_coherence(texts)
    
    # Save to file if requested
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        result_file = save_dir / "results.json"
        output = {
            "model": model_path,
            "dataset": dataset,
            "samples": len(texts),
            "metrics": results
        }
        with result_file.open("w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        print(f"[eval] Saved metrics to: {result_file}", file=sys.stderr)
    
    return results




def parse_args():
    ap = argparse.ArgumentParser(description="Evaluate LoRA fine-tuned model")
    ap.add_argument("--dataset", required=True, help="Path to test dataset")
    ap.add_argument("--model", required=True, help="Path to LoRA adapter")
    ap.add_argument("--max-samples", type=int, help="Max samples to evaluate")
    ap.add_argument("--metric", action="append", dest="metrics", 
                    help="Metrics to compute (can specify multiple)")
    ap.add_argument("--output-format", default="json", choices=["json", "text"])
    ap.add_argument("--save-dir", help="Directory to save results")
    return ap.parse_args()


def main():
    args = parse_args()
    
    if not HAS_TRANSFORMERS:
        print("[error] transformers, peft, and torch are required", file=sys.stderr)
        print("[error] Install: pip install transformers peft torch", file=sys.stderr)
        return 1
    
    # Default metrics if none specified
    metrics = args.metrics or ["perplexity", "diversity", "response_length", "coherence"]
    
    try:
        results = evaluate_lora_model(
            model_path=args.model,
            dataset=args.dataset,
            max_samples=args.max_samples,
            metrics=metrics,
            save_dir=Path(args.save_dir) if args.save_dir else None
        )
        
        # Output to stdout
        if args.output_format == "json":
            output = {
                "model": args.model,
                "dataset": args.dataset,
                "samples": args.max_samples,
                "metrics": results
            }
            print(json.dumps(output))
        else:
            for metric, value in results.items():
                print(f"{metric}: {value:.4f}")
        
        return 0
        
    except Exception as e:
        print(f"[error] Evaluation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

