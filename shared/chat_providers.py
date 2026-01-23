"""Re-export chat providers from the talk_to_ai package.

This keeps backward compatibility for imports from shared.chat_providers
while using the canonical implementations under talk_to_ai.providers.
"""
from __future__ import annotations

import sys
from pathlib import Path

package_root = Path(__file__).resolve().parent.parent / "talk-to-ai" / "src"
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

from talk_to_ai.providers import (  # type: ignore
    RoleMessage,
    ProviderChoice,
    BaseChatProvider,
    LocalEchoProvider,
    OpenAIProvider,
    AzureOpenAIProvider,
    detect_provider,
)

__all__ = [
    "RoleMessage",
    "ProviderChoice",
    "BaseChatProvider",
    "LocalEchoProvider",
    "OpenAIProvider",
    "AzureOpenAIProvider",
    "detect_provider",
]

try:  # Optional providers
    from talk_to_ai.providers import LoraLocalProvider  # type: ignore

    LoraLocalProvider
    __all__.append("LoraLocalProvider")
except Exception:
    pass

try:
    from talk_to_ai.providers import LMStudioProvider  # type: ignore

    LMStudioProvider
    __all__.append("LMStudioProvider")
except Exception:
    pass

try:
    from talk_to_ai.providers.agi_provider import (  # type: ignore
        AGIProvider,
        AGIContext,
        ReasoningStep,
        create_agi_provider,
    )

    __all__.extend([
        "AGIProvider",
        "AGIContext",
        "ReasoningStep",
        "create_agi_provider",
    ])
except Exception:
    pass
