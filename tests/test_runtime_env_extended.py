"""Extended tests for shared/runtime_env.py.

Covers paths not exercised by test_runtime_env.py:
- _candidate_venv_python_paths ordering and content
- locate_project_python fallback when no venv exists (returns first candidate)
- probe_python_packages with non-zero exit code
- probe_python_packages with timeout
- probe_python_packages with missing Python executable
- build_venv_info with custom module list
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.runtime_env import (
    _candidate_venv_python_paths,
    build_venv_info,
    locate_project_python,
    probe_python_packages,
)

# ---------------------------------------------------------------------------
# _candidate_venv_python_paths
# ---------------------------------------------------------------------------


class TestCandidateVenvPythonPaths:
    def test_returns_list_of_paths(self, tmp_path):
        result = _candidate_venv_python_paths(tmp_path, [".venv"])
        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)

    def test_includes_dot_venv_prefix(self, tmp_path):
        result = _candidate_venv_python_paths(tmp_path, [".venv"])
        assert any(".venv" in str(p) for p in result)

    def test_includes_venv_prefix(self, tmp_path):
        result = _candidate_venv_python_paths(tmp_path, ["venv"])
        assert any("venv" in str(p) for p in result)

    def test_both_venv_names_present(self, tmp_path):
        result = _candidate_venv_python_paths(tmp_path, [".venv", "venv"])
        names = {str(p) for p in result}
        has_dot_venv = any(".venv" in n for n in names)
        has_venv = any("/venv/" in n or "\\venv\\" in n for n in names)
        assert has_dot_venv
        assert has_venv

    def test_candidates_rooted_at_repo_root(self, tmp_path):
        result = _candidate_venv_python_paths(tmp_path, [".venv"])
        assert all(str(p).startswith(str(tmp_path)) for p in result)

    def test_python_in_all_candidate_names(self, tmp_path):
        result = _candidate_venv_python_paths(tmp_path, [".venv"])
        assert all("python" in p.name for p in result)


# ---------------------------------------------------------------------------
# locate_project_python — fallback when no venv exists
# ---------------------------------------------------------------------------


class TestLocateProjectPythonExtended:
    def test_fallback_path_is_path_object(self, tmp_path):
        # No venv exists; should return the first candidate without raising
        result = locate_project_python(tmp_path)
        assert isinstance(result, Path)

    def test_fallback_path_contains_python(self, tmp_path):
        result = locate_project_python(tmp_path)
        assert "python" in result.name.lower()

    def test_prefers_dot_venv_over_venv(self, tmp_path):
        # Create .venv/bin/python and venv/bin/python; .venv should win
        dot_venv_python = tmp_path / ".venv" / "bin" / "python"
        venv_python = tmp_path / "venv" / "bin" / "python"
        dot_venv_python.parent.mkdir(parents=True)
        venv_python.parent.mkdir(parents=True)
        dot_venv_python.write_text("#!/usr/bin/env python3\n")
        venv_python.write_text("#!/usr/bin/env python3\n")

        result = locate_project_python(tmp_path)
        assert ".venv" in str(result)

    def test_custom_venv_names_respected(self, tmp_path):
        custom_python = tmp_path / "myenv" / "bin" / "python"
        custom_python.parent.mkdir(parents=True)
        custom_python.write_text("#!/usr/bin/env python3\n")
        result = locate_project_python(tmp_path, venv_names=["myenv"])
        assert result == custom_python


# ---------------------------------------------------------------------------
# probe_python_packages — error paths
# ---------------------------------------------------------------------------


class TestProbePythonPackagesExtended:
    def test_missing_executable_returns_error_dict(self, tmp_path):
        fake_python = str(tmp_path / "nonexistent_python")
        result = probe_python_packages(fake_python, ("numpy",))
        assert result["available"]["numpy"] is False
        assert result["error"] is not None
        assert "not found" in result["error"].lower()

    def test_nonzero_exit_code_returns_error(self, tmp_path, monkeypatch):
        python_path = tmp_path / ".venv" / "bin" / "python"
        python_path.parent.mkdir(parents=True)
        python_path.write_text("#!/usr/bin/env python3\n")

        class _FailProc:
            returncode = 1
            stdout = ""
            stderr = "module not found"

        monkeypatch.setattr("shared.runtime_env.subprocess.run", lambda *a, **k: _FailProc())
        # Clear the lru_cache so our monkeypatch actually takes effect
        probe_python_packages.cache_clear()

        result = probe_python_packages(str(python_path), ("torch",), timeout_seconds=1)
        assert result["available"]["torch"] is False
        assert result["error"] is not None
        assert "exit" in result["error"] or "module" in result["error"]

    def test_timeout_returns_error(self, tmp_path, monkeypatch):
        python_path = tmp_path / ".venv" / "bin" / "python"
        python_path.parent.mkdir(parents=True)
        python_path.write_text("#!/usr/bin/env python3\n")

        def _timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd=a[0], timeout=k.get("timeout", 1))

        monkeypatch.setattr("shared.runtime_env.subprocess.run", _timeout)
        probe_python_packages.cache_clear()

        result = probe_python_packages(str(python_path), ("torch",), timeout_seconds=1)
        assert result["available"]["torch"] is False
        assert "timed out" in result["error"].lower()

    def test_result_has_available_and_versions_keys(self, tmp_path, monkeypatch):
        python_path = tmp_path / ".venv" / "bin" / "python"
        python_path.parent.mkdir(parents=True)
        python_path.write_text("#!/usr/bin/env python3\n")

        class _OkProc:
            returncode = 0
            stdout = json.dumps({"available": {"torch": False}, "versions": {"torch": None}})
            stderr = ""

        monkeypatch.setattr("shared.runtime_env.subprocess.run", lambda *a, **k: _OkProc())
        probe_python_packages.cache_clear()

        result = probe_python_packages(str(python_path), ("torch",), timeout_seconds=1)
        assert "available" in result
        assert "versions" in result


# ---------------------------------------------------------------------------
# build_venv_info — additional paths
# ---------------------------------------------------------------------------


class TestBuildVenvInfoExtended:
    def test_custom_module_list_forwarded(self, tmp_path, monkeypatch):
        python_path = tmp_path / ".venv" / "bin" / "python"
        python_path.parent.mkdir(parents=True)
        python_path.write_text("#!/usr/bin/env python3\n")

        seen_modules: list = []

        class _OkProc:
            returncode = 0
            stdout = json.dumps({"available": {"numpy": True}, "versions": {"numpy": "1.24"}})
            stderr = ""

        def _fake_run(cmd, **kwargs):
            seen_modules.append(cmd)
            return _OkProc()

        monkeypatch.setattr("shared.runtime_env.subprocess.run", _fake_run)
        probe_python_packages.cache_clear()

        info = build_venv_info(tmp_path, modules=("numpy",), timeout_seconds=1)
        assert info["packages"]["available"]["numpy"] is True

    def test_error_none_when_probe_succeeds(self, tmp_path, monkeypatch):
        python_path = tmp_path / ".venv" / "bin" / "python"
        python_path.parent.mkdir(parents=True)
        python_path.write_text("#!/usr/bin/env python3\n")

        class _OkProc:
            returncode = 0
            stdout = json.dumps({"available": {"torch": False}, "versions": {"torch": None}})
            stderr = ""

        monkeypatch.setattr("shared.runtime_env.subprocess.run", lambda *a, **k: _OkProc())
        probe_python_packages.cache_clear()

        info = build_venv_info(tmp_path, timeout_seconds=1)
        assert info["error"] is None

    def test_path_key_in_result(self, tmp_path):
        info = build_venv_info(tmp_path)
        assert "path" in info
        assert "python" in info["path"].lower()
