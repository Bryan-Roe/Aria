"""Validator — run lint / tests after executor changes.

The validator is best-effort: if a tool is missing it returns success with
a note, rather than blocking the loop. The orchestrator decides how to
react to validation results (e.g., revert and skip commit).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence

_logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Aggregate result of all validation steps."""

    ok: bool
    steps: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "steps": list(self.steps)}


@dataclass
class Validator:
    """Run lightweight repository checks after applying changes."""

    repo_root: Path
    timeout_seconds: int = 120

    def validate(self, changed_paths: Sequence[Path] | None = None) -> ValidationResult:
        steps: List[dict] = []
        ok = True

        ruff_step = self._run_ruff(changed_paths)
        steps.append(ruff_step)
        if ruff_step["status"] == "failed":
            ok = False

        return ValidationResult(ok=ok, steps=steps)

    # ------------------------------------------------------------------
    def _run_ruff(self, changed_paths: Sequence[Path] | None) -> dict:
        ruff = shutil.which("ruff")
        if not ruff:
            return {
                "name": "ruff",
                "status": "skipped",
                "reason": "ruff binary not found on PATH",
            }

        targets: list[str]
        if changed_paths:
            targets = [str(p) for p in changed_paths if p.suffix == ".py"]
            if not targets:
                return {
                    "name": "ruff",
                    "status": "skipped",
                    "reason": "no python files in changeset",
                }
        else:
            targets = ["."]

        cmd = [ruff, "check", *targets]
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {"name": "ruff", "status": "failed", "reason": "ruff timed out"}
        except OSError as exc:  # pragma: no cover - environment dependent
            return {"name": "ruff", "status": "skipped", "reason": f"ruff not runnable: {exc}"}

        status = "passed" if proc.returncode == 0 else "failed"
        return {
            "name": "ruff",
            "status": status,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
        }
