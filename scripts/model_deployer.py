#!/usr/bin/env python
"""
Model Deployer

Automatically deploy trained models based on quality gates and performance metrics.

Features:
- Quality gate validation (accuracy, loss thresholds)
- Model scoring and ranking
- Deployment strategies (canary, blue-green, rolling)
- Rollback on failure
- Version tracking
- Model registry integration

Usage examples (PowerShell):
  python .\\scripts\\model_deployer.py --scan                    # Scan for deployable models
  python .\\scripts\\model_deployer.py --deploy best --strategy canary
  python .\\scripts\\model_deployer.py --status                  # Show deployment status
  python .\\scripts\\model_deployer.py --rollback <version>      # Rollback to version
"""

from __future__ import annotations

import argparse
import json
import shutil
import smtplib
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out"
DEPLOY_DIR = REPO_ROOT / "deployed_models"
REGISTRY_FILE = DEPLOY_DIR / "model_registry.json"


@dataclass
class ModelScore:
    """Scoring metrics for a trained model."""
    model_path: str
    model_type: str
    dataset: str
    trained_at: str
    accuracy: Optional[float] = None
    loss: Optional[float] = None
    f1_score: Optional[float] = None
    validation_accuracy: Optional[float] = None
    total_score: float = 0.0
    passes_quality_gates: bool = False
    quality_issues: List[str] = field(default_factory=list)


@dataclass
class DeploymentRecord:
    """Record of a model deployment."""
    version: str
    model_path: str
    deployed_at: str
    strategy: str
    status: str  # active, canary, rolled_back
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelDeployer:
    """Manages model deployment with quality gates."""
    
    def __init__(self):
        self.deploy_dir = DEPLOY_DIR
        self.deploy_dir.mkdir(parents=True, exist_ok=True)
        self.registry: Dict[str, DeploymentRecord] = {}
        self._load_registry()
        
        # Quality gate thresholds
        self.quality_gates = {
            "min_accuracy": 0.75,
            "max_loss": 0.5,
            "min_f1_score": 0.70,
            "min_validation_accuracy": 0.70,
        }

    def auto_rollback_if_needed(self):
        """Check for failed deploys or bad quality and rollback automatically."""
        # Find last active deployment
        active_versions = [v for v, rec in self.registry.items() if rec.status == "active"]
        if not active_versions:
            return False
        active_version = active_versions[0]
        rec = self.registry[active_version]
        # Check for quality drop
        min_acc = self.quality_gates.get("min_accuracy", 0.75)
        if rec.metadata.get("accuracy", 1.0) < min_acc:
            self.rollback_to_last_good()
            self.send_notification("Auto-rollback triggered", f"Model {active_version} accuracy dropped below {min_acc}")
            return True
        return False

    def rollback_to_last_good(self):
        """Rollback to last good deployment (highest score, passes quality gates)."""
        valid = [rec for rec in self.registry.values() if rec.status != "active" and rec.score >= 70]
        if not valid:
            self.send_notification("Rollback failed", "No valid previous deployment found.")
            return False
        best = sorted(valid, key=lambda r: r.score, reverse=True)[0]
        self.rollback(best.version)
        return True

    def send_notification(self, subject, body, config=None):
        import yaml
        cfg_path = Path(__file__).resolve().parents[1] / "config" / "notification_config.yaml"
        if cfg_path.exists():
            with open(cfg_path) as f:
                config = yaml.safe_load(f)
        notif_log = Path(config.get('log_file', DATA_OUT / "notifications.log"))
        with open(notif_log, 'a') as f:
            f.write(f"[{datetime.now()}] {subject}: {body}\n")
        if config.get('email_enabled'):
            try:
                msg = EmailMessage()
                msg.set_content(body)
                msg['Subject'] = subject
                msg['From'] = config.get('email_from')
                msg['To'] = config.get('email_to')
                with smtplib.SMTP(config.get('smtp_server', 'localhost')) as s:
                    s.send_message(msg)
            except Exception as e:
                print(f"Email notification failed: {e}")
        if config.get('local_alert'):
            print(f"ALERT: {subject} - {body}")
    
    def _load_registry(self):
        """Load deployment registry from disk."""
        if REGISTRY_FILE.exists():
            with REGISTRY_FILE.open("r") as f:
                data = json.load(f)
                for item in data.get("deployments", []):
                    rec = DeploymentRecord(**item)
                    self.registry[rec.version] = rec
    
    def _save_registry(self):
        """Save deployment registry to disk."""
        data = {
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "deployments": [rec.__dict__ for rec in self.registry.values()],
        }
        with REGISTRY_FILE.open("w") as f:
            json.dump(data, f, indent=2)
    
    def scan_models(self) -> List[ModelScore]:
        """Scan data_out for trained models and score them."""
        models = []
        
        # Scan LoRA training outputs
        lora_dir = DATA_OUT / "lora_training"
        if lora_dir.exists():
            for model_dir in lora_dir.iterdir():
                if model_dir.is_dir() and (model_dir / "adapter_config.json").exists():
                    score = self._score_lora_model(model_dir)
                    if score:
                        models.append(score)
        
        # Scan quantum training outputs
        quantum_dir = DATA_OUT / "quantum_autorun"
        if quantum_dir.exists() and (quantum_dir / "status.json").exists():
            with (quantum_dir / "status.json").open("r") as f:
                status = json.load(f)
                for job in status.get("jobs", []):
                    if job["status"] == "succeeded":
                        score = self._score_quantum_model(job)
                        if score:
                            models.append(score)
        
        # Scan autotrain outputs
        autotrain_dir = DATA_OUT / "autotrain"
        if autotrain_dir.exists() and (autotrain_dir / "status.json").exists():
            with (autotrain_dir / "status.json").open("r") as f:
                status = json.load(f)
                for job in status.get("jobs", []):
                    if job["status"] == "succeeded":
                        score = self._score_autotrain_model(job)
                        if score:
                            models.append(score)
        
        # Apply quality gates
        for model in models:
            model.passes_quality_gates = self._check_quality_gates(model)
        
        return models
    
    def _score_lora_model(self, model_dir: Path) -> Optional[ModelScore]:
        """Score a LoRA model based on training metrics."""
        # Look for training logs or metrics
        score = ModelScore(
            model_path=str(model_dir),
            model_type="lora",
            dataset="unknown",
            trained_at=datetime.fromtimestamp(model_dir.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        
        # Try to extract metrics from logs
        metrics_file = model_dir / "training_metrics.json"
        if metrics_file.exists():
            with metrics_file.open("r") as f:
                metrics = json.load(f)
                score.accuracy = metrics.get("accuracy")
                score.loss = metrics.get("loss")
                score.validation_accuracy = metrics.get("eval_accuracy")
        
        # Calculate total score
        score.total_score = self._calculate_score(score)
        return score
    
    def _score_quantum_model(self, job: Dict) -> Optional[ModelScore]:
        """Score a quantum model based on job results."""
        score = ModelScore(
            model_path=job.get("name", "unknown"),
            model_type="quantum",
            dataset=job.get("preset", "unknown"),
            trained_at=job.get("completed_at", "unknown")
        )
        
        # Extract metrics from job metadata
        if "meta" in job:
            score.accuracy = job["meta"].get("accuracy")
            score.loss = job["meta"].get("loss")
        
        score.total_score = self._calculate_score(score)
        return score
    
    def _score_autotrain_model(self, job: Dict) -> Optional[ModelScore]:
        """Score an autotrain model based on job results."""
        score = ModelScore(
            model_path=job.get("name", "unknown"),
            model_type="autotrain",
            dataset=job.get("dataset", "unknown"),
            trained_at=job.get("completed_at", "unknown")
        )
        
        # Extract metrics from job
        if "meta" in job:
            score.accuracy = job["meta"].get("accuracy")
            score.loss = job["meta"].get("loss")
            score.validation_accuracy = job["meta"].get("validation_accuracy")
        
        score.total_score = self._calculate_score(score)
        return score
    
    def _calculate_score(self, model: ModelScore) -> float:
        """Calculate overall model score (0-100)."""
        score = 0.0
        weights = {"accuracy": 0.4, "loss": 0.3, "validation_accuracy": 0.3}
        
        if model.accuracy is not None:
            score += model.accuracy * 100 * weights["accuracy"]
        
        if model.loss is not None:
            # Lower loss is better (inverse)
            loss_score = max(0, 1.0 - model.loss)
            score += loss_score * 100 * weights["loss"]
        
        if model.validation_accuracy is not None:
            score += model.validation_accuracy * 100 * weights["validation_accuracy"]
        
        return round(score, 2)
    
    def _check_quality_gates(self, model: ModelScore) -> bool:
        """Check if model passes quality gates."""
        issues = []
        
        if model.accuracy is not None and model.accuracy < self.quality_gates["min_accuracy"]:
            issues.append(f"Accuracy {model.accuracy:.3f} below threshold {self.quality_gates['min_accuracy']}")
        
        if model.loss is not None and model.loss > self.quality_gates["max_loss"]:
            issues.append(f"Loss {model.loss:.3f} above threshold {self.quality_gates['max_loss']}")
        
        if model.validation_accuracy is not None and model.validation_accuracy < self.quality_gates["min_validation_accuracy"]:
            issues.append(f"Val accuracy {model.validation_accuracy:.3f} below threshold {self.quality_gates['min_validation_accuracy']}")
        
        model.quality_issues = issues
        return len(issues) == 0
    
    def deploy_model(self, model: ModelScore, strategy: str = "direct") -> Optional[str]:
        """Deploy a model using specified strategy."""
        if not model.passes_quality_gates:
            print(f"[deployer] Model failed quality gates:")
            for issue in model.quality_issues:
                print(f"  - {issue}")
            self.send_notification("Model failed quality gates", f"Model {model.model_path} issues: {model.quality_issues}")
            self.auto_rollback_if_needed()
            return None
            # After deployment, check for auto-rollback
            self.auto_rollback_if_needed()
        
        version = f"v{len(self.registry) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        deploy_path = self.deploy_dir / version
        
        print(f"[deployer] Deploying model: {model.model_path}")
        print(f"[deployer] Version: {version}")
        print(f"[deployer] Strategy: {strategy}")
        print(f"[deployer] Score: {model.total_score}")
        
        # Copy model to deployment directory
        if Path(model.model_path).exists():
            shutil.copytree(model.model_path, deploy_path, dirs_exist_ok=True)
        
        # Create deployment record
        status = "active" if strategy == "direct" else "canary"
        record = DeploymentRecord(
            version=version,
            model_path=str(deploy_path),
            deployed_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            strategy=strategy,
            status=status,
            score=model.total_score,
            metadata={
                "model_type": model.model_type,
                "dataset": model.dataset,
                "accuracy": model.accuracy,
                "loss": model.loss,
            }
        )
        
        # Update registry
        if strategy == "direct":
            # Mark previous deployments as inactive
            for rec in self.registry.values():
                if rec.status == "active":
                    rec.status = "superseded"
        
        self.registry[version] = record
        self._save_registry()
        
        print(f"[deployer] Deployment successful: {version}")
        self.send_notification("Model deployed", f"Model {model.model_path} deployed as {version}")
        return version
    
    def deploy_best(self, strategy: str = "direct") -> Optional[str]:
        """Find and deploy the best model."""
        models = self.scan_models()
        
        # Filter models that pass quality gates
        valid_models = [m for m in models if m.passes_quality_gates]
        
        if not valid_models:
            print("[deployer] No models pass quality gates")
            return None
        
        # Sort by score (descending)
        valid_models.sort(key=lambda m: m.total_score, reverse=True)
        best_model = valid_models[0]
        
        print(f"[deployer] Found best model:")
        print(f"  Path: {best_model.model_path}")
        print(f"  Type: {best_model.model_type}")
        print(f"  Dataset: {best_model.dataset}")
        print(f"  Score: {best_model.total_score}")
        
        return self.deploy_model(best_model, strategy)
    
    def rollback(self, version: str) -> bool:
        """Rollback to a previous deployment."""
        if version not in self.registry:
            print(f"[deployer] Version not found: {version}")
            return False
        
        print(f"[deployer] Rolling back to: {version}")
        
        # Mark current active as rolled_back
        for rec in self.registry.values():
            if rec.status == "active":
                rec.status = "rolled_back"
        
        # Activate target version
        self.registry[version].status = "active"
        self._save_registry()
        
        print(f"[deployer] Rollback successful: {version}")
        self.send_notification("Model rollback", f"Rolled back to {version}")
        return True
    
    def get_status(self) -> Dict:
        """Get deployment status."""
        active = [rec for rec in self.registry.values() if rec.status == "active"]
        canary = [rec for rec in self.registry.values() if rec.status == "canary"]
        
        return {
            "total_deployments": len(self.registry),
            "active_deployments": len(active),
            "canary_deployments": len(canary),
            "active_version": active[0].version if active else None,
            "deployments": [rec.__dict__ for rec in self.registry.values()],
        }


def main():
    ap = argparse.ArgumentParser(description="Model Deployer")
    ap.add_argument("--scan", action="store_true", help="Scan for deployable models")
    ap.add_argument("--deploy", help="Deploy specific model or 'best'")
    ap.add_argument("--strategy", default="direct", choices=["direct", "canary", "blue-green"], help="Deployment strategy")
    ap.add_argument("--rollback", help="Rollback to version")
    ap.add_argument("--status", action="store_true", help="Show deployment status")
    ap.add_argument("--set-quality-gate", nargs=2, metavar=("NAME", "VALUE"), help="Set quality gate threshold")
    args = ap.parse_args()
    
    deployer = ModelDeployer()
    
    if args.set_quality_gate:
        gate_name, gate_value = args.set_quality_gate
        if gate_name in deployer.quality_gates:
            deployer.quality_gates[gate_name] = float(gate_value)
            print(f"[deployer] Set {gate_name} = {gate_value}")
        else:
            print(f"[deployer] Unknown quality gate: {gate_name}")
        return
    
    if args.scan:
        models = deployer.scan_models()
        print(f"\n[deployer] Found {len(models)} trained models:\n")
        
        for i, model in enumerate(models, 1):
            status = "✓ PASS" if model.passes_quality_gates else "✗ FAIL"
            print(f"{i}. {model.model_path}")
            print(f"   Type: {model.model_type} | Dataset: {model.dataset}")
            print(f"   Score: {model.total_score} | Status: {status}")
            if model.accuracy:
                print(f"   Accuracy: {model.accuracy:.3f}")
            if model.loss:
                print(f"   Loss: {model.loss:.3f}")
            if model.quality_issues:
                print(f"   Issues: {', '.join(model.quality_issues)}")
            print()
        return
    
    if args.deploy:
        if args.deploy == "best":
            deployer.deploy_best(args.strategy)
        else:
            # Deploy specific model by path
            models = deployer.scan_models()
            for model in models:
                if args.deploy in model.model_path:
                    deployer.deploy_model(model, args.strategy)
                    break
        return
    
    if args.rollback:
        deployer.rollback(args.rollback)
        return
    
    if args.status:
        status = deployer.get_status()
        print(json.dumps(status, indent=2))
        return
    
    # Default: show help
    ap.print_help()


if __name__ == "__main__":
    main()
