"""Unit tests for AutoTrain orchestrator components."""
from autotrain import (
    Job,
    read_yaml,
    load_jobs,
    build_hf_command,
    build_local_command,
)
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import json
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))


# Import the module under test
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))


class TestJobDataclass:
    """Test Job dataclass creation and defaults."""

    def test_minimal_job(self):
        j = Job(name="test_job")
        assert j.name == "test_job"
        assert j.runner == "hf"
        assert j.dataset is None
        assert j.reinstall is False
        assert j.extra_args == []

    def test_full_job(self):
        j = Job(
            name="full_job",
            runner="local",
            dataset="data/train",
            config="config.yaml",
            learning_rate=0.0001,
            epochs=3,
            reinstall=True,
            extra_args=["--verbose"],
        )
        assert j.name == "full_job"
        assert j.runner == "local"
        assert j.learning_rate == 0.0001
        assert j.epochs == 3
        assert j.reinstall is True
        assert j.extra_args == ["--verbose"]


class TestYAMLParsing:
    """Test YAML config loading and job parsing."""

    def test_read_yaml(self, tmp_path):
        cfg = tmp_path / "test.yaml"
        cfg.write_text("foo: bar\nlist:\n  - a\n  - b\n", encoding="utf-8")
        data = read_yaml(cfg)
        assert data == {"foo": "bar", "list": ["a", "b"]}

    def test_load_jobs_single(self, tmp_path):
        cfg = tmp_path / "autotrain.yaml"
        cfg.write_text(
            """
version: 1
jobs:
  - name: test_job
    runner: hf
    dataset: datasets/test
    epochs: 2
""",
            encoding="utf-8",
        )
        jobs = load_jobs(cfg)
        assert len(jobs) == 1
        assert jobs[0].name == "test_job"
        assert jobs[0].runner == "hf"
        assert jobs[0].dataset == "datasets/test"
        assert jobs[0].epochs == 2

    def test_load_jobs_multiple(self, tmp_path):
        cfg = tmp_path / "autotrain.yaml"
        cfg.write_text(
            """
jobs:
  - name: job1
    runner: hf
  - name: job2
    runner: local
    reinstall: true
""",
            encoding="utf-8",
        )
        jobs = load_jobs(cfg)
        assert len(jobs) == 2
        assert jobs[0].name == "job1"
        assert jobs[1].name == "job2"
        assert jobs[1].reinstall is True

    def test_load_jobs_missing_name_raises(self, tmp_path):
        cfg = tmp_path / "autotrain.yaml"
        cfg.write_text("jobs:\n  - runner: hf\n", encoding="utf-8")
        with pytest.raises(ValueError) as excinfo:
            load_jobs(cfg)
        assert "name" in str(excinfo.value).lower()


class TestHFCommandBuilder:
    """Test HuggingFace runner command building."""

    def test_minimal_command(self):
        job = Job(name="test")
        cmd = build_hf_command(job)
        # Should have python + script at minimum
        assert len(cmd) >= 2
        assert cmd[0].endswith("python.exe") or cmd[0].endswith("python")
        assert "train_lora.py" in cmd[1]

    def test_command_with_dataset_and_config(self):
        job = Job(
            name="test",
            dataset="datasets/test",
            config="configs/lora.yaml",
        )
        cmd = build_hf_command(job)
        assert "--dataset" in cmd
        assert "datasets/test" in cmd
        assert "--config" in cmd
        assert "configs/lora.yaml" in cmd

    def test_command_with_overrides(self):
        job = Job(
            name="test",
            learning_rate=0.0001,
            lora_dropout=0.05,
            epochs=5,
            max_train_samples=100,
            max_eval_samples=20,
            seed=123,
            hf_model_id="microsoft/Phi-3.5-mini-instruct",
            save_dir="output",
        )
        cmd = build_hf_command(job)
        assert "--learning-rate" in cmd
        assert "0.0001" in cmd
        assert "--lora-dropout" in cmd
        assert "0.05" in cmd
        assert "--epochs" in cmd
        assert "5" in cmd
        assert "--max-train-samples" in cmd
        assert "100" in cmd
        assert "--max-eval-samples" in cmd
        assert "20" in cmd
        assert "--seed" in cmd
        assert "123" in cmd
        assert "--hf-model-id" in cmd
        assert "microsoft/Phi-3.5-mini-instruct" in cmd
        assert "--save-dir" in cmd
        assert "output" in cmd

    def test_command_with_extra_args(self):
        job = Job(
            name="test",
            extra_args=["--no-stream", "--deepspeed", "ds_config.json"],
        )
        cmd = build_hf_command(job)
        assert "--no-stream" in cmd
        assert "--deepspeed" in cmd
        assert "ds_config.json" in cmd


class TestLocalCommandBuilder:
    """Test local runner command building."""

    def test_minimal_command(self):
        job = Job(name="test", runner="local")
        cmd = build_local_command(job)
        assert len(cmd) >= 2
        assert cmd[0].endswith("python.exe") or cmd[0].endswith("python")
        assert "run_local_lora_training.py" in cmd[1]

    def test_command_with_config(self):
        job = Job(
            name="test",
            runner="local",
            config="AI/microsoft_phi-silica-3.6_v1/local_train/local_config.yaml",
        )
        cmd = build_local_command(job)
        assert "--config" in cmd
        # Should use basename for local runner
        assert "local_config.yaml" in cmd

    def test_command_with_samples_and_epochs(self):
        job = Job(
            name="test",
            runner="local",
            max_train_samples=50,
            epochs=2,
        )
        cmd = build_local_command(job)
        assert "--max-samples" in cmd
        assert "50" in cmd
        assert "--epochs" in cmd
        assert "2" in cmd

    def test_command_with_reinstall(self):
        job = Job(
            name="test",
            runner="local",
            reinstall=True,
        )
        cmd = build_local_command(job)
        assert "--reinstall" in cmd

    def test_command_ignores_hf_specific_params(self):
        """Local runner should not include HF-specific params."""
        job = Job(
            name="test",
            runner="local",
            learning_rate=0.0001,  # Not used by local runner
            lora_dropout=0.05,  # Not used by local runner
            hf_model_id="microsoft/Phi-3.5-mini-instruct",  # Not used
        )
        cmd = build_local_command(job)
        # These should NOT appear in local runner commands
        assert "--learning-rate" not in cmd
        assert "--lora-dropout" not in cmd
        assert "--hf-model-id" not in cmd


class TestValidation:
    """Test validation logic in dry-run mode."""

    @patch("autotrain.HF_TRAIN_SCRIPT", Path("/fake/train_lora.py"))
    @patch("autotrain.LOCAL_RUNNER", Path("/fake/local_runner.py"))
    def test_dry_run_detects_missing_scripts(self):
        """Dry-run should detect missing training scripts."""
        from autotrain import run_job

        job = Job(name="test", runner="hf", dataset="datasets/fake")
        result = run_job(job, dry_run=True)
        assert result["status"] == "missing"
        assert any("train_lora.py" in m for m in result.get("missing", []))

    def test_dry_run_detects_missing_dataset(self, tmp_path):
        """Dry-run should detect missing dataset paths."""
        from autotrain import run_job

        job = Job(
            name="test",
            dataset=str(tmp_path / "nonexistent"),
        )
        result = run_job(job, dry_run=True)
        # Should report missing dataset
        assert "missing" in result or result["status"] == "missing"


class TestStatusJSON:
    """Test status JSON generation and structure."""

    def test_collect_status_structure(self):
        from autotrain import collect_status

        results = [
            {
                "name": "job1",
                "status": "succeeded",
                "return_code": 0,
            },
            {
                "name": "job2",
                "status": "failed",
                "return_code": 1,
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("autotrain.DATA_OUT", Path(tmpdir)):
                status = collect_status(results)

        assert "generated_at" in status
        assert "jobs" in status
        assert len(status["jobs"]) == 2
        assert status["jobs"][0]["name"] == "job1"
        assert status["jobs"][1]["name"] == "job2"


class TestCLIParsing:
    """Test command-line argument handling."""

    def test_list_option_returns_jobs(self, tmp_path):
        """--list should output job configurations as JSON."""
        cfg = tmp_path / "test.yaml"
        cfg.write_text(
            """
jobs:
  - name: test1
    runner: hf
  - name: test2
    runner: local
""",
            encoding="utf-8",
        )

        # We can't easily test main() with sys.exit, but we can test load_jobs
        jobs = load_jobs(cfg)
        job_dicts = [j.__dict__ for j in jobs]
        json_str = json.dumps(job_dicts, indent=2)

        assert "test1" in json_str
        assert "test2" in json_str
        parsed = json.loads(json_str)
        assert len(parsed) == 2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_jobs_list(self, tmp_path):
        cfg = tmp_path / "empty.yaml"
        cfg.write_text("jobs: []\n", encoding="utf-8")
        jobs = load_jobs(cfg)
        assert jobs == []

    def test_no_jobs_key(self, tmp_path):
        cfg = tmp_path / "nojobs.yaml"
        cfg.write_text("version: 1\n", encoding="utf-8")
        jobs = load_jobs(cfg)
        assert jobs == []

    def test_job_with_none_values(self, tmp_path):
        """Jobs with null/None values should work."""
        cfg = tmp_path / "nulls.yaml"
        cfg.write_text(
            """
jobs:
  - name: test
    runner: hf
    dataset: null
    config: null
""",
            encoding="utf-8",
        )
        jobs = load_jobs(cfg)
        assert len(jobs) == 1
        assert jobs[0].dataset is None
        assert jobs[0].config is None

    def test_extra_args_empty_list(self):
        job = Job(name="test", extra_args=[])
        cmd = build_hf_command(job)
        # Should not crash with empty extra_args
        assert isinstance(cmd, list)

    def test_path_with_spaces(self):
        """Commands should handle paths with spaces."""
        job = Job(
            name="test",
            dataset="my datasets/chat data",
            config="configs/my lora.yaml",
        )
        cmd = build_hf_command(job)
        assert "my datasets/chat data" in cmd
        assert "configs/my lora.yaml" in cmd
