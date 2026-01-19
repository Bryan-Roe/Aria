#!/usr/bin/env python
"""Auto Operations Dashboard - Unified CLI View of All Automated Systems

Displays current state of:
- Autonomous training orchestrator
- Master orchestrator schedules
- Training scheduler (nightly/grid)
- Aria automation
- GGUF training pipeline
- Model deployment & promotion
- Scheduled tasks (auto-scheduler)
- CI/CD pipeline status
- Resource utilization

Usage:
  python scripts/monitoring/auto_ops_dashboard.py              # Single-shot view
  python scripts/monitoring/auto_ops_dashboard.py --watch      # Auto-refresh every 5s
  python scripts/monitoring/auto_ops_dashboard.py --compact    # Condensed output
  python scripts/monitoring/auto_ops_dashboard.py --export     # Export to JSON
  python scripts/monitoring/auto_ops_dashboard.py --problems   # Show only issues
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

# Status file paths
AUTONOMOUS_TRAINING_STATUS = REPO_ROOT / "data_out" / "autonomous_training_status.json"
MASTER_ORCHESTRATOR_STATUS = REPO_ROOT / "data_out" / "master_orchestrator" / "status.json"
TRAINING_SCHEDULER_STATUS = REPO_ROOT / "data_out" / "training_scheduler" / "scheduler_state.json"
AUTO_SCHEDULER_STATUS = REPO_ROOT / "data_out" / "auto_scheduler" / "schedule.json"
GGUF_TRAINING_STATUS = REPO_ROOT / "data_out" / "gguf_training" / "training_status.json"
GGUF_SUMMARY = REPO_ROOT / "data_out" / "gguf_training" / "summary.json"
TRAIN_PROMOTE_LATEST = REPO_ROOT / "data_out" / "train_and_promote"
AUTOTRAIN_STATUS = REPO_ROOT / "data_out" / "autotrain" / "status.json"
EVALUATION_STATUS = REPO_ROOT / "data_out" / "evaluation_autorun" / "status.json"
QUANTUM_STATUS = REPO_ROOT / "data_out" / "quantum_autorun" / "status.json"
CI_RESULTS = REPO_ROOT / "data_out" / "ci_orchestrator" / "ci_results.json"
ARIA_LOG = REPO_ROOT / "data_out" / "autonomous_training.log"


@dataclass
class AutoOpStatus:
    """Status for an auto operation"""
    name: str
    category: str  # "learning", "scheduling", "evaluation", "deployment", "ci"
    status: str  # "running", "idle", "scheduled", "error", "unknown"
    cycles_completed: int = 0
    current_task: Optional[str] = None
    progress: float = 0.0  # 0-100
    last_update: Optional[str] = None
    next_trigger: Optional[str] = None
    alerts: List[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []
        if self.metrics is None:
            self.metrics = {}


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load JSON file"""
    if not path.exists():
        return None
    try:
        with path.open("r") as f:
            return json.load(f)
    except Exception:
        return None


def get_latest_train_promote() -> Optional[Dict[str, Any]]:
    """Get the most recent train_and_promote result"""
    if not TRAIN_PROMOTE_LATEST.exists():
        return None
    try:
        files = sorted(TRAIN_PROMOTE_LATEST.glob("pipeline_*.json"), reverse=True)
        if files:
            return load_json(files[0])
    except Exception:
        pass
    return None


def parse_autonomous_training() -> AutoOpStatus:
    """Parse autonomous training orchestrator status"""
    data = load_json(AUTONOMOUS_TRAINING_STATUS)
    if not data:
        return AutoOpStatus(
            name="Autonomous Training",
            category="learning",
            status="unknown",
            alerts=["Status file not found - may not be running"],
        )
    
    cycles = data.get("cycles_completed", 0)
    active_tasks = data.get("active_tasks", [])
    completed_tasks = data.get("completed_tasks", [])
    
    if active_tasks:
        current_task = active_tasks[0].get("type", "unknown")
        status = "running"
    else:
        current_task = None
        status = "idle"
    
    status_obj = AutoOpStatus(
        name="Autonomous Training",
        category="learning",
        status=status,
        cycles_completed=cycles,
        current_task=current_task,
        last_update=data.get("started_at"),
        metrics={
            "best_accuracy": data.get("best_accuracy", 0.0),
            "total_datasets": data.get("total_datasets_available", 0),
            "trained_datasets": data.get("total_datasets_trained", 0),
            "datasets_by_type": data.get("dataset_inventory", {}),
        }
    )
    
    if status == "running" and active_tasks:
        task = active_tasks[0]
        try:
            started = task["started_at"]
            if isinstance(started, str):
                # Parse ISO format datetime
                if "T" in started:
                    if started.endswith("Z"):
                        started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                    elif "+" in started or started.count("-") > 2:
                        started_dt = datetime.fromisoformat(started)
                    else:
                        started_dt = datetime.fromisoformat(started).replace(tzinfo=timezone.utc)
                    
                    elapsed = (datetime.now(timezone.utc) - started_dt).total_seconds()
                    # Rough estimate for progress
                    status_obj.progress = min(100, (elapsed / 1800) * 100) if elapsed < 1800 else 0
        except Exception:
            status_obj.progress = 0
    
    # Check for issues
    if cycles > 100:
        status_obj.alerts.append(f"⚠️  High cycle count ({cycles}) - consider archiving results")
    
    performance = data.get("performance_history", [])
    if len(performance) > 1:
        recent = performance[-1]
        older = performance[-2]
        if recent.get("accuracy", 0) < older.get("accuracy", 1):
            status_obj.alerts.append(f"📉 Accuracy declined from {older.get('accuracy')} to {recent.get('accuracy')}")
    
    return status_obj


def parse_master_orchestrator() -> AutoOpStatus:
    """Parse master orchestrator schedule"""
    data = load_json(MASTER_ORCHESTRATOR_STATUS)
    if not data:
        return AutoOpStatus(
            name="Master Orchestrator",
            category="scheduling",
            status="unknown",
            alerts=["Config not found"],
        )
    
    orchestrators = data.get("orchestrators", [])
    enabled = sum(1 for o in orchestrators if o.get("enabled"))
    
    status_obj = AutoOpStatus(
        name="Master Orchestrator",
        category="scheduling",
        status="active" if enabled > 0 else "disabled",
        metrics={
            "total_orchestrators": len(orchestrators),
            "enabled": enabled,
            "disabled": len(orchestrators) - enabled,
            "workflows": len(data.get("workflows", [])),
        }
    )
    
    # Check resource usage
    resources = data.get("resource_usage", {})
    if resources.get("available"):
        cpu = resources.get("cpu_percent", 0)
        mem = resources.get("memory_percent", 0)
        disk = resources.get("disk_percent", 0)
        
        if cpu > 80:
            status_obj.alerts.append(f"🔴 CPU at {cpu}%")
        if mem > 80:
            status_obj.alerts.append(f"🔴 Memory at {mem}%")
        if disk > 85:
            status_obj.alerts.append(f"🔴 Disk at {disk}%")
    
    status_obj.last_update = data.get("generated_at")
    return status_obj


def parse_training_scheduler() -> AutoOpStatus:
    """Parse training scheduler (nightly/grid)"""
    data = load_json(TRAINING_SCHEDULER_STATUS)
    if not data:
        return AutoOpStatus(
            name="Training Scheduler",
            category="scheduling",
            status="unknown",
        )
    
    jobs = data.get("jobs", [])
    active = sum(1 for j in jobs if j.get("status") in ("running", "pending"))
    completed = sum(1 for j in jobs if j.get("status") == "success")
    failed = sum(1 for j in jobs if j.get("status") == "failed")
    
    status_obj = AutoOpStatus(
        name="Training Scheduler",
        category="scheduling",
        status="running" if active > 0 else "idle",
        metrics={
            "total_jobs": len(jobs),
            "completed": completed,
            "failed": failed,
            "active": active,
        }
    )
    
    if failed > 0:
        status_obj.alerts.append(f"❌ {failed} failed training jobs")
    
    status_obj.last_update = data.get("last_check")
    return status_obj


def parse_auto_scheduler() -> AutoOpStatus:
    """Parse auto-scheduler"""
    data = load_json(AUTO_SCHEDULER_STATUS)
    if not data:
        return AutoOpStatus(
            name="Auto Scheduler",
            category="scheduling",
            status="unknown",
        )
    
    jobs = data.get("jobs", [])
    enabled = sum(1 for j in jobs if j.get("enabled"))
    
    status_obj = AutoOpStatus(
        name="Auto Scheduler",
        category="scheduling",
        status="active" if enabled > 0 else "disabled",
        metrics={
            "total_jobs": len(jobs),
            "enabled": enabled,
            "disabled": len(jobs) - enabled,
        }
    )
    
    status_obj.last_update = data.get("updated_at")
    return status_obj


def parse_gguf_training() -> AutoOpStatus:
    """Parse GGUF training pipeline"""
    data = load_json(GGUF_SUMMARY)
    if not data:
        return AutoOpStatus(
            name="GGUF Training",
            category="learning",
            status="unknown",
        )
    
    results = data.get("results", {})
    total = len(results)
    
    # Count quantum-enhanced
    quantum_enhanced = sum(1 for r in results.values() if r.get("quantum_enhanced"))
    
    status_obj = AutoOpStatus(
        name="GGUF Training",
        category="learning",
        status="idle",
        metrics={
            "total_jobs": total,
            "quantum_enhanced": quantum_enhanced,
            "standard": total - quantum_enhanced,
        }
    )
    
    status_obj.last_update = data.get("timestamp")
    return status_obj


def parse_train_and_promote() -> AutoOpStatus:
    """Parse train_and_promote pipeline"""
    data = get_latest_train_promote()
    if not data:
        return AutoOpStatus(
            name="Train & Promote",
            category="deployment",
            status="unknown",
        )
    
    training = data.get("training", {})
    evaluation = data.get("evaluation", {})
    summary = data.get("summary", {})
    
    train_status = summary.get("training_status", "unknown")
    eval_status = summary.get("evaluation_status", "unknown")
    
    # Determine overall status
    if train_status == "success" and eval_status == "success":
        status = "success"
    elif train_status == "failed" or eval_status == "failed":
        status = "error"
    else:
        status = "running"
    
    metrics = {
        "training_duration_sec": summary.get("total_duration", 0),
        "best_model": summary.get("best_model", "unknown"),
        "promotion_successful": summary.get("promotion_successful", False),
    }
    
    # Count training/evaluation models
    if isinstance(training, dict):
        metrics["trained_models"] = len(training)
    if isinstance(evaluation, dict):
        metrics["evaluated_models"] = len(evaluation)
    
    status_obj = AutoOpStatus(
        name="Train & Promote",
        category="deployment",
        status=status,
        metrics=metrics,
    )
    
    status_obj.last_update = data.get("pipeline_run", {}).get("started_at")
    
    if not summary.get("promotion_successful"):
        status_obj.alerts.append("⚠️  Promotion failed - check logs")
    
    return status_obj


def parse_autotrain() -> AutoOpStatus:
    """Parse autotrain orchestrator"""
    data = load_json(AUTOTRAIN_STATUS)
    if not data:
        return AutoOpStatus(
            name="AutoTrain",
            category="learning",
            status="unknown",
        )
    
    jobs = data.get("jobs", [])
    succeeded = sum(1 for j in jobs if j.get("status") == "succeeded")
    failed = sum(1 for j in jobs if j.get("status") == "failed")
    
    status_obj = AutoOpStatus(
        name="AutoTrain",
        category="learning",
        status="idle",
        metrics={
            "total_jobs": len(jobs),
            "succeeded": succeeded,
            "failed": failed,
            "success_rate": (succeeded / len(jobs) * 100) if jobs else 0,
        }
    )
    
    if failed > 0:
        failed_jobs = [j["name"] for j in jobs if j.get("status") == "failed"][:3]
        status_obj.alerts.append(f"❌ {failed} failed jobs: {', '.join(failed_jobs)}")
    
    status_obj.last_update = data.get("generated_at")
    return status_obj


def parse_evaluation() -> AutoOpStatus:
    """Parse evaluation autorun"""
    data = load_json(EVALUATION_STATUS)
    if not data:
        return AutoOpStatus(
            name="Evaluation AutoRun",
            category="evaluation",
            status="unknown",
        )
    
    jobs = data.get("jobs", [])
    succeeded = sum(1 for j in jobs if j.get("status") == "succeeded")
    failed = sum(1 for j in jobs if j.get("status") == "failed")
    
    status_obj = AutoOpStatus(
        name="Evaluation AutoRun",
        category="evaluation",
        status="idle",
        metrics={
            "total_jobs": len(jobs),
            "succeeded": succeeded,
            "failed": failed,
        }
    )
    
    status_obj.last_update = data.get("generated_at")
    return status_obj


def parse_quantum() -> AutoOpStatus:
    """Parse quantum autorun"""
    data = load_json(QUANTUM_STATUS)
    if not data:
        return AutoOpStatus(
            name="Quantum AutoRun",
            category="evaluation",
            status="unknown",
            alerts=["Not configured or no runs yet"],
        )
    
    jobs = data.get("jobs", [])
    succeeded = sum(1 for j in jobs if j.get("status") in ("succeeded", "validated"))
    failed = sum(1 for j in jobs if j.get("status") == "failed")
    
    status_obj = AutoOpStatus(
        name="Quantum AutoRun",
        category="evaluation",
        status="idle",
        metrics={
            "total_jobs": len(jobs),
            "succeeded": succeeded,
            "failed": failed,
        }
    )
    
    status_obj.last_update = data.get("generated_at")
    return status_obj


def parse_ci_pipeline() -> AutoOpStatus:
    """Parse CI/CD pipeline"""
    data = load_json(CI_RESULTS)
    if not data:
        return AutoOpStatus(
            name="CI Pipeline",
            category="ci",
            status="unknown",
        )
    
    succeeded = data.get("succeeded", 0)
    failed = data.get("failed", 0)
    skipped = data.get("skipped", 0)
    
    status_obj = AutoOpStatus(
        name="CI Pipeline",
        category="ci",
        status="error" if failed > 0 else "success" if succeeded > 0 else "idle",
        metrics={
            "total_steps": data.get("total_steps", 0),
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped,
        }
    )
    
    if failed > 0:
        results = data.get("results", [])
        failed_steps = [r["name"] for r in results if r.get("status") == "failed"]
        status_obj.alerts.append(f"❌ CI failed: {', '.join(failed_steps[:3])}")
    
    status_obj.last_update = data.get("generated_at")
    return status_obj


def get_all_statuses() -> List[AutoOpStatus]:
    """Collect all auto operation statuses"""
    return [
        parse_autonomous_training(),
        parse_autotrain(),
        parse_evaluation(),
        parse_quantum(),
        parse_gguf_training(),
        parse_train_and_promote(),
        parse_master_orchestrator(),
        parse_training_scheduler(),
        parse_auto_scheduler(),
        parse_ci_pipeline(),
    ]


def render_terminal(statuses: List[AutoOpStatus], compact: bool = False) -> None:
    """Render dashboard to terminal"""
    # Clear screen
    if os.name != "nt":
        os.system("clear")
    else:
        os.system("cls")
    
    print("\n" + "=" * 100)
    print("AUTO OPERATIONS DASHBOARD".center(100))
    print("=" * 100 + "\n")
    
    # Group by category
    categories = {}
    for status in statuses:
        if status.category not in categories:
            categories[status.category] = []
        categories[status.category].append(status)
    
    category_titles = {
        "learning": "🤖 LEARNING & TRAINING",
        "evaluation": "📊 EVALUATION & ANALYSIS",
        "scheduling": "⏰ SCHEDULING & ORCHESTRATION",
        "deployment": "🚀 DEPLOYMENT & PROMOTION",
        "ci": "🔄 CI/CD PIPELINE",
    }
    
    for category in ["learning", "evaluation", "scheduling", "deployment", "ci"]:
        if category not in categories:
            continue
        
        print(f"\n{category_titles.get(category, category.upper())}")
        print("-" * 100)
        
        for status in categories[category]:
            # Status emoji
            status_emoji = {
                "running": "🟢",
                "idle": "⚪",
                "success": "✅",
                "error": "❌",
                "scheduled": "📅",
                "unknown": "❓",
                "disabled": "🔒",
                "active": "🟢",
            }.get(status.status, "❓")
            
            # Main line
            if compact:
                print(f"{status_emoji} {status.name:<35} {status.status:<12} ")
            else:
                metrics_str = " | ".join(f"{k}={v}" for k, v in status.metrics.items())
                print(f"{status_emoji} {status.name:<35} {status.status:<12} {metrics_str:<40}")
                
                if status.current_task:
                    print(f"  ├─ Task: {status.current_task}")
                if status.progress > 0:
                    progress_bar = "█" * int(status.progress / 5) + "░" * (20 - int(status.progress / 5))
                    print(f"  ├─ Progress: [{progress_bar}] {status.progress:.1f}%")
                if status.cycles_completed > 0:
                    print(f"  ├─ Cycles: {status.cycles_completed}")
                
                # Alerts
                if status.alerts:
                    for alert in status.alerts:
                        print(f"  ├─ {alert}")
                
                if status.last_update:
                    print(f"  └─ Last update: {status.last_update}")
    
    print("\n" + "=" * 100 + "\n")


def render_json(statuses: List[AutoOpStatus]) -> str:
    """Render as JSON"""
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "operations": [
            {
                "name": s.name,
                "category": s.category,
                "status": s.status,
                "cycles_completed": s.cycles_completed,
                "current_task": s.current_task,
                "progress": s.progress,
                "alerts": s.alerts,
                "metrics": s.metrics,
                "last_update": s.last_update,
            }
            for s in statuses
        ]
    }
    return json.dumps(data, indent=2)


def main() -> None:
    ap = argparse.ArgumentParser(description="Auto Operations Dashboard")
    ap.add_argument("--watch", action="store_true", help="Auto-refresh every 5s")
    ap.add_argument("--compact", action="store_true", help="Condensed output")
    ap.add_argument("--export", action="store_true", help="Export to JSON")
    ap.add_argument("--problems", action="store_true", help="Show only items with alerts")
    args = ap.parse_args()
    
    def render():
        statuses = get_all_statuses()
        
        if args.problems:
            statuses = [s for s in statuses if s.alerts or s.status in ("error", "failed")]
        
        if args.export:
            output = render_json(statuses)
            out_file = REPO_ROOT / "data_out" / "auto_ops_dashboard.json"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with out_file.open("w") as f:
                f.write(output)
            print(f"Exported to: {out_file}")
        else:
            render_terminal(statuses, compact=args.compact)
    
    if args.watch:
        print("Watch mode - Ctrl+C to exit")
        try:
            while True:
                render()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nWatch stopped")
    else:
        render()


if __name__ == "__main__":
    main()
