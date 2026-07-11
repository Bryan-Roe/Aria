"""Regression tests for scripts/training_analytics.py CLI behavior."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.mark.unit
def test_training_analytics_report_exits_zero() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "training_analytics.py"

    assert script.exists(), "Expected training_analytics.py to exist"

    proc = subprocess.run(
        [sys.executable, str(script), "--report"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0
    assert "AUTONOMOUS TRAINING ANALYTICS REPORT" in proc.stdout


@pytest.mark.unit
def test_training_analytics_report_pipe_head_exits_zero() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    # Regression guard: piping to head should not fail with BrokenPipeError.
    proc = subprocess.run(
        [
            "bash",
            "-lc",
            "python3 scripts/training_analytics.py --report | head -20 >/dev/null",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, f"expected zero exit when piped to head, got {proc.returncode}; stderr={proc.stderr!r}"


@pytest.mark.unit
def test_training_analytics_report_pipe_head_with_pipefail_exits_zero() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    # Regression guard: pipefail + python executable should still exit cleanly.
    proc = subprocess.run(
        [
            "bash",
            "-lc",
            "set -o pipefail; python scripts/training_analytics.py --report | head -20 >/dev/null",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert (
        proc.returncode == 0
    ), f"expected zero exit with pipefail enabled, got {proc.returncode}; stderr={proc.stderr!r}"


@pytest.mark.unit
def test_training_analytics_missing_status_file_exits_zero() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "training_analytics.py"

    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--status-file",
            "data_out/does_not_exist_status.json",
            "--report",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0
    assert "AUTONOMOUS TRAINING ANALYTICS REPORT" in proc.stdout
    assert "Total Cycles: 0" in proc.stdout


@pytest.mark.unit
def test_training_analytics_malformed_status_file_exits_zero() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "training_analytics.py"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp.write("{ malformed json")
        tmp_path = tmp.name

    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                "--status-file",
                tmp_path,
                "--report",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert proc.returncode == 0
        assert "AUTONOMOUS TRAINING ANALYTICS REPORT" in proc.stdout
        assert "Total Cycles: 0" in proc.stdout
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_training_analytics_nondict_status_file_exits_zero() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "training_analytics.py"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp.write("[1, 2, 3]")
        tmp_path = tmp.name

    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                "--status-file",
                tmp_path,
                "--report",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert proc.returncode == 0
        assert "AUTONOMOUS TRAINING ANALYTICS REPORT" in proc.stdout
        assert "Total Cycles: 0" in proc.stdout
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_training_analytics_chart_pipe_head_with_pipefail_exits_zero() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    proc = subprocess.run(
        [
            "bash",
            "-lc",
            "set -o pipefail; python scripts/training_analytics.py --chart | head -20 >/dev/null",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert (
        proc.returncode == 0
    ), f"expected zero exit for chart mode under pipefail, got {proc.returncode}; stderr={proc.stderr!r}"


@pytest.mark.unit
def test_training_analytics_default_mode_pipe_head_with_pipefail_exits_zero() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    proc = subprocess.run(
        [
            "bash",
            "-lc",
            "set -o pipefail; python scripts/training_analytics.py | head -20 >/dev/null",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert (
        proc.returncode == 0
    ), f"expected zero exit for default mode under pipefail, got {proc.returncode}; stderr={proc.stderr!r}"
