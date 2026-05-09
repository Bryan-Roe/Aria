"""Tests for quantum LLM health check functionality."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
HEALTH_CHECK_SCRIPT = SCRIPTS_DIR / "quantum_llm_health_check.py"


@pytest.mark.unit
class TestQuantumLLMHealthCheck:
    """Test quantum LLM health check script."""

    def test_health_check_script_exists(self) -> None:
        """Test that health check script exists."""
        assert (
            HEALTH_CHECK_SCRIPT.exists()
        ), f"Health check script not found at {HEALTH_CHECK_SCRIPT}"

    def test_health_check_with_no_status_file(self, tmp_path: Path) -> None:
        """Test health check behavior when status file is missing."""
        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, "Should exit with error when status file missing"
        assert (
            "Status file not found" in result.stdout
            or "Status file not found" in result.stderr
        )

    def test_health_check_with_valid_status(self, tmp_path: Path) -> None:
        """Test health check with valid status file."""
        status_data = {
            "status": "completed",
            "checkpoint_exists": True,
            "checkpoint_path": "best_model.pt",
            "inference_ready": True,
            "epochs_completed": 5,
            "best_loss": 0.089,
            "final_loss": 0.123,
            "started_at": "2026-03-22T09:00:00",
            "completed_at": "2026-03-22T09:15:00",
            "last_updated": "2026-03-22T09:15:00",
        }

        # Create status file
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        # Create checkpoint file
        (tmp_path / "best_model.pt").write_bytes(b"x" * 10000)

        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        # Should succeed since checkpoint exists and is ready
        assert "Health Check" in result.stdout

    def test_health_check_detects_missing_checkpoint(self, tmp_path: Path) -> None:
        """Test that health check detects missing checkpoint."""
        status_data = {
            "status": "completed",
            "checkpoint_exists": True,
            "checkpoint_path": "missing_model.pt",
            "inference_ready": True,
        }

        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        # Note: Don't create the checkpoint file

        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert "Checkpoint file not found" in result.stdout

    def test_health_check_detects_invalid_status(self, tmp_path: Path) -> None:
        """Test that health check detects invalid training status."""
        status_data = {
            "status": "unknown_status",
            "checkpoint_exists": True,
            "checkpoint_path": "model.pt",
        }

        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert "Invalid training status" in result.stdout

    def test_health_check_detects_invalid_loss(self, tmp_path: Path) -> None:
        """Test that health check detects invalid loss metrics."""
        status_data = {
            "status": "completed",
            "checkpoint_exists": True,
            "checkpoint_path": "model.pt",
            "best_loss": -5.0,  # Invalid: negative loss
        }

        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert "Invalid best_loss" in result.stdout

    def test_health_check_with_error_condition(self, tmp_path: Path) -> None:
        """Test that health check detects error conditions."""
        status_data = {
            "status": "failed",
            "checkpoint_exists": False,
            "last_error": "GPU out of memory",
        }

        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert "Error recorded" in result.stdout

    def test_health_check_malformed_json(self, tmp_path: Path) -> None:
        """Test health check with malformed JSON file."""
        status_file = tmp_path / "status.json"
        status_file.write_text("not valid json", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0

    def test_health_check_running_training(self, tmp_path: Path) -> None:
        """Test health check during active training."""
        status_data = {
            "status": "running",
            "checkpoint_exists": False,
            "checkpoint_path": None,
            "inference_ready": False,
            "epochs_completed": 2,
        }

        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        # Training in progress is expected output
        assert "running" in result.stdout

    def test_health_check_missing_checkpoint_path_field(self, tmp_path: Path) -> None:
        """Test health check when checkpoint_path field is missing."""
        status_data = {
            "status": "completed",
            "checkpoint_exists": True,
            # checkpoint_path is missing
        }

        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert "No checkpoint path" in result.stdout

    def test_health_check_small_checkpoint_warning(self, tmp_path: Path) -> None:
        """Test that health check warns about suspiciously small checkpoints."""
        status_data = {
            "status": "completed",
            "checkpoint_exists": True,
            "checkpoint_path": "tiny_model.pt",
            "inference_ready": True,
        }

        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        # Create a tiny checkpoint (less than 1KB)
        (tmp_path / "tiny_model.pt").write_bytes(b"x" * 100)

        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--output", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert "seems too small" in result.stdout
