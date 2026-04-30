from __future__ import annotations

import subprocess
from pathlib import Path

TASK_COMPLETE = Path(__file__).resolve().parent.parent / "task_complete"


def test_task_complete_shell_stub_fails_with_guidance():
    result = subprocess.run([str(TASK_COMPLETE)], capture_output=True, text=True)

    assert result.returncode == 64
    assert result.stdout == ""
    combined = result.stderr.lower()
    assert "does not" in combined or "cannot" in combined
    assert "real task_complete tool" in combined
    assert "completion hook" in combined
