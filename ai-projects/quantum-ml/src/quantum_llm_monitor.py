"""
Quantum LLM Training Monitor & Visualization
=============================================

Real-time monitoring, logging, and visualization for quantum-enhanced
language model training.

Features:
- Real-time metrics dashboard
- Quantum circuit performance tracking
- Training progress visualization
- Resource utilization monitoring
- Alert system for anomalies

Author: Quantum AI Workspace
Date: March 9, 2026
"""

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class QuantumMetrics:
    """Quantum-specific training metrics."""

    circuit_execution_time: float = 0.0
    circuit_depth: int = 0
    gate_count: int = 0
    qubit_count: int = 0
    quantum_classical_ratio: float = 0.0
    cache_hit_rate: float = 0.0
    shots_per_circuit: int = 1000
    backend: str = "default.qubit"


@dataclass
class TrainingSnapshot:
    """Complete training state snapshot."""

    timestamp: float
    global_step: int
    epoch: int
    loss: float
    perplexity: float
    learning_rate: float
    batch_size: int
    quantum_metrics: QuantumMetrics
    gpu_memory_mb: float = 0.0
    cpu_percent: float = 0.0


class MetricsAggregator:
    """
    Aggregates and computes statistics on training metrics.
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.loss_history = deque(maxlen=window_size)
        self.perplexity_history = deque(maxlen=window_size)
        self.quantum_time_history = deque(maxlen=window_size)
        self.snapshots: List[TrainingSnapshot] = []

        logger.info(f"MetricsAggregator initialized: window_size={window_size}")

    def add_snapshot(self, snapshot: TrainingSnapshot):
        """Add a training snapshot."""
        self.loss_history.append(snapshot.loss)
        self.perplexity_history.append(snapshot.perplexity)
        self.quantum_time_history.append(
            snapshot.quantum_metrics.circuit_execution_time
        )
        self.snapshots.append(snapshot)

    def get_moving_average(self, metric: str, window: Optional[int] = None) -> float:
        """Compute moving average for a metric."""
        window = window or self.window_size

        if metric == "loss":
            history = list(self.loss_history)
        elif metric == "perplexity":
            history = list(self.perplexity_history)
        elif metric == "quantum_time":
            history = list(self.quantum_time_history)
        else:
            return 0.0

        if not history:
            return 0.0

        recent = history[-window:]
        return np.mean(recent)

    def get_trend(self, metric: str, window: int = 20) -> str:
        """
        Determine trend direction for a metric.

        Returns:
            "improving", "degrading", or "stable"
        """
        if metric == "loss":
            history = list(self.loss_history)
        elif metric == "perplexity":
            history = list(self.perplexity_history)
        else:
            return "unknown"

        if len(history) < window:
            return "insufficient_data"

        recent = history[-window:]
        first_half = np.mean(recent[: window // 2])
        second_half = np.mean(recent[window // 2 :])

        # For loss/perplexity, lower is better
        if second_half < first_half * 0.95:
            return "improving"
        elif second_half > first_half * 1.05:
            return "degrading"
        else:
            return "stable"

    def detect_anomalies(self, threshold: float = 3.0) -> List[Dict[str, Any]]:
        """
        Detect anomalous metrics using z-score.

        Args:
            threshold: Z-score threshold for anomaly detection

        Returns:
            List of detected anomalies
        """
        anomalies = []

        if len(self.loss_history) < 10:
            return anomalies

        losses = np.array(list(self.loss_history))
        mean_loss = np.mean(losses)
        std_loss = np.std(losses)

        if std_loss > 0:
            z_scores = (losses - mean_loss) / std_loss
            anomaly_indices = np.where(np.abs(z_scores) > threshold)[0]

            for idx in anomaly_indices:
                if idx < len(self.snapshots):
                    anomalies.append(
                        {
                            "type": "loss_anomaly",
                            "step": self.snapshots[idx].global_step,
                            "value": losses[idx],
                            "z_score": float(z_scores[idx]),
                        }
                    )

        return anomalies

    def get_summary(self) -> Dict[str, Any]:
        """Get complete metrics summary."""
        return {
            "total_snapshots": len(self.snapshots),
            "moving_avg_loss": self.get_moving_average("loss"),
            "moving_avg_perplexity": self.get_moving_average("perplexity"),
            "moving_avg_quantum_time": self.get_moving_average("quantum_time"),
            "loss_trend": self.get_trend("loss"),
            "perplexity_trend": self.get_trend("perplexity"),
            "anomalies": self.detect_anomalies(),
        }


class PerformanceMonitor:
    """
    Monitors system and quantum performance during training.
    """

    def __init__(self, enable_gpu_monitoring: bool = True):
        self.enable_gpu = enable_gpu_monitoring
        self.performance_history = []

        # Try to import psutil for CPU monitoring
        try:
            import psutil

            self.psutil = psutil
            self.psutil_available = True
        except ImportError:
            self.psutil_available = False
            logger.warning("psutil not available - CPU monitoring disabled")

        # Try to import for GPU monitoring
        try:
            import torch

            self.torch = torch
            self.torch_available = (
                torch.cuda.is_available() if self.enable_gpu else False
            )
        except ImportError:
            self.torch_available = False

        logger.info(
            f"PerformanceMonitor: CPU={self.psutil_available}, GPU={self.torch_available}"
        )

    def get_current_performance(self) -> Dict[str, float]:
        """Get current system performance metrics."""
        metrics = {
            "cpu_percent": 0.0,
            "memory_used_mb": 0.0,
            "memory_percent": 0.0,
            "gpu_memory_used_mb": 0.0,
            "gpu_utilization_percent": 0.0,
        }

        if self.psutil_available:
            metrics["cpu_percent"] = self.psutil.cpu_percent(interval=0.1)
            mem = self.psutil.virtual_memory()
            metrics["memory_used_mb"] = mem.used / (1024 * 1024)
            metrics["memory_percent"] = mem.percent

        if self.torch_available:
            try:
                metrics["gpu_memory_used_mb"] = self.torch.cuda.memory_allocated() / (
                    1024 * 1024
                )
            except:
                pass

        self.performance_history.append(
            {
                "timestamp": time.time(),
                **metrics,
            }
        )

        return metrics

    def get_resource_report(self) -> Dict[str, Any]:
        """Get comprehensive resource usage report."""
        if not self.performance_history:
            return {"status": "no_data"}

        recent = self.performance_history[-100:]

        return {
            "avg_cpu_percent": np.mean([p["cpu_percent"] for p in recent]),
            "max_cpu_percent": np.max([p["cpu_percent"] for p in recent]),
            "avg_memory_mb": np.mean([p["memory_used_mb"] for p in recent]),
            "max_memory_mb": np.max([p["memory_used_mb"] for p in recent]),
            "avg_gpu_memory_mb": np.mean([p["gpu_memory_used_mb"] for p in recent]),
            "max_gpu_memory_mb": np.max([p["gpu_memory_used_mb"] for p in recent]),
        }


class QuantumCircuitProfiler:
    """
    Profiles quantum circuit execution performance.
    """

    def __init__(self):
        self.circuit_profiles = defaultdict(list)

        logger.info("QuantumCircuitProfiler initialized")

    def profile_circuit(
        self,
        circuit_id: str,
        execution_time: float,
        gate_count: int,
        depth: int,
        qubit_count: int,
    ):
        """Record circuit execution profile."""
        self.circuit_profiles[circuit_id].append(
            {
                "timestamp": time.time(),
                "execution_time": execution_time,
                "gate_count": gate_count,
                "depth": depth,
                "qubit_count": qubit_count,
            }
        )

    def get_circuit_stats(self, circuit_id: str) -> Dict[str, Any]:
        """Get statistics for a specific circuit."""
        profiles = self.circuit_profiles.get(circuit_id, [])

        if not profiles:
            return {"status": "no_data"}

        execution_times = [p["execution_time"] for p in profiles]

        return {
            "executions": len(profiles),
            "avg_time": np.mean(execution_times),
            "min_time": np.min(execution_times),
            "max_time": np.max(execution_times),
            "std_time": np.std(execution_times),
            "avg_gate_count": np.mean([p["gate_count"] for p in profiles]),
            "avg_depth": np.mean([p["depth"] for p in profiles]),
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all circuits."""
        return {
            circuit_id: self.get_circuit_stats(circuit_id)
            for circuit_id in self.circuit_profiles.keys()
        }


class TrainingDashboard:
    """
    Real-time training dashboard with logging and alerts.
    """

    def __init__(
        self,
        output_dir: Path,
        update_interval: int = 10,
        enable_alerts: bool = True,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.update_interval = update_interval
        self.enable_alerts = enable_alerts

        # Components
        self.metrics_aggregator = MetricsAggregator()
        self.performance_monitor = PerformanceMonitor()
        self.circuit_profiler = QuantumCircuitProfiler()

        # State
        self.last_update = time.time()
        self.alerts: List[Dict[str, Any]] = []

        logger.info(f"TrainingDashboard initialized: output_dir={output_dir}")

    def update(self, snapshot: TrainingSnapshot):
        """Update dashboard with new training snapshot."""
        self.metrics_aggregator.add_snapshot(snapshot)

        # Update performance metrics
        perf_metrics = self.performance_monitor.get_current_performance()

        # Check if it's time for a dashboard update
        if time.time() - self.last_update >= self.update_interval:
            self._refresh_dashboard()
            self.last_update = time.time()

        # Check for alerts
        if self.enable_alerts:
            self._check_alerts(snapshot)

    def _refresh_dashboard(self):
        """Refresh dashboard display and save state."""
        summary = self.metrics_aggregator.get_summary()
        perf_report = self.performance_monitor.get_resource_report()
        circuit_stats = self.circuit_profiler.get_all_stats()

        dashboard_data = {
            "timestamp": time.time(),
            "metrics_summary": summary,
            "performance_report": perf_report,
            "circuit_stats": circuit_stats,
            "recent_alerts": self.alerts[-10:],
        }

        # Save to file
        dashboard_path = self.output_dir / "dashboard.json"
        with open(dashboard_path, "w") as f:
            json.dump(dashboard_data, f, indent=2)

        # Log summary
        logger.info("=" * 80)
        logger.info("TRAINING DASHBOARD")
        logger.info("=" * 80)
        logger.info(
            f"Loss (MA): {summary['moving_avg_loss']:.4f} [{summary['loss_trend']}]"
        )
        logger.info(
            f"Perplexity (MA): {summary['moving_avg_perplexity']:.2f} [{summary['perplexity_trend']}]"
        )
        logger.info(f"Quantum Time (MA): {summary['moving_avg_quantum_time']:.4f}s")

        if perf_report.get("status") != "no_data":
            logger.info(
                f"CPU: {perf_report['avg_cpu_percent']:.1f}% (max: {perf_report['max_cpu_percent']:.1f}%)"
            )
            logger.info(
                f"Memory: {perf_report['avg_memory_mb']:.0f}MB (max: {perf_report['max_memory_mb']:.0f}MB)"
            )

        if self.alerts:
            logger.info(
                f"Alerts: {len(self.alerts)} total, {len([a for a in self.alerts if a['severity'] == 'high'])} high"
            )

        logger.info("=" * 80)

    def _check_alerts(self, snapshot: TrainingSnapshot):
        """Check for alert conditions."""
        # Check loss anomalies
        anomalies = self.metrics_aggregator.detect_anomalies()
        for anomaly in anomalies:
            if not any(a.get("step") == anomaly["step"] for a in self.alerts):
                self.alerts.append(
                    {
                        "timestamp": time.time(),
                        "type": "anomaly",
                        "severity": "medium",
                        "message": f"Loss anomaly detected at step {anomaly['step']}",
                        "details": anomaly,
                    }
                )

        # Check degrading trends
        if self.metrics_aggregator.get_trend("loss") == "degrading":
            self.alerts.append(
                {
                    "timestamp": time.time(),
                    "type": "trend",
                    "severity": "low",
                    "message": "Loss trend is degrading",
                }
            )

        # Check high perplexity
        if snapshot.perplexity > 1000.0:
            self.alerts.append(
                {
                    "timestamp": time.time(),
                    "type": "perplexity",
                    "severity": "high",
                    "message": f"Very high perplexity: {snapshot.perplexity:.2f}",
                }
            )

    def get_full_report(self) -> Dict[str, Any]:
        """Generate complete training report."""
        return {
            "metrics_summary": self.metrics_aggregator.get_summary(),
            "performance_report": self.performance_monitor.get_resource_report(),
            "circuit_stats": self.circuit_profiler.get_all_stats(),
            "alerts": self.alerts,
            "total_snapshots": len(self.metrics_aggregator.snapshots),
        }

    def save_report(self, filename: str = "training_report.json"):
        """Save complete report to file."""
        report = self.get_full_report()
        report_path = self.output_dir / filename

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved: {report_path}")
        return report_path


class VisualizationExporter:
    """
    Exports training data in formats suitable for visualization.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"VisualizationExporter: output_dir={output_dir}")

    def export_loss_curve(
        self, snapshots: List[TrainingSnapshot], filename: str = "loss_curve.json"
    ):
        """Export loss curve data."""
        data = {
            "steps": [s.global_step for s in snapshots],
            "loss": [s.loss for s in snapshots],
            "perplexity": [s.perplexity for s in snapshots],
        }

        path = self.output_dir / filename
        with open(path, "w") as f:
            json.dump(data, f)

        logger.info(f"Loss curve exported: {path}")
        return path

    def export_quantum_metrics(
        self, snapshots: List[TrainingSnapshot], filename: str = "quantum_metrics.json"
    ):
        """Export quantum-specific metrics."""
        data = {
            "steps": [s.global_step for s in snapshots],
            "circuit_time": [
                s.quantum_metrics.circuit_execution_time for s in snapshots
            ],
            "quantum_ratio": [
                s.quantum_metrics.quantum_classical_ratio for s in snapshots
            ],
            "cache_hit_rate": [s.quantum_metrics.cache_hit_rate for s in snapshots],
        }

        path = self.output_dir / filename
        with open(path, "w") as f:
            json.dump(data, f)

        logger.info(f"Quantum metrics exported: {path}")
        return path

    def export_all(self, snapshots: List[TrainingSnapshot]):
        """Export all available visualization data."""
        self.export_loss_curve(snapshots)
        self.export_quantum_metrics(snapshots)
        logger.info("All visualization data exported")


# Export components
__all__ = [
    "QuantumMetrics",
    "TrainingSnapshot",
    "MetricsAggregator",
    "PerformanceMonitor",
    "QuantumCircuitProfiler",
    "TrainingDashboard",
    "VisualizationExporter",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test components
    dashboard = TrainingDashboard(
        output_dir=Path("data_out/quantum_llm_dashboard"),
        update_interval=5,
    )

    # Simulate some training snapshots
    for step in range(20):
        snapshot = TrainingSnapshot(
            timestamp=time.time(),
            global_step=step,
            epoch=0,
            loss=5.0 - step * 0.1 + np.random.randn() * 0.1,
            perplexity=np.exp(5.0 - step * 0.1),
            learning_rate=1e-4,
            batch_size=16,
            quantum_metrics=QuantumMetrics(
                circuit_execution_time=0.1 + np.random.randn() * 0.01,
                circuit_depth=10,
                gate_count=50,
                qubit_count=4,
                quantum_classical_ratio=0.3,
                cache_hit_rate=0.5 + step * 0.02,
            ),
        )

        dashboard.update(snapshot)
        time.sleep(0.1)

    # Generate report
    report_path = dashboard.save_report()
    logger.info(f"✅ Dashboard test complete: {report_path}")

    # Export visualizations
    exporter = VisualizationExporter(Path("data_out/quantum_llm_visualizations"))
    exporter.export_all(dashboard.metrics_aggregator.snapshots)
    logger.info("✅ Visualization export complete")
