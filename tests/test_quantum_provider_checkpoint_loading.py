"""Integration tests for quantum provider checkpoint loading with status metadata."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest


# Add paths for imports
REPO_ROOT = Path(__file__).resolve().parents[1]
CHAT_CLI_SRC = REPO_ROOT / "ai-projects" / "chat-cli" / "src"
if str(CHAT_CLI_SRC) not in sys.path:
    sys.path.insert(0, str(CHAT_CLI_SRC))

try:
    from quantum_provider import QuantumLLMChatProvider

    QUANTUM_PROVIDER_AVAILABLE = True
except (ImportError, OSError):
    QUANTUM_PROVIDER_AVAILABLE = False
    QuantumLLMChatProvider = None  # type: ignore[assignment]


def _new_provider(model_path: Path) -> Any:
    """Create provider instance with guard for type checkers and optional import paths."""
    assert QuantumLLMChatProvider is not None
    provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)
    provider.model_path = model_path
    return provider


@pytest.mark.unit
@pytest.mark.skipif(not QUANTUM_PROVIDER_AVAILABLE, reason="quantum_provider not available")
class TestQuantumProviderCheckpointLoading:
    """Test quantum provider checkpoint loading with status metadata."""

    def test_checkpoint_from_status_metadata(self, tmp_path: Path) -> None:
        """Provider should resolve checkpoint from status metadata."""
        status_data = {
            "checkpoint_path": "best_quantum_llm.pt",
            "checkpoint_exists": True,
            "inference_ready": True,
        }
        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")
        (tmp_path / "best_quantum_llm.pt").write_bytes(b"dummy checkpoint data")

        provider = _new_provider(tmp_path)

        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.exists()
        assert resolved.name == "best_quantum_llm.pt"

    def test_checkpoint_fallback_to_defaults(self, tmp_path: Path) -> None:
        """Provider should fall back to default checkpoint filenames."""
        for name in ["best_quantum_llm.pt", "final_model.pt"]:
            (tmp_path / name).write_bytes(b"checkpoint")

        provider = _new_provider(tmp_path)

        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.name in ("best_quantum_llm.pt", "final_model.pt")

    def test_checkpoint_priority_order(self, tmp_path: Path) -> None:
        """Status-based best checkpoint should take precedence over defaults."""
        status_data = {
            "best_checkpoint_path": "status_based.pt",
            "checkpoint_exists": True,
        }
        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")
        (tmp_path / "status_based.pt").write_bytes(b"status checkpoint")
        (tmp_path / "best_quantum_llm.pt").write_bytes(b"default checkpoint")

        provider = _new_provider(tmp_path)

        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.name == "status_based.pt"

    def test_handles_missing_status_metadata(self, tmp_path: Path) -> None:
        """Missing status file should not break default checkpoint discovery."""
        (tmp_path / "best_quantum_llm.pt").write_bytes(b"checkpoint")

        provider = _new_provider(tmp_path)

        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.exists()

    def test_handles_malformed_status_file(self, tmp_path: Path) -> None:
        """Malformed status JSON should gracefully fall back to default files."""
        (tmp_path / "status.json").write_text("not valid json", encoding="utf-8")
        (tmp_path / "best_quantum_llm.pt").write_bytes(b"checkpoint")

        provider = _new_provider(tmp_path)

        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.name == "best_quantum_llm.pt"


@pytest.mark.unit
@pytest.mark.skipif(not QUANTUM_PROVIDER_AVAILABLE, reason="quantum_provider not available")
class TestQuantumProviderStatusMetadata:
    """Test quantum provider status metadata path handling."""

    def test_status_metadata_with_absolute_path(self, tmp_path: Path) -> None:
        """Absolute checkpoint paths in status should resolve correctly."""
        absolute_checkpoint = tmp_path / "checkpoints" / "model.pt"
        absolute_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        absolute_checkpoint.write_bytes(b"model data")

        status_data = {
            "checkpoint_path": str(absolute_checkpoint),
            "checkpoint_exists": True,
        }
        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")

        provider = _new_provider(tmp_path)

        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.exists()
        assert resolved == absolute_checkpoint

    def test_status_metadata_with_relative_path(self, tmp_path: Path) -> None:
        """Relative checkpoint paths in status should resolve under model_path."""
        checkpoint_file = tmp_path / "checkpoints" / "model.pt"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_bytes(b"model data")

        status_data = {
            "checkpoint_path": "checkpoints/model.pt",
            "checkpoint_exists": True,
        }
        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")

        provider = _new_provider(tmp_path)

        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.exists()

    def test_status_metadata_nonexistent_checkpoint(self, tmp_path: Path) -> None:
        """Nonexistent status checkpoint should fall back to defaults when present."""
        status_data = {
            "checkpoint_path": "nonexistent.pt",
            "checkpoint_exists": False,
        }
        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")
        (tmp_path / "best_quantum_llm.pt").write_bytes(b"checkpoint")

        provider = _new_provider(tmp_path)

        resolved = provider._resolve_checkpoint_path()
        if resolved is not None:
            assert resolved.exists()
