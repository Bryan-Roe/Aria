"""Public API for chat-cli module.

This module defines the stable interface for the chat-cli component.
All imports from chat-cli should come through this module.
"""

# Re-export main APIs from internal modules
from .chat_providers import (
    detect_provider,
    BaseChatProvider,
    RoleMessage,
    LocalChatProvider,
    OpenAIChatProvider,
    AzureOpenAIChatProvider,
    LMStudioChatProvider,
)
from .token_utils import (
    prune_messages,
    count_tokens,
    estimate_tokens,
)
from .agi_provider import (
    create_agi,
    AGIProvider,
)

__all__ = [
    # Chat providers
    'detect_provider',
    'BaseChatProvider',
    'RoleMessage',
    'LocalChatProvider',
    'OpenAIChatProvider',
    'AzureOpenAIChatProvider',
    'LMStudioChatProvider',
    # Token utilities
    'prune_messages',
    'count_tokens',
    'estimate_tokens',
    # AGI provider
    'create_agi',
    'AGIProvider',
]
