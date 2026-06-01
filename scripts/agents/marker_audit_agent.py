"""Audit repository source files for maintenance marker comments."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path

_REPO_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FOR_IMPORT))

from scripts.agents.base import (  # noqa: E402
    REPO_ROOT,
    AgentResult,
    AutomationAgent,
    iter_source_files,
    register,
)

MARKER_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX|BUG)\b")
SOURCE_EXTENSIONS = {"py", "js", "ts", "jsx", "tsx", "md", "sh", "yaml", "yml", "html", "css"}
MARKER_NAMES = ("TODO", "FIXME", "HACK", "XXX", "BUG")
MAX_TEXT_LENGTH = 200
_THIS_FILE = Path(__file__).resolve()


@register
class MarkerAuditAgent(AutomationAgent):
    """Scan source files for maintenance markers such as TODO and FIXME."""

    name = "marker-audit"
    description = "Scans repository source files for TODO/FIXME/HACK/XXX/BUG markers."

    def run(self) -> AgentResult:
        """Execute the marker audit and return a structured result."""
        findings: list[dict] = []
        by_marker = dict.fromkeys(MARKER_NAMES, 0)
        files_scanned = 0

        for path in iter_source_files(self.repo_root, extensions=SOURCE_EXTENSIONS):
            if path.resolve() == _THIS_FILE:
                continue
            files_scanned += 1
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for line_number, line in enumerate(content.splitlines(), start=1):
                for match in MARKER_PATTERN.finditer(line):
                    marker = match.group(1)
                    by_marker[marker] += 1
                    findings.append(
                        {
                            "file": self._relative_path(path),
                            "line": line_number,
                            "marker": marker,
                            "text": line.strip()[:MAX_TEXT_LENGTH],
                        }
                    )

        total = len(findings)
        status = "ok" if total == 0 else "warning"
        summary = f"Found {total} marker{'s' if total != 1 else ''} across {files_scanned} scanned files."
        return self.make_result(
            status=status,
            summary=summary,
            findings=findings,
            metrics={"total": total, "by_marker": by_marker, "files_scanned": files_scanned},
        )

    def _relative_path(self, path: Path) -> str:
        """Return *path* relative to the configured repo root when possible."""
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the marker audit agent."""
    parser = argparse.ArgumentParser(description=MarkerAuditAgent.description)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Directory to scan (default: repo root).")
    parser.add_argument(
        "--max-allowed",
        type=int,
        default=None,
        help="Fail with exit code 1 when marker count exceeds this limit.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute results without writing status.json.")
    parser.add_argument("--json", action="store_true", help="Print the full result as JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the marker audit CLI and return a process exit code."""
    args = build_parser().parse_args(argv)
    agent = MarkerAuditAgent(repo_root=args.root)
    result = agent.run()

    if not args.dry_run:
        agent.write_status(result)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.summary)

    if args.max_allowed is not None and result.metrics["total"] > args.max_allowed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
