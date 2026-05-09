from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "training-health-report.yml"


def _extract_status_script() -> str:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    marker = "python3 - << 'PYEOF'\n"
    start = text.index(marker) + len(marker)
    end = text.index("\n          PYEOF", start)
    return textwrap.dedent(text[start:end]).strip()


def _run_status_script(tmp_path: Path, training: dict) -> dict:
    (tmp_path / "data_out").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data_out" / "autonomous_training_status.json").write_text(
        json.dumps(training), encoding="utf-8"
    )

    github_output = tmp_path / "github_output.txt"
    env = os.environ.copy()
    env["GITHUB_OUTPUT"] = str(github_output)

    proc = subprocess.run(
        [sys.executable, "-c", _extract_status_script()],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert proc.returncode == 0, proc.stderr
    pairs = {}
    for line in github_output.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            pairs[key] = value
    return pairs


def test_no_training_attempt_is_no_data_not_degraded(tmp_path: Path) -> None:
    outputs = _run_status_script(
        tmp_path,
        {
            "cycles_completed": 0,
            "best_accuracy": 0.0,
            "performance_history": [],
            "dataset_inventory": {},
        },
    )

    assert outputs["no_data"] == "true"
    assert outputs["degraded"] == "false"


def test_low_accuracy_after_training_is_degraded(tmp_path: Path) -> None:
    outputs = _run_status_script(
        tmp_path,
        {
            "cycles_completed": 1,
            "best_accuracy": 0.2,
            "performance_history": [{"accuracy": 0.2}],
            "dataset_inventory": {},
        },
    )

    assert outputs["no_data"] == "false"
    assert outputs["degraded"] == "true"
