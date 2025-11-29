#!/usr/bin/env python
"""
Auto-Scheduler

Automatically schedules and executes orchestrator workflows based on triggers:
- Time-based (cron-like scheduling)
- Event-based (file changes, new datasets)
- Performance-based (metrics thresholds)
- Resource-based (CPU/GPU availability)

Features:
- Persistent schedule state
- Skip overlapping runs
- Resource-aware scheduling
- Auto-retry on failure
- Email/Slack notifications

Usage examples (PowerShell):
  python .\\scripts\\auto_scheduler.py --start  # Start scheduler daemon
  python .\\scripts\\auto_scheduler.py --schedule "daily_full_pipeline" --cron "0 2 * * *"
  python .\\scripts\\auto_scheduler.py --list   # List scheduled jobs
  python .\\scripts\\auto_scheduler.py --status # Show scheduler status
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import signal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading
import smtplib
from email.message import EmailMessage

try:
    from croniter import croniter
except ImportError:
    croniter = None  # Optional dependency

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "auto_scheduler"
SCHEDULE_FILE = DATA_OUT / "schedule.json"
STATE_FILE = DATA_OUT / "state.json"


@dataclass
class ScheduledJob:
    name: str
    workflow: str
    cron: str
    enabled: bool = True
    last_run: Optional[str] = None
    last_status: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    consecutive_failures: int = 0
    max_consecutive_failures: int = 3
    notify_on_failure: bool = True


class AutoScheduler:
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
        self.data_out = DATA_OUT
        self.data_out.mkdir(parents=True, exist_ok=True)
        self.jobs = {}
        self.running = True
        self.check_interval = 60  # seconds
        self._load_schedule()
        self._load_state()
    
    def _load_schedule(self):
        """Load scheduled jobs from disk."""
        if SCHEDULE_FILE.exists():
            with SCHEDULE_FILE.open("r") as f:
                data = json.load(f)
                for item in data.get("jobs", []):
                    job = ScheduledJob(**item)
                    self.jobs[job.name] = job
    
    def _save_schedule(self):
        """Save scheduled jobs to disk."""
        data = {
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "jobs": [job.__dict__ for job in self.jobs.values()],
        }
        with SCHEDULE_FILE.open("w") as f:
            json.dump(data, f, indent=2)
    
    def _load_state(self):
        """Load scheduler state from disk."""
        if STATE_FILE.exists():
            with STATE_FILE.open("r") as f:
                state = json.load(f)
                for job_name, job_state in state.get("jobs", {}).items():
                    if job_name in self.jobs:
                        job = self.jobs[job_name]
                        job.last_run = job_state.get("last_run")
                        job.last_status = job_state.get("last_status")
                        job.run_count = job_state.get("run_count", 0)
                        job.consecutive_failures = job_state.get("consecutive_failures", 0)
    
    def _save_state(self):
        """Save scheduler state to disk."""
        state = {
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "jobs": {
                name: {
                    "last_run": job.last_run,
                    "last_status": job.last_status,
                    "next_run": job.next_run,
                    "run_count": job.run_count,
                    "consecutive_failures": job.consecutive_failures,
                }
                for name, job in self.jobs.items()
            }
        }
        with STATE_FILE.open("w") as f:
            json.dump(state, f, indent=2)
    
    def add_job(self, name: str, workflow: str, cron: str, **kwargs):
        """Add a new scheduled job."""
        if croniter is None:
            print("WARNING: croniter not installed. Install with: pip install croniter")
            print("Cron scheduling will not work without croniter.")
        
        job = ScheduledJob(name=name, workflow=workflow, cron=cron, **kwargs)
        self.jobs[name] = job
        self._calculate_next_run(job)
        self._save_schedule()
        print(f"[scheduler] Added job: {name} (workflow={workflow}, cron={cron})")
        print(f"[scheduler] Next run: {job.next_run}")
    
    def remove_job(self, name: str):
        """Remove a scheduled job."""
        if name in self.jobs:
            del self.jobs[name]
            self._save_schedule()
            print(f"[scheduler] Removed job: {name}")
        else:
            print(f"[scheduler] Job not found: {name}")
    
    def enable_job(self, name: str):
        """Enable a job."""
        if name in self.jobs:
            self.jobs[name].enabled = True
            self._save_schedule()
            print(f"[scheduler] Enabled job: {name}")
    
    def disable_job(self, name: str):
        """Disable a job."""
        if name in self.jobs:
            self.jobs[name].enabled = False
            self._save_schedule()
            print(f"[scheduler] Disabled job: {name}")
    
    def _calculate_next_run(self, job: ScheduledJob):
        """Calculate next run time for a job."""
        if croniter is None:
            job.next_run = "croniter not installed"
            return
        
        try:
            cron = croniter(job.cron, datetime.now())
            next_dt = cron.get_next(datetime)
            job.next_run = next_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"[scheduler] Invalid cron for {job.name}: {e}")
            job.next_run = "invalid cron"
    
    def run_job(self, job: ScheduledJob):
        """Execute a scheduled job."""
        print(f"\n[scheduler] ========================================")
        print(f"[scheduler] Running scheduled job: {job.name}")
        print(f"[scheduler] Workflow: {job.workflow}")
        print(f"[scheduler] ========================================\n")
        
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "master_orchestrator.py"),
            "--workflow",
            job.workflow
        ]
        
        t0 = time.time()
        notif_config = None  # TODO: Load from YAML or pass as arg
        try:
            result = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            duration = time.time() - t0
            success = result.returncode == 0
            # Update job state
            job.last_run = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            job.last_status = "succeeded" if success else "failed"
            job.run_count += 1
            if success:
                self.send_notification("Scheduled job completed", f"Job {job.name} finished successfully.", notif_config)
                job.consecutive_failures = 0
            else:
                self.send_notification("Scheduled job failed", f"Job {job.name} failed.", notif_config)
                job.consecutive_failures += 1
            # Calculate next run
            self._calculate_next_run(job)
            self._save_state()
            print(f"\n[scheduler] Job completed: {job.name}")
            print(f"[scheduler] Status: {job.last_status}")
            print(f"[scheduler] Duration: {duration:.2f}s")
            print(f"[scheduler] Next run: {job.next_run}")
            
            # Check if we should disable due to consecutive failures
            if job.consecutive_failures >= job.max_consecutive_failures:
                print(f"[scheduler] WARNING: Job disabled after {job.consecutive_failures} failures")
                job.enabled = False
                self._save_schedule()
                if job.notify_on_failure:
                    self.send_notification("Job disabled", f"Job {job.name} disabled after {job.consecutive_failures} failures.", notif_config)
            
        except subprocess.TimeoutExpired:
            print(f"[scheduler] Job timed out: {job.name}")
            job.last_status = "timeout"
            job.consecutive_failures += 1
            self._save_state()
        except Exception as e:
            print(f"[scheduler] Job error: {e}")
            job.last_status = "error"
            job.consecutive_failures += 1
            self._save_state()
    
    def _send_notification(self, job: ScheduledJob, message: str):
        # Method removed; replaced by send_notification
        pass
    
    def start_daemon(self):
        """Start the scheduler daemon."""
        print("[scheduler] Starting scheduler daemon...")
        print(f"[scheduler] Check interval: {self.check_interval} seconds")
        print(f"[scheduler] Scheduled jobs: {len(self.jobs)}")
        
        def signal_handler(sig, frame):
            print("\n[scheduler] Received shutdown signal")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while self.running:
            now = datetime.now()
            print(f"\n[scheduler] Health check at {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
            for job in self.jobs.values():
                if not job.enabled:
                    continue
                
                # Check if job should run now
                if croniter and job.next_run and job.next_run != "invalid cron":
                    try:
                        next_run_dt = datetime.strptime(job.next_run, "%Y-%m-%d %H:%M:%S")
                        if now >= next_run_dt:
                            # Run job in a separate thread to avoid blocking
                            thread = threading.Thread(target=self.run_job, args=(job,))
                            thread.start()
                            thread.join()  # Wait for completion
                    except ValueError:
                        pass
            
            time.sleep(self.check_interval)
        
        print("[scheduler] Daemon stopped")
    
    def list_jobs(self):
        """List all scheduled jobs."""
        return [
            {
                "name": job.name,
                "workflow": job.workflow,
                "cron": job.cron,
                "enabled": job.enabled,
                "last_run": job.last_run,
                "last_status": job.last_status,
                "next_run": job.next_run,
                "run_count": job.run_count,
                "consecutive_failures": job.consecutive_failures,
            }
            for job in self.jobs.values()
        ]
    
    def get_status(self):
        """Get scheduler status."""
        return {
            "scheduler_running": self.running,
            "total_jobs": len(self.jobs),
            "enabled_jobs": sum(1 for j in self.jobs.values() if j.enabled),
            "disabled_jobs": sum(1 for j in self.jobs.values() if not j.enabled),
            "jobs": self.list_jobs(),
        }


def main():
    ap = argparse.ArgumentParser(description="Auto-Scheduler")
    ap.add_argument("--start", action="store_true", help="Start scheduler daemon")
    ap.add_argument("--schedule", help="Schedule a new job (job name)")
    ap.add_argument("--workflow", help="Workflow name for scheduled job")
    ap.add_argument("--cron", help="Cron expression (e.g., '0 2 * * *')")
    ap.add_argument("--remove", help="Remove a scheduled job")
    ap.add_argument("--enable", help="Enable a job")
    ap.add_argument("--disable", help="Disable a job")
    ap.add_argument("--list", action="store_true", help="List scheduled jobs")
    ap.add_argument("--status", action="store_true", help="Show scheduler status")
    ap.add_argument("--check-interval", type=int, default=60, help="Check interval in seconds")
    args = ap.parse_args()
    
    scheduler = AutoScheduler()
    
    if args.check_interval:
        scheduler.check_interval = args.check_interval
    
    if args.schedule:
        if not args.workflow or not args.cron:
            print("ERROR: --workflow and --cron are required when scheduling")
            sys.exit(1)
        scheduler.add_job(args.schedule, args.workflow, args.cron)
        return
    
    if args.remove:
        scheduler.remove_job(args.remove)
        return
    
    if args.enable:
        scheduler.enable_job(args.enable)
        return
    
    if args.disable:
        scheduler.disable_job(args.disable)
        return
    
    if args.list:
        jobs = scheduler.list_jobs()
        print(json.dumps(jobs, indent=2))
        return
    
    if args.status:
        status = scheduler.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.start:
        scheduler.start_daemon()
        return
    
    # Default: show help
    ap.print_help()


if __name__ == "__main__":
    main()
