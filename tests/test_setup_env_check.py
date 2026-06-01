"""Tests for scripts/setup_env_check.py token health and path behavior."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_setup_env_check_module():
    script_path = Path(__file__).parent.parent / "scripts" / "setup_env_check.py"
    spec = importlib.util.spec_from_file_location("setup_env_check", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_ai_token_health_missing_file(tmp_path, monkeypatch, capsys):
    mod = _load_setup_env_check_module()

    fake_script_path = tmp_path / "scripts" / "setup_env_check.py"
    fake_script_path.parent.mkdir(parents=True)
    fake_script_path.write_text("# fake")

    monkeypatch.setattr(mod, "__file__", str(fake_script_path))

    ok = mod.check_ai_token_health()
    out = capsys.readouterr().out

    assert ok is True
    assert "No token health status found" in out
    assert "generate_ai_tokens.py" in out


def test_check_ai_token_health_valid_status(tmp_path, monkeypatch, capsys):
    mod = _load_setup_env_check_module()

    root = tmp_path
    (root / "scripts").mkdir(parents=True)
    fake_script_path = root / "scripts" / "setup_env_check.py"
    fake_script_path.write_text("# fake")
    (root / "data_out").mkdir(parents=True)
    (root / "data_out" / "ai_token_status.json").write_text(
        json.dumps(
            {
                "last_updated": "2026-03-29T09:00:00Z",
                "healthy": 2,
                "total": 4,
                "providers": {
                    "ollama": {"status": "ok", "model": "mistral:latest", "error": ""},
                    "lmstudio": {
                        "status": "warn",
                        "model": "",
                        "error": "401 — token required",
                    },
                },
            }
        )
    )

    monkeypatch.setattr(mod, "__file__", str(fake_script_path))

    ok = mod.check_ai_token_health()
    out = capsys.readouterr().out

    assert ok is True
    assert "Token health: 2/4 providers healthy" in out
    assert "Last token check: 2026-03-29T09:00:00Z" in out
    assert "ollama: ok" in out
    assert "lmstudio: warn" in out


def test_check_ai_token_health_invalid_json(tmp_path, monkeypatch, capsys):
    mod = _load_setup_env_check_module()

    root = tmp_path
    (root / "scripts").mkdir(parents=True)
    fake_script_path = root / "scripts" / "setup_env_check.py"
    fake_script_path.write_text("# fake")
    (root / "data_out").mkdir(parents=True)
    (root / "data_out" / "ai_token_status.json").write_text("{not valid json")

    monkeypatch.setattr(mod, "__file__", str(fake_script_path))

    ok = mod.check_ai_token_health()
    out = capsys.readouterr().out

    assert ok is True
    assert "invalid JSON" in out


def test_check_ai_token_health_no_healthy_providers(tmp_path, monkeypatch, capsys):
    mod = _load_setup_env_check_module()

    root = tmp_path
    (root / "scripts").mkdir(parents=True)
    fake_script_path = root / "scripts" / "setup_env_check.py"
    fake_script_path.write_text("# fake")
    (root / "data_out").mkdir(parents=True)
    (root / "data_out" / "ai_token_status.json").write_text(
        json.dumps(
            {
                "last_updated": "2026-03-29T09:00:00Z",
                "healthy": 0,
                "total": 4,
                "providers": {"openai": {"status": "fail", "model": "", "error": "401"}},
            }
        )
    )

    monkeypatch.setattr(mod, "__file__", str(fake_script_path))

    ok = mod.check_ai_token_health()
    out = capsys.readouterr().out

    assert ok is True
    assert "no healthy providers" in out
    assert "openai: fail" in out


def test_check_test_suite_uses_repo_root_parent_parent(tmp_path, monkeypatch, capsys):
    mod = _load_setup_env_check_module()

    root = tmp_path
    (root / "scripts").mkdir(parents=True)
    fake_script_path = root / "scripts" / "setup_env_check.py"
    fake_script_path.write_text("# fake")

    (root / "pytest.ini").write_text("[pytest]\n")
    tests_dir = root / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_sample.py").write_text("def test_ok():\n    assert True\n")

    monkeypatch.setattr(mod, "__file__", str(fake_script_path))

    ok = mod.check_test_suite()
    out = capsys.readouterr().out

    assert ok is True
    assert "pytest.ini configured" in out
    assert "Test suite directory exists" in out
