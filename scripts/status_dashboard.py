#!/usr/bin/env python
"""Status Dashboard - Unified View of All Orchestrators

Aggregates status from all orchestrators and presents a unified dashboard view.

Features:
- Real-time status aggregation from all orchestrators
- Performance metrics (avg duration, success rate, throughput)
- Resource utilization tracking (GPU, disk space)
- Alert detection (failures, slow jobs, resource constraints)
- Export to multiple formats (terminal, JSON, markdown, HTML)

Usage:
  python .\\scripts\\status_dashboard.py                    # Terminal view
  python .\\scripts\\status_dashboard.py --watch            # Auto-refresh every 10s
  python .\\scripts\\status_dashboard.py --export markdown  # Generate report
  python .\\scripts\\status_dashboard.py --alerts           # Show only problems
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parents[1]

STATUS_FILES = {
    "autotrain": REPO_ROOT / "data_out" / "autotrain" / "status.json",
    "evaluation": REPO_ROOT / "data_out" / "evaluation_autorun" / "status.json",
    "train_and_eval": REPO_ROOT / "data_out" / "train_and_evaluate" / "summary.json",
    "quantum": REPO_ROOT / "data_out" / "quantum_autorun" / "status.json",
    "env_autofix": REPO_ROOT / "data_out" / "env_autofix" / "status.json",
    "metrics_ranker": REPO_ROOT / "data_out" / "metrics_ranker" / "ranking.json",
    "smart_orchestrator": REPO_ROOT / "data_out" / "smart_orchestrator",
}


@dataclass
class OrchestratorStatus:
    """Status snapshot for one orchestrator"""
    name: str
    total_jobs: int = 0
    succeeded: int = 0
    failed: int = 0
    running: int = 0
    pending: int = 0
    last_updated: Optional[str] = None
    avg_duration: float = 0.0
    alerts: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        completed = self.succeeded + self.failed
        return (self.succeeded / completed * 100) if completed > 0 else 0.0
    
    @property
    def status_emoji(self) -> str:
        if self.failed > 0:
            return "❌"
        elif self.running > 0:
            return "⏳"
        elif self.succeeded == self.total_jobs and self.total_jobs > 0:
            return "✅"
        else:
            return "⚪"


def load_status(path: Path) -> Optional[Dict[str, Any]]:
    """Load status JSON if it exists"""
    if not path.exists():
        return None
    try:
        with path.open("r") as f:
            return json.load(f)
    except Exception:
        return None


def parse_autotrain_status() -> OrchestratorStatus:
    """Parse autotrain status.json"""
    data = load_status(STATUS_FILES["autotrain"])
    if not data:
        return OrchestratorStatus(name="AutoTrain", alerts=["Status file not found"])
    
    jobs = data.get("jobs", [])
    status = OrchestratorStatus(
        name="AutoTrain",
        total_jobs=len(jobs),
        succeeded=sum(1 for j in jobs if j.get("status") == "succeeded"),
        failed=sum(1 for j in jobs if j.get("status") == "failed"),
        last_updated=data.get("generated_at"),
    )
    
    # Calculate avg duration
    durations = [j.get("duration_sec", 0) for j in jobs if j.get("duration_sec")]
    if durations:
        status.avg_duration = sum(durations) / len(durations)
    
    # Detect alerts
    recent_failures = [j["name"] for j in jobs if j.get("status") == "failed"][:3]
    if recent_failures:
        status.alerts.append(f"Failed jobs: {', '.join(recent_failures)}")
    
    slow_jobs = [j["name"] for j in jobs if (j.get("duration_sec") or 0) > 600]
    if slow_jobs:
        status.alerts.append(f"{len(slow_jobs)} jobs took >10min")
    
    return status


def parse_evaluation_status() -> OrchestratorStatus:
    """Parse evaluation_autorun status.json"""
    data = load_status(STATUS_FILES["evaluation"])
    if not data:
        return OrchestratorStatus(name="Evaluation", alerts=["Status file not found"])
    
    jobs = data.get("jobs", [])
    status = OrchestratorStatus(
        name="Evaluation",
        total_jobs=len(jobs),
        succeeded=sum(1 for j in jobs if j.get("status") == "succeeded"),
        failed=sum(1 for j in jobs if j.get("status") == "failed"),
        last_updated=data.get("generated_at"),
    )
    
    # Calculate avg duration
    durations = [j.get("duration_sec", 0) for j in jobs if j.get("duration_sec")]
    if durations:
        status.avg_duration = sum(durations) / len(durations)
    
    # Check for placeholder metrics (template evaluators)
    placeholder_jobs = [
        j["name"] for j in jobs 
        if j.get("evaluation_summary", {}).get("status") == "template_placeholder"
    ]
    if placeholder_jobs:
        status.alerts.append(f"{len(placeholder_jobs)} jobs using template evaluator (no real metrics)")
    
    return status


def parse_quantum_status() -> OrchestratorStatus:
    """Parse quantum_autorun status.json"""
    data = load_status(STATUS_FILES["quantum"])
    if not data:
        return OrchestratorStatus(name="Quantum", alerts=["Not configured or no runs yet"])
    
    jobs = data.get("jobs", [])
    status = OrchestratorStatus(
        name="Quantum",
        total_jobs=len(jobs),
        succeeded=sum(1 for j in jobs if j.get("status") in ("succeeded", "validated")),
        failed=sum(1 for j in jobs if j.get("status") == "failed"),
        last_updated=data.get("generated_at"),
    )
    
    return status


def parse_env_status() -> OrchestratorStatus:
    """Parse env_autofix status.json"""
    data = load_status(STATUS_FILES["env_autofix"])
    if not data:
        return OrchestratorStatus(name="EnvRepair", alerts=["No env_autofix status (not run)"])
    state = data.get("state")
    status = OrchestratorStatus(name="EnvRepair", total_jobs=1)
    if state in ("healthy", "repaired"):
        status.succeeded = 1
    else:
        status.failed = 1
        status.alerts.append(f"Environment state: {state}")
    if data.get("timestamp"):
        status.last_updated = data.get("timestamp")
    return status


def parse_ranking_status() -> OrchestratorStatus:
    """Parse metrics_ranker ranking.json"""
    data = load_status(STATUS_FILES["metrics_ranker"])
    if not data:
        return OrchestratorStatus(name="Ranking", alerts=["No ranking results yet"])
    models = data.get("models", [])
    status = OrchestratorStatus(name="Ranking", total_jobs=len(models))
    status.succeeded = sum(1 for m in models if m.get("delta") is not None)
    failed_models = [m.get("job") for m in models if m.get("delta") is None]
    if failed_models:
        status.alerts.append(f"No score for: {', '.join(failed_models[:5])}")
    if data.get("alerts"):
        status.alerts.extend(data.get("alerts"))
    status.last_updated = data.get("generated_at")
    return status


def parse_train_eval_status() -> OrchestratorStatus:
    """Parse train_and_evaluate summary.json"""
    data = load_status(STATUS_FILES["train_and_eval"])
    if not data:
        return OrchestratorStatus(name="Train+Eval", alerts=["Not run yet"])
    
    training = data.get("training", {})
    evaluation = data.get("evaluation", {})
    
    total_trained = len(training)
    succeeded_train = sum(1 for v in training.values() if v.get("status") in ("succeeded", "skipped_existing"))
    failed_train = sum(1 for v in training.values() if v.get("status") == "failed")
    
    total_eval = len(evaluation)
    succeeded_eval = sum(1 for v in evaluation.values() if v.get("status") == "succeeded")
    
    status = OrchestratorStatus(
        name="Train+Eval Pipeline",
        total_jobs=total_trained + total_eval,
        succeeded=succeeded_train + succeeded_eval,
        failed=failed_train,
    )
    
    # Check ranking quality
    ranking = data.get("ranking", [])
    if ranking and all(r.get("score") is None for r in ranking):
        status.alerts.append("Ranking has no scores (evaluator not implemented)")
    
    return status


def get_resource_info() -> Dict[str, Any]:
    """Get system resource information"""
    info = {}
    
    # Check disk space in data_out
    data_out = REPO_ROOT / "data_out"
    if data_out.exists():
        try:
            total_size = sum(f.stat().st_size for f in data_out.rglob("*") if f.is_file())
            info["data_out_size_mb"] = round(total_size / 1024 / 1024, 1)
        except Exception:
            pass
    
    # Check GPU availability (if torch installed)
    try:
        import torch
        info["cuda_available"] = torch.cuda.is_available()
        if info["cuda_available"]:
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_count"] = torch.cuda.device_count()
    except Exception:
        info["cuda_available"] = False
    
    return info


def render_terminal(statuses: List[OrchestratorStatus], resources: Dict[str, Any]) -> None:
    """Render dashboard to terminal"""
    print("\n" + "=" * 80)
    print("QAI STATUS DASHBOARD".center(80))
    print("=" * 80 + "\n")
    
    # Orchestrator statuses
    for status in statuses:
        print(f"{status.status_emoji} {status.name}")
        print(f"  Jobs: {status.succeeded}/{status.total_jobs} succeeded ({status.success_rate:.1f}%)")
        if status.failed > 0:
            print(f"  Failed: {status.failed}")
        if status.avg_duration > 0:
            print(f"  Avg duration: {int(status.avg_duration)}s")
        if status.last_updated:
            print(f"  Last updated: {status.last_updated}")
        if status.alerts:
            for alert in status.alerts:
                print(f"  ⚠️  {alert}")
        print()
    
    # Resource info
    print("-" * 80)
    print("RESOURCES")
    print("-" * 80)
    if resources.get("cuda_available"):
        print(f"✓ GPU: {resources.get('gpu_name')} ({resources.get('gpu_count')} device(s))")
    else:
        print("⚠️  GPU: Not available (CPU training only)")
    
    if "data_out_size_mb" in resources:
        print(f"📁 data_out size: {resources['data_out_size_mb']} MB")
    
    print("\n" + "=" * 80 + "\n")


def render_markdown(statuses: List[OrchestratorStatus], resources: Dict[str, Any]) -> str:
    """Render dashboard as markdown"""
    lines = [
        "# QAI Status Dashboard",
        "",
        f"_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC_",
        "",
        "## Orchestrators",
        "",
    ]
    
    for status in statuses:
        lines.extend([
            f"### {status.status_emoji} {status.name}",
            "",
            f"- **Jobs**: {status.succeeded}/{status.total_jobs} succeeded ({status.success_rate:.1f}%)",
        ])
        if status.failed > 0:
            lines.append(f"- **Failed**: {status.failed}")
        if status.avg_duration > 0:
            lines.append(f"- **Avg Duration**: {int(status.avg_duration)}s")
        if status.alerts:
            lines.append("- **Alerts**:")
            for alert in status.alerts:
                lines.append(f"  - {alert}")
        lines.append("")
    
    lines.extend([
        "## Resources",
        "",
    ])
    
    if resources.get("cuda_available"):
        lines.append(f"- **GPU**: {resources.get('gpu_name')} ({resources.get('gpu_count')} device(s))")
    else:
        lines.append("- **GPU**: Not available")
    
    if "data_out_size_mb" in resources:
        lines.append(f"- **data_out size**: {resources['data_out_size_mb']} MB")
    
    return "\n".join(lines)


def render_json(statuses: List[OrchestratorStatus], resources: Dict[str, Any]) -> str:
    """Render dashboard as JSON"""
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "orchestrators": [
            {
                "name": s.name,
                "total_jobs": s.total_jobs,
                "succeeded": s.succeeded,
                "failed": s.failed,
                "success_rate": s.success_rate,
                "avg_duration_sec": s.avg_duration,
                "alerts": s.alerts,
            }
            for s in statuses
        ],
        "resources": resources,
    }
    return json.dumps(data, indent=2)


def main() -> None:
    ap = argparse.ArgumentParser(description="Unified status dashboard")
    ap.add_argument("--export", choices=["markdown", "json"], help="Export format")
    ap.add_argument("--watch", action="store_true", help="Auto-refresh every 10s")
    ap.add_argument("--alerts", action="store_true", help="Show only orchestrators with alerts")
    args = ap.parse_args()
    
    def collect_and_render():
        # Collect status from all orchestrators
        statuses = [
            parse_env_status(),
            parse_autotrain_status(),
            parse_evaluation_status(),
            parse_train_eval_status(),
            parse_ranking_status(),
            parse_quantum_status(),
        ]
        
        # Filter to alerts only if requested
        if args.alerts:
            statuses = [s for s in statuses if s.alerts or s.failed > 0]
        
        resources = get_resource_info()
        
        # Render
        if args.export == "markdown":
            output = render_markdown(statuses, resources)
            out_file = REPO_ROOT / "data_out" / "status_dashboard.md"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with out_file.open("w", encoding="utf-8") as f:
                f.write(output)
            print(f"Exported to: {out_file}")
        elif args.export == "json":
            output = render_json(statuses, resources)
            out_file = REPO_ROOT / "data_out" / "status_dashboard.json"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with out_file.open("w", encoding="utf-8") as f:
                f.write(output)
            print(f"Exported to: {out_file}")
        else:
            render_terminal(statuses, resources)
    
    if args.watch:
        print("Watch mode - Ctrl+C to exit")
        try:
            while True:
                if os.name == "nt":
                    os.system("cls")
                else:
                    os.system("clear")
                collect_and_render()
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nWatch stopped")
    else:
        collect_and_render()


if __name__ == "__main__":
    main()
