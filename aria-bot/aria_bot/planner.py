"""Planner — convert :class:`Finding` objects into :class:`UpgradePlan` items.

A :class:`UpgradePlan` is a single, atomic, file-scoped change. Plans are
filtered by the :class:`RiskManager` before being returned, so callers can
treat the output as already vetted at the path level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence

from .analyzer import Finding
from .risk_manager import RiskManager

_logger = logging.getLogger(__name__)


@dataclass
class UpgradePlan:
    """A grouped, file-scoped set of findings to apply together."""

    path: Path
    kinds: tuple[str, ...]
    findings: tuple[Finding, ...] = field(default_factory=tuple)

    def description(self) -> str:
        if len(self.kinds) == 1:
            return self.kinds[0]
        return "+".join(self.kinds)

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "kinds": list(self.kinds),
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class Planner:
    """Group findings into atomic per-file upgrade plans."""

    risk_manager: RiskManager
    max_plans: int = 50

    def build_plans(self, findings: Sequence[Finding]) -> List[UpgradePlan]:
        # Group findings by file so each plan is a single commit candidate.
        by_path: dict[Path, list[Finding]] = {}
        for finding in findings:
            by_path.setdefault(finding.path, []).append(finding)

        plans: List[UpgradePlan] = []
        for path, file_findings in by_path.items():
            assessment = self.risk_manager.assess_file(path)
            if not assessment.allowed:
                _logger.debug(
                    "planner: skipping %s due to risk policy: %s",
                    path,
                    assessment.reasons,
                )
                continue

            kinds = tuple(sorted({f.kind for f in file_findings}))
            plans.append(
                UpgradePlan(
                    path=path,
                    kinds=kinds,
                    findings=tuple(file_findings),
                )
            )

        # Sort plans for deterministic output and apply the cycle cap.
        plans.sort(key=lambda p: str(p.path))
        if len(plans) > self.max_plans:
            _logger.info(
                "planner: trimming %d plans to max_plans=%d",
                len(plans),
                self.max_plans,
            )
            plans = plans[: self.max_plans]
        return plans
