"""Tests for ai-projects/quantum-ml/quantum_llm_quickstart.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "ai-projects" / "quantum-ml" / "quantum_llm_quickstart.py"


def _load_quickstart_module():
    spec = importlib.util.spec_from_file_location("quantum_llm_quickstart", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_quickstart(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run quantum_llm_quickstart.py with provided args."""
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        timeout=20,
    )


@pytest.mark.unit
def test_quickstart_script_exists() -> None:
    """Quickstart script should exist in expected location."""
    assert SCRIPT_PATH.exists(), f"Expected script at {SCRIPT_PATH}"


@pytest.mark.unit
def test_quickstart_help_is_available() -> None:
    """--help should work without requiring heavy runtime dependencies."""
    result = _run_quickstart(["--help"])
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "Quantum LLM Quick Start" in combined or "quick" in combined.lower()


@pytest.mark.unit
def test_monitor_mode_runs_without_training_deps(tmp_path: Path) -> None:
    """Monitor mode should run even when training dependencies are unavailable."""
    result = _run_quickstart(["--mode", "monitor", "--output-dir", str(tmp_path)])
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "TRAINING MONITOR" in combined


@pytest.mark.unit
def test_resolve_generate_model_path_prefers_explicit_existing(tmp_path: Path) -> None:
    mod = _load_quickstart_module()
    model_path = tmp_path / "my_model.pt"
    model_path.write_bytes(b"checkpoint")

    resolved = mod._resolve_generate_model_path(str(model_path), None)

    assert resolved == model_path


@pytest.mark.unit
def test_resolve_generate_model_path_autodetects_output_dir(tmp_path: Path) -> None:
    mod = _load_quickstart_module()
    ckpt = tmp_path / "final_model.pt"
    ckpt.write_bytes(b"checkpoint")

    resolved = mod._resolve_generate_model_path(None, str(tmp_path))

    assert resolved == ckpt


@pytest.mark.unit
def test_resolve_generate_model_path_none_when_missing(tmp_path: Path) -> None:
    mod = _load_quickstart_module()

    resolved = mod._resolve_generate_model_path(None, str(tmp_path))

    assert resolved is None
