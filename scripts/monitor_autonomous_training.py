"""
Real-time Monitoring Dashboard for Autonomous AI Training
Provides live status, metrics, and alerts
"""

import json
import os
import sys
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TrainingMonitor:
    """Monitor autonomous training in real-time"""
    
    def __init__(self, status_file: str = "data_out/autonomous_training_status.json",
                 log_file: str = "data_out/autonomous_training.log"):
        self.status_file = Path(status_file)
        self.log_file = Path(log_file)
        self.last_status = None
        self.last_log_position = 0
        
    def clear_screen(self):
        """Clear terminal screen"""
        try:
            if os.name == 'nt':
                subprocess.run(['cmd', '/c', 'cls'], check=False)
            else:
                subprocess.run(['clear'], check=False)
        except Exception:
            # If clearing fails, just print newlines
            print('\n' * 50)
    
    def load_status(self) -> Optional[Dict]:
        """Load current status from file"""
        if not self.status_file.exists():
            return None
        
        try:
            with open(self.status_file) as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}
    
    def get_recent_logs(self, lines: int = 20) -> List[str]:
        """Get recent log entries"""
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
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
        print(f"{Colors.BOLD}{Colors.HEADER}🤖 AUTONOMOUS AI TRAINING MONITOR{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        print(f"📊 Status File: {self.status_file}")
        print(f"📝 Log File: {self.log_file}")
        print(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    def print_overview(self, status: Dict):
        """Print system overview"""
        print(f"{Colors.BOLD}SYSTEM OVERVIEW{Colors.ENDC}")
        print("─" * 80)
        
        if "error" in status:
            print(f"{Colors.FAIL}❌ Error loading status: {status['error']}{Colors.ENDC}")
            return
        
        # Basic info
        started = status.get("started_at", "Unknown")
        phase = status.get("current_phase", "unknown")
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
            "error": Colors.FAIL
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
        
        print()
    
    def print_datasets(self, status: Dict):
        """Print dataset information"""
        print(f"{Colors.BOLD}DATASET INVENTORY{Colors.ENDC}")
        print("─" * 80)
        
        inventory = status.get("dataset_inventory", {})
        total = status.get("total_datasets_available", 0)
        
        if inventory:
            for category, count in inventory.items():
                print(f"  {category:20s}: {Colors.BOLD}{count:4d}{Colors.ENDC} datasets")
        
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
        
        print(f"  {'Cycle':<8} {'Epochs':<8} {'Mean Acc':<12} {'Max Acc':<12} {'Models':<10}")
        print("  " + "─" * 70)
        
        for i, perf in enumerate(recent, start=len(history)-len(recent)+1):
            mean_acc = perf.get("mean_accuracy", 0)
            max_acc = perf.get("max_accuracy", 0)
            epochs = perf.get("epochs", 0)
            successful = perf.get("successful_count", 0)
            
            mean_str = f"{mean_acc*100:.2f}%"
            max_str = f"{max_acc*100:.2f}%"
            
            print(f"  #{i:<7} {epochs:<8} {mean_str:<12} {max_str:<12} {successful:<10}")
        
        # Trend analysis
        if len(history) >= 2:
            prev_acc = history[-2].get("mean_accuracy", 0)
            curr_acc = history[-1].get("mean_accuracy", 0)
            diff = curr_acc - prev_acc
            
            if diff > 0.01:
                trend = f"{Colors.OKGREEN}↑ +{diff*100:.2f}% (Improving){Colors.ENDC}"
            elif diff < -0.01:
                trend = f"{Colors.FAIL}↓ {diff*100:.2f}% (Declining){Colors.ENDC}"
            else:
                trend = f"{Colors.WARNING}→ Stable{Colors.ENDC}"
            
            print(f"\n  Trend: {trend}")
        
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
        if status.get("current_phase") == "error":
            alerts.append(("ERROR", status.get("error", "Unknown error")))
        
        # Check for stopped state
        if status.get("current_phase") == "stopped":
            alerts.append(("WARNING", "Training orchestrator is stopped"))
        
        # Check for performance degradation
        history = status.get("performance_history", [])
        if len(history) >= 2:
            prev = history[-2].get("mean_accuracy", 0)
            curr = history[-1].get("mean_accuracy", 0)
            if curr < prev - 0.05:
                alerts.append(("WARNING", f"Performance degradation: {prev:.2%} → {curr:.2%}"))
        
        # Check dataset count
        total = status.get("total_datasets_available", 0)
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
            print(f"{Colors.WARNING}⚠️  Status file not found. Is the orchestrator running?{Colors.ENDC}")
            print(f"\\nStart it with: python .\\scripts\\autonomous_training_orchestrator.py")
            return
        
        self.print_overview(status)
        self.print_alerts(status)
        self.print_datasets(status)
        self.print_performance(status)
        self.print_active_tasks(status)
        self.print_recent_logs()
        
        print(f"{Colors.BOLD}{'─'*80}{Colors.ENDC}")
        print(f"Press Ctrl+C to exit  |  Refreshing every 5 seconds...")
    
    def print_summary(self):
        """Print compact summary"""
        status = self.load_status()
        
        if status is None:
            print(f"{Colors.WARNING}Status file not found{Colors.ENDC}")
            return
        
        phase = status.get("current_phase", "unknown")
        cycles = status.get("cycles_completed", 0)
        best_acc = status.get("best_accuracy", 0)
        total = status.get("total_datasets_available", 0)
        
        print(f"\n{'='*80}")
        print(f"AUTONOMOUS TRAINING STATUS")
        print(f"{'='*80}")
        print(f"Phase: {phase.upper()}")
        print(f"Cycles: {cycles}")
        print(f"Best Accuracy: {best_acc:.2%}")
        print(f"Datasets: {total}")
        
        history = status.get("performance_history", [])
        if history:
            latest = history[-1]
            print(f"\nLatest Results:")
            print(f"  Epochs: {latest.get('epochs', 0)}")
            print(f"  Mean Accuracy: {latest.get('mean_accuracy', 0):.2%}")
            print(f"  Max Accuracy: {latest.get('max_accuracy', 0):.2%}")
            print(f"  Successful: {latest.get('successful_count', 0)}")
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
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'cycle', 'epochs', 'mean_accuracy', 'median_accuracy',
                'max_accuracy', 'successful_count', 'failed_count',
                'exceptional_models', 'excellent_models'
            ])
            writer.writeheader()
            
            for i, perf in enumerate(status["performance_history"], start=1):
                writer.writerow({
                    'timestamp': perf.get('timestamp', ''),
                    'cycle': i,
                    'epochs': perf.get('epochs', 0),
                    'mean_accuracy': perf.get('mean_accuracy', 0),
                    'median_accuracy': perf.get('median_accuracy', 0),
                    'max_accuracy': perf.get('max_accuracy', 0),
                    'successful_count': perf.get('successful_count', 0),
                    'failed_count': perf.get('failed_count', 0),
                    'exceptional_models': perf.get('exceptional_models', 0),
                    'excellent_models': perf.get('excellent_models', 0)
                })
        
        print(f"{Colors.OKGREEN}✅ Metrics exported to {output_path}{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description="Monitor Autonomous AI Training")
    parser.add_argument("--status-file", default="data_out/autonomous_training_status.json",
                       help="Path to status file")
    parser.add_argument("--log-file", default="data_out/autonomous_training.log",
                       help="Path to log file")
    parser.add_argument("--summary", action="store_true",
                       help="Print summary and exit")
    parser.add_argument("--export", metavar="FILE",
                       help="Export metrics to CSV file")
    parser.add_argument("--refresh", type=int, default=5,
                       help="Refresh interval in seconds (default: 5)")
    parser.add_argument("--once", action="store_true",
                       help="Display once and exit")
    
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
