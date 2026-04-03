"""Tests for quantum_llm_status_check.py script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "quantum_llm_status_check.py"


def _run_status_check(args: list[str] | None = None) -> tuple[int, str]:
    """Run the status check script and return (exit_code, output)."""
    cmd = [sys.executable, str(SCRIPT_PATH)]
    if args:
        cmd.extend(args)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    return result.returncode, result.stdout + result.stderr


@pytest.mark.unit
def test_script_exists() -> None:
    """Test that the status check script exists."""
    assert SCRIPT_PATH.exists(), f"Expected script at {SCRIPT_PATH}"


@pytest.mark.unit
def test_script_help() -> None:
    """Test that the script shows help."""
    exit_code, output = _run_status_check(["--help"])
    assert exit_code == 0
    assert "Quantum LLM" in output or "quantum" in output.lower()


@pytest.mark.unit
def test_script_default_output() -> None:
    """Test default status check output."""
    exit_code, output = _run_status_check()
    # Should succeed even if no status file exists
    assert exit_code == 0
    # Should show status information
    assert "Status" in output or "QUANTUM" in output


@pytest.mark.unit
def test_script_json_output() -> None:
    """Test JSON output format."""
    exit_code, output = _run_status_check(["--json"])
    assert exit_code == 0

    # Should be valid JSON
    try:
        data = json.loads(output)
        assert isinstance(data, dict)
        # Should have expected keys
        assert "status" in data
        assert "available" in data
    except json.JSONDecodeError:
        pytest.fail("Output is not valid JSON")


@pytest.mark.unit
def test_script_with_output_dir(tmp_path: Path) -> None:
    """Test status check with custom output directory."""
    exit_code, output = _run_status_check(["--output", str(tmp_path)])
    assert exit_code == 0
    # Should work even with empty directory
    assert "Status" in output or "status" in output.lower()


@pytest.mark.unit
def test_script_json_output_with_custom_dir(tmp_path: Path) -> None:
    """Test JSON output with custom directory."""
    exit_code, output = _run_status_check(["--output", str(tmp_path), "--json"])
    assert exit_code == 0

    try:
        data = json.loads(output)
        assert isinstance(data, dict)
        assert "status" in data
        # Since directory is empty, should indicate no training
        assert data["status_file_exists"] is False
    except json.JSONDecodeError:
        pytest.fail("Output is not valid JSON")


@pytest.mark.unit
def test_script_with_status_file(tmp_path: Path) -> None:
    """Test status check with actual status file."""
    # Create a minimal status file
    status_file = tmp_path / "status.json"
    test_status = {
        "status": "completed",
        "available": True,
        "epochs_completed": 5,
        "epochs_requested": 10,
        "final_loss": 0.123,
        "best_loss": 0.089,
        "checkpoint_path": "data_out/quantum_llm_training/best_quantum_llm.pt",
        "checkpoint_exists": True,
        "inference_ready": True,
    }
    status_file.write_text(json.dumps(test_status, indent=2), encoding="utf-8")

    exit_code, output = _run_status_check(["--output", str(tmp_path)])
    assert exit_code == 0
    # Should display training progress
    assert "completed" in output.lower() or "COMPLETED" in output


@pytest.mark.unit
def test_script_json_with_status_file(tmp_path: Path) -> None:
    """Test JSON output with actual status file."""
    # Create a status file
    status_file = tmp_path / "status.json"
    test_status = {
        "status": "running",
        "available": True,
        "epochs_completed": 3,
        "epochs_requested": 10,
        "final_loss": 0.234,
        "best_loss": 0.200,
    }
    status_file.write_text(json.dumps(test_status, indent=2), encoding="utf-8")

    exit_code, output = _run_status_check(["--output", str(tmp_path), "--json"])
    assert exit_code == 0

    data = json.loads(output)
    # Should reflect the status file data
    assert data["status"] == "running"
    assert data["epochs_completed"] == 3
