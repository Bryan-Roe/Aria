"""Tests for the status freshness automation agent."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.status_freshness_agent import StatusFreshnessAgent, main  # noqa: E402


def write_status(data_dir: Path, name: str, payload: dict) -> Path:
    """Write a test status payload under *data_dir*."""
    path = data_dir / name / "status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def recent_timestamp() -> str:
    """Return a recent UTC ISO-8601 timestamp."""
    return datetime.now(timezone.utc).isoformat()


def test_fresh_status_has_no_findings(tmp_path):
    write_status(tmp_path, "fresh", {"last_updated": recent_timestamp(), "failed": 0})

    result = StatusFreshnessAgent(data_dir=tmp_path).run()

    assert result.status == "ok"
    assert result.findings == []
    assert result.metrics == {"files_scanned": 1, "stale": 0, "failed": 0, "unparseable": 0, "no_timestamp": 0}


def test_stale_status_is_warning(tmp_path):
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()
    write_status(tmp_path, "stale", {"last_updated": stale_time, "failed": 0})

    result = StatusFreshnessAgent(data_dir=tmp_path, max_age_hours=24).run()

    assert result.status == "warning"
    assert result.metrics["stale"] == 1
    assert result.findings[0]["issue"] == "stale"
    assert "100 hours old" in result.findings[0]["detail"]


def test_failed_count_is_error(tmp_path):
    write_status(tmp_path, "failed", {"last_updated": recent_timestamp(), "failed": 3})

    result = StatusFreshnessAgent(data_dir=tmp_path).run()

    assert result.status == "error"
    assert result.metrics["failed"] == 1
    assert result.findings[0]["issue"] == "failed"


def test_crashed_status_string_is_failed(tmp_path):
    write_status(tmp_path, "crashed", {"last_updated": recent_timestamp(), "status": "crashed"})

    result = StatusFreshnessAgent(data_dir=tmp_path).run()

    assert result.status == "error"
    assert result.metrics["failed"] == 1
    assert result.findings[0]["issue"] == "failed"


def test_unparseable_status_is_error(tmp_path):
    path = tmp_path / "bad" / "status.json"
    path.parent.mkdir(parents=True)
    path.write_text("{ not json", encoding="utf-8")

    result = StatusFreshnessAgent(data_dir=tmp_path).run()

    assert result.status == "error"
    assert result.metrics["unparseable"] == 1
    assert result.findings[0]["issue"] == "unparseable"


def test_status_without_timestamp_is_warning(tmp_path):
    write_status(tmp_path, "no-timestamp", {"succeeded": 2, "failed": 0})

    result = StatusFreshnessAgent(data_dir=tmp_path).run()

    assert result.status == "warning"
    assert result.metrics["no_timestamp"] == 1
    assert result.findings[0]["issue"] == "no_timestamp"


def test_trailing_z_timestamp_parses_as_fresh(tmp_path):
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    write_status(tmp_path, "zulu", {"last_updated": timestamp, "failed": 0})

    result = StatusFreshnessAgent(data_dir=tmp_path).run()

    assert result.status == "ok"
    assert result.findings == []


def test_metrics_counts_across_mixed_directory(tmp_path):
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()
    write_status(tmp_path, "fresh", {"last_updated": recent_timestamp(), "failed": 0})
    write_status(tmp_path, "stale", {"last_updated": stale_time, "failed": 0})
    write_status(tmp_path, "failed", {"last_updated": recent_timestamp(), "failed": 1})
    write_status(tmp_path, "crashed", {"last_updated": recent_timestamp(), "state": "ERROR"})
    write_status(tmp_path, "no-timestamp", {"running": 0})
    bad_path = tmp_path / "bad" / "status.json"
    bad_path.parent.mkdir(parents=True)
    bad_path.write_text("{ not json", encoding="utf-8")
    write_status(tmp_path, "agents/self", {"status": "error"})

    result = StatusFreshnessAgent(data_dir=tmp_path).run()

    assert result.status == "error"
    assert result.metrics == {"files_scanned": 6, "stale": 1, "failed": 2, "unparseable": 1, "no_timestamp": 1}
    assert {finding["issue"] for finding in result.findings} == {"stale", "failed", "unparseable", "no_timestamp"}


def test_fail_on_stale_gate_returns_one_only_with_flag_for_warning(tmp_path):
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()
    write_status(tmp_path, "stale", {"last_updated": stale_time, "failed": 0})

    assert main(["--data-dir", str(tmp_path), "--dry-run"]) == 0
    assert main(["--data-dir", str(tmp_path), "--dry-run", "--fail-on-stale"]) == 1


def test_dry_run_skips_status_write_and_normal_run_writes(tmp_path, monkeypatch):
    import scripts.agents.base as base

    monkeypatch.setattr(base, "AGENTS_DATA_DIR", tmp_path / "agents")
    data_dir = tmp_path / "data"
    write_status(data_dir, "fresh", {"last_updated": recent_timestamp(), "failed": 0})

    assert main(["--data-dir", str(data_dir), "--dry-run"]) == 0
    status_path = tmp_path / "agents" / "status-freshness" / "status.json"
    assert not status_path.exists()

    assert main(["--data-dir", str(data_dir)]) == 0
    assert status_path.exists()
    assert json.loads(status_path.read_text(encoding="utf-8"))["name"] == "status-freshness"
