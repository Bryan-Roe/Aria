#!/usr/bin/env python
"""VS Code Alert Monitor - Watches for issues and sends VS Code notifications

Runs in background and checks for problems every 30 seconds.
Sends notifications for:
- High CPU/memory/disk
- Failed jobs
- Accuracy decline
- Promotion failures
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.monitoring.auto_ops_dashboard import get_all_statuses


class VSCodeAlertMonitor:
    """Monitor auto operations and send alerts to VS Code"""
    
    def __init__(self):
        self.last_alerts = {}
        self.alert_cooldown = 300  # 5 minutes between same alerts
        
    def check_and_alert(self):
        """Check operations and send alerts"""
        statuses = get_all_statuses()
        current_time = datetime.now()
        
        alerts = []
        
        for status in statuses:
            # Check for errors
            if status.status == "error":
                alert_key = f"error_{status.name}"
                if self._should_alert(alert_key, current_time):
                    alerts.append({
                        "severity": "error",
                        "title": f"❌ {status.name} Failed",
                        "message": f"{status.name} operation failed. {', '.join(status.alerts[:2])}",
                        "key": alert_key
                    })
            
            # Check for alerts
            for alert_text in status.alerts:
                if "CPU at" in alert_text and any(x in alert_text for x in ["95", "96", "97", "98", "99"]):
                    alert_key = "cpu_high"
                    if self._should_alert(alert_key, current_time):
                        alerts.append({
                            "severity": "critical",
                            "title": "🔴 High CPU Usage",
                            "message": alert_text,
                            "key": alert_key
                        })
                
                elif "Memory at" in alert_text and int(alert_text.split("Memory at ")[1].split("%")[0]) > 85:
                    alert_key = "memory_high"
                    if self._should_alert(alert_key, current_time):
                        alerts.append({
                            "severity": "critical",
                            "title": "🔴 High Memory Usage",
                            "message": alert_text,
                            "key": alert_key
                        })
                
                elif "Disk at" in alert_text:
                    alert_key = "disk_high"
                    if self._should_alert(alert_key, current_time):
                        alerts.append({
                            "severity": "critical",
                            "title": "🔴 Disk Space Low",
                            "message": alert_text,
                            "key": alert_key
                        })
                
                elif "Accuracy declined" in alert_text:
                    alert_key = "accuracy_decline"
                    if self._should_alert(alert_key, current_time):
                        alerts.append({
                            "severity": "warning",
                            "title": "📉 Accuracy Decline",
                            "message": alert_text,
                            "key": alert_key
                        })
                
                elif "failed" in alert_text.lower() or "failed" in status.name.lower():
                    alert_key = f"failed_{status.name}"
                    if self._should_alert(alert_key, current_time):
                        alerts.append({
                            "severity": "error",
                            "title": f"❌ {status.name}",
                            "message": alert_text,
                            "key": alert_key
                        })
        
        return alerts
    
    def _should_alert(self, key, current_time):
        """Check if enough time has passed since last alert"""
        if key not in self.last_alerts:
            self.last_alerts[key] = current_time
            return True
        
        elapsed = (current_time - self.last_alerts[key]).total_seconds()
        if elapsed > self.alert_cooldown:
            self.last_alerts[key] = current_time
            return True
        
        return False


def run_monitor():
    """Run the monitor loop"""
    monitor = VSCodeAlertMonitor()
    
    print("✅ VS Code Alert Monitor started")
    print("Monitoring for: High CPU/memory/disk, failures, accuracy decline")
    print("Alert cooldown: 5 minutes (avoids spam)")
    print("\nChecking every 30 seconds...\n")
    
    try:
        while True:
            alerts = monitor.check_and_alert()
            
            for alert in alerts:
                emoji = "🔴" if alert["severity"] == "critical" else "⚠️" if alert["severity"] == "warning" else "❌"
                print(f"{emoji} [{alert['severity'].upper()}] {alert['title']}")
                print(f"   └─ {alert['message']}")
            
            time.sleep(30)
    
    except KeyboardInterrupt:
        print("\n✋ Monitor stopped")
        sys.exit(0)


if __name__ == "__main__":
    run_monitor()
