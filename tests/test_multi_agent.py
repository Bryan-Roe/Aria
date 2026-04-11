"""Focused regression tests for ``scripts/multi_agent.py``."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_multi_agent_module():
    sys.modules.pop("scripts.multi_agent", None)
    return importlib.import_module("scripts.multi_agent")


def _fake_state(*, status: str = "complete") -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        rollback_performed=False,
        tests_skipped=False,
        files_modified=[],
        tokens_estimated=0,
        duration_seconds=0.0,
        errors=[],
        to_dict=lambda: {"status": status},
    )


def test_load_jobs_from_file_preserves_optional_files(tmp_path: Path) -> None:
    mod = _load_multi_agent_module()
    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_text(
        json.dumps(
            [
                {
                    "task": "Patch consensus flow",
                    "llm_type": "echo",
                    "files": [
                        "shared/consensus_engine.py",
                        "scripts/multi_agent.py",
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    jobs = mod._load_jobs_from_file(
        str(tasks_file),
        default_llm="ollama",
        default_dry_run=False,
        default_skip_tests=False,
    )

    assert len(jobs) == 1
    assert jobs[0].files == ["shared/consensus_engine.py", "scripts/multi_agent.py"]
    assert jobs[0].llm_type == "echo"


def test_load_jobs_from_file_cli_flags_override_task_flags(tmp_path: Path) -> None:
    mod = _load_multi_agent_module()
    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_text(
        json.dumps(
            [
                {
                    "task": "Update provider logging",
                    "files": ["shared/chat_providers.py"],
                    "dry_run": False,
                    "skip_tests": False,
                }
            ]
        ),
        encoding="utf-8",
    )

    jobs = mod._load_jobs_from_file(
        str(tasks_file),
        default_llm="ollama",
        default_dry_run=True,
        default_skip_tests=True,
    )

    assert len(jobs) == 1
    assert jobs[0].llm_type == "ollama"
    assert jobs[0].files == ["shared/chat_providers.py"]
    # CLI flags are hard overrides when enabled.
    assert jobs[0].dry_run is True
    assert jobs[0].skip_tests is True


def test_run_single_job_passes_forced_files(monkeypatch) -> None:
    mod = _load_multi_agent_module()
    captured: dict[str, object] = {}

    class FakeCodeAgent:
        def __init__(self, llm_type: str, model: str | None = None):
            captured["llm_type"] = llm_type
            captured["model"] = model

        def execute_task(
            self, task, forced_files=None, dry_run=False, skip_tests=False
        ):
            captured["task"] = task
            captured["forced_files"] = forced_files
            captured["dry_run"] = dry_run
            captured["skip_tests"] = skip_tests
            return _fake_state(status="complete")

    monkeypatch.setattr(mod, "CodeAgent", FakeCodeAgent)

    job = mod.AgentJob(
        task="Patch only target files",
        llm_type="echo",
        model="demo",
        files=["scripts/multi_agent.py", "shared/consensus_engine.py"],
        dry_run=True,
        skip_tests=True,
    )

    state = mod._run_single_job(job)

    assert state.status == "complete"
    assert captured == {
        "llm_type": "echo",
        "model": "demo",
        "task": "Patch only target files",
        "forced_files": ["scripts/multi_agent.py", "shared/consensus_engine.py"],
        "dry_run": True,
        "skip_tests": True,
    }


def test_run_parallel_counts_complete_states_as_success(monkeypatch) -> None:
    mod = _load_multi_agent_module()

    monkeypatch.setattr(
        mod, "_run_single_job", lambda job: _fake_state(status="complete")
    )

    report = mod.run_parallel(
        [mod.AgentJob(task="Task A", llm_type="echo")],
        max_workers=1,
    )

    assert report.succeeded == 1
    assert report.failed == 0
    assert report.consensus["reached"] is True
    assert report.consensus["winner"] == "success"
    assert report.consensus["reason"] == "ok"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
