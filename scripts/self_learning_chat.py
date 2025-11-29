"""
Self-Learning Chat System
Automatically improves from conversations by:
1. Logging all conversations
2. Periodically training LoRA adapters on chat history
3. Deploying improved models automatically
"""

import json
import time
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SelfLearningChat:
    def __init__(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.chat_logs_dir = self.repo_root / "talk-to-ai" / "logs"
        self.training_data_dir = self.repo_root / "datasets" / "chat" / "chat_logs"
        self.output_dir = self.repo_root / "data_out" / "self_learning"
        self.status_file = self.output_dir / "status.json"
        
        # Create directories
        self.training_data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.status = self.load_status()
        
    def load_status(self) -> Dict:
        """Load learning status"""
        if self.status_file.exists():
            with open(self.status_file, "r") as f:
                return json.load(f)
        return {
            "started_at": datetime.now().isoformat(),
            "training_cycles": 0,
            "total_conversations": 0,
            "conversations_since_last_train": 0,
            "last_training": None,
            "best_model_path": None,
            "current_accuracy": 0.0,
            "learning_enabled": True
        }
    
    def save_status(self):
        """Save learning status"""
        with open(self.status_file, "w") as f:
            json.dump(self.status, f, indent=2)
    
    def collect_conversations(self) -> int:
        """Collect new conversations from logs with quality filtering"""
        if not self.chat_logs_dir.exists():
            print(f"No chat logs directory found at: {self.chat_logs_dir}")
            print("💡 Start chatting to generate conversation data!")
            return 0
        
        # Find all chat log files
        log_files = list(self.chat_logs_dir.glob("chat_*.jsonl"))
        print(f"Found {len(log_files)} conversation logs")
        
        if not log_files:
            return 0
        
        # Aggregate conversations into training format
        training_file = self.training_data_dir / "aggregated_conversations.jsonl"
        conversation_count = 0
        
        with open(training_file, "w", encoding="utf-8") as out_f:
            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8") as in_f:
                        messages = []
                        for line in in_f:
                            if line.strip():
                                msg = json.loads(line)
                                messages.append({
                                    "role": msg.get("role", "user"),
                                    "content": msg.get("content", "")
                                })
                        
                        # Group messages into conversation pairs with quality filtering
                        if len(messages) >= 2:
                            for i in range(0, len(messages) - 1, 2):
                                if i + 1 < len(messages):
                                    user_msg = messages[i]
                                    asst_msg = messages[i + 1]
                                    
                                    # Quality filters
                                    if len(user_msg.get("content", "").strip()) < 10:
                                        continue  # Skip very short questions
                                    if len(asst_msg.get("content", "").strip()) < 20:
                                        continue  # Skip very short answers
                                    if user_msg.get("content") == asst_msg.get("content"):
                                        continue  # Skip duplicates
                                    
                                    # Create training example
                                    training_example = {
                                        "messages": [user_msg, asst_msg]
                                    }
                                    out_f.write(json.dumps(training_example) + "\n")
                                    conversation_count += 1
                except Exception as e:
                    print(f"Error processing {log_file}: {e}")
        
        print(f"Collected {conversation_count} conversation pairs")
        self.status["conversations_since_last_train"] += conversation_count
        self.status["total_conversations"] += conversation_count
        self.save_status()
        
        return conversation_count
    
    def should_train(self, min_conversations: int = 50) -> bool:
        """Check if enough new conversations for training"""
        return self.status["conversations_since_last_train"] >= min_conversations
    
    def train_model(self, min_conversations: int, max_samples: int = 500, epochs: int = 3):
        """Train LoRA adapter on collected conversations"""
        if self.status["conversations_since_last_train"] < min_conversations:
            print(f"Not enough conversations yet ({self.status['conversations_since_last_train']} < {min_conversations})")
            return False
        
        print(f"\n{'='*60}")
        print(f"Starting self-learning training cycle #{self.status['training_cycles'] + 1}")
        print(f"Training on {self.status['conversations_since_last_train']} new conversations")
        print(f"{'='*60}\n")
        
        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cycle_dir = self.output_dir / f"cycle_{self.status['training_cycles'] + 1}_{timestamp}"
        
        # Build training command
        ml_venv = self.repo_root / "AI" / "microsoft_phi-silica-3.6_v1" / "venv" / "Scripts" / "python.exe"
        train_script = self.repo_root / "AI" / "microsoft_phi-silica-3.6_v1" / "scripts" / "train_lora.py"
        lora_config = self.repo_root / "AI" / "microsoft_phi-silica-3.6_v1" / "lora" / "lora.yaml"
        
        cmd = [
            str(ml_venv),
            str(train_script),
            "--dataset", str(self.training_data_dir),
            "--config", str(lora_config),
            "--save-dir", str(cycle_dir),
            "--max-train-samples", str(max_samples),
            "--epochs", str(epochs)
        ]
        
        print(f"Training command: {' '.join(cmd)}")
        
        try:
            # Run training with progress monitoring
            print("\n⏳ Training in progress (this may take several minutes)...")
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                check=False  # We manually check returncode
            )
            
            if result.returncode == 0:
                print("\n✅ Training completed successfully!")
                
                # Check if adapter was created
                adapter_path = cycle_dir / "lora_adapter"
                if adapter_path.exists() and (adapter_path / "adapter_config.json").exists():
                    # Validate adapter
                    print(f"✓ Model validated: {adapter_path}")
                    
                    # Update status with metrics
                    self.status["training_cycles"] += 1
                    self.status["conversations_since_last_train"] = 0
                    self.status["last_training"] = datetime.now().isoformat()
                    self.status["best_model_path"] = str(adapter_path)
                    
                    # Track model history
                    if "model_history" not in self.status:
                        self.status["model_history"] = []
                    self.status["model_history"].append({
                        "cycle": self.status["training_cycles"],
                        "timestamp": datetime.now().isoformat(),
                        "path": str(adapter_path),
                        "conversations_used": self.status["total_conversations"]
                    })
                    
                    print(f"📊 Cycle #{self.status['training_cycles']} metrics:")
                    print(f"   Total conversations trained: {self.status['total_conversations']}")
                    print(f"   Model path: {adapter_path}")
                else:
                    print("⚠️ Training completed but adapter not found")
                    return False
                
                self.save_status()
                return True
            else:
                print(f"\n❌ Training failed with return code {result.returncode}")
                print(f"Error: {result.stderr[:500]}")
                return False
                
        except subprocess.TimeoutExpired:
            print("\n⏱️ Training timed out after 1 hour")
            return False
        except Exception as e:
            print(f"\n❌ Training error: {e}")
            return False
    
    def run_learning_cycle(self, min_conversations: int = 50, max_samples: int = 500, epochs: int = 3):
        """Run one complete learning cycle"""
        print(f"\n{'='*70}")
        print(f"SELF-LEARNING CHAT - Learning Cycle")
        print(f"{'='*70}")
        print(f"Status: {self.status['training_cycles']} cycles completed")
        print(f"Total conversations: {self.status['total_conversations']}")
        print(f"New conversations: {self.status['conversations_since_last_train']}")
        
        if self.status["best_model_path"]:
            print(f"Current model: {self.status['best_model_path']}")
        
        print(f"\n{'='*70}\n")
        
        # Step 1: Collect conversations
        print("📚 Collecting conversations from logs...")
        new_convs = self.collect_conversations()
        
        # Step 2: Check if training needed
        if self.status["conversations_since_last_train"] < min_conversations:
            print(f"\n⏸️ Not enough conversations for training yet")
            print(f"   Current: {self.status['conversations_since_last_train']}")
            print(f"   Required: {min_conversations}")
            return False
        
        # Step 3: Train model
        print(f"\n🎓 Training new model...")
        success = self.train_model(min_conversations=min_conversations, max_samples=max_samples, epochs=epochs)
        
        if success:
            print(f"\n✅ Learning cycle completed successfully!")
            print(f"   Total cycles: {self.status['training_cycles']}")
            print(f"   Latest model: {self.status['best_model_path']}")
            
            # Auto-deploy: symlink latest model to default location
            try:
                default_adapter = self.repo_root / "data_out" / "lora_training" / "lora_adapter"
                latest_adapter = Path(self.status['best_model_path'])
                
                if latest_adapter.exists():
                    # Remove old symlink/dir if exists
                    if default_adapter.exists() or default_adapter.is_symlink():
                        if default_adapter.is_symlink():
                            default_adapter.unlink()
                        else:
                            import shutil
                            shutil.rmtree(default_adapter, ignore_errors=True)
                    
                    # Create symlink to latest model
                    try:
                        default_adapter.symlink_to(latest_adapter, target_is_directory=True)
                        print(f"\n🚀 Auto-deployed to: {default_adapter}")
                        print("   Restart chat system to use new model")
                    except OSError:
                        # Symlink failed (no admin rights), copy instead
                        import shutil
                        shutil.copytree(latest_adapter, default_adapter, dirs_exist_ok=True)
                        print(f"\n🚀 Deployed (copied) to: {default_adapter}")
                        print("   Restart chat system to use new model")
            except Exception as deploy_err:
                print(f"⚠️ Auto-deployment failed: {deploy_err}")
        
        return success
    
    def continuous_learning(self, 
                          check_interval_minutes: int = 30,
                          min_conversations: int = 50,
                          max_samples: int = 500,
                          epochs: int = 3):
        """Run continuous learning loop"""
        print(f"\n{'='*70}")
        print(f"SELF-LEARNING CHAT - Continuous Mode")
        print(f"{'='*70}")
        print(f"Check interval: {check_interval_minutes} minutes")
        print(f"Min conversations for training: {min_conversations}")
        print(f"Max training samples: {max_samples}")
        print(f"Training epochs: {epochs}")
        print(f"{'='*70}\n")
        
        try:
            while True:
                self.run_learning_cycle(
                    min_conversations=min_conversations,
                    max_samples=max_samples,
                    epochs=epochs
                )
                
                # Wait for next check
                print(f"\n⏰ Sleeping for {check_interval_minutes} minutes...")
                print(f"   Next check at: {(datetime.now() + timedelta(minutes=check_interval_minutes)).strftime('%H:%M:%S')}")
                time.sleep(check_interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Continuous learning stopped by user")
            self.save_status()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Self-Learning Chat System")
    parser.add_argument("--mode", choices=["single", "continuous"], default="single",
                      help="Run mode: single cycle or continuous learning")
    parser.add_argument("--min-conversations", type=int, default=50,
                      help="Minimum conversations before training (default: 50)")
    parser.add_argument("--max-samples", type=int, default=500,
                      help="Maximum training samples (default: 500)")
    parser.add_argument("--epochs", type=int, default=3,
                      help="Training epochs (default: 3)")
    parser.add_argument("--check-interval", type=int, default=30,
                      help="Minutes between checks in continuous mode (default: 30)")
    parser.add_argument("--status", action="store_true",
                      help="Show current learning status")
    
    args = parser.parse_args()
    
    learner = SelfLearningChat()
    
    if args.status:
        print(f"\n{'='*70}")
        print("SELF-LEARNING CHAT STATUS")
        print(f"{'='*70}")
        print(f"Training cycles completed: {learner.status['training_cycles']}")
        print(f"Total conversations: {learner.status['total_conversations']}")
        print(f"New conversations: {learner.status['conversations_since_last_train']}")
        print(f"Last training: {learner.status.get('last_training', 'Never')}")
        print(f"Best model: {learner.status.get('best_model_path', 'None')}")
        print(f"Learning enabled: {learner.status.get('learning_enabled', True)}")
        print(f"{'='*70}\n")
    elif args.mode == "continuous":
        learner.continuous_learning(
            check_interval_minutes=args.check_interval,
            min_conversations=args.min_conversations,
            max_samples=args.max_samples,
            epochs=args.epochs
        )
    else:
        learner.run_learning_cycle(
            min_conversations=args.min_conversations,
            max_samples=args.max_samples,
            epochs=args.epochs
        )


if __name__ == "__main__":
    main()
