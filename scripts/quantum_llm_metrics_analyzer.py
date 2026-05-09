#!/usr/bin/env python3
"""Quantum LLM training metrics collector and analyzer.

Collects metrics from quantum LLM status files over time and provides
analysis of training progress, loss trends, and performance improvements.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


def load_status(status_file: Path) -> dict[str, Any] | None:
    """Load status from JSON file."""
    if not status_file.exists():
        return None
    try:
        return json.loads(status_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def extract_metrics(status: dict[str, Any]) -> dict[str, Any]:
    """Extract key metrics from status data."""
    return {
        "timestamp": status.get("last_updated"),
        "status": status.get("status"),
        "epochs_completed": status.get("epochs_completed", 0),
        "best_loss": status.get("best_loss"),
        "final_loss": status.get("final_loss"),
        "inference_ready": status.get("inference_ready", False),
        "checkpoint_exists": status.get("checkpoint_exists", False),
    }


def analyze_metrics(metrics_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze a list of metrics for trends and statistics."""
    if not metrics_list:
        return {}

    # Extract numeric values
    best_losses = [m["best_loss"] for m in metrics_list if m.get("best_loss")]
    final_losses = [m["final_loss"] for m in metrics_list if m.get("final_loss")]
    epochs = [m["epochs_completed"] for m in metrics_list if m.get("epochs_completed")]

    analysis = {
        "total_snapshots": len(metrics_list),
        "inference_ready_count": sum(
            1 for m in metrics_list if m.get("inference_ready")
        ),
        "checkpoint_count": sum(1 for m in metrics_list if m.get("checkpoint_exists")),
    }

    # Loss statistics
    if best_losses:
        analysis["best_loss"] = {
            "min": min(best_losses),
            "max": max(best_losses),
            "mean": statistics.mean(best_losses),
            "count": len(best_losses),
        }
        if len(best_losses) > 1:
            analysis["best_loss"]["stdev"] = statistics.stdev(best_losses)

    if final_losses:
        analysis["final_loss"] = {
            "min": min(final_losses),
            "max": max(final_losses),
            "mean": statistics.mean(final_losses),
            "count": len(final_losses),
        }
        if len(final_losses) > 1:
            analysis["final_loss"]["stdev"] = statistics.stdev(final_losses)

    # Epoch statistics
    if epochs:
        analysis["epochs"] = {
            "current": epochs[-1] if epochs else 0,
            "max": max(epochs),
            "mean": statistics.mean(epochs),
        }

    # Trend analysis
    if len(final_losses) >= 2:
        improvement = final_losses[0] - final_losses[-1]
        improvement_pct = (
            (improvement / final_losses[0] * 100) if final_losses[0] != 0 else 0
        )
        analysis["trend"] = {
            "first_loss": final_losses[0],
            "latest_loss": final_losses[-1],
            "improvement": improvement,
            "improvement_percentage": improvement_pct,
        }

    return analysis


def format_analysis_report(analysis: dict[str, Any]) -> str:
    """Format analysis results as human-readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append("Quantum LLM Training Metrics Analysis")
    lines.append("=" * 60)

    lines.append("\n📊 Snapshot Summary:")
    lines.append(f"  Total snapshots:    {analysis.get('total_snapshots', 0)}")
    lines.append(f"  Inference ready:    {analysis.get('inference_ready_count', 0)}")
    lines.append(f"  Checkpoints saved:  {analysis.get('checkpoint_count', 0)}")

    if "best_loss" in analysis:
        bl = analysis["best_loss"]
        lines.append("\n🎯 Best Loss:")
        lines.append(f"  Minimum:  {bl.get('min', 'N/A'):.6f}")
        lines.append(f"  Maximum:  {bl.get('max', 'N/A'):.6f}")
        lines.append(f"  Average:  {bl.get('mean', 'N/A'):.6f}")
        if "stdev" in bl:
            lines.append(f"  Std Dev:  {bl['stdev']:.6f}")

    if "final_loss" in analysis:
        fl = analysis["final_loss"]
        lines.append("\n📉 Final Loss:")
        lines.append(f"  Minimum:  {fl.get('min', 'N/A'):.6f}")
        lines.append(f"  Maximum:  {fl.get('max', 'N/A'):.6f}")
        lines.append(f"  Average:  {fl.get('mean', 'N/A'):.6f}")
        if "stdev" in fl:
            lines.append(f"  Std Dev:  {fl['stdev']:.6f}")

    if "epochs" in analysis:
        ep = analysis["epochs"]
        lines.append("\n⏱️  Epoch Statistics:")
        lines.append(f"  Current:  {ep.get('current', 0)}")
        lines.append(f"  Maximum:  {ep.get('max', 0)}")
        lines.append(f"  Average:  {ep.get('mean', 0):.1f}")

    if "trend" in analysis:
        tr = analysis["trend"]
        lines.append("\n📈 Training Trend:")
        lines.append(f"  First loss:  {tr.get('first_loss', 'N/A'):.6f}")
        lines.append(f"  Latest loss: {tr.get('latest_loss', 'N/A'):.6f}")
        improvement = tr.get("improvement", 0)
        improvement_pct = tr.get("improvement_percentage", 0)
        emoji = "✓" if improvement > 0 else "✗"
        lines.append(
            f"  {emoji} Improvement: {improvement:.6f} ({improvement_pct:.2f}%)"
        )

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze quantum LLM training metrics history"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data_out/quantum_llm_training"),
        help="Training output directory (default: data_out/quantum_llm_training)",
    )
    parser.add_argument(
        "--history",
        type=int,
        default=0,
        help="Show last N status snapshots (0 = all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output metrics as JSON",
    )
    parser.add_argument(
        "--export",
        type=Path,
        help="Export metrics to CSV file",
    )

    args = parser.parse_args()

    # Load current status
    status_file = args.output / "status.json"
    status = load_status(status_file)

    if not status:
        print(f"❌ No status file found at {status_file}")
        return

    # Extract metrics
    metrics = extract_metrics(status)

    # Build metrics list (single snapshot for now, could be extended)
    metrics_list = [metrics]

    # Analyze
    analysis = analyze_metrics(metrics_list)

    if args.json:
        # Output as JSON
        print(json.dumps({"metrics": metrics, "analysis": analysis}, indent=2))
    else:
        # Output human-readable report
        report = format_analysis_report(analysis)
        print(report)

        # Show current status details
        print("\n📋 Current Status Details:")
        print(f"  Status:       {status.get('status', 'unknown')}")
        print(f"  Mode:         {status.get('mode', 'unknown')}")
        if status.get("started_at"):
            print(f"  Started:      {status.get('started_at')}")
        if status.get("completed_at"):
            print(f"  Completed:    {status.get('completed_at')}")
        if status.get("last_error"):
            print(f"  Error:        {status.get('last_error')}")

    # Export to CSV if requested
    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            f.write(
                "timestamp,status,epochs_completed,best_loss,final_loss,inference_ready\n"
            )
            for m in metrics_list:
                f.write(
                    f"{m.get('timestamp', '')},{m.get('status', '')},{m.get('epochs_completed', '')}"
                    f",{m.get('best_loss', '')},{m.get('final_loss', '')},{m.get('inference_ready', '')}\n"
                )
        print(f"\n✓ Exported metrics to {args.export}")


if __name__ == "__main__":
    main()
