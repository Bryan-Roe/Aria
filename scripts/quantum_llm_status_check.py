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
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data_out" / "quantum_llm_training"
CHECKPOINT_FILENAMES = (
    "best_quantum_llm.pt",
    "quantum_llm_checkpoint.pt",
    "final_model.pt",
)


def _resolve_output_dir(output_dir: Path | None) -> Path:
    if output_dir is None:
        return DEFAULT_OUTPUT_DIR
    if output_dir.is_absolute():
        return output_dir
    return (REPO_ROOT / output_dir).resolve()


def _repo_relative_str(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def get_quantum_llm_status_fast(*, output_dir: Path | None = None) -> dict[str, Any]:
    """Fast status loader that avoids importing heavy training dependencies."""
    resolved_output_dir = _resolve_output_dir(output_dir)
    resolved_status_file = resolved_output_dir / "status.json"

    payload: dict[str, Any] = {
        "available": False,
        "status": "not_started",
        "output_dir": _repo_relative_str(resolved_output_dir),
        "status_file": _repo_relative_str(resolved_status_file),
        "status_file_exists": resolved_status_file.exists(),
        "checkpoint_path": None,
        "best_checkpoint_path": None,
        "checkpoint_exists": False,
        "inference_ready": False,
        "quantum_available": False,
        "epochs_completed": 0,
        "epochs_requested": None,
        "best_loss": None,
        "final_loss": None,
        "last_updated": None,
        "last_error": None,
        "passive_mode": False,
        "mode": None,
    }

    if resolved_status_file.exists():
        try:
            existing = json.loads(resolved_status_file.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                payload.update(existing)
                payload["available"] = True
        except Exception as exc:  # noqa: BLE001
            payload.update(
                {
                    "status": "error",
                    "available": False,
                    "last_error": f"Failed to read status file: {exc}",
                }
            )

    checkpoint_ref = (
        payload.get("best_checkpoint_path")
        or payload.get("checkpoint_path")
        or payload.get("last_checkpoint_path")
    )

    checkpoint_path: Path | None = None
    if checkpoint_ref:
        candidate = Path(str(checkpoint_ref))
        checkpoint_path = (
            candidate
            if candidate.is_absolute()
            else (resolved_output_dir / candidate).resolve()
        )
    else:
        for filename in CHECKPOINT_FILENAMES:
            candidate = resolved_output_dir / filename
            if candidate.exists():
                checkpoint_path = candidate
                break

    if checkpoint_path is not None:
        payload["checkpoint_path"] = _repo_relative_str(checkpoint_path)
        payload["checkpoint_exists"] = checkpoint_path.exists()
        payload["inference_ready"] = bool(
            checkpoint_path.exists()
            and payload.get("status") in {"completed", "running", "idle"}
        )

    return payload


def format_status(status_data: dict[str, Any]) -> str:
    """Format status data as human-readable text."""
    lines: list[str] = []
    lines.append("╔════════════════════════════════════════════════════════════════╗")
    lines.append("║              QUANTUM LLM TRAINING STATUS                       ║")
    lines.append("╚════════════════════════════════════════════════════════════════╝")
    lines.append("")

    status = str(status_data.get("status", "unknown")).upper()
    available = "✓" if status_data.get("available") else "✗"
    quantum_available = "✓" if status_data.get("quantum_available") else "✗"

    lines.append(f"Status:                  {available} {status}")
    lines.append(
        f"Available:               {'✓' if status_data.get('available') else '✗'}"
    )
    lines.append(f"Quantum Available:       {quantum_available}")
    lines.append("")

    if status_data.get("epochs_completed") is not None:
        total_epochs = status_data.get("epochs_requested")
        completed = status_data.get("epochs_completed", 0)
        requested = total_epochs or "?"
        progress = (completed / total_epochs * 100) if total_epochs else 0
        progress_bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
        lines.append("TRAINING PROGRESS")
        lines.append(
            f"  Epochs:                  {completed}/{requested} [{progress_bar}] {progress:.0f}%"
        )
        lines.append(f"  Current Loss:            {status_data.get('final_loss', '—')}")
        lines.append(f"  Best Loss:               {status_data.get('best_loss', '—')}")
        lines.append("")

    checkpoint_path = status_data.get("checkpoint_path") or status_data.get(
        "best_checkpoint_path"
    )
    if checkpoint_path:
        checkpoint_exists = status_data.get("checkpoint_exists", False)
        inference_ready = status_data.get("inference_ready", False)
        lines.append("CHECKPOINT")
        lines.append(f"  Path:                    {checkpoint_path}")
        lines.append(f"  Exists:                  {'✓' if checkpoint_exists else '✗'}")
        lines.append(f"  Inference Ready:         {'✓' if inference_ready else '✗'}")
        lines.append("")

    if status_data.get("status_file"):
        lines.append("STATUS FILE")
        lines.append(f"  Path:                    {status_data.get('status_file')}")
        lines.append(
            f"  Exists:                  {'✓' if status_data.get('status_file_exists') else '✗'}"
        )
        lines.append("")

    if status_data.get("last_error"):
        lines.append("ERROR")
        lines.append(f"  {status_data.get('last_error')}")
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
        help="Output directory path (default: data_out/quantum_llm_training)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON (machine-readable)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Auto-refresh every 5 seconds (Ctrl+C to stop)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None

    try:
        if args.watch:
            iteration = 0
            while True:
                iteration += 1
                print("\033[2J\033[H", end="", flush=True)
                status = get_quantum_llm_status_fast(output_dir=output_dir)
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

        status = get_quantum_llm_status_fast(output_dir=output_dir)
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(format_status(status))
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"Error checking quantum LLM status: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
