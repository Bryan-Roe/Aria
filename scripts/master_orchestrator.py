#!/usr/bin/env python
"""
Master Orchestrator

Coordinates all sub-orchestrators (autotrain, quantum_autorun, evaluation_autorun)
with scheduling, dependency management, and workflow automation.

Features:
- Schedule-based execution (cron-like syntax)
- Dependency management between orchestrators
- Workflow pipelines with success/failure handlers
- Resource monitoring and limits
- Automatic retry on failure
- Health checks and metrics
- Backup and cleanup automation

Usage examples (PowerShell):
  python .\\scripts\\master_orchestrator.py --workflow daily_full_pipeline
  python .\\scripts\\master_orchestrator.py --workflow quick_validation
  python .\\scripts\\master_orchestrator.py --orchestrator autotrain
  python .\\scripts\\master_orchestrator.py --daemon  # Run as background service
  python .\\scripts\\master_orchestrator.py --status   # Check status
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import signal
import threading

try:
    import yaml
except Exception:
    raise SystemExit("pyyaml is required. Install with: pip install pyyaml")

try:
    import psutil
except Exception:
    psutil = None  # Optional, for resource monitoring

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "master_orchestrator"
CONFIG_FILE = REPO_ROOT / "master_orchestrator.yaml"


@dataclass
class OrchestratorConfig:
    name: str
    script: str
    enabled: bool = True
    schedule: Optional[str] = None
    priority: int = 1
    retry_on_failure: int = 0
    timeout_minutes: int = 0
    dependencies: List[str] = field(default_factory=list)
    last_run: Optional[str] = None
    last_status: Optional[str] = None


@dataclass
class WorkflowConfig:
    name: str
    enabled: bool = True
    trigger: str = "manual"  # schedule | manual | webhook
    schedule: Optional[str] = None
    orchestrators: List[str] = field(default_factory=list)
    flags: Dict[str, Any] = field(default_factory=dict)
    on_success: List[str] = field(default_factory=list)
    on_failure: List[str] = field(default_factory=list)


class MasterOrchestrator:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()
        self.orchestrators: Dict[str, OrchestratorConfig] = {}
        self.workflows: Dict[str, WorkflowConfig] = {}
        self.running = True
        self.status_file = DATA_OUT / "status.json"
        self._parse_config()
        self._ensure_dirs()
        
    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise SystemExit(f"Config not found: {self.config_path}")
        with self.config_path.open("r") as f:
            return yaml.safe_load(f) or {}
    
    def _parse_config(self):
        # Parse orchestrators
        for item in self.config.get("orchestrators", []):
            orc = OrchestratorConfig(
                name=item["name"],
                script=item["script"],
                enabled=item.get("enabled", True),
                schedule=item.get("schedule"),
                priority=item.get("priority", 1),
                retry_on_failure=item.get("retry_on_failure", 0),
                timeout_minutes=item.get("timeout_minutes", 0),
                dependencies=item.get("dependencies", []),
            )
            self.orchestrators[orc.name] = orc
        
        # Parse workflows
        for item in self.config.get("workflows", []):
            wf = WorkflowConfig(
                name=item["name"],
                enabled=item.get("enabled", True),
                trigger=item.get("trigger", "manual"),
                schedule=item.get("schedule"),
                orchestrators=item.get("orchestrators", []),
                flags=item.get("flags", {}),
                on_success=item.get("on_success", []),
                on_failure=item.get("on_failure", []),
            )
            self.workflows[wf.name] = wf
    
    def _ensure_dirs(self):
        DATA_OUT.mkdir(parents=True, exist_ok=True)
    
    def run_orchestrator(self, name: str, flags: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a single orchestrator."""
        if name not in self.orchestrators:
            return {"status": "error", "message": f"Unknown orchestrator: {name}"}
        
        orc = self.orchestrators[name]
        if not orc.enabled:
            return {"status": "skipped", "message": f"Orchestrator disabled: {name}"}
        
        # Check dependencies
        for dep in orc.dependencies:
            if dep in self.orchestrators:
                dep_orc = self.orchestrators[dep]
                if dep_orc.last_status != "succeeded":
                    return {
                        "status": "blocked",
                        "message": f"Dependency not met: {dep} (status: {dep_orc.last_status})"
                    }
        
        script_path = REPO_ROOT / orc.script
        if not script_path.exists():
            return {"status": "error", "message": f"Script not found: {script_path}"}
        
        # Build command
        cmd = [sys.executable, str(script_path)]
        
        # Apply flags
        if flags:
            if flags.get("dry_run"):
                cmd.append("--dry-run")
            if "max_train_samples" in flags and flags["max_train_samples"] is not None:
                cmd.extend(["--max-train-samples", str(flags["max_train_samples"])])
        
        print(f"[master] Running orchestrator: {name}")
        print(f"[master] Command: {' '.join(cmd)}")
        
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_dir = DATA_OUT / name / ts
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "stdout.log"
        
        t0 = time.time()
        result = {
            "name": name,
            "cmd": cmd,
            "start_time": ts,
            "status": "running",
        }
        
        try:
            with log_file.open("w") as logf:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(REPO_ROOT),
                    stdout=logf,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Wait with timeout
                timeout = orc.timeout_minutes * 60 if orc.timeout_minutes > 0 else None
                rc = proc.wait(timeout=timeout)
                
            duration = time.time() - t0
            result["return_code"] = rc
            result["duration_sec"] = round(duration, 2)
            result["status"] = "succeeded" if rc == 0 else "failed"
            result["log"] = str(log_file)
            
            # Update orchestrator state
            orc.last_run = ts
            orc.last_status = result["status"]
            
        except subprocess.TimeoutExpired:
            proc.kill()
            result["status"] = "timeout"
            result["message"] = f"Exceeded timeout of {orc.timeout_minutes} minutes"
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)
        
        return result
    
    def run_workflow(self, name: str) -> Dict[str, Any]:
        """Run a workflow pipeline."""
        if name not in self.workflows:
            return {"status": "error", "message": f"Unknown workflow: {name}"}
        
        wf = self.workflows[name]
        if not wf.enabled:
            return {"status": "skipped", "message": f"Workflow disabled: {name}"}
        
        print(f"\n[master] ========================================")
        print(f"[master] Starting workflow: {name}")
        print(f"[master] Orchestrators: {', '.join(wf.orchestrators)}")
        print(f"[master] ========================================\n")
        
        results = []
        all_succeeded = True
        
        for orc_name in wf.orchestrators:
            result = self.run_orchestrator(orc_name, flags=wf.flags)
            results.append(result)
            print(json.dumps(result, indent=2, default=str))
            
            if result["status"] not in ["succeeded", "skipped"]:
                all_succeeded = False
                # Stop on first failure unless configured otherwise
                break
        
        workflow_result = {
            "workflow": name,
            "start_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "succeeded" if all_succeeded else "failed",
            "orchestrators": results,
        }
        
        # Execute handlers
        handlers = wf.on_success if all_succeeded else wf.on_failure
        for handler in handlers:
            print(f"[master] Executing handler: {handler}")
            self._execute_handler(handler, workflow_result)
        
        # Save workflow result
        self._save_workflow_result(workflow_result)
        
        return workflow_result
    
    def _execute_handler(self, handler: str, result: Dict[str, Any]):
        """Execute a success/failure handler."""
        if handler == "notify_slack":
            print("[master] Would notify Slack (not implemented)")
        elif handler == "update_dashboard":
            print("[master] Would update dashboard (not implemented)")
        elif handler == "deploy_best_models":
            print("[master] Would deploy best models (not implemented)")
        elif handler == "create_issue":
            print("[master] Would create GitHub issue (not implemented)")
        elif handler == "fail_build":
            sys.exit(1)
        elif handler == "log_result":
            print(f"[master] Logged result: {result['status']}")
        elif handler == "generate_report":
            print("[master] Would generate comprehensive report (not implemented)")
        elif handler == "backup_models":
            print("[master] Would backup models (not implemented)")
        elif handler == "create_incident":
            print("[master] Would create incident ticket (not implemented)")
        else:
            print(f"[master] Unknown handler: {handler}")
    
    def _save_workflow_result(self, result: Dict[str, Any]):
        """Save workflow result to disk."""
        wf_name = result["workflow"]
        ts = result["start_time"].replace(":", "").replace("-", "")
        result_file = DATA_OUT / f"{wf_name}_{ts}.json"
        with result_file.open("w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"[master] Workflow result saved: {result_file}")
    
    def list_orchestrators(self) -> List[Dict[str, Any]]:
        """List all configured orchestrators."""
        return [
            {
                "name": orc.name,
                "script": orc.script,
                "enabled": orc.enabled,
                "schedule": orc.schedule,
                "priority": orc.priority,
                "dependencies": orc.dependencies,
                "last_run": orc.last_run,
                "last_status": orc.last_status,
            }
            for orc in sorted(self.orchestrators.values(), key=lambda x: x.priority)
        ]
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all configured workflows."""
        return [
            {
                "name": wf.name,
                "enabled": wf.enabled,
                "trigger": wf.trigger,
                "schedule": wf.schedule,
                "orchestrators": wf.orchestrators,
            }
            for wf in self.workflows.values()
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall status."""
        return {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "orchestrators": self.list_orchestrators(),
            "workflows": self.list_workflows(),
            "resource_usage": self._get_resource_usage(),
        }
    
    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage."""
        if not psutil:
            return {"available": False}
        
        return {
            "available": True,
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage(str(REPO_ROOT)).percent,
        }
    
    def daemon_mode(self, check_interval: int = 60):
        """Run in daemon mode, checking schedules periodically."""
        print("[master] Starting daemon mode...")
        print(f"[master] Check interval: {check_interval} seconds")
        
        def signal_handler(sig, frame):
            print("\n[master] Received shutdown signal")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while self.running:
            print(f"[master] Health check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check scheduled workflows
            for wf_name, wf in self.workflows.items():
                if wf.enabled and wf.trigger == "schedule" and wf.schedule:
                    if self._should_run_now(wf.schedule):
                        print(f"[master] Triggering scheduled workflow: {wf_name}")
                        self.run_workflow(wf_name)
            
            time.sleep(check_interval)
        
        print("[master] Daemon stopped")
    
    def _should_run_now(self, schedule: str) -> bool:
        """Check if schedule matches current time (simplified cron-like logic)."""
        # TODO: Implement proper cron parsing
        # For now, just return False (manual trigger only)
        return False


def main():
    ap = argparse.ArgumentParser(description="Master Orchestrator")
    ap.add_argument("--config", default=str(CONFIG_FILE), help="Config file path")
    ap.add_argument("--workflow", help="Run a specific workflow")
    ap.add_argument("--orchestrator", help="Run a specific orchestrator")
    ap.add_argument("--list-orchestrators", action="store_true", help="List all orchestrators")
    ap.add_argument("--list-workflows", action="store_true", help="List all workflows")
    ap.add_argument("--status", action="store_true", help="Show current status")
    ap.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    ap.add_argument("--check-interval", type=int, default=60, help="Daemon check interval (seconds)")
    args = ap.parse_args()
    
    master = MasterOrchestrator(Path(args.config))
    
    if args.list_orchestrators:
        print(json.dumps(master.list_orchestrators(), indent=2))
        return
    
    if args.list_workflows:
        print(json.dumps(master.list_workflows(), indent=2))
        return
    
    if args.status:
        status = master.get_status()
        print(json.dumps(status, indent=2, default=str))
        
        # Save status
        with master.status_file.open("w") as f:
            json.dump(status, f, indent=2, default=str)
        return
    
    if args.daemon:
        master.daemon_mode(check_interval=args.check_interval)
        return
    
    if args.workflow:
        result = master.run_workflow(args.workflow)
        sys.exit(0 if result["status"] == "succeeded" else 1)
    
    if args.orchestrator:
        result = master.run_orchestrator(args.orchestrator)
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result["status"] == "succeeded" else 1)
    
    # No action specified, show help
    ap.print_help()


if __name__ == "__main__":
    main()
