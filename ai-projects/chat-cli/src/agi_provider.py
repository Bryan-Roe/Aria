"""
AGI (Artificial General Intelligence) Enhanced Chat Provider.

This module wraps a base chat provider and adds:
- query analysis (intent/domain/complexity)
- optional task decomposition
- optional reasoning traces
- optional self-reflection improvements

Architecture overview
---------------------
The module is organised around three logical subsystems:

Reasoning core
    ``AGIProvider._reason`` orchestrates the multi-step reasoning pipeline:
    query analysis → agent routing → optional task decomposition →
    chain-of-thought synthesis → self-reflection.

Memory subsystem
    ``AGIContext`` is the short-term, in-process memory store.  It tracks
    conversation history, past reasoning chains, active goals, and learned
    routing patterns.  ``MemoryInterface`` is a structural ``Protocol`` that
    any alternative memory backend must satisfy to be used as a drop-in
    replacement.

Environment interface
    The provider interacts with the outside world only through a
    ``BaseChatProvider`` for LLM inference and the ``_AGENT_REGISTRY`` for
    specialist dispatch.  ``EnvironmentInterface`` is a structural ``Protocol``
    describing the minimal contract for any environment adapter.

Extensibility
    Both ``MemoryInterface`` and ``EnvironmentInterface`` are
    ``runtime_checkable`` protocols so that third-party implementations can be
    validated at import time without inheriting from an abstract base class.

Public API (``__all__``)
    ``AGIProvider``, ``AGIContext``, ``ReasoningStep``,
    ``create_agi_provider``, ``MemoryInterface``, ``EnvironmentInterface``.
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, Iterable, List, Optional, Protocol, runtime_checkable

from chat_providers import (BaseChatProvider, ProviderChoice, RoleMessage,
                            detect_provider)

_logger = logging.getLogger(__name__)

__all__ = [
    "AGIProvider",
    "AGIContext",
    "ReasoningStep",
    "create_agi_provider",
    "MemoryInterface",
    "EnvironmentInterface",
    "MAX_INPUT_LENGTH",
    "MAX_HISTORY_SIZE",
    "MAX_GOALS",
    "MAX_REASONING_CHAINS",
    "_sanitize_input",
    "_sanitize_for_logging",
    "_infer_aria_movement_tag",
    "_AGENT_REGISTRY",
]

MAX_INPUT_LENGTH = 10000
MAX_HISTORY_SIZE = 50
MAX_GOALS = 5
MAX_REASONING_CHAINS = 10


# ---------------------------------------------------------------------------
# Extensibility protocols
# ---------------------------------------------------------------------------

@runtime_checkable
class MemoryInterface(Protocol):
    """Structural protocol for AGI memory backends.

    Any object that implements these three methods can be passed where
    ``AGIContext`` is expected, allowing alternative memory backends
    (e.g. a Redis-backed store or an in-process SQLite cache) without
    requiring inheritance.

    All methods **must** be safe to call from multiple threads when the
    provider is used concurrently.
    """

    def add_message(self, message: RoleMessage) -> None:
        """Append *message* to the conversation history.

        Implementations should enforce bounded storage — old messages should
        be evicted when the history exceeds the configured limit.

        Parameters
        ----------
        message:
            A dict with ``"role"`` and ``"content"`` keys.
        """
        ...

    # type: ignore[name-defined]
    def add_reasoning_chain(self, chain: List[ReasoningStep]) -> None:
        """Persist a completed reasoning *chain*.

        Implementations should cap the number of stored chains to avoid
        unbounded memory growth.

        Parameters
        ----------
        chain:
            Ordered list of ``ReasoningStep`` objects produced during one
            ``AGIProvider.complete`` call.
        """
        ...

    def get_relevant_context(self, query: str) -> str:
        """Return a concise textual summary of memory relevant to *query*.

        The returned string is injected into the AGI system prompt so it
        should be brief (a few hundred characters at most).

        Parameters
        ----------
        query:
            The user's latest query used to select relevant memory fragments.

        Returns
        -------
        str
            A plain-text context snippet, or an empty string when no relevant
            context is available.
        """
        raise NotImplementedError


@runtime_checkable
class EnvironmentInterface(Protocol):
    """Structural protocol for AGI environment adapters.

    An environment adapter provides the AGI provider with read/write access to
    its external execution context: submitting messages to an LLM backend and
    receiving responses.

    The minimal contract mirrors ``BaseChatProvider.complete`` so that any
    existing chat provider can serve as a conforming environment adapter.

    Implementing this protocol is **not** required for normal use — it is
    provided as an extension point for testing (mock environments) and for
    future multi-environment or simulation scenarios.
    """

    def complete(
        # type: ignore[name-defined]
        self, messages: List[RoleMessage], stream: bool = True
    ) -> Iterable[str] | str:
        """Submit *messages* to the environment and return the response.

        Parameters
        ----------
        messages:
            Ordered conversation turn list; each element is a dict with
            ``"role"`` and ``"content"`` keys.
        stream:
            When ``True`` the environment should return an iterable of token
            strings for real-time display.  When ``False`` it should return
            the complete response as a single ``str``.

        Returns
        -------
        Iterable[str] | str
            Either a generator of token strings (streaming) or a complete
            response string (non-streaming).
        """
        ...


# ---------------------------------------------------------------------------
# Agent registry — maps agent names to capabilities for multi-agent routing.
# Each entry describes the domains/intents an agent handles best, which
# underlying provider to instantiate, and subtask templates for decomposition.
# ---------------------------------------------------------------------------
_AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "quantum-specialist": {
        "domains": ["quantum"],
        "intents": ["explanation", "coding", "question"],
        "provider": "quantum",
        "confidence_boost": 0.3,
        "subtask_templates": [
            "Define the quantum computing concepts involved",
            "Explain quantum gates or circuit design if relevant",
            "Connect to classical computing equivalent",
            "Provide code using Qiskit or PennyLane if applicable",
        ],
        "description": "Expert in quantum computing, qubits, gates, and quantum algorithms",
    },
    "code-specialist": {
        "domains": ["technical"],
        "intents": ["coding", "creation"],
        "provider": "lora",
        "confidence_boost": 0.2,
        "subtask_templates": [
            "Identify required inputs, outputs, and edge cases",
            "Design the function/class interface",
            "Implement core logic with error handling",
            "Add type hints and docstring",
        ],
        "description": "Expert code generator for implementation tasks",
    },
    "aria-character": {
        "domains": ["aria"],
        "intents": ["movement", "creation"],
        "provider": "local",
        "confidence_boost": 0.4,
        "subtask_templates": [
            "Parse requested Aria action",
            "Select appropriate [aria:action] tag",
            "Compose natural language acknowledgement",
        ],
        "description": "Handles Aria character movement and action commands",
    },
    "ai-specialist": {
        "domains": ["ai"],
        "intents": ["explanation", "question", "coding"],
        "provider": "lora",
        "confidence_boost": 0.15,
        "subtask_templates": [
            "Identify the AI/ML concept being asked about",
            "Explain the mechanism with a concrete analogy",
            "Discuss trade-offs and practical usage",
            "Summarize key takeaways",
        ],
        "description": "AI/ML training, LoRA, transformers specialist",
    },
    "reasoning-specialist": {
        "domains": ["ai"],
        "intents": ["explanation", "question", "reasoning"],
        "provider": "agi",
        "confidence_boost": 0.1,
        "subtask_templates": [
            "Identify core question and key concepts",
            "Build analogies from familiar domains",
            "Explain step by step from simple to complex",
            "Summarize with a concrete example",
        ],
        "description": "Deep reasoning and explanation using AGI chain-of-thought",
    },
    "lmstudio-specialist": {
        "domains": [],
        "intents": ["explanation", "question", "coding", "creation"],
        "provider": "lmstudio",
        "confidence_boost": 0.05,
        "subtask_templates": [
            "Understand the query: identify key concepts and requirements",
            "Formulate response: structure thoughts logically and clearly",
            "Review: ensure accuracy, completeness, and helpful presentation",
        ],
        "description": "Local LM Studio inference for general-purpose reasoning and Q&A",
    },
    "summarizer-specialist": {
        "domains": [],
        "intents": ["summarize", "explanation", "question"],
        "provider": "agi",
        "confidence_boost": 0.05,
        "subtask_templates": [
            "Identify the key points and themes in the content",
            "Condense information, removing redundancy",
            "Produce a concise 2-3 sentence digest",
        ],
        "description": "Summarizes conversation history and event logs into compact digests",
    },
    "critique-specialist": {
        "domains": ["ai", "technical"],
        "intents": ["critique", "explanation", "question", "reasoning"],
        "provider": "agi",
        "confidence_boost": 0.08,
        "subtask_templates": [
            "Identify the evaluation criteria for the content",
            "Score accuracy, completeness, and clarity",
            "List concrete issues and improvement suggestions",
        ],
        "description": "Evaluates plans and responses against a quality rubric",
    },
    "reasoning-chain-specialist": {
        "domains": ["ai", "technical"],
        "intents": ["explanation", "question", "reasoning"],
        "provider": "agi",
        "confidence_boost": 0.12,
        "subtask_templates": [
            "Identify the core question and key concepts",
            "Break the problem into explicit reasoning steps",
            "Evaluate each step and surface assumptions",
            "Synthesise a confident conclusion from the chain",
        ],
        "description": "Multi-step chain-of-thought reasoning for complex questions",
    },
    "debate-specialist": {
        "domains": ["ai", "technical"],
        "intents": ["debate", "question", "reasoning"],
        "provider": "agi",
        "confidence_boost": 0.1,
        "subtask_templates": [
            "Identify the core claim or proposal",
            "Generate devil's advocate counter-arguments",
            "Surface structural weaknesses and edge cases",
            "Provide a steelmanned defence and overall verdict",
        ],
        "description": "Stress-tests ideas with counter-arguments and devil's advocate analysis",
    },
    "hypothesis-specialist": {
        "domains": ["ai", "technical"],
        "intents": ["hypothesize", "question", "reasoning"],
        "provider": "agi",
        "confidence_boost": 0.09,
        "subtask_templates": [
            "Identify observable patterns in the provided data or events",
            "Formulate 2–4 falsifiable hypotheses from those patterns",
            "Assign a rationale and testability flag to each hypothesis",
            "Summarise the dominant pattern in one sentence",
        ],
        "description": "Generates testable hypotheses from memory patterns and observations",
    },
    "reflection-specialist": {
        "domains": ["ai"],
        "intents": ["reflect", "question", "reasoning"],
        "provider": "agi",
        "confidence_boost": 0.11,
        "subtask_templates": [
            "Review recent autonomous execution cycle outcomes",
            "Extract key lessons and recurring failure patterns",
            "Recommend concrete behavioural adjustments",
            "Produce an executive summary of system learning",
        ],
        "description": "Produces meta-learning insights and retrospective analysis from cycle history",
    },
    "general": {
        "domains": [],
        "intents": [],
        "provider": "agi",
        "confidence_boost": 0.0,
        "subtask_templates": [
            "Understand the query",
            "Formulate a response",
            "Review for completeness",
        ],
        "description": "General-purpose AGI assistant",
    },
}


# ---------------------------------------------------------------------------
# Sanitization helpers
# ---------------------------------------------------------------------------
def _sanitize_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """Sanitize user input to reduce injection and control-char issues."""
    if not isinstance(text, str):
        return ""
    text = text[:max_length]
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def _sanitize_for_logging(text: str, max_length: int = 200) -> str:
    """Sanitize data before writing to logs."""
    if not isinstance(text, str):
        return "[invalid]"
    out = text[:max_length]
    if len(text) > max_length:
        out += "..."
    return html.escape(out)


def _infer_aria_movement_tag(query: str) -> Optional[str]:
    """Infer the best matching Aria movement tag from a user query."""
    query_lower = query.lower()
    if "left" in query_lower:
        return "[aria:walk:left]"
    if "right" in query_lower:
        return "[aria:walk:right]"
    if "up" in query_lower:
        return "[aria:walk:up]"
    if "down" in query_lower:
        return "[aria:walk:down]"
    if "jump" in query_lower:
        return "[aria:jump]"
    if "wave" in query_lower:
        return "[aria:wave]"
    if "dance" in query_lower:
        return "[aria:dance]"
    if "spin" in query_lower:
        return "[aria:spin]"
    if any(word in query_lower for word in ["move", "walk", "go", "run"]):
        return "[aria:idle]"
    return None


@dataclass
class ReasoningStep:
    """One step in an AGI reasoning chain.

    Parameters
    ----------
    step_type:
        Categorical label for this step.  Standard types are ``"analyze"``,
        ``"route"``, ``"decompose"``, ``"synthesize"``, ``"reflect"``, and
        ``"refine"``.  Custom step types are allowed for specialised use cases.
    content:
        Human-readable description of what this step concluded.
    confidence:
        A float in ``[0.0, 1.0]`` representing the provider's self-assessed
        confidence in this step.  Defaults to ``1.0``.
    metadata:
        Arbitrary key-value pairs for structured data produced by this step
        (e.g. the full query analysis dict for an ``"analyze"`` step).
    """

    step_type: str
    content: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AGIContext:
    """Bounded short-term memory for an ``AGIProvider`` instance.

    ``AGIContext`` implements the :class:`MemoryInterface` protocol, so it can
    be replaced by any object that satisfies that structural interface.

    Parameters
    ----------
    conversation_history:
        Ordered list of sanitized role messages seen in the current session.
        Bounded to ``max_history`` entries; system messages are preserved
        when older non-system messages are evicted.
    reasoning_chains:
        Ordered list of per-turn reasoning chains, bounded to
        ``MAX_REASONING_CHAINS``.
    goals:
        Active user-specified goals injected into the system prompt.  Bounded
        to ``MAX_GOALS`` entries.
    learned_patterns:
        Dictionary of routing observations used to improve agent selection
        over the course of a session.
    max_history:
        Maximum number of messages to retain.  Defaults to ``MAX_HISTORY_SIZE``.
    """

    conversation_history: List[RoleMessage] = field(default_factory=list)
    reasoning_chains: List[List[ReasoningStep]] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    max_history: int = MAX_HISTORY_SIZE

    def add_message(self, message: RoleMessage) -> None:
        """Append *message* to the conversation history after sanitisation.

        System messages are always preserved during eviction; the oldest
        non-system messages are dropped first when the history is full.

        Parameters
        ----------
        message:
            Dict with ``"role"`` and ``"content"`` keys.  Both values are
            sanitised before storage.
        """
        sanitized = {
            "role": _sanitize_input(str(message.get("role", "user")), max_length=20),
            "content": _sanitize_input(str(message.get("content", ""))),
        }
        self.conversation_history.append(sanitized)
        if len(self.conversation_history) > self.max_history:
            system_msgs = [
                m for m in self.conversation_history if m.get("role") == "system"
            ]
            other_msgs = [
                m for m in self.conversation_history if m.get("role") != "system"
            ]
            keep_count = max(0, self.max_history - len(system_msgs))
            self.conversation_history = system_msgs + other_msgs[-keep_count:]

    def add_reasoning_chain(self, chain: List[ReasoningStep]) -> None:
        """Persist *chain* and evict old chains when the cap is reached.

        Parameters
        ----------
        chain:
            Completed reasoning chain from one ``AGIProvider.complete`` call.
        """
        self.reasoning_chains.append(chain)
        if len(self.reasoning_chains) > MAX_REASONING_CHAINS:
            self.reasoning_chains = self.reasoning_chains[-MAX_REASONING_CHAINS:]

    def get_relevant_context(self, query: str) -> str:
        """Return a brief text summary of recent memory relevant to *query*.

        Includes the last six conversation turns and the first three active
        goals.  The query argument is sanitised but not used for retrieval in
        the default implementation (it is reserved for future semantic search).

        Parameters
        ----------
        query:
            The current user query (reserved for future retrieval use).

        Returns
        -------
        str
            Plain-text context snippet, or empty string when no context exists.
        """
        _ = _sanitize_input(query)
        parts: List[str] = []
        recent = self.conversation_history[-6:]
        if recent:
            parts.append("Recent conversation:")
            for msg in recent:
                role = _sanitize_for_logging(
                    str(msg.get("role", "unknown")), 20)
                content = _sanitize_for_logging(
                    str(msg.get("content", "")), 200)
                parts.append(f"  {role}: {content}")
        if self.goals:
            safe_goals = [_sanitize_for_logging(g, 50) for g in self.goals[:3]]
            parts.append(f"Active goals: {', '.join(safe_goals)}")
        return "\n".join(parts)


class AGIProvider(BaseChatProvider):
    """AGI-enhanced chat provider with reasoning, memory, and multi-agent routing.

    ``AGIProvider`` wraps any :class:`~chat_providers.BaseChatProvider` and
    adds a structured reasoning pipeline:

    1. **Query analysis** — classify intent, domain, and complexity.
    2. **Agent routing** — select the best specialist from ``_AGENT_REGISTRY``.
    3. **Task decomposition** — break complex queries into ordered subtasks.
    4. **Chain-of-thought synthesis** — generate domain-aware reasoning hints.
    5. **Self-reflection** — validate and patch the response (e.g. missing
       Aria movement tags).

    Parameters
    ----------
    base_provider:
        Underlying LLM provider.  When ``None`` the provider is auto-detected
        via :func:`~chat_providers.detect_provider` on first use.
    temperature:
        Sampling temperature forwarded to the base provider.  Agent-aware
        overrides are applied per specialist during response generation.
    max_output_tokens:
        Maximum token budget for generated responses.
    enable_chain_of_thought:
        Include chain-of-thought synthesis steps in the reasoning trace.
    enable_self_reflection:
        Validate and improve the generated response after synthesis.
    enable_task_decomposition:
        Break complex queries into subtasks before synthesis.
    reasoning_depth:
        Number of reasoning steps to generate, clamped to ``[1, 5]``.
    verbose:
        Prepend the formatted reasoning trace to each response.

    Examples
    --------
    Wrap any provider::

        from agi_provider import AGIProvider
        from chat_providers import detect_provider

        base, _ = detect_provider(explicit="local")
        agi = AGIProvider(base_provider=base, verbose=True)
        print(agi.complete([{"role": "user", "content": "Explain LoRA"}], stream=False))

    Auto-detect the best available provider::

        provider, info = create_agi_provider(temperature=0.4)
        response = provider.complete([{"role": "user", "content": "Hello"}], stream=False)
    """

    def __init__(
        self,
        base_provider: Optional[BaseChatProvider] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        enable_chain_of_thought: bool = True,
        enable_self_reflection: bool = True,
        enable_task_decomposition: bool = True,
        reasoning_depth: int = 3,
        verbose: bool = False,
    ) -> None:
        self.base_provider = base_provider
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.enable_chain_of_thought = enable_chain_of_thought
        self.enable_self_reflection = enable_self_reflection
        self.enable_task_decomposition = enable_task_decomposition
        self.reasoning_depth = min(max(1, reasoning_depth), 5)
        self.verbose = verbose
        self.context = AGIContext()
        self._base_provider_choice: Optional[ProviderChoice] = None
        self._last_agent_used: Optional[str] = None

    def _get_base_provider(self) -> BaseChatProvider:
        """Return the base provider, auto-detecting it on first call.

        The detected provider and its :class:`~chat_providers.ProviderChoice`
        are cached on the instance so subsequent calls are cheap.

        Returns
        -------
        BaseChatProvider
            The underlying LLM provider used for final response generation.
        """
        if self.base_provider is None:
            provider, choice = detect_provider(explicit="auto")
            self.base_provider = provider
            self._base_provider_choice = choice
        return self.base_provider

    def complete(
        self, messages: List[RoleMessage], stream: bool = True
    ) -> Iterable[str] | str:
        """Process *messages* through the AGI reasoning pipeline and return a response.

        The pipeline:

        1. Truncate ``messages`` to ``MAX_HISTORY_SIZE`` if needed.
        2. Deduplicate and add new messages to ``self.context``.
        3. Extract the latest user query.
        4. Run ``_reason`` to build the reasoning chain.
        5. Generate a response via the base provider (or a specialist).
        6. Optionally apply self-reflection.
        7. Store the chain and return the response, streaming if requested.

        Parameters
        ----------
        messages:
            Ordered conversation turn list.
        stream:
            When ``True`` yield tokens one by one; when ``False`` return the
            full response as a single ``str``.

        Returns
        -------
        Iterable[str] | str
            Streaming token generator or complete response string.
        """
        if len(messages) > MAX_HISTORY_SIZE:
            messages = messages[-MAX_HISTORY_SIZE:]
            _logger.warning(
                "Message count exceeded limit; truncating to %d", MAX_HISTORY_SIZE
            )

        existing = {m.get("content", "")
                    for m in self.context.conversation_history}
        for msg in messages:
            content = _sanitize_input(str(msg.get("content", "")))
            if content not in existing:
                self.context.add_message(
                    {"role": msg.get("role", "user"), "content": content}
                )
                existing.add(content)

        user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_query = _sanitize_input(str(msg.get("content", "")))
                break

        if not user_query.strip():
            text = "I'm ready to help. What would you like to discuss?"
            return self._stream_text(text) if stream else text

        try:
            reasoning_chain = self._reason(user_query, messages)
            response = self._generate_response(
                user_query, reasoning_chain, messages)
            if self.enable_self_reflection:
                response = self._reflect_and_improve(
                    user_query, response, reasoning_chain
                )
            self.context.add_reasoning_chain(reasoning_chain)
            # Persist reasoning chain to optional persistence backend (best-effort)
            if getattr(self, "persistence", None) is not None:
                try:
                    serialized_chain = []
                    for step in reasoning_chain:
                        serialized_chain.append(
                            {
                                "step_type": step.step_type,
                                "content": step.content,
                                "confidence": step.confidence,
                                "metadata": step.metadata,
                            }
                        )
                    meta = {"query": user_query,
                            "agent": self._last_agent_used, "ts": time.time()}
                    if hasattr(self.persistence, "write_reasoning_chain"):
                        self.persistence.write_reasoning_chain(
                            serialized_chain, meta)
                    elif hasattr(self.persistence, "add_reasoning_chain"):
                        self.persistence.add_reasoning_chain(serialized_chain)
                    elif hasattr(self.persistence, "write"):
                        try:
                            self.persistence.write("reasoning_chain", {
                                                   "chain": serialized_chain, "meta": meta})
                        except Exception:
                            pass
                except Exception as pers_exc:
                    _logger.exception(
                        "Failed to persist AGI reasoning chain: %s", _sanitize_for_logging(str(pers_exc)))
        except Exception as exc:
            _logger.error("AGI processing error: %s",
                          _sanitize_for_logging(str(exc)))
            response = self._generate_fallback_response(
                user_query, {"intent": "general", "domain": "general"}
            )

        return self._stream_text(response) if stream else response

    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Classify *query* by complexity, intent, and domain.

        Complexity classification (from repository instructions):

        * ``"complex"`` — more than 30 words, or contains keywords
          ``implement``, ``architect``, ``debug``, ``refactor``, or phrases
          ``step by step``, ``detailed``, ``comprehensive``.
        * ``"simple"`` — fewer than 10 words with no complex keywords.
        * ``"moderate"`` — everything else.

        Intent categories:
            ``movement``, ``coding``, ``reasoning``, ``explanation``,
            ``creation``, ``question``, ``general``.

        Domain categories:
            ``quantum``, ``aria``, ``ai``, ``technical``, ``general``.

        Parameters
        ----------
        query:
            Raw user query string (should already be sanitised by the caller).

        Returns
        -------
        Dict[str, Any]
            A dict with keys: ``query``, ``complexity``, ``intent``,
            ``domain``, ``word_count``, ``has_question``, ``confidence``,
            ``summary``.
        """
        query_lower = query.lower()
        words = query.split()
        word_count = len(words)

        # Complexity policy from repo instructions.
        complex_keywords = ("implement", "architect", "debug", "refactor")
        complex_phrases = ("step by step", "detailed", "comprehensive")
        if (
            word_count > 30
            or any(k in query_lower for k in complex_keywords)
            or any(p in query_lower for p in complex_phrases)
        ):
            complexity = "complex"
        elif word_count < 10 and not any(k in query_lower for k in complex_keywords):
            complexity = "simple"
        else:
            complexity = "moderate"

        intent = "general"
        if any(
            w in query_lower for w in ["move", "walk", "jump", "dance", "wave", "spin"]
        ):
            intent = "movement"
        elif any(
            w in query_lower
            for w in ["code", "function", "class", "debug", "refactor", "implement"]
        ):
            intent = "coding"
        elif any(
            p in query_lower
            for p in [
                "reason about",
                "think through",
                "step by step",
                "analyze step",
                "break down",
                "explain your reasoning",
                "chain of thought",
                "agi reasoning",
                "use agi reasoning",
                "autonomous planning",
            ]
        ):
            intent = "reasoning"
        elif any(
            p in query_lower
            for p in ["summarize", "condense", "digest", "tl;dr", "brief summary", "compress this"]
        ):
            intent = "summarize"
        elif any(
            p in query_lower
            for p in ["debate", "counter-argument", "steelman", "argue against", "challenge this", "devil's advocate"]
        ):
            intent = "debate"
        elif any(
            p in query_lower
            for p in ["critique", "evaluate this", "assess quality", "score this", "review this", "assess this"]
        ):
            intent = "critique"
        elif any(
            p in query_lower
            for p in ["hypothesis", "hypothesize", "generate hypothes", "infer from patterns", "what patterns"]
        ):
            intent = "hypothesize"
        elif any(
            p in query_lower
            for p in ["reflect on", "retrospect", "lessons learned", "what did we learn", "meta-learn"]
        ):
            intent = "reflect"
        elif any(
            p in query_lower
            for p in ["what is", "explain", "how does", "define", "describe"]
        ):
            intent = "explanation"
        elif any(
            w in query_lower for w in ["create", "build", "generate", "write", "design"]
        ):
            intent = "creation"
        elif "?" in query:
            intent = "question"

        domain = "general"
        if any(
            w in query_lower
            for w in ["quantum", "qubit", "entanglement", "qiskit", "pennylane"]
        ):
            domain = "quantum"
        elif any(w in query_lower for w in ["aria", "avatar", "gesture", "animation"]):
            domain = "aria"
        elif (
            re.search(r"\b(?:ai|agi)\b", query_lower) is not None
            or any(
                w in query_lower
                for w in [
                "llm",
                "transformer",
                "lora",
                "training",
                "fine-tun",
                "neural network",
                "machine learning",
                "deep learning",
                "embeddings",
                "tokenizer",
                "inference",
                "model weights",
                ]
            )
        ):
            domain = "ai"
        elif any(
            w in query_lower
            for w in [
                "api",
                "database",
                "sql",
                "http",
                "endpoint",
                "code",
                "python",
                "function",
                "class",
                "debug",
                "refactor",
                "implement",
            ]
        ):
            domain = "technical"

        if intent == "movement" and domain == "general":
            domain = "aria"

        return {
            "query": query,
            "complexity": complexity,
            "intent": intent,
            "domain": domain,
            "word_count": word_count,
            "has_question": "?" in query,
            "confidence": 0.8 if complexity == "simple" else 0.65,
            "summary": f"{complexity.capitalize()} {intent} query about {domain}",
        }

    # ------------------------------------------------------------------
    # Multi-agent routing
    # ------------------------------------------------------------------

    def _select_agent(self, analysis: Dict[str, Any]) -> tuple:
        """Select the best specialist agent based on query analysis.

        Scores each non-fallback agent by domain match, intent match, and a
        confidence-weighted boost factor.  Also incorporates previously learned
        routing patterns stored in ``context.learned_patterns`` to reinforce
        successful agent assignments for the same domain+intent signature.

        A time-decay factor is applied to the learned-pattern bonus so that
        stale observations contribute progressively less weight.  The half-life
        is 24 hours: ``decay = 0.5 ** (age_hours / 24)``.

        Returns a ``(agent_name, score)`` tuple where *score* is the winning
        match score (0.0 for the general fallback).
        """
        import math
        import time

        intent = analysis.get("intent", "general")
        domain = analysis.get("domain", "general")
        confidence = analysis.get("confidence", 0.5)

        # Retrieve past routing pattern for this domain+intent, if any.
        pattern_key = f"routing_{domain}_{intent}"
        learned = self.context.learned_patterns.get(pattern_key)
        learned_agent = learned.get("agent") if learned else None
        if learned:
            count = learned.get("count", 1)
            last_seen = learned.get("last_seen")
            if last_seen:
                age_hours = (time.time() - last_seen) / 3600.0
                decay = 0.5 ** (age_hours / 24.0)  # 24 h half-life
            else:
                decay = 1.0
            learned_weight = min(0.15, 0.05 * math.log(count + 1)) * decay
        else:
            learned_weight = 0.0

        best_agent = "general"
        best_score = 0.0

        for agent_name, agent_config in _AGENT_REGISTRY.items():
            if agent_name == "general":
                continue
            score = 0.0
            if domain in agent_config.get("domains", []):
                score += 0.5
            if intent in agent_config.get("intents", []):
                score += 0.3
            # Only apply confidence boost when there is at least one domain or
            # intent match — prevents pure-boost wins on general queries.
            if score > 0.0:
                score += agent_config.get("confidence_boost", 0.0) * confidence
                # Learned pattern bonus for agents that previously handled this signature.
                if agent_name == learned_agent:
                    score += learned_weight
            if score > best_score:
                best_score = score
                best_agent = agent_name

        _logger.debug(
            "Agent selected: %s (score=%.3f, domain=%s, intent=%s, learned=%s)",
            best_agent,
            best_score,
            domain,
            intent,
            learned_agent,
        )
        return best_agent, best_score

    def _dispatch_to_agent(
        self, query: str, agent_name: str, analysis: Dict[str, Any]
    ) -> Optional[str]:
        """Try to route *query* to a specialist provider.

        Returns the agent's reply as a plain string, or ``None`` when the
        specialist is unavailable (falls back to AGI processing).
        """
        if not query or not str(query).strip():
            _logger.warning(
                "Agent dispatch to %s: empty query provided", agent_name)
            return None

        config = _AGENT_REGISTRY.get(agent_name, {})
        provider_name = config.get("provider", "agi")

        if provider_name in ("agi", ""):
            return None  # let AGI handle it directly

        model_override: Optional[str] = None
        if provider_name == "quantum":
            model_override = self._resolve_quantum_model_path(analysis)
            if not model_override:
                analysis["quantum_backend_ready"] = False
                _logger.info(
                    "Agent dispatch skipped for %s: quantum model path not configured",
                    agent_name,
                )
                return None
            analysis["quantum_backend_ready"] = True
            analysis["quantum_model_path"] = model_override

        try:
            specialist, choice = detect_provider(
                explicit=provider_name,
                model_override=model_override,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
            )
            if choice.name != provider_name:
                _logger.debug(
                    "Agent dispatch skipped for %s: requested provider=%s resolved to %s",
                    agent_name,
                    provider_name,
                    choice.name,
                )
                return None
            messages = [{"role": "user", "content": query}]
            result = specialist.complete(messages, stream=False)
            response = result if isinstance(result, str) else "".join(result)
            _logger.debug("Agent dispatch: %s → %s chars",
                          agent_name, len(response))
            return response
        except Exception as exc:
            _logger.debug(
                "Agent dispatch to %s failed: %s",
                agent_name,
                _sanitize_for_logging(str(exc)),
            )
            return None  # fall back to AGI

    def _resolve_quantum_model_path(self, analysis: Dict[str, Any]) -> Optional[str]:
        """Resolve the quantum model path for quantum-specialist dispatch.

        Resolution order:
        1. ``analysis["quantum_model_path"]``
        2. ``analysis["model_path"]``
        3. ``QAI_QUANTUM_MODEL_PATH`` environment variable
        4. ``QAI_QUANTUM_MODEL`` environment variable
        5. ``ARIA_QUANTUM_MODEL_PATH`` environment variable
        """
        candidates = (
            analysis.get("quantum_model_path"),
            analysis.get("model_path"),
            os.getenv("QAI_QUANTUM_MODEL_PATH"),
            os.getenv("QAI_QUANTUM_MODEL"),
            os.getenv("ARIA_QUANTUM_MODEL_PATH"),
        )
        for candidate in candidates:
            if isinstance(candidate, str):
                stripped = candidate.strip()
                if stripped:
                    return stripped
        return None

    def _decompose_task(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """Break *query* into an ordered list of subtasks for the reasoning trace.

        Subtasks are taken from the selected agent's ``subtask_templates`` in
        ``_AGENT_REGISTRY`` when available; otherwise a generic template is
        chosen based on the detected intent.

        The returned list is capped to ``self.reasoning_depth`` entries.

        Parameters
        ----------
        query:
            The user query (not used in the default implementation — the
            ``analysis`` dict contains all required information).
        analysis:
            Output of ``_analyze_query``.  Must include ``"intent"`` and
            optionally ``"selected_agent"``.

        Returns
        -------
        List[str]
            Ordered subtask descriptions, bounded by ``self.reasoning_depth``.
        """
        _ = query
        # First try to pull subtask templates from the selected agent's registry entry.
        selected_agent = analysis.get("selected_agent")
        if selected_agent and selected_agent in _AGENT_REGISTRY:
            templates = _AGENT_REGISTRY[selected_agent].get(
                "subtask_templates", [])
            if templates:
                return templates[: self.reasoning_depth]

        intent = analysis.get("intent", "general")
        if intent == "coding":
            steps = [
                "Understand requirements",
                "Design approach",
                "Implement core logic",
                "Handle edge cases",
                "Test and validate",
            ]
        elif intent == "explanation":
            steps = [
                "Define key concept",
                "Give examples",
                "Explain relationships",
                "Summarize clearly",
            ]
        elif intent == "creation":
            steps = [
                "Clarify constraints",
                "Outline structure",
                "Create output",
                "Review and polish",
            ]
        elif intent == "question":
            steps = [
                "Answer directly",
                "Provide context",
                "Add example",
                "Summarize",
            ]
        else:
            steps = [
                "Understand request",
                "Gather context",
                "Draft response",
                "Verify answer",
            ]
        return steps[: self.reasoning_depth]

    def _chain_of_thought(
        self, query: str, analysis: Dict[str, Any], messages: List[RoleMessage]
    ) -> List[str]:
        """Generate domain-aware chain-of-thought reasoning hints.

        Produces a list of natural-language reasoning statements that are
        injected into the AGI system prompt to steer the base provider toward
        a well-structured response.

        The list is bounded by ``self.reasoning_depth``.

        Parameters
        ----------
        query:
            The user query; used to retrieve relevant memory context.
        analysis:
            Output of ``_analyze_query``.
        messages:
            Full conversation turn list (reserved for future contextual use).

        Returns
        -------
        List[str]
            Ordered reasoning hints, bounded by ``self.reasoning_depth``.
        """
        _ = messages
        summary = analysis.get(
            "summary",
            f"{analysis.get('complexity', 'simple').capitalize()} {analysis.get('intent', 'general')} query about {analysis.get('domain', 'general')}",
        )
        thoughts = [f"Understanding: {summary}"]

        # Domain-specific reasoning hints.
        domain = analysis.get("domain", "general")
        if domain == "aria":
            thoughts.append(
                "Aria context: include movement/action tags when appropriate."
            )
        elif domain == "quantum":
            thoughts.append(
                "Quantum context: distinguish simulator vs hardware where relevant."
            )
        elif domain == "ai":
            thoughts.append(
                "AI/ML context: distinguish training, inference, and evaluation concerns."
            )
        elif domain == "technical":
            thoughts.append(
                "Technical context: prefer concrete, runnable code examples."
            )

        # Surface which specialist will handle this query.
        selected_agent = analysis.get("selected_agent")
        if selected_agent and selected_agent != "general":
            agent_desc = _AGENT_REGISTRY.get(selected_agent, {}).get(
                "description", selected_agent
            )
            thoughts.append(f"Specialist: {agent_desc}")

        context_hint = self.context.get_relevant_context(query)
        if context_hint:
            thoughts.append("Considering recent conversation context.")
        thoughts.append(
            f"Approach: provide a {analysis['complexity']}-appropriate response."
        )
        return thoughts[: self.reasoning_depth]

    def _reason(self, query: str, messages: List[RoleMessage]) -> List[ReasoningStep]:
        """Build the full reasoning chain for *query*.

        Executes the reasoning pipeline in order:

        1. ``_analyze_query`` — classify intent, domain, and complexity.
        2. ``_select_agent`` — pick the best specialist from the registry.
        3. (optional) ``_decompose_task`` — generate subtasks for complex queries.
        4. (optional) ``_chain_of_thought`` — generate domain-aware hints.

        The chain is stored in ``self.context`` by the caller (``complete``).

        Parameters
        ----------
        query:
            Sanitised user query extracted from *messages*.
        messages:
            Full conversation history for context retrieval.

        Returns
        -------
        List[ReasoningStep]
            Ordered reasoning steps ready for system-prompt injection and
            verbose display.
        """
        chain: List[ReasoningStep] = []
        analysis = self._analyze_query(query)

        # Multi-agent: pick the best specialist for this query and record it.
        selected_agent, agent_score = self._select_agent(analysis)
        analysis["selected_agent"] = selected_agent
        analysis["agent_score"] = round(agent_score, 3)
        self._last_agent_used = selected_agent

        chain.append(
            ReasoningStep(
                step_type="analyze",
                content=analysis["summary"],
                confidence=analysis["confidence"],
                metadata=analysis,
            )
        )

        # Add an agent-selection step so the reasoning trace is transparent.
        agent_desc = _AGENT_REGISTRY.get(selected_agent, {}).get(
            "description", selected_agent
        )
        chain.append(
            ReasoningStep(
                step_type="route",
                content=f"Routing to: {selected_agent} — {agent_desc}",
                metadata={"agent": selected_agent},
            )
        )

        if self.enable_task_decomposition and analysis["complexity"] == "complex":
            subtasks = self._decompose_task(query, analysis)
            chain.append(
                ReasoningStep(
                    step_type="decompose",
                    content=f"Subtasks: {', '.join(subtasks)}",
                    metadata={"subtasks": subtasks},
                )
            )

        if self.enable_chain_of_thought:
            for thought in self._chain_of_thought(query, analysis, messages):
                chain.append(ReasoningStep(
                    step_type="synthesize", content=thought))

        return chain

    def _build_agi_system_prompt(
        self, analysis: Dict[str, Any], reasoning_chain: List[ReasoningStep]
    ) -> str:
        intent = analysis.get("intent", "general")
        domain = analysis.get("domain", "general")
        complexity = analysis.get("complexity", "simple")
        selected_agent = analysis.get("selected_agent", "general")

        lines = [
            "You are Aria, an intelligent assistant with structured reasoning.",
            "Be accurate, helpful, and concise.",
        ]

        # Agent-specific persona guidance injected before generic rules
        if selected_agent == "quantum-specialist":
            lines += [
                "You are acting as the Quantum Specialist.",
                "Always distinguish between quantum simulation and real hardware execution.",
                "Use proper notation (|0⟩, |1⟩, ⊗, unitary matrices) where helpful.",
                "Prefer Qiskit/Pennylane examples unless another framework is mentioned.",
            ]
        elif selected_agent == "code-specialist":
            lines += [
                "You are acting as the Code Specialist.",
                "Provide complete, runnable code. Include relevant imports.",
                "Prefer Python unless another language is explicitly requested.",
                "Briefly explain non-obvious logic after the code block.",
            ]
        elif selected_agent == "aria-character":
            lines += [
                "You are acting as the Aria Character Specialist.",
                "For movement/gesture requests include tags like:",
                "[aria:walk:left], [aria:walk:right], [aria:walk:up], [aria:walk:down],"
                " [aria:jump], [aria:wave], [aria:dance], [aria:spin], [aria:idle]",
                "Describe character actions in present tense, vivid but brief.",
            ]
        elif selected_agent == "ai-specialist":
            lines += [
                "You are acting as the AI/ML Specialist.",
                "Cover both theoretical intuition and practical implementation.",
                "Cite standard libraries (PyTorch, Transformers, PEFT) when relevant.",
                "When discussing LoRA: mention rank, alpha, target_modules, and adapter merging.",
            ]
        elif selected_agent == "reasoning-specialist":
            lines += [
                "You are acting as the Reasoning Specialist.",
                "Think step-by-step. Show your intermediate reasoning before the final answer.",
                "Use structured formats (numbered lists, tables) for multi-step logic.",
            ]
        elif selected_agent == "summarizer-specialist":
            lines += [
                "You are acting as the Summarizer Specialist.",
                "Produce a concise, accurate summary. Omit redundant detail.",
                "Lead with the most important takeaway, then add supporting points.",
                "Target 2–4 sentences unless more detail is explicitly requested.",
            ]
        elif selected_agent == "critique-specialist":
            lines += [
                "You are acting as the Critique Specialist.",
                "Evaluate the content against accuracy, completeness, and clarity.",
                "List concrete issues as bullet points, then provide improvement suggestions.",
                "Assign an overall quality score (0–1) and justify it briefly.",
            ]
        elif selected_agent == "reasoning-chain-specialist":
            lines += [
                "You are acting as the Reasoning Chain Specialist.",
                "Break the problem into explicit, numbered reasoning steps.",
                "State your assumptions clearly before each step.",
                "Conclude with a confident answer synthesised from the chain.",
            ]
        elif selected_agent == "debate-specialist":
            lines += [
                "You are acting as the Debate Specialist.",
                "Generate strong counter-arguments and identify structural weaknesses.",
                "Include a steelmanned defence of the strongest opposing position.",
                "Close with a balanced verdict that acknowledges both sides.",
            ]
        elif selected_agent == "hypothesis-specialist":
            lines += [
                "You are acting as the Hypothesis Specialist.",
                "Identify observable patterns and formulate 2–4 falsifiable hypotheses.",
                "Each hypothesis must include a rationale and a testability assessment.",
                "Summarise the dominant pattern in one sentence at the end.",
            ]
        elif selected_agent == "reflection-specialist":
            lines += [
                "You are acting as the Reflection Specialist.",
                "Analyse past outcomes to extract key lessons and recurring patterns.",
                "Recommend concrete, actionable behavioural adjustments.",
                "Close with a one-sentence executive summary of the overall insight.",
            ]
        else:
            # General / fallback — keep existing aria domain guidance
            if domain == "aria":
                lines.extend(
                    [
                        "For movement/gesture requests include tags like:",
                        "[aria:walk:left], [aria:walk:right], [aria:walk:up], [aria:walk:down], [aria:jump], [aria:wave], [aria:dance], [aria:spin], [aria:idle]",
                    ]
                )

        if intent == "coding" and selected_agent not in (
            "code-specialist",
            "quantum-specialist",
        ):
            lines.append(
                "For coding responses: include practical, runnable snippets when asked."
            )
        elif intent == "explanation":
            lines.append(
                "For explanations: define terms clearly, then build depth gradually."
            )

        if complexity == "complex":
            lines.append(
                "Structure the answer with clear sections and a concise summary."
            )

        for step in reasoning_chain:
            if step.step_type == "decompose":
                subtasks = step.metadata.get("subtasks", [])
                if subtasks:
                    lines.append("Suggested steps:")
                    lines.extend([f"- {t}" for t in subtasks])
                break

        return "\n".join(lines)

    def _generate_response(
        self,
        query: str,
        reasoning_chain: List[ReasoningStep],
        messages: List[RoleMessage],
    ) -> str:
        analysis: Dict[str, Any] = {}
        for step in reasoning_chain:
            if step.step_type == "analyze":
                analysis = step.metadata
                break

        # --- Multi-agent dispatch: try the selected specialist first. ---
        selected_agent = analysis.get("selected_agent", "general")
        if selected_agent and selected_agent != "general":
            specialist_response = self._dispatch_to_agent(
                query, selected_agent, analysis
            )
            if specialist_response is not None:
                if self.verbose and reasoning_chain:
                    specialist_response = f"{self._format_reasoning_chain(reasoning_chain)}\n\n---\n\n{specialist_response}"
                return specialist_response

        # Specialist unavailable or returned None — fall back to AGI base provider.
        system_prompt = self._build_agi_system_prompt(
            analysis, reasoning_chain)
        enhanced_messages: List[RoleMessage] = [
            {"role": "system", "content": system_prompt}
        ]

        for msg in messages:
            if msg.get("role") != "system":
                enhanced_messages.append(msg)
            else:
                enhanced_messages[0][
                    "content"
                ] += f"\n\nAdditional context: {msg.get('content', '')}"

        try:
            provider = self._get_base_provider()
            # Apply agent-aware temperature: deterministic domains run cooler.
            _AGENT_TEMPERATURES: Dict[str, float] = {
                "quantum-specialist": 0.3,
                "code-specialist": 0.2,
                "ai-specialist": 0.5,
                "aria-character": 0.8,
                "reasoning-specialist": 0.4,
                "summarizer-specialist": 0.3,
                "critique-specialist": 0.4,
                "reasoning-chain-specialist": 0.3,
                "debate-specialist": 0.6,
                "hypothesis-specialist": 0.5,
                "reflection-specialist": 0.4,
            }
            original_temp = getattr(provider, "temperature", None)
            if selected_agent in _AGENT_TEMPERATURES:
                try:
                    provider.temperature = _AGENT_TEMPERATURES[selected_agent]
                except AttributeError:
                    pass  # provider is immutable — skip
            result = provider.complete(enhanced_messages, stream=False)
            # Restore original temperature so state doesn't leak.
            if original_temp is not None:
                try:
                    provider.temperature = original_temp
                except AttributeError:
                    pass
            response = result if isinstance(result, str) else "".join(result)
        except Exception as exc:
            _logger.error("Base provider error: %s",
                          _sanitize_for_logging(str(exc)))
            response = self._generate_fallback_response(query, analysis)

        # Record a routing pattern so future queries benefit from history.
        self._learn_from_routing(analysis, selected_agent)

        if self.verbose and reasoning_chain:
            response = (
                f"{self._format_reasoning_chain(reasoning_chain)}\n\n---\n\n{response}"
            )
        return response

    def _learn_from_routing(self, analysis: Dict[str, Any], agent_used: str) -> None:
        """Record successful routing decisions as learned patterns.

        Stores `(domain, intent) → agent` mappings in ``context.learned_patterns``
        so that future calls with the same domain+intent signature can be
        resolved with increased confidence.  Only non-general routings are
        stored to avoid polluting the pattern store with uninformative data.

        Each pattern entry records a ``last_seen`` Unix timestamp so that
        `_select_agent` can apply time-decay to older observations.
        """

        if agent_used == "general":
            return
        domain = analysis.get("domain", "general")
        intent = analysis.get("intent", "general")
        pattern_key = f"routing_{domain}_{intent}"
        now = time.time()
        existing = self.context.learned_patterns.get(pattern_key)
        if existing is None:
            self.context.learned_patterns[pattern_key] = {
                "agent": agent_used,
                "domain": domain,
                "intent": intent,
                "count": 1,
                "last_seen": now,
            }
        else:
            # If a different agent somehow wins for the same signature, reset to this winner.
            if existing.get("agent") != agent_used:
                existing["agent"] = agent_used
                existing["count"] = 1
            else:
                existing["count"] = existing.get("count", 0) + 1
            existing["last_seen"] = now

    def _generate_fallback_response(self, query: str, analysis: Dict[str, Any]) -> str:
        """Generate a canned fallback response when the base provider is unavailable.

        For Aria movement queries the appropriate ``[aria:…]`` tag is included.
        For questions a brief apology noting fallback mode is returned.  All
        other queries receive a generic request for more information.

        Parameters
        ----------
        query:
            The user query, used to infer an Aria movement tag.
        analysis:
            Output of ``_analyze_query`` (must include ``"intent"`` and
            ``"domain"``).

        Returns
        -------
        str
            A self-contained fallback response string.
        """
        intent = analysis.get("intent", "general")
        domain = analysis.get("domain", "general")

        if intent == "movement" and domain == "aria":
            tag = _infer_aria_movement_tag(query)
            if tag == "[aria:walk:left]":
                return "I'll move to the left! [aria:walk:left]"
            if tag == "[aria:walk:right]":
                return "Moving to the right! [aria:walk:right]"
            if tag == "[aria:walk:up]":
                return "Moving up! [aria:walk:up]"
            if tag == "[aria:walk:down]":
                return "Moving down! [aria:walk:down]"
            if tag == "[aria:jump]":
                return "Here I go! [aria:jump]"
            if tag == "[aria:wave]":
                return "Hello there! [aria:wave]"
            if tag == "[aria:dance]":
                return "Time to dance! [aria:dance]"
            if tag == "[aria:spin]":
                return "Spinning now! [aria:spin]"
            return "I'm ready to move! [aria:idle]"

        if analysis.get("has_question"):
            return (
                "Great question. I'm currently in fallback mode, but I can still help with "
                "Aria actions, coding guidance, and general explanations."
            )

        return "I understand your request. Tell me more and I'll help."

    def _reflect_and_improve(
        self, query: str, response: str, reasoning_chain: List[ReasoningStep]
    ) -> str:
        """Validate *response* and apply targeted improvements.

        Reflection checks performed:

        * **Length check** — flags complex responses that are too short
          (< 50 words) or simple responses that are too long (> 300 words).
        * **Aria tag injection** — when the query intent is ``"movement"`` and
          the domain is ``"aria"``, appends the appropriate ``[aria:…]`` tag
          if one is absent from the response.

        All identified issues are recorded in ``context.learned_patterns`` for
        diagnostic inspection via ``get_reasoning_summary()``.

        Parameters
        ----------
        query:
            The original user query, used to infer the Aria movement tag.
        response:
            The generated response string to validate and potentially modify.
        reasoning_chain:
            The reasoning chain for this turn; the ``"analyze"`` step's
            metadata is used to retrieve intent, domain, and complexity.

        Returns
        -------
        str
            The (possibly modified) response string.
        """
        issues: List[str] = []
        analysis: Dict[str, Any] = {}
        for step in reasoning_chain:
            if step.step_type == "analyze":
                analysis = step.metadata
                break

        complexity = analysis.get("complexity", "simple")
        word_count = len(response.split())
        if complexity == "complex" and word_count < 50:
            issues.append("response_too_short")
        elif complexity == "simple" and word_count > 300:
            issues.append("response_too_long")

        if (
            analysis.get("intent") == "movement"
            and analysis.get("domain") == "aria"
            and "[aria:" not in response
        ):
            tag = _infer_aria_movement_tag(query) or "[aria:idle]"
            response += f" {tag}"
            issues.append("aria_tag_injected")

        if issues:
            self.context.learned_patterns[
                f"reflection_{len(self.context.reasoning_chains)}"
            ] = {
                "issues": issues,
                "query_type": analysis.get("intent"),
                "improvements_applied": True,
            }

        return response

    def _format_reasoning_chain(self, chain: List[ReasoningStep]) -> str:
        parts = ["🧠 **AGI Reasoning Process**", ""]
        icons = {
            "analyze": "🔍",
            "decompose": "📋",
            "route": "🧭",
            "synthesize": "💡",
            "reflect": "🪞",
            "refine": "✨",
        }
        for i, step in enumerate(chain, 1):
            parts.append(
                f"{icons.get(step.step_type, '•')} Step {i} ({step.step_type}): {step.content}"
            )
        return "\n".join(parts)

    def _stream_text(self, text: str) -> Generator[str, None, None]:
        words = text.split()
        if len(words) < 20:
            for ch in text:
                yield ch
                time.sleep(0.012)
            return

        delay = max(0.002, min(0.018, 0.8 / (len(words) + 10)))
        for i, word in enumerate(words):
            yield word if i == 0 else " " + word
            time.sleep(delay)

    def set_goal(self, goal: str) -> None:
        """Add *goal* to the active goals list, enforcing the per-session cap.

        Duplicate goals are silently ignored.  When the list exceeds
        ``MAX_GOALS`` the oldest goal is evicted.  Empty or whitespace-only
        strings are rejected.

        Parameters
        ----------
        goal:
            A free-text goal description.  Sanitised and truncated to 200
            characters before storage.
        """
        safe_goal = _sanitize_input(str(goal), max_length=200).strip()
        if not safe_goal:
            return
        if safe_goal not in self.context.goals:
            self.context.goals.append(safe_goal)
            if len(self.context.goals) > MAX_GOALS:
                self.context.goals = self.context.goals[-MAX_GOALS:]

    def clear_goals(self) -> None:
        """Remove all active goals from the context."""
        self.context.goals.clear()

    def get_reasoning_summary(self) -> Dict[str, Any]:
        """Return a structured summary of the provider's current state.

        Useful for monitoring, debugging, and observability dashboards.

        Returns
        -------
        Dict[str, Any]
            Keys:

            * ``total_reasoning_chains`` — number of completed reasoning chains
              stored in context (max ``MAX_REASONING_CHAINS``).
            * ``active_goals`` — copy of the current goals list.
            * ``learned_patterns_count`` — total entries in
              ``context.learned_patterns``.
            * ``top_learned_patterns`` — up to five routing patterns sorted by
              observation count (descending).
            * ``conversation_length`` — number of messages in the history.
            * ``last_agent_used`` — name of the agent used in the last call.
            * ``last_agent_score`` — routing confidence score from the last
              call's ``"analyze"`` step, or ``None``.
            * ``available_agents`` — list of all registered agent names.
        """
        last_agent_score: Optional[float] = None
        if self.context.reasoning_chains:
            last_chain = self.context.reasoning_chains[-1]
            for step in last_chain:
                if step.step_type == "analyze":
                    last_agent_score = step.metadata.get("agent_score")
                    break

        # Top learned routing patterns (by observation count, routing only).
        routing_patterns = [
            v
            for v in self.context.learned_patterns.values()
            if isinstance(v, dict) and "agent" in v and "count" in v
        ]
        top_patterns = sorted(
            routing_patterns, key=lambda p: p.get("count", 0), reverse=True
        )[:5]

        return {
            "total_reasoning_chains": len(self.context.reasoning_chains),
            "active_goals": self.context.goals.copy(),
            "learned_patterns_count": len(self.context.learned_patterns),
            "top_learned_patterns": top_patterns,
            "conversation_length": len(self.context.conversation_history),
            "last_agent_used": self._last_agent_used,
            "last_agent_score": last_agent_score,
            "available_agents": list(_AGENT_REGISTRY.keys()),
        }

    async def async_complete(
        self, messages: List[RoleMessage], stream: bool = False
    ) -> str:
        """Asynchronous variant of :meth:`complete` for use in async contexts.

        Delegates to the synchronous ``complete`` implementation via
        :func:`asyncio.to_thread` so that blocking I/O in the base provider
        does not stall the event loop.  Streaming is disabled by default
        because async callers typically await a complete response; pass
        ``stream=True`` only when the caller can iterate the generator in a
        thread context.

        Parameters
        ----------
        messages:
            Ordered conversation turn list.
        stream:
            Passed through to ``complete``.  Defaults to ``False`` — callers
            expecting a generator should set this to ``True`` and consume the
            result appropriately.

        Returns
        -------
        str
            The complete response string.  When ``stream=True`` the generator
            is consumed internally and returned as a joined string.

        Examples
        --------
        ::

            import asyncio
            from agi_provider import AGIProvider

            async def main():
                agi = AGIProvider()
                response = await agi.async_complete(
                    [{"role": "user", "content": "Hello"}]
                )
                print(response)

            asyncio.run(main())
        """
        result = await asyncio.to_thread(self.complete, messages, stream)
        if isinstance(result, str):
            return result
        return "".join(result)


def create_agi_provider(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    verbose: bool = False,
    **kwargs: Any,
) -> tuple[AGIProvider, ProviderChoice]:
    """Create an :class:`AGIProvider` wrapping the best available base provider.

    Auto-detects the base provider using :func:`~chat_providers.detect_provider`
    with ``explicit="auto"``.  If detection fails the provider is created
    without a pre-loaded base provider (it will be auto-detected on the first
    ``complete`` call).

    Parameters
    ----------
    model:
        Optional model name override forwarded to the base provider.
    temperature:
        Sampling temperature (defaults to ``0.7`` when ``None``).
    max_output_tokens:
        Maximum token budget (defaults to ``2048`` when ``None``).
    verbose:
        When ``True`` the reasoning trace is prepended to each response.
    **kwargs:
        Additional keyword arguments forwarded to :class:`AGIProvider`.

    Returns
    -------
    tuple[AGIProvider, ProviderChoice]
        A ``(provider, info)`` pair.  ``info.name`` is always ``"agi"``;
        ``info.model`` encodes the underlying base provider and model name,
        e.g. ``"agi-openai-gpt-4"``.

    Examples
    --------
    ::

        provider, info = create_agi_provider(temperature=0.4, verbose=True)
        response = provider.complete(
            [{"role": "user", "content": "Explain LoRA fine-tuning"}],
            stream=False,
        )
    """
    base_provider = None
    base_choice = None

    try:
        base_provider, base_choice = detect_provider(
            explicit="auto",
            model_override=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
    except Exception:
        base_provider = None
        base_choice = None

    provider = AGIProvider(
        base_provider=base_provider,
        temperature=temperature or 0.7,
        max_output_tokens=max_output_tokens or 2048,
        verbose=verbose,
        **kwargs,
    )

    def _ensure_parent_dir(path: str) -> None:
        """Create a parent directory for file-backed persistence paths.

        Safely no-ops for in-memory SQLite markers and URI-style strings.
        """
        raw = (path or "").strip()
        if not raw:
            return
        if raw in {":memory:", "file::memory:?cache=shared"}:
            return
        if "://" in raw:
            return
        parent = os.path.dirname(os.path.abspath(raw))
        if parent:
            os.makedirs(parent, exist_ok=True)

    # Optionally attach a persistence backend if configured via environment.
    persist_enabled = os.getenv(
        "QAI_AGI_PERSIST", "").lower() in ("1", "true", "yes")
    jsonl_path = os.getenv("QAI_AGI_PERSIST_PATH")
    sqlite_path = os.getenv("QAI_AGI_PERSIST_DB") or os.getenv(
        "QAI_AGI_PERSIST_SQLITE")
    if sqlite_path:
        try:
            from shared.agi_persistence_sqlite import SQLiteAGIPersistence

            path = sqlite_path
            _ensure_parent_dir(path)
            provider.persistence = SQLiteAGIPersistence(path)
        except Exception as exc:  # pragma: no cover - best-effort persistence
            _logger.exception(
                "Failed to initialise SQLite AGI persistence backend: %s",
                _sanitize_for_logging(str(exc)),
            )
            provider.persistence = None
    elif persist_enabled or jsonl_path:
        try:
            from shared.agi_persistence import FileAGIPersistence

            path = jsonl_path or os.path.join(
                os.getcwd(), "data_out", "agi_reasoning.jsonl")
            _ensure_parent_dir(path)
            provider.persistence = FileAGIPersistence(path)
        except Exception as exc:  # pragma: no cover - best-effort persistence
            _logger.exception(
                "Failed to initialise AGI persistence backend: %s",
                _sanitize_for_logging(str(exc)),
            )
            provider.persistence = None
    else:
        provider.persistence = None

    if base_choice:
        model_name = f"agi-{base_choice.name}-{base_choice.model}"
    elif model:
        model_name = f"agi-{model}"
    else:
        model_name = "agi-enhanced"

    return provider, ProviderChoice(name="agi", model=model_name)
