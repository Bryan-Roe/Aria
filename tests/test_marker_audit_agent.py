"""Tests for the marker audit automation agent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.marker_audit_agent import MarkerAuditAgent, main  # noqa: E402


def test_detects_each_marker_type_with_line_numbers_and_paths(tmp_path):
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir()
    source.write_text(
        "print('hello')\n"
        "# TODO: add feature\n"
        "# FIXME repair this\n"
        "# HACK temporary workaround\n"
        "# XXX investigate\n"
        "# BUG known issue\n",
        encoding="utf-8",
    )

    result = MarkerAuditAgent(repo_root=tmp_path).run()

    assert result.status == "warning"
    assert [finding["marker"] for finding in result.findings] == ["TODO", "FIXME", "HACK", "XXX", "BUG"]
    assert [finding["line"] for finding in result.findings] == [2, 3, 4, 5, 6]
    assert {finding["file"] for finding in result.findings} == {"src/app.py"}
    assert result.findings[0]["text"] == "# TODO: add feature"


def test_metrics_total_and_by_marker_counts_are_correct(tmp_path):
    source = tmp_path / "notes.md"
    source.write_text("TODO one\nTODO two\nBUG one\nplain text\n", encoding="utf-8")

    result = MarkerAuditAgent(repo_root=tmp_path).run()

    assert result.metrics["total"] == 3
    assert result.metrics["by_marker"] == {"TODO": 2, "FIXME": 0, "HACK": 0, "XXX": 0, "BUG": 1}
    assert result.metrics["files_scanned"] == 1


def test_status_is_ok_when_no_markers(tmp_path):
    (tmp_path / "clean.js").write_text("const ok = true;\n", encoding="utf-8")

    result = MarkerAuditAgent(repo_root=tmp_path).run()

    assert result.status == "ok"
    assert result.metrics["total"] == 0
    assert result.findings == []


def test_excluded_directories_are_skipped(tmp_path):
    node_modules = tmp_path / "node_modules"
    datasets = tmp_path / "datasets"
    node_modules.mkdir()
    datasets.mkdir()
    (node_modules / "package.js").write_text("TODO ignored\n", encoding="utf-8")
    (datasets / "sample.py").write_text("BUG ignored\n", encoding="utf-8")
    (tmp_path / "kept.py").write_text("# FIXME counted\n", encoding="utf-8")

    result = MarkerAuditAgent(repo_root=tmp_path).run()

    assert result.metrics["total"] == 1
    assert result.findings[0]["file"] == "kept.py"
    assert result.findings[0]["marker"] == "FIXME"


def test_max_allowed_gate_returns_nonzero_when_total_exceeds_limit(tmp_path, capsys):
    (tmp_path / "file.py").write_text("# TODO counted\n", encoding="utf-8")

    assert main(["--root", str(tmp_path), "--dry-run", "--max-allowed", "0"]) == 1
    assert main(["--root", str(tmp_path), "--dry-run", "--max-allowed", "1"]) == 0
    capsys.readouterr()


def test_dry_run_does_not_write_status_but_normal_run_does(tmp_path, monkeypatch, capsys):
    import scripts.agents.base as base

    monkeypatch.setattr(base, "AGENTS_DATA_DIR", tmp_path / "agent-status")
    scan_root = tmp_path / "scan"
    scan_root.mkdir()
    (scan_root / "file.py").write_text("# TODO counted\n", encoding="utf-8")
    status_path = tmp_path / "agent-status" / "marker-audit" / "status.json"

    assert main(["--root", str(scan_root), "--dry-run"]) == 0
    assert not status_path.exists()

    assert main(["--root", str(scan_root)]) == 0
    assert status_path.exists()
    loaded = json.loads(status_path.read_text(encoding="utf-8"))
    assert loaded["name"] == "marker-audit"
    assert loaded["metrics"]["total"] == 1
    capsys.readouterr()


def test_undecodable_file_is_skipped_without_crashing(tmp_path):
    (tmp_path / "binary.py").write_bytes(b"\xff\xfe\xff")
    (tmp_path / "clean.py").write_text("print('clean')\n", encoding="utf-8")

    result = MarkerAuditAgent(repo_root=tmp_path).run()

    assert result.status == "ok"
    assert result.metrics["total"] == 0
    assert result.findings == []


def test_json_flag_prints_full_result(tmp_path, capsys):
    (tmp_path / "file.py").write_text("# BUG counted\n", encoding="utf-8")

    assert main(["--root", str(tmp_path), "--dry-run", "--json"]) == 0

    printed = json.loads(capsys.readouterr().out)
    assert printed["name"] == "marker-audit"
    assert printed["metrics"]["total"] == 1
    assert printed["findings"][0]["marker"] == "BUG"
