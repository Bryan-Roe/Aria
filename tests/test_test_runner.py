from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

import scripts.test_runner as test_runner


def test_parse_pytest_summary_handles_extra_statuses() -> None:
    output = "=== 12 passed, 2 failed, 3 errors, 4 skipped, 5 warnings, 6 deselected in 0.12s ==="

    summary = test_runner._parse_pytest_summary(output)

    assert summary == {"passed": 12, "failed": 2, "errors": 3, "skipped": 4}


def test_parse_pytest_summary_returns_zeroes_without_match() -> None:
    assert test_runner._parse_pytest_summary("no pytest summary here") == {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
    }


def test_parse_pytest_summary_ignores_non_summary_dividers() -> None:
    output = "\n".join(
        [
            "============================================================",
            "  Running suite: unit",
            "============================================================",
            "============================= test session starts ==============================",
            "collected 2404 items / 18 deselected / 2 skipped / 2386 selected",
            "=============== 2344 passed, 44 skipped, 18 deselected in 51.21s ===============",
        ]
    )

    summary = test_runner._parse_pytest_summary(output)

    assert summary == {"passed": 2344, "failed": 0, "errors": 0, "skipped": 44}


def test_run_suite_builds_pytest_command_and_parses_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monotonic_values = iter([10.0, 13.75])

    def fake_run(cmd: list[str], capture_output: bool, text: bool, cwd: str):
        captured["cmd"] = cmd
        captured["capture_output"] = capture_output
        captured["text"] = text
        captured["cwd"] = cwd
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout="=== 7 passed, 1 skipped, 2 deselected in 0.10s ===",
            stderr="",
        )

    monkeypatch.setattr(test_runner.subprocess, "run", fake_run)
    monkeypatch.setattr(test_runner.time, "monotonic", lambda: next(monotonic_values))

    summary, stdout, stderr = test_runner.run_suite("chat", coverage=True, verbose=2)

    assert captured["cmd"] == [
        sys.executable,
        "-m",
        "pytest",
        str(test_runner.TESTS_DIR),
        "-k",
        "provider or chat or lmstudio",
        "--cov=shared",
        "--cov=scripts",
        "--cov-report=term-missing",
        "-v",
        "--tb=short",
        "--no-header",
    ]
    assert captured["capture_output"] is True
    assert captured["text"] is True
    assert captured["cwd"] == str(test_runner.REPO_ROOT)
    assert stdout == "=== 7 passed, 1 skipped, 2 deselected in 0.10s ==="
    assert stderr == ""
    assert summary == {
        "passed": 7,
        "failed": 0,
        "errors": 0,
        "skipped": 1,
        "suite": "chat",
        "returncode": 0,
        "duration_s": 3.75,
        "success": True,
    }


def test_write_report_persists_json_and_markdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 1, 2, 3, 4, 5, tzinfo=tz or timezone.utc)

    monkeypatch.setattr(test_runner, "DATA_OUT", tmp_path / "data_out")
    monkeypatch.setattr(test_runner, "datetime", FixedDateTime)

    report_path = test_runner.write_report(
        [
            {
                "suite": "unit",
                "passed": 5,
                "failed": 0,
                "errors": 0,
                "skipped": 1,
                "duration_s": 1.5,
                "success": True,
            }
        ]
    )

    assert report_path == tmp_path / "data_out" / "test_runner" / "latest_results.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["timestamp"] == "20260102T030405Z"
    assert payload["overall_success"] is True
    assert payload["suites"][0]["suite"] == "unit"

    markdown = report_path.with_suffix(".md").read_text(encoding="utf-8")
    assert "# Test Runner Results — 20260102T030405Z" in markdown
    assert "| ✅ | **unit** | passed=5 failed=0 errors=0 skipped=1 | 1.5s |" in markdown


def test_run_selected_reports_failures_and_returns_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runs = iter(
        [
            (
                {
                    "suite": "unit",
                    "passed": 2,
                    "failed": 0,
                    "errors": 0,
                    "skipped": 0,
                    "duration_s": 0.5,
                    "success": True,
                },
                "unit stdout",
                "",
            ),
            (
                {
                    "suite": "chat",
                    "passed": 1,
                    "failed": 1,
                    "errors": 0,
                    "skipped": 0,
                    "duration_s": 0.75,
                    "success": False,
                },
                "",
                "chat stderr",
            ),
        ]
    )

    monkeypatch.setattr(test_runner, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(test_runner, "run_suite", lambda name, coverage, verbose: next(runs))
    monkeypatch.setattr(test_runner, "write_report", lambda results: tmp_path / "data_out" / "latest_results.json")

    success = test_runner._run_selected(["unit", "chat"], coverage=False, verbose=1)

    captured = capsys.readouterr()
    assert success is False
    assert "Running suite: unit" in captured.out
    assert "unit stdout" in captured.out
    assert "❌ chat: passed=1 failed=1 errors=0 skipped=0" in captured.out
    assert "Some suites failed" in captured.out
    assert "chat stderr" in captured.err


def test_main_lists_suites_without_running(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"listed": False}

    monkeypatch.setattr(sys, "argv", ["test_runner.py", "--list-suites"])
    monkeypatch.setattr(test_runner, "list_suites", lambda: called.__setitem__("listed", True))
    monkeypatch.setattr(
        test_runner,
        "_run_selected",
        lambda suites, coverage, verbose: pytest.fail("should not run suites"),
    )

    test_runner.main()

    assert called["listed"] is True


def test_main_defaults_to_unit_and_exits_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(sys, "argv", ["test_runner.py"])
    monkeypatch.setattr(
        test_runner,
        "_run_selected",
        lambda suites, coverage, verbose: captured.update({"suites": suites, "coverage": coverage, "verbose": verbose})
        or True,
    )

    with pytest.raises(SystemExit) as excinfo:
        test_runner.main()

    assert excinfo.value.code == 0
    assert captured == {"suites": ["unit"], "coverage": False, "verbose": 1}


def test_main_watch_mode_handles_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["test_runner.py", "--watch", "--chat"])
    monkeypatch.setattr(
        test_runner,
        "_watch_loop",
        lambda suites, coverage, verbose: (_ for _ in ()).throw(KeyboardInterrupt),
    )
    monkeypatch.setattr(
        test_runner,
        "_run_selected",
        lambda suites, coverage, verbose: pytest.fail("watch mode should return early"),
    )

    test_runner.main()

    assert "Watch mode stopped." in capsys.readouterr().out
