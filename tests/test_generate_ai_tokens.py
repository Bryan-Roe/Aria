"""Tests for scripts/generate_ai_tokens.py.

Covers:
- Settings load/save helpers
- Token generation helpers
- Ollama probe (mocked HTTP)
- LM Studio probe (mocked HTTP, token generation)
- Azure OpenAI probe (mocked HTTP, az-cli path)
- OpenAI probe (mocked HTTP)
- Aggregate runner (write path)
- CLI exit codes
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import unittest.mock as mock
from pathlib import Path

import pytest

# Add repo root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import scripts.generate_ai_tokens as gat


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_probe(status: int, data: object, latency: float = 5.0):
    return (status, data, latency)


# ── Settings helpers ──────────────────────────────────────────────────────────

class TestLoadSettings:
    def test_returns_empty_if_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gat, "LOCAL_SETTINGS", tmp_path / "nonexistent.json")
        result = gat._load_settings()
        assert result == {"IsEncrypted": False, "Values": {}}

    def test_loads_valid_json(self, tmp_path, monkeypatch):
        f = tmp_path / "local.settings.json"
        f.write_text(json.dumps({"IsEncrypted": False, "Values": {"FOO": "bar"}}))
        monkeypatch.setattr(gat, "LOCAL_SETTINGS", f)
        result = gat._load_settings()
        assert result["Values"]["FOO"] == "bar"

    def test_returns_empty_on_invalid_json(self, tmp_path, monkeypatch, capsys):
        f = tmp_path / "local.settings.json"
        f.write_text("{not valid json")
        monkeypatch.setattr(gat, "LOCAL_SETTINGS", f)
        result = gat._load_settings()
        assert result == {"IsEncrypted": False, "Values": {}}


class TestGetSetting:
    def test_reads_from_values(self):
        settings = {"Values": {"MY_KEY": "from_settings"}}
        assert gat._get_setting(settings, "MY_KEY") == "from_settings"

    def test_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv("MY_KEY", "from_env")
        result = gat._get_setting({"Values": {}}, "MY_KEY")
        assert result == "from_env"

    def test_skips_comment_values(self):
        settings = {"Values": {"AZURE_OPENAI_API_KEY": "# set this"}}
        assert gat._get_setting(settings, "AZURE_OPENAI_API_KEY") == ""

    def test_returns_fallback_when_missing(self):
        assert gat._get_setting({}, "MISSING_KEY", "default") == "default"


class TestSaveSettings:
    def test_writes_json(self, tmp_path, monkeypatch):
        f = tmp_path / "local.settings.json"
        monkeypatch.setattr(gat, "LOCAL_SETTINGS", f)
        settings = {"IsEncrypted": False, "Values": {"X": "y"}}
        gat._save_settings(settings)
        assert json.loads(f.read_text())["Values"]["X"] == "y"


# ── Token generation helpers ──────────────────────────────────────────────────

class TestGenerateLocalToken:
    def test_starts_with_prefix(self):
        tok = gat._generate_local_token("lmstudio")
        assert tok.startswith("lmstudio-")

    def test_sufficient_entropy(self):
        tokens = {gat._generate_local_token() for _ in range(20)}
        assert len(tokens) == 20  # all unique

    def test_default_prefix(self):
        tok = gat._generate_local_token()
        assert tok.startswith("lm-")


class TestAzCliGetAccount:
    def test_returns_none_when_az_not_found(self, monkeypatch):
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError()),
        )
        assert gat._az_cli_get_account() is None

    def test_returns_none_on_nonzero_exit(self, monkeypatch):
        fake = mock.MagicMock()
        fake.returncode = 1
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
        assert gat._az_cli_get_account() is None

    def test_returns_dict_on_success(self, monkeypatch):
        fake = mock.MagicMock()
        fake.returncode = 0
        fake.stdout = json.dumps({"name": "My Sub", "user": {"name": "user@example.com"}})
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
        result = gat._az_cli_get_account()
        assert result["name"] == "My Sub"


# ── Ollama probe ──────────────────────────────────────────────────────────────

class TestProbeOllama:
    def test_ok_with_models(self, monkeypatch):
        models_data = {"models": [{"name": "llama3.2"}, {"name": "mistral"}]}
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (200, models_data, 12.0))
        env = {}
        r = gat.probe_ollama(env)
        assert r.status == "ok"
        assert r.model == "llama3.2"
        assert r.token_present is True

    def test_warn_no_models_installed(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (200, {"models": []}, 8.0))
        r = gat.probe_ollama({})
        assert r.status == "warn"
        assert any("No models" in n for n in r.notes)

    def test_fail_on_connection_refused(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (-1, None, 0.0))
        r = gat.probe_ollama({})
        assert r.status == "fail"
        assert r.error == "connection refused"

    def test_records_latency(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url",
                            lambda *a, **kw: (200, {"models": [{"name": "phi3"}]}, 42.5))
        r = gat.probe_ollama({})
        assert r.latency_ms == pytest.approx(42.5)

    def test_write_sets_model_when_missing(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url",
                            lambda *a, **kw: (200, {"models": [{"name": "llama3.2"}]}, 5.0))
        env = {}  # OLLAMA_MODEL not set
        r = gat.probe_ollama(env, write=True)
        assert "OLLAMA_MODEL" in r.env_written


# ── LM Studio probe ───────────────────────────────────────────────────────────

class TestProbeLmStudio:
    def test_ok_authenticated(self, monkeypatch):
        models_data = {"data": [{"id": "lmstudio-community/phi-3"}]}
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (200, models_data, 18.0))
        env = {"LM_API_TOKEN": "lm-supersecret", "LMSTUDIO_BASE_URL": "http://localhost:1234"}
        r = gat.probe_lmstudio(env)
        assert r.status == "ok"
        assert r.model == "lmstudio-community/phi-3"
        assert r.token_present is True

    def test_connection_refused(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (-1, None, 0.0))
        r = gat.probe_lmstudio({})
        assert r.status == "fail"
        assert r.error == "connection refused"

    def test_401_generates_token_when_rotate(self, monkeypatch):
        call_count = {"n": 0}

        def fake_probe(url, headers=None, **kw):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return (401, "Unauthorized", 5.0)
            # second call with new token → ok
            return (200, {"data": [{"id": "some-model"}]}, 10.0)

        monkeypatch.setattr(gat, "_probe_url", fake_probe)
        r = gat.probe_lmstudio({}, rotate=True, write=True)
        assert r.token_generated is True
        assert "LM_API_TOKEN" in r.env_written
        assert r.env_written["LM_API_TOKEN"].startswith("lmstudio-")

    def test_401_no_rotate_gives_warn(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (401, "Unauth", 5.0))
        r = gat.probe_lmstudio({"LM_API_TOKEN": "bad-key"})
        assert r.status == "warn"
        assert "401" in r.error

    def test_write_records_model_and_base_url(self, monkeypatch):
        data = {"data": [{"id": "phi-3-mini"}]}
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (200, data, 8.0))
        env = {"LM_API_TOKEN": "tok"}
        r = gat.probe_lmstudio(env, write=True)
        assert "LMSTUDIO_MODEL" in r.env_written
        assert r.env_written["LMSTUDIO_MODEL"] == "phi-3-mini"


# ── Azure OpenAI probe ────────────────────────────────────────────────────────

class TestProbeAzureOpenAI:
    def _base_env(self) -> dict:
        return {
            "AZURE_OPENAI_API_KEY": "test-key-abc123",
            "AZURE_OPENAI_ENDPOINT": "https://myres.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
            "AZURE_OPENAI_API_VERSION": "2024-02-01",
        }

    def test_ok_with_valid_key(self, monkeypatch):
        deployments = {"value": [{"id": "gpt-4"}, {"id": "gpt-35-turbo"}]}
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (200, deployments, 55.0))
        r = gat.probe_azure_openai(self._base_env())
        assert r.status == "ok"
        assert r.model == "gpt-4"

    def test_skipped_when_no_api_key(self, monkeypatch):
        r = gat.probe_azure_openai({"AZURE_OPENAI_ENDPOINT": "https://x.openai.azure.com"})
        assert r.status == "skipped"
        assert "no api key" in r.error

    def test_skipped_when_no_endpoint(self, monkeypatch):
        r = gat.probe_azure_openai({"AZURE_OPENAI_API_KEY": "key123"})
        assert r.status == "skipped"
        assert "no endpoint" in r.error

    def test_fail_on_401(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (401, "Unauth", 20.0))
        r = gat.probe_azure_openai(self._base_env())
        assert r.status == "fail"
        assert "401" in r.error

    def test_az_cli_token_exchange(self, monkeypatch):
        monkeypatch.setattr(gat, "_az_cli_get_account",
                            lambda: {"user": {"name": "me"}, "name": "MySub"})
        monkeypatch.setattr(gat, "_az_cli_get_token", lambda resource="": "aad-token-xyz")
        monkeypatch.setattr(gat, "_probe_url",
                            lambda *a, **kw: (200, {"value": [{"id": "gpt-4"}]}, 40.0))
        env = {
            "AZURE_OPENAI_ENDPOINT": "https://myres.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
        }
        r = gat.probe_azure_openai(env, use_az_cli=True, write=True)
        assert r.status == "ok"
        assert r.token_generated is True
        assert r.env_written.get("AZURE_OPENAI_API_KEY") == "aad-token-xyz"

    def test_az_cli_not_logged_in(self, monkeypatch):
        monkeypatch.setattr(gat, "_az_cli_get_account", lambda: None)
        r = gat.probe_azure_openai({}, use_az_cli=True)
        assert r.status == "fail"
        assert "az account show" in r.error

    def test_auto_discover_deployment(self, monkeypatch):
        deployments = {"value": [{"id": "gpt-35-turbo"}, {"id": "gpt-4"}]}
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (200, deployments, 40.0))
        env = {
            "AZURE_OPENAI_API_KEY": "key",
            "AZURE_OPENAI_ENDPOINT": "https://x.openai.azure.com",
            # No AZURE_OPENAI_DEPLOYMENT
        }
        r = gat.probe_azure_openai(env, write=True)
        assert r.status == "ok"
        assert r.env_written.get("AZURE_OPENAI_DEPLOYMENT") == "gpt-35-turbo"


# ── OpenAI probe ──────────────────────────────────────────────────────────────

class TestProbeOpenAI:
    def test_ok_with_valid_key(self, monkeypatch):
        models = {"data": [{"id": "gpt-4"}, {"id": "gpt-3.5-turbo"}]}
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (200, models, 120.0))
        r = gat.probe_openai({"OPENAI_API_KEY": "sk-abcdef1234567890"})
        assert r.status == "ok"
        assert "gpt" in r.model

    def test_skipped_when_no_key(self):
        r = gat.probe_openai({})
        assert r.status == "skipped"

    def test_fail_on_401(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (401, "Unauth", 80.0))
        r = gat.probe_openai({"OPENAI_API_KEY": "sk-badkey"})
        assert r.status == "fail"
        assert "401" in r.error

    def test_warn_on_429(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (429, "Rate", 80.0))
        r = gat.probe_openai({"OPENAI_API_KEY": "sk-ok"})
        assert r.status == "warn"

    def test_warn_on_network_failure(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (-1, None, 0.0))
        r = gat.probe_openai({"OPENAI_API_KEY": "sk-ok"})
        assert r.status == "warn"
        assert "connection" in r.error

    def test_key_format_note_on_weird_prefix(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (200, {"data": []}, 10.0))
        r = gat.probe_openai({"OPENAI_API_KEY": "notsk-something"})
        assert any("sk-" in n for n in r.notes)


# ── Aggregate runner ──────────────────────────────────────────────────────────

class TestRun:
    def test_writes_env_to_settings(self, tmp_path, monkeypatch):
        target = tmp_path / "local.settings.json"
        target.write_text(json.dumps({"IsEncrypted": False, "Values": {}}))
        monkeypatch.setattr(gat, "LOCAL_SETTINGS", target)

        # Let lmstudio return a generated token
        call_count = {"n": 0}
        def fake_probe(url, headers=None, **kw):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return (401, "Unauth", 5.0)
            return (200, {"data": [{"id": "phi-3"}]}, 8.0)

        monkeypatch.setattr(gat, "_probe_url", fake_probe)

        settings = gat._load_settings()
        results = gat.run(["lmstudio"], settings, rotate=True, write=True)
        saved = json.loads(target.read_text())
        assert "LM_API_TOKEN" in saved["Values"]
        assert saved["Values"]["LM_API_TOKEN"].startswith("lmstudio-")

    def test_skips_unknown_provider(self, monkeypatch, capsys):
        settings = {"Values": {}}
        results = gat.run(["unknownprovider"], settings)
        assert results == []

    def test_returns_one_result_per_provider(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (-1, None, 0.0))
        settings = {"Values": {}}
        results = gat.run(["ollama", "lmstudio"], settings)
        assert len(results) == 2


# ── JSON status file ──────────────────────────────────────────────────────────

class TestWriteJsonStatus:
    def test_creates_status_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gat, "STATUS_OUT", tmp_path / "status.json")
        results = [
            gat.ProviderResult(name="ollama", status="ok", latency_ms=12.0),
            gat.ProviderResult(name="openai", status="fail", error="401"),
        ]
        gat._write_json_status(results)
        data = json.loads((tmp_path / "status.json").read_text())
        assert data["healthy"] == 1
        assert data["total"] == 2
        assert data["providers"]["openai"]["error"] == "401"
        assert "last_updated" in data


# ── CLI exit codes ────────────────────────────────────────────────────────────

class TestCLIExitCodes:
    def _run(self, args: list, monkeypatch, settings=None):
        if settings is None:
            settings = {"IsEncrypted": False, "Values": {}}
        monkeypatch.setattr(gat, "_load_settings", lambda: settings)
        status_path = Path("/tmp/test_ai_token_status.json")
        monkeypatch.setattr(gat, "STATUS_OUT", status_path)
        with mock.patch("sys.argv", ["generate_ai_tokens.py"] + args):
            return gat.main()

    def test_exit_0_when_at_least_one_ok(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url",
                            lambda *a, **kw: (200, {"models": [{"name": "llama3.2"}]}, 5.0))
        rc = self._run(["--provider", "ollama"], monkeypatch)
        assert rc == 0

    def test_exit_1_when_all_fail(self, monkeypatch):
        monkeypatch.setattr(gat, "_probe_url", lambda *a, **kw: (-1, None, 0.0))
        rc = self._run(["--provider", "ollama,lmstudio"], monkeypatch)
        assert rc == 1

    def test_json_flag_produces_valid_json(self, monkeypatch, capsys):
        monkeypatch.setattr(gat, "_probe_url",
                            lambda *a, **kw: (200, {"models": [{"name": "phi3"}]}, 8.0))
        rc = self._run(["--provider", "ollama", "--json"], monkeypatch)
        out = capsys.readouterr().out
        # The JSON block starts with '{' on its own line; find and parse it
        json_lines: list[str] = []
        in_json = False
        brace_depth = 0
        for line in out.splitlines():
            stripped = line.strip()
            if not in_json and stripped.startswith("{"):
                in_json = True
            if in_json:
                json_lines.append(line)
                brace_depth += stripped.count("{") - stripped.count("}")
                if brace_depth <= 0:
                    break
        assert json_lines, "No JSON block found in stdout"
        data = json.loads("\n".join(json_lines))
        assert "providers" in data
        assert data["healthy"] >= 0
