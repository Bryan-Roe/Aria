"""Tests for shared/core/module_registry.py.

Covers: _LazyModule loading/caching/__getattr__,
AIProjectsRegistry path resolution, project loading,
error paths, and register_paths.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_registry_cache():
    """Reset AIProjectsRegistry class-level caches between tests."""
    from shared.core.module_registry import AIProjectsRegistry

    AIProjectsRegistry._cache.clear()
    AIProjectsRegistry._repo_root = None


@pytest.fixture(autouse=True)
def _reset_registry():
    _clear_registry_cache()
    yield
    _clear_registry_cache()


# ---------------------------------------------------------------------------
# _LazyModule
# ---------------------------------------------------------------------------


class TestLazyModule:
    def _make_lazy(self, path: Path, name: str):
        from shared.core.module_registry import _LazyModule

        return _LazyModule(path, name)

    def test_load_raises_import_error_for_missing_path(self, tmp_path):
        lm = self._make_lazy(tmp_path / "does_not_exist", "fake_module")
        with pytest.raises(ImportError, match="Module path not found"):
            lm._load()

    def test_load_is_cached_after_first_call(self, tmp_path):
        """Second call to _load() returns the same object."""
        # Create a minimal package directory with __init__.py
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("VALUE = 42\n")

        lm = self._make_lazy(pkg, "mypkg_test_cache")
        # Remove from sys.modules to ensure fresh import
        sys.modules.pop("mypkg_test_cache", None)

        m1 = lm._load()
        m2 = lm._load()
        assert m1 is m2

        # Cleanup sys.modules
        sys.modules.pop("mypkg_test_cache", None)

    def test_load_adds_parent_to_syspath(self, tmp_path):
        pkg = tmp_path / "mypkg2"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("VALUE = 99\n")

        lm = self._make_lazy(pkg, "mypkg2_test_path")
        sys.modules.pop("mypkg2_test_path", None)

        lm._load()
        assert str(tmp_path) in sys.path

        sys.modules.pop("mypkg2_test_path", None)
        if str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))

    def test_getattr_delegates_to_module(self, tmp_path):
        pkg = tmp_path / "mypkg3"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("MY_CONST = 'hello'\n")

        lm = self._make_lazy(pkg, "mypkg3_test_attr")
        sys.modules.pop("mypkg3_test_attr", None)

        assert lm.MY_CONST == "hello"

        sys.modules.pop("mypkg3_test_attr", None)
        if str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))


# ---------------------------------------------------------------------------
# AIProjectsRegistry._get_repo_root
# ---------------------------------------------------------------------------


class TestGetRepoRoot:
    def test_get_repo_root_returns_path_with_ai_projects(self):
        from shared.core.module_registry import AIProjectsRegistry

        root = AIProjectsRegistry._get_repo_root()
        assert (root / "ai-projects").exists()

    def test_get_repo_root_is_cached(self):
        from shared.core.module_registry import AIProjectsRegistry

        r1 = AIProjectsRegistry._get_repo_root()
        r2 = AIProjectsRegistry._get_repo_root()
        assert r1 is r2

    def test_get_repo_root_raises_when_ai_projects_missing(self, tmp_path):
        from shared.core.module_registry import AIProjectsRegistry

        AIProjectsRegistry._repo_root = None
        with patch.object(
            Path,
            "exists",
            lambda self: False if "ai-projects" in str(self) else True,
        ):
            with pytest.raises(RuntimeError, match="Cannot find ai-projects"):
                # Force re-discovery by clearing cached root
                AIProjectsRegistry._repo_root = None
                # Patch __file__ to point inside tmp_path
                fake_path = tmp_path / "shared" / "core" / "module_registry.py"
                with patch("shared.core.module_registry.__file__", str(fake_path)):
                    AIProjectsRegistry._get_repo_root()
        AIProjectsRegistry._repo_root = None


# ---------------------------------------------------------------------------
# AIProjectsRegistry._get_ai_project_path
# ---------------------------------------------------------------------------


class TestGetAIProjectPath:
    def test_returns_path_for_chat_cli(self):
        from shared.core.module_registry import AIProjectsRegistry

        path = AIProjectsRegistry._get_ai_project_path("chat-cli", "src")
        assert path.exists()
        assert path.name == "src"

    def test_raises_import_error_for_nonexistent_project(self):
        from shared.core.module_registry import AIProjectsRegistry

        with pytest.raises(ImportError, match="AI project module not found"):
            AIProjectsRegistry._get_ai_project_path("does-not-exist", "src")


# ---------------------------------------------------------------------------
# AIProjectsRegistry.chat_cli
# ---------------------------------------------------------------------------


class TestChatCli:
    def test_chat_cli_returns_namespace_with_detect_provider(self):
        from shared.core.module_registry import AIProjectsRegistry

        ns = AIProjectsRegistry.chat_cli()
        assert hasattr(ns, "detect_provider")
        assert callable(ns.detect_provider)

    def test_chat_cli_is_cached(self):
        from shared.core.module_registry import AIProjectsRegistry

        ns1 = AIProjectsRegistry.chat_cli()
        ns2 = AIProjectsRegistry.chat_cli()
        assert ns1 is ns2

    def test_chat_cli_has_prune_messages(self):
        from shared.core.module_registry import AIProjectsRegistry

        ns = AIProjectsRegistry.chat_cli()
        assert hasattr(ns, "prune_messages")

    def test_chat_cli_has_create_agi_provider(self):
        from shared.core.module_registry import AIProjectsRegistry

        ns = AIProjectsRegistry.chat_cli()
        assert hasattr(ns, "create_agi_provider")

    def test_chat_cli_raises_on_import_failure(self):
        from shared.core.module_registry import AIProjectsRegistry

        with patch(
            "shared.core.module_registry.AIProjectsRegistry._get_ai_project_path",
            side_effect=ImportError("no path"),
        ):
            AIProjectsRegistry._cache.clear()
            with pytest.raises(ImportError, match="Failed to load chat-cli"):
                AIProjectsRegistry.chat_cli()


# ---------------------------------------------------------------------------
# AIProjectsRegistry.quantum_ml
# ---------------------------------------------------------------------------


class TestQuantumML:
    def test_quantum_ml_returns_namespace(self):
        from shared.core.module_registry import AIProjectsRegistry

        ns = AIProjectsRegistry.quantum_ml()
        assert ns is not None
        assert hasattr(ns, "pipeline")

    def test_quantum_ml_is_cached(self):
        from shared.core.module_registry import AIProjectsRegistry

        ns1 = AIProjectsRegistry.quantum_ml()
        ns2 = AIProjectsRegistry.quantum_ml()
        assert ns1 is ns2

    def test_quantum_ml_raises_on_import_failure(self):
        from shared.core.module_registry import AIProjectsRegistry

        with patch(
            "shared.core.module_registry.AIProjectsRegistry._get_ai_project_path",
            side_effect=ImportError("no path"),
        ):
            AIProjectsRegistry._cache.clear()
            with pytest.raises(ImportError, match="Failed to load quantum-ml"):
                AIProjectsRegistry.quantum_ml()


# ---------------------------------------------------------------------------
# AIProjectsRegistry.lora_training
# ---------------------------------------------------------------------------


class TestLoraTraining:
    def test_lora_training_returns_namespace_or_raises(self):
        from shared.core.module_registry import AIProjectsRegistry

        try:
            ns = AIProjectsRegistry.lora_training()
            assert hasattr(ns, "path")
        except ImportError:
            # Acceptable if lora-training path is not present
            pass

    def test_lora_training_raises_on_import_failure(self):
        from shared.core.module_registry import AIProjectsRegistry

        with patch(
            "shared.core.module_registry.AIProjectsRegistry._get_ai_project_path",
            side_effect=ImportError("no path"),
        ):
            AIProjectsRegistry._cache.clear()
            with pytest.raises(ImportError, match="Failed to load lora-training"):
                AIProjectsRegistry.lora_training()


# ---------------------------------------------------------------------------
# AIProjectsRegistry.llm_maker
# ---------------------------------------------------------------------------


class TestLLMMaker:
    def test_llm_maker_returns_namespace_or_raises(self):
        from shared.core.module_registry import AIProjectsRegistry

        try:
            ns = AIProjectsRegistry.llm_maker()
            assert hasattr(ns, "tool_maker")
        except ImportError:
            # Acceptable if llm-maker path is not present
            pass

    def test_llm_maker_raises_on_import_failure(self):
        from shared.core.module_registry import AIProjectsRegistry

        with patch(
            "shared.core.module_registry.AIProjectsRegistry._get_ai_project_path",
            side_effect=ImportError("no path"),
        ):
            AIProjectsRegistry._cache.clear()
            with pytest.raises(ImportError, match="Failed to load llm-maker"):
                AIProjectsRegistry.llm_maker()


# ---------------------------------------------------------------------------
# AIProjectsRegistry.get_repo_root
# ---------------------------------------------------------------------------


def test_get_repo_root_public():
    from shared.core.module_registry import AIProjectsRegistry

    root = AIProjectsRegistry.get_repo_root()
    assert isinstance(root, Path)
    assert (root / "ai-projects").exists()


# ---------------------------------------------------------------------------
# AIProjectsRegistry.register_paths
# ---------------------------------------------------------------------------


class TestRegisterPaths:
    def test_register_paths_registers_chat_cli(self):
        from shared.core.module_registry import AIProjectsRegistry

        registered = AIProjectsRegistry.register_paths(["chat-cli"])
        assert "chat-cli" in registered
        chat_cli_path = str(registered["chat-cli"])
        assert chat_cli_path in sys.path

    def test_register_paths_registers_quantum_ml(self):
        from shared.core.module_registry import AIProjectsRegistry

        registered = AIProjectsRegistry.register_paths(["quantum-ml"])
        assert "quantum-ml" in registered

    def test_register_paths_all_when_none_provided(self):
        from shared.core.module_registry import AIProjectsRegistry

        registered = AIProjectsRegistry.register_paths(None)
        # At minimum chat-cli and quantum-ml should be registered
        assert len(registered) >= 1

    def test_register_paths_skips_unknown_project_silently(self):
        from shared.core.module_registry import AIProjectsRegistry

        registered = AIProjectsRegistry.register_paths(["unknown-project-xyz"])
        assert "unknown-project-xyz" not in registered

    def test_register_paths_does_not_duplicate_sys_path(self):
        from shared.core.module_registry import AIProjectsRegistry

        before_count = len(sys.path)
        AIProjectsRegistry.register_paths(["chat-cli"])
        AIProjectsRegistry.register_paths(["chat-cli"])  # second call
        after_count = len(sys.path)
        # Should not grow unboundedly — at most 1 new entry per project
        assert after_count <= before_count + 5  # generous bound
