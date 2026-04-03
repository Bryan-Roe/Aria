"""
Advanced Analytics for Autonomous Training
Generates charts, trends, and insights
"""

import argparse
import os
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Ensure repository root is on sys.path as early as possible so subprocess
# invocations and test runners can import local packages reliably.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.json_utils import load_status_json  # noqa: E402


class TrainingAnalytics:
    """Analyze training performance and generate insights"""

    def __init__(self, status_file: str = "data_out/autonomous_training_status.json"):
        self.status_file = Path(status_file)
        self.status = self.load_status()

    def load_status(self) -> Dict:
        """Load status from file"""
        loaded = load_status_json(self.status_file)
        if loaded.get("_status_file_error"):
            return {}
        return {k: v for k, v in loaded.items() if not k.startswith("_status_file_")}

    @staticmethod
    def _get_accuracy(perf: Dict) -> float:
        """Get accuracy from either modern or legacy status schema."""
        return perf.get("mean_accuracy", perf.get("accuracy", 0.0))

    def calculate_improvement_rate(self) -> float:
        """Calculate average improvement rate per cycle"""
        history = self.status.get("performance_history", [])

        if len(history) < 2:
            return 0.0

        first_acc = self._get_accuracy(history[0])
        last_acc = self._get_accuracy(history[-1])
        cycles = len(history)

        if cycles > 1:
            return (last_acc - first_acc) / (cycles - 1)
        return 0.0

    def predict_target_accuracy(self, target: float = 0.90) -> int:
        """Predict cycles needed to reach target accuracy"""
        history = self.status.get("performance_history", [])

        if not history:
            return 0

        current = self._get_accuracy(history[-1])
        improvement_rate = self.calculate_improvement_rate()

        if improvement_rate <= 0 or current >= target:
            return 0

        cycles_needed = (target - current) / improvement_rate
        return int(cycles_needed) + 1

    def identify_best_epoch_count(self) -> int:
        """Identify optimal epoch count based on accuracy/time tradeoff"""
        history = self.status.get("performance_history", [])

        if not history:
            return 100

        # Group by epoch count and calculate average accuracy
        epoch_performance = {}

        for perf in history:
            epochs = perf.get("epochs")
            if not epochs:
                continue
            accuracy = self._get_accuracy(perf)

            if epochs not in epoch_performance:
                epoch_performance[epochs] = []
            epoch_performance[epochs].append(accuracy)

        if not epoch_performance:
            return 100

        best_epochs = 100
        best_avg = 0.0

        for epochs, accuracies in epoch_performance.items():
            avg = statistics.fmean(accuracies)
            if avg > best_avg:
                best_avg = avg
                best_epochs = epochs

        return best_epochs

    def detect_plateau(self, window: int = 3) -> bool:
        """Detect if performance has plateaued"""
        history = self.status.get("performance_history", [])

        if len(history) < window:
            return False

        recent = history[-window:]
        accuracies = [self._get_accuracy(p) for p in recent]

        # Check if variance is very low
        variance = statistics.pvariance(accuracies)

        return variance < 0.0001  # Less than 0.01% variance

    def generate_report(self) -> str:
        """Generate comprehensive analytics report"""
        report = []
        improvement_rate = 0.0
        report.append("\n" + "=" * 80)
        report.append("AUTONOMOUS TRAINING ANALYTICS REPORT")
        report.append("=" * 80 + "\n")

        # Overview
        cycles = self.status.get("cycles_completed", 0)
        best_acc = self.status.get("best_accuracy", 0)
        plateau_cycles = self.status.get("plateau_cycles", 0)
        promotions = self.status.get("promotions", [])
        total_datasets = self.status.get("total_datasets_available")
        if total_datasets is None:
            total_datasets = len(self.status.get("dataset_inventory", {}))

        report.append("OVERVIEW")
        report.append("-" * 80)
        report.append(f"Total Cycles: {cycles}")
        report.append(f"Best Accuracy: {best_acc:.2%}")
        report.append(f"Total Datasets: {total_datasets}")
        report.append(f"Plateau Cycles at Peak: {plateau_cycles}")
        report.append(f"Promotions Completed: {len(promotions)}")
        if promotions:
            p = promotions[-1]
            report.append(
                (
                    f"Latest Promotion: v{p.get('version', '?')} at cycle "
                    f"{p.get('cycle', '?')} ({p.get('accuracy', 0):.2%})"
                )
            )
        report.append("")

        # Performance trend
        history = self.status.get("performance_history", [])
        if history:
            report.append("PERFORMANCE TREND")
            report.append("-" * 80)

            first = self._get_accuracy(history[0])
            last = self._get_accuracy(history[-1])
            improvement = last - first

            report.append(f"Initial Accuracy: {first:.2%}")
            report.append(f"Current Accuracy: {last:.2%}")
            report.append(
                f"Total Improvement: {improvement:.2%} (+{improvement*100:.2f} percentage points)"
            )

            improvement_rate = self.calculate_improvement_rate()
            report.append(f"Improvement Rate: {improvement_rate*100:.3f}% per cycle")
            report.append("")

            # Predictions
            report.append("PREDICTIONS")
            report.append("-" * 80)

            for target in [0.80, 0.85, 0.90, 0.95]:
                cycles_needed = self.predict_target_accuracy(target)
                if cycles_needed > 0:
                    report.append(f"Cycles to reach {target:.0%}: ~{cycles_needed}")
            report.append("")

        # Epoch analysis
        best_epochs = self.identify_best_epoch_count()
        report.append("OPTIMIZATION INSIGHTS")
        report.append("-" * 80)
        report.append(f"Optimal Epoch Count: {best_epochs}")

        plateau = self.detect_plateau()
        if plateau:
            report.append(
                "Status: ⚠️  PLATEAU DETECTED - Consider increasing epochs or tuning hyperparameters"
            )
        else:
            report.append("Status: ✅ Model is still improving")
        report.append("")

        # Model quality breakdown
        if history:
            latest = history[-1]
            exceptional = latest.get("exceptional_models", 0)
            excellent = latest.get("excellent_models", 0)
            successful = latest.get("successful_count", 0)

            report.append("MODEL QUALITY BREAKDOWN (Latest Cycle)")
            report.append("-" * 80)
            denom = successful if successful > 0 else 1
            report.append(
                f"Exceptional (≥95%): {exceptional} ({exceptional/denom*100:.1f}%)"
            )
            report.append(
                f"Excellent (85-95%): {excellent} ({excellent/denom*100:.1f}%)"
            )
            report.append(f"Total Successful: {successful}")
            report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 80)

        if plateau:
            report.append("• Increase epoch count to 200+")
            report.append("• Enable hyperparameter tuning")
            report.append("• Try architecture evolution")
        elif improvement_rate < 0.001:
            report.append("• Progress is slow - consider boosting epochs")
        else:
            report.append("• Continue current training strategy")
            report.append("• Performance is improving steadily")

        if plateau_cycles >= 5:
            report.append(
                "• Plateau stable for 5+ cycles — promotion cadence is active"
            )
        if promotions:
            report.append("• Model promotion history available in status['promotions']")

        if best_acc >= 0.90:
            report.append("• Ready for production deployment")
            report.append("• Enable auto_deploy_best in config")

        report.append("\n" + "=" * 80 + "\n")

        return "\n".join(report)

    def generate_ascii_chart(self, metric: str = "mean_accuracy") -> str:
        """Generate ASCII chart of performance over time"""
        history = self.status.get("performance_history", [])

        if not history:
            return "No data available"

        # Extract values
        values = [p.get(metric, p.get("accuracy", 0)) for p in history]

        # Scale to chart height (20 rows)
        chart_height = 20
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            return "All values are equal"

        # Normalize values
        scaled = []
        for v in values:
            normalized = (v - min_val) / (max_val - min_val)
            scaled.append(int(normalized * (chart_height - 1)))

        # Build chart
        chart = []
        chart.append(f"\n{metric.upper()} OVER TIME")
        chart.append("─" * 80)
        chart.append(f"Max: {max_val:.2%}  │")

        for row in range(chart_height - 1, -1, -1):
            chars = []
            for value in scaled:
                if value >= row:
                    chars.append("█")
                else:
                    chars.append(" ")
            chart.append("            │" + "".join(chars))

        chart.append(f"Min: {min_val:.2%}  └" + "─" * len(scaled))
        chart.append(f"             Cycle: 1{' ' * (len(scaled) - 5)}{len(scaled)}")
        chart.append("")

        return "\n".join(chart)

    def export_html_report(self, output_file: str = "data_out/training_report.html"):
        """Export analytics as HTML report"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = f"""<!doctype html>
<html>
  <head>
    <meta charset='utf-8'>
    <title>Autonomous Training Report</title>
    <style>body{{font-family:Segoe UI, Arial, sans-serif;padding:24px}}</style>
  </head>
  <body>
    <h1>Autonomous Training Analytics Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <h2>Overview</h2>
    <ul>
      <li>Cycles completed: {self.status.get('cycles_completed', 0)}</li>
      <li>Best accuracy: {self.status.get('best_accuracy', 0):.2%}</li>
            <li>Total datasets: {self.status.get(
                    'total_datasets_available',
                    len(self.status.get('dataset_inventory', {})),
            )}</li>
    </ul>
    <h2>Report</h2>
    <pre>{self.generate_report()}</pre>
  </body>
</html>
"""

        history = self.status.get("performance_history", [])
        for i, perf in enumerate(history, start=1):
            row_mean = perf.get("mean_accuracy", perf.get("accuracy", 0))
            row_max = perf.get("max_accuracy", perf.get("accuracy", row_mean))
            html += f"""
            <tr>
                <td>#{i}</td>
                <td>{perf.get('epochs', '-')}</td>
                <td>{row_mean:.2%}</td>
                <td>{row_max:.2%}</td>
                <td>{perf.get('exceptional_models', 0)}</td>
                <td>{perf.get('successful_count', perf.get('datasets_trained', 0))}</td>
            </tr>
"""

        html += f"""
        </table>

        <h2>Analysis & Recommendations</h2>
        <div class="chart">
            <pre>{self.generate_report()}</pre>
        </div>
    </div>
</body>
</html>
"""

        with open(output_path, "w") as f:
            f.write(html)

        print(f"✅ HTML report exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Training Analytics")
    parser.add_argument(
        "--status-file",
        default="data_out/autonomous_training_status.json",
        help="Path to status file",
    )
    parser.add_argument("--report", action="store_true", help="Generate text report")
    parser.add_argument("--chart", action="store_true", help="Display ASCII chart")
    parser.add_argument("--html", metavar="FILE", help="Export HTML report")
    parser.add_argument(
        "--metric",
        default="mean_accuracy",
        help="Metric to chart (default: mean_accuracy)",
    )

    args = parser.parse_args()

    analytics = TrainingAnalytics(args.status_file)

    try:
        if args.report:
            print(analytics.generate_report())
        elif args.chart:
            print(analytics.generate_ascii_chart(args.metric))
        elif args.html:
            analytics.export_html_report(args.html)
        else:
            # Default: show report and chart
            print(analytics.generate_report())
            print(analytics.generate_ascii_chart())
    except BrokenPipeError:
        # Handle broken pipe when output is piped to commands like head
        _squelch_stdout_after_broken_pipe()
        return


def _squelch_stdout_after_broken_pipe() -> None:
    """Redirect stdout to /dev/null to prevent shutdown-time flush errors."""
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
        try:
            sys.stdout.flush()
        except BrokenPipeError:
            _squelch_stdout_after_broken_pipe()
            sys.exit(0)
    except BrokenPipeError:
        _squelch_stdout_after_broken_pipe()
        sys.exit(0)
