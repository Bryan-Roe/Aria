#!/usr/bin/env python
"""
Automated Data Generation & Training Pipeline
==============================================

Generates synthetic chat datasets and automatically trains models.
Combines multiple data generation strategies:
1. LLM-based synthetic conversations (using existing model)
2. Repository-based Q&A generation  
3. Template-based chat augmentation
4. Self-training iterations (model improves on its own outputs)

Then automatically launches ultra-fast training on generated data.

Usage:
    # Quick: Generate 100 samples + train (2-3 min total)
    python scripts/auto_data_train.py --quick
    
    # Medium: Generate 500 samples + train (10-15 min)
    python scripts/auto_data_train.py --samples 500
    
    # Full pipeline with self-training (30-60 min)
    python scripts/auto_data_train.py --samples 1000 --self-train --iterations 2
    
    # Custom dataset + training
    python scripts/auto_data_train.py --output-dir datasets/chat/custom --samples 300 --train-mode rapid
"""

import argparse
import json
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Repository root
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Training scripts
ULTRAFAST_TRAIN = REPO_ROOT / "scripts" / "ultrafast_train.ps1"
FAST_TRAIN = REPO_ROOT / "scripts" / "fast_train.ps1"
SELF_TRAIN_SCRIPT = REPO_ROOT / "scripts" / "self_train_synthetic.py"
REPO_GEN_SCRIPT = REPO_ROOT / "scripts" / "generate_repo_training_dataset.py"

# Default output
DEFAULT_OUTPUT_DIR = REPO_ROOT / "datasets" / "chat" / "auto_generated"

# Conversation templates for synthetic data
CONVERSATION_TEMPLATES = [
    {
        "user": "Explain {topic} in simple terms.",
        "assistant": "{topic} is a fundamental concept in {domain}. It involves {explanation} and is commonly used for {use_case}. Key benefits include {benefits}."
    },
    {
        "user": "How do I implement {task} in {language}?",
        "assistant": "To implement {task} in {language}, follow these steps:\n1. {step1}\n2. {step2}\n3. {step3}\n\nHere's a code example:\n```{language}\n{code}\n```"
    },
    {
        "user": "What's the difference between {concept1} and {concept2}?",
        "assistant": "{concept1} and {concept2} are related but distinct:\n\n{concept1}:\n- {feature1}\n- {feature2}\n\n{concept2}:\n- {feature3}\n- {feature4}\n\nChoose {concept1} when {scenario1}, and {concept2} when {scenario2}."
    },
    {
        "user": "Debug this error: {error}",
        "assistant": "This error typically occurs when {cause}. To fix it:\n\n1. Check {check1}\n2. Verify {check2}\n3. Ensure {check3}\n\nIf the issue persists, try {solution}."
    },
    {
        "user": "Best practices for {activity}?",
        "assistant": "Here are the best practices for {activity}:\n\n1. **{practice1}**: {description1}\n2. **{practice2}**: {description2}\n3. **{practice3}**: {description3}\n\nAlways remember to {reminder}."
    },
]

# Knowledge base for filling templates
KNOWLEDGE_BASE = {
    "topics": [
        "machine learning", "neural networks", "API design", "database optimization",
        "cloud architecture", "containerization", "microservices", "GraphQL",
        "REST APIs", "authentication", "caching", "load balancing", "CI/CD",
        "quantum computing", "blockchain", "edge computing", "serverless",
    ],
    "domains": [
        "software engineering", "data science", "DevOps", "cloud computing",
        "web development", "mobile development", "AI/ML", "cybersecurity",
    ],
    "languages": [
        "Python", "JavaScript", "TypeScript", "C#", "Java", "Go", "Rust",
    ],
    "tasks": [
        "async operations", "error handling", "data validation", "API calls",
        "database queries", "file processing", "authentication", "caching",
    ],
    "errors": [
        "NullReferenceException", "ConnectionTimeout", "401 Unauthorized",
        "500 Internal Server Error", "Memory Leak", "DeadLock",
    ],
}


class DataGenerator:
    """Generate synthetic training data"""
    
    def __init__(self, output_dir: Path, seed: int = 42):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        random.seed(seed)
    
    def generate_template_based(self, count: int) -> List[Dict[str, Any]]:
        """Generate conversations from templates"""
        print(f"\n[DataGen] Generating {count} template-based conversations...")
        
        conversations = []
        for i in range(count):
            template = random.choice(CONVERSATION_TEMPLATES)
            
            # Fill template with random knowledge
            user_prompt = template["user"]
            assistant_response = template["assistant"]
            
            # Simple template filling
            for key, values in KNOWLEDGE_BASE.items():
                if f"{{{key[:-1]}}}" in user_prompt or f"{{{key[:-1]}}}" in assistant_response:
                    value = random.choice(values)
                    user_prompt = user_prompt.replace(f"{{{key[:-1]}}}", value)
                    assistant_response = assistant_response.replace(f"{{{key[:-1]}}}", value)
            
            # Fill numbered placeholders
            for match in ["step", "feature", "practice", "check"]:
                for j in range(1, 5):
                    placeholder = f"{{{match}{j}}}"
                    if placeholder in user_prompt or placeholder in assistant_response:
                        value = f"{match} {j} details here"
                        user_prompt = user_prompt.replace(placeholder, value)
                        assistant_response = assistant_response.replace(placeholder, value)
            
            conversation = {
                "messages": [
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": assistant_response}
                ],
                "source": "template_generated",
                "timestamp": datetime.now().isoformat()
            }
            conversations.append(conversation)
        
        print(f"[DataGen] ✓ Generated {len(conversations)} conversations")
        return conversations
    
    def generate_from_repo(self, max_records: int = 200) -> List[Dict[str, Any]]:
        """Generate Q&A from repository code"""
        print(f"\n[DataGen] Generating repository-based Q&A...")
        
        try:
            # Run repo generation script
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_GEN_SCRIPT),
                    "--max-records", str(max_records),
                    "--output-dir", str(self.output_dir / "repo_temp"),
                    "--seed", str(self.seed)
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0:
                # Load generated data
                train_file = self.output_dir / "repo_temp" / "train.json"
                if train_file.exists():
                    with open(train_file) as f:
                        data = [json.loads(line) for line in f if line.strip()]
                    print(f"[DataGen] ✓ Generated {len(data)} repo Q&A samples")
                    return data
            else:
                print(f"[DataGen] ⚠ Repo generation failed: {result.stderr}")
                return []
        except Exception as e:
            print(f"[DataGen] ⚠ Repo generation error: {e}")
            return []
    
    def combine_and_save(self, datasets: List[List[Dict[str, Any]]], train_ratio: float = 0.9):
        """Combine multiple datasets and split train/test"""
        print(f"\n[DataGen] Combining datasets...")
        
        all_data = []
        for ds in datasets:
            all_data.extend(ds)
        
        # Shuffle
        random.shuffle(all_data)
        
        # Split
        split_idx = int(len(all_data) * train_ratio)
        train_data = all_data[:split_idx]
        test_data = all_data[split_idx:]
        
        # Save
        train_file = self.output_dir / "train.json"
        test_file = self.output_dir / "test.json"
        metadata_file = self.output_dir / "metadata.json"
        
        with open(train_file, 'w') as f:
            for item in train_data:
                f.write(json.dumps(item) + '\n')
        
        with open(test_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "total_samples": len(all_data),
            "train_samples": len(train_data),
            "test_samples": len(test_data),
            "seed": self.seed,
            "sources": sorted({item.get("source", "unknown") for item in all_data})
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"[DataGen] ✓ Saved dataset:")
        print(f"  Train: {len(train_data)} samples")
        print(f"  Test: {len(test_data)} samples")
        print(f"  Location: {self.output_dir}")
        
        return train_file, test_file, metadata


def create_training_config(dataset_dir: Path, output_name: str, model: str) -> tuple[Path, str]:
    """Create autotrain config for generated dataset for selected model.

    Args:
        dataset_dir: Directory containing generated train/test files
        output_name: Unique run token (timestamp based)
        model: 'phi', 'qwen', or 'tinyllama'

    Returns:
        (config_path, job_name)
    """
    ds_path = dataset_dir.as_posix()  # POSIX style for YAML portability

    if model == 'qwen':
        config_file = 'AI/microsoft_phi-silica-3.6_v1/lora/lora_qwen_ultrafast.yaml'
        hf_model_id = 'Qwen/Qwen2.5-3B-Instruct'
        prefix = 'qwen_ultra'
        learning_rate = 0.0003
        lora_rank = 4
    elif model == 'tinyllama':
        config_file = 'AI/microsoft_phi-silica-3.6_v1/lora/lora_tinyllama_ultrafast.yaml'
        hf_model_id = 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
        prefix = 'tinyllama_ultra'
        learning_rate = 0.00035
        lora_rank = 4
    else:
        config_file = 'AI/microsoft_phi-silica-3.6_v1/lora/lora_ultrafast.yaml'
        hf_model_id = 'microsoft/Phi-3.5-mini-instruct'
        prefix = 'phi35_ultra'
        learning_rate = 0.0004
        lora_rank = 4

    job_name = f"{prefix}_{output_name}"
    config_content = (
        "version: 1\n\n"
        f"# Auto-generated training config for synthetic data\n"
        f"# Dataset: {ds_path}\n"
        f"# Generated: {datetime.now().isoformat()}\n"
        f"# Model: {hf_model_id}\n\n"
        "jobs:\n"
        f"  - name: {job_name}\n"
        "    category: autogen\n"
        "    runner: hf\n"
        f"    config: {config_file}\n"
        f"    dataset: \"{ds_path}\"\n"
        f"    save_dir: data_out/lora_training/{output_name}\n"
        "    epochs: 1\n"
        "    max_train_samples: null\n"
        "    max_eval_samples: null\n"
        f"    learning_rate: {learning_rate}\n"
        "    lora_dropout: 0.05\n"
        f"    lora_rank: {lora_rank}\n"
        f"    hf_model_id: {hf_model_id}\n"
    )

    config_path = REPO_ROOT / f"autotrain_{output_name}.yaml"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print(f"\n[Config] Created training config: {config_path}")
    print(f"[Config] Job name: {job_name}")
    return config_path, job_name


def run_training(mode: str = "ultra", config_path: Path | None = None, job_name: str | None = None, filter_override: str | None = None, min_train_samples: int | None = None) -> bool:
    """Launch training using parallel_train.py so custom config & dataset are applied.

    Args:
        mode: Training mode label (currently informational)
        config_path: Path to generated autotrain YAML
        job_name: Name of job inside config for filtering

    Returns:
        True on success, False otherwise.
    """
    print(f"\n[Training] Starting training (mode: {mode}) with config: {config_path}")
    if not config_path or not config_path.exists():
        print("[Training] ✗ Missing config file; aborting")
        return False

    # Use parallel_train directly
    parallel_script = REPO_ROOT / "scripts" / "parallel_train.py"
    filter_pattern = filter_override if filter_override else (job_name if job_name else "*")
    cmd = [
        sys.executable,
        str(parallel_script),
        "--config", str(config_path),
        "--filter", filter_pattern,
        "--max-parallel", "1",
    ]
    if min_train_samples is not None:
        cmd.extend(["--min-train-samples", str(min_train_samples)])
    # Pass through optional evaluation / cleanup flags if env vars set by caller
    # Using environment or global args isn't ideal; proper pass-through handled in main below.

    try:
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
        if result.returncode == 0:
            print("[Training] ✓ Training completed successfully!")
            return True
        else:
            print(f"[Training] ✗ Training failed (exit code {result.returncode})")
            return False
    except Exception as e:
        print(f"[Training] ✗ Training error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate synthetic data and train models"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: 100 samples, ultra-fast training (2-3 min)"
    )
    
    parser.add_argument(
        "--samples",
        type=int,
        default=200,
        help="Total samples to generate (default: 200)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    
    parser.add_argument(
        "--train-mode",
        choices=["ultra", "rapid", "quick", "none"],
        default="ultra",
        help="Training mode after generation (default: ultra)"
    )
    
    parser.add_argument(
        "--self-train",
        action="store_true",
        help="Run self-training iterations (requires more time)"
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=2,
        help="Self-training iterations (default: 2)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    
    parser.add_argument(
        "--no-repo",
        action="store_true",
        help="Skip repository-based generation"
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Override job name filter passed to parallel trainer (optional)"
    )
    parser.add_argument(
        "--model",
        choices=["phi", "qwen", "tinyllama"],
        default="phi",
        help="Model family to train (phi, qwen, tinyllama). Default: phi"
    )
    parser.add_argument(
        "--min-train-samples",
        type=int,
        default=50,
        help="Safety guard: skip training if counted train samples below this threshold (default: 50)"
    )
    parser.add_argument(
        "--no-eval",
        action="store_true",
        help="Disable evaluation & sample generation (passes --no-eval to parallel trainer)"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="After training, remove intermediate checkpoints (passes --cleanup)"
    )
    parser.add_argument(
        "--ranking-metric",
        choices=["perplexity_improvement", "post_perplexity", "diversity_avg", "combined_improvement", "distinct_diversity"],
        default="perplexity_improvement",
        help="Ranking metric for jobs in status history (passes --ranking-metric)"
    )
    
    args = parser.parse_args()
    
    # Quick mode overrides (preserve explicit 'none')
    if args.quick:
        args.samples = 100
        if args.train_mode != "none":
            args.train_mode = "ultra"
    
    print("=" * 70)
    print("  AUTO DATA GENERATION & TRAINING PIPELINE")
    print("=" * 70)
    print(f"Samples: {args.samples}")
    print(f"Output: {args.output_dir}")
    print(f"Training Mode: {args.train_mode}")
    print(f"Self-Training: {args.self_train}")
    print("=" * 70)
    
    # Initialize generator
    generator = DataGenerator(args.output_dir, args.seed)
    
    # Generate datasets
    datasets = []
    
    # Template-based generation (fast)
    template_count = int(args.samples * 0.7)  # 70% templates
    templates = generator.generate_template_based(template_count)
    datasets.append(templates)
    
    # Repository-based generation (if enabled)
    if not args.no_repo:
        repo_count = int(args.samples * 0.3)  # 30% repo Q&A
        repo_data = generator.generate_from_repo(repo_count)
        if repo_data:
            datasets.append(repo_data)
    
    # Combine and save
    train_file, test_file, metadata = generator.combine_and_save(datasets)
    
    # Create training config
    output_name = f"autogen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    config_path, job_name = create_training_config(args.output_dir, output_name, args.model)
    
    # Run training
    if args.train_mode != "none":
        # Build command by invoking run_training after enriching environment/args
        parallel_script = REPO_ROOT / "scripts" / "parallel_train.py"
        filter_pattern = args.filter if args.filter else job_name
        cmd = [
            sys.executable,
            str(parallel_script),
            "--config", str(config_path),
            "--filter", filter_pattern,
            "--max-parallel", "1",
            "--min-train-samples", str(args.min_train_samples),
            "--ranking-metric", args.ranking_metric,
        ]
        if args.no_eval:
            cmd.append("--no-eval")
        if args.cleanup:
            cmd.append("--cleanup")
        print(f"\n[Training] Launch command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
            success = (result.returncode == 0)
            if success:
                print("[Training] ✓ Training pipeline finished")
            else:
                print(f"[Training] ✗ Training pipeline exit code {result.returncode}")
        except Exception as e:
            print(f"[Training] ✗ Training error: {e}")
            success = False
        
        if not success:
            print("\n[Pipeline] Training failed, but data is generated and ready.")
            print(f"  Dataset: {args.output_dir}")
            print(f"  Config: {config_path}")
            print("\nManual training:")
            print(f"  .\\scripts\\ultrafast_train.ps1 -Mode ultra")
            return 1
    
    # Self-training (optional)
    if args.self_train:
        print(f"\n[Pipeline] Starting self-training ({args.iterations} iterations)...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SELF_TRAIN_SCRIPT),
                    "--iterations", str(args.iterations),
                    "--samples-per-iter", str(args.samples // 2),
                    "--output-dir", str(args.output_dir.parent / "self_training")
                ],
                cwd=str(REPO_ROOT),
                check=False
            )
            
            if result.returncode == 0:
                print("[Pipeline] ✓ Self-training completed!")
            else:
                print("[Pipeline] ⚠ Self-training had issues")
        except Exception as e:
            print(f"[Pipeline] ⚠ Self-training error: {e}")
    
    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE!")
    print("=" * 70)
    print(f"📊 Dataset: {args.output_dir}")
    print(f"📈 Samples: {metadata['train_samples']} train, {metadata['test_samples']} test")
    if args.train_mode != "none":
        print(f"🤖 Model Output Dir: data_out/lora_training/{output_name}")
        print(f"🔧 Job Name: {job_name}")
        base_model_map = {
            'phi': 'microsoft/Phi-3.5-mini-instruct',
            'qwen': 'Qwen/Qwen2.5-3B-Instruct',
            'tinyllama': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
        }
        print(f"🧬 Base Model: {base_model_map.get(args.model, 'unknown')}")
        if args.filter:
            print(f"🪄 Filter Override: {args.filter}")
        print(f"🛡 Min Train Samples Guard: {args.min_train_samples}")
        print(f"🧪 Evaluation Enabled: {not args.no_eval}")
        print(f"🧹 Cleanup Enabled: {args.cleanup}")
        print(f"📊 Ranking Metric: {args.ranking_metric}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
