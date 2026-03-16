"""
Quantum LLM Quick Start Example
================================

Complete example demonstrating quantum-enhanced LLM training.

Usage:
    python quantum_llm_quickstart.py --mode quick
    python quantum_llm_quickstart.py --mode full --config my_config.yaml
    python quantum_llm_quickstart.py --mode monitor
    python quantum_llm_quickstart.py --mode generate --prompt "Hello"

Author: Quantum AI Workspace
Date: March 9, 2026
"""

import logging
import argparse
import sys
from pathlib import Path
from typing import Optional
import time

import torch
import torch.nn as nn

# Ensure src modules are importable when running from repository root.
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import quantum LLM components
try:
    from src.quantum_llm_integrated import (
        QuantumLLMConfig,
        QuantumLLMSystem,
        IntegratedQuantumLLM,
    )
    INTEGRATED_AVAILABLE = True
except ImportError:
    INTEGRATED_AVAILABLE = False

try:
    from src.quantum_llm_datasets import (
        CharacterTokenizer,
        TextDataset,
        DatasetBuilder,
        create_train_val_split,
    )
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False

logger = logging.getLogger(__name__)


def quick_start_example():
    """
    Quick start: Minimal quantum LLM training example.
    """
    logger.info("=" * 80)
    logger.info("QUANTUM LLM QUICK START")
    logger.info("=" * 80)
    
    if not INTEGRATED_AVAILABLE or not DATASETS_AVAILABLE:
        logger.error("Required components not available")
        logger.error(f"Integrated: {INTEGRATED_AVAILABLE}, Datasets: {DATASETS_AVAILABLE}")
        return
    
    # Step 1: Create configuration
    logger.info("Step 1: Creating configuration...")
    config = QuantumLLMConfig()
    config.config.update({
        "vocab_size": 256,
        "d_model": 64,
        "n_heads": 2,
        "n_layers": 2,
        "n_qubits": 2,
        "max_seq_length": 128,
        "batch_size": 4,
        "num_epochs": 2,
        "learning_rate": 1e-3,
        "output_dir": "data_out/quantum_llm_quickstart",
        "enable_curriculum": True,
        "enable_dashboard": True,
    })
    
    # Step 2: Create tokenizer
    logger.info("Step 2: Creating tokenizer...")
    tokenizer = CharacterTokenizer(vocab_size=config["vocab_size"])
    
    # Step 3: Create sample dataset
    logger.info("Step 3: Creating sample dataset...")
    sample_texts = [
        "Quantum computing harnesses quantum mechanics to process information.",
        "Machine learning algorithms learn patterns from data.",
        "Language models understand and generate natural language text.",
        "Quantum circuits use qubits and quantum gates for computation.",
        "Neural networks consist of interconnected layers of artificial neurons.",
        "Superposition allows quantum bits to exist in multiple states.",
        "Training deep learning models requires large datasets and computing power.",
        "Entanglement creates correlations between quantum particles.",
        "Natural language processing enables computers to understand human language.",
        "Quantum advantage emerges when quantum algorithms outperform classical ones.",
    ] * 10  # Repeat for more training data
    
    dataset = TextDataset(
        texts=sample_texts,
        tokenizer=tokenizer,
        max_seq_length=config["max_seq_length"],
        stride=64,
    )
    
    train_dataset, val_dataset = create_train_val_split(dataset, val_ratio=0.1)
    logger.info(f"Train size: {len(train_dataset)}, Val size: {len(val_dataset)}")
    
    # Step 4: Initialize quantum LLM system
    logger.info("Step 4: Initializing quantum LLM system...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    system = QuantumLLMSystem(config, device=device)
    
    # Step 5: Start training
    logger.info("Step 5: Starting training...")
    logger.info(f"Model parameters: {sum(p.numel() for p in system.model.parameters()):,}")
    
    start_time = time.time()
    report = system.train(train_dataset, val_dataset)
    training_time = time.time() - start_time
    
    # Step 6: Results
    logger.info("=" * 80)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Training time: {training_time:.2f}s")
    logger.info(f"Output directory: {system.output_dir}")
    
    # Step 7: Generate report
    logger.info("Step 7: Generating final report...")
    final_report = system.generate_report()
    
    logger.info("✅ Quick start complete!")
    logger.info(f"📁 Check results in: {system.output_dir}")
    
    return system, tokenizer


def full_training_example(config_path: Optional[Path] = None):
    """
    Full training: Complete quantum LLM training with all features.
    """
    logger.info("=" * 80)
    logger.info("QUANTUM LLM FULL TRAINING")
    logger.info("=" * 80)
    
    if not INTEGRATED_AVAILABLE or not DATASETS_AVAILABLE:
        logger.error("Required components not available")
        return
    
    # Load configuration
    if config_path and Path(config_path).exists():
        config = QuantumLLMConfig(config_path)
        logger.info(f"Configuration loaded from: {config_path}")
    else:
        # Use default configuration
        config = QuantumLLMConfig()
        config.config.update({
            "vocab_size": 256,
            "d_model": 128,
            "n_heads": 4,
            "n_layers": 4,
            "n_qubits": 4,
            "max_seq_length": 512,
            "batch_size": 16,
            "num_epochs": 10,
            "learning_rate": 1e-4,
            "output_dir": "data_out/quantum_llm_full",
            "enable_multi_scale_attention": True,
            "enable_adaptive_entanglement": True,
            "enable_circuit_caching": True,
            "enable_curriculum": True,
            "enable_dashboard": True,
            "optimization_level": 2,
        })
    
    # Create tokenizer
    tokenizer = CharacterTokenizer(vocab_size=config["vocab_size"])
    
    # Load datasets
    # Try to find datasets in the workspace
    datasets_dir = Path("datasets")
    available_datasets = []
    
    if datasets_dir.exists():
        for category in ["chat", "quantum", "massive_quantum"]:
            category_dir = datasets_dir / category
            if category_dir.exists():
                for file in category_dir.glob("*.json"):
                    available_datasets.append(file)
    
    if available_datasets:
        logger.info(f"Found {len(available_datasets)} dataset files")
        # Use first available dataset
        dataset = DatasetBuilder.auto_detect_and_load(
            available_datasets[0],
            tokenizer,
            config["max_seq_length"],
        )
    else:
        logger.info("No datasets found, using sample data")
        sample_texts = [
            "The quantum language model combines quantum computing with natural language processing.",
            "Training involves curriculum learning with progressive quantum integration.",
            "Circuit optimization reduces execution time through caching and compilation.",
            "Multi-scale attention captures information at different granularities.",
            "Adaptive entanglement routing selects optimal quantum circuit topology.",
        ] * 50
        
        dataset = TextDataset(
            texts=sample_texts,
            tokenizer=tokenizer,
            max_seq_length=config["max_seq_length"],
        )
    
    train_dataset, val_dataset = create_train_val_split(dataset, val_ratio=0.1)
    
    # Initialize system
    device = "cuda" if torch.cuda.is_available() else "cpu"
    system = QuantumLLMSystem(config, device=device)
    
    # Save configuration
    config_save_path = Path(config["output_dir"]) / "config.yaml"
    config.save(config_save_path)
    
    # Train
    logger.info("Starting full training pipeline...")
    report = system.train(train_dataset, val_dataset)
    
    # Generate comprehensive report
    final_report = system.generate_report()
    
    logger.info("✅ Full training complete!")
    logger.info(f"📁 Results: {system.output_dir}")
    
    return system, tokenizer


def monitor_training(output_dir: Path):
    """
    Monitor an ongoing or completed training session.
    """
    logger.info("=" * 80)
    logger.info("QUANTUM LLM TRAINING MONITOR")
    logger.info("=" * 80)
    
    output_dir = Path(output_dir)
    
    # Check for dashboard data
    dashboard_path = output_dir / "dashboard" / "dashboard.json"
    if dashboard_path.exists():
        import json
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        logger.info("Dashboard Data:")
        logger.info(f"  Timestamp: {dashboard_data.get('timestamp', 'N/A')}")
        
        metrics = dashboard_data.get('metrics_summary', {})
        logger.info(f"  Loss (MA): {metrics.get('moving_avg_loss', 'N/A'):.4f}")
        logger.info(f"  Perplexity (MA): {metrics.get('moving_avg_perplexity', 'N/A'):.2f}")
        logger.info(f"  Loss Trend: {metrics.get('loss_trend', 'N/A')}")
        
        alerts = dashboard_data.get('recent_alerts', [])
        logger.info(f"  Recent Alerts: {len(alerts)}")
    else:
        logger.warning(f"Dashboard not found: {dashboard_path}")
    
    # Check for training report
    report_path = output_dir / "training" / "training_report.json"
    if report_path.exists():
        import json
        with open(report_path) as f:
            report = json.load(f)
        
        logger.info("Training Report:")
        logger.info(f"  Total Stages: {report.get('total_stages', 'N/A')}")
        logger.info(f"  Total Time: {report.get('total_time', 'N/A'):.2f}s")
        logger.info(f"  Best Loss: {report.get('best_loss', 'N/A'):.4f}")
    else:
        logger.warning(f"Training report not found: {report_path}")
    
    logger.info("=" * 80)


def generate_text(model_path: Path, tokenizer: CharacterTokenizer, prompt: str, max_length: int = 100):
    """
    Generate text using trained quantum LLM.
    """
    logger.info("=" * 80)
    logger.info("QUANTUM LLM TEXT GENERATION")
    logger.info("=" * 80)
    
    if not INTEGRATED_AVAILABLE:
        logger.error("Integrated components not available")
        return
    
    # Load model
    checkpoint = torch.load(model_path, map_location="cpu")
    config = QuantumLLMConfig()
    config.config = checkpoint["config"]
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = IntegratedQuantumLLM(config).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    
    logger.info(f"Model loaded from: {model_path}")
    logger.info(f"Prompt: {prompt}")
    
    # Encode prompt
    input_ids = torch.tensor(tokenizer.encode(prompt, add_special_tokens=False)).unsqueeze(0).to(device)
    
    # Generate
    generated_ids = input_ids[0].tolist()
    
    with torch.no_grad():
        for _ in range(max_length):
            # Forward pass
            outputs = model(input_ids)
            
            # Get next token
            next_token_logits = outputs[0, -1, :]
            next_token_id = torch.argmax(next_token_logits).item()
            
            generated_ids.append(next_token_id)
            
            # Update input
            input_ids = torch.tensor([generated_ids]).to(device)
            
            # Stop at EOS
            if next_token_id == tokenizer.eos_id:
                break
    
    # Decode
    generated_text = tokenizer.decode(generated_ids)
    
    logger.info("=" * 80)
    logger.info("GENERATED TEXT:")
    logger.info("=" * 80)
    logger.info(generated_text)
    logger.info("=" * 80)
    
    return generated_text


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Quantum LLM Quick Start Examples")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["quick", "full", "monitor", "generate"],
        default="quick",
        help="Execution mode",
    )
    parser.add_argument("--config", type=str, help="Path to configuration YAML")
    parser.add_argument("--output-dir", type=str, help="Output directory to monitor")
    parser.add_argument("--model", type=str, help="Path to trained model")
    parser.add_argument("--prompt", type=str, default="Hello", help="Generation prompt")
    parser.add_argument("--max-length", type=int, default=100, help="Max generation length")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check dependencies
    if not INTEGRATED_AVAILABLE:
        logger.error("❌ Integrated components not available")
        logger.error("   Make sure quantum_llm_integrated.py is importable")
        return
    
    if not DATASETS_AVAILABLE:
        logger.error("❌ Dataset utilities not available")
        logger.error("   Make sure quantum_llm_datasets.py is importable")
        return
    
    # Execute requested mode
    if args.mode == "quick":
        system, tokenizer = quick_start_example()
        
    elif args.mode == "full":
        config_path = Path(args.config) if args.config else None
        system, tokenizer = full_training_example(config_path)
        
    elif args.mode == "monitor":
        output_dir = Path(args.output_dir) if args.output_dir else Path("data_out/quantum_llm_quickstart")
        monitor_training(output_dir)
        
    elif args.mode == "generate":
        if not args.model:
            logger.error("--model required for generate mode")
            return
        
        # Need tokenizer
        tokenizer = CharacterTokenizer(vocab_size=256)
        
        generate_text(
            model_path=Path(args.model),
            tokenizer=tokenizer,
            prompt=args.prompt,
            max_length=args.max_length,
        )


if __name__ == "__main__":
    main()
