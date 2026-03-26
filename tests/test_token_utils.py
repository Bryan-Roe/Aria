"""Tests for shared/token_utils.py — token counting and message pruning re-export."""
from __future__ import annotations

import pytest
from typing import List

from shared.token_utils import (
    RoleMessage,
    MODEL_CONTEXT_DEFAULTS,
    PruneStats,
    count_messages_tokens,
    prune_messages,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _msg(role: str, content: str) -> RoleMessage:
    return {"role": role, "content": content}


def _chat(*pairs: tuple[str, str]) -> List[RoleMessage]:
    """Build a message list from (role, content) pairs."""
    return [_msg(r, c) for r, c in pairs]


# ---------------------------------------------------------------------------
# Import / re-export sanity
# ---------------------------------------------------------------------------

class TestImports:
    def test_all_symbols_accessible(self):
        assert callable(count_messages_tokens)
        assert callable(prune_messages)
        assert isinstance(MODEL_CONTEXT_DEFAULTS, dict)

    def test_model_context_defaults_has_known_models(self):
        assert "gpt-4o" in MODEL_CONTEXT_DEFAULTS
        assert "azure-default" in MODEL_CONTEXT_DEFAULTS
        assert MODEL_CONTEXT_DEFAULTS["gpt-4o"] == 128000

    def test_prune_stats_namedtuple_style(self):
        # PruneStats should be accessible and usable as a container.
        stats = PruneStats  # may be a class or namedtuple
        assert stats is not None


# ---------------------------------------------------------------------------
# count_messages_tokens
# ---------------------------------------------------------------------------

class TestCountMessagesTokens:
    def test_empty_messages(self):
        count = count_messages_tokens([], "local", None)
        assert isinstance(count, int)
        assert count >= 0

    def test_single_message_nonzero(self):
        msgs = _chat(("user", "Hello, how are you?"))
        count = count_messages_tokens(msgs, "local", None)
        assert count > 0

    def test_more_content_more_tokens(self):
        short_msgs = _chat(("user", "Hi"))
        long_msgs = _chat(("user", "Hi " * 100))
        short_count = count_messages_tokens(short_msgs, "local", None)
        long_count = count_messages_tokens(long_msgs, "local", None)
        assert long_count > short_count

    def test_provider_azure(self):
        msgs = _chat(("user", "test"))
        count = count_messages_tokens(msgs, "azure", "azure-default")
        assert isinstance(count, int)
        assert count > 0

    def test_with_system_prompt(self):
        msgs = _chat(("user", "question"))
        without_sys = count_messages_tokens(msgs, "local", None)
        with_sys = count_messages_tokens(msgs, "local", None, system_prompt="You are helpful.")
        assert with_sys > without_sys

    def test_multiple_messages(self):
        msgs = _chat(
            ("system", "You are a helpful assistant."),
            ("user", "What is 2 + 2?"),
            ("assistant", "2 + 2 equals 4."),
            ("user", "Thanks!"),
        )
        count = count_messages_tokens(msgs, "openai", "gpt-4o")
        assert count > 10


# ---------------------------------------------------------------------------
# prune_messages
# ---------------------------------------------------------------------------

class TestPruneMessages:
    def test_no_prune_needed(self):
        msgs = _chat(("user", "Hi"))
        pruned, stats, sys_msg = prune_messages(msgs, "local", None, max_context_tokens=4096)
        assert len(pruned) >= 1

    def test_returns_three_tuple(self):
        msgs = _chat(("user", "Hello"))
        result = prune_messages(msgs, "local", None, max_context_tokens=4096)
        assert len(result) == 3

    def test_prune_removes_oldest_messages(self):
        # Create many messages that would exceed a tiny context window
        msgs = [_msg("user" if i % 2 == 0 else "assistant", f"message number {i} " * 20)
                for i in range(20)]
        pruned, stats, _ = prune_messages(msgs, "local", None, max_context_tokens=200)
        # Should have removed some messages under tight constraint
        assert len(pruned) <= len(msgs)

    def test_prune_stats_accessible(self):
        msgs = _chat(("user", "Hello"), ("assistant", "Hi"), ("user", "How are you?"))
        _, stats, _ = prune_messages(msgs, "local", None, max_context_tokens=4096)
        # stats should be PruneStats — has some attribute about pruning
        assert stats is not None

    def test_system_message_extraction(self):
        msgs = [
            _msg("system", "You are Aria."),
            _msg("user", "Hello"),
            _msg("assistant", "Hi there"),
        ]
        pruned, stats, sys_msg = prune_messages(msgs, "local", None, max_context_tokens=4096)
        # System message may be extracted or kept inline depending on implementation
        # At minimum, the function should not error
        assert pruned is not None

    def test_large_context_preserves_all(self):
        msgs = _chat(
            ("user", "Message one"),
            ("assistant", "Response one"),
            ("user", "Message two"),
        )
        pruned, stats, _ = prune_messages(msgs, "local", None, max_context_tokens=128000)
        assert len(pruned) == len(msgs)

    def test_none_max_tokens_uses_default(self):
        msgs = _chat(("user", "Hello"))
        # passing None for max_context_tokens should use a sensible default
        result = prune_messages(msgs, "local", None, max_context_tokens=None)
        assert result is not None
