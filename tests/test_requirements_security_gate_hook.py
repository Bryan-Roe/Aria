"""Tests for .github/hooks/scripts/requirements_security_gate.py.

Uses importlib + monkeypatch to keep hook behavior deterministic without depending
on the real pip-audit binary or network access.
"""

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
    / "requirements_security_gate.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("requirements_security_gate", HOOK_PATH)
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


def test_non_requirements_file_is_skipped(monkeypatch, capsys):
    module = _load_module()
    payload = {
        "toolName": "write_file",
        "filePath": "apps/aria/server.py",
        "content": "print('hi')",
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 0
    assert out == ""
    assert err == ""


def test_missing_pip_audit_prints_reminder(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "_pip_audit_available", lambda: False)
    payload = {
        "toolName": "write_file",
        "filePath": "requirements.txt",
        "content": "requests==2.32.0\n",
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 0
    assert "SECURITY REMINDER" in out
    assert "pip-audit -r requirements.txt" in out
    assert err == ""


def test_vulnerabilities_warn_by_default(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "_pip_audit_available", lambda: True)
    monkeypatch.setattr(module, "_run_audit", lambda content, filename: (True, "  • flask==0.1 → GHSA-test (fix: 3.0.0)"))
    payload = {
        "toolName": "write_file",
        "filePath": "requirements.txt",
        "content": "flask==0.1\n",
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 0
    assert "SECURITY GATE" in out
    assert "flask==0.1" in out
    assert err == ""


def test_vulnerabilities_block_when_env_enabled(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "_pip_audit_available", lambda: True)
    monkeypatch.setattr(module, "_run_audit", lambda content, filename: (True, "  • flask==0.1 → GHSA-test (fix: 3.0.0)"))
    monkeypatch.setattr(module, "_SEVERITY_BLOCK", True)
    payload = {
        "toolName": "write_file",
        "filePath": "requirements.txt",
        "content": "flask==0.1\n",
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 1
    assert out == ""
    assert "SECURITY GATE" in err


def test_posttool_reads_from_disk_when_content_missing(monkeypatch, capsys, tmp_path):
    module = _load_module()
    monkeypatch.setattr(module, "_pip_audit_available", lambda: True)
    seen = {}

    def fake_run_audit(content, filename):
        seen["content"] = content
        seen["filename"] = filename
        return False, ""

    monkeypatch.setattr(module, "_run_audit", fake_run_audit)
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.32.0\n", encoding="utf-8")
    payload = {
        "toolName": "replace_string_in_file",
        "filePath": str(req),
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys, event="PostToolUse")
    assert code == 0
    assert seen["content"] == "requests==2.32.0\n"
    assert seen["filename"] == "requirements.txt"
    assert out == ""
    assert err == ""


def test_pyproject_dependencies_are_extracted_before_audit(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "_pip_audit_available", lambda: True)
    seen = {}

    def fake_run_audit(content, filename):
        seen["content"] = content
        seen["filename"] = filename
        return False, ""

    monkeypatch.setattr(module, "_run_audit", fake_run_audit)
    payload = {
        "toolName": "write_file",
        "filePath": "pyproject.toml",
        "content": (
            "[build-system]\n"
            'requires = ["setuptools>=78.1.1", "wheel>=0.46.2"]\n\n'
            "[project]\n"
            'dependencies = ["flask>=3.1.3", "requests>=2.32.0"]\n\n'
            "[project.optional-dependencies]\n"
            'dev = ["pytest>=8.4.2"]\n'
        ),
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 0
    assert seen["filename"] == "pyproject.toml"
    assert "setuptools>=78.1.1" in seen["content"]
    assert "wheel>=0.46.2" in seen["content"]
    assert "flask>=3.1.3" in seen["content"]
    assert "requests>=2.32.0" in seen["content"]
    assert "pytest>=8.4.2" in seen["content"]
    assert out == ""
    assert err == ""


def test_malformed_pyproject_warns_but_does_not_block(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "_pip_audit_available", lambda: True)
    payload = {
        "toolName": "write_file",
        "filePath": "pyproject.toml",
        "content": "[project\ndependencies = [\"flask\"]\n",
    }
    code, out, err = _run_main(module, payload, monkeypatch, capsys)
    assert code == 0
    assert "SECURITY REMINDER" in out
    assert "Unable to parse pyproject.toml" in out
    assert err == ""
