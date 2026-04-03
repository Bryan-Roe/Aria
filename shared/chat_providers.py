"""Chat providers re-export module for shared infrastructure.

This module re-exports chat providers from the canonical source at
ai-projects/chat-cli/src/chat_providers.py to avoid code duplication while
maintaining backward compatibility for imports from shared/.

Usage:
    from shared.chat_providers import detect_provider, RoleMessage
    # or after adding shared/ to sys.path:
    from chat_providers import detect_provider
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Load the canonical chat_providers module directly from ai-projects/chat-cli/src
_canonical_path = (
    Path(__file__).resolve().parent.parent
    / "ai-projects"
    / "chat-cli"
    / "src"
    / "chat_providers.py"
)
_spec = importlib.util.spec_from_file_location(
    "_canonical_chat_providers", _canonical_path
)
_canonical_module = importlib.util.module_from_spec(_spec)
sys.modules["_canonical_chat_providers"] = _canonical_module
_spec.loader.exec_module(_canonical_module)

# Re-export all public symbols from canonical chat_providers
RoleMessage = _canonical_module.RoleMessage
ProviderChoice = _canonical_module.ProviderChoice
BaseChatProvider = _canonical_module.BaseChatProvider
LocalEchoProvider = _canonical_module.LocalEchoProvider
OpenAIProvider = _canonical_module.OpenAIProvider
AzureOpenAIProvider = _canonical_module.AzureOpenAIProvider
detect_provider = _canonical_module.detect_provider

# Build __all__ dynamically based on what's exported and conditionally add optional providers
__all__ = [
    "RoleMessage",
    "ProviderChoice",
    "BaseChatProvider",
    "LocalEchoProvider",
    "OpenAIProvider",
    "AzureOpenAIProvider",
    "detect_provider",
]

# Conditionally export LoraLocalProvider if available
try:
    LoraLocalProvider = _canonical_module.LoraLocalProvider
    __all__.append("LoraLocalProvider")
except AttributeError:
    pass

# Conditionally export LMStudioProvider if available
try:
    LMStudioProvider = _canonical_module.LMStudioProvider
    __all__.append("LMStudioProvider")
except AttributeError:
    pass

# Conditionally export AGI provider using the same dynamic import pattern
try:
    _agi_path = (
        Path(__file__).resolve().parent.parent
        / "ai-projects"
        / "chat-cli"
        / "src"
        / "agi_provider.py"
    )
    if _agi_path.exists():
        _agi_spec = importlib.util.spec_from_file_location(
            "_agi_provider_module", _agi_path
        )
        _agi_module = importlib.util.module_from_spec(_agi_spec)
        sys.modules["_agi_provider_module"] = _agi_module
        _agi_spec.loader.exec_module(_agi_module)
        AGIProvider = _agi_module.AGIProvider
        AGIContext = _agi_module.AGIContext
        ReasoningStep = _agi_module.ReasoningStep
        create_agi_provider = _agi_module.create_agi_provider
        __all__.extend(
            ["AGIProvider", "AGIContext", "ReasoningStep", "create_agi_provider"]
        )
except (ImportError, AttributeError):
    pass
