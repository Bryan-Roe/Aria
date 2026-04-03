"""Unit tests for scripts/parallel_train.py concurrency orchestration."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

_PT_PATH = SCRIPTS_DIR / "parallel_train.py"
_spec = importlib.util.spec_from_file_location("_test_parallel_train", _PT_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load parallel_train module from {_PT_PATH}")
parallel_train = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parallel_train)
ParallelTrainer = parallel_train.ParallelTrainer


def _write_parallel_config(tmp_path: Path, jobs: list[dict]) -> Path:
    config_path = tmp_path / "parallel_train_test.yaml"
    config_path.write_text(yaml.safe_dump({"jobs": jobs}), encoding="utf-8")
    return config_path


def _job(name: str) -> dict:
    return {
        "name": name,
        "dataset": "datasets/chat",
        "save_dir": f"data_out/{name}",
        "hf_model_id": "tiny-test-model",
    }


@pytest.mark.unit
def test_run_all_parallel_cycles_devices_and_writes_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _write_parallel_config(
        tmp_path,
        [_job("quantum-a"), _job("quantum-b"), _job("quantum-c")],
    )
    trainer = ParallelTrainer(
        str(config_path), max_parallel=2, perform_evaluation=False
    )
    trainer.root = tmp_path

    seen_devices: dict[str, int] = {}

    async def fake_run_job(job: dict, device_id: int) -> dict:
        seen_devices[job["name"]] = device_id
        await asyncio.sleep(0)
        return {
            "name": job["name"],
            "status": "succeeded",
            "device": device_id,
            "evaluation": {
                "pre_eval_perplexity": 10.0,
                "post_eval_perplexity": 5.0,
            },
        }

    monkeypatch.setattr(trainer, "run_job", fake_run_job)

    asyncio.run(trainer.run_all_parallel("quantum-*"))

    assert seen_devices == {
        "quantum-a": 0,
        "quantum-b": 1,
        "quantum-c": 0,
    }

    status_path = tmp_path / "data_out" / "parallel_training" / "status.json"
    data = json.loads(status_path.read_text(encoding="utf-8"))
    assert data["total_runs"] == 1
    assert len(data["runs"]) == 1
    assert len(data["runs"][0]["jobs"]) == 3
    assert data["runs"][0]["job_ranking"][0]["name"] in {
        "quantum-a",
        "quantum-b",
        "quantum-c",
    }


@pytest.mark.unit
def test_run_all_parallel_appends_status_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _write_parallel_config(tmp_path, [_job("quantum-next")])
    trainer = ParallelTrainer(
        str(config_path), max_parallel=1, perform_evaluation=False
    )
    trainer.root = tmp_path

    status_dir = tmp_path / "data_out" / "parallel_training"
    status_dir.mkdir(parents=True, exist_ok=True)
    status_path = status_dir / "status.json"
    status_path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": "old-run",
                        "jobs": [{"name": "old-job", "status": "succeeded"}],
                    }
                ],
                "total_runs": 1,
                "last_updated": "2026-03-17T00:00:00",
            }
        ),
        encoding="utf-8",
    )

    async def fake_run_job(job: dict, device_id: int) -> dict:
        await asyncio.sleep(0)
        return {
            "name": job["name"],
            "status": "skipped",
            "device": device_id,
            "reason": "insufficient_train_samples",
        }

    monkeypatch.setattr(trainer, "run_job", fake_run_job)

    asyncio.run(trainer.run_all_parallel("quantum-*"))

    data = json.loads(status_path.read_text(encoding="utf-8"))
    assert data["total_runs"] == 2
    assert len(data["runs"]) == 2
    assert data["runs"][-1]["jobs"][0]["name"] == "quantum-next"
    assert data["runs"][-1]["jobs"][0]["status"] == "skipped"
