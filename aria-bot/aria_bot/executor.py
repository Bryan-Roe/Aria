"""Executor — apply :class:`UpgradePlan` objects to the filesystem.

The executor is intentionally tiny: every supported finding kind maps to a
pure, in-memory text transform. The transformed bytes are then re-checked
by the :class:`RiskManager` before being written to disk. If anything
looks wrong we abort the plan and leave the file untouched.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence

from .planner import UpgradePlan
from .risk_manager import RiskManager

_logger = logging.getLogger(__name__)

# Each transform takes the file text and returns the rewritten text.
Transform = Callable[[str], str]


def _strip_trailing_whitespace(text: str) -> str:
    # Preserve the original line endings (LF only here — repo is LF).
    return "\n".join(line.rstrip(" \t") for line in text.split("\n"))


def _ensure_final_newline(text: str) -> str:
    if not text:
        return text
    return text if text.endswith("\n") else text + "\n"


_TRANSFORMS: Dict[str, Transform] = {
    "trailing_whitespace": _strip_trailing_whitespace,
    "missing_final_newline": _ensure_final_newline,
}

#: Finding kinds the executor knows how to apply. Keep this in sync with
#: :data:`aria_bot.analyzer.SUPPORTED_KINDS`.
SUPPORTED_KINDS: tuple[str, ...] = tuple(sorted(_TRANSFORMS.keys()))


@dataclass
class ExecutionResult:
    """Outcome of executing a single :class:`UpgradePlan`."""

    plan: UpgradePlan
    applied: bool
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "path": str(self.plan.path),
            "kinds": list(self.plan.kinds),
            "applied": self.applied,
            "reason": self.reason,
        }


@dataclass
class Executor:
    """Apply upgrade plans, with optional dry-run."""

    risk_manager: RiskManager
    dry_run: bool = True

    def execute(self, plans: Sequence[UpgradePlan]) -> List[ExecutionResult]:
        results: List[ExecutionResult] = []
        for plan in plans:
            results.append(self._execute_one(plan))
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _execute_one(self, plan: UpgradePlan) -> ExecutionResult:
        path = plan.path

        # Final path-level safety check — never trust the planner alone.
        path_assessment = self.risk_manager.assess_file(path)
        if not path_assessment.allowed:
            return ExecutionResult(plan=plan, applied=False, reason="; ".join(path_assessment.reasons))

        unsupported = [k for k in plan.kinds if k not in _TRANSFORMS]
        if unsupported:
            return ExecutionResult(
                plan=plan,
                applied=False,
                reason=f"unsupported transform(s): {','.join(unsupported)}",
            )

        try:
            original = path.read_bytes()
        except OSError as exc:
            return ExecutionResult(plan=plan, applied=False, reason=f"read failed: {exc}")

        # Apply each transform in a deterministic order.
        try:
            text = original.decode("utf-8")
        except UnicodeDecodeError:
            return ExecutionResult(plan=plan, applied=False, reason="file is not valid UTF-8")

        new_text = text
        for kind in plan.kinds:
            new_text = _TRANSFORMS[kind](new_text)
        new_bytes = new_text.encode("utf-8")

        # Diff-level safety: re-check size delta and require an actual change.
        change_assessment = self.risk_manager.assess_change(path, original, new_bytes)
        if not change_assessment.allowed:
            return ExecutionResult(plan=plan, applied=False, reason="; ".join(change_assessment.reasons))

        if self.dry_run:
            _logger.info("[dry-run] would update %s (%s)", path, plan.description())
            return ExecutionResult(plan=plan, applied=False, reason="dry-run")

        try:
            path.write_bytes(new_bytes)
        except OSError as exc:
            return ExecutionResult(plan=plan, applied=False, reason=f"write failed: {exc}")

        _logger.info("updated %s (%s)", path, plan.description())
        return ExecutionResult(plan=plan, applied=True, reason="ok")
