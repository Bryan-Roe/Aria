"""
Training Integration Module
Interfaces with LoRA training and orchestration systems

Dataset names are validated with a strict allowlist policy before subprocess
invocation. Names must match regex ``^[A-Za-z0-9_.-]+$`` and must not contain
path separators or traversal tokens.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
DATASET_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def _normalize_dataset_name(name: str) -> str:
    """Normalize dataset names for case-insensitive allowlist matching."""
    return name.strip().lower()


def _is_safe_dataset_name(name: str) -> bool:
    """Return True when dataset name is non-path-like and matches safe regex."""
    name_norm = name.strip()
    if any(token in name_norm for token in ("/", "\\", "..")):
        return False
    return bool(DATASET_NAME_PATTERN.fullmatch(name_norm))


def _error_response(code: str, message: str) -> Dict[str, Any]:
    """Return a consistent error payload."""
    return {"success": False, "error": code, "message": message}

_DATASET_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def _normalize_dataset_name(name: str) -> str:
    return name.strip().lower()


def _is_safe_dataset_name(name: str) -> bool:
    name_norm = name.strip()
    if any(token in name_norm for token in ("/", "\\", "..")):
        return False
    return bool(_DATASET_NAME_PATTERN.fullmatch(name_norm))


def _error_response(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    response: Dict[str, Any] = {"success": False, "error": code, "message": message}
    if extra:
        response.update(extra)
    return response


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
                logger.exception("Failed to read autotrain status file")

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
                logger.exception("Failed to read quantum_autorun status file")

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
                logger.exception("Failed to read adapter config")

        return adapter_info

    def _get_recent_trainings(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent training runs"""
        trainings = []
        lora_output = self.output_dir / "lora_training"

        if not lora_output.exists():
            return trainings

        # Look for training logs and checkpoints
        try:
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
        except Exception:
            logger.exception("Failed to list recent trainings")

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
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.workspace_root),
                env={"PATH": os.environ.get("PATH", "")},
            )

            return {
                "success": result.returncode == 0,
                "job_name": job_name or "all",
                "dry_run": dry_run,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            logger.exception("run_autotrain failed")
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
                env={"PATH": os.environ.get("PATH", "")},
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
            logger.exception("list_autotrain_jobs failed")
            return []

    async def train_lora(
        self,
        dataset: str,
        max_train_samples: int = 64,
        max_eval_samples: int = 16,
        epochs: int = 1,
    ) -> Dict[str, Any]:
        """Run LoRA training directly

        Hardening and validation added to prevent uncontrolled command-line and
        path-injection issues. This method validates the dataset against the
        discovered datasets and runs the training script using a safe argument
        list, a restricted environment, and a bounded timeout. Dataset matching
        is case-insensitive via lower-case normalization.
        """
        try:
            # Basic type/format checks
            if not isinstance(dataset, str) or not dataset.strip():
                return _error_response(
                    "invalid_dataset", "Dataset must be a non-empty string."
                )

            # Fetch available datasets (list_datasets uses a thread for FS ops)
            available_datasets = await self.list_datasets()

            # Build allowed map (normalized -> canonical discovered dataset name)
            allowed_dataset_map: Dict[str, str] = {}
            for names in available_datasets.values():
                for name in names:
                    if isinstance(name, str) and _is_safe_dataset_name(name):
                        allowed_dataset_map[_normalize_dataset_name(name)] = name.strip()

            logger.debug(
                "train_lora: allowed dataset names=%s", sorted(allowed_dataset_map.keys())
            )

            if not _is_safe_dataset_name(dataset):
                logger.warning(
                    "train_lora: rejected dataset with disallowed characters: %s",
                    dataset,
                )
                return _error_response(
                    "invalid_dataset",
                    "Dataset name contains disallowed characters or path traversal tokens.",
                )

            dataset_norm = _normalize_dataset_name(dataset)
            dataset_for_cmd = allowed_dataset_map.get(dataset_norm)

            if dataset_for_cmd is None:
                logger.warning("train_lora: dataset not in allowlist: %s", dataset_norm)
                return _error_response(
                    "unknown_dataset",
                    "Dataset not found. Call list_datasets() to see valid names.",
                )

            train_script = self.phi_path / "scripts" / "train_lora.py"
            config_file = self.phi_path / "lora" / "lora.yaml"

            if not train_script.exists():
                logger.error("train_lora: train script missing: %s", train_script)
                return _error_response("training_script_missing", "Training script not found")

            cmd = [
                sys.executable,
                str(train_script),
                "--dataset",
                dataset_for_cmd,
                "--config",
                str(config_file),
                "--max-train-samples",
                str(int(max_train_samples)),
                "--max-eval-samples",
                str(int(max_eval_samples)),
                "--epochs",
                str(int(epochs)),
            ]

            # Restrict environment to a minimal PATH to avoid leaking secrets into child
            env = {"PATH": os.environ.get("PATH", ""), "LANG": "en_US.UTF-8"}

            try:
                # Use a reasonable timeout (2 hours) to prevent runaway processes
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(self.phi_path),
                    env=env,
                    timeout=2 * 60 * 60,
                )
            except subprocess.TimeoutExpired as exc:
                logger.exception("train_lora: training timed out for dataset %s", dataset_norm)
                return {
                    **_error_response("training_timeout", "Training timed out."),
                    "stdout": getattr(exc, "stdout", ""),
                    "stderr": getattr(exc, "stderr", ""),
                }

            return {
                "success": result.returncode == 0,
                "dataset": dataset_norm,
                "samples": int(max_train_samples),
                "epochs": int(epochs),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            logger.exception("train_lora failed")
            return _error_response("training_failed", str(e))

    async def list_datasets(self) -> Dict[str, List[str]]:
        """List available training datasets.

        Filesystem operations are performed in a thread to avoid blocking the event
        loop since Path.glob / iterdir are blocking calls.
        """
        datasets_root = self.workspace_root / "datasets"

        def _scan() -> Dict[str, List[str]]:
            result = {"quantum": [], "chat": [], "vision": []}

            try:
                # Quantum datasets (CSV)
                quantum_dir = datasets_root / "quantum"
                if quantum_dir.exists():
                    result["quantum"] = [f.stem for f in quantum_dir.glob("*.csv") if f.is_file()]

                # Chat datasets (JSONL directories)
                chat_dir = datasets_root / "chat"
                if chat_dir.exists():
                    result["chat"] = [d.name for d in chat_dir.iterdir() if d.is_dir()]

                # Vision datasets
                vision_dir = datasets_root / "vision"
                if vision_dir.exists():
                    result["vision"] = [d.name for d in vision_dir.iterdir() if d.is_dir()]
            except Exception:
                logger.exception("list_datasets: failed during filesystem scan")

            return result

        try:
            return await asyncio.to_thread(_scan)
        except Exception:
            logger.exception("list_datasets failed")
            return {"quantum": [], "chat": [], "vision": []}

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
        try:
            for checkpoint in run_dir.glob("checkpoint-*"):
                if checkpoint.is_dir():
                    metrics["checkpoints"].append(checkpoint.name)
        except Exception:
            logger.exception("get_training_metrics failed for run: %s", run_name)

        return metrics
