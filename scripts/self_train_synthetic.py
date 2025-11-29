#!/usr/bin/env python
"""Self-Training with Synthetic Data Generation

Iterative self-improvement loop:
1. Load base or checkpoint model
2. Generate synthetic responses for prompts
3. Filter high-quality responses (perplexity, coherence, length)
4. Train on filtered synthetic data
5. Repeat for N iterations

Usage:
  python .\\scripts\\self_train_synthetic.py --model microsoft/Phi-3.5-mini-instruct --iterations 3 --samples-per-iter 100
  python .\\scripts\\self_train_synthetic.py --base-adapter data_out/lora_training/phi35_lr_low --iterations 2
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import List, Dict, Any

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    from datasets import Dataset
except ImportError:
    print("Missing dependencies. Install: pip install torch transformers datasets accelerate peft")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTOTRAIN_SCRIPT = REPO_ROOT / "scripts" / "autotrain.py"

# Seed prompts for synthetic data generation (diverse domains)
SEED_PROMPTS = [
    "Explain the concept of",
    "Write a tutorial on",
    "Describe the process of",
    "What are the benefits of",
    "Compare and contrast",
    "Provide step-by-step instructions for",
    "Summarize the main ideas in",
    "Analyze the following problem:",
    "Create a plan to",
    "Debug this code:",
]

TOPICS = [
    "machine learning", "quantum computing", "web development", "data science",
    "cloud architecture", "cybersecurity", "database design", "API development",
    "containerization", "CI/CD pipelines", "microservices", "GraphQL",
    "natural language processing", "computer vision", "reinforcement learning",
    "distributed systems", "blockchain", "edge computing", "IoT", "5G networks",
]


def generate_prompts(n_prompts: int, seed: int = 42) -> List[str]:
    """Generate diverse prompts by combining templates with topics."""
    random.seed(seed)
    prompts = []
    for _ in range(n_prompts):
        template = random.choice(SEED_PROMPTS)
        topic = random.choice(TOPICS)
        prompts.append(f"{template} {topic}")
    return prompts


def load_model_and_tokenizer(model_id_or_path: str, adapter_path: Path | None = None):
    """Load model (with optional LoRA adapter) and tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(model_id_or_path, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id_or_path,
        torch_dtype=dtype,
        device_map="cuda:0" if device == "cuda" and torch.cuda.device_count() == 1 else "auto",
    )
    
    if adapter_path and adapter_path.exists():
        from peft import PeftModel
        print(f"[self_train] Loading LoRA adapter from {adapter_path}")
        model = PeftModel.from_pretrained(model, str(adapter_path))
    
    return model, tokenizer, device


def generate_responses(
    model,
    tokenizer,
    prompts: List[str],
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> List[Dict[str, Any]]:
    """Generate responses for given prompts."""
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=True,
    )
    
    results = []
    for prompt in prompts:
        try:
            messages = [{"role": "user", "content": prompt}]
            output = pipe(messages, return_full_text=False)
            response = output[0]["generated_text"] if output else ""
            results.append({
                "messages": messages + [{"role": "assistant", "content": response}],
                "prompt": prompt,
                "response": response,
            })
        except Exception as e:
            print(f"[self_train] Generation error for prompt '{prompt[:50]}...': {e}")
            continue
    
    return results


def filter_quality_responses(
    responses: List[Dict[str, Any]],
    min_length: int = 50,
    max_length: int = 2000,
    perplexity_threshold: float | None = None,
) -> List[Dict[str, Any]]:
    """Filter responses by length and optional perplexity."""
    filtered = []
    for resp in responses:
        content = resp.get("response", "")
        if len(content) < min_length or len(content) > max_length:
            continue
        # TODO: Add perplexity filtering if threshold provided
        filtered.append(resp)
    
    print(f"[self_train] Filtered {len(filtered)}/{len(responses)} responses (length {min_length}-{max_length})")
    return filtered


def save_synthetic_dataset(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save synthetic data in JSONL format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    print(f"[self_train] Saved {len(data)} samples to {output_path}")


def run_training_iteration(
    dataset_path: Path,
    model_id: str,
    output_dir: Path,
    epochs: int = 1,
    learning_rate: float = 2e-4,
    max_samples: int | None = None,
) -> bool:
    """Run one training iteration using autotrain script."""
    import subprocess
    
    cmd = [
        sys.executable,
        str(AUTOTRAIN_SCRIPT),
        "--job", "self_train_iter",  # Placeholder; could define dynamic job
    ]
    
    # Alternative: call train_lora.py directly
    train_script = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "scripts" / "train_lora.py"
    config_path = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "lora" / "lora.yaml"
    
    cmd = [
        sys.executable,
        str(train_script),
        "--config", str(config_path),
        "--dataset", str(dataset_path.parent),
        "--hf-model-id", model_id,
        "--save-dir", str(output_dir),
        "--epochs", str(epochs),
        "--learning-rate", str(learning_rate),
    ]
    
    if max_samples:
        cmd.extend(["--max-train-samples", str(max_samples), "--max-eval-samples", str(max(16, max_samples // 4))])
    
    print(f"[self_train] Running training: {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=False, text=True)
    
    return proc.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Self-training with synthetic data generation")
    ap.add_argument("--model", default="microsoft/Phi-3.5-mini-instruct", help="Base HF model ID")
    ap.add_argument("--base-adapter", default=None, help="Path to initial LoRA adapter (optional)")
    ap.add_argument("--iterations", type=int, default=3, help="Number of self-training iterations")
    ap.add_argument("--samples-per-iter", type=int, default=100, help="Synthetic samples to generate per iteration")
    ap.add_argument("--output-dir", default="data_out/self_training", help="Base output directory")
    ap.add_argument("--epochs-per-iter", type=int, default=1, help="Training epochs per iteration")
    ap.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    ap.add_argument("--temperature", type=float, default=0.7, help="Generation temperature")
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    args = ap.parse_args()
    
    output_base = Path(args.output_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    
    current_model_id = args.model
    current_adapter_path = Path(args.base_adapter) if args.base_adapter else None
    
    for iteration in range(1, args.iterations + 1):
        print(f"\n{'='*60}")
        print(f"[self_train] Iteration {iteration}/{args.iterations}")
        print(f"{'='*60}")
        
        # Load current model
        model, tokenizer, device = load_model_and_tokenizer(current_model_id, current_adapter_path)
        
        # Generate prompts
        prompts = generate_prompts(args.samples_per_iter, seed=args.seed + iteration)
        print(f"[self_train] Generated {len(prompts)} prompts")
        
        # Generate responses
        print(f"[self_train] Generating responses...")
        responses = generate_responses(model, tokenizer, prompts, temperature=args.temperature)
        
        # Filter quality
        filtered = filter_quality_responses(responses, min_length=50, max_length=1500)
        
        if len(filtered) < 10:
            print(f"[self_train] Too few quality samples ({len(filtered)}). Stopping.")
            break
        
        # Save synthetic dataset
        iter_dataset_dir = output_base / f"iter_{iteration}" / "synthetic_data"
        iter_dataset_dir.mkdir(parents=True, exist_ok=True)
        train_path = iter_dataset_dir / "train.jsonl"
        test_path = iter_dataset_dir / "test.jsonl"
        
        # Split 90/10 train/test
        split_idx = int(len(filtered) * 0.9)
        save_synthetic_dataset(filtered[:split_idx], train_path)
        save_synthetic_dataset(filtered[split_idx:], test_path)
        
        # Train on synthetic data
        iter_output_dir = output_base / f"iter_{iteration}" / "adapter"
        success = run_training_iteration(
            dataset_path=train_path,
            model_id=current_model_id,
            output_dir=iter_output_dir,
            epochs=args.epochs_per_iter,
            learning_rate=args.learning_rate,
            max_samples=len(filtered[:split_idx]),
        )
        
        if not success:
            print(f"[self_train] Training failed at iteration {iteration}. Stopping.")
            break
        
        # Update for next iteration
        adapter_checkpoint = iter_output_dir / "lora_adapter"
        if adapter_checkpoint.exists():
            current_adapter_path = adapter_checkpoint
            print(f"[self_train] Updated adapter checkpoint: {current_adapter_path}")
        
        # Free memory
        del model, tokenizer
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    print(f"\n[self_train] Self-training complete. Final adapter: {current_adapter_path}")
    print(f"[self_train] Artifacts in: {output_base}")


if __name__ == "__main__":
    main()
