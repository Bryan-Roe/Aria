"""Tests for the docstring audit automation agent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.docstring_audit_agent import DocstringAuditAgent, main  # noqa: E402


def write_module(path: Path, source: str) -> Path:
    """Write a Python module under *path* and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def test_fully_documented_module_reports_ok(tmp_path):
    """A fully documented module should report 100 percent coverage."""
    write_module(
        tmp_path / "pkg" / "documented.py",
        '\"\"\"Module docs.\"\"\"\n\n'
        'def documented_function():\n    \"\"\"Function docs.\"\"\"\n    return 1\n\n'
        'class DocumentedClass:\n    \"\"\"Class docs.\"\"\"\n',
    )

    result = DocstringAuditAgent(repo_root=tmp_path, paths=["pkg"]).run()

    assert result.status == "ok"
    assert result.metrics["coverage_pct"] == 100.0
    assert result.findings == []


def test_missing_public_function_docstring_reports_warning(tmp_path):
    """A missing public function docstring should produce a warning finding."""
    write_module(
        tmp_path / "pkg" / "missing.py",
        '\"\"\"Module docs.\"\"\"\n\n'
        'def missing_function():\n    return 1\n',
    )

    result = DocstringAuditAgent(repo_root=tmp_path, paths=["pkg"]).run()

    assert result.status == "warning"
    assert result.metrics["coverage_pct"] < 100.0
    assert result.metrics["missing_public"] == 1
    assert result.findings == [
        {
            "file": "pkg/missing.py",
            "type": "function",
            "name": "missing_function",
            "line": 3,
            "reason": "missing_docstring",
        }
    ]


def test_private_missing_docstring_counts_without_public_finding(tmp_path):
    """Private definitions should count in totals without producing findings."""
    write_module(
        tmp_path / "pkg" / "private.py",
        '\"\"\"Module docs.\"\"\"\n\n'
        'def _private_function():\n    return 1\n',
    )

    result = DocstringAuditAgent(repo_root=tmp_path, paths=["pkg"]).run()

    assert result.status == "warning"
    assert result.metrics["documentable"] == 2
    assert result.metrics["documented"] == 1
    assert result.metrics["missing_public"] == 0
    assert result.findings == []


def test_syntax_error_reports_parse_failed_and_error_status(tmp_path):
    """Syntax errors should be reported and force an error status."""
    write_module(tmp_path / "pkg" / "broken.py", "def broken(:\n")

    result = DocstringAuditAgent(repo_root=tmp_path, paths=["pkg"]).run()

    assert result.status == "error"
    assert result.findings[0]["file"] == "pkg/broken.py"
    assert result.findings[0]["reason"] == "parse_failed"


def test_no_files_reports_full_coverage_without_divide_by_zero(tmp_path):
    """An empty path set should report healthy full coverage."""
    result = DocstringAuditAgent(repo_root=tmp_path, paths=[]).run()

    assert result.status == "ok"
    assert result.metrics["files_scanned"] == 0
    assert result.metrics["documentable"] == 0
    assert result.metrics["coverage_pct"] == 100.0


def test_min_coverage_gate_returns_failure_below_threshold(tmp_path, monkeypatch):
    """The CLI gate should fail only when coverage is below the threshold."""
    write_module(tmp_path / "pkg" / "missing.py", "def missing_function():\n    return 1\n")
    monkeypatch.setattr("scripts.agents.docstring_audit_agent.REPO_ROOT", tmp_path)

    assert main(["--dry-run", "--path", "pkg", "--min-coverage", "100"]) == 1
    assert main(["--dry-run", "--path", "pkg", "--min-coverage", "0"]) == 0


def test_dry_run_does_not_write_status_json(tmp_path, monkeypatch):
    """Dry-run mode should compute results without persisting status JSON."""
    import scripts.agents.base as base

    write_module(tmp_path / "pkg" / "documented.py", '\"\"\"Module docs.\"\"\"\n')
    status_root = tmp_path / "agents-data"
    monkeypatch.setattr(base, "AGENTS_DATA_DIR", status_root)
    monkeypatch.setattr("scripts.agents.docstring_audit_agent.REPO_ROOT", tmp_path)

    assert main(["--dry-run", "--path", "pkg"]) == 0
    assert not (status_root / "docstring-audit" / "status.json").exists()


def test_mixed_file_metrics_are_correct(tmp_path):
    """Mixed documented and undocumented nodes should produce exact metrics."""
    write_module(
        tmp_path / "pkg" / "mixed.py",
        '\"\"\"Module docs.\"\"\"\n\n'
        'class Documented:\n    \"\"\"Class docs.\"\"\"\n\n'
        '    def method(self):\n        return 1\n\n'
        'async def async_missing():\n    return 2\n\n'
        'def documented_function():\n    \"\"\"Function docs.\"\"\"\n    return 3\n',
    )

    result = DocstringAuditAgent(repo_root=tmp_path, paths=["pkg"]).run()

    assert result.metrics["documentable"] == 5
    assert result.metrics["documented"] == 3
    assert result.metrics["coverage_pct"] == 60.0
    assert result.metrics["missing_public"] == 2
    assert {finding["name"] for finding in result.findings} == {"Documented.method", "async_missing"}


def test_json_output_prints_full_result(tmp_path, monkeypatch, capsys):
    """JSON mode should print the full result dictionary."""
    write_module(tmp_path / "pkg" / "documented.py", '\"\"\"Module docs.\"\"\"\n')
    monkeypatch.setattr("scripts.agents.docstring_audit_agent.REPO_ROOT", tmp_path)

    assert main(["--dry-run", "--json", "--path", "pkg"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert data["name"] == "docstring-audit"
    assert data["metrics"]["coverage_pct"] == 100.0
