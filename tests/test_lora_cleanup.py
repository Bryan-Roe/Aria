import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = REPO_ROOT / "data_out" / "parallel_training" / "status.json"


def test_lora_cleanup_removes_checkpoint_artifacts():
    if not STATUS_PATH.exists():
        pytest.skip("parallel_training status.json missing")
    data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    # Find any job with cleanup completed
    for run in data.get("runs", []):
        for job in run.get("jobs", []):
            if job.get("cleanup") == "completed":
                save_dir = job.get("output_dir")
                if not save_dir:
                    continue
                # output_dir is relative path like data_out/lora_training/<token>
                full_path = REPO_ROOT / Path(save_dir)
                if not full_path.exists():
                    continue
                checkpoint_dirs = [
                    p for p in full_path.glob("checkpoint*") if p.is_dir()
                ]
                assert (
                    not checkpoint_dirs
                ), f"Found leftover checkpoints: {[p.name for p in checkpoint_dirs]}"
                return
    pytest.skip("No completed cleanup jobs found to validate")
