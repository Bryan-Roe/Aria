#!/usr/bin/env python
"""
Automated Training Scheduler

Schedule and manage periodic training runs with various strategies:
- Nightly training (new models every night)
- Continuous improvement (retrain when new data available)
- A/B testing (train multiple variants in parallel)
- Auto-tuning (grid search hyperparameters)

Usage:
    python scripts/training_scheduler.py --start nightly
    python scripts/training_scheduler.py --start continuous --check-interval 3600
    python scripts/training_scheduler.py --run-once --preset quick
    python scripts/training_scheduler.py --grid-search
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "training_scheduler"
STATE_FILE = DATA_OUT / "scheduler_state.json"


@dataclass
class TrainingJob:
    """A scheduled training job."""
    job_id: str
    preset: str
    dataset: str
    schedule: str  # cron-like or "once", "continuous"
    config: Dict[str, Any] = field(default_factory=dict)
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    runs_completed: int = 0
    status: str = "pending"


class TrainingScheduler:
    """Manages scheduled training jobs."""
    
    def __init__(self):
        self.data_out = DATA_OUT
        self.data_out.mkdir(parents=True, exist_ok=True)
        self.jobs: List[TrainingJob] = []
        self.state = self.load_state()
    
    def load_state(self) -> Dict:
        """Load scheduler state from disk."""
        if STATE_FILE.exists():
            with STATE_FILE.open("r") as f:
                return json.load(f)
        return {"jobs": [], "last_check": None}
    
    def save_state(self):
        """Save scheduler state to disk."""
        state = {
            "jobs": [
                {
                    "job_id": j.job_id,
                    "preset": j.preset,
                    "dataset": j.dataset,
                    "schedule": j.schedule,
                    "config": j.config,
                    "last_run": j.last_run,
                    "next_run": j.next_run,
                    "runs_completed": j.runs_completed,
                    "status": j.status
                }
                for j in self.jobs
            ],
            "last_check": datetime.now().isoformat()
        }
        
        with STATE_FILE.open("w") as f:
            json.dump(state, f, indent=2)
    
    def add_job(self, job: TrainingJob):
        """Add a training job to the schedule."""
        self.jobs.append(job)
        print(f"[scheduler] Added job: {job.job_id} (schedule: {job.schedule})")
    
    def should_run_job(self, job: TrainingJob) -> bool:
        """Check if a job should run now."""
        if job.schedule == "once":
            return job.runs_completed == 0
        
        if job.schedule == "continuous":
            # Check if new data available
            dataset_path = REPO_ROOT / job.dataset
            if dataset_path.exists():
                dataset_modified = datetime.fromtimestamp(dataset_path.stat().st_mtime)
                last_run = datetime.fromisoformat(job.last_run) if job.last_run else datetime.min
                return dataset_modified > last_run
            return False
        
        if job.schedule == "nightly":
            now = datetime.now()
            # Run at 2 AM if not run today
            if job.last_run:
                last_run_date = datetime.fromisoformat(job.last_run).date()
                if last_run_date == now.date():
                    return False
            # Check if it's past 2 AM
            return now.hour >= 2
        
        return False
    
    def run_job(self, job: TrainingJob) -> Dict[str, Any]:
        """Execute a training job."""
        print(f"\n[scheduler] Running job: {job.job_id}")
        print(f"[scheduler] Preset: {job.preset}")
        print(f"[scheduler] Dataset: {job.dataset}")
        
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "train_and_promote.py"),
            f"--{job.preset}",
            "--dataset", job.dataset,
            "--auto-promote"
        ]
        
        # Add custom config
        for key, value in job.config.items():
            cmd.extend([f"--{key}", str(value)])
        
        t0 = time.time()
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        duration = time.time() - t0
        
        job.last_run = datetime.now().isoformat()
        job.runs_completed += 1
        
        if result.returncode == 0:
            job.status = "success"
            print(f"[scheduler] Job {job.job_id} succeeded in {duration:.1f}s")
        else:
            job.status = "failed"
            print(f"[scheduler] Job {job.job_id} failed: {result.stderr}")
        
        self.save_state()
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "duration": duration,
            "output": result.stdout
        }
    
    def run_grid_search(self, param_grid: Dict[str, List[Any]]) -> List[Dict]:
        """Run grid search over hyperparameters."""
        print("[scheduler] Starting grid search...")
        
        results = []
        job_num = 0
        
        # Simple grid iteration
        learning_rates = param_grid.get("learning_rate", [2e-5])
        batch_sizes = param_grid.get("batch_size", [8])
        epochs_list = param_grid.get("epochs", [3])
        
        for lr in learning_rates:
            for bs in batch_sizes:
                for epochs in epochs_list:
                    job_num += 1
                    job_id = f"grid_search_{job_num}"
                    
                    job = TrainingJob(
                        job_id=job_id,
                        preset="standard",
                        dataset="datasets/chat/mixed_chat",
                        schedule="once",
                        config={
                            "learning-rate": lr,
                            "batch-size": bs,
                            "epochs": epochs
                        }
                    )
                    
                    result = self.run_job(job)
                    results.append({
                        "params": {"lr": lr, "batch_size": bs, "epochs": epochs},
                        "result": result
                    })
        
        # Save grid search results
        grid_file = self.data_out / f"grid_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with grid_file.open("w") as f:
            json.dump(results, f, indent=2)
        
        print(f"[scheduler] Grid search complete. Results: {grid_file}")
        return results
    
    def start_daemon(self, check_interval: int = 3600):
        """Start scheduler daemon."""
        print(f"[scheduler] Starting daemon (check interval: {check_interval}s)")
        
        try:
            while True:
                print(f"\n[scheduler] Checking jobs at {datetime.now()}")
                
                for job in self.jobs:
                    if self.should_run_job(job):
                        self.run_job(job)
                
                print(f"[scheduler] Next check in {check_interval}s")
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\n[scheduler] Stopping daemon")
            self.save_state()


def main():
    ap = argparse.ArgumentParser(description="Automated Training Scheduler")
    
    # Modes
    ap.add_argument("--start", choices=["nightly", "continuous", "daemon"], 
                    help="Start scheduled training")
    ap.add_argument("--run-once", action="store_true", help="Run a single training job")
    ap.add_argument("--grid-search", action="store_true", help="Run hyperparameter grid search")
    
    # Job config
    ap.add_argument("--preset", default="quick", choices=["quick", "standard", "full"],
                    help="Training preset")
    ap.add_argument("--dataset", default="datasets/chat/mixed_chat", help="Training dataset")
    ap.add_argument("--check-interval", type=int, default=3600, 
                    help="Daemon check interval (seconds)")
    
    # Grid search config
    ap.add_argument("--learning-rates", nargs="+", type=float, 
                    default=[1e-5, 2e-5, 5e-5], help="Learning rates for grid search")
    ap.add_argument("--batch-sizes", nargs="+", type=int,
                    default=[4, 8], help="Batch sizes for grid search")
    ap.add_argument("--epochs-list", nargs="+", type=int,
                    default=[2, 3], help="Epoch counts for grid search")
    
    args = ap.parse_args()
    
    scheduler = TrainingScheduler()
    
    if args.run_once:
        print("[scheduler] Running single training job")
        job = TrainingJob(
            job_id=f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            preset=args.preset,
            dataset=args.dataset,
            schedule="once"
        )
        scheduler.run_job(job)
    
    elif args.grid_search:
        param_grid = {
            "learning_rate": args.learning_rates,
            "batch_size": args.batch_sizes,
            "epochs": args.epochs_list
        }
        scheduler.run_grid_search(param_grid)
    
    elif args.start:
        if args.start == "nightly":
            job = TrainingJob(
                job_id="nightly_training",
                preset="standard",
                dataset=args.dataset,
                schedule="nightly"
            )
            scheduler.add_job(job)
            scheduler.start_daemon(check_interval=args.check_interval)
        
        elif args.start == "continuous":
            job = TrainingJob(
                job_id="continuous_training",
                preset="quick",
                dataset=args.dataset,
                schedule="continuous"
            )
            scheduler.add_job(job)
            scheduler.start_daemon(check_interval=args.check_interval)
        
        elif args.start == "daemon":
            # Load jobs from state
            for job_data in scheduler.state.get("jobs", []):
                job = TrainingJob(**job_data)
                scheduler.jobs.append(job)
            scheduler.start_daemon(check_interval=args.check_interval)
    
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
