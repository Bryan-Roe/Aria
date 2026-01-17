"""
Autonomous AI Training Orchestrator
Automatically manages learning cycles, data collection, and model optimization
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import subprocess
import sys
import multiprocessing
try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_out/autonomous_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutonomousTrainingOrchestrator:
    """Manages autonomous AI training, data collection, and optimization"""
    
    def __init__(self, config_path: str = "config/autonomous_training.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.status_file = Path("data_out/autonomous_training_status.json")
        self.results_dir = Path("data_out/autonomous_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.scaling_mode = self.config.get("scaling", {}).get("mode", "multiprocessing")
        self.max_workers = self.config.get("scaling", {}).get("max_workers", None)
        self.batch_size = self.config.get("scaling", {}).get("batch_size", 100)
        self.resource_limits = self.config.get("scaling", {}).get("resource_limits", {})
        
        self.status = {
            "started_at": datetime.now().isoformat(),
            "cycles_completed": 0,
            "total_datasets_trained": 0,
            "best_accuracy": 0.0,
            "current_phase": "initialization",
            "active_tasks": [],
            "completed_tasks": [],
            "dataset_inventory": {},
            "performance_history": []
        }
        
    def load_config(self) -> dict:
        """Load configuration from YAML file"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            default_config = {
                "autonomous_mode": {
                    "enabled": True,
                    "continuous": True,
                    "cycle_interval_minutes": 60,
                    "max_cycles": 0  # 0 = infinite
                },
                "data_collection": {
                    "auto_discover": True,
                    "min_datasets": 500,
                    "quality_threshold": 50,
                    "categories": ["quantum", "chat", "vision"],
                    "sources": ["openml", "huggingface", "kaggle"],
                    "parallel_downloads": 10
                },
                "training": {
                    "auto_train": True,
                    "epochs_progression": [25, 50, 100, 200],
                    "workers": 20,
                    "min_accuracy_threshold": 0.75,
                    "adaptive_epochs": True,
                    "checkpoint_frequency": 10
                },
                "optimization": {
                    "auto_tune": True,
                    "hyperparameter_search": True,
                    "architecture_evolution": False,
                    "pruning_enabled": False
                },
                "monitoring": {
                    "track_metrics": True,
                    "alert_on_degradation": True,
                    "performance_threshold": 0.70
                },
                "deployment": {
                    "auto_deploy_best": False,
                    "min_accuracy_for_deployment": 0.90,
                    "azure_quantum_enabled": False
                }
            }
            
            # Save default config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            return default_config
    
    def save_status(self):
        """Save current status to JSON file"""
        with open(self.status_file, 'w') as f:
            json.dump(self.status, f, indent=2)
    
    async def discover_datasets(self) -> Dict[str, int]:
        """Automatically discover and catalog available datasets"""
        logger.info("🔍 Starting autonomous dataset discovery...")
        self.status["current_phase"] = "data_discovery"
        self.save_status()
        
        discovered = {}
        
        # Scan local directories
        for category in self.config["data_collection"]["categories"]:
            dataset_dir = Path(f"datasets/{category}")
            if dataset_dir.exists():
                csv_files = list(dataset_dir.glob("*.csv"))
                jsonl_files = list(dataset_dir.glob("*.jsonl"))
                discovered[category] = len(csv_files) + len(jsonl_files)
                logger.info(f"  Found {discovered[category]} datasets in {category}")
        
        # Check massive quantum datasets
        massive_dir = Path("datasets/massive_quantum")
        if massive_dir.exists():
            massive_count = len(list(massive_dir.glob("*.csv")))
            discovered["massive_quantum"] = massive_count
            logger.info(f"  Found {massive_count} datasets in massive_quantum")
        
        total = sum(discovered.values())
        logger.info(f"✅ Total datasets discovered: {total}")
        
        self.status["dataset_inventory"] = discovered
        self.status["total_datasets_available"] = total
        self.save_status()
        
        return discovered
    
    async def download_new_datasets(self, target_count: int = 100) -> int:
        """Automatically download new datasets if below threshold"""
        logger.info(f"📥 Starting autonomous data collection (target: {target_count})...")
        self.status["current_phase"] = "data_collection"
        self.save_status()
        
        current_count = self.status.get("total_datasets_available", 0)
        
        if current_count >= self.config["data_collection"]["min_datasets"]:
            logger.info(f"  Dataset threshold met ({current_count} >= {self.config['data_collection']['min_datasets']})")
            return 0
        
        needed = target_count - current_count
        logger.info(f"  Need to download {needed} more datasets")
        
        # Run parallel dataset download
        download_script = Path("scripts/massive_dataset_expansion.py")
        if download_script.exists():
            try:
                cmd = [
                    sys.executable,
                    str(download_script),
                    "--start-batch", str(current_count),
                    "--end-batch", str(current_count + needed),
                    "--quality-threshold", str(self.config["data_collection"]["quality_threshold"])
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"✅ Successfully downloaded {needed} new datasets")
                    return needed
                else:
                    logger.error(f"❌ Dataset download failed: {stderr.decode()}")
                    return 0
                    
            except Exception as e:
                logger.error(f"❌ Error downloading datasets: {e}")
                return 0
        
        return 0
    
    async def select_optimal_epochs(self, dataset_count: int, cycle_number: int) -> int:
        """Intelligently select epoch count based on cycle and performance history"""
        if not self.config["training"]["adaptive_epochs"]:
            return self.config["training"]["epochs_progression"][0]
        
        progression = self.config["training"]["epochs_progression"]
        
        # Progressive training: increase epochs with each cycle
        epoch_index = min(cycle_number, len(progression) - 1)
        selected_epochs = progression[epoch_index]
        
        # Adjust based on recent performance
        if self.status["performance_history"]:
            recent_accuracy = self.status["performance_history"][-1].get("mean_accuracy", 0)
            
            # If accuracy is low, use more epochs
            if recent_accuracy < 0.70 and epoch_index < len(progression) - 1:
                selected_epochs = progression[epoch_index + 1]
                logger.info(f"  Increasing epochs to {selected_epochs} due to low accuracy ({recent_accuracy:.2%})")
            
            # If accuracy plateaued, try even more epochs
            if len(self.status["performance_history"]) >= 2:
                prev_accuracy = self.status["performance_history"][-2].get("mean_accuracy", 0)
                improvement = recent_accuracy - prev_accuracy
                
                if 0 < improvement < 0.01 and epoch_index < len(progression) - 1:
                    selected_epochs = progression[min(epoch_index + 2, len(progression) - 1)]
                    logger.info(f"  Boosting epochs to {selected_epochs} due to plateau")
        
        return selected_epochs
    
    async def train_cycle(self, epochs: int) -> Dict:
        """Execute a scalable training cycle"""
        logger.info(f"🚀 Starting training cycle with {epochs} epochs...")
        self.status["current_phase"] = "training"
        self.status["active_tasks"].append({
            "type": "training",
            "epochs": epochs,
            "started_at": datetime.now().isoformat()
        })
        self.save_status()

        benchmark_script = Path("scripts/distributed_benchmark.py")
        datasets_dir = Path("datasets/massive_quantum")

        if not benchmark_script.exists():
            logger.error("Distributed benchmark script not found")
            return {"success": False, "error": "Script not found"}

        if not datasets_dir.exists() or not list(datasets_dir.glob("*.csv")):
            logger.error("No datasets found for training")
            return {"success": False, "error": "No datasets"}

        # Determine worker count
        cpu_count = multiprocessing.cpu_count()
        max_workers = self.max_workers or min(cpu_count, self.config["training"]["workers"])
        logger.info(f"  Using {max_workers} workers (CPU count: {cpu_count})")

        # Run distributed benchmark (single invocation, handles batching internally)
        try:
            cmd = [
                sys.executable,
                str(benchmark_script),
                "--datasets-dir", str(datasets_dir),
                "--workers", str(max_workers),
                "--epochs", str(epochs)
            ]
            
            logger.info(f"  Executing: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Parse results
                results_file = Path("data_out/distributed_benchmark/distributed_results.json")
                if results_file.exists():
                    with open(results_file) as f:
                        results = json.load(f)
                    
                    logger.info(f"Training cycle completed successfully")
                    logger.info(f"  Mean accuracy: {results.get('mean_accuracy', 0):.2%}")
                    logger.info(f"  Datasets trained: {results.get('successful_count', 0)}")
                    
                    return {
                        "success": True,
                        "results": results,
                        "epochs": epochs,
                        "completed_at": datetime.now().isoformat()
                    }
                else:
                    logger.warning("Training completed but results file not found")
                    return {"success": True, "warning": "No results file"}
            else:
                logger.error(f"Training failed: {stderr.decode()}")
                return {"success": False, "error": stderr.decode()}
                
        except Exception as e:
            logger.error(f"Training cycle error: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_performance(self, results: Dict):
        """Analyze training results and update status"""
        logger.info("📊 Analyzing performance...")
        
        if not results.get("success"):
            return
        
        result_data = results.get("results", {})
        
        performance_record = {
            "timestamp": datetime.now().isoformat(),
            "epochs": results.get("epochs", 0),
            "mean_accuracy": result_data.get("mean_accuracy", 0),
            "median_accuracy": result_data.get("median_accuracy", 0),
            "max_accuracy": result_data.get("max_accuracy", 0),
            "successful_count": result_data.get("successful_count", 0),
            "failed_count": result_data.get("failed_count", 0),
            "exceptional_models": result_data.get("performance_tiers", {}).get("exceptional", 0),
            "excellent_models": result_data.get("performance_tiers", {}).get("excellent", 0)
        }
        
        self.status["performance_history"].append(performance_record)
        
        # Update best accuracy
        if performance_record["mean_accuracy"] > self.status["best_accuracy"]:
            self.status["best_accuracy"] = performance_record["mean_accuracy"]
            logger.info(f"🏆 New best accuracy: {performance_record['mean_accuracy']:.2%}")
        
        # Check for performance degradation
        if self.config["monitoring"]["alert_on_degradation"] and len(self.status["performance_history"]) >= 2:
            prev = self.status["performance_history"][-2]["mean_accuracy"]
            current = performance_record["mean_accuracy"]
            
            if current < prev - 0.05:  # 5% degradation
                logger.warning(f"⚠️ Performance degradation detected: {prev:.2%} → {current:.2%}")
        
        self.save_status()
    
    async def optimization_cycle(self):
        """Run optimization and hyperparameter tuning"""
        if not self.config["optimization"]["auto_tune"]:
            return
        
        logger.info("⚙️ Running optimization cycle...")
        self.status["current_phase"] = "optimization"
        self.save_status()
        
        # Placeholder for future optimization logic
        # Could include:
        # - Hyperparameter tuning
        # - Architecture search
        # - Pruning and quantization
        # - Model ensemble creation
        
        logger.info("  Optimization cycle completed")
    
    async def deployment_cycle(self):
        """Deploy best models if criteria met"""
        if not self.config["deployment"]["auto_deploy_best"]:
            return
        
        if self.status["best_accuracy"] < self.config["deployment"]["min_accuracy_for_deployment"]:
            logger.info(f"  Skipping deployment (accuracy {self.status['best_accuracy']:.2%} < {self.config['deployment']['min_accuracy_for_deployment']:.2%})")
            return
        
        logger.info("🚀 Starting deployment cycle...")
        self.status["current_phase"] = "deployment"
        self.save_status()
        
        # Placeholder for deployment logic
        # Could include:
        # - Azure Quantum deployment
        # - Model API deployment
        # - Edge device deployment
        
        logger.info("  Deployment cycle completed")
    
    async def run_quantum_llm_training(self, cycle_number: int):
        """Execute quantum-enhanced LLM training cycle"""
        if not self.config.get("quantum_llm", {}).get("enabled", False):
            return
        
        logger.info("⚛️ Starting quantum-enhanced LLM training...")
        self.status["current_phase"] = "quantum_llm_training"
        self.save_status()
        
        quantum_script = Path("scripts/quantum_llm_trainer.py")
        if not quantum_script.exists():
            logger.warning("Quantum LLM trainer script not found, skipping")
            return
        
        try:
            # Check if it's time for quantum LLM training
            interval_minutes = self.config.get("quantum_llm", {}).get("training_interval_minutes", 60)
            last_quantum_cycle = self.status.get("last_quantum_llm_cycle", 0)
            
            # Run quantum training every N cycles based on interval
            cycles_per_quantum = max(1, interval_minutes // self.config["autonomous_mode"]["cycle_interval_minutes"])
            
            if (cycle_number - last_quantum_cycle) >= cycles_per_quantum:
                config_file = self.config.get("quantum_llm", {}).get("config_file", "config/quantum_llm_config.yaml")
                
                cmd = [
                    sys.executable,
                    str(quantum_script),
                    "--config", config_file,
                    "--interval", "0"  # Single run, orchestrator handles timing
                ]
                
                logger.info(f"  Executing: {' '.join(cmd)}")
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Set timeout for quantum training (10 minutes max)
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=600
                    )
                    
                    if process.returncode == 0:
                        logger.info("✅ Quantum LLM training completed successfully")
                        self.status["last_quantum_llm_cycle"] = cycle_number
                        self.status["quantum_llm_last_run"] = datetime.now().isoformat()
                    else:
                        logger.warning(f"⚠️ Quantum LLM training failed: {stderr.decode()}")
                
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Quantum LLM training timed out, killing process")
                    process.kill()
                    await process.wait()
        
        except Exception as e:
            logger.error(f"❌ Error in quantum LLM training: {e}")
    
    async def run_single_cycle(self, cycle_number: int):
        """Execute one complete autonomous cycle"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔄 AUTONOMOUS CYCLE #{cycle_number}")
        logger.info(f"{'='*80}\n")
        
        cycle_start = time.time()
        
        # 1. Discover datasets
        await self.discover_datasets()
        
        # 2. Download more if needed
        if self.config["data_collection"]["auto_discover"]:
            await self.download_new_datasets()
        
        # 3. Select optimal training parameters
        epochs = await self.select_optimal_epochs(
            self.status.get("total_datasets_available", 0),
            cycle_number
        )
        
        # 4. Execute training
        results = await self.train_cycle(epochs)
        
        # 5. Analyze performance
        await self.analyze_performance(results)
        
        # 6. Run quantum-enhanced LLM training (NEW)
        await self.run_quantum_llm_training(cycle_number)
        
        # 7. Run optimization
        if self.config["optimization"]["auto_tune"]:
            await self.optimization_cycle()
        
        # 8. Deploy if ready
        if self.config["deployment"]["auto_deploy_best"]:
            await self.deployment_cycle()
        
        # Update status
        self.status["cycles_completed"] = cycle_number
        self.status["last_cycle_duration_seconds"] = time.time() - cycle_start
        self.status["last_cycle_completed_at"] = datetime.now().isoformat()
        self.save_status()
        
        logger.info(f"\n✅ Cycle #{cycle_number} completed in {self.status['last_cycle_duration_seconds']:.1f}s")
        logger.info(f"   Best accuracy so far: {self.status['best_accuracy']:.2%}")
        logger.info(f"   Total datasets: {self.status.get('total_datasets_available', 0)}\n")
    
    async def run_continuous(self):
        """Run continuous autonomous training"""
        logger.info("🤖 Starting Autonomous Training Orchestrator (Continuous Mode)")
        logger.info(f"   Configuration: {self.config_path}")
        logger.info(f"   Status file: {self.status_file}")
        logger.info(f"   Cycle interval: {self.config['autonomous_mode']['cycle_interval_minutes']} minutes")
        
        cycle_number = 1
        max_cycles = self.config["autonomous_mode"]["max_cycles"]
        
        try:
            while True:
                # Check if we've reached max cycles
                if max_cycles > 0 and cycle_number > max_cycles:
                    logger.info(f"🏁 Reached maximum cycles ({max_cycles}). Stopping.")
                    break
                
                # Run cycle
                await self.run_single_cycle(cycle_number)
                
                cycle_number += 1
                
                # Wait for next cycle
                if self.config["autonomous_mode"]["continuous"]:
                    wait_minutes = self.config["autonomous_mode"]["cycle_interval_minutes"]
                    logger.info(f"⏳ Waiting {wait_minutes} minutes until next cycle...")
                    await asyncio.sleep(wait_minutes * 60)
                else:
                    logger.info("🏁 Single cycle mode - stopping.")
                    break
                    
        except KeyboardInterrupt:
            logger.info("\n\n⚠️ Received interrupt signal. Shutting down gracefully...")
            self.status["current_phase"] = "stopped"
            self.status["stopped_at"] = datetime.now().isoformat()
            self.save_status()
        
        except Exception as e:
            logger.error(f"\n\n❌ Fatal error in autonomous orchestrator: {e}")
            self.status["current_phase"] = "error"
            self.status["error"] = str(e)
            self.save_status()
            raise
    
    async def run_once(self):
        """Run a single autonomous cycle"""
        logger.info("🤖 Starting Autonomous Training Orchestrator (Single Cycle)")
        await self.run_single_cycle(1)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous AI Training Orchestrator")
    parser.add_argument("--config", default="config/autonomous_training.yaml",
                       help="Path to configuration file")
    parser.add_argument("--once", action="store_true",
                       help="Run single cycle and exit")
    parser.add_argument("--status", action="store_true",
                       help="Show current status and exit")
    
    args = parser.parse_args()
    
    orchestrator = AutonomousTrainingOrchestrator(args.config)
    
    if args.status:
        # Show status
        print("\n" + "="*80)
        print("AUTONOMOUS TRAINING STATUS")
        print("="*80)
        print(json.dumps(orchestrator.status, indent=2))
        return
    
    if args.once:
        await orchestrator.run_once()
    else:
        await orchestrator.run_continuous()


if __name__ == "__main__":
    asyncio.run(main())
