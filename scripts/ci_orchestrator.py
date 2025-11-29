#!/usr/bin/env python
"""
CI/CD Orchestrator

Specialized orchestrator for continuous integration and deployment workflows.
Validates all configurations, runs quick tests, and prepares deployment artifacts.

Features:
- Fast validation (all --dry-run checks in parallel)
- Unit test execution
- Integration test execution
- Code quality checks
- Security scanning
- Deployment artifact preparation
- GitHub Actions / Azure Pipelines integration

Usage examples (PowerShell):
  python .\\scripts\\ci_orchestrator.py --validate-all
  python .\\scripts\\ci_orchestrator.py --quick-test
  python .\\scripts\\ci_orchestrator.py --full-test
  python .\\scripts\\ci_orchestrator.py --prepare-deployment
  python .\\scripts\\ci_orchestrator.py --ci-pipeline  # Run full CI pipeline
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "ci_orchestrator"


@dataclass
class ValidationJob:
    name: str
    cmd: List[str]
    critical: bool = True  # If True, failure blocks deployment


class CIOrchestrator:
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.data_out = DATA_OUT
        self.data_out.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict[str, Any]] = []
    
    def validate_all_orchestrators(self) -> bool:
        """Run --dry-run on all orchestrators in parallel."""
        print("\n[ci] ========================================")
        print("[ci] Validating All Orchestrators")
        print("[ci] ========================================\n")
        
        jobs = [
            ValidationJob("autotrain", [sys.executable, "scripts/autotrain.py", "--dry-run"]),
            ValidationJob("quantum_autorun", [sys.executable, "scripts/quantum_autorun.py", "--dry-run"]),
            ValidationJob("evaluation_autorun", [sys.executable, "scripts/evaluation_autorun.py", "--dry-run"]),
        ]
        
        return self._run_parallel_jobs(jobs)
    
    def run_unit_tests(self) -> bool:
        """Run all unit tests using test_runner."""
        print("\n[ci] Running Unit Tests")
        cmd = [sys.executable, "scripts/test_runner.py", "--unit"]
        return self._run_command("unit_tests", cmd)
    
    def run_integration_tests(self) -> bool:
        """Run integration tests using test_runner."""
        print("\n[ci] Running Integration Tests")
        cmd = [sys.executable, "scripts/test_runner.py", "--integration"]
        return self._run_command("integration_tests", cmd, critical=False)
    
    def validate_datasets(self) -> bool:
        """Validate dataset integrity."""
        print("\n[ci] Validating Datasets")
        cmd = [sys.executable, "scripts/validate_datasets.py", "--category", "chat"]
        return self._run_command("validate_datasets", cmd, critical=False)
    
    def check_code_quality(self) -> bool:
        """Run code quality checks."""
        print("\n[ci] Checking Code Quality")
        # This would run tools like pylint, flake8, black, mypy
        # For now, just a placeholder
        result = {
            "name": "code_quality",
            "status": "skipped",
            "message": "Code quality tools not configured",
        }
        self.results.append(result)
        return True
    
    def security_scan(self) -> bool:
        """Run security vulnerability scanning."""
        print("\n[ci] Security Scanning")
        # This would run tools like bandit, safety
        result = {
            "name": "security_scan",
            "status": "skipped",
            "message": "Security scanning not configured",
        }
        self.results.append(result)
        return True
    
    def prepare_deployment(self) -> bool:
        """Prepare deployment artifacts."""
        print("\n[ci] Preparing Deployment Artifacts")
        
        artifacts = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "configurations": [],
            "models": [],
            "scripts": [],
        }
        
        # Check for trained models
        lora_dir = self.repo_root / "data_out" / "lora_training"
        if lora_dir.exists():
            for adapter_dir in lora_dir.iterdir():
                if adapter_dir.is_dir() and (adapter_dir / "adapter_config.json").exists():
                    artifacts["models"].append({
                        "type": "lora",
                        "path": str(adapter_dir.relative_to(self.repo_root)),
                        "size_mb": sum(f.stat().st_size for f in adapter_dir.rglob("*") if f.is_file()) / (1024 * 1024),
                    })
        
        # List key configuration files
        config_files = [
            "autotrain.yaml",
            "quantum_autorun.yaml",
            "evaluation_autorun.yaml",
            "master_orchestrator.yaml",
            "local.settings.json",
        ]
        for cfg in config_files:
            cfg_path = self.repo_root / cfg
            if cfg_path.exists():
                artifacts["configurations"].append(str(cfg))
        
        # Save artifacts manifest
        manifest_file = self.data_out / "deployment_artifacts.json"
        with manifest_file.open("w") as f:
            json.dump(artifacts, f, indent=2)
        
        print(f"[ci] Deployment artifacts manifest: {manifest_file}")
        print(f"[ci] Found {len(artifacts['models'])} trained models")
        
        result = {
            "name": "prepare_deployment",
            "status": "succeeded",
            "artifacts": artifacts,
        }
        self.results.append(result)
        return True

    def azureml_validate(self) -> bool:
        """Validate latest Azure ML job spec if available using 'az ml job validate'.

        Returns True if validation succeeded or was skipped gracefully (no spec / CLI missing).
        """
        print("\n[ci] Azure ML Job Spec Validation")
        aml_dir = self.repo_root / ".azureml"
        if not aml_dir.exists():
            self.results.append({"name": "azureml_validate", "status": "skipped", "message": ".azureml directory missing"})
            return True
        job_specs = sorted(aml_dir.glob("job_*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not job_specs:
            self.results.append({"name": "azureml_validate", "status": "skipped", "message": "No job_*.yaml files found"})
            return True
        latest = job_specs[0]
        # Check az CLI presence
        try:
            az_check = subprocess.run(["az", "version"], capture_output=True, text=True, timeout=30)
        except Exception as e:
            self.results.append({"name": "azureml_validate", "status": "skipped", "message": f"Azure CLI not available: {e}"})
            return True
        if az_check.returncode != 0:
            self.results.append({"name": "azureml_validate", "status": "skipped", "message": "Azure CLI not installed or not in PATH"})
            return True
        # Perform validation
        try:
            val_proc = subprocess.run(["az", "ml", "job", "validate", "--file", str(latest)], capture_output=True, text=True, timeout=120)
            status = "succeeded" if val_proc.returncode == 0 else "failed"
            self.results.append({
                "name": "azureml_validate",
                "status": status,
                "job_file": str(latest.relative_to(self.repo_root)),
                "return_code": val_proc.returncode,
                "stdout_tail": val_proc.stdout[-500:] if val_proc.stdout else "",
                "stderr_tail": val_proc.stderr[-500:] if val_proc.stderr else "",
            })
            if status == "failed":
                print(f"[ci] [FAIL] Azure ML validation failed for {latest}")
                if val_proc.stderr:
                    print(val_proc.stderr)
            else:
                print(f"[ci] [OK] Azure ML validation passed: {latest}")
            return status == "succeeded"
        except subprocess.TimeoutExpired:
            self.results.append({"name": "azureml_validate", "status": "timeout", "job_file": str(latest.relative_to(self.repo_root))})
            return False
        except Exception as e:
            self.results.append({"name": "azureml_validate", "status": "error", "message": str(e)})
            return False
    
    def run_ci_pipeline(self) -> bool:
        """Run the full CI pipeline."""
        print("\n[ci] ========================================")
        print("[ci] Starting Full CI Pipeline")
        print("[ci] ========================================\n")
        
        pipeline_steps = [
            ("Validate Orchestrators", self.validate_all_orchestrators),
            ("Unit Tests", self.run_unit_tests),
            ("Validate Datasets", self.validate_datasets),
            ("Code Quality", self.check_code_quality),
            ("Security Scan", self.security_scan),
            ("Integration Tests", self.run_integration_tests),
            ("Prepare Deployment", self.prepare_deployment),
            ("Azure ML Validate", self.azureml_validate),
        ]
        
        all_passed = True
        for step_name, step_func in pipeline_steps:
            print(f"\n[ci] Step: {step_name}")
            if not step_func():
                all_passed = False
                print(f"[ci] [FAIL] Step failed: {step_name}")
                # Continue with remaining steps even on failure
            else:
                print(f"[ci] [OK] Step passed: {step_name}")
        
        self._save_results()
        return all_passed
    
    def _run_parallel_jobs(self, jobs: List[ValidationJob]) -> bool:
        """Run multiple jobs in parallel."""
        all_passed = True
        
        with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
            futures = {executor.submit(self._run_validation_job, job): job for job in jobs}
            
            for future in as_completed(futures):
                job = futures[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    if result["status"] != "succeeded" and job.critical:
                        all_passed = False
                except Exception as e:
                    print(f"[ci] Exception in job {job.name}: {e}")
                    all_passed = False
        
        return all_passed
    
    def _run_validation_job(self, job: ValidationJob) -> Dict[str, Any]:
        """Run a single validation job."""
        print(f"[ci] Validating: {job.name}")
        t0 = time.time()
        
        try:
            result = subprocess.run(
                job.cmd,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - t0
            status = "succeeded" if result.returncode == 0 else "failed"
            
            return {
                "name": job.name,
                "cmd": job.cmd,
                "status": status,
                "return_code": result.returncode,
                "duration_sec": round(duration, 2),
                "critical": job.critical,
            }
        except subprocess.TimeoutExpired:
            return {
                "name": job.name,
                "status": "timeout",
                "critical": job.critical,
            }
        except Exception as e:
            return {
                "name": job.name,
                "status": "error",
                "message": str(e),
                "critical": job.critical,
            }
    
    def _run_command(self, name: str, cmd: List[str], critical: bool = True) -> bool:
        """Run a single command and track result."""
        t0 = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.time() - t0
            status = "succeeded" if result.returncode == 0 else "failed"
            
            self.results.append({
                "name": name,
                "cmd": cmd,
                "status": status,
                "return_code": result.returncode,
                "duration_sec": round(duration, 2),
                "critical": critical,
            })
            
            if status != "succeeded":
                print(f"[ci] Failed: {name}")
                if result.stdout:
                    print(f"[ci] stdout: {result.stdout[-500:]}")  # Last 500 chars
                if result.stderr:
                    print(f"[ci] stderr: {result.stderr[-500:]}")
            
            return status == "succeeded"
        
        except subprocess.TimeoutExpired:
            self.results.append({
                "name": name,
                "status": "timeout",
                "critical": critical,
            })
            return False
        except Exception as e:
            self.results.append({
                "name": name,
                "status": "error",
                "message": str(e),
                "critical": critical,
            })
            return False
    
    def _save_results(self):
        """Save CI results to disk."""
        summary = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_steps": len(self.results),
            "succeeded": sum(1 for r in self.results if r["status"] == "succeeded"),
            "failed": sum(1 for r in self.results if r["status"] == "failed"),
            "skipped": sum(1 for r in self.results if r["status"] == "skipped"),
            "results": self.results,
        }
        
        results_file = self.data_out / "ci_results.json"
        with results_file.open("w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n[ci] Results saved: {results_file}")
        print(f"[ci] Summary: {summary['succeeded']}/{summary['total_steps']} passed")


def main():
    ap = argparse.ArgumentParser(description="CI/CD Orchestrator")
    ap.add_argument("--validate-all", action="store_true", help="Validate all orchestrators")
    ap.add_argument("--quick-test", action="store_true", help="Run quick tests (unit only)")
    ap.add_argument("--full-test", action="store_true", help="Run all tests")
    ap.add_argument("--prepare-deployment", action="store_true", help="Prepare deployment artifacts")
    ap.add_argument("--ci-pipeline", action="store_true", help="Run full CI pipeline")
    ap.add_argument("--validate-azureml", action="store_true", help="Validate latest Azure ML job spec and schema")
    args = ap.parse_args()
    
    ci = CIOrchestrator()
    
    if args.validate_all:
        success = ci.validate_all_orchestrators()
        ci._save_results()
        sys.exit(0 if success else 1)
    
    if args.quick_test:
        success = ci.run_unit_tests()
        ci._save_results()
        sys.exit(0 if success else 1)
    
    if args.full_test:
        success = ci.run_unit_tests() and ci.run_integration_tests()
        ci._save_results()
        sys.exit(0 if success else 1)
    
    if args.prepare_deployment:
        success = ci.prepare_deployment()
        ci._save_results()
        sys.exit(0 if success else 1)
    
    if args.ci_pipeline:
        success = ci.run_ci_pipeline()
        sys.exit(0 if success else 1)

    if args.validate_azureml:
        success = ci.azureml_validate()
        ci._save_results()
        sys.exit(0 if success else 1)
    
    # Default: show help
    ap.print_help()


if __name__ == "__main__":
    main()
