from __future__ import annotations
import pytest
import chat_providers
import json
import tempfile
import unittest.mock
import unittest
from pathlib import Path
import sys
import os

# Ensure the src directory is on sys.path BEFORE any local module imports so
# that pytest running from the repo root finds the right chat_providers /
# agi_provider modules (src/ versions) instead of the root-level stubs.
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


pytest.importorskip("colorama")

from chat_cli import save_conversation  # noqa: E402


class ChatProviderTests(unittest.TestCase):
    def test_detect_provider_explicit_local_with_model_override(self) -> None:
        """Explicit local provider should always resolve to LocalEchoProvider."""
        # Remove keys so auto-detection cannot drift to cloud providers
        original = {
            "AZURE_OPENAI_API_KEY": os.environ.pop("AZURE_OPENAI_API_KEY", None),
            "AZURE_OPENAI_ENDPOINT": os.environ.pop("AZURE_OPENAI_ENDPOINT", None),
            "AZURE_OPENAI_DEPLOYMENT": os.environ.pop("AZURE_OPENAI_DEPLOYMENT", None),
            "OPENAI_API_KEY": os.environ.pop("OPENAI_API_KEY", None),
        }
        try:
            provider, info = chat_providers.detect_provider(
                explicit="local", model_override="offline-test-model")
            self.assertIsInstance(provider, chat_providers.LocalEchoProvider)
            self.assertEqual(info.name, "local")
            self.assertEqual(info.model, "offline-test-model")
        finally:
            for key, value in original.items():
                if value is not None:
                    os.environ[key] = value

    def test_local_echo_includes_aria_movement_tags(self) -> None:
        """Offline mode should still emit actionable Aria movement tags."""
        provider = chat_providers.LocalEchoProvider(seed=1)
        messages = [
            {"role": "user", "content": "Please move right and then wave"}]

        reply = provider.complete(messages, stream=False)

        self.assertIsInstance(reply, str)
        self.assertIn("[aria:", reply)
        self.assertTrue(any(tag in reply for tag in [
                        "[aria:walk:right]", "[aria:wave]"]))

    def test_local_echo_question_mentions_live_provider(self) -> None:
        """Generic question in local mode should direct user to real providers."""
        provider = chat_providers.LocalEchoProvider(seed=2)
        messages = [
            {"role": "user", "content": "What is quantum entanglement?"}]

        reply = provider.complete(messages, stream=False)

        self.assertIsInstance(reply, str)
        lowered = reply.lower()
        self.assertTrue("provider" in lowered or "offline" in lowered)
        self.assertTrue(any(name in lowered for name in [
                        "openai", "azure", "agi", "lm studio", "ollama"]))

    def test_local_echo_autonomous_prompt_returns_actionable_plan(self) -> None:
        """Autonomous prompts should stay useful offline instead of repeating fallback warnings."""
        provider = chat_providers.LocalEchoProvider(seed=3)
        messages = [
            {
                "role": "user",
                "content": "Start working autonomously on the most useful next step and keep driving the conversation without waiting for user input.",
            }
        ]

        reply = provider.complete(messages, stream=False)

        self.assertIsInstance(reply, str)
        lowered = reply.lower()
        self.assertIn("autonomous", lowered)
        self.assertTrue(any(token in lowered for token in [
                        "plan", "next step", "review", "objective"]))
        self.assertNotIn("canned responses", lowered)

    def test_save_conversation_writes_jsonl(self) -> None:
        """save_conversation should persist one JSON object per line in order."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = save_conversation(messages, Path(tmp_dir))

            self.assertTrue(out_path.exists())
            lines = out_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 3)

            parsed = [json.loads(line) for line in lines]
            self.assertEqual(parsed, messages)

    def test_save_conversation_retries_when_timestamp_collides(self) -> None:
        """Saving twice with the same timestamp should not overwrite the first file."""
        messages = [{"role": "user", "content": "Hello"}]

        with tempfile.TemporaryDirectory() as tmp_dir:
            with unittest.mock.patch("chat_cli.now_ts", return_value="20250101_010203_000000"):
                first_path = save_conversation(messages, Path(tmp_dir))
                second_path = save_conversation(messages, Path(tmp_dir))

            self.assertTrue(first_path.exists())
            self.assertTrue(second_path.exists())
            self.assertNotEqual(first_path, second_path)
            self.assertEqual(
                first_path.name, "chat_20250101_010203_000000.jsonl")
            self.assertEqual(second_path.name,
                             "chat_20250101_010203_000000_1.jsonl")
            self.assertEqual(
                first_path.read_text(encoding="utf-8"),
                second_path.read_text(encoding="utf-8"),
            )


class AGIMultiAgentTests(unittest.TestCase):
    """Tests for AGI multi-agent routing and dispatch."""

    def setUp(self) -> None:
        import agi_provider
        self.agi = agi_provider.AGIProvider(base_provider=None)
        self._registry = agi_provider._AGENT_REGISTRY

    def test_select_agent_quantum_domain(self) -> None:
        """Quantum domain + explanation intent should select quantum-specialist."""
        analysis = {"intent": "explanation",
                    "domain": "quantum", "confidence": 0.8}
        agent, score = self.agi._select_agent(analysis)
        self.assertEqual(agent, "quantum-specialist")
        self.assertGreater(score, 0.0)

    def test_select_agent_aria_movement(self) -> None:
        """Movement intent + aria domain should select aria-character."""
        analysis = {"intent": "movement", "domain": "aria", "confidence": 0.9}
        agent, score = self.agi._select_agent(analysis)
        self.assertEqual(agent, "aria-character")
        self.assertGreater(score, 0.0)

    def test_select_agent_coding_falls_to_code_specialist(self) -> None:
        """Technical domain + coding intent should select code-specialist."""
        analysis = {"intent": "coding",
                    "domain": "technical", "confidence": 0.7}
        agent, score = self.agi._select_agent(analysis)
        self.assertEqual(agent, "code-specialist")
        self.assertGreater(score, 0.0)

    def test_select_agent_unknown_returns_general(self) -> None:
        """Unrecognised domain/intent should fall back to 'general' with score 0."""
        analysis = {"intent": "general",
                    "domain": "general", "confidence": 0.5}
        agent, score = self.agi._select_agent(analysis)
        self.assertEqual(agent, "general")
        self.assertEqual(score, 0.0)

    def test_dispatch_agi_agent_returns_none(self) -> None:
        """Dispatching to 'general' (provider=agi) must return None so AGI handles it."""
        result = self.agi._dispatch_to_agent("hello", "general", {})
        self.assertIsNone(result)

    def test_dispatch_unavailable_specialist_returns_none(self) -> None:
        """If specialist provider is unavailable, dispatch should return None gracefully."""
        # 'quantum' provider will fail in this env — we just need no exception raised.
        result = self.agi._dispatch_to_agent(
            "What is superposition?", "quantum-specialist",
            {"intent": "explanation", "domain": "quantum"},
        )
        # Either None (unavailable) or a string (available) — must not raise.
        self.assertTrue(result is None or isinstance(result, str))

    def test_reason_sets_last_agent_used(self) -> None:
        """After _reason(), _last_agent_used should be set to a registry key."""
        messages: list = [{"role": "user", "content": "move Aria to the left"}]
        self.agi._reason("move Aria to the left", messages)
        self.assertIn(self.agi._last_agent_used, self._registry)

    def test_reasoning_summary_includes_agent_info(self) -> None:
        """get_reasoning_summary() must include last_agent_used, available_agents, and last_agent_score."""
        summary = self.agi.get_reasoning_summary()
        self.assertIn("last_agent_used", summary)
        self.assertIn("available_agents", summary)
        self.assertIn("last_agent_score", summary)
        self.assertIn("top_learned_patterns", summary)
        self.assertIsInstance(summary["available_agents"], list)
        self.assertIn("general", summary["available_agents"])
        self.assertIsInstance(summary["top_learned_patterns"], list)

    def test_reasoning_summary_top_patterns_populated_after_learning(self) -> None:
        """top_learned_patterns should reflect learned routing patterns, sorted by count."""
        self.agi._learn_from_routing(
            {"domain": "quantum", "intent": "explanation", "agent_score": 0.8},
            "quantum-specialist")
        self.agi._learn_from_routing(
            {"domain": "quantum", "intent": "explanation", "agent_score": 0.8},
            "quantum-specialist")
        self.agi._learn_from_routing(
            {"domain": "code", "intent": "coding", "agent_score": 0.7},
            "code-specialist")
        summary = self.agi.get_reasoning_summary()
        top = summary["top_learned_patterns"]
        self.assertGreaterEqual(len(top), 2)
        # Top pattern should be the one with count=2
        self.assertEqual(top[0]["agent"], "quantum-specialist")
        self.assertEqual(top[0]["count"], 2)

    def test_decompose_uses_agent_registry_templates(self) -> None:
        """When selected_agent is set, decompose should use its subtask templates."""
        analysis = {
            "intent": "coding",
            "domain": "quantum",
            "complexity": "complex",
            "confidence": 0.8,
            "selected_agent": "quantum-specialist",
        }
        steps = self.agi._decompose_task(
            "Write a Bell state circuit", analysis)
        # Should pull from quantum-specialist templates, not generic coding steps.
        self.assertTrue(any("quantum" in s.lower() for s in steps))

    def test_registry_has_required_agents(self) -> None:
        """All expected specialist agents should exist in the registry."""
        expected = {"quantum-specialist", "code-specialist", "aria-character",
                    "ai-specialist", "reasoning-specialist", "general"}
        self.assertTrue(expected.issubset(set(self._registry.keys())))

    def test_select_agent_reasoning_intent_routes_to_reasoning_specialist(self) -> None:
        """A query with intent='reasoning' and domain='ai' should select reasoning-specialist."""
        analysis = {"intent": "reasoning", "domain": "ai", "confidence": 0.7}
        agent, score = self.agi._select_agent(analysis)
        # ai-specialist also matches domain=ai, but reasoning-specialist matches both domain+intent
        self.assertEqual(agent, "reasoning-specialist")
        self.assertGreater(score, 0.0)

    def test_analyze_query_detects_step_by_step_as_reasoning_intent(self) -> None:
        """'Think through this step by step' should be detected as intent='reasoning'."""
        analysis = self.agi._analyze_query("Think through this step by step")
        self.assertEqual(analysis["intent"], "reasoning")

    def test_learn_from_routing_stores_pattern(self) -> None:
        """_learn_from_routing should record domain+intent routing in learned_patterns."""
        analysis = {"domain": "quantum", "intent": "explanation",
                    "agent_score": 0.8, "selected_agent": "quantum-specialist"}
        self.agi._learn_from_routing(analysis, "quantum-specialist")
        key = "routing_quantum_explanation"
        self.assertIn(key, self.agi.context.learned_patterns)
        pattern = self.agi.context.learned_patterns[key]
        self.assertEqual(pattern["agent"], "quantum-specialist")
        self.assertEqual(pattern["count"], 1)

    def test_learn_from_routing_increments_count(self) -> None:
        """Repeated calls with same domain+intent should increment the pattern count."""
        analysis = {"domain": "technical",
                    "intent": "coding", "agent_score": 0.7}
        self.agi._learn_from_routing(analysis, "code-specialist")
        self.agi._learn_from_routing(analysis, "code-specialist")
        key = "routing_technical_coding"
        self.assertEqual(self.agi.context.learned_patterns[key]["count"], 2)

    def test_learn_from_routing_ignores_general(self) -> None:
        """General agent routing should NOT be stored as a pattern."""
        analysis = {"domain": "general",
                    "intent": "general", "agent_score": 0.0}
        self.agi._learn_from_routing(analysis, "general")
        self.assertNotIn("routing_general_general",
                         self.agi.context.learned_patterns)

    def test_select_agent_learned_pattern_boosts_score(self) -> None:
        """After routing to quantum-specialist for quantum+explanation, the next call should have a higher score."""
        analysis = {"domain": "quantum", "intent": "explanation",
                    "confidence": 0.8, "agent_score": 0.8}
        # First call — no learned pattern yet.
        _, score_before = self.agi._select_agent(analysis)
        # Simulate the routing being learned.
        self.agi._learn_from_routing(analysis, "quantum-specialist")
        # Second call — learned pattern should add a small bonus.
        _, score_after = self.agi._select_agent(analysis)
        self.assertGreaterEqual(score_after, score_before)

    def test_select_agent_decay_reduces_old_pattern_boost(self) -> None:
        """A pattern last observed 48 h ago should give a smaller boost than one just observed."""
        import time
        analysis = {"domain": "quantum", "intent": "explanation",
                    "confidence": 0.8, "agent_score": 0.8}
        # Learn a fresh pattern.
        self.agi._learn_from_routing(analysis, "quantum-specialist")
        _, score_fresh = self.agi._select_agent(analysis)

        # Artificially age the pattern by 48 h.
        key = "routing_quantum_explanation"
        self.agi.context.learned_patterns[key]["last_seen"] = time.time(
        ) - 48 * 3600
        _, score_old = self.agi._select_agent(analysis)

        # Stale pattern should yield a lower (or equal) score.
        self.assertLessEqual(score_old, score_fresh)


class ProviderAliasTests(unittest.TestCase):
    """Tests for provider name alias normalization in detect_provider."""

    def setUp(self) -> None:
        # Strip cloud keys so only local provider can be selected via alias
        self._saved = {}
        for k in (
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT",
            "OPENAI_API_KEY",
        ):
            self._saved[k] = os.environ.pop(k, None)

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is not None:
                os.environ[k] = v

    def test_local_echo_alias_resolves_to_local_provider(self) -> None:
        """'local-echo' alias should resolve to LocalEchoProvider."""
        provider, info = chat_providers.detect_provider(explicit="local-echo")
        self.assertIsInstance(provider, chat_providers.LocalEchoProvider)
        self.assertEqual(info.name, "local")

    def test_aliases_dict_is_exported(self) -> None:
        """_PROVIDER_ALIASES must be accessible as a module attribute."""
        aliases = chat_providers._PROVIDER_ALIASES
        self.assertIsInstance(aliases, dict)
        self.assertIn("azure_openai", aliases)
        self.assertIn("local-echo", aliases)
        self.assertIn("quantum-llm", aliases)


if __name__ == "__main__":
    unittest.main()
