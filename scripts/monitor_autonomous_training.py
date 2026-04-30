"""
Real-time Monitoring Dashboard for Autonomous AI Training
Provides live status, metrics, and alerts
"""

import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Color codes for terminal output


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class TrainingMonitor:
    """Monitor autonomous training in real-time"""

    def __init__(
        self,
        status_file: str = "data_out/autonomous_training_status.json",
        log_file: str = "data_out/autonomous_training.log",
    ):
        self.status_file = Path(status_file)
        self.log_file = Path(log_file)
        self.heartbeat_file = (
            self.status_file.parent / "autonomous_training_heartbeat.json"
        )
        self.last_status = None
        self.last_log_position = 0

    def clear_screen(self):
        """Clear terminal screen"""
        try:
            if os.name == "nt":
                subprocess.run(["cmd", "/c", "cls"], check=False)
            else:
                subprocess.run(["clear"], check=False)
        except Exception:
            # If clearing fails, just print newlines
            print("\n" * 50)

    def load_status(self) -> Optional[Dict]:
        """Load current status from file"""
        if not self.status_file.exists():
            return None

        try:
            with open(self.status_file) as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}

    def load_heartbeat(self) -> Optional[Dict]:
        """Load lightweight heartbeat metadata if present."""
        if not self.heartbeat_file.exists():
            return None
        try:
            with open(self.heartbeat_file) as f:
                return json.load(f)
        except Exception:
            return None

    def get_recent_logs(self, lines: int = 20) -> List[str]:
        """Get recent log entries using streaming to avoid memory issues"""
        if not self.log_file.exists():
            return []

        try:
            # Stream log file with rolling buffer instead of loading entire file
            buffer = []
            with open(self.log_file, "r") as f:
                for line in f:
                    buffer.append(line)
                    if len(buffer) > lines:
                        buffer.pop(0)  # Keep only last N lines
            return buffer
        except Exception:
            return []

    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def format_percentage(self, value: float) -> str:
        """Format percentage with color coding"""
        pct = value * 100
        if pct >= 90:
            return f"{Colors.OKGREEN}{pct:.2f}%{Colors.ENDC}"
        elif pct >= 75:
            return f"{Colors.OKCYAN}{pct:.2f}%{Colors.ENDC}"
        elif pct >= 60:
            return f"{Colors.WARNING}{pct:.2f}%{Colors.ENDC}"
        else:
            return f"{Colors.FAIL}{pct:.2f}%{Colors.ENDC}"

    def print_header(self):
        """Print dashboard header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(
            f"{Colors.BOLD}{Colors.HEADER}🤖 AUTONOMOUS AI TRAINING MONITOR{Colors.ENDC}"
        )
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        print(f"📊 Status File: {self.status_file}")
        print(f"📝 Log File: {self.log_file}")
        print(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def print_overview(self, status: Dict):
        """Print system overview"""
        print(f"{Colors.BOLD}SYSTEM OVERVIEW{Colors.ENDC}")
        print("─" * 80)

        if "error" in status:
            print(
                f"{Colors.FAIL}❌ Error loading status: {status['error']}{Colors.ENDC}"
            )
            return

        # Basic info
        started = status.get("started_at", status.get("last_updated", "Unknown"))
        phase = status.get("current_phase", status.get("status", "unknown"))
        cycles = status.get("cycles_completed", 0)

        # Phase with color
        phase_colors = {
            "initialization": Colors.OKCYAN,
            "data_discovery": Colors.OKBLUE,
            "data_collection": Colors.OKBLUE,
            "training": Colors.WARNING,
            "optimization": Colors.OKCYAN,
            "deployment": Colors.OKGREEN,
            "stopped": Colors.FAIL,
            "error": Colors.FAIL,
        }
        phase_color = phase_colors.get(phase, Colors.ENDC)

        print(f"  Status: {phase_color}{phase.upper()}{Colors.ENDC}")
        print(f"  Started: {started}")
        print(f"  Cycles Completed: {Colors.BOLD}{cycles}{Colors.ENDC}")

        # Best accuracy
        best_acc = status.get("best_accuracy", 0)
        print(f"  Best Accuracy: {self.format_percentage(best_acc)}")

        # Last cycle
        if "last_cycle_completed_at" in status:
            last_cycle = status["last_cycle_completed_at"]
            duration = status.get("last_cycle_duration_seconds", 0)
            print(f"  Last Cycle: {last_cycle} ({self.format_duration(duration)})")
        elif status.get("last_updated"):
            print(f"  Last Cycle: {status.get('last_updated')}")

        print()

    def print_heartbeat(self):
        """Print orchestrator heartbeat state and freshness."""
        hb = self.load_heartbeat()
        if not hb:
            return

        print(f"{Colors.BOLD}HEARTBEAT{Colors.ENDC}")
        print("─" * 80)
        ts = hb.get("timestamp")
        state = hb.get("state", "unknown")
        pid = hb.get("pid", "-")
        next_eta = hb.get("next_cycle_eta")

        freshness = "unknown"
        freshness_state = "stale"
        if ts:
            try:
                hb_dt = datetime.fromisoformat(ts)
                age = datetime.now() - hb_dt
                freshness = f"{int(age.total_seconds())}s ago"
                age_sec = age.total_seconds()
                if age_sec <= 15:
                    freshness_state = "fresh"
                elif age_sec <= 60:
                    freshness_state = "warming"
                else:
                    freshness_state = "stale"
            except Exception:
                freshness = ts

        freshness_label = {
            "fresh": f"{Colors.OKGREEN}fresh{Colors.ENDC}",
            "warming": f"{Colors.WARNING}aging{Colors.ENDC}",
            "stale": f"{Colors.FAIL}stale{Colors.ENDC}",
        }.get(freshness_state, freshness_state)

        print(f"  State: {state.upper()}")
        print(f"  PID: {pid}")
        print(f"  Last Beat: {ts} ({freshness}, {freshness_label})")
        if next_eta:
            print(f"  Next Cycle ETA: {next_eta}")
        print()

    def print_datasets(self, status: Dict):
        """Print dataset information"""
        print(f"{Colors.BOLD}DATASET INVENTORY{Colors.ENDC}")
        print("─" * 80)

        inventory = status.get("dataset_inventory", {})
        total = status.get("total_datasets_available")
        if total is None:
            total = sum(
                v.get("count", 0) if isinstance(v, dict) else int(v)
                for v in inventory.values()
            )

        if inventory:
            for category, item in inventory.items():
                count = item.get("count", 0) if isinstance(item, dict) else int(item)
                print(
                    f"  {category:20s}: {Colors.BOLD}{count:4d}{Colors.ENDC} datasets"
                )

        print(f"\n  {Colors.BOLD}Total Available: {total}{Colors.ENDC}")
        print()

    def print_performance(self, status: Dict):
        """Print performance metrics"""
        print(f"{Colors.BOLD}PERFORMANCE METRICS{Colors.ENDC}")
        print("─" * 80)

        history = status.get("performance_history", [])

        if not history:
            print("  No performance data yet")
            print()
            return

        # Show last 5 cycles
        recent = history[-5:]

        print(
            f"  {'Cycle':<8} {'Epochs':<8} {'Mean Acc':<12} {'Max Acc':<12} {'Models':<10}"
        )
        print("  " + "─" * 70)

        for i, perf in enumerate(recent, start=len(history) - len(recent) + 1):
            mean_acc = perf.get("mean_accuracy", perf.get("accuracy", 0))
            max_acc = perf.get("max_accuracy", perf.get("accuracy", mean_acc))
            epochs = perf.get("epochs", "-")
            successful = perf.get("successful_count", perf.get("datasets_trained", 0))
            cycle_display = perf.get("cycle", i)

            mean_str = f"{mean_acc*100:.2f}%"
            max_str = f"{max_acc*100:.2f}%"

            print(
                f"  #{cycle_display:<7} {str(epochs):<8} {mean_str:<12} {max_str:<12} {successful:<10}"
            )

        # Trend analysis
        if len(history) >= 2:
            prev_acc = history[-2].get("mean_accuracy", history[-2].get("accuracy", 0))
            curr_acc = history[-1].get("mean_accuracy", history[-1].get("accuracy", 0))
            diff = curr_acc - prev_acc

            if diff > 0.01:
                trend = f"{Colors.OKGREEN}↑ +{diff*100:.2f}% (Improving){Colors.ENDC}"
            elif diff < -0.01:
                trend = f"{Colors.FAIL}↓ {diff*100:.2f}% (Declining){Colors.ENDC}"
            else:
                trend = f"{Colors.WARNING}→ Stable{Colors.ENDC}"

            print(f"\n  Trend: {trend}")

        plateau_cycles = status.get("plateau_cycles", 0)
        promotions = status.get("promotions", [])
        if plateau_cycles:
            print(f"  Plateau Cycles at Peak: {plateau_cycles}")
        if promotions:
            latest = promotions[-1]
            print(
                f"  Promotions: {len(promotions)} "
                f"(latest v{latest.get('version', '?')} @ cycle {latest.get('cycle', '?')})"
            )

        print()

    def print_active_tasks(self, status: Dict):
        """Print active and completed tasks"""
        print(f"{Colors.BOLD}TASK QUEUE{Colors.ENDC}")
        print("─" * 80)

        active = status.get("active_tasks", [])
        completed = status.get("completed_tasks", [])

        if active:
            print(f"  {Colors.WARNING}Active Tasks:{Colors.ENDC}")
            for task in active[-5:]:  # Last 5
                task_type = task.get("type", "unknown")
                started = task.get("started_at", "")
                epochs = task.get("epochs", "")
                print(f"    • {task_type} (epochs: {epochs}) - started {started}")
        else:
            print(f"  {Colors.OKGREEN}No active tasks{Colors.ENDC}")

        if completed:
            print(f"\n  Completed: {len(completed)} tasks")

        print()

    def print_recent_logs(self):
        """Print recent log entries"""
        print(f"{Colors.BOLD}RECENT ACTIVITY{Colors.ENDC}")
        print("─" * 80)

        logs = self.get_recent_logs(10)

        if not logs:
            print("  No log entries")
            print()
            return

        for log in logs:
            log = log.strip()
            if not log:
                continue

            # Color code by log level
            if "ERROR" in log or "FAIL" in log:
                print(f"  {Colors.FAIL}{log}{Colors.ENDC}")
            elif "WARNING" in log or "WARN" in log:
                print(f"  {Colors.WARNING}{log}{Colors.ENDC}")
            elif "SUCCESS" in log or "✅" in log:
                print(f"  {Colors.OKGREEN}{log}{Colors.ENDC}")
            else:
                print(f"  {log}")

        print()

    def print_alerts(self, status: Dict):
        """Print any alerts or warnings"""
        alerts = []

        # Check for errors
        phase = status.get("current_phase", status.get("status", "unknown"))
        if phase == "error":
            alerts.append(("ERROR", status.get("error", "Unknown error")))

        # Check for stopped state
        if phase == "stopped":
            alerts.append(("WARNING", "Training orchestrator is stopped"))

        # Check for performance degradation
        history = status.get("performance_history", [])
        if len(history) >= 2:
            prev = history[-2].get("mean_accuracy", history[-2].get("accuracy", 0))
            curr = history[-1].get("mean_accuracy", history[-1].get("accuracy", 0))
            if curr < prev - 0.05:
                alerts.append(
                    ("WARNING", f"Performance degradation: {prev:.2%} → {curr:.2%}")
                )

        # Check dataset count
        total = status.get("total_datasets_available")
        if total is None:
            inventory = status.get("dataset_inventory", {})
            total = sum(
                v.get("count", 0) if isinstance(v, dict) else int(v)
                for v in inventory.values()
            )
        if total < 100:
            alerts.append(("WARNING", f"Low dataset count: {total}"))

        if alerts:
            print(f"{Colors.BOLD}ALERTS{Colors.ENDC}")
            print("─" * 80)
            for level, message in alerts:
                if level == "ERROR":
                    print(f"  {Colors.FAIL}❌ {message}{Colors.ENDC}")
                else:
                    print(f"  {Colors.WARNING}⚠️  {message}{Colors.ENDC}")
            print()

    def print_dashboard(self):
        """Print complete monitoring dashboard"""
        self.clear_screen()
        self.print_header()

        status = self.load_status()

        if status is None:
            print(
                f"{Colors.WARNING}⚠️  Status file not found. Is the orchestrator running?{Colors.ENDC}"
            )
            print(
                "\nStart it with: python ./scripts/autonomous_training_demo.py --cycles 3 --interval 5"
            )
            return

        self.print_overview(status)
        self.print_heartbeat()
        self.print_alerts(status)
        self.print_datasets(status)
        self.print_performance(status)
        self.print_active_tasks(status)
        self.print_recent_logs()

        print(f"{Colors.BOLD}{'─'*80}{Colors.ENDC}")
        print("Press Ctrl+C to exit  |  Refreshing every 5 seconds...")

    def print_summary(self):
        """Print compact summary"""
        status = self.load_status()
        heartbeat = self.load_heartbeat()

        if status is None:
            print(f"{Colors.WARNING}Status file not found{Colors.ENDC}")
            return

        phase = status.get("current_phase", status.get("status", "unknown"))
        cycles = status.get("cycles_completed", 0)
        best_acc = status.get("best_accuracy", 0)
        total = status.get("total_datasets_available")
        if total is None:
            inventory = status.get("dataset_inventory", {})
            total = sum(
                v.get("count", 0) if isinstance(v, dict) else int(v)
                for v in inventory.values()
            )

        print(f"\n{'='*80}")
        print("AUTONOMOUS TRAINING STATUS")
        print(f"{'='*80}")
        print(f"Phase: {phase.upper()}")
        print(f"Cycles: {cycles}")
        print(f"Best Accuracy: {best_acc:.2%}")
        print(f"Datasets: {total}")
        print(f"Plateau Cycles: {status.get('plateau_cycles', 0)}")
        promotions = status.get("promotions", [])
        print(f"Promotions: {len(promotions)}")
        if heartbeat:
            print(
                f"Heartbeat: {heartbeat.get('state', 'unknown').upper()} @ {heartbeat.get('timestamp', '-')}"
            )
            if heartbeat.get("next_cycle_eta"):
                print(f"Next Cycle ETA: {heartbeat.get('next_cycle_eta')}")

        history = status.get("performance_history", [])
        if history:
            latest = history[-1]
            print("\nLatest Results:")
            print(f"  Epochs: {latest.get('epochs', '-')}")
            print(
                f"  Mean Accuracy: {latest.get('mean_accuracy', latest.get('accuracy', 0)):.2%}"
            )
            print(
                f"  Max Accuracy: {latest.get('max_accuracy', latest.get('accuracy', 0)):.2%}"
            )
            print(
                f"  Successful: {latest.get('successful_count', latest.get('datasets_trained', 0))}"
            )
            print(f"  Exceptional: {latest.get('exceptional_models', 0)}")

        print(f"{'='*80}\n")

    def monitor_continuous(self, refresh_seconds: int = 5):
        """Monitor in continuous mode with auto-refresh"""
        try:
            while True:
                self.print_dashboard()
                time.sleep(refresh_seconds)
        except KeyboardInterrupt:
            print(f"\n\n{Colors.OKGREEN}Monitoring stopped{Colors.ENDC}\n")

    def export_metrics(self, output_file: str = "data_out/training_metrics.csv"):
        """Export metrics to CSV for analysis"""
        status = self.load_status()

        if not status or "performance_history" not in status:
            print("No metrics to export")
            return

        import csv

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "cycle",
                    "epochs",
                    "mean_accuracy",
                    "median_accuracy",
                    "max_accuracy",
                    "successful_count",
                    "failed_count",
                    "exceptional_models",
                    "excellent_models",
                ],
            )
            writer.writeheader()

            for i, perf in enumerate(status["performance_history"], start=1):
                mean_acc = perf.get("mean_accuracy", perf.get("accuracy", 0))
                max_acc = perf.get("max_accuracy", perf.get("accuracy", mean_acc))
                writer.writerow(
                    {
                        "timestamp": perf.get("timestamp", ""),
                        "cycle": perf.get("cycle", i),
                        "epochs": perf.get("epochs", ""),
                        "mean_accuracy": mean_acc,
                        "median_accuracy": perf.get("median_accuracy", 0),
                        "max_accuracy": max_acc,
                        "successful_count": perf.get(
                            "successful_count", perf.get("datasets_trained", 0)
                        ),
                        "failed_count": perf.get("failed_count", 0),
                        "exceptional_models": perf.get("exceptional_models", 0),
                        "excellent_models": perf.get("excellent_models", 0),
                    }
                )

        print(f"{Colors.OKGREEN}✅ Metrics exported to {output_path}{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description="Monitor Autonomous AI Training")
    parser.add_argument(
        "--status-file",
        default="data_out/autonomous_training_status.json",
        help="Path to status file",
    )
    parser.add_argument(
        "--log-file",
        default="data_out/autonomous_training.log",
        help="Path to log file",
    )
    parser.add_argument("--summary", action="store_true", help="Print summary and exit")
    parser.add_argument("--export", metavar="FILE", help="Export metrics to CSV file")
    parser.add_argument(
        "--refresh",
        type=int,
        default=5,
        help="Refresh interval in seconds (default: 5)",
    )
    parser.add_argument("--once", action="store_true", help="Display once and exit")

    args = parser.parse_args()

    monitor = TrainingMonitor(args.status_file, args.log_file)

    if args.summary:
        monitor.print_summary()
    elif args.export:
        monitor.export_metrics(args.export)
    elif args.once:
        monitor.print_dashboard()
    else:
        monitor.monitor_continuous(args.refresh)


if __name__ == "__main__":
    main()
