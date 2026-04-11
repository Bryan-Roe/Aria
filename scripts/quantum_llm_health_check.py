#!/usr/bin/env python3
"""Quantum LLM system health check and validation.

Validates that all quantum LLM components are properly configured,
checkpoints are valid, and the system is ready for inference.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def check_status_file(output_dir: Path) -> tuple[bool, str]:
    """Check if status file exists and is valid."""
    status_file = output_dir / "status.json"

    if not status_file.exists():
        return False, f"❌ Status file not found at {status_file}"

    try:
        status = json.loads(status_file.read_text(encoding="utf-8"))
        return True, "✓ Status file found and valid"
    except json.JSONDecodeError as e:
        return False, f"❌ Status file is malformed: {e}"


def check_checkpoint(output_dir: Path, status: dict[str, Any]) -> tuple[bool, str]:
    """Check if checkpoint file exists and is accessible."""
    checkpoint_path = status.get("checkpoint_path")

    if not checkpoint_path:
        return False, "❌ No checkpoint path in status"

    # Resolve relative paths
    if not Path(checkpoint_path).is_absolute():
        checkpoint_file = output_dir / checkpoint_path
    else:
        checkpoint_file = Path(checkpoint_path)

    if not checkpoint_file.exists():
        return False, f"❌ Checkpoint file not found at {checkpoint_file}"

    file_size = checkpoint_file.stat().st_size
    if file_size < 1024:  # Less than 1KB
        return False, f"❌ Checkpoint file seems too small ({file_size} bytes)"

    return True, f"✓ Checkpoint file found ({file_size / 1024 / 1024:.2f} MB)"


def check_training_state(status: dict[str, Any]) -> tuple[bool, str]:
    """Check training status and epochs."""
    training_status = status.get("status", "unknown")

    valid_states = {"completed", "running", "idle", "not_started", "failed"}
    if training_status not in valid_states:
        return False, f"❌ Invalid training status: {training_status}"

    epochs_completed = status.get("epochs_completed", 0)
    if epochs_completed < 0:
        return False, f"❌ Invalid epochs_completed: {epochs_completed}"

    return True, f"✓ Training status: {training_status} ({epochs_completed} epochs)"


def check_loss_metrics(status: dict[str, Any]) -> tuple[bool, str]:
    """Validate loss metrics."""
    best_loss = status.get("best_loss")
    final_loss = status.get("final_loss")

    if best_loss is None:
        return True, "⚠ No best_loss metric yet"

    if not isinstance(best_loss, (int, float)) or best_loss < 0:
        return False, f"❌ Invalid best_loss: {best_loss}"

    if final_loss is not None:
        if not isinstance(final_loss, (int, float)) or final_loss < 0:
            return False, f"❌ Invalid final_loss: {final_loss}"

        if best_loss > final_loss * 10:  # Best loss is way worse than final
            return (
                True,
                f"⚠ Unexpected loss relationship (best={best_loss}, final={final_loss})",
            )

    return True, f"✓ Loss metrics valid (best={best_loss:.6f})"


def check_inference_readiness(status: dict[str, Any]) -> tuple[bool, str]:
    """Check if system is ready for inference."""
    inference_ready = status.get("inference_ready", False)
    checkpoint_exists = status.get("checkpoint_exists", False)
    training_status = status.get("status", "")

    if inference_ready:
        return True, "✓ System ready for inference"

    reasons = []
    if not checkpoint_exists:
        reasons.append("checkpoint doesn't exist")
    if training_status == "running":
        reasons.append("training still in progress")
    if training_status == "failed":
        reasons.append("training failed")

    return False, f"❌ Not ready for inference ({', '.join(reasons)})"


def check_timestamps(status: dict[str, Any]) -> tuple[bool, str]:
    """Validate timestamp fields."""
    timestamps = {}
    for field in ["started_at", "completed_at", "last_updated"]:
        if field in status:
            timestamps[field] = status[field]

    if not timestamps:
        return True, "⚠ No timestamp information"

    # Basic validation - timestamps should be ISO format strings
    for field, value in timestamps.items():
        if not isinstance(value, str):
            return False, f"❌ Invalid timestamp format in {field}: {value}"

    return True, f"✓ Timestamps valid ({len(timestamps)} fields)"


def check_error_state(status: dict[str, Any]) -> tuple[bool, str]:
    """Check for error conditions."""
    last_error = status.get("last_error")

    if not last_error:
        return True, "✓ No errors recorded"

    if isinstance(last_error, str) and len(last_error) > 0:
        return False, f"❌ Error recorded: {last_error}"

    return True, "✓ No errors recorded"


def run_health_check(output_dir: Path | None = None) -> int:
    """Run comprehensive health check."""
    if output_dir is None:
        output_dir = Path("data_out/quantum_llm_training")

    output_dir = Path(output_dir)
    status_file = output_dir / "status.json"

    print("=" * 70)
    print("🔬 Quantum LLM System Health Check")
    print("=" * 70)
    print(f"\n📂 Checking directory: {output_dir}")

    # Check 1: Status file
    print("\n1️⃣  Status File:")
    status_ok, msg = check_status_file(output_dir)
    print(f"   {msg}")

    if not status_ok:
        print("\n❌ System health check failed (status file issue)")
        return 1

    # Load status for remaining checks
    try:
        status = json.loads(status_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"\n❌ Failed to load status: {e}")
        return 1

    # Check 2: Checkpoint
    print("\n2️⃣  Checkpoint File:")
    checkpoint_ok, msg = check_checkpoint(output_dir, status)
    print(f"   {msg}")

    # Check 3: Training state
    print("\n3️⃣  Training State:")
    state_ok, msg = check_training_state(status)
    print(f"   {msg}")

    # Check 4: Loss metrics
    print("\n4️⃣  Loss Metrics:")
    loss_ok, msg = check_loss_metrics(status)
    print(f"   {msg}")

    # Check 5: Inference readiness
    print("\n5️⃣  Inference Readiness:")
    inference_ok, msg = check_inference_readiness(status)
    print(f"   {msg}")

    # Check 6: Timestamps
    print("\n6️⃣  Timestamps:")
    time_ok, msg = check_timestamps(status)
    print(f"   {msg}")

    # Check 7: Error state
    print("\n7️⃣  Error State:")
    error_ok, msg = check_error_state(status)
    print(f"   {msg}")

    # Summary
    print("\n" + "=" * 70)
    all_ok = status_ok and state_ok and loss_ok and time_ok and error_ok

    if all_ok and inference_ok:
        print("✅ System Health: EXCELLENT - All checks passed")
        exit_code = 0
    elif all_ok and checkpoint_ok:
        print(
            "⚠️  System Health: GOOD - Ready for training, checkpoint validation pending"
        )
        exit_code = 0
    elif all_ok:
        print("⚠️  System Health: FAIR - Core system intact, some issues detected")
        exit_code = 1
    else:
        print("❌ System Health: CRITICAL - Multiple issues detected")
        exit_code = 1

    print("=" * 70)
    return exit_code


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check quantum LLM system health")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Training output directory (default: data_out/quantum_llm_training)",
    )

    args = parser.parse_args()
    sys.exit(run_health_check(args.output))
