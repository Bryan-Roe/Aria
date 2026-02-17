"""
Advanced Analytics for Autonomous Training
Generates charts, trends, and insights
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


class TrainingAnalytics:
    """Analyze training performance and generate insights"""
    
    def __init__(self, status_file: str = "data_out/autonomous_training_status.json"):
        self.status_file = Path(status_file)
        self.status = self.load_status()
    
    def load_status(self) -> Dict:
        """Load status from file"""
        if not self.status_file.exists():
            return {}
        
        with open(self.status_file) as f:
            return json.load(f)
    
    def calculate_improvement_rate(self) -> float:
        """Calculate average improvement rate per cycle"""
        history = self.status.get("performance_history", [])
        
        if len(history) < 2:
            return 0.0
        
        first_acc = history[0].get("mean_accuracy", 0)
        last_acc = history[-1].get("mean_accuracy", 0)
        cycles = len(history)
        
        if cycles > 1:
            return (last_acc - first_acc) / (cycles - 1)
        return 0.0
    
    def predict_target_accuracy(self, target: float = 0.90) -> int:
        """Predict cycles needed to reach target accuracy"""
        history = self.status.get("performance_history", [])
        
        if not history:
            return 0
        
        current = history[-1].get("mean_accuracy", 0)
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
            epochs = perf.get("epochs", 0)
            accuracy = perf.get("mean_accuracy", 0)
            
            if epochs not in epoch_performance:
                epoch_performance[epochs] = []
            epoch_performance[epochs].append(accuracy)
        
        # Find epoch count with best average accuracy
        best_epochs = 100
        best_avg = 0
        
        for epochs, accuracies in epoch_performance.items():
            avg = sum(accuracies) / len(accuracies)
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
        accuracies = [p.get("mean_accuracy", 0) for p in recent]
        
        # Check if variance is very low
        avg = sum(accuracies) / len(accuracies)
        variance = sum((x - avg) ** 2 for x in accuracies) / len(accuracies)
        
        return variance < 0.0001  # Less than 0.01% variance
    
    def generate_report(self) -> str:
        """Generate comprehensive analytics report"""
        report = []
        report.append("\n" + "="*80)
        report.append("AUTONOMOUS TRAINING ANALYTICS REPORT")
        report.append("="*80 + "\n")
        
        # Overview
        cycles = self.status.get("cycles_completed", 0)
        best_acc = self.status.get("best_accuracy", 0)
        total_datasets = self.status.get("total_datasets_available", 0)
        
        report.append("OVERVIEW")
        report.append("-" * 80)
        report.append(f"Total Cycles: {cycles}")
        report.append(f"Best Accuracy: {best_acc:.2%}")
        report.append(f"Total Datasets: {total_datasets}")
        report.append("")
        
        # Performance trend
        history = self.status.get("performance_history", [])
        if history:
            report.append("PERFORMANCE TREND")
            report.append("-" * 80)
            
            first = history[0].get("mean_accuracy", 0)
            last = history[-1].get("mean_accuracy", 0)
            improvement = last - first
            
            report.append(f"Initial Accuracy: {first:.2%}")
            report.append(f"Current Accuracy: {last:.2%}")
            report.append(f"Total Improvement: {improvement:.2%} (+{improvement*100:.2f} percentage points)")
            
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
            report.append("Status: ⚠️  PLATEAU DETECTED - Consider increasing epochs or tuning hyperparameters")
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
            report.append(f"Exceptional (≥95%): {exceptional} ({exceptional/successful*100:.1f}%)")
            report.append(f"Excellent (85-95%): {excellent} ({excellent/successful*100:.1f}%)")
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
        
        if best_acc >= 0.90:
            report.append("• Ready for production deployment")
            report.append("• Enable auto_deploy_best in config")
        
        report.append("\n" + "="*80 + "\n")
        
        return "\n".join(report)
    
    def generate_ascii_chart(self, metric: str = "mean_accuracy") -> str:
        """Generate ASCII chart of performance over time"""
        history = self.status.get("performance_history", [])
        
        if not history:
            return "No data available"
        
        # Extract values
        values = [p.get(metric, 0) for p in history]
        
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
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Autonomous Training Analytics Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: #ecf0f1; border-radius: 5px; min-width: 200px; }}
        .metric-label {{ font-size: 14px; color: #7f8c8d; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
        .good {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .bad {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .chart {{ margin: 20px 0; padding: 20px; background: #f9f9f9; border-radius: 5px; }}
        .timestamp {{ color: #95a5a6; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Autonomous Training Analytics Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Key Metrics</h2>
        <div class="metric">
            <div class="metric-label">Cycles Completed</div>
            <div class="metric-value">{self.status.get('cycles_completed', 0)}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Best Accuracy</div>
            <div class="metric-value {'good' if self.status.get('best_accuracy', 0) >= 0.85 else 'warning' if self.status.get('best_accuracy', 0) >= 0.75 else 'bad'}">
                {self.status.get('best_accuracy', 0):.2%}
            </div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Datasets</div>
            <div class="metric-value">{self.status.get('total_datasets_available', 0)}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Improvement Rate</div>
            <div class="metric-value">{self.calculate_improvement_rate()*100:.3f}%</div>
            <div class="metric-label">per cycle</div>
        </div>
        
        <h2>Performance History</h2>
        <table>
            <tr>
                <th>Cycle</th>
                <th>Epochs</th>
                <th>Mean Accuracy</th>
                <th>Max Accuracy</th>
                <th>Exceptional Models</th>
                <th>Successful</th>
            </tr>
"""
        
        history = self.status.get("performance_history", [])
        for i, perf in enumerate(history, start=1):
            html += f"""
            <tr>
                <td>#{i}</td>
                <td>{perf.get('epochs', 0)}</td>
                <td>{perf.get('mean_accuracy', 0):.2%}</td>
                <td>{perf.get('max_accuracy', 0):.2%}</td>
                <td>{perf.get('exceptional_models', 0)}</td>
                <td>{perf.get('successful_count', 0)}</td>
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
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"✅ HTML report exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Training Analytics")
    parser.add_argument("--status-file", default="data_out/autonomous_training_status.json",
                       help="Path to status file")
    parser.add_argument("--report", action="store_true",
                       help="Generate text report")
    parser.add_argument("--chart", action="store_true",
                       help="Display ASCII chart")
    parser.add_argument("--html", metavar="FILE",
                       help="Export HTML report")
    parser.add_argument("--metric", default="mean_accuracy",
                       help="Metric to chart (default: mean_accuracy)")
    
    args = parser.parse_args()
    
    analytics = TrainingAnalytics(args.status_file)
    
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


if __name__ == "__main__":
    main()
