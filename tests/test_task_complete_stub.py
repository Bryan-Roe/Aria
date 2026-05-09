from __future__ import annotations

import os
import subprocess
from pathlib import Path

TASK_COMPLETE = Path(__file__).resolve().parent.parent / "task_complete"


def test_task_complete_shell_stub_fails_with_guidance():
    assert os.access(TASK_COMPLETE, os.X_OK), (
        f"{TASK_COMPLETE} must be executable so shell invocation works in CI"
    )
    result = subprocess.run([str(TASK_COMPLETE)], capture_output=True, text=True)

    assert result.returncode == 64
    assert result.stdout == ""
    combined = result.stderr.lower()
    assert "does not" in combined or "cannot" in combined
    assert "real task_complete tool" in combined
    assert "completion hook" in combined
