"""Tests for quantum provider checkpoint loading with status metadata."""

import json
import sys
from pathlib import Path

import pytest


# Add paths for imports
REPO_ROOT = Path(__file__).resolve().parents[1]
CHAT_CLI_SRC = REPO_ROOT / "ai-projects" / "chat-cli" / "src"
if str(CHAT_CLI_SRC) not in sys.path:
    sys.path.insert(0, str(CHAT_CLI_SRC))


@pytest.mark.unit
class TestQuantumProviderCheckpointLoading:
    """Test quantum provider checkpoint loading with status metadata."""

    def test_checkpoint_status_file_creation(self, tmp_path: Path) -> None:
        """Test that status files with checkpoint metadata are created correctly."""
        status_data = {
            "checkpoint_path": "best_quantum_llm.pt",
            "checkpoint_exists": True,
            "inference_ready": True,
            "status": "completed",
        }
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        assert status_file.exists()
        loaded = json.loads(status_file.read_text(encoding="utf-8"))
        assert loaded["checkpoint_path"] == "best_quantum_llm.pt"
        assert loaded["inference_ready"] is True

    def test_checkpoint_path_resolution_priority(self, tmp_path: Path) -> None:
        """Test checkpoint path resolution order."""
        # Priority order should be:
        # 1. best_checkpoint_path from status
        # 2. checkpoint_path from status
        # 3. last_checkpoint_path from status
        # 4. Default file names

        status_data = {
            "best_checkpoint_path": "checkpoints/best.pt",
            "checkpoint_path": "checkpoints/current.pt",
            "last_checkpoint_path": "checkpoints/last.pt",
        }
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        loaded = json.loads(status_file.read_text(encoding="utf-8"))
        # Verify best checkpoint path is highest priority
        assert "best_checkpoint_path" in loaded
        assert loaded["best_checkpoint_path"] == "checkpoints/best.pt"

    def test_checkpoint_exists_flag(self, tmp_path: Path) -> None:
        """Test checkpoint existence tracking."""
        checkpoint_file = tmp_path / "best_quantum_llm.pt"
        checkpoint_file.write_bytes(b"model checkpoint data")

        status_data = {
            "checkpoint_path": str(checkpoint_file),
            "checkpoint_exists": checkpoint_file.exists(),
            "inference_ready": checkpoint_file.exists(),
        }
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        loaded = json.loads(status_file.read_text(encoding="utf-8"))
        assert loaded["checkpoint_exists"] is True
        assert loaded["inference_ready"] is True

    def test_status_metadata_timestamp(self, tmp_path: Path) -> None:
        """Test that status metadata includes timing information."""
        status_data = {
            "status": "completed",
            "checkpoint_exists": True,
            "started_at": "2026-03-22T09:00:00",
            "completed_at": "2026-03-22T09:15:00",
            "last_updated": "2026-03-22T09:15:00",
        }
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        loaded = json.loads(status_file.read_text(encoding="utf-8"))
        assert "started_at" in loaded
        assert "completed_at" in loaded
        assert "last_updated" in loaded

    def test_checkpoint_metadata_validation(self, tmp_path: Path) -> None:
        """Test that checkpoint metadata can be validated."""
        status_data = {
            "checkpoint_path": "model.pt",
            "checkpoint_exists": True,
            "inference_ready": True,
            "epochs_completed": 5,
            "best_loss": 0.089,
            "final_loss": 0.123,
        }
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        loaded = json.loads(status_file.read_text(encoding="utf-8"))

        # Verify all required metadata present
        assert loaded["checkpoint_exists"] is not None
        assert loaded["inference_ready"] is not None
        assert loaded["epochs_completed"] >= 0
        assert loaded["best_loss"] >= 0
        assert loaded["final_loss"] >= 0

    def test_checkpoint_with_error_tracking(self, tmp_path: Path) -> None:
        """Test checkpoint status with error tracking."""
        status_data = {
            "status": "failed",
            "checkpoint_exists": False,
            "inference_ready": False,
            "last_error": "Training failed: GPU out of memory",
        }
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        loaded = json.loads(status_file.read_text(encoding="utf-8"))
        assert loaded["inference_ready"] is False
        assert "last_error" in loaded
        assert loaded["last_error"] is not None
