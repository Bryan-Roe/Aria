"""Orchestrator — run a single self-modification cycle end-to-end.

Execution flow (matches ``aria-bot/README.md``):

1. Analyze repository state.
2. Generate improvement plan.
3. Execute safe changes (or simulate, in dry-run).
4. Validate results.
5. Commit changes (only when ``apply`` and ``commit`` are both enabled).

Every cycle writes a machine-readable status file to
``data_out/aria_bot/status.json`` so dashboards and other orchestrators
can observe progress (per the repo's status.json convention).
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .analyzer import Analyzer, Finding
from .commit_system import CommitSystem
from .executor import ExecutionResult, Executor
from .planner import Planner, UpgradePlan
from .risk_manager import RiskManager
from .validator import Validator

_logger = logging.getLogger(__name__)

# The orchestrator is stateless across runs but always writes its status
# to the same well-known location for observability.
_DEFAULT_STATUS_PATH = Path("data_out") / "aria_bot" / "status.json"


@dataclass
class OrchestratorConfig:
    """User-facing knobs for one cycle."""

    repo_root: Path
    apply: bool = False
    commit: bool = False
    max_plans: int = 50
    status_path: Optional[Path] = None

    def resolve_status_path(self) -> Path:
        if self.status_path is not None:
            return Path(self.status_path)
        return Path(self.repo_root) / _DEFAULT_STATUS_PATH


@dataclass
class CycleResult:
    """Aggregated outcome of one cycle, ready to serialize."""

    started_at: str
    finished_at: str
    duration_seconds: float
    apply: bool
    commit: bool
    findings: List[Finding] = field(default_factory=list)
    plans: List[UpgradePlan] = field(default_factory=list)
    executions: List[ExecutionResult] = field(default_factory=list)
    validation_ok: bool = True
    validation: dict = field(default_factory=dict)
    commit_sha: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        applied = [e for e in self.executions if e.applied]
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": round(self.duration_seconds, 3),
            "apply": self.apply,
            "commit": self.commit,
            "totals": {
                "findings": len(self.findings),
                "plans": len(self.plans),
                "applied": len(applied),
            },
            "findings": [f.to_dict() for f in self.findings],
            "plans": [p.to_dict() for p in self.plans],
            "executions": [e.to_dict() for e in self.executions],
            "validation_ok": self.validation_ok,
            "validation": self.validation,
            "commit_sha": self.commit_sha,
            "notes": list(self.notes),
        }


@dataclass
class Orchestrator:
    """Wire the modules together for a single cycle."""

    config: OrchestratorConfig

    def run(self) -> CycleResult:
        started = time.monotonic()
        started_iso = datetime.now(timezone.utc).isoformat()

        repo_root = Path(self.config.repo_root).resolve()
        risk = RiskManager(repo_root=repo_root)
        analyzer = Analyzer(risk_manager=risk)
        planner = Planner(risk_manager=risk, max_plans=self.config.max_plans)
        executor = Executor(risk_manager=risk, dry_run=not self.config.apply)
        validator = Validator(repo_root=repo_root)
        commits = CommitSystem(repo_root=repo_root)

        notes: List[str] = []

        _logger.info("aria-bot: scanning repository at %s", repo_root)
        findings = analyzer.scan()
        _logger.info("aria-bot: %d finding(s)", len(findings))

        plans = planner.build_plans(findings)
        _logger.info("aria-bot: %d plan(s) after risk filter", len(plans))

        executions = executor.execute(plans)
        applied_paths = [e.plan.path for e in executions if e.applied]

        validation = validator.validate(applied_paths if applied_paths else None)
        if not validation.ok:
            notes.append("validation failed; skipping commit")

        commit_sha: Optional[str] = None
        if self.config.apply and self.config.commit and validation.ok and applied_paths:
            message = self._commit_message(executions)
            commit_sha = commits.commit(applied_paths, message)
            if commit_sha is None:
                notes.append("commit step produced no SHA (nothing staged or git unavailable)")
        elif not self.config.apply:
            notes.append("dry-run: no files were modified")
        elif not applied_paths:
            notes.append("no plans were applied")

        finished = time.monotonic()
        finished_iso = datetime.now(timezone.utc).isoformat()
        result = CycleResult(
            started_at=started_iso,
            finished_at=finished_iso,
            duration_seconds=finished - started,
            apply=self.config.apply,
            commit=self.config.commit,
            findings=findings,
            plans=plans,
            executions=executions,
            validation_ok=validation.ok,
            validation=validation.to_dict(),
            commit_sha=commit_sha,
            notes=notes,
        )
        self._write_status(result)
        return result

    # ------------------------------------------------------------------
    def _commit_message(self, executions: List[ExecutionResult]) -> str:
        # Only called when at least one execution applied; defend against
        # accidental misuse by future callers.
        applied = [e for e in executions if e.applied]
        if not applied:
            return "no applied changes"
        kinds: set[str] = set()
        for e in applied:
            kinds.update(e.plan.kinds)
        kind_str = ",".join(sorted(kinds))
        return f"apply {kind_str} to {len(applied)} file(s)"

    def _write_status(self, result: CycleResult) -> None:
        status_path = self.config.resolve_status_path()
        try:
            status_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.write_text(
                json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:  # pragma: no cover - filesystem dependent
            _logger.warning("unable to write status file %s: %s", status_path, exc)


def run_cycle(
    repo_root: Path,
    *,
    apply: bool = False,
    commit: bool = False,
    max_plans: int = 50,
    status_path: Optional[Path] = None,
) -> CycleResult:
    """Convenience wrapper used by the CLI and tests."""

    config = OrchestratorConfig(
        repo_root=Path(repo_root),
        apply=apply,
        commit=commit,
        max_plans=max_plans,
        status_path=status_path,
    )
    return Orchestrator(config=config).run()
