"""Unit tests for scripts/system_health_check.py."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


# ─── module loader ────────────────────────────────────────────────────────────

def _load():
    import sys
    path = Path(__file__).parent.parent / "scripts" / "system_health_check.py"
    mod_name = "system_health_check"
    # Return cached module if already loaded (avoids duplicate dataclass issues)
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Register in sys.modules BEFORE exec so @dataclass can resolve __module__
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── CheckResult model ────────────────────────────────────────────────────────

class TestCheckResult:
    def setup_method(self):
        self.mod = _load()

    def test_ok_result_icon(self):
        r = self.mod.CheckResult("test", "ok")
        assert r.icon == "✅"

    def test_warn_result_icon(self):
        r = self.mod.CheckResult("test", "warn")
        assert "⚠" in r.icon

    def test_fail_result_icon(self):
        r = self.mod.CheckResult("test", "fail")
        assert r.icon == "❌"

    def test_unknown_status_icon(self):
        r = self.mod.CheckResult("test", "unknown_status")
        assert r.icon == "❓"

    def test_to_dict_contains_name(self):
        r = self.mod.CheckResult("my_check", "ok", "all good")
        d = r.to_dict()
        assert d["name"] == "my_check"

    def test_to_dict_contains_status(self):
        r = self.mod.CheckResult("my_check", "warn", "low disk")
        d = r.to_dict()
        assert d["status"] == "warn"

    def test_to_dict_contains_detail(self):
        r = self.mod.CheckResult("my_check", "ok", "detail text")
        d = r.to_dict()
        assert d["detail"] == "detail text"

    def test_to_dict_contains_icon(self):
        r = self.mod.CheckResult("c", "ok")
        d = r.to_dict()
        assert "icon" in d

    def test_to_dict_sub_is_list(self):
        r = self.mod.CheckResult("parent", "ok")
        d = r.to_dict()
        assert isinstance(d["sub"], list)

    def test_sub_results_are_serialized(self):
        mod = self.mod
        parent = mod.CheckResult("parent", "ok", sub=[
            mod.CheckResult("child1", "ok"),
            mod.CheckResult("child2", "warn", "something"),
        ])
        d = parent.to_dict()
        assert len(d["sub"]) == 2
        assert d["sub"][0]["name"] == "child1"
        assert d["sub"][1]["status"] == "warn"


# ─── _ok / _warn / _fail helpers ─────────────────────────────────────────────

class TestHelpers:
    def setup_method(self):
        self.mod = _load()

    def test_ok_creates_ok_result(self):
        r = self.mod._ok("name", "detail")
        assert r.status == "ok"
        assert r.name == "name"
        assert r.detail == "detail"

    def test_warn_creates_warn_result(self):
        r = self.mod._warn("name")
        assert r.status == "warn"

    def test_fail_creates_fail_result(self):
        r = self.mod._fail("name", "critical error")
        assert r.status == "fail"
        assert r.detail == "critical error"

    def test_ok_default_detail_is_empty(self):
        r = self.mod._ok("name")
        assert r.detail == ""


# ─── checks_to_json ───────────────────────────────────────────────────────────

class TestChecksToJson:
    def setup_method(self):
        self.mod = _load()

    def _make_checks(self):
        mod = self.mod
        return [
            mod._ok("check_a"),
            mod._warn("check_b", "minor issue"),
            mod._fail("check_c", "critical"),
        ]

    def test_returns_dict(self):
        result = self.mod.checks_to_json(self._make_checks())
        assert isinstance(result, dict)

    def test_has_generated_at(self):
        result = self.mod.checks_to_json(self._make_checks())
        assert "generated_at" in result

    def test_has_summary(self):
        result = self.mod.checks_to_json(self._make_checks())
        assert "summary" in result

    def test_has_checks_list(self):
        result = self.mod.checks_to_json(self._make_checks())
        assert "checks" in result
        assert isinstance(result["checks"], list)

    def test_summary_total_count(self):
        result = self.mod.checks_to_json(self._make_checks())
        assert result["summary"]["total"] == 3

    def test_summary_ok_count(self):
        result = self.mod.checks_to_json(self._make_checks())
        assert result["summary"]["ok"] == 1

    def test_summary_warn_count(self):
        result = self.mod.checks_to_json(self._make_checks())
        assert result["summary"]["warn"] == 1

    def test_summary_fail_count(self):
        result = self.mod.checks_to_json(self._make_checks())
        assert result["summary"]["fail"] == 1

    def test_all_ok_flag_true(self):
        checks = [self.mod._ok("a"), self.mod._ok("b")]
        result = self.mod.checks_to_json(checks)
        assert result["summary"]["all_ok"] is True

    def test_all_ok_flag_false_with_warn(self):
        checks = [self.mod._ok("a"), self.mod._warn("b")]
        result = self.mod.checks_to_json(checks)
        assert result["summary"]["all_ok"] is False

    def test_all_ok_flag_false_with_fail(self):
        checks = [self.mod._ok("a"), self.mod._fail("b")]
        result = self.mod.checks_to_json(checks)
        assert result["summary"]["all_ok"] is False

    def test_checks_is_json_serializable(self):
        result = self.mod.checks_to_json(self._make_checks())
        serialized = json.dumps(result)
        assert isinstance(serialized, str)

    def test_empty_checks_list(self):
        result = self.mod.checks_to_json([])
        assert result["summary"]["total"] == 0
        assert result["summary"]["all_ok"] is True


# ─── run_all_checks ───────────────────────────────────────────────────────────

class TestRunAllChecks:
    def setup_method(self):
        self.mod = _load()

    def test_returns_list(self):
        results = self.mod.run_all_checks()
        assert isinstance(results, list)

    def test_all_items_are_check_results(self):
        results = self.mod.run_all_checks()
        for r in results:
            assert isinstance(r, self.mod.CheckResult)

    def test_returns_expected_check_count(self):
        results = self.mod.run_all_checks()
        # 11 checks defined in run_all_checks()
        assert len(results) == 11

    def test_all_statuses_are_valid(self):
        results = self.mod.run_all_checks()
        valid_statuses = {"ok", "warn", "fail"}
        for r in results:
            assert r.status in valid_statuses, \
                f"{r.name} has unexpected status: {r.status}"

    def test_python_check_present(self):
        results = self.mod.run_all_checks()
        names = {r.name for r in results}
        assert any("python" in n.lower() or "Python" in n for n in names)

    def test_no_check_raises_exception(self):
        # run_all_checks should not raise; all checks handle their own errors
        results = self.mod.run_all_checks()
        assert len(results) > 0

    def test_check_python_passes_in_valid_env(self):
        # In any working Python env this should not be fail
        result = self.mod.check_python()
        assert result.status in ("ok", "warn")
