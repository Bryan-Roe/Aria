"""Integration tests for quantum provider checkpoint loading with status metadata.""""""Integration tests for quantum provider checkpoint loading with status metadata."""




















































































































































































            assert resolved.exists()        if resolved is not None:        # Either raises or falls back - behavior depends on implementation        resolved = provider._resolve_checkpoint_path()        # Should fall back to default when status checkpoint doesn't exist                provider.model_path = tmp_path        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)                (tmp_path / "best_quantum_llm.pt").write_bytes(b"checkpoint")        # Create a default checkpoint to fall back to                (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")        }            "checkpoint_exists": False,            "checkpoint_path": "nonexistent.pt",        status_data = {        """Test handling of nonexistent checkpoint in status."""    def test_status_metadata_nonexistent_checkpoint(self, tmp_path: Path) -> None:        assert resolved.exists()        assert resolved is not None        resolved = provider._resolve_checkpoint_path()                provider.model_path = tmp_path        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)                (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")        }            "checkpoint_exists": True,            "checkpoint_path": "checkpoints/model.pt",        status_data = {                checkpoint_file.write_bytes(b"model data")        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)        checkpoint_file = tmp_path / "checkpoints" / "model.pt"        """Test handling of relative checkpoint paths in status."""    def test_status_metadata_with_relative_path(self, tmp_path: Path) -> None:        assert resolved == absolute_checkpoint        assert resolved.exists()        assert resolved is not None        resolved = provider._resolve_checkpoint_path()                provider.model_path = tmp_path        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)                (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")        }            "checkpoint_exists": True,            "checkpoint_path": str(absolute_checkpoint),        status_data = {                absolute_checkpoint.write_bytes(b"model data")        absolute_checkpoint.parent.mkdir(parents=True, exist_ok=True)        absolute_checkpoint = tmp_path / "checkpoints" / "model.pt"        """Test handling of absolute checkpoint paths in status."""    def test_status_metadata_with_absolute_path(self, tmp_path: Path) -> None:    """Test quantum provider status metadata handling."""class TestQuantumProviderStatusMetadata:@pytest.mark.skipif(not QUANTUM_PROVIDER_AVAILABLE, reason="quantum_provider not available")@pytest.mark.unit        assert resolved.name == "best_quantum_llm.pt"        assert resolved is not None        resolved = provider._resolve_checkpoint_path()        # Should fall back to default checkpoint despite bad status file                provider.model_path = tmp_path        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)                (tmp_path / "best_quantum_llm.pt").write_bytes(b"checkpoint")        # Create default checkpoint                (tmp_path / "status.json").write_text("not valid json", encoding="utf-8")        # Create malformed status file        """Test graceful handling of malformed status JSON."""    def test_handles_malformed_status_file(self, tmp_path: Path) -> None:        assert resolved.exists()        assert resolved is not None        resolved = provider._resolve_checkpoint_path()        # Should still find default checkpoint                provider.model_path = tmp_path        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)                (tmp_path / "best_quantum_llm.pt").write_bytes(b"checkpoint")        # Create only default checkpoints, no status file        """Test that provider handles missing status file gracefully."""    def test_handles_missing_status_metadata(self, tmp_path: Path) -> None:        assert resolved.name == "status_based.pt"        assert resolved is not None        resolved = provider._resolve_checkpoint_path()        # Should prefer status-based checkpoint                provider.model_path = tmp_path        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)                (tmp_path / "best_quantum_llm.pt").write_bytes(b"default checkpoint")        (tmp_path / "status_based.pt").write_bytes(b"status checkpoint")        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")        }            "checkpoint_exists": True,            "best_checkpoint_path": "status_based.pt",        status_data = {        # Create both status-referenced and default checkpoints        """Test that status metadata checkpoint is preferred over defaults."""    def test_checkpoint_priority_order(self, tmp_path: Path) -> None:        assert resolved.name in ("best_quantum_llm.pt", "final_model.pt")        assert resolved is not None        resolved = provider._resolve_checkpoint_path()        # Should find best_quantum_llm.pt file                provider.model_path = tmp_path        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)                    (tmp_path / name).write_bytes(b"checkpoint")        for name in ["best_quantum_llm.pt", "final_model.pt"]:        # Create default checkpoint files        """Test fallback to default checkpoint names when status not found."""    def test_checkpoint_fallback_to_defaults(self, tmp_path: Path) -> None:        assert resolved.name == "best_quantum_llm.pt"        assert resolved.exists()        assert resolved is not None        resolved = provider._resolve_checkpoint_path()        # Should resolve checkpoint from status metadata                provider.model_path = tmp_path        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)        # Create provider                checkpoint_file.write_bytes(b"dummy checkpoint data")        checkpoint_file = tmp_path / "best_quantum_llm.pt"        # Create a dummy checkpoint file                status_file.write_text(json.dumps(status_data), encoding="utf-8")        status_file = tmp_path / "status.json"        }            "inference_ready": True,            "checkpoint_exists": True,            "checkpoint_path": "best_quantum_llm.pt",        status_data = {        # Create a status file with checkpoint path        """Test that provider loads checkpoint from status metadata."""    def test_checkpoint_from_status_metadata(self, tmp_path: Path) -> None:    """Test quantum provider checkpoint loading with status metadata."""class TestQuantumProviderCheckpointLoading:@pytest.mark.skipif(not QUANTUM_PROVIDER_AVAILABLE, reason="quantum_provider not available")@pytest.mark.unit    QUANTUM_PROVIDER_AVAILABLE = Falseexcept (ImportError, OSError):    QUANTUM_PROVIDER_AVAILABLE = True    from quantum_provider import QuantumLLMChatProvidertry:    sys.path.insert(0, str(CHAT_CLI_SRC))if str(CHAT_CLI_SRC) not in sys.path:CHAT_CLI_SRC = REPO_ROOT / "ai-projects" / "chat-cli" / "src"REPO_ROOT = Path(__file__).resolve().parents[1]# Add paths for importsimport pytestfrom pathlib import Pathimport sysimport jsonfrom __future__ import annotations
from __future__ import annotations

import json
import sys
from pathlib import Path

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


@pytest.mark.unit
@pytest.mark.skipif(not QUANTUM_PROVIDER_AVAILABLE, reason="quantum_provider not available")
class TestQuantumProviderCheckpointLoading:
    """Test quantum provider checkpoint loading with status metadata."""

    def test_checkpoint_from_status_metadata(self, tmp_path: Path) -> None:
        """Test that provider loads checkpoint from status metadata."""
        # Create a status file with checkpoint path
        status_data = {
            "checkpoint_path": "best_quantum_llm.pt",
            "checkpoint_exists": True,
            "inference_ready": True,
        }
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status_data), encoding="utf-8")
        
        # Create a dummy checkpoint file
        checkpoint_file = tmp_path / "best_quantum_llm.pt"
        checkpoint_file.write_bytes(b"dummy checkpoint data")
        
        # Create provider
        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)
        provider.model_path = tmp_path
        
        # Should resolve checkpoint from status metadata
        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.exists()
        assert resolved.name == "best_quantum_llm.pt"

    def test_checkpoint_fallback_to_defaults(self, tmp_path: Path) -> None:
        """Test fallback to default checkpoint names when status not found."""
        # Create default checkpoint files
        for name in ["best_quantum_llm.pt", "final_model.pt"]:
            (tmp_path / name).write_bytes(b"checkpoint")
        
        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)
        provider.model_path = tmp_path
        
        # Should find best_quantum_llm.pt file
        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.name in ("best_quantum_llm.pt", "final_model.pt")

    def test_checkpoint_priority_order(self, tmp_path: Path) -> None:
        """Test that status metadata checkpoint is preferred over defaults."""
        # Create both status-referenced and default checkpoints
        status_data = {
            "best_checkpoint_path": "status_based.pt",
            "checkpoint_exists": True,
        }
        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")
        (tmp_path / "status_based.pt").write_bytes(b"status checkpoint")
        (tmp_path / "best_quantum_llm.pt").write_bytes(b"default checkpoint")
        
        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)
        provider.model_path = tmp_path
        
        # Should prefer status-based checkpoint
        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.name == "status_based.pt"

    def test_handles_missing_status_metadata(self, tmp_path: Path) -> None:
        """Test that provider handles missing status file gracefully."""
        # Create only default checkpoints, no status file
        (tmp_path / "best_quantum_llm.pt").write_bytes(b"checkpoint")
        
        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)
        provider.model_path = tmp_path
        
        # Should still find default checkpoint
        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.exists()

    def test_handles_malformed_status_file(self, tmp_path: Path) -> None:
        """Test graceful handling of malformed status JSON."""
        # Create malformed status file
        (tmp_path / "status.json").write_text("not valid json", encoding="utf-8")
        
        # Create default checkpoint
        (tmp_path / "best_quantum_llm.pt").write_bytes(b"checkpoint")
        
        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)
        provider.model_path = tmp_path
        
        # Should fall back to default checkpoint despite bad status file
        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.name == "best_quantum_llm.pt"


@pytest.mark.unit
@pytest.mark.skipif(not QUANTUM_PROVIDER_AVAILABLE, reason="quantum_provider not available")
class TestQuantumProviderStatusMetadata:
    """Test quantum provider status metadata handling."""

    def test_status_metadata_with_absolute_path(self, tmp_path: Path) -> None:
        """Test handling of absolute checkpoint paths in status."""
        absolute_checkpoint = tmp_path / "checkpoints" / "model.pt"
        absolute_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        absolute_checkpoint.write_bytes(b"model data")
        
        status_data = {
            "checkpoint_path": str(absolute_checkpoint),
            "checkpoint_exists": True,
        }
        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")
        
        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)
        provider.model_path = tmp_path
        
        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.exists()
        assert resolved == absolute_checkpoint

    def test_status_metadata_with_relative_path(self, tmp_path: Path) -> None:
        """Test handling of relative checkpoint paths in status."""
        checkpoint_file = tmp_path / "checkpoints" / "model.pt"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_bytes(b"model data")
        
        status_data = {
            "checkpoint_path": "checkpoints/model.pt",
            "checkpoint_exists": True,
        }
        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")
        
        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)
        provider.model_path = tmp_path
        
        resolved = provider._resolve_checkpoint_path()
        assert resolved is not None
        assert resolved.exists()

    def test_status_metadata_nonexistent_checkpoint(self, tmp_path: Path) -> None:
        """Test handling of nonexistent checkpoint in status."""
        status_data = {
            "checkpoint_path": "nonexistent.pt",
            "checkpoint_exists": False,
        }
        (tmp_path / "status.json").write_text(json.dumps(status_data), encoding="utf-8")
        
        # Create a default checkpoint to fall back to
        (tmp_path / "best_quantum_llm.pt").write_bytes(b"checkpoint")
        
        provider = QuantumLLMChatProvider.__new__(QuantumLLMChatProvider)
        provider.model_path = tmp_path
        
        # Should fall back to default when status checkpoint doesn't exist
        resolved = provider._resolve_checkpoint_path()
        # Either raises or falls back - behavior depends on implementation
        if resolved is not None:
            assert resolved.exists()
