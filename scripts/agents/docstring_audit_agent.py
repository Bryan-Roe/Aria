"""Audit Python source files for module, class, and function docstrings."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT_FALLBACK = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_FALLBACK) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_FALLBACK))

from scripts.agents.base import (  # noqa: E402
    REPO_ROOT,
    AgentResult,
    AutomationAgent,
    iter_source_files,
    register,
)

DEFAULT_PATHS = ["shared", "scripts/agents"]
PYTHON_EXTENSIONS = {"py"}


@dataclass(frozen=True)
class DocumentableNode:
    """A Python AST node that can carry a docstring."""

    node_type: str
    name: str
    line: int
    has_docstring: bool
    is_public: bool


@register
class DocstringAuditAgent(AutomationAgent):
    """Compute docstring coverage for Python modules, classes, and functions."""

    name = "docstring-audit"
    description = "Computes Python docstring coverage for modules, classes, and functions."

    def __init__(
        self,
        repo_root: Path | str | None = None,
        paths: list[str] | None = None,
        min_coverage: float = 0.0,
    ) -> None:
        """Initialize the audit agent with repo-relative paths and a coverage gate."""
        super().__init__(repo_root=Path(repo_root) if repo_root is not None else None)
        self.paths = paths if paths is not None else list(DEFAULT_PATHS)
        self.min_coverage = min_coverage

    def run(self) -> AgentResult:
        """Execute the docstring audit and return a structured result."""
        findings: list[dict] = []
        files_scanned = 0
        documentable = 0
        documented = 0

        for path in self._target_files():
            files_scanned += 1
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(path))
            except (OSError, SyntaxError, UnicodeDecodeError) as exc:
                findings.append(self._parse_failed_finding(path, exc))
                continue

            for item in self._documentable_nodes(tree):
                documentable += 1
                if item.has_docstring:
                    documented += 1
                elif item.is_public:
                    findings.append(
                        {
                            "file": self._relative_path(path),
                            "type": item.node_type,
                            "name": item.name,
                            "line": item.line,
                            "reason": "missing_docstring",
                        }
                    )

        coverage_pct = 100.0 if documentable == 0 else round(documented / documentable * 100, 1)
        missing_public = sum(1 for finding in findings if finding.get("reason") == "missing_docstring")
        parse_failed = any(finding.get("reason") == "parse_failed" for finding in findings)
        status = "error" if parse_failed else "warning" if coverage_pct < 100.0 or missing_public else "ok"
        summary = (
            f"Docstring coverage {coverage_pct:.1f}% "
            f"({documented}/{documentable}); {missing_public} public missing."
        )
        return self.make_result(
            status=status,
            summary=summary,
            findings=findings,
            metrics={
                "files_scanned": files_scanned,
                "documentable": documentable,
                "documented": documented,
                "coverage_pct": coverage_pct,
                "missing_public": missing_public,
            },
        )

    def _target_files(self) -> list[Path]:
        """Return deterministic Python files selected by the configured paths."""
        files: set[Path] = set()
        for raw_path in self.paths:
            target = self.repo_root / raw_path
            if target.is_dir():
                files.update(iter_source_files(target, extensions=PYTHON_EXTENSIONS))
            elif target.is_file() and target.suffix.lower() == ".py":
                files.add(target)
        return sorted(files)

    def _documentable_nodes(self, tree: ast.Module) -> list[DocumentableNode]:
        """Return the module and all documentable definitions in *tree*."""
        nodes = [
            DocumentableNode(
                node_type="module",
                name="<module>",
                line=1,
                has_docstring=ast.get_docstring(tree) is not None,
                is_public=True,
            )
        ]
        nodes.extend(self._definition_nodes(tree.body, parents=[]))
        return nodes

    def _definition_nodes(
        self,
        body: list[ast.stmt],
        parents: list[str],
    ) -> list[DocumentableNode]:
        """Return documentable class and function definitions nested in *body*."""
        nodes: list[DocumentableNode] = []
        for node in body:
            if isinstance(node, ast.ClassDef):
                nodes.append(self._node_record(node, "class", parents))
                nodes.extend(self._definition_nodes(node.body, [*parents, node.name]))
            elif isinstance(node, ast.AsyncFunctionDef):
                nodes.append(self._node_record(node, "async_function", parents))
                nodes.extend(self._definition_nodes(node.body, [*parents, node.name]))
            elif isinstance(node, ast.FunctionDef):
                nodes.append(self._node_record(node, "function", parents))
                nodes.extend(self._definition_nodes(node.body, [*parents, node.name]))
        return nodes

    def _node_record(
        self,
        node: ast.ClassDef | ast.AsyncFunctionDef | ast.FunctionDef,
        node_type: str,
        parents: list[str],
    ) -> DocumentableNode:
        """Build a documentable node record for one definition."""
        qualified_name = ".".join([*parents, node.name]) if parents else node.name
        return DocumentableNode(
            node_type=node_type,
            name=qualified_name,
            line=node.lineno,
            has_docstring=ast.get_docstring(node) is not None,
            is_public=not node.name.startswith("_"),
        )

    def _parse_failed_finding(self, path: Path, exc: Exception) -> dict:
        """Return a structured finding for an unreadable or unparseable file."""
        return {
            "file": self._relative_path(path),
            "type": "file",
            "name": "<parse>",
            "line": getattr(exc, "lineno", 1) or 1,
            "reason": "parse_failed",
            "message": str(exc),
        }

    def _relative_path(self, path: Path) -> str:
        """Return *path* relative to the configured repo root when possible."""
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the docstring audit agent."""
    parser = argparse.ArgumentParser(description=DocstringAuditAgent.description)
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help="Repo-relative file or directory to audit; repeat to include multiple paths.",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=0.0,
        help="Fail with exit code 1 when coverage is below this percentage.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute results without writing status.json.")
    parser.add_argument("--json", action="store_true", help="Print the full result as JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the docstring audit CLI and return a process exit code."""
    args = build_parser().parse_args(argv)
    agent = DocstringAuditAgent(repo_root=REPO_ROOT, paths=args.paths, min_coverage=args.min_coverage)
    result = agent.run()

    if not args.dry_run:
        agent.write_status(result)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(
            f"{result.summary} Coverage: {result.metrics['coverage_pct']:.1f}%; "
            f"missing public: {result.metrics['missing_public']}."
        )

    return 1 if result.metrics["coverage_pct"] < agent.min_coverage else 0


if __name__ == "__main__":
    raise SystemExit(main())
