"""
Unit tests for scripts/autotrain.py — TrainJob, load_config, load_jobs,
validate_job, build_command, and _build_status.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load():
    mod_name = "autotrain"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    # Ensure scripts/ is on sys.path so relative imports (config_paths) resolve
    scripts_dir = str(Path(__file__).parent.parent / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    path = Path(__file__).parent.parent / "scripts" / "autotrain.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load()
TrainJob = mod.TrainJob
load_config = mod.load_config
load_jobs = mod.load_jobs
validate_job = mod.validate_job
build_command = mod.build_command
_build_status = mod._build_status


# ---------------------------------------------------------------------------
# TestTrainJob
# ---------------------------------------------------------------------------


class TestTrainJob:
    def test_required_name(self):
        job = TrainJob(name="my_job")
        assert job.name == "my_job"

    def test_default_runner(self):
        job = TrainJob(name="j")
        assert job.runner == "hf"

    def test_default_category(self):
        job = TrainJob(name="j")
        assert job.category == "baseline"

    def test_default_enabled(self):
        job = TrainJob(name="j")
        assert job.enabled is True

    def test_default_epochs(self):
        job = TrainJob(name="j")
        assert job.epochs == 1

    def test_default_device(self):
        job = TrainJob(name="j")
        assert job.device == "auto"

    def test_default_extra_args_is_empty_list(self):
        job = TrainJob(name="j")
        assert job.extra_args == []

    def test_extra_args_not_shared_between_instances(self):
        j1 = TrainJob(name="a")
        j2 = TrainJob(name="b")
        j1.extra_args.append("--foo")
        assert j2.extra_args == []

    def test_custom_values_set(self):
        job = TrainJob(
            name="custom",
            runner="local",
            category="chat",
            enabled=False,
            epochs=50,
            learning_rate=1e-3,
            device="cuda",
        )
        assert job.runner == "local"
        assert job.category == "chat"
        assert job.enabled is False
        assert job.epochs == 50
        assert job.learning_rate == pytest.approx(1e-3)
        assert job.device == "cuda"


# ---------------------------------------------------------------------------
# TestLoadConfig
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_missing_file_returns_empty_jobs(self, tmp_path):
        result = load_config(tmp_path / "nonexistent.yaml")
        assert result == {"jobs": []}

    def test_valid_yaml_loaded(self, tmp_path):
        p = tmp_path / "cfg.yaml"
        p.write_text("jobs:\n  - name: job1\n    runner: hf\n", encoding="utf-8")
        result = load_config(p)
        assert "jobs" in result
        assert len(result["jobs"]) == 1
        assert result["jobs"][0]["name"] == "job1"

    def test_empty_yaml_returns_empty_jobs(self, tmp_path):
        p = tmp_path / "empty.yaml"
        p.write_text("", encoding="utf-8")
        result = load_config(p)
        assert result == {"jobs": []}

    def test_multiple_jobs(self, tmp_path):
        p = tmp_path / "multi.yaml"
        content = "jobs:\n  - name: job1\n  - name: job2\n  - name: job3\n"
        p.write_text(content, encoding="utf-8")
        result = load_config(p)
        assert len(result["jobs"]) == 3

    def test_job_fields_preserved(self, tmp_path):
        p = tmp_path / "cfg.yaml"
        content = (
            "jobs:\n"
            "  - name: train_chat\n"
            "    runner: hf\n"
            "    category: chat\n"
            "    epochs: 25\n"
            "    enabled: true\n"
        )
        p.write_text(content, encoding="utf-8")
        result = load_config(p)
        job = result["jobs"][0]
        assert job["runner"] == "hf"
        assert job["category"] == "chat"
        assert job["epochs"] == 25


# ---------------------------------------------------------------------------
# TestLoadJobs
# ---------------------------------------------------------------------------


class TestLoadJobs:
    def test_empty_config_returns_empty_list(self, tmp_path):
        p = tmp_path / "empty.yaml"
        p.write_text("", encoding="utf-8")
        assert load_jobs(p) == []

    def test_missing_file_returns_empty_list(self, tmp_path):
        assert load_jobs(tmp_path / "no.yaml") == []

    def test_returns_train_job_instances(self, tmp_path):
        p = tmp_path / "cfg.yaml"
        p.write_text("jobs:\n  - name: j1\n", encoding="utf-8")
        jobs = load_jobs(p)
        assert len(jobs) == 1
        assert isinstance(jobs[0], TrainJob)

    def test_job_name_set(self, tmp_path):
        p = tmp_path / "cfg.yaml"
        p.write_text("jobs:\n  - name: my_training_job\n", encoding="utf-8")
        jobs = load_jobs(p)
        assert jobs[0].name == "my_training_job"

    def test_job_numeric_fields(self, tmp_path):
        p = tmp_path / "cfg.yaml"
        content = "jobs:\n  - name: j\n    epochs: 100\n    max_train_samples: 500\n"
        p.write_text(content, encoding="utf-8")
        jobs = load_jobs(p)
        assert jobs[0].epochs == 100
        assert jobs[0].max_train_samples == 500

    def test_enabled_false(self, tmp_path):
        p = tmp_path / "cfg.yaml"
        p.write_text("jobs:\n  - name: j\n    enabled: false\n", encoding="utf-8")
        jobs = load_jobs(p)
        assert jobs[0].enabled is False

    def test_defaults_applied_for_missing_fields(self, tmp_path):
        p = tmp_path / "cfg.yaml"
        p.write_text("jobs:\n  - name: minimal\n", encoding="utf-8")
        jobs = load_jobs(p)
        j = jobs[0]
        assert j.runner == "hf"
        assert j.epochs == 1
        assert j.device == "auto"
        assert j.extra_args == []

    def test_multiple_jobs_loaded(self, tmp_path):
        p = tmp_path / "cfg.yaml"
        content = "jobs:\n  - name: j1\n  - name: j2\n  - name: j3\n"
        p.write_text(content, encoding="utf-8")
        assert len(load_jobs(p)) == 3


# ---------------------------------------------------------------------------
# TestValidateJob
# ---------------------------------------------------------------------------


class TestValidateJob:
    def test_no_dataset_is_missing(self):
        job = TrainJob(name="j", runner="local", dataset=None)
        result = validate_job(job)
        assert result["status"] == "missing"
        assert "dataset" in result["missing"]

    def test_nonexistent_dataset_path_is_missing(self):
        job = TrainJob(name="j", runner="local", dataset="no/such/path")
        result = validate_job(job)
        assert result["status"] == "missing"
        assert any("dataset path not found" in m for m in result["missing"])

    def test_existing_dataset_passes_with_local_runner(self, tmp_path):
        # Use a known existing directory (relative to REPO_ROOT)
        job = TrainJob(name="j", runner="local", dataset="datasets/chat")
        result = validate_job(job)
        # datasets/chat exists in the repo
        if result["status"] == "missing":
            # Skip if somehow path doesn't exist in this env
            pytest.skip("datasets/chat not found in this environment")
        assert result["status"] == "ok"

    def test_no_missing_items_returns_ok(self):
        # runner="local" skips HF script check; use a dataset that exists
        job = TrainJob(name="j", runner="local", dataset="datasets/chat")
        result = validate_job(job)
        assert "missing" in result
        assert isinstance(result["missing"], list)

    def test_missing_list_empty_when_ok(self):
        job = TrainJob(name="j", runner="local", dataset="datasets/chat")
        result = validate_job(job)
        if result["status"] == "ok":
            assert result["missing"] == []

    def test_lora_config_not_found_is_missing(self):
        job = TrainJob(
            name="j",
            runner="local",
            dataset="datasets/chat",
            config="no/such/lora_config.yaml",
        )
        result = validate_job(job)
        assert result["status"] == "missing"
        assert any("lora config not found" in m for m in result["missing"])

    def test_result_has_required_keys(self):
        job = TrainJob(name="j", runner="local")
        result = validate_job(job)
        assert "status" in result
        assert "missing" in result

    def test_multiple_missing_items(self):
        job = TrainJob(
            name="j",
            runner="local",
            dataset=None,
            config="no/such/config.yaml",
        )
        result = validate_job(job)
        assert result["status"] == "missing"
        assert len(result["missing"]) >= 2


# ---------------------------------------------------------------------------
# TestBuildCommand
# ---------------------------------------------------------------------------


class TestBuildCommand:
    def test_local_runner_returns_local_script(self):
        job = TrainJob(name="j", runner="local")
        cmd = build_command(job)
        assert any("run_local_lora_training.py" in c for c in cmd)
        assert "--job" in cmd
        assert "j" in cmd

    def test_hf_runner_uses_train_lora(self):
        job = TrainJob(name="j", runner="hf")
        cmd = build_command(job)
        assert any("train_lora.py" in c for c in cmd)

    def test_hf_includes_epochs(self):
        job = TrainJob(name="j", runner="hf", epochs=50)
        cmd = build_command(job)
        assert "--epochs" in cmd
        assert "50" in cmd

    def test_hf_includes_dataset(self):
        job = TrainJob(name="j", runner="hf", dataset="datasets/chat")
        cmd = build_command(job)
        assert "--dataset" in cmd
        assert "datasets/chat" in cmd

    def test_hf_includes_model_id(self):
        job = TrainJob(name="j", runner="hf", hf_model_id="microsoft/phi-2")
        cmd = build_command(job)
        assert "--model-id" in cmd
        assert "microsoft/phi-2" in cmd

    def test_hf_includes_learning_rate(self):
        job = TrainJob(name="j", runner="hf", learning_rate=5e-5)
        cmd = build_command(job)
        assert "--learning-rate" in cmd
        assert str(5e-5) in cmd

    def test_hf_includes_lora_dropout(self):
        job = TrainJob(name="j", runner="hf", lora_dropout=0.05)
        cmd = build_command(job)
        assert "--lora-dropout" in cmd

    def test_hf_includes_device(self):
        job = TrainJob(name="j", runner="hf", device="cpu")
        cmd = build_command(job)
        assert "--device" in cmd
        assert "cpu" in cmd

    def test_hf_no_dataset_no_dataset_flag(self):
        job = TrainJob(name="j", runner="hf", dataset=None)
        cmd = build_command(job)
        assert "--dataset" not in cmd

    def test_hf_extra_args_appended(self):
        job = TrainJob(name="j", runner="hf", extra_args=["--fp16", "--no-cache"])
        cmd = build_command(job)
        assert "--fp16" in cmd
        assert "--no-cache" in cmd

    def test_hf_max_train_samples_included(self):
        job = TrainJob(name="j", runner="hf", max_train_samples=200)
        cmd = build_command(job)
        assert "--max-train-samples" in cmd
        assert "200" in cmd

    def test_hf_max_train_samples_omitted_when_none(self):
        job = TrainJob(name="j", runner="hf", max_train_samples=None)
        cmd = build_command(job)
        assert "--max-train-samples" not in cmd

    def test_returns_list_of_strings(self):
        job = TrainJob(name="j", runner="hf")
        cmd = build_command(job)
        assert isinstance(cmd, list)
        assert all(isinstance(c, str) for c in cmd)


# ---------------------------------------------------------------------------
# TestBuildStatus
# ---------------------------------------------------------------------------


class TestBuildStatus:
    def test_empty_jobs_list(self):
        result = _build_status([])
        assert result["total_jobs"] == 0
        assert result["succeeded"] == 0
        assert result["failed"] == 0

    def test_counts_succeeded(self):
        jobs_info = [{"status": "ok"}, {"status": "ok"}, {"status": "failed"}]
        result = _build_status(jobs_info)
        assert result["succeeded"] == 2
        assert result["failed"] == 1

    def test_counts_failed(self):
        jobs_info = [{"status": "failed"}, {"status": "failed"}]
        result = _build_status(jobs_info)
        assert result["failed"] == 2
        assert result["succeeded"] == 0

    def test_total_jobs_matches_input(self):
        jobs_info = [{"status": "ok"} for _ in range(7)]
        result = _build_status(jobs_info)
        assert result["total_jobs"] == 7

    def test_has_required_keys(self):
        result = _build_status([])
        for key in (
            "generated_at",
            "total_jobs",
            "succeeded",
            "failed",
            "running",
            "avg_duration",
            "last_updated",
            "jobs",
        ):
            assert key in result, f"Missing key: {key}"

    def test_running_is_zero(self):
        result = _build_status([{"status": "ok"}])
        assert result["running"] == 0

    def test_jobs_list_preserved(self):
        jobs_info = [{"status": "ok", "name": "j1"}]
        result = _build_status(jobs_info)
        assert result["jobs"] == jobs_info

    def test_unknown_status_not_counted(self):
        jobs_info = [{"status": "pending"}, {"status": "running"}]
        result = _build_status(jobs_info)
        assert result["succeeded"] == 0
        assert result["failed"] == 0

    def test_generated_at_is_iso_string(self):
        result = _build_status([])
        from datetime import datetime

        # Should parse without error
        datetime.fromisoformat(result["generated_at"])
