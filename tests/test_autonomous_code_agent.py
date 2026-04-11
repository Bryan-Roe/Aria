from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import autonomous_code_agent as aca  # noqa: E402


def _configure_agent_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(aca, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(aca, "DATA_OUT", tmp_path / "data_out")
    monkeypatch.setattr(aca, "STATUS_FILE", tmp_path / "data_out" / "status.json")
    aca._LOGGER.handlers.clear()


def _make_state() -> aca.AgentState:
    return aca.AgentState(
        task_id="test-task",
        task_description="test task",
        status="implementing",
        llm_type="echo",
        files_modified=[],
        tests_run=0,
        tests_passed=0,
        tests_failed=0,
        reasoning="",
        commits=[],
        errors=[],
        started_at="now",
        updated_at="now",
    )


def test_restore_modified_files_preserves_user_content(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _configure_agent_repo(monkeypatch, tmp_path)
    target = tmp_path / "sample.py"
    target.write_text("print('user work')\n", encoding="utf-8")

    agent = aca.CodeAgent(llm_type="echo")
    agent.state = _make_state()
    monkeypatch.setattr(
        agent,
        "_llm_query",
        lambda prompt, max_tokens=aca.MAX_TASK_TOKENS: "print('agent edit')\n",
    )

    modified = agent.implement_changes("update sample", ["sample.py"])

    assert modified == ["sample.py"]
    assert target.read_text(encoding="utf-8") == "print('agent edit')\n"

    restored = agent._restore_modified_files()

    assert restored is True
    assert target.read_text(encoding="utf-8") == "print('user work')\n"


def test_commit_changes_stages_only_agent_modified_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _configure_agent_repo(monkeypatch, tmp_path)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "agent@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Agent Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    tracked = tmp_path / "tracked.py"
    unrelated = tmp_path / "notes.txt"
    tracked.write_text("print('base')\n", encoding="utf-8")
    unrelated.write_text("original\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "tracked.py", "notes.txt"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    unrelated.write_text("user local change\n", encoding="utf-8")
    tracked.write_text("print('agent change')\n", encoding="utf-8")

    agent = aca.CodeAgent(llm_type="echo")
    agent.state = _make_state()
    agent.state.files_modified = ["tracked.py"]

    committed = agent.commit_changes("agent commit", files=["tracked.py"])

    assert committed is True

    show = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    committed_files = {
        line.strip() for line in show.stdout.splitlines() if line.strip()
    }
    assert committed_files == {"tracked.py"}

    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert " M notes.txt" in status.stdout
    assert "tracked.py" not in status.stdout


def test_commit_changes_uses_agent_repo_root_instead_of_global(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "agent@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Agent Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    tracked = tmp_path / "tracked.py"
    tracked.write_text("print('base')\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "tracked.py"], cwd=tmp_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    tracked.write_text("print('agent change')\n", encoding="utf-8")

    wrong_root = tmp_path / "wrong-root"
    wrong_root.mkdir()
    monkeypatch.setattr(aca, "REPO_ROOT", wrong_root)
    monkeypatch.setattr(aca, "DATA_OUT", tmp_path / "data_out")
    monkeypatch.setattr(aca, "STATUS_FILE", tmp_path / "data_out" / "status.json")

    agent = aca.CodeAgent(llm_type="echo")
    agent.repo.repo_root = tmp_path
    agent.state = _make_state()
    agent.state.files_modified = ["tracked.py"]

    committed = agent.commit_changes("agent commit", files=["tracked.py"])

    assert committed is True

    show = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    committed_files = {
        line.strip() for line in show.stdout.splitlines() if line.strip()
    }
    assert committed_files == {"tracked.py"}


def test_run_tests_uses_agent_repo_root_instead_of_global(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    test_runner = scripts_dir / "test_runner.py"
    test_runner.write_text(
        "print('collected 1 items')\n" "print('1 passed')\n",
        encoding="utf-8",
    )

    wrong_root = tmp_path / "wrong-root"
    wrong_root.mkdir()
    monkeypatch.setattr(aca, "REPO_ROOT", wrong_root)
    monkeypatch.setattr(aca, "DATA_OUT", tmp_path / "data_out")
    monkeypatch.setattr(aca, "STATUS_FILE", tmp_path / "data_out" / "status.json")

    agent = aca.CodeAgent(llm_type="echo")
    agent.repo.repo_root = tmp_path

    results = agent.run_tests()

    assert results["success"] is True
    assert results["total"] == 1
    assert results["passed"] == 1
    assert results["failed"] == 0


def test_repository_context_tolerates_git_status_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(aca, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(aca, "GIT_STATUS_TIMEOUT_SECONDS", 0.01)

    def _run(cmd, *args, **kwargs):
        if cmd[:2] == ["git", "--version"]:
            return SimpleNamespace(stdout="git version 2.0")
        if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return SimpleNamespace(stdout="main\n")
        if cmd[:3] == ["git", "status", "--short"]:
            raise subprocess.TimeoutExpired(
                cmd=cmd, timeout=kwargs.get("timeout", 0.01)
            )
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(subprocess, "run", _run)

    repo = aca.RepositoryContext()

    assert repo.git_available is True
    assert repo.current_branch == "main"
    assert repo.uncommitted_changes == []


def test_repository_context_skips_uncommitted_scan_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(aca, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(aca, "CAPTURE_UNCOMMITTED_CHANGES", False)

    calls: list[list[str]] = []

    def _run(cmd, *args, **kwargs):
        calls.append(cmd)
        if cmd[:2] == ["git", "--version"]:
            return SimpleNamespace(stdout="git version 2.0")
        if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return SimpleNamespace(stdout="main\n")
        if cmd[:3] == ["git", "status", "--short"]:
            raise AssertionError("git status --short should be skipped by default")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(subprocess, "run", _run)

    repo = aca.RepositoryContext()

    assert repo.git_available is True
    assert repo.current_branch == "main"
    assert repo.uncommitted_changes == []
    assert ["git", "status", "--short"] not in calls


def test_execute_task_uses_forced_files_without_identify_phase(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _configure_agent_repo(monkeypatch, tmp_path)
    target = tmp_path / "existing.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    agent = aca.CodeAgent(llm_type="echo")
    captured: dict[str, object] = {}

    monkeypatch.setattr(agent, "plan_task", lambda task: "short plan")

    def _identify_files(_: str) -> list[str]:
        raise AssertionError(
            "identify_files should not be called when forced_files is provided"
        )

    monkeypatch.setattr(agent, "identify_files", _identify_files)

    def _implement_changes(task: str, files: list[str]) -> list[str]:
        captured["task"] = task
        captured["files"] = files
        agent.state.mark_file_modified(files[0])
        return files

    monkeypatch.setattr(agent, "implement_changes", _implement_changes)
    monkeypatch.setattr(
        agent,
        "run_tests",
        lambda: {"success": True, "total": 1, "passed": 1, "failed": 0},
    )
    monkeypatch.setattr(agent, "commit_changes", lambda message, files=None: True)

    state = agent.execute_task(
        "update only the requested file",
        forced_files=["existing.py", "missing.py"],
    )

    assert captured["task"] == "update only the requested file"
    assert captured["files"] == ["existing.py"]
    assert state.status == "complete"
    assert state.tests_run == 1
    assert state.tests_passed == 1
    assert state.tests_failed == 0
    assert state.files_modified == ["existing.py"]
    assert state.errors == []
