#!/usr/bin/env python3
"""
Dataset Profiler - QAI Phase 26
Analyzes chat datasets to provide intelligent hyperparameter recommendations.
Profiles: token counts, message lengths, vocabulary size, complexity metrics.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
import statistics


def tokenize_simple(text: str) -> List[str]:
    """Simple whitespace tokenization (fallback)."""
    return text.split()


def analyze_dataset(dataset_path: Path) -> Dict[str, Any]:
    """
    Analyze a chat dataset and return profiling metrics.
    
    Args:
        dataset_path: Path to train.json or test.json
    
    Returns:
        Dictionary with profiling metrics
    """
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            # Try standard JSON first
            try:
                f.seek(0)
                data = json.load(f)
            except json.JSONDecodeError:
                # Fall back to JSONL (one object per line)
                f.seek(0)
                data = []
                for line in f:
                    line = line.strip()
                    if line:
                        data.append(json.loads(line))
    except Exception as e:
        return {"error": f"Failed to load dataset: {e}"}
    
    if not isinstance(data, list):
        return {"error": "Dataset must be a JSON array or JSONL format"}
    
    # Metrics
    total_samples = len(data)
    token_counts = []
    message_lengths = []
    vocab = Counter()
    role_counts = Counter()
    turn_counts = []
    
    for idx, sample in enumerate(data):
        if not isinstance(sample, dict) or 'messages' not in sample:
            continue
        
        messages = sample.get('messages', [])
        turn_counts.append(len(messages))
        
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            role_counts[role] += 1
            
            # Tokenize (simple split for now, can be upgraded to tiktoken)
            tokens = tokenize_simple(content)
            token_counts.append(len(tokens))
            message_lengths.append(len(content))
            
            # Vocabulary
            for token in tokens:
                vocab[token.lower()] += 1
    
    # Calculate statistics
    profile = {
        "total_samples": total_samples,
        "valid_samples": len(turn_counts),
        "tokens": {
            "total": sum(token_counts),
            "mean": statistics.mean(token_counts) if token_counts else 0,
            "median": statistics.median(token_counts) if token_counts else 0,
            "min": min(token_counts) if token_counts else 0,
            "max": max(token_counts) if token_counts else 0,
            "stdev": statistics.stdev(token_counts) if len(token_counts) > 1 else 0,
        },
        "message_length": {
            "mean": statistics.mean(message_lengths) if message_lengths else 0,
            "median": statistics.median(message_lengths) if message_lengths else 0,
            "min": min(message_lengths) if message_lengths else 0,
            "max": max(message_lengths) if message_lengths else 0,
        },
        "turns_per_sample": {
            "mean": statistics.mean(turn_counts) if turn_counts else 0,
            "median": statistics.median(turn_counts) if turn_counts else 0,
            "min": min(turn_counts) if turn_counts else 0,
            "max": max(turn_counts) if turn_counts else 0,
        },
        "vocabulary": {
            "size": len(vocab),
            "unique_tokens": len(vocab),
            "top_20": vocab.most_common(20),
        },
        "roles": dict(role_counts),
    }
    
    return profile


def recommend_hyperparameters(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate hyperparameter recommendations based on dataset profile.
    
    Args:
        profile: Dataset profiling metrics
    
    Returns:
        Recommended hyperparameters with reasoning
    """
    samples = profile.get("valid_samples", 0)
    avg_tokens = profile.get("tokens", {}).get("mean", 0)
    vocab_size = profile.get("vocabulary", {}).get("size", 0)
    
    recommendations = {
        "batch_size": 8,
        "learning_rate": "1e-4",
        "lora_rank": 16,
        "epochs": 3,
        "max_samples": -1,
        "reasoning": []
    }
    
    # Sample size heuristics
    if samples < 500:
        recommendations["batch_size"] = 4
        recommendations["learning_rate"] = "2e-4"
        recommendations["lora_rank"] = 8
        recommendations["epochs"] = 5
        recommendations["reasoning"].append("Small dataset (<500): lower batch, higher LR, more epochs")
    elif samples < 2000:
        recommendations["batch_size"] = 8
        recommendations["learning_rate"] = "1e-4"
        recommendations["lora_rank"] = 16
        recommendations["epochs"] = 3
        recommendations["reasoning"].append("Medium dataset (<2k): balanced configuration")
    else:
        recommendations["batch_size"] = 16
        recommendations["learning_rate"] = "5e-5"
        recommendations["lora_rank"] = 32
        recommendations["epochs"] = 2
        recommendations["reasoning"].append("Large dataset (>2k): higher batch, lower LR, fewer epochs")
    
    # Token length adjustments
    if avg_tokens > 500:
        recommendations["batch_size"] = max(2, recommendations["batch_size"] // 2)
        recommendations["reasoning"].append(f"Long messages (avg {int(avg_tokens)} tokens): reduced batch to fit VRAM")
    
    # Vocabulary complexity
    if vocab_size > 10000:
        recommendations["lora_rank"] = min(64, recommendations["lora_rank"] * 2)
        recommendations["reasoning"].append(f"Rich vocabulary ({vocab_size} unique): increased LoRA rank for capacity")
    
    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Profile chat datasets for training optimization")
    parser.add_argument("dataset", type=Path, help="Path to dataset directory or train.json")
    parser.add_argument("--output", type=Path, help="Save profile to JSON file")
    parser.add_argument("--recommend", action="store_true", help="Show hyperparameter recommendations")
    parser.add_argument("--quiet", action="store_true", help="Minimal output (JSON only)")
    
    args = parser.parse_args()
    
    # Resolve dataset path
    if args.dataset.is_dir():
        dataset_file = args.dataset / "train.json"
        if not dataset_file.exists():
            print(f"Error: {dataset_file} not found", file=sys.stderr)
            sys.exit(1)
    else:
        dataset_file = args.dataset
    
    if not dataset_file.exists():
        print(f"Error: Dataset file not found: {dataset_file}", file=sys.stderr)
        sys.exit(1)
    
    # Profile dataset
    profile = analyze_dataset(dataset_file)
    
    if "error" in profile:
        print(f"Error: {profile['error']}", file=sys.stderr)
        sys.exit(1)
    
    # Generate recommendations
    if args.recommend:
        recommendations = recommend_hyperparameters(profile)
        profile["recommendations"] = recommendations
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2)
        if not args.quiet:
            print(f"Profile saved to: {args.output}")
    
    if not args.quiet:
        print("\n=== Dataset Profile ===")
        print(f"Samples: {profile['total_samples']} (valid: {profile['valid_samples']})")
        print(f"Tokens: {profile['tokens']['total']:,} total, {profile['tokens']['mean']:.1f} avg")
        print(f"  Range: {profile['tokens']['min']}-{profile['tokens']['max']}, σ={profile['tokens']['stdev']:.1f}")
        print(f"Vocabulary: {profile['vocabulary']['size']:,} unique tokens")
        print(f"Turns/sample: {profile['turns_per_sample']['mean']:.1f} avg")
        print(f"Roles: {', '.join(f'{k}={v}' for k,v in profile['roles'].items())}")
        
        if args.recommend:
            print("\n=== Recommendations ===")
            rec = recommendations
            print(f"Batch Size: {rec['batch_size']}")
            print(f"Learning Rate: {rec['learning_rate']}")
            print(f"LoRA Rank: {rec['lora_rank']}")
            print(f"Epochs: {rec['epochs']}")
            print("\nReasoning:")
            for reason in rec['reasoning']:
                print(f"  • {reason}")
    else:
        # JSON only output
        print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()
