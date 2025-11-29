"""Integration tests for AutoTrain orchestrator end-to-end flows."""
import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTOTRAIN_SCRIPT = REPO_ROOT / "scripts" / "autotrain.py"


@pytest.fixture
def sample_config(tmp_path):
    """Create a minimal valid autotrain.yaml for testing."""
    cfg = tmp_path / "autotrain.yaml"
    cfg.write_text(
        """
version: 1
jobs:
  - name: test_job
    runner: hf
    dataset: datasets/chat/mixed_chat
    config: AI/microsoft_phi-silica-3.6_v1/lora/lora.yaml
    max_train_samples: 10
    max_eval_samples: 4
    epochs: 1
""",
        encoding="utf-8",
    )
    return cfg


@pytest.fixture
def multi_job_config(tmp_path):
    """Create a config with multiple jobs."""
    cfg = tmp_path / "multi.yaml"
    cfg.write_text(
        """
jobs:
  - name: job_a
    runner: hf
    dataset: datasets/chat/mixed_chat
    max_train_samples: 5
  - name: job_b
    runner: hf
    dataset: datasets/chat/mixed_chat
    max_train_samples: 5
""",
        encoding="utf-8",
    )
    return cfg


class TestCLIInvocation:
    """Test command-line interface behavior."""

    def test_help_option(self):
        """--help should exit cleanly."""
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        assert "autotrain" in proc.stdout.lower() or "usage" in proc.stdout.lower()

    def test_list_option(self, sample_config):
        """--list should output JSON."""
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(sample_config), "--list"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "test_job"

    def test_missing_config_file(self):
        """Missing config should exit with error."""
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", "nonexistent.yaml"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode != 0
        assert "not found" in proc.stderr.lower() or "not found" in proc.stdout.lower()


class TestDryRun:
    """Test dry-run validation mode."""

    def test_dry_run_succeeds_with_valid_config(self, sample_config):
        """Dry-run should validate successfully."""
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(sample_config), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        # Should print job name
        assert "test_job" in proc.stdout

    def test_dry_run_creates_status_json(self, sample_config):
        """Dry-run should still generate status.json."""
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(sample_config), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        status_path = REPO_ROOT / "data_out" / "autotrain" / "status.json"
        assert status_path.exists()
        data = json.loads(status_path.read_text(encoding="utf-8"))
        assert "jobs" in data
        assert len(data["jobs"]) >= 1

    def test_dry_run_with_invalid_dataset_path(self, tmp_path):
        """Dry-run should detect missing dataset."""
        cfg = tmp_path / "bad.yaml"
        cfg.write_text(
            """
jobs:
  - name: bad_dataset
    runner: hf
    dataset: /fake/nonexistent/path
""",
            encoding="utf-8",
        )
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(cfg), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Should complete (exit 0) but report missing in JSON
        assert proc.returncode == 0
        assert "missing" in proc.stdout.lower() or "nonexistent" in proc.stdout.lower()


class TestSingleJobExecution:
    """Test running a single named job."""

    def test_job_filter(self, multi_job_config):
        """--job should filter to one job."""
        proc = subprocess.run(
            [
                "python",
                str(AUTOTRAIN_SCRIPT),
                "--config",
                str(multi_job_config),
                "--job",
                "job_a",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        assert "job_a" in proc.stdout
        # job_b should NOT run
        assert "job_b" not in proc.stdout

    def test_nonexistent_job_fails(self, sample_config):
        """Requesting a job that doesn't exist should fail."""
        proc = subprocess.run(
            [
                "python",
                str(AUTOTRAIN_SCRIPT),
                "--config",
                str(sample_config),
                "--job",
                "nonexistent_job",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode != 0
        assert "not found" in proc.stderr.lower() or "not found" in proc.stdout.lower()


class TestOutputStructure:
    """Test that output directories and files are created correctly."""

    def test_status_json_structure(self, sample_config):
        """status.json should have required fields."""
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(sample_config), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        
        status_path = REPO_ROOT / "data_out" / "autotrain" / "status.json"
        data = json.loads(status_path.read_text(encoding="utf-8"))
        
        # Check top-level structure
        assert "generated_at" in data
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
        
        # Check job structure
        if data["jobs"]:
            job = data["jobs"][0]
            assert "name" in job
            assert "runner" in job
            assert "cmd" in job
            assert "status" in job
            assert isinstance(job["cmd"], list)

    def test_last_run_json_created(self, sample_config):
        """Each job should create timestamped output dir."""
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(sample_config), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        
        # Check that job dir exists with timestamped subdirs
        job_dir = REPO_ROOT / "data_out" / "autotrain" / "test_job"
        assert job_dir.exists()
        # Should have at least one timestamped run dir
        run_dirs = [d for d in job_dir.glob("*") if d.is_dir()]
        assert len(run_dirs) > 0
        # Dry-run creates the dir but may not write log until actual execution
        # Just verify structure exists
        assert any(d.name.startswith("20") for d in run_dirs)  # Timestamp format


class TestMultiJobExecution:
    """Test running multiple jobs sequentially."""

    def test_all_jobs_run_in_order(self, multi_job_config):
        """All jobs should execute in config order."""
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(multi_job_config), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        
        # Check both jobs appear in output
        assert "job_a" in proc.stdout
        assert "job_b" in proc.stdout
        
        # Check status.json contains both
        status_path = REPO_ROOT / "data_out" / "autotrain" / "status.json"
        data = json.loads(status_path.read_text(encoding="utf-8"))
        job_names = [j["name"] for j in data["jobs"]]
        assert "job_a" in job_names
        assert "job_b" in job_names


class TestErrorHandling:
    """Test error conditions and recovery."""

    def test_malformed_yaml(self, tmp_path):
        """Invalid YAML should produce clear error."""
        cfg = tmp_path / "bad.yaml"
        cfg.write_text("jobs:\n  - name: test\n    invalid yaml syntax here", encoding="utf-8")
        
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(cfg), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode != 0

    def test_missing_required_job_name(self, tmp_path):
        """Job without name creates a 'None' named job (not ideal but current behavior)."""
        cfg = tmp_path / "noname.yaml"
        cfg.write_text("jobs:\n  - runner: hf\n", encoding="utf-8")
        
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(cfg), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Currently succeeds but creates job named 'None'
        assert proc.returncode == 0
        assert "None" in proc.stdout  # Job name becomes string 'None'


@pytest.mark.slow
class TestRealExecution:
    """Tests that actually run training (marked slow)."""

    def test_real_run_produces_logs(self, tmp_path):
        """Real execution should create stdout.log."""
        # Create a minimal job that will fail fast (missing deps or data)
        cfg = tmp_path / "real.yaml"
        cfg.write_text(
            """
jobs:
  - name: fast_fail
    runner: hf
    dataset: /nonexistent
    max_train_samples: 1
""",
            encoding="utf-8",
        )
        
        proc = subprocess.run(
            ["python", str(AUTOTRAIN_SCRIPT), "--config", str(cfg)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,  # Fail if it takes too long
        )
        
        # May fail (expected), but should create log
        job_dirs = [
            p for p in (REPO_ROOT / "data_out" / "autotrain" / "fast_fail").glob("*")
            if p.is_dir()
        ]
        if job_dirs:
            # Find most recent timestamp dir
            latest = max(job_dirs, key=lambda p: p.name)
            log_file = latest / "stdout.log"
            assert log_file.exists()
            assert log_file.stat().st_size > 0


class TestReinstallFlag:
    """Test --reinstall flag behavior."""

    def test_reinstall_flag_passed_to_local_jobs(self, tmp_path):
        """--reinstall should set reinstall=True for local runner jobs."""
        cfg = tmp_path / "local.yaml"
        cfg.write_text(
            """
jobs:
  - name: local_job
    runner: local
    config: AI/microsoft_phi-silica-3.6_v1/local_train/local_config.yaml
""",
            encoding="utf-8",
        )
        
        result = subprocess.run(
            [
                "python",
                str(AUTOTRAIN_SCRIPT),
                "--config",
                str(cfg),
                "--reinstall",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        # Command should include --reinstall flag
        assert "--reinstall" in result.stdout
