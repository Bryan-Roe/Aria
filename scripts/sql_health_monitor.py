"""
SQL Integration Health Monitor

Continuous health monitoring for SQL connections, pool saturation, and query performance.
Can run as standalone script or imported as module for integration with monitoring systems.

Usage:
    python sql_health_monitor.py [--interval 60] [--threshold-critical 90] [--alert-webhook URL]
    
Environment Variables:
    QAI_SQL_URL: Database connection string (required)
    QAI_HEALTH_CHECK_INTERVAL: Check interval in seconds (default: 60)
    QAI_SATURATION_CRITICAL: Critical saturation threshold (default: 90)
    QAI_ALERT_WEBHOOK: Webhook URL for critical alerts (optional)
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add shared modules to path
script_dir = Path(__file__).parent
repo_root = script_dir.parent
sys.path.insert(0, str(repo_root))

from shared.sql_engine import engine_stats, sql_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """SQL integration health monitor."""
    
    def __init__(
        self,
        interval: int = 60,
        threshold_warning: int = 80,
        threshold_critical: int = 90,
        alert_webhook: Optional[str] = None,
    ):
        """Initialize health monitor."""
        self.interval = interval
        self.threshold_warning = threshold_warning
        self.threshold_critical = threshold_critical
        self.alert_webhook = alert_webhook
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes between repeat alerts
        
    def check_health(self) -> Dict:
        """Perform health check and return status."""
        timestamp = datetime.now().isoformat()
        
        # Check SQL connectivity
        is_healthy, health_msg = sql_health()
        
        # Get pool metrics
        stats = engine_stats()
        
        # Determine overall status
        status = "healthy"
        alerts = []
        
        if not is_healthy:
            status = "critical"
            alerts.append({
                "level": "critical",
                "message": f"SQL connection failed: {health_msg}",
                "metric": "connectivity",
            })
        
        if stats:
            saturation = stats.get("saturation_pct", 0)
            
            if saturation >= self.threshold_critical:
                status = "critical"
                alerts.append({
                    "level": "critical",
                    "message": f"Pool saturation critical: {saturation}%",
                    "metric": "saturation",
                    "value": saturation,
                })
            elif saturation >= self.threshold_warning:
                if status == "healthy":
                    status = "warning"
                alerts.append({
                    "level": "warning",
                    "message": f"Pool saturation high: {saturation}%",
                    "metric": "saturation",
                    "value": saturation,
                })
            
            slow_queries = stats.get("slow_queries_1min", 0)
            if slow_queries > 10:
                if status == "healthy":
                    status = "warning"
                alerts.append({
                    "level": "warning",
                    "message": f"High slow query rate: {slow_queries} in last minute",
                    "metric": "slow_queries",
                    "value": slow_queries,
                })
        
        return {
            "timestamp": timestamp,
            "status": status,
            "connectivity": {
                "healthy": is_healthy,
                "message": health_msg,
            },
            "pool": stats if stats else {},
            "alerts": alerts,
        }
    
    def should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent based on cooldown period."""
        now = time.time()
        last_sent = self.last_alert_time.get(alert_key, 0)
        
        if now - last_sent >= self.alert_cooldown:
            self.last_alert_time[alert_key] = now
            return True
        
        return False
    
    def send_alert(self, health_status: Dict):
        """Send alert via webhook if configured."""
        if not self.alert_webhook:
            return
        
        critical_alerts = [a for a in health_status["alerts"] if a["level"] == "critical"]
        
        if not critical_alerts:
            return
        
        # Check cooldown for each alert type
        for alert in critical_alerts:
            alert_key = f"{alert['metric']}_{alert['level']}"
            
            if not self.should_send_alert(alert_key):
                logger.debug(f"Alert cooldown active for: {alert_key}")
                continue
            
            try:
                import requests
                
                payload = {
                    "timestamp": health_status["timestamp"],
                    "status": health_status["status"],
                    "alert": alert,
                    "pool_stats": health_status.get("pool", {}),
                }
                
                response = requests.post(
                    self.alert_webhook,
                    json=payload,
                    timeout=10,
                )
                
                if response.status_code == 200:
                    logger.info(f"Alert sent successfully: {alert['message']}")
                else:
                    logger.warning(f"Alert webhook returned status {response.status_code}")
                    
            except ImportError:
                logger.warning("requests library not available for webhook alerts")
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
    
    def run_once(self) -> Dict:
        """Run health check once and return status."""
        health_status = self.check_health()
        
        # Log status
        status_symbol = {"healthy": "✓", "warning": "⚠", "critical": "✗"}
        logger.info(f"{status_symbol[health_status['status']]} Status: {health_status['status'].upper()}")
        
        if health_status["connectivity"]["healthy"]:
            pool = health_status.get("pool", {})
            if pool:
                logger.info(
                    f"  Pool: {pool.get('checked_out', 0)}/{pool.get('size', 0)} "
                    f"({pool.get('saturation_pct', 0)}% saturated)"
                )
                logger.info(
                    f"  Slow queries (1 min): {pool.get('slow_queries_1min', 0)}"
                )
        else:
            logger.error(f"  Connection: {health_status['connectivity']['message']}")
        
        # Log alerts
        for alert in health_status["alerts"]:
            level_colors = {"warning": "WARNING", "critical": "ERROR"}
            log_level = level_colors.get(alert["level"], "INFO")
            getattr(logger, log_level.lower())(f"  {alert['message']}")
        
        # Send webhooks if needed
        self.send_alert(health_status)
        
        return health_status
    
    def run_continuous(self):
        """Run continuous health monitoring."""
        logger.info("========================================")
        logger.info("SQL Health Monitor - Continuous Mode")
        logger.info("========================================")
        logger.info(f"Check interval: {self.interval} seconds")
        logger.info(f"Warning threshold: {self.threshold_warning}%")
        logger.info(f"Critical threshold: {self.threshold_critical}%")
        logger.info(f"Alert webhook: {'configured' if self.alert_webhook else 'not configured'}")
        logger.info("")
        
        try:
            while True:
                self.run_once()
                logger.info("")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SQL Integration Health Monitor"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Check interval in seconds (default: 60 or QAI_HEALTH_CHECK_INTERVAL)",
    )
    parser.add_argument(
        "--threshold-warning",
        type=int,
        default=80,
        help="Warning threshold for saturation percentage (default: 80)",
    )
    parser.add_argument(
        "--threshold-critical",
        type=int,
        default=None,
        help="Critical threshold for saturation percentage (default: 90 or QAI_SATURATION_CRITICAL)",
    )
    parser.add_argument(
        "--alert-webhook",
        type=str,
        default=None,
        help="Webhook URL for critical alerts (default: QAI_ALERT_WEBHOOK)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run health check once and exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for --once mode)",
    )
    return parser.parse_args()


def main():
    """Main execution."""
    args = parse_args()
    
    # Get configuration from args or environment
    interval = args.interval or int(os.getenv("QAI_HEALTH_CHECK_INTERVAL", "60"))
    threshold_critical = args.threshold_critical or int(os.getenv("QAI_SATURATION_CRITICAL", "90"))
    alert_webhook = args.alert_webhook or os.getenv("QAI_ALERT_WEBHOOK")
    
    # Create monitor
    monitor = HealthMonitor(
        interval=interval,
        threshold_warning=args.threshold_warning,
        threshold_critical=threshold_critical,
        alert_webhook=alert_webhook,
    )
    
    if args.once:
        # Single check mode
        health_status = monitor.run_once()
        
        if args.json:
            print(json.dumps(health_status, indent=2))
        
        # Exit with appropriate code
        exit_codes = {"healthy": 0, "warning": 1, "critical": 2}
        return exit_codes.get(health_status["status"], 1)
    else:
        # Continuous monitoring mode
        monitor.run_continuous()
        return 0


if __name__ == "__main__":
    sys.exit(main())
