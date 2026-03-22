#!/usr/bin/env python3
"""
Check and display Quantum LLM training status.

Usage:
    python scripts/quantum_llm_status_check.py                    # Default output_dir
    python scripts/quantum_llm_status_check.py --output data_out/custom_dir
    python scripts/quantum_llm_status_check.py --json              # Machine-readable JSON
    python scripts/quantum_llm_status_check.py --watch             # Auto-refresh every 5s
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add scripts to path for quantum_llm_trainer imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from quantum_llm_trainer import get_quantum_llm_status
except ImportError as exc:
    print(f"Error: Could not import quantum_llm_trainer: {exc}", file=sys.stderr)
    sys.exit(1)


def format_duration(seconds: float | None) -> str:
    """Format duration in seconds to human-readable format."""
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.1f}h"


def format_status(status_data: dict[str, Any]) -> str:
    """Format status data as human-readable text."""
    lines = []
    lines.append("╔════════════════════════════════════════════════════════════════╗")
    lines.append("║              QUANTUM LLM TRAINING STATUS                       ║")
    lines.append("╚════════════════════════════════════════════════════════════════╝")
    lines.append("")

    # Core status
    status = status_data.get("status", "unknown").upper()
    available = "✓" if status_data.get("available") else "✗"
    quantum_available = "✓" if status_data.get("quantum_available") else "✗"

    lines.append(f"Status:                  {available} {status}")
    lines.append(f"Available:               {available if status_data.get('available') else '✗'}")
    lines.append(f"Quantum Available:       {quantum_available}")
    lines.append("")

    # Training progress
    if status_data.get("epochs_completed") is not None:
        total_epochs = status_data.get("epochs_requested")
        completed = status_data.get("epochs_completed", 0)
        requested = total_epochs or "?"
        progress = (completed / total_epochs * 100) if total_epochs else 0
        progress_bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
        lines.append("TRAINING PROGRESS")
        lines.append(f"  Epochs:                  {completed}/{requested} [{progress_bar}] {progress:.0f}%")
        lines.append(f"  Current Loss:            {status_data.get('final_loss', '—')}")
        lines.append(f"  Best Loss:               {status_data.get('best_loss', '—')}")
        lines.append("")

    # Checkpoint information
    checkpoint_path = status_data.get("checkpoint_path") or status_data.get("best_checkpoint_path")
    if checkpoint_path:
        checkpoint_exists = status_data.get("checkpoint_exists", False)
        inference_ready = status_data.get("inference_ready", False)
        checkpoint_indicator = "✓" if checkpoint_exists else "✗"
        ready_indicator = "✓" if inference_ready else "✗"
        
        lines.append("CHECKPOINT")
        lines.append(f"  Path:                    {checkpoint_path}")
        lines.append(f"  Exists:                  {checkpoint_indicator}")
        lines.append(f"  Inference Ready:         {ready_indicator}")
        lines.append("")

    # Dataset & Mode
    if status_data.get("dataset_path"):
        lines.append("CONFIGURATION")
        lines.append(f"  Dataset:                 {status_data.get('dataset_path', '—')}")
        lines.append(f"  Mode:                    {status_data.get('mode', '—').upper()}")
        if status_data.get("passive_mode"):
            lines.append(f"  Passive Training:        ✓ (cycling)")
        lines.append("")

    # Timestamps
    started = status_data.get("started_at")
    completed = status_data.get("completed_at")
    updated = status_data.get("last_updated")
    
    if started or completed or updated:
        lines.append("TIMESTAMPS")
        if started:
            lines.append(f"  Started:                 {started}")
        if completed:
            lines.append(f"  Completed:               {completed}")
        if updated:
            lines.append(f"  Last Updated:            {updated}")
        lines.append("")

    # Error information
    if status_data.get("last_error"):
        lines.append("ERROR")
        lines.append(f"  {status_data.get('last_error')}")
        lines.append("")

    # File information
    status_file = status_data.get("status_file")
    if status_file:
        lines.append("STATUS FILE")
        lines.append(f"  Path:                    {status_file}")
        if status_data.get("status_file_exists"):
            lines.append("  Exists:                  ✓")
        else:
            lines.append("  Exists:                  ✗")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check and display Quantum LLM training status"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory path (default: data_out/quantum_llm_training)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (machine-readable)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Auto-refresh every 5 seconds (Ctrl+C to stop)"
    )
    args = parser.parse_args()

    output_dir = None
    if args.output:
        output_dir = Path(args.output)

    try:
        if args.watch:
            # Watch mode - auto-refresh every 5 seconds
            iteration = 0
            while True:
                iteration += 1
                # Clear screen (works on most terminals)
                print("\033[2J\033[H", end="", flush=True)
                
                status = get_quantum_llm_status(output_dir=output_dir)
                
                if args.json:
                    print(json.dumps(status, indent=2))
                else:
                    print(format_status(status))
                    print(f"\n[Auto-refresh #{iteration}] Press Ctrl+C to stop...")
                
                try:
                    time.sleep(5)
                except KeyboardInterrupt:
                    print("\nWatch mode stopped.")
                    return 0
        else:
            # Single check mode
            status = get_quantum_llm_status(output_dir=output_dir)
            
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print(format_status(status))
            
            return 0

    except Exception as exc:
        print(f"Error checking quantum LLM status: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
