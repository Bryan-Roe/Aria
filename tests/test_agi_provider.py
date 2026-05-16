"""
Unit tests for the AGI (Artificial General Intelligence) provider.

Tests cover:
- AGI provider initialization
- Chain-of-thought reasoning
- Task decomposition
- Self-reflection
- Memory/context management
- Integration with base providers
"""

import sys
from collections.abc import Iterable
from pathlib import Path

import pytest

from agi_provider import AGIContext, AGIProvider, ReasoningStep, _infer_aria_movement_tag, create_agi_provider
from chat_providers import BaseChatProvider, ProviderChoice, RoleMessage

# Add ai-projects/chat-cli/src to path
repo_root = Path(__file__).resolve().parent.parent
talk_to_ai_src = repo_root / "ai-projects" / "chat-cli" / "src"
sys.path.insert(0, str(talk_to_ai_src))


class MockBaseProvider(BaseChatProvider):
    """Mock provider for testing AGI enhancement."""

    def __init__(self, response: str = "Mock response"):
        self.response = response
        self.call_count = 0
        self.last_messages = None

    def complete(self, messages: list[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        self.call_count += 1
        self.last_messages = messages
        if stream:

            def gen():
                yield self.response

            return gen()
        return self.response


class TestAGIContext:
    """Tests for AGIContext memory management."""

    def test_context_initialization(self):
        """Test AGIContext initializes with empty state."""
        ctx = AGIContext()
        assert ctx.conversation_history == []
        assert ctx.reasoning_chains == []
        assert ctx.goals == []
        assert ctx.learned_patterns == {}
        assert ctx.max_history == 50

    def test_add_message(self):
        """Test adding messages to context."""
        ctx = AGIContext()
        msg = {"role": "user", "content": "Hello"}
        ctx.add_message(msg)
        assert len(ctx.conversation_history) == 1
        assert ctx.conversation_history[0] == msg

    def test_message_pruning(self):
        """Test that old messages are pruned when max_history is reached."""
        ctx = AGIContext(max_history=5)

        # Add a system message
        ctx.add_message({"role": "system", "content": "System prompt"})

        # Add more messages than max_history
        for i in range(10):
            ctx.add_message({"role": "user", "content": f"Message {i}"})

        # Should have kept system + last 4 messages
        assert len(ctx.conversation_history) == 5
        # System message should be preserved
        assert ctx.conversation_history[0]["role"] == "system"

    def test_add_reasoning_chain(self):
        """Test adding reasoning chains."""
        ctx = AGIContext()
        chain = [ReasoningStep(step_type="analyze", content="Test analysis")]
        ctx.add_reasoning_chain(chain)
        assert len(ctx.reasoning_chains) == 1
        assert ctx.reasoning_chains[0] == chain

    def test_reasoning_chain_limit(self):
        """Test that only last 10 reasoning chains are kept."""
        ctx = AGIContext()

        for i in range(15):
            chain = [ReasoningStep(step_type="analyze", content=f"Chain {i}")]
            ctx.add_reasoning_chain(chain)

        assert len(ctx.reasoning_chains) == 10
        # Should have chains 5-14
        assert "Chain 5" in ctx.reasoning_chains[0][0].content
        assert "Chain 14" in ctx.reasoning_chains[-1][0].content

    def test_get_relevant_context(self):
        """Test extracting relevant context for a query."""
        ctx = AGIContext()
        ctx.add_message({"role": "user", "content": "What is quantum computing?"})
        ctx.add_message({"role": "assistant", "content": "Quantum computing uses qubits..."})
        ctx.goals = ["Learn about quantum"]

        context = ctx.get_relevant_context("Tell me more")

        assert "Recent conversation:" in context
        assert "user:" in context
        assert "Active goals:" in context
        assert "Learn about quantum" in context


class TestReasoningStep:
    """Tests for ReasoningStep dataclass."""

    def test_basic_step(self):
        """Test creating a basic reasoning step."""
        step = ReasoningStep(step_type="analyze", content="Analyzing the query")
        assert step.step_type == "analyze"
        assert step.content == "Analyzing the query"
        assert step.confidence == 1.0
        assert step.metadata == {}

    def test_step_with_metadata(self):
        """Test creating a step with metadata."""
        step = ReasoningStep(
            step_type="decompose",
            content="Breaking down task",
            confidence=0.8,
            metadata={"subtasks": ["task1", "task2"]},
        )
        assert step.confidence == 0.8
        assert step.metadata["subtasks"] == ["task1", "task2"]


class TestAGIHelpers:
    """Tests for AGI helper utilities."""

    def test_infer_aria_movement_tag_supports_vertical_and_spin(self):
        assert _infer_aria_movement_tag("Move up") == "[aria:walk:up]"
        assert _infer_aria_movement_tag("Go down") == "[aria:walk:down]"
        assert _infer_aria_movement_tag("Spin around") == "[aria:spin]"


class TestAGIProvider:
    """Tests for AGIProvider functionality."""

    def test_initialization_defaults(self):
        """Test AGI provider initializes with sensible defaults."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        assert agi.temperature == 0.7
        assert agi.max_output_tokens == 2048
        assert agi.enable_chain_of_thought is True
        assert agi.enable_self_reflection is True
        assert agi.enable_task_decomposition is True
        assert agi.reasoning_depth == 3
        assert agi.verbose is False

    def test_initialization_custom_settings(self):
        """Test AGI provider with custom settings."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(
            base_provider=mock_provider,
            temperature=0.5,
            max_output_tokens=1024,
            enable_chain_of_thought=False,
            reasoning_depth=5,
            verbose=True,
        )

        assert agi.temperature == 0.5
        assert agi.max_output_tokens == 1024
        assert agi.enable_chain_of_thought is False
        assert agi.reasoning_depth == 5
        assert agi.verbose is True

    def test_reasoning_depth_bounds(self):
        """Test reasoning depth is bounded between 1 and 5."""
        mock_provider = MockBaseProvider()

        # Test minimum bound
        agi = AGIProvider(base_provider=mock_provider, reasoning_depth=0)
        assert agi.reasoning_depth == 1

        # Test maximum bound
        agi = AGIProvider(base_provider=mock_provider, reasoning_depth=10)
        assert agi.reasoning_depth == 5

    def test_complete_simple_query(self):
        """Test completing a simple query."""
        mock_provider = MockBaseProvider(response="Test response")
        agi = AGIProvider(base_provider=mock_provider)

        messages = [{"role": "user", "content": "Hello"}]
        result = agi.complete(messages, stream=False)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_complete_streaming(self):
        """Test streaming response."""
        mock_provider = MockBaseProvider(response="Streaming test")
        agi = AGIProvider(base_provider=mock_provider)

        messages = [{"role": "user", "content": "Stream test"}]
        result = agi.complete(messages, stream=True)

        # Should return an iterable
        chunks = list(result)
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0

    def test_complete_empty_query(self):
        """Test handling empty query."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        messages = [{"role": "user", "content": "   "}]
        result = agi.complete(messages, stream=False)

        assert "ready to help" in result.lower()

    def test_query_analysis_simple(self):
        """Test query analysis for simple queries."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        analysis = agi._analyze_query("Hello")

        assert analysis["complexity"] == "simple"
        assert analysis["word_count"] == 1
        assert analysis["has_question"] is False

    def test_query_analysis_complex(self):
        """Test query analysis for complex queries."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        # Query with "step by step" triggers complex analysis
        query = "Can you provide a step by step detailed explanation of how quantum entanglement works in quantum computing and what are the practical applications?"
        analysis = agi._analyze_query(query)

        assert analysis["complexity"] == "complex"
        assert analysis["has_question"] is True
        assert "quantum" in analysis["domain"]

    def test_query_analysis_movement_intent(self):
        """Test query analysis detects Aria movement intent."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        analysis = agi._analyze_query("Move Aria to the left")

        assert analysis["intent"] == "movement"
        assert analysis["domain"] == "aria"

    def test_query_analysis_movement_defaults_to_aria_domain(self):
        """Bare movement commands should still resolve to Aria domain."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        analysis = agi._analyze_query("Jump left")

        assert analysis["intent"] == "movement"
        assert analysis["domain"] == "aria"

    def test_query_analysis_coding_intent(self):
        """Test query analysis detects coding intent."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        analysis = agi._analyze_query("Write a Python function to sort a list")

        assert analysis["intent"] == "coding"
        assert analysis["domain"] == "technical"

    def test_task_decomposition_explanation(self):
        """Test task decomposition for explanation queries."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        analysis = {"intent": "explanation", "domain": "general"}
        subtasks = agi._decompose_task("Explain machine learning", analysis)

        assert len(subtasks) > 0
        assert len(subtasks) <= 3  # Limited by reasoning_depth
        assert "concepts" in subtasks[0].lower() or "define" in subtasks[0].lower()

    def test_task_decomposition_coding(self):
        """Test task decomposition for coding queries."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        analysis = {"intent": "coding", "domain": "technical"}
        subtasks = agi._decompose_task("Write a sorting algorithm", analysis)

        assert len(subtasks) > 0
        assert any("requirement" in s.lower() or "understand" in s.lower() for s in subtasks)

    def test_chain_of_thought(self):
        """Test chain-of-thought reasoning generation."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        analysis = {"intent": "question", "domain": "quantum", "complexity": "moderate"}
        messages = [{"role": "user", "content": "What is a qubit?"}]

        thoughts = agi._chain_of_thought("What is a qubit?", analysis, messages)

        assert len(thoughts) > 0
        assert any("quantum" in t.lower() for t in thoughts)

    def test_self_reflection_aria_movement(self):
        """Test self-reflection adds Aria movement tags when needed."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        reasoning_chain = [
            ReasoningStep(
                step_type="analyze",
                content="Movement request",
                metadata={"intent": "movement", "domain": "aria"},
            )
        ]

        response = agi._reflect_and_improve("Move Aria left", "I'll move to the left!", reasoning_chain)

        assert "[aria:walk:left]" in response

    def test_self_reflection_aria_spin(self):
        """Test self-reflection adds Aria spin tag when needed."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        reasoning_chain = [
            ReasoningStep(
                step_type="analyze",
                content="Movement request",
                metadata={"intent": "movement", "domain": "aria"},
            )
        ]

        response = agi._reflect_and_improve("Spin Aria around", "Spinning now!", reasoning_chain)

        assert "[aria:spin]" in response

    def test_goal_management(self):
        """Test setting and clearing goals."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        # Set goals
        agi.set_goal("Learn quantum computing")
        agi.set_goal("Build an AI assistant")

        assert len(agi.context.goals) == 2

        # Clear goals
        agi.clear_goals()
        assert len(agi.context.goals) == 0

    def test_goal_limit(self):
        """Test that goals are limited to 5."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        for i in range(10):
            agi.set_goal(f"Goal {i}")

        assert len(agi.context.goals) == 5
        # Should have the last 5 goals
        assert "Goal 9" in agi.context.goals[-1]

    def test_reasoning_summary(self):
        """Test getting reasoning summary."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        # Add some state
        agi.set_goal("Test goal")
        agi.context.add_reasoning_chain([ReasoningStep(step_type="analyze", content="Test")])

        summary = agi.get_reasoning_summary()

        assert summary["total_reasoning_chains"] == 1
        assert summary["active_goals"] == ["Test goal"]
        assert isinstance(summary["learned_patterns_count"], int)

    def test_verbose_output(self):
        """Test verbose mode includes reasoning steps."""
        mock_provider = MockBaseProvider(response="Test response")
        agi = AGIProvider(base_provider=mock_provider, verbose=True)

        messages = [{"role": "user", "content": "Explain something"}]
        result = agi.complete(messages, stream=False)

        assert "AGI Reasoning Process" in result
        assert "Step 1" in result

    def test_fallback_response(self):
        """Test fallback response generation."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        analysis = {"intent": "movement", "domain": "aria", "has_question": False}

        # Test movement fallback
        response = agi._generate_fallback_response("Move left", analysis)
        assert "[aria:walk:left]" in response

        response = agi._generate_fallback_response("Jump", analysis)
        assert "[aria:jump]" in response

    def test_context_updates_during_complete(self):
        """Test that context is updated during completion."""
        mock_provider = MockBaseProvider(response="Test")
        agi = AGIProvider(base_provider=mock_provider)

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        agi.complete(messages, stream=False)

        # Context should have been updated
        assert len(agi.context.conversation_history) == 2
        assert len(agi.context.reasoning_chains) >= 1


class TestCreateAGIProvider:
    """Tests for the create_agi_provider factory function."""

    def test_create_default(self):
        """Test creating AGI provider with defaults."""
        provider, info = create_agi_provider()

        assert isinstance(provider, AGIProvider)
        assert info.name == "agi"
        assert "agi" in info.model.lower()

    def test_create_uses_auto_detected_base_provider(self, monkeypatch: pytest.MonkeyPatch):
        """Factory should wrap the best available non-AGI provider."""
        base = MockBaseProvider("auto wrapped")

        def fake_detect_provider(explicit=None, model_override=None, temperature=None, max_output_tokens=None):
            assert explicit == "auto"
            return base, ProviderChoice(name="openai", model=model_override or "gpt-test")

        monkeypatch.setitem(create_agi_provider.__globals__, "detect_provider", fake_detect_provider)

        provider, info = create_agi_provider(model="gpt-4")

        assert provider.base_provider is base
        assert info.name == "agi"
        assert info.model == "agi-openai-gpt-4"

    def test_create_with_options(self):
        """Test creating AGI provider with custom options."""
        provider, info = create_agi_provider(temperature=0.5, max_output_tokens=1024, verbose=True)

        assert provider.temperature == 0.5
        assert provider.max_output_tokens == 1024
        assert provider.verbose is True

    def test_create_with_model(self):
        """Test creating AGI provider with model override."""
        provider, info = create_agi_provider(model="gpt-4")

        assert "gpt-4" in info.model


class TestProviderIntegration:
    """Integration tests with the provider detection system."""

    def test_detect_agi_provider(self):
        """Test that AGI provider can be detected."""
        from chat_providers import detect_provider

        provider, info = detect_provider(explicit="agi")

        assert info.name == "agi"
        assert isinstance(provider, AGIProvider)

    def test_agi_provider_with_messages(self):
        """Test AGI provider processes messages correctly."""
        from chat_providers import detect_provider

        provider, info = detect_provider(explicit="agi")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"},
        ]

        result = provider.complete(messages, stream=False)

        assert isinstance(result, str)
        assert len(result) > 0


# Smoke test for basic functionality
def test_agi_smoke():
    """Smoke test for AGI provider."""
    mock_provider = MockBaseProvider(response="Smoke test passed")
    agi = AGIProvider(base_provider=mock_provider)

    result = agi.complete([{"role": "user", "content": "What is 2 plus 2?"}], stream=False)

    assert len(result) > 0
    assert mock_provider.call_count == 1


class TestAGISecurity:
    """Security tests for AGI provider input sanitization and validation."""

    def test_sanitize_input_null_bytes(self):
        """Test that null bytes are removed from input."""
        from agi_provider import _sanitize_input

        malicious = "Hello\x00World\x00!"
        result = _sanitize_input(malicious)

        assert "\x00" not in result
        assert "HelloWorld!" in result

    def test_sanitize_input_control_chars(self):
        """Test that control characters are removed."""
        from agi_provider import _sanitize_input

        malicious = "Hello\x01\x02\x03World"
        result = _sanitize_input(malicious)

        assert "\x01" not in result
        assert "\x02" not in result
        assert "HelloWorld" in result

    def test_sanitize_input_length_limit(self):
        """Test that input is truncated to max length."""
        from agi_provider import MAX_INPUT_LENGTH, _sanitize_input

        long_input = "A" * (MAX_INPUT_LENGTH + 1000)
        result = _sanitize_input(long_input)

        assert len(result) == MAX_INPUT_LENGTH

    def test_sanitize_input_non_string(self):
        """Test that non-string input returns empty string."""
        from agi_provider import _sanitize_input

        assert _sanitize_input(None) == ""
        assert _sanitize_input(123) == ""
        assert _sanitize_input([1, 2, 3]) == ""

    def test_sanitize_for_logging_escapes_html(self):
        """Test that HTML is escaped in logging output."""
        from agi_provider import _sanitize_for_logging

        malicious = "<script>alert('xss')</script>"
        result = _sanitize_for_logging(malicious)

        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_for_logging_length_limit(self):
        """Test that log output is truncated."""
        from agi_provider import _sanitize_for_logging

        long_input = "A" * 500
        result = _sanitize_for_logging(long_input, max_length=100)

        assert len(result) <= 103  # 100 + "..."
        assert result.endswith("...")

    def test_context_sanitizes_messages(self):
        """Test that AGIContext sanitizes message content."""
        ctx = AGIContext()

        # Add message with potential injection
        ctx.add_message({"role": "user", "content": "Hello\x00World"})

        # Message should be sanitized
        assert len(ctx.conversation_history) == 1
        assert "\x00" not in ctx.conversation_history[0]["content"]

    def test_provider_sanitizes_query(self):
        """Test that AGI provider sanitizes user queries."""
        mock_provider = MockBaseProvider(response="Test")
        agi = AGIProvider(base_provider=mock_provider)

        # Query with control characters
        messages = [{"role": "user", "content": "Test\x00Query\x01!"}]
        result = agi.complete(messages, stream=False)

        # Should complete without error
        assert len(result) > 0

    def test_goal_input_sanitization(self):
        """Test that goals are sanitized."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        # Set goal with potential injection
        agi.set_goal("Goal\x00with\x01control\x02chars")

        assert len(agi.context.goals) == 1
        goal = agi.context.goals[0]
        assert "\x00" not in goal
        assert "\x01" not in goal

    def test_goal_length_limit(self):
        """Test that goals are truncated to safe length."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        # Set very long goal
        long_goal = "A" * 500
        agi.set_goal(long_goal)

        assert len(agi.context.goals) == 1
        assert len(agi.context.goals[0]) <= 200

    def test_empty_goal_rejected(self):
        """Test that empty goals are not added."""
        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        agi.set_goal("")
        agi.set_goal("   ")

        # No goals should be added for empty or whitespace-only input
        assert len(agi.context.goals) == 0

    def test_message_count_limit(self):
        """Test that message count is limited to prevent DoS."""
        from agi_provider import MAX_HISTORY_SIZE

        mock_provider = MockBaseProvider(response="Test")
        agi = AGIProvider(base_provider=mock_provider)

        # Create more messages than the limit
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(MAX_HISTORY_SIZE + 10)]

        # Should complete without error
        result = agi.complete(messages, stream=False)
        assert len(result) > 0

    def test_exception_handling_no_leak(self):
        """Test that exceptions don't leak sensitive information."""

        class FailingProvider(BaseChatProvider):
            def complete(self, messages, stream=True):
                raise RuntimeError("SENSITIVE: database password is secret123")

        agi = AGIProvider(base_provider=FailingProvider())

        result = agi.complete([{"role": "user", "content": "Test"}], stream=False)

        # Should return fallback response, not expose error details
        assert "SENSITIVE" not in result
        assert "secret123" not in result
        assert "database" not in result.lower() or "password" not in result.lower()


# ---------------------------------------------------------------------------
# Protocol compliance tests
# ---------------------------------------------------------------------------


class TestMemoryInterface:
    """Tests for the MemoryInterface protocol and AGIContext compliance."""

    def test_agi_context_satisfies_memory_interface(self):
        """AGIContext must be a runtime-checkable MemoryInterface implementation."""
        from agi_provider import MemoryInterface

        ctx = AGIContext()
        assert isinstance(ctx, MemoryInterface)

    def test_custom_memory_backend_satisfies_interface(self):
        """A custom class implementing the three methods passes the protocol check."""
        from agi_provider import MemoryInterface

        class MinimalMemory:
            def add_message(self, message):
                pass

            def add_reasoning_chain(self, chain):
                pass

            def get_relevant_context(self, query):
                return ""

        mem = MinimalMemory()
        assert isinstance(mem, MemoryInterface)

    def test_incomplete_class_fails_interface(self):
        """A class missing required methods does not satisfy MemoryInterface."""
        from agi_provider import MemoryInterface

        class IncompleteMemory:
            def add_message(self, message):
                pass

            # missing add_reasoning_chain and get_relevant_context

        obj = IncompleteMemory()
        assert not isinstance(obj, MemoryInterface)


class TestEnvironmentInterface:
    """Tests for the EnvironmentInterface protocol."""

    def test_mock_provider_satisfies_environment_interface(self):
        """MockBaseProvider (used in other tests) satisfies EnvironmentInterface."""
        from agi_provider import EnvironmentInterface

        mock = MockBaseProvider()
        assert isinstance(mock, EnvironmentInterface)

    def test_custom_environment_satisfies_interface(self):
        """A custom class implementing complete() satisfies EnvironmentInterface."""
        from agi_provider import EnvironmentInterface

        class EchoEnvironment:
            def complete(self, messages, stream=True):
                return "echo"

        env = EchoEnvironment()
        assert isinstance(env, EnvironmentInterface)

    def test_object_without_complete_fails_interface(self):
        """An object without complete() does not satisfy EnvironmentInterface."""
        from agi_provider import EnvironmentInterface

        class NotAnEnvironment:
            def send(self, messages):
                return "nope"

        obj = NotAnEnvironment()
        assert not isinstance(obj, EnvironmentInterface)


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestAGIProviderAsync:
    """Tests for the async_complete method."""

    def test_async_complete_returns_string(self):
        """async_complete should resolve to a non-empty string."""
        import asyncio

        mock_provider = MockBaseProvider(response="Async response")
        agi = AGIProvider(base_provider=mock_provider)

        result = asyncio.run(
            agi.async_complete([{"role": "user", "content": "Hello async"}])
        )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_async_complete_empty_query(self):
        """async_complete should handle empty queries gracefully."""
        import asyncio

        mock_provider = MockBaseProvider()
        agi = AGIProvider(base_provider=mock_provider)

        result = asyncio.run(
            agi.async_complete([{"role": "user", "content": "   "}])
        )

        assert "ready to help" in result.lower()

    def test_async_complete_updates_context(self):
        """async_complete should update the provider's context."""
        import asyncio

        mock_provider = MockBaseProvider(response="Context update test")
        agi = AGIProvider(base_provider=mock_provider)

        asyncio.run(
            agi.async_complete([{"role": "user", "content": "Update context"}])
        )

        assert len(agi.context.conversation_history) >= 1

    def test_async_complete_concurrent(self):
        """Multiple concurrent async_complete calls should not corrupt state."""
        import asyncio

        async def run_concurrent():
            mock_provider = MockBaseProvider(response="Concurrent")
            agi = AGIProvider(base_provider=mock_provider)

            results = await asyncio.gather(
                agi.async_complete([{"role": "user", "content": "First"}]),
                agi.async_complete([{"role": "user", "content": "Second"}]),
            )
            return results

        results = asyncio.run(run_concurrent())
        assert len(results) == 2
        assert all(isinstance(r, str) and len(r) > 0 for r in results)
