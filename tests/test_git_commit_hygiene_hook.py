"""Tests for .github/hooks/scripts/git_commit_hygiene.py."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

HOOK_PATH = (
    Path(__file__).resolve().parent.parent
    / ".github"
    / "hooks"
    / "scripts"
    / "git_commit_hygiene.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("git_commit_hygiene", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_main(module, payload: dict, monkeypatch, capsys, *, event: str = "PreToolUse"):
    monkeypatch.setenv("COPILOT_HOOK_EVENT", event)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    try:
        module.main()
    except SystemExit as exc:
        out = capsys.readouterr()
        return exc.code, out.out, out.err
    raise AssertionError("main() did not exit")


def test_warns_on_prompt_with_git_add_all(monkeypatch, capsys):
    module = _load_module()
    payload = {"userMessage": "please run git add . and commit"}
    code, out, err = _run_main(
        module, payload, monkeypatch, capsys, event="UserPromptSubmit"
    )
    assert code == 0
    assert "Git hygiene reminder" in out
    assert err == ""


def test_blocks_git_add_dot(monkeypatch, capsys):
    module = _load_module()
    payload = {
        "toolName": "run_in_terminal",
        "command": "git add . && git commit -m 'x'",
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 1
    assert out == ""
    assert "BLOCKED" in err
    assert "git add ." in err


def test_blocks_staging_protected_file_explicitly(monkeypatch, capsys):
    module = _load_module()
    payload = {
        "toolName": "run_in_terminal",
        "command": "git add local.settings.json",
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 1
    assert out == ""
    assert "protected" in err.lower()
    assert "local.settings.json" in err


def test_blocks_commit_when_protected_files_already_staged(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(
        module,
        "_staged_files",
        lambda: ["local.settings.json", "ai-projects/chat-cli/src/chat_providers.py"],
    )
    payload = {
        "toolName": "run_in_terminal",
        "command": "git commit -m 'update'",
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 1
    assert out == ""
    assert "currently staged" in err
    assert "local.settings.json" in err


def test_allows_commit_when_staged_files_are_safe(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(
        module,
        "_staged_files",
        lambda: ["ai-projects/chat-cli/src/chat_providers.py"],
    )
    payload = {
        "toolName": "run_in_terminal",
        "command": "git commit -m 'safe commit'",
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 0
    assert out == ""
    assert err == ""
