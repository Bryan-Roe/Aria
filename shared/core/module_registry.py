"""Central registry for ai-projects modules with lazy loading and path management.

This module provides a single source of truth for importing from ai-projects/,
eliminating the need for scattered sys.path manipulations and multiple import patterns.

Usage:
    from shared.core.module_registry import AIProjectsRegistry

    # Access chat provider API
    provider_module = AIProjectsRegistry.chat_cli()
    detect_provider = provider_module.detect_provider

    # Access quantum ML API
    quantum_module = AIProjectsRegistry.quantum_ml()
    submit_job = quantum_module.submit_job
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class _LazyModule:
    """Wrapper for lazy-loaded modules to avoid early imports."""

    def __init__(self, module_path: Path, module_name: str):
        self.module_path = module_path
        self.module_name = module_name
        self._module = None

    def _load(self) -> Any:
        """Load module on first access."""
        if self._module is not None:
            return self._module

        if not self.module_path.exists():
            raise ImportError(f"Module path not found: {self.module_path}")

        # Add to sys.path if not already there
        str_path = str(self.module_path.parent)
        if str_path not in sys.path:
            sys.path.insert(0, str_path)

        # Import the module
        spec = importlib.util.spec_from_file_location(self.module_name, self.module_path / "__init__.py")
        if spec and spec.loader:
            self._module = importlib.util.module_from_spec(spec)
            sys.modules[self.module_name] = self._module
            spec.loader.exec_module(self._module)
        else:
            # Fallback: use direct import with sys.path
            if str_path not in sys.path:
                sys.path.insert(0, str_path)
            self._module = importlib.import_module(self.module_name)

        return self._module

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to loaded module."""
        return getattr(self._load(), name)


class AIProjectsRegistry:
    """Registry for all ai-projects module APIs with lazy loading.

    Each project is loaded exactly once and cached thereafter.
    Import paths are managed centrally here.
    """

    _cache: Dict[str, Any] = {}
    _repo_root: Optional[Path] = None

    @classmethod
    def _get_repo_root(cls) -> Path:
        """Get repository root path."""
        if cls._repo_root is None:
            # Traverse up from shared/ to find repo root
            current = Path(__file__).parent.parent.parent
            if not (current / "ai-projects").exists():
                raise RuntimeError("Cannot find ai-projects/ directory")
            cls._repo_root = current
        return cls._repo_root

    @classmethod
    def _get_ai_project_path(cls, project_name: str, submodule: str = "src") -> Path:
        """Get path to ai-project submodule."""
        repo_root = cls._get_repo_root()
        project_path = repo_root / "ai-projects" / project_name / submodule
        if not project_path.exists():
            raise ImportError(f"AI project module not found: {project_path}")
        return project_path

    @classmethod
    def chat_cli(cls) -> Any:
        """Get chat-cli module (chat providers, token utilities, AGI provider)."""
        cache_key = "chat_cli"
        if cache_key not in cls._cache:
            import sys

            # Ensure project path exists; if missing, this is a hard failure for tests.
            try:
                chat_cli_src = cls._get_ai_project_path("chat-cli", "src")
            except ImportError as e:
                raise ImportError(f"Failed to load chat-cli: {e}")

            if str(chat_cli_src) not in sys.path:
                sys.path.insert(0, str(chat_cli_src))

            try:
                # Import using the dynamic module pattern
                import importlib

                chat_providers = importlib.import_module("chat_providers")
                token_utils = importlib.import_module("token_utils")
                agi_provider = importlib.import_module("agi_provider")

                # Create namespace module
                class ChatCliNamespace:
                    pass

                ns = ChatCliNamespace()
                ns.chat_providers = chat_providers
                ns.token_utils = token_utils
                ns.agi_provider = agi_provider
                ns.detect_provider = chat_providers.detect_provider
                ns.prune_messages = token_utils.prune_messages
                ns.create_agi_provider = agi_provider.create_agi_provider

                cls._cache[cache_key] = ns
            except ImportError as e:
                # Provide a graceful fallback namespace when chat-cli is unavailable.
                # This allows the rest of the application to operate with a local
                # echo-style provider instead of raising ImportError at import time.
                import logging as _logging

                _logging.warning(f"chat-cli not found: {e}. Using fallback local shim.")

                class ChatCliNamespace:
                    pass

                ns = ChatCliNamespace()

                # Minimal token_utils fallback
                class _TokenUtils:
                    @staticmethod
                    def prune_messages(messages, max_tokens=None):
                        # Best-effort no-op prune for environments without token utils
                        return messages

                ns.token_utils = _TokenUtils()

                # Minimal AGI provider stub
                class _AGIProviderStub:
                    @staticmethod
                    def create_agi_provider(*args, **kwargs):
                        raise ImportError("AGI provider not available in fallback")

                ns.agi_provider = _AGIProviderStub()

                # Simple fallback provider compatible with Consumer API used across repo
                class _FallbackProvider:
                    def complete(self, messages, stream=True):
                        # Find last user message and echo it
                        last = ""
                        for m in reversed(messages or []):
                            if isinstance(m, dict) and m.get("role") == "user":
                                content = m.get("content")
                                if isinstance(content, str) and content.strip():
                                    last = content.strip()
                                    break
                        reply = f"Echo (fallback): {last}" if last else "Echo (fallback): Hello"
                        if stream:

                            def _gen():
                                yield reply

                            return _gen()
                        return reply

                # Lightweight info object with name/model attributes
                class _Info:
                    def __init__(self, name, model):
                        self.name = name
                        self.model = model

                def _detect_provider(explicit=None, model_override=None, temperature=None, max_output_tokens=None):
                    return _FallbackProvider(), _Info(name="local", model=(model_override or "fallback"))

                ns.chat_providers = None
                ns.detect_provider = _detect_provider
                ns.prune_messages = ns.token_utils.prune_messages
                ns.create_agi_provider = lambda *args, **kwargs: (_AGIProviderStub())

                cls._cache[cache_key] = ns

        return cls._cache[cache_key]

    @classmethod
    def quantum_ml(cls) -> Any:
        """Get quantum-ml module API."""
        cache_key = "quantum_ml"
        if cache_key not in cls._cache:
            try:
                import sys

                quantum_src = cls._get_ai_project_path("quantum-ml", "src")
                if str(quantum_src) not in sys.path:
                    sys.path.insert(0, str(quantum_src))

                import importlib

                # Try to import quantum pipeline module if it exists
                try:
                    quantum_pipeline = importlib.import_module("quantum_pipeline")
                except ImportError:
                    quantum_pipeline = None

                class QuantumMLNamespace:
                    pass

                ns = QuantumMLNamespace()
                ns.pipeline = quantum_pipeline

                cls._cache[cache_key] = ns
            except ImportError as e:
                raise ImportError(f"Failed to load quantum-ml: {e}")

        return cls._cache[cache_key]

    @classmethod
    def lora_training(cls) -> Any:
        """Get LoRA training module API."""
        cache_key = "lora_training"
        if cache_key not in cls._cache:
            try:
                import sys

                lora_path = cls._get_ai_project_path("lora-training", "microsoft_phi-silica-3.6_v1/src")
                if str(lora_path) not in sys.path:
                    sys.path.insert(0, str(lora_path))

                # LoRA training API TBD; for now just store the path
                class LoraNamespace:
                    path = lora_path

                ns = LoraNamespace()
                cls._cache[cache_key] = ns
            except ImportError as e:
                raise ImportError(f"Failed to load lora-training: {e}")

        return cls._cache[cache_key]

    @classmethod
    def llm_maker(cls) -> Any:
        """Get LLM-maker module API."""
        cache_key = "llm_maker"
        if cache_key not in cls._cache:
            try:
                import sys

                llm_src = cls._get_ai_project_path("llm-maker", "src")
                if str(llm_src) not in sys.path:
                    sys.path.insert(0, str(llm_src))

                import importlib

                tool_maker = importlib.import_module("tool_maker")

                class LLMMakerNamespace:
                    pass

                ns = LLMMakerNamespace()
                ns.tool_maker = tool_maker

                cls._cache[cache_key] = ns
            except ImportError as e:
                raise ImportError(f"Failed to load llm-maker: {e}")

        return cls._cache[cache_key]

    @classmethod
    def get_repo_root(cls) -> Path:
        """Get the repository root path."""
        return cls._get_repo_root()

    @classmethod
    def register_paths(cls, projects: list[str] = None) -> Dict[str, Path]:
        """Register sys.path entries for specified projects.

        Returns a dict of {project_name: path_added} for verification.

        Args:
            projects: List of project names to register, e.g., ['chat-cli', 'quantum-ml'].
                     If None, registers all known projects.
        """
        registered = {}
        all_projects = ["chat-cli", "quantum-ml", "lora-training", "llm-maker"]
        projects_to_register = projects or all_projects

        for project in projects_to_register:
            try:
                if project == "chat-cli":
                    path = cls._get_ai_project_path("chat-cli", "src")
                elif project == "quantum-ml":
                    path = cls._get_ai_project_path("quantum-ml", "src")
                elif project == "lora-training":
                    path = cls._get_ai_project_path("lora-training", "microsoft_phi-silica-3.6_v1/src")
                elif project == "llm-maker":
                    path = cls._get_ai_project_path("llm-maker", "src")
                else:
                    continue

                if str(path) not in sys.path:
                    sys.path.insert(0, str(path))
                registered[project] = path
            except ImportError:
                # Project path not found; skip silently
                pass

        return registered


__all__ = ["AIProjectsRegistry"]
