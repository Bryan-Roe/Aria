#!/usr/bin/env python
"""
Quantum GGUF Complete Pipeline

End-to-end workflow for:
1. Finding or training LoRA models
2. Generating quantum enhancement circuits
3. Converting to GGUF format
4. Validation and deployment

Usage:
    # Use existing model
    python scripts/training/quantum_gguf_complete_pipeline.py --use-existing phi35_chat
    
    # Train new model then convert
    python scripts/training/quantum_gguf_complete_pipeline.py --train-new anime_avatar
    
    # Quick quantum-enhanced GGUF
    python scripts/training/quantum_gguf_complete_pipeline.py --quick-quantum
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_OUT = REPO_ROOT / "data_out"
DEPLOYED = REPO_ROOT / "deployed_models"

sys.path.insert(0, str(REPO_ROOT))


def setup_logging() -> logging.Logger:
    """Setup logging"""
    logger = logging.getLogger("quantum_gguf_pipeline")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    
    return logger


def find_existing_lora_models() -> List[Dict[str, Any]]:
    """Find all existing trained LoRA models"""
    models = []
    lora_dirs = [
        DATA_OUT / "lora_training",
        DATA_OUT / "autotrain",
        DATA_OUT / "train_and_promote",
    ]
    
    for base_dir in lora_dirs:
        if not base_dir.exists():
            continue
            
        for job_dir in base_dir.iterdir():
            if not job_dir.is_dir():
                continue
                
            # Look for checkpoint directories
            for checkpoint in job_dir.glob("checkpoint-*"):
                if checkpoint.is_dir():
                    # Check for required files
                    has_adapter = (checkpoint / "adapter_config.json").exists()
                    has_model = (checkpoint / "adapter_model.safetensors").exists()
                    
                    if has_adapter and has_model:
                        models.append({
                            "name": job_dir.name,
                            "path": str(checkpoint),
                            "base_dir": str(base_dir.name),
                            "timestamp": checkpoint.stat().st_mtime
                        })
    
    # Sort by timestamp (most recent first)
    models.sort(key=lambda x: x["timestamp"], reverse=True)
    return models


def generate_quantum_circuits(model_name: str, output_dir: Path, logger: logging.Logger) -> bool:
    """Generate quantum enhancement circuits"""
    logger.info(f"🔮 Generating quantum circuits for {model_name}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create quantum enhancement config
    quantum_config = {
        "quantum_features": [
            "quantum_encoding",
            "lightweight_quantum_attention",
            "quantum_noise_injection"
        ],
        "circuits": {
            "encoding": {
                "type": "amplitude_encoding",
                "n_qubits": 4,
                "layers": 2
            },
            "attention": {
                "type": "efficient_quantum_attention",
                "n_qubits": 4,
                "layers": 1
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    config_path = output_dir / "quantum_config.json"
    config_path.write_text(json.dumps(quantum_config, indent=2))
    
    logger.info(f"✅ Quantum config created: {config_path}")
    logger.info(f"   Features: {', '.join(quantum_config['quantum_features'])}")
    
    return True


def convert_to_gguf(
    model_path: str,
    output_name: str,
    logger: logging.Logger,
    dry_run: bool = False
) -> Optional[Path]:
    """Convert LoRA model to GGUF format"""
    logger.info(f"🔄 Converting {output_name} to GGUF")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = DATA_OUT / "gguf_training" / "convert_only" / timestamp
    gguf_path = output_dir / "convert_only.gguf"
    
    if dry_run:
        logger.info(f"[DRY-RUN] Would convert {model_path} -> {gguf_path}")
        return gguf_path
    
    # Use the gguf_training_automation script
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "training" / "gguf_training_automation.py"),
        "--convert-only",
        model_path
    ]
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Conversion failed: {result.stderr}")
            return None
            
        actual_gguf_path = _find_latest_convert_only_gguf(logger)
        if not actual_gguf_path:
            return None
        
        logger.info(f"✅ GGUF created: {actual_gguf_path}")
        return actual_gguf_path
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Conversion timed out (10 min limit)")
        return None
    except Exception as e:
        logger.error(f"❌ Conversion error: {e}")
        return None


def _find_latest_convert_only_gguf(logger: logging.Logger) -> Optional[Path]:
    convert_only_dir = DATA_OUT / "gguf_training" / "convert_only"
    if not convert_only_dir.exists():
        logger.error(f"❌ Convert-only output dir missing: {convert_only_dir}")
        return None
    
    gguf_files = list(convert_only_dir.rglob("convert_only.gguf"))
    if not gguf_files:
        logger.error(f"❌ No GGUF files found under: {convert_only_dir}")
        return None
    
    return max(gguf_files, key=lambda p: p.stat().st_mtime)


def validate_gguf(gguf_path: Path, logger: logging.Logger) -> bool:
    """Validate GGUF file"""
    logger.info(f"🔍 Validating {gguf_path.name}")
    
    if not gguf_path.exists():
        logger.error(f"❌ GGUF file not found: {gguf_path}")
        return False
    
    # Basic validation - check file size and magic bytes
    try:
        size_mb = gguf_path.stat().st_size / (1024 * 1024)
        
        if size_mb < 1:
            logger.warning(f"⚠️  GGUF file suspiciously small: {size_mb:.2f} MB")
            return False
        
        # Check magic bytes
        with open(gguf_path, "rb") as f:
            magic = f.read(4)
            if magic != b"GGUF":
                logger.error(f"❌ Invalid GGUF magic bytes: {magic}")
                return False
        
        logger.info(f"✅ GGUF validation passed ({size_mb:.1f} MB)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation error: {e}")
        return False


def deploy_model(gguf_path: Path, logger: logging.Logger) -> bool:
    """Deploy GGUF model to deployed_models/"""
    logger.info(f"🚀 Deploying {gguf_path.name}")
    
    DEPLOYED.mkdir(parents=True, exist_ok=True)
    
    dest = DEPLOYED / gguf_path.name
    
    try:
        import shutil
        shutil.copy2(gguf_path, dest)
        logger.info(f"✅ Deployed to: {dest}")
        return True
    except Exception as e:
        logger.error(f"❌ Deployment error: {e}")
        return False


def run_complete_pipeline(
    model_path: str,
    model_name: str,
    logger: logging.Logger,
    dry_run: bool = False,
    deploy: bool = True
) -> Dict[str, Any]:
    """Run complete quantum GGUF pipeline"""
    
    logger.info("=" * 60)
    logger.info(f"🎯 Quantum GGUF Pipeline: {model_name}")
    logger.info("=" * 60)
    
    result = {
        "model_name": model_name,
        "model_path": model_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phases": {}
    }
    
    # Phase 1: Generate quantum circuits
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quantum_dir = DATA_OUT / "quantum_gguf_training" / model_name / timestamp / "quantum_enhancements"
    
    if generate_quantum_circuits(model_name, quantum_dir, logger):
        result["phases"]["quantum_generation"] = {"success": True}
    else:
        result["phases"]["quantum_generation"] = {"success": False}
        return result
    
    # Phase 2: Convert to GGUF
    gguf_path = convert_to_gguf(model_path, model_name, logger, dry_run)
    
    if gguf_path:
        result["phases"]["conversion"] = {"success": True, "gguf_path": str(gguf_path)}
    else:
        result["phases"]["conversion"] = {"success": False}
        return result
    
    if dry_run:
        logger.info("✅ Dry-run complete")
        result["success"] = True
        result["dry_run"] = True
        return result
    
    # Phase 3: Validate
    if validate_gguf(gguf_path, logger):
        result["phases"]["validation"] = {"success": True}
    else:
        result["phases"]["validation"] = {"success": False}
        logger.warning("⚠️  Validation failed, skipping deployment")
        return result
    
    # Phase 4: Deploy (optional)
    if deploy:
        if deploy_model(gguf_path, logger):
            result["phases"]["deployment"] = {"success": True}
        else:
            result["phases"]["deployment"] = {"success": False}
    else:
        logger.info("ℹ️  Deployment skipped")
    
    result["success"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description="Quantum GGUF Complete Pipeline")
    parser.add_argument("--use-existing", help="Use existing model by name")
    parser.add_argument("--model-path", help="Direct path to LoRA model")
    parser.add_argument("--train-new", help="Train new model first (job name)")
    parser.add_argument("--quick-quantum", action="store_true", 
                       help="Quick demo with most recent model")
    parser.add_argument("--list-models", action="store_true",
                       help="List available LoRA models")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry-run mode (no actual conversion)")
    parser.add_argument("--no-deploy", action="store_true",
                       help="Skip deployment phase")
    
    args = parser.parse_args()
    logger = setup_logging()
    
    # List models mode
    if args.list_models:
        logger.info("🔍 Scanning for existing LoRA models...")
        models = find_existing_lora_models()
        
        if not models:
            logger.info("No LoRA models found")
            return
        
        logger.info(f"\nFound {len(models)} LoRA models:\n")
        for i, model in enumerate(models, 1):
            logger.info(f"{i}. {model['name']}")
            logger.info(f"   Path: {model['path']}")
            logger.info(f"   Source: {model['base_dir']}")
            logger.info("")
        
        return
    
    # Determine which model to use
    model_path = None
    model_name = None
    
    if args.model_path:
        model_path = args.model_path
        model_name = Path(model_path).parent.name
    
    elif args.use_existing or args.quick_quantum:
        logger.info("🔍 Finding existing LoRA models...")
        models = find_existing_lora_models()
        
        if not models:
            logger.error("❌ No existing LoRA models found")
            logger.info("Run with --list-models to see available models")
            return 1
        
        if args.use_existing:
            # Find by name
            matching = [m for m in models if args.use_existing in m["name"]]
            if not matching:
                logger.error(f"❌ No model found matching '{args.use_existing}'")
                logger.info(f"Available: {', '.join([m['name'] for m in models[:5]])}")
                return 1
            model = matching[0]
        else:
            # Use most recent
            model = models[0]
        
        model_path = model["path"]
        model_name = model["name"]
        logger.info(f"✅ Selected: {model_name}")
        logger.info(f"   Path: {model_path}")
    
    elif args.train_new:
        logger.error("❌ --train-new not yet implemented")
        logger.info("Use --use-existing or --model-path for now")
        return 1
    
    else:
        parser.print_help()
        logger.info("\n💡 Tip: Run with --list-models to see available models")
        return 1
    
    # Run pipeline
    result = run_complete_pipeline(
        model_path=model_path,
        model_name=model_name,
        logger=logger,
        dry_run=args.dry_run,
        deploy=not args.no_deploy
    )
    
    # Save result
    output_file = DATA_OUT / "quantum_gguf_pipeline_result.json"
    output_file.write_text(json.dumps(result, indent=2))
    
    logger.info(f"\n📊 Result saved to: {output_file}")
    
    if result.get("success"):
        logger.info("✅ Pipeline complete!")
        return 0
    else:
        logger.error("❌ Pipeline failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
