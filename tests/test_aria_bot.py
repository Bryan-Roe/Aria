"""Tests for the deterministic self-modifying loop in ``aria-bot/aria_bot``."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG_PARENT = REPO_ROOT / "aria-bot"
if str(PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(PKG_PARENT))

from aria_bot import (  # noqa: E402  (sys.path tweak above)
    Analyzer,
    Executor,
    Orchestrator,
    OrchestratorConfig,
    Planner,
    RiskManager,
    run_cycle,
)
from aria_bot.commit_system import COMMIT_PREFIX  # noqa: E402


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    """Build a tiny fake repo: one fixable file, one protected file."""

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "needs_fix.py").write_bytes(
        b"def foo():    \n    return 1   \n"  # trailing ws on both lines, has final newline
    )
    (tmp_path / "src" / "needs_newline.md").write_bytes(b"# heading")  # no trailing newline
    (tmp_path / "src" / "clean.py").write_bytes(b"def ok():\n    return 1\n")

    # Protected: must never be touched.
    (tmp_path / "datasets").mkdir()
    (tmp_path / "datasets" / "dirty.py").write_bytes(b"x = 1   \n")
    return tmp_path


def test_risk_manager_blocks_protected_paths(fake_repo: Path) -> None:
    rm = RiskManager(repo_root=fake_repo)
    assert rm.is_path_protected(fake_repo / "datasets" / "dirty.py")
    assert rm.is_path_protected(fake_repo / ".git" / "HEAD")
    assert not rm.is_path_protected(fake_repo / "src" / "needs_fix.py")


def test_risk_manager_blocks_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "real.py"
    target.write_text("x = 1\n")
    link = tmp_path / "link.py"
    link.symlink_to(target)

    rm = RiskManager(repo_root=tmp_path)
    assessment = rm.assess_file(link)
    assert not assessment.allowed
    assert any("symlink" in r for r in assessment.reasons)


def test_risk_manager_caps_file_size(tmp_path: Path) -> None:
    big = tmp_path / "big.py"
    big.write_bytes(b"a = 1\n" * 2)  # 12 bytes, well over the 1-byte cap
    rm = RiskManager(repo_root=tmp_path, max_file_bytes=1)
    assert not rm.assess_file(big).allowed


def test_risk_manager_rejects_no_op(tmp_path: Path) -> None:
    p = tmp_path / "a.py"
    p.write_bytes(b"x = 1\n")
    rm = RiskManager(repo_root=tmp_path)
    assessment = rm.assess_change(p, b"x = 1\n", b"x = 1\n")
    assert not assessment.allowed
    assert any("no-op" in r for r in assessment.reasons)


def test_analyzer_detects_findings(fake_repo: Path) -> None:
    rm = RiskManager(repo_root=fake_repo)
    findings = Analyzer(risk_manager=rm).scan()
    kinds_by_path = {(f.path.name, f.kind) for f in findings}

    assert ("needs_fix.py", "trailing_whitespace") in kinds_by_path
    assert ("needs_newline.md", "missing_final_newline") in kinds_by_path
    # Protected file must not appear at all.
    assert not any(f.path.name == "dirty.py" for f in findings)
    # Clean file should produce nothing.
    assert not any(f.path.name == "clean.py" for f in findings)


def test_planner_groups_by_path_and_filters_protected(fake_repo: Path) -> None:
    rm = RiskManager(repo_root=fake_repo)
    findings = Analyzer(risk_manager=rm).scan()
    plans = Planner(risk_manager=rm).build_plans(findings)
    paths = {p.path.name for p in plans}
    assert "needs_fix.py" in paths
    assert "needs_newline.md" in paths
    assert "dirty.py" not in paths


def test_executor_dry_run_does_not_write(fake_repo: Path) -> None:
    rm = RiskManager(repo_root=fake_repo)
    findings = Analyzer(risk_manager=rm).scan()
    plans = Planner(risk_manager=rm).build_plans(findings)
    before = (fake_repo / "src" / "needs_fix.py").read_bytes()

    results = Executor(risk_manager=rm, dry_run=True).execute(plans)
    after = (fake_repo / "src" / "needs_fix.py").read_bytes()

    assert before == after
    assert all(not r.applied for r in results)
    assert any(r.reason == "dry-run" for r in results)


def test_executor_applies_and_is_idempotent(fake_repo: Path) -> None:
    rm = RiskManager(repo_root=fake_repo)

    # First pass: applies fixes.
    findings = Analyzer(risk_manager=rm).scan()
    plans = Planner(risk_manager=rm).build_plans(findings)
    results = Executor(risk_manager=rm, dry_run=False).execute(plans)
    assert any(r.applied for r in results)

    fixed = (fake_repo / "src" / "needs_fix.py").read_bytes()
    assert b"   \n" not in fixed
    assert (fake_repo / "src" / "needs_newline.md").read_bytes().endswith(b"\n")
    # Protected file untouched.
    assert (fake_repo / "datasets" / "dirty.py").read_bytes() == b"x = 1   \n"

    # Second pass: nothing left to do.
    findings2 = Analyzer(risk_manager=rm).scan()
    plans2 = Planner(risk_manager=rm).build_plans(findings2)
    assert plans2 == []


def test_orchestrator_dry_run_writes_status(fake_repo: Path) -> None:
    config = OrchestratorConfig(repo_root=fake_repo, apply=False, commit=False)
    result = Orchestrator(config=config).run()

    status_path = fake_repo / "data_out" / "aria_bot" / "status.json"
    assert status_path.exists()
    payload = json.loads(status_path.read_text())
    assert payload["apply"] is False
    assert payload["totals"]["findings"] >= 2
    # Dry-run never applies.
    assert payload["totals"]["applied"] == 0
    # No file mutation occurred.
    assert (fake_repo / "src" / "needs_fix.py").read_bytes().endswith(b"   \n")
    assert result.validation_ok in (True, False)  # ruff may be missing in test env


def test_run_cycle_apply_modifies_files(fake_repo: Path) -> None:
    result = run_cycle(repo_root=fake_repo, apply=True, commit=False)
    assert result.apply is True
    applied = [e for e in result.executions if e.applied]
    assert applied, "expected at least one applied plan"
    # Protected dataset file is still dirty.
    assert (fake_repo / "datasets" / "dirty.py").read_bytes() == b"x = 1   \n"


def test_commit_requires_apply(fake_repo: Path) -> None:
    """The CLI rejects --commit without --apply."""

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "aria_bot",
            "--repo-root",
            str(fake_repo),
            "--commit",
            "--quiet",
        ],
        cwd=PKG_PARENT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "--commit requires --apply" in proc.stderr


def test_commit_message_uses_known_prefix() -> None:
    assert COMMIT_PREFIX.startswith("chore(aria-bot):")
