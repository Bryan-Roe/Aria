"""Unit tests for cron-like schedule matching in master orchestrator."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import scripts.master_orchestrator as master_module


@pytest.mark.unit
def test_match_cron_field_supports_common_syntax() -> None:
    matcher = master_module.MasterOrchestrator._match_cron_field

    assert matcher("*", 10, 0, 59)
    assert matcher("*/15", 30, 0, 59)
    assert not matcher("*/15", 31, 0, 59)
    assert matcher("1,3,5", 3, 0, 59)
    assert not matcher("1,3,5", 4, 0, 59)
    assert matcher("10-20", 15, 0, 59)
    assert matcher("10-20/2", 14, 0, 59)


@pytest.mark.unit
def test_should_run_now_matches_and_dedupes(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now = datetime(2026, 3, 10, 12, 30, tzinfo=timezone.utc)

    class _FakeDateTime:
        @staticmethod
        def now(tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(master_module, "datetime", _FakeDateTime)

    orchestrator = master_module.MasterOrchestrator.__new__(master_module.MasterOrchestrator)
    orchestrator._last_schedule_run = {}

    assert orchestrator._should_run_now("wf", "30 12 * * *")
    assert not orchestrator._should_run_now("wf", "30 12 * * *")
    assert not orchestrator._should_run_now("wf", "31 12 * * *")


@pytest.mark.unit
def test_should_run_now_dom_dow_or_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    # Monday, day-of-month 9
    fixed_now = datetime(2026, 3, 9, 12, 30, tzinfo=timezone.utc)

    class _FakeDateTime:
        @staticmethod
        def now(tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(master_module, "datetime", _FakeDateTime)

    orchestrator = master_module.MasterOrchestrator.__new__(master_module.MasterOrchestrator)
    orchestrator._last_schedule_run = {}

    # dom matches, dow does not
    assert orchestrator._should_run_now("wf1", "30 12 9 * 2")
    # dom does not match, dow matches (Monday=1 in cron convention used here)
    assert orchestrator._should_run_now("wf2", "30 12 8 * 1")
    # neither dom nor dow match
    assert not orchestrator._should_run_now("wf3", "30 12 8 * 2")


@pytest.mark.unit
def test_should_run_now_rejects_invalid_or_continuous_schedule(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now = datetime(2026, 3, 10, 12, 30, tzinfo=timezone.utc)

    class _FakeDateTime:
        @staticmethod
        def now(tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(master_module, "datetime", _FakeDateTime)

    orchestrator = master_module.MasterOrchestrator.__new__(master_module.MasterOrchestrator)
    orchestrator._last_schedule_run = {}

    assert not orchestrator._should_run_now("wf", "continuous")
    assert not orchestrator._should_run_now("wf", "bad schedule")
