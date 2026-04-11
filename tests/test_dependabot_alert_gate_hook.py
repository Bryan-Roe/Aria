"""Tests for .github/hooks/scripts/dependabot_alert_gate.py."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import time
from pathlib import Path

HOOK_PATH = (
    Path(__file__).resolve().parent.parent
    / ".github"
    / "hooks"
    / "scripts"
    / "dependabot_alert_gate.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("dependabot_alert_gate", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_main(
    module,
    payload: dict,
    monkeypatch,
    capsys,
    *,
    event: str = "SessionStart",
    skip_env: str = "",
):
    monkeypatch.setenv("COPILOT_HOOK_EVENT", event)
    monkeypatch.setenv("ARIA_SKIP_DEPENDABOT_GATE", skip_env)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    try:
        module.main()
    except SystemExit as exc:
        out = capsys.readouterr()
        return exc.code, out.out, out.err
    raise AssertionError("main() did not exit")


def _make_cache_data(
    total: int = 45,
    critical: int = 4,
    high: int = 13,
    timestamp: float | None = None,
) -> dict:
    return {
        "timestamp": timestamp if timestamp is not None else time.time(),
        "total": total,
        "critical": critical,
        "high": high,
        "audited_files": ["requirements.txt"],
        "sample_vulns": [
            {
                "id": "PYSEC-2024-001",
                "package": "somelib",
                "version": "1.2.3",
                "fix_versions": ["1.2.4"],
            }
        ],
    }


# ---------------------------------------------------------------------------
# SessionStart with fresh cache and high vuln count → inject context
# ---------------------------------------------------------------------------


class TestSessionStartInjectsContext:
    def test_injects_context_when_cache_has_critical_vulns(
        self, monkeypatch, capsys, tmp_path
    ):
        module = _load_module()
        cache_file = tmp_path / "advisory_cache.json"
        cache_file.write_text(json.dumps(_make_cache_data(critical=4, high=13)))
        monkeypatch.setattr(module, "CACHE_FILE", cache_file)
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        code, out, err = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0
        assert "Vulnerability Advisory" in out
        assert err == ""

    def test_context_mentions_critical_count(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert "CRITICAL" in out or "critical" in out.lower()

    def test_context_mentions_high_count(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert "HIGH" in out or "high" in out.lower()

    def test_context_mentions_pip_audit_command(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert "pip-audit" in out

    def test_context_mentions_override(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert "ARIA_SKIP_DEPENDABOT_GATE" in out

    def test_context_lists_sample_vuln(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert "somelib" in out or "PYSEC" in out


# ---------------------------------------------------------------------------
# SessionStart but below threshold → silent
# ---------------------------------------------------------------------------


class TestSessionStartBelowThreshold:
    def test_silent_when_zero_vulns(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(total=0, critical=0, high=0)
        )

        code, out, err = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0
        assert out == ""

    def test_silent_when_only_low_vulns(self, monkeypatch, capsys):
        """high < HIGH_THRESHOLD and critical==0 should not trigger."""
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        # HIGH_THRESHOLD is 5; 3 high vulns should not trigger
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(total=3, critical=0, high=3)
        )

        code, out, err = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0
        assert out == ""


# ---------------------------------------------------------------------------
# No cache + pip-audit not available → hint message
# ---------------------------------------------------------------------------


class TestNoCachePipAuditUnavailable:
    def test_hint_when_pip_audit_not_installed(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: False)
        monkeypatch.setattr(module, "_pip_audit_available", lambda: False)

        code, out, err = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0
        assert "pip-audit" in out
        assert "install" in out.lower() or "pip install" in out


# ---------------------------------------------------------------------------
# No cache + pip-audit available → run audit and cache result
# ---------------------------------------------------------------------------


class TestNoCachePipAuditAvailable:
    def test_runs_audit_and_caches_when_no_cache(self, monkeypatch, capsys, tmp_path):
        module = _load_module()
        audit_result = _make_cache_data(critical=2, high=10)
        cache_write_calls = []

        monkeypatch.setattr(module, "_cache_valid", lambda: False)
        monkeypatch.setattr(module, "_pip_audit_available", lambda: True)
        monkeypatch.setattr(module, "_run_audit", lambda: audit_result)
        monkeypatch.setattr(
            module, "_write_cache", lambda d: cache_write_calls.append(d)
        )
        monkeypatch.setattr(module, "_read_cache", lambda: audit_result)

        code, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0
        assert len(cache_write_calls) == 1
        assert "Vulnerability Advisory" in out

    def test_uses_audit_result_for_context(self, monkeypatch, capsys):
        module = _load_module()
        audit_result = _make_cache_data(critical=1, high=6)

        monkeypatch.setattr(module, "_cache_valid", lambda: False)
        monkeypatch.setattr(module, "_pip_audit_available", lambda: True)
        monkeypatch.setattr(module, "_run_audit", lambda: audit_result)
        monkeypatch.setattr(module, "_write_cache", lambda d: None)

        code, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0
        assert "Vulnerability Advisory" in out


# ---------------------------------------------------------------------------
# Environment override
# ---------------------------------------------------------------------------


class TestEnvOverride:
    def test_skip_env_suppresses_everything(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=20)
        )

        code, out, err = _run_main(module, {}, monkeypatch, capsys, skip_env="1")
        assert code == 0
        assert out == ""

    def test_skip_env_zero_does_not_suppress(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=20)
        )

        code, out, err = _run_main(module, {}, monkeypatch, capsys, skip_env="0")
        assert code == 0
        assert "Vulnerability Advisory" in out


# ---------------------------------------------------------------------------
# Non-SessionStart events → silent
# ---------------------------------------------------------------------------


class TestNonSessionStartEvents:
    def test_silent_on_pre_tool_use(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        code, out, err = _run_main(module, {}, monkeypatch, capsys, event="PreToolUse")
        assert code == 0
        assert out == ""

    def test_silent_on_stop(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        code, out, err = _run_main(module, {}, monkeypatch, capsys, event="Stop")
        assert code == 0
        assert out == ""

    def test_silent_on_user_prompt_submit(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        code, out, err = _run_main(
            module, {}, monkeypatch, capsys, event="UserPromptSubmit"
        )
        assert code == 0
        assert out == ""


class TestEventNameResolution:
    def test_uses_hook_event_name_env_when_copilot_env_missing(
        self, monkeypatch, capsys
    ):
        module = _load_module()
        monkeypatch.delenv("COPILOT_HOOK_EVENT", raising=False)
        monkeypatch.setenv("hook_event_name", "SessionStart")
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )
        monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))

        try:
            module.main()
        except SystemExit as exc:
            out = capsys.readouterr().out
            assert exc.code == 0
            assert "Vulnerability Advisory" in out

    def test_uses_payload_event_when_env_is_missing(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.delenv("COPILOT_HOOK_EVENT", raising=False)
        monkeypatch.delenv("hook_event_name", raising=False)
        monkeypatch.delenv("HOOK_EVENT_NAME", raising=False)
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=4, high=13)
        )

        code, out, _ = _run_main(
            module,
            {"event": "SessionStart"},
            monkeypatch,
            capsys,
            event="",
        )
        assert code == 0
        assert "Vulnerability Advisory" in out


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_stdin_exits_cleanly(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setenv("COPILOT_HOOK_EVENT", "SessionStart")
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(total=0, critical=0, high=0)
        )
        monkeypatch.setattr(sys, "stdin", io.StringIO(""))
        try:
            module.main()
        except SystemExit as exc:
            assert exc.code == 0

    def test_malformed_json_exits_cleanly(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setenv("COPILOT_HOOK_EVENT", "SessionStart")
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(total=0, critical=0, high=0)
        )
        monkeypatch.setattr(sys, "stdin", io.StringIO("{bad json}"))
        try:
            module.main()
        except SystemExit as exc:
            assert exc.code == 0

    def test_always_exits_zero(self, monkeypatch, capsys):
        """This hook must never block — exit 0 always."""
        module = _load_module()
        monkeypatch.setattr(module, "_cache_valid", lambda: True)
        monkeypatch.setattr(
            module, "_read_cache", lambda: _make_cache_data(critical=99, high=99)
        )

        code, _, _ = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0


# ---------------------------------------------------------------------------
# Helper unit tests
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_format_context_with_critical(self):
        module = _load_module()
        data = _make_cache_data(total=10, critical=2, high=8)
        text = module._format_context(data)
        assert "CRITICAL" in text
        assert "HIGH" in text
        assert "pip-audit" in text
        assert "ARIA_SKIP_DEPENDABOT_GATE" in text

    def test_format_context_without_critical(self):
        module = _load_module()
        data = _make_cache_data(total=8, critical=0, high=8)
        text = module._format_context(data)
        assert "CRITICAL" not in text
        assert "HIGH" in text

    def test_cache_valid_false_for_old_file(self, tmp_path, monkeypatch):
        module = _load_module()
        cache_file = tmp_path / "old_cache.json"
        cache_file.write_text("{}")
        # Fake an old mtime
        old_time = time.time() - (10 * 3600)  # 10 hours old
        import os

        os.utime(cache_file, (old_time, old_time))
        monkeypatch.setattr(module, "CACHE_FILE", cache_file)
        assert not module._cache_valid()

    def test_cache_valid_true_for_fresh_file(self, tmp_path, monkeypatch):
        module = _load_module()
        cache_file = tmp_path / "fresh_cache.json"
        cache_file.write_text("{}")
        monkeypatch.setattr(module, "CACHE_FILE", cache_file)
        assert module._cache_valid()
