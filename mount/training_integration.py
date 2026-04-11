"""
Training Integration Module
Interfaces with LoRA training and orchestration systems
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class TrainingIntegration:
    """Integration layer for training operations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.workspace_root = Path(config["paths"]["workspace_root"]).resolve()
        self.phi_path = Path(config["paths"]["phi_training"]).resolve()
        self.scripts_path = Path(config["paths"]["scripts"]).resolve()
        self.output_dir = Path(config["paths"]["data_out"]).resolve()

    async def get_status(self) -> Dict[str, Any]:
        """Get current training system status"""
        return {
            "enabled": self.config["training"]["enabled"],
            "orchestrators": {
                "autotrain": self._get_autotrain_status(),
                "quantum_autorun": self._get_quantum_autorun_status(),
            },
            "lora_adapter": self._check_lora_adapter(),
            "recent_trainings": self._get_recent_trainings(),
        }

    def _get_autotrain_status(self) -> Dict[str, Any]:
        """Get AutoTrain orchestrator status"""
        config_file = self.workspace_root / "autotrain.yaml"
        status_file = self.output_dir / "autotrain" / "status.json"

        status = {
            "config_exists": config_file.exists(),
            "status_file": None,
            "jobs": [],
        }

        if status_file.exists():
            try:
                with open(status_file) as f:
                    status_data = json.load(f)
                    status["status_file"] = str(status_file)
                    status["jobs"] = status_data.get("jobs", {})
                    status["last_run"] = status_data.get("timestamp")
            except Exception:
                pass

        return status

    def _get_quantum_autorun_status(self) -> Dict[str, Any]:
        """Get Quantum AutoRun orchestrator status"""
        config_file = self.workspace_root / "quantum_autorun.yaml"
        status_file = self.output_dir / "quantum_autorun" / "status.json"

        status = {
            "config_exists": config_file.exists(),
            "status_file": None,
            "jobs": [],
        }

        if status_file.exists():
            try:
                with open(status_file) as f:
                    status_data = json.load(f)
                    status["status_file"] = str(status_file)
                    status["jobs"] = status_data.get("jobs", {})
                    status["last_run"] = status_data.get("timestamp")
            except Exception:
                pass

        return status

    def _check_lora_adapter(self) -> Dict[str, Any]:
        """Check if LoRA adapter is available"""
        adapter_dir = self.output_dir / "lora_training" / "lora_adapter"
        config_file = adapter_dir / "adapter_config.json"

        adapter_info = {
            "available": config_file.exists(),
            "path": str(adapter_dir) if config_file.exists() else None,
        }

        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    adapter_info["rank"] = config.get("r")
                    adapter_info["target_modules"] = config.get("target_modules")
                    adapter_info["model"] = config.get("base_model_name_or_path")
            except Exception:
                pass

        return adapter_info

    def _get_recent_trainings(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent training runs"""
        trainings = []
        lora_output = self.output_dir / "lora_training"

        if not lora_output.exists():
            return trainings

        # Look for training logs and checkpoints
        for run_dir in sorted(
            lora_output.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        )[:limit]:
            if run_dir.is_dir():
                trainings.append(
                    {
                        "name": run_dir.name,
                        "path": str(run_dir),
                        "timestamp": run_dir.stat().st_mtime,
                        "has_adapter": (run_dir / "adapter_config.json").exists(),
                    }
                )

        return trainings

    async def run_autotrain(
        self, job_name: Optional[str] = None, dry_run: bool = False
    ) -> Dict[str, Any]:
        """Run AutoTrain orchestrator"""
        try:
            autotrain_script = self.scripts_path / "autotrain.py"

            cmd = [sys.executable, str(autotrain_script)]
            if dry_run:
                cmd.append("--dry-run")
            if job_name:
                cmd.extend(["--job", job_name])

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.workspace_root)
            )

            return {
                "success": result.returncode == 0,
                "job_name": job_name or "all",
                "dry_run": dry_run,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_autotrain_jobs(self) -> List[str]:
        """List all configured AutoTrain jobs"""
        try:
            autotrain_script = self.scripts_path / "autotrain.py"

            result = subprocess.run(
                [sys.executable, str(autotrain_script), "--list"],
                capture_output=True,
                text=True,
                cwd=str(self.workspace_root),
            )

            if result.returncode == 0:
                # Parse job names from output
                lines = result.stdout.strip().split("\n")
                jobs = [
                    line.strip()
                    for line in lines
                    if line.strip() and not line.startswith("-")
                ]
                return jobs
            return []
        except Exception:
            return []

    async def train_lora(
        self,
        dataset: str,
        max_train_samples: int = 64,
        max_eval_samples: int = 16,
        epochs: int = 1,
    ) -> Dict[str, Any]:
        """Run LoRA training directly"""
        try:
            train_script = self.phi_path / "scripts" / "train_lora.py"
            config_file = self.phi_path / "lora" / "lora.yaml"

            cmd = [
                sys.executable,
                str(train_script),
                "--dataset",
                dataset,
                "--config",
                str(config_file),
                "--max-train-samples",
                str(max_train_samples),
                "--max-eval-samples",
                str(max_eval_samples),
                "--epochs",
                str(epochs),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.phi_path)
            )

            return {
                "success": result.returncode == 0,
                "dataset": dataset,
                "samples": max_train_samples,
                "epochs": epochs,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_datasets(self) -> Dict[str, List[str]]:
        """List available training datasets"""
        datasets_root = self.workspace_root / "datasets"

        result = {"quantum": [], "chat": [], "vision": []}

        # Quantum datasets (CSV)
        quantum_dir = datasets_root / "quantum"
        if quantum_dir.exists():
            result["quantum"] = [f.stem for f in quantum_dir.glob("*.csv")]

        # Chat datasets (JSONL directories)
        chat_dir = datasets_root / "chat"
        if chat_dir.exists():
            result["chat"] = [d.name for d in chat_dir.iterdir() if d.is_dir()]

        # Vision datasets
        vision_dir = datasets_root / "vision"
        if vision_dir.exists():
            result["vision"] = [d.name for d in vision_dir.iterdir() if d.is_dir()]

        return result

    async def get_training_metrics(self, run_name: str) -> Dict[str, Any]:
        """Get metrics for a specific training run"""
        run_dir = self.output_dir / "lora_training" / run_name

        if not run_dir.exists():
            return {"error": "Training run not found"}

        metrics = {
            "run_name": run_name,
            "path": str(run_dir),
            "has_adapter": (run_dir / "adapter_config.json").exists(),
            "checkpoints": [],
        }

        # Look for checkpoint directories
        for checkpoint in run_dir.glob("checkpoint-*"):
            if checkpoint.is_dir():
                metrics["checkpoints"].append(checkpoint.name)

        return metrics
