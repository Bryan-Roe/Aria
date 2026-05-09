"""Tests for run_automation.py status and exit behavior."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


def _load_run_automation_module():
    script_path = Path(__file__).parent.parent / "run_automation.py"
    spec = importlib.util.spec_from_file_location("run_automation", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_tests_returns_false_when_pytest_missing(monkeypatch, capsys):
    mod = _load_run_automation_module()
    runner = mod.AutomationRunner(Path(__file__).parent.parent)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout="",
            stderr="No module named pytest",
        )

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    ok = runner.run_tests()
    out = capsys.readouterr().out

    assert ok is False
    assert "pytest is not installed" in out


def test_run_returns_false_and_reports_issues(monkeypatch, capsys):
    mod = _load_run_automation_module()
    runner = mod.AutomationRunner(Path(__file__).parent.parent)

    monkeypatch.setattr(runner, "setup_signal_handlers", lambda: None)
    monkeypatch.setattr(runner, "validate_environment", lambda: True)
    monkeypatch.setattr(runner, "run_env_setup_check", lambda: True)
    monkeypatch.setattr(runner, "run_tests", lambda: False)
    monkeypatch.setattr(runner, "run_validation", lambda: True)

    ok = runner.run()
    out = capsys.readouterr().out

    assert ok is False
    assert "Automation finished with issues" in out


def test_main_returns_zero_on_success(monkeypatch):
    mod = _load_run_automation_module()

    class FakeRunner:
        def __init__(self, workspace_root):
            self.workspace_root = workspace_root

        def run(self):
            return True

    monkeypatch.setattr(mod, "AutomationRunner", FakeRunner)

    assert mod.main() == 0
