"""Scan orchestrator status files for stale or failed runs."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agents.base import REPO_ROOT, AgentResult, AutomationAgent, register  # noqa: E402

TIMESTAMP_FIELDS = ("last_updated", "timestamp", "updated_at", "last_run", "completed_at")
FAILED_STATES = {"failed", "error", "crashed"}


@register
class StatusFreshnessAgent(AutomationAgent):
    """Check data_out status files for stale timestamps and failed runs."""

    name = "status-freshness"
    description = "Scans orchestrator status.json files for stale timestamps and failed run states."

    def __init__(
        self,
        repo_root: Path | None = None,
        *,
        max_age_hours: float = 24.0,
        data_dir: Path | None = None,
    ) -> None:
        """Initialize the agent with an optional max age and scan directory."""
        super().__init__(repo_root=repo_root)
        self.max_age_hours = max_age_hours
        self.data_dir = Path(data_dir) if data_dir is not None else self.repo_root / "data_out"

    def run(self) -> AgentResult:
        """Scan status files and return stale, failed, and parse findings."""
        findings: list[dict] = []
        metrics = {"files_scanned": 0, "stale": 0, "failed": 0, "unparseable": 0, "no_timestamp": 0}
        now = datetime.now(timezone.utc)

        if not self.data_dir.exists():
            return self.make_result(
                status="ok",
                summary=f"Scanned 0 status files under {self._relative_path(self.data_dir)}; no issues found.",
                findings=findings,
                metrics=metrics,
            )

        for path in sorted(self.data_dir.rglob("status.json")):
            if self._is_agent_output(path):
                continue

            metrics["files_scanned"] += 1
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (JSONDecodeError, OSError) as exc:
                self._add_finding(findings, metrics, path, "unparseable", f"Could not parse JSON: {exc}")
                continue

            timestamp = self._find_timestamp(payload)
            if timestamp is None:
                self._add_finding(findings, metrics, path, "no_timestamp", "No recognized timestamp field found.")
            else:
                age_hours = (now - timestamp).total_seconds() / 3600
                if age_hours > self.max_age_hours:
                    self._add_finding(
                        findings,
                        metrics,
                        path,
                        "stale",
                        f"Last update is {round(age_hours)} hours old; max allowed is {self.max_age_hours:g} hours.",
                    )

            if self._has_failed(payload):
                self._add_finding(findings, metrics, path, "failed", "Status reports failed, error, or crashed state.")

        if metrics["unparseable"] or metrics["failed"]:
            status = "error"
        elif metrics["stale"] or metrics["no_timestamp"]:
            status = "warning"
        else:
            status = "ok"

        issue_count = len(findings)
        summary = (
            f"Scanned {metrics['files_scanned']} status files; "
            f"found {issue_count} issue{'s' if issue_count != 1 else ''}."
        )
        return self.make_result(status=status, summary=summary, findings=findings, metrics=metrics)

    def _is_agent_output(self, path: Path) -> bool:
        """Return true when *path* is under an agents output directory."""
        try:
            relative_parts = path.relative_to(self.data_dir).parts
        except ValueError:
            relative_parts = path.parts
        return "agents" in relative_parts[:-1] or path.parent.name == "agents"

    def _find_timestamp(self, payload: object) -> datetime | None:
        """Return the first recognized timestamp parsed as UTC, if present."""
        if not isinstance(payload, dict):
            return None

        for field in TIMESTAMP_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                continue
            parsed = self._parse_iso_datetime(value)
            if parsed is not None:
                return parsed
        return None

    def _parse_iso_datetime(self, value: str) -> datetime | None:
        """Parse an ISO-8601 timestamp, accepting trailing Z and naive UTC values."""
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _has_failed(self, payload: object) -> bool:
        """Return true when a status payload reports failures."""
        if not isinstance(payload, dict):
            return False

        failed = payload.get("failed")
        if isinstance(failed, (int, float)) and not isinstance(failed, bool) and failed > 0:
            return True

        for field in ("status", "state"):
            value = payload.get(field)
            if isinstance(value, str) and value.casefold() in FAILED_STATES:
                return True
        return False

    def _add_finding(
        self,
        findings: list[dict],
        metrics: dict,
        path: Path,
        issue: str,
        detail: str,
    ) -> None:
        """Append one finding and increment its metric."""
        findings.append({"file": self._relative_path(path), "issue": issue, "detail": detail})
        metrics[issue] += 1

    def _relative_path(self, path: Path) -> str:
        """Return *path* relative to the configured repo root when possible."""
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the status freshness agent."""
    parser = argparse.ArgumentParser(description=StatusFreshnessAgent.description)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data_out", help="Directory to scan.")
    parser.add_argument("--max-age-hours", type=float, default=24.0, help="Maximum allowed status age in hours.")
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Return exit code 1 when stale or failed status files are found.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute results without writing status.json.")
    parser.add_argument("--json", action="store_true", help="Print the full result as JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the status freshness CLI and return a process exit code."""
    args = build_parser().parse_args(argv)
    agent = StatusFreshnessAgent(data_dir=args.data_dir, max_age_hours=args.max_age_hours)
    result = agent.run()

    if not args.dry_run:
        agent.write_status(result)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.summary)

    if result.status == "error":
        return 1
    if args.fail_on_stale and (result.metrics["stale"] or result.metrics["failed"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
