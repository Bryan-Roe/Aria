"""Integration tests for Quantum AutoRun orchestrator."""
import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
Q_SCRIPT = REPO_ROOT / "scripts" / "quantum_autorun.py"


@pytest.fixture
def sample_qconfig(tmp_path):
    cfg = tmp_path / "quantum_autorun.yaml"
    cfg.write_text(
        """
jobs:
  - name: heart_quick
    preset: heart
    epochs: 1
    n_qubits: 4
""",
        encoding="utf-8",
    )
    return cfg


class TestCLI:
    def test_help(self):
        import sys
        proc = subprocess.run([sys.executable, str(
            Q_SCRIPT), "--help"], capture_output=True, text=True)
        assert proc.returncode == 0
        assert "Quantum AutoRun" in proc.stdout or "usage" in proc.stdout.lower()

    def test_list(self, sample_qconfig):
        import sys
        proc = subprocess.run(
            [sys.executable, str(Q_SCRIPT), "--config",
             str(sample_qconfig), "--list"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert isinstance(data, list) and len(data) == 1
        assert data[0]["name"] == "heart_quick"


class TestDryRun:
    def test_dry_run_validates(self, sample_qconfig):
        import sys
        proc = subprocess.run(
            [sys.executable, str(Q_SCRIPT), "--config",
             str(sample_qconfig), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        assert "heart_quick" in proc.stdout
        # status.json created
        status_path = REPO_ROOT / "data_out" / "quantum_autorun" / "status.json"
        assert status_path.exists()
        data = json.loads(status_path.read_text(encoding="utf-8"))
        assert "jobs" in data and len(data["jobs"]) >= 1

    def test_job_filter(self, sample_qconfig):
        # Create multi-job config
        cfg = sample_qconfig
        with cfg.open("a", encoding="utf-8") as f:
            f.write(
                """
  - name: another
    preset: heart
"""
            )
        import sys
        proc = subprocess.run(
            [
                sys.executable,
                str(Q_SCRIPT),
                "--config",
                str(cfg),
                "--job",
                "another",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        assert "another" in proc.stdout
        assert "heart_quick" not in proc.stdout

    def test_nonexistent_job_fails(self, sample_qconfig):
        import sys
        proc = subprocess.run(
            [
                sys.executable,
                str(Q_SCRIPT),
                "--config",
                str(sample_qconfig),
                "--job",
                "nope",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode != 0
        assert "not found" in proc.stderr.lower() or "not found" in proc.stdout.lower()
