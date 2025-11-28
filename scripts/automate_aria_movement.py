"""
Automated Aria Movement Training Pipeline
Trains AI models to understand and generate Aria movement commands
"""
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class AriaTrainingAutomation:
    """Automates training and deployment of Aria movement models"""
    
    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.dataset_path = "datasets/chat/aria_movement"
        self.output_base = "data_out/aria_models"
        self.deployment_path = "data_out/lora_training/lora_adapter"
        
    def validate_dataset(self) -> bool:
        """Validate aria movement dataset exists and has proper format"""
        print("\n=== Validating Aria Movement Dataset ===")
        
        train_file = self.root / self.dataset_path / "train.json"
        test_file = self.root / self.dataset_path / "test.json"
        
        if not train_file.exists():
            print(f"❌ Training file not found: {train_file}")
            return False
        
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
        
        # Check format
        try:
            with open(train_file, 'r', encoding='utf-8') as f:
                train_data = json.load(f)
            
            # Validate structure
            if not isinstance(train_data, list):
                print("❌ Train data must be a list of examples")
                return False
            
            # Count command types
            command_counts = {
                'move': 0,
                'walk': 0,
                'center': 0,
                'wave': 0,
                'jump': 0,
                'dance': 0
            }
            
            for example in train_data:
                if 'messages' not in example:
                    print("❌ Example missing 'messages' field")
                    return False
                
                response = example['messages'][-1]['content'].lower()
                for cmd in command_counts.keys():
                    if f'[aria:{cmd}' in response or f'aria:{cmd}' in response:
                        command_counts[cmd] += 1
            
            print(f"✅ Dataset validated: {len(train_data)} training examples")
            print("\nCommand distribution:")
            for cmd, count in command_counts.items():
                print(f"  - {cmd}: {count} examples")
            
            return True
            
        except Exception as e:
            print(f"❌ Error validating dataset: {e}")
            return False
    
    def train_aria_model(self, quick: bool = False) -> Dict[str, Any]:
        """Train a model specialized for Aria movement commands"""
        print("\n=== Training Aria Movement Model ===")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.root / self.output_base / f"aria_{timestamp}"
        
        # Training parameters
        if quick:
            max_train = 40
            max_eval = 10
            epochs = 2
            print("Mode: Quick training (for testing)")
        else:
            max_train = None  # Use all samples
            max_eval = None
            epochs = 3
            print("Mode: Full training")
        
        cmd = [
            sys.executable,
            str(self.root / "AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py"),
            "--dataset", self.dataset_path,
            "--save-dir", str(output_dir),
            "--epochs", str(epochs),
            "--learning-rate", "0.0003",  # Higher LR for specialized task
            "--lora-dropout", "0.05",     # Lower dropout for small dataset
        ]
        
        if max_train:
            cmd.extend(["--max-train-samples", str(max_train)])
        if max_eval:
            cmd.extend(["--max-eval-samples", str(max_eval)])
        
        print(f"\nCommand: {' '.join(cmd)}")
        print(f"Output: {output_dir}")
        
        try:
            result = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print("✅ Training completed successfully!")
                return {
                    "status": "success",
                    "output_dir": str(output_dir),
                    "timestamp": timestamp
                }
            else:
                print(f"❌ Training failed with code {result.returncode}")
                print(f"Error: {result.stderr[-500:]}")  # Last 500 chars
                return {
                    "status": "failed",
                    "error": result.stderr[-500:]
                }
        
        except subprocess.TimeoutExpired:
            print("❌ Training timed out after 10 minutes")
            return {"status": "timeout"}
        except Exception as e:
            print(f"❌ Training error: {e}")
            return {"status": "error", "error": str(e)}
    
    def evaluate_aria_model(self, model_path: str) -> Dict[str, Any]:
        """Evaluate Aria model on test set"""
        print("\n=== Evaluating Aria Model ===")
        
        cmd = [
            sys.executable,
            str(self.root / "scripts/evaluate_lora_model.py"),
            "--dataset", self.dataset_path,
            "--model", model_path,
            "--max-samples", "10",
            "--metric", "perplexity",
            "--metric", "diversity",
            "--output-format", "json"
        ]
        
        print(f"Evaluating: {model_path}")
        
        try:
            result = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, timeout=300)
            
            # Parse JSON from output
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('{'):
                    try:
                        metrics = json.loads(line)
                        print("✅ Evaluation complete")
                        print(f"  Perplexity: {metrics.get('metrics', {}).get('perplexity', 'N/A')}")
                        print(f"  Diversity: {metrics.get('metrics', {}).get('diversity', 'N/A')}")
                        return {"status": "success", "metrics": metrics}
                    except json.JSONDecodeError:
                        continue
            
            return {"status": "no_metrics", "output": result.stdout[-200:]}
        
        except Exception as e:
            print(f"❌ Evaluation error: {e}")
            return {"status": "error", "error": str(e)}
    
    def deploy_aria_model(self, trained_model_path: str) -> bool:
        """Deploy trained Aria model to active LoRA adapter location"""
        print("\n=== Deploying Aria Model ===")
        
        source = Path(trained_model_path)
        target = self.root / self.deployment_path
        
        if not source.exists():
            print(f"❌ Source model not found: {source}")
            return False
        
        # Create backup of current model
        if target.exists():
            backup_path = target.parent / f"lora_adapter_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"📦 Backing up current model to: {backup_path}")
            try:
                import shutil
                shutil.copytree(target, backup_path)
                print("✅ Backup created")
            except Exception as e:
                print(f"⚠️  Backup failed: {e}")
        
        # Deploy new model
        try:
            import shutil
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
            print(f"✅ Model deployed to: {target}")
            print("\n⚡ Aria movement model is now active!")
            return True
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False
    
    def run_full_pipeline(self, quick: bool = False, auto_deploy: bool = False) -> Dict[str, Any]:
        """Run complete automated pipeline: validate -> train -> evaluate -> deploy"""
        print("=" * 70)
        print("ARIA MOVEMENT AUTOMATION PIPELINE")
        print("=" * 70)
        
        results = {}
        
        # Step 1: Validate dataset
        if not self.validate_dataset():
            return {"status": "failed", "step": "validation"}
        results["validation"] = "passed"
        
        # Step 2: Train model
        train_result = self.train_aria_model(quick=quick)
        results["training"] = train_result
        
        if train_result.get("status") != "success":
            return results
        
        model_path = train_result["output_dir"]
        
        # Step 3: Evaluate model
        eval_result = self.evaluate_aria_model(model_path)
        results["evaluation"] = eval_result
        
        # Step 4: Deploy (if requested and training succeeded)
        if auto_deploy and train_result.get("status") == "success":
            deploy_success = self.deploy_aria_model(model_path)
            results["deployment"] = "success" if deploy_success else "failed"
        
        # Summary
        print("\n" + "=" * 70)
        print("PIPELINE SUMMARY")
        print("=" * 70)
        print(f"Validation: {results.get('validation', 'N/A')}")
        print(f"Training: {results.get('training', {}).get('status', 'N/A')}")
        print(f"Evaluation: {results.get('evaluation', {}).get('status', 'N/A')}")
        if 'deployment' in results:
            print(f"Deployment: {results['deployment']}")
        
        return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Aria Movement Training")
    parser.add_argument("--validate-only", action="store_true", help="Only validate dataset")
    parser.add_argument("--train-only", action="store_true", help="Only train model")
    parser.add_argument("--quick", action="store_true", help="Quick training mode (40 samples, 2 epochs)")
    parser.add_argument("--full", action="store_true", help="Full training mode (all samples, 3 epochs)")
    parser.add_argument("--deploy", action="store_true", help="Auto-deploy after successful training")
    parser.add_argument("--model-path", type=str, help="Path to trained model for evaluation/deployment")
    
    args = parser.parse_args()
    
    automation = AriaTrainingAutomation()
    
    if args.validate_only:
        automation.validate_dataset()
    elif args.train_only:
        automation.train_aria_model(quick=args.quick)
    elif args.model_path:
        if args.deploy:
            automation.deploy_aria_model(args.model_path)
        else:
            automation.evaluate_aria_model(args.model_path)
    else:
        # Full pipeline
        automation.run_full_pipeline(quick=args.quick, auto_deploy=args.deploy)

if __name__ == "__main__":
    main()
