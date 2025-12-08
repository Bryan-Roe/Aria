from typing import Any, Dict, List, cast
import subprocess
import json
from pathlib import Path

import pytest

from scripts.autotrain import load_jobs, Job


def write_yaml(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj))


def test_load_jobs_valid(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    data = {
        "jobs": [{"name": "myjob", "runner": "hf", "dataset": "datasets/foo"}]}
    write_yaml(cfg, data)

    jobs = load_jobs(cfg)
    assert isinstance(jobs, list)
    assert len(jobs) == 1
    assert isinstance(jobs[0], Job)
    assert jobs[0].name == "myjob"


def test_load_jobs_missing_name(tmp_path: Path) -> None:
    cfg = tmp_path / "missing_name.json"
    # The job entry is missing the 'name' key which should raise
    write_yaml(cfg, {"jobs": [{"runner": "hf"}]})
    with pytest.raises(ValueError, match="Every job requires a 'name'"):
        load_jobs(cfg)


def test_load_jobs_empty_name(tmp_path: Path) -> None:
    cfg = tmp_path / "empty_name.json"
    # A whitespace-only name should be rejected
    write_yaml(cfg, {"jobs": [{"name": "   ", "runner": "hf"}]})

    with pytest.raises(ValueError, match="Every job requires a non-empty 'name'"):
        load_jobs(cfg)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_autotrain_dry_run_smoke(tmp_path: Path) -> None:
    """Smoke test: the autotrain script should validate the default config in dry-run mode."""
    script = REPO_ROOT / "scripts" / "autotrain.py"
    cfg = REPO_ROOT / "config" / "training" / "autotrain.yaml"
    assert script.exists(), "autotrain.py missing"
    assert cfg.exists(), "autotrain.yaml missing"

    # Run dry-run for the named job
    import sys

    proc = subprocess.run(
        [sys.executable, str(script), "--config", str(cfg), "--job",
         "phi35_mixed_chat", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr

    # The script prints a JSON block per job result; verify at least one JSON-looking structure
    stdout = proc.stdout.strip()
    assert "phi35_mixed_chat" in stdout

    # Status file should be created
    status_path = REPO_ROOT / "data_out" / "autotrain" / "status.json"
    assert status_path.exists(), "status.json not created"
    data = cast(Dict[str, Any], json.loads(
        status_path.read_text(encoding="utf-8")))
    assert isinstance(data, dict) and "jobs" in data
    jobs = cast(List[Dict[str, Any]], data.get("jobs", []))
    assert any(j.get("name") == "phi35_mixed_chat" for j in jobs)
