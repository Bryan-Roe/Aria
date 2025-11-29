#!/usr/bin/env python
"""
Resource Monitor

Real-time monitoring of system resources with alerts and historical tracking.

Features:
- CPU, memory, disk, GPU monitoring
- Threshold-based alerts
- Historical data collection
- Export to time-series format
- Integration with orchestrators

Usage examples (PowerShell):
  python .\\scripts\\resource_monitor.py --stream              # Real-time streaming
  python .\\scripts\\resource_monitor.py --snapshot            # Single snapshot
  python .\\scripts\\resource_monitor.py --history --hours 24  # Last 24 hours
  python .\\scripts\\resource_monitor.py --export csv          # Export to CSV
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Deque, Dict, List, Optional

try:
    import psutil
except ImportError:
    psutil = None

try:
    import GPUtil
except ImportError:
    GPUtil = None

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "resource_monitor"
HISTORY_FILE = DATA_OUT / "history.jsonl"


@dataclass
class ResourceSnapshot:
    """Single point-in-time resource measurement."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    gpu_count: int = 0
    gpu_utilization: List[float] = field(default_factory=list)
    gpu_memory_percent: List[float] = field(default_factory=list)
    process_count: int = 0
    load_average: Optional[List[float]] = None


@dataclass
class Alert:
    """Resource threshold alert."""
    timestamp: str
    resource: str
    value: float
    threshold: float
    message: str


class ResourceMonitor:
    """Monitors system resources in real-time."""
    
    def __init__(self, max_history: int = 1000):
        self.data_out = DATA_OUT
        self.data_out.mkdir(parents=True, exist_ok=True)
        self.max_history = max_history
        self.history: Deque[ResourceSnapshot] = deque(maxlen=max_history)
        
        # Alert thresholds
        self.thresholds = {
            "cpu_percent": 90.0,
            "memory_percent": 90.0,
            "disk_percent": 90.0,
            "gpu_utilization": 95.0,
            "gpu_memory_percent": 95.0,
        }
        
        self.alerts: List[Alert] = []
        self._load_history()
    
    def _load_history(self):
        """Load historical data from disk."""
        if HISTORY_FILE.exists():
            with HISTORY_FILE.open("r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        snapshot = ResourceSnapshot(**data)
                        self.history.append(snapshot)
                    except Exception:
                        pass
    
    def _save_snapshot(self, snapshot: ResourceSnapshot):
        """Append snapshot to history file."""
        with HISTORY_FILE.open("a") as f:
            f.write(json.dumps(snapshot.__dict__) + "\n")
    
    def capture_snapshot(self) -> ResourceSnapshot:
        """Capture current resource usage."""
        if psutil is None:
            # Return mock data if psutil not available
            return ResourceSnapshot(
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_gb=0.0,
                memory_total_gb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_total_gb=0.0,
            )
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory
        mem = psutil.virtual_memory()
        memory_percent = mem.percent
        memory_used_gb = mem.used / (1024 ** 3)
        memory_total_gb = mem.total / (1024 ** 3)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        
        # Process count
        process_count = len(psutil.pids())
        
        # Load average (Unix-like systems)
        load_average = None
        try:
            load_average = list(psutil.getloadavg())
        except (AttributeError, OSError):
            pass
        
        # GPU (if available)
        gpu_count = 0
        gpu_utilization = []
        gpu_memory_percent = []
        
        if GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()
                gpu_count = len(gpus)
                for gpu in gpus:
                    gpu_utilization.append(gpu.load * 100)
                    gpu_memory_percent.append(gpu.memoryUtil * 100)
            except Exception:
                pass
        
        snapshot = ResourceSnapshot(
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            gpu_count=gpu_count,
            gpu_utilization=gpu_utilization,
            gpu_memory_percent=gpu_memory_percent,
            process_count=process_count,
            load_average=load_average,
        )
        
        # Check thresholds and generate alerts
        self._check_thresholds(snapshot)
        
        return snapshot
    
    def _check_thresholds(self, snapshot: ResourceSnapshot):
        """Check if any thresholds are exceeded."""
        timestamp = snapshot.timestamp
        
        if snapshot.cpu_percent > self.thresholds["cpu_percent"]:
            alert = Alert(
                timestamp=timestamp,
                resource="cpu",
                value=snapshot.cpu_percent,
                threshold=self.thresholds["cpu_percent"],
                message=f"CPU usage {snapshot.cpu_percent:.1f}% exceeds threshold {self.thresholds['cpu_percent']:.1f}%"
            )
            self.alerts.append(alert)
            print(f"[monitor] ALERT: {alert.message}")
        
        if snapshot.memory_percent > self.thresholds["memory_percent"]:
            alert = Alert(
                timestamp=timestamp,
                resource="memory",
                value=snapshot.memory_percent,
                threshold=self.thresholds["memory_percent"],
                message=f"Memory usage {snapshot.memory_percent:.1f}% exceeds threshold {self.thresholds['memory_percent']:.1f}%"
            )
            self.alerts.append(alert)
            print(f"[monitor] ALERT: {alert.message}")
        
        if snapshot.disk_percent > self.thresholds["disk_percent"]:
            alert = Alert(
                timestamp=timestamp,
                resource="disk",
                value=snapshot.disk_percent,
                threshold=self.thresholds["disk_percent"],
                message=f"Disk usage {snapshot.disk_percent:.1f}% exceeds threshold {self.thresholds['disk_percent']:.1f}%"
            )
            self.alerts.append(alert)
            print(f"[monitor] ALERT: {alert.message}")
        
        # GPU alerts
        for i, util in enumerate(snapshot.gpu_utilization):
            if util > self.thresholds["gpu_utilization"]:
                alert = Alert(
                    timestamp=timestamp,
                    resource=f"gpu_{i}",
                    value=util,
                    threshold=self.thresholds["gpu_utilization"],
                    message=f"GPU {i} utilization {util:.1f}% exceeds threshold {self.thresholds['gpu_utilization']:.1f}%"
                )
                self.alerts.append(alert)
                print(f"[monitor] ALERT: {alert.message}")
    
    def stream_monitoring(self, interval: int = 5, duration: Optional[int] = None):
        """Stream real-time resource monitoring."""
        print("[monitor] Starting real-time monitoring...")
        print(f"[monitor] Interval: {interval}s")
        if duration:
            print(f"[monitor] Duration: {duration}s")
        print()
        
        start_time = time.time()
        
        try:
            while True:
                snapshot = self.capture_snapshot()
                self.history.append(snapshot)
                self._save_snapshot(snapshot)
                
                # Print snapshot
                print(f"[{snapshot.timestamp}]")
                print(f"  CPU: {snapshot.cpu_percent:5.1f}%")
                print(f"  Memory: {snapshot.memory_percent:5.1f}% ({snapshot.memory_used_gb:.1f}/{snapshot.memory_total_gb:.1f} GB)")
                print(f"  Disk: {snapshot.disk_percent:5.1f}% ({snapshot.disk_used_gb:.0f}/{snapshot.disk_total_gb:.0f} GB)")
                
                if snapshot.gpu_count > 0:
                    for i in range(snapshot.gpu_count):
                        print(f"  GPU {i}: {snapshot.gpu_utilization[i]:5.1f}% util, {snapshot.gpu_memory_percent[i]:5.1f}% mem")
                
                if snapshot.load_average:
                    print(f"  Load: {snapshot.load_average[0]:.2f}, {snapshot.load_average[1]:.2f}, {snapshot.load_average[2]:.2f}")
                
                print()
                
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    print("[monitor] Duration reached, stopping...")
                    break
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n[monitor] Monitoring stopped by user")
    
    def get_history(self, hours: Optional[int] = None) -> List[ResourceSnapshot]:
        """Get historical snapshots."""
        if hours is None:
            return list(self.history)
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return [s for s in self.history if s.timestamp >= cutoff_str]
    
    def export_csv(self, output_file: Optional[Path] = None):
        """Export history to CSV."""
        if output_file is None:
            output_file = self.data_out / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with output_file.open("w", newline="") as f:
            writer = csv.writer(f)
            
            # Header
            header = [
                "timestamp", "cpu_percent", "memory_percent", "memory_used_gb",
                "memory_total_gb", "disk_percent", "disk_used_gb", "disk_total_gb",
                "gpu_count", "process_count"
            ]
            writer.writerow(header)
            
            # Data
            for snapshot in self.history:
                row = [
                    snapshot.timestamp,
                    snapshot.cpu_percent,
                    snapshot.memory_percent,
                    snapshot.memory_used_gb,
                    snapshot.memory_total_gb,
                    snapshot.disk_percent,
                    snapshot.disk_used_gb,
                    snapshot.disk_total_gb,
                    snapshot.gpu_count,
                    snapshot.process_count,
                ]
                writer.writerow(row)
        
        print(f"[monitor] Exported {len(self.history)} snapshots to: {output_file}")
        return output_file
    
    def get_summary(self, hours: Optional[int] = None) -> Dict:
        """Get summary statistics."""
        history = self.get_history(hours)
        
        if not history:
            return {"error": "No data available"}
        
        cpu_values = [s.cpu_percent for s in history]
        mem_values = [s.memory_percent for s in history]
        disk_values = [s.disk_percent for s in history]
        
        return {
            "period": f"Last {hours} hours" if hours else "All time",
            "sample_count": len(history),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
            },
            "memory": {
                "avg": sum(mem_values) / len(mem_values),
                "min": min(mem_values),
                "max": max(mem_values),
            },
            "disk": {
                "avg": sum(disk_values) / len(disk_values),
                "min": min(disk_values),
                "max": max(disk_values),
            },
            "alerts": len(self.alerts),
        }


def main():
    ap = argparse.ArgumentParser(description="Resource Monitor")
    ap.add_argument("--stream", action="store_true", help="Start real-time monitoring")
    ap.add_argument("--snapshot", action="store_true", help="Capture single snapshot")
    ap.add_argument("--history", action="store_true", help="Show historical data")
    ap.add_argument("--summary", action="store_true", help="Show summary statistics")
    ap.add_argument("--export", choices=["csv", "json"], help="Export data")
    ap.add_argument("--interval", type=int, default=5, help="Monitoring interval (seconds)")
    ap.add_argument("--duration", type=int, help="Monitoring duration (seconds)")
    ap.add_argument("--hours", type=int, help="Hours of history to show")
    ap.add_argument("--set-threshold", nargs=2, metavar=("RESOURCE", "VALUE"), help="Set alert threshold")
    args = ap.parse_args()
    
    monitor = ResourceMonitor()
    
    if args.set_threshold:
        resource, value = args.set_threshold
        if resource in monitor.thresholds:
            monitor.thresholds[resource] = float(value)
            print(f"[monitor] Set threshold {resource} = {value}")
        else:
            print(f"[monitor] Unknown resource: {resource}")
            print(f"[monitor] Available: {', '.join(monitor.thresholds.keys())}")
        return
    
    if args.stream:
        monitor.stream_monitoring(interval=args.interval, duration=args.duration)
        return
    
    if args.snapshot:
        snapshot = monitor.capture_snapshot()
        print(json.dumps(snapshot.__dict__, indent=2))
        return
    
    if args.history:
        history = monitor.get_history(hours=args.hours)
        print(f"[monitor] Historical snapshots: {len(history)}\n")
        for snapshot in history[-10:]:  # Last 10
            print(f"{snapshot.timestamp}: CPU {snapshot.cpu_percent:.1f}%, Mem {snapshot.memory_percent:.1f}%, Disk {snapshot.disk_percent:.1f}%")
        return
    
    if args.summary:
        summary = monitor.get_summary(hours=args.hours)
        print(json.dumps(summary, indent=2))
        return
    
    if args.export:
        if args.export == "csv":
            monitor.export_csv()
        elif args.export == "json":
            output_file = monitor.data_out / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with output_file.open("w") as f:
                data = [s.__dict__ for s in monitor.history]
                json.dump(data, f, indent=2)
            print(f"[monitor] Exported to: {output_file}")
        return
    
    # Default: show help
    ap.print_help()


if __name__ == "__main__":
    main()
