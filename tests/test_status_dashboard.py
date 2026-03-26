"""Unit tests for scripts/status_dashboard.py."""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ─── module loader ────────────────────────────────────────────────────────────

def _load():
    path = Path(__file__).parent.parent / "scripts" / "status_dashboard.py"
    spec = importlib.util.spec_from_file_location("status_dashboard", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── _badge ───────────────────────────────────────────────────────────────────

class TestBadge:
    def setup_method(self):
        self.mod = _load()

    def test_ok_status(self):
        assert self.mod._badge("ok") == "✅"

    def test_completed_status(self):
        assert self.mod._badge("completed") == "✅"

    def test_success_status(self):
        assert self.mod._badge("success") == "✅"

    def test_running_status(self):
        assert self.mod._badge("running") == "🟢"

    def test_failed_status(self):
        assert self.mod._badge("failed") == "❌"

    def test_error_status(self):
        assert self.mod._badge("error") == "❌"

    def test_warning_status(self):
        assert self.mod._badge("warning") == "⚠️"

    def test_unknown_status_returns_question_mark(self):
        assert self.mod._badge("something_unknown") == "❓"

    def test_case_insensitive_ok(self):
        assert self.mod._badge("OK") == "✅"

    def test_case_insensitive_failed(self):
        assert self.mod._badge("FAILED") == "❌"


# ─── _fmt_time ────────────────────────────────────────────────────────────────

class TestFmtTime:
    def setup_method(self):
        self.mod = _load()

    def test_none_returns_dash(self):
        assert self.mod._fmt_time(None) == "—"

    def test_empty_string_returns_dash(self):
        assert self.mod._fmt_time("") == "—"

    def test_recent_seconds(self):
        now = datetime.now(timezone.utc)
        iso = now.isoformat()
        result = self.mod._fmt_time(iso)
        assert "s ago" in result

    def test_minutes_ago(self):
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        iso = past.isoformat()
        result = self.mod._fmt_time(iso)
        assert "m ago" in result

    def test_hours_ago(self):
        past = datetime.now(timezone.utc) - timedelta(hours=3)
        iso = past.isoformat()
        result = self.mod._fmt_time(iso)
        assert "h ago" in result

    def test_days_ago(self):
        past = datetime.now(timezone.utc) - timedelta(days=2)
        iso = past.isoformat()
        result = self.mod._fmt_time(iso)
        assert "d ago" in result

    def test_invalid_iso_returns_truncated_string(self):
        result = self.mod._fmt_time("not-a-date")
        assert isinstance(result, str)


# ─── _load ────────────────────────────────────────────────────────────────────

class TestLoad:
    def setup_method(self):
        self.mod = _load()

    def test_missing_file_returns_empty_dict(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        result = self.mod._load("nonexistent.json")
        assert result == {}

    def test_valid_json_file_returns_dict(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        (tmp_path / "test_status.json").write_text(
            '{"total_jobs": 10, "succeeded": 8}', encoding="utf-8"
        )
        result = self.mod._load("test_status.json")
        assert result["total_jobs"] == 10
        assert result["succeeded"] == 8

    def test_invalid_json_returns_empty_dict(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        (tmp_path / "broken.json").write_text("{ not json }", encoding="utf-8")
        result = self.mod._load("broken.json")
        assert result == {}

    def test_json_array_returns_empty_dict(self, tmp_path, monkeypatch):
        # _load only accepts dicts; arrays should return {}
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        (tmp_path / "array.json").write_text("[1, 2, 3]", encoding="utf-8")
        result = self.mod._load("array.json")
        assert result == {}

    def test_nested_path_resolved(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "status.json").write_text(
            '{"status": "ok"}', encoding="utf-8"
        )
        result = self.mod._load("sub/status.json")
        assert result["status"] == "ok"


# ─── export_dashboard ─────────────────────────────────────────────────────────

class TestExportDashboard:
    def setup_method(self):
        self.mod = _load()

    def test_creates_output_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        out = tmp_path / "dashboard.json"
        self.mod.export_dashboard(str(out))
        assert out.exists()

    def test_output_is_valid_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        out = tmp_path / "dashboard.json"
        self.mod.export_dashboard(str(out))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_output_has_required_keys(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        out = tmp_path / "dashboard.json"
        self.mod.export_dashboard(str(out))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "generated_at" in data
        assert "orchestrators" in data

    def test_orchestrators_is_list(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        out = tmp_path / "dashboard.json"
        self.mod.export_dashboard(str(out))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data["orchestrators"], list)

    def test_all_known_orchestrators_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.mod, "DATA_OUT", tmp_path)
        out = tmp_path / "dashboard.json"
        self.mod.export_dashboard(str(out))
        data = json.loads(out.read_text(encoding="utf-8"))
        expected_names = {o[0] for o in self.mod.ORCHESTRATORS}
        exported_names = {o["orchestrator"] for o in data["orchestrators"]}
        assert expected_names == exported_names


# ─── _row ─────────────────────────────────────────────────────────────────────

class TestRow:
    def setup_method(self):
        self.mod = _load()

    def test_row_contains_label_and_value(self):
        result = self.mod._row("MyLabel", "MyValue")
        assert "MyLabel" in result
        assert "MyValue" in result

    def test_row_custom_width(self):
        result = self.mod._row("A", "B", width=10)
        assert "A" in result
        assert "B" in result
