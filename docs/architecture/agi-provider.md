# AGI Provider — Architecture & Design

> **Canonical implementation:** `ai-projects/chat-cli/src/agi_provider.py`
> **Compatibility shim:** `agi_provider.py` (root)
> **Tests:** `tests/test_agi_provider.py`

## Overview

The AGI Provider wraps any `BaseChatProvider` with a structured, multi-step
reasoning pipeline. It is the primary mechanism for intelligent, context-aware
responses within the Aria platform.

```
User query
    │
    ▼
┌─────────────────────────────────────┐
│  AGIProvider.complete()             │
│                                     │
│  1. Sanitize & validate input       │
│  2. _reason()                       │
│     ├─ _analyze_query()             │
│     ├─ _select_agent()              │
│     ├─ _decompose_task()  (opt.)    │
│     └─ _chain_of_thought() (opt.)   │
│  3. _generate_response()            │
│     ├─ _dispatch_to_agent() (opt.)  │
│     └─ base_provider.complete()     │
│  4. _reflect_and_improve() (opt.)   │
│  5. _learn_from_routing()           │
│  6. Return / stream response        │
└─────────────────────────────────────┘
```

---

## Subsystems

### Reasoning Core

The reasoning core lives in `AGIProvider._reason()`. It produces an ordered
list of `ReasoningStep` objects that:

- describe how the query was analysed,
- record which specialist agent was selected and why,
- list subtasks for complex queries, and
- surface domain-aware chain-of-thought hints.

The chain is stored in `AGIContext.reasoning_chains` for observability and is
optionally prepended to the response in `verbose` mode.

**Step types and their semantics:**

| `step_type`  | Produced by           | Description                               |
|--------------|-----------------------|-------------------------------------------|
| `analyze`    | `_analyze_query`      | Intent / domain / complexity breakdown    |
| `route`      | `_select_agent`       | Selected specialist agent                 |
| `decompose`  | `_decompose_task`     | Ordered subtask list (complex queries)    |
| `synthesize` | `_chain_of_thought`   | Domain-aware reasoning hints              |
| `reflect`    | `_reflect_and_improve`| Post-generation validation annotations    |

---

### Memory Subsystem

Memory is managed by `AGIContext`, a bounded in-process store with four
components:

| Component             | Bound         | Purpose                               |
|-----------------------|---------------|---------------------------------------|
| `conversation_history`| `MAX_HISTORY_SIZE` (50) | Recent turn-by-turn messages  |
| `reasoning_chains`    | `MAX_REASONING_CHAINS` (10) | Per-turn reasoning traces   |
| `goals`               | `MAX_GOALS` (5) | User-specified session goals        |
| `learned_patterns`    | Unbounded†    | Routing observations with time-decay  |

† `learned_patterns` is bounded in practice by session lifetime; entries decay
  with a 24-hour half-life applied in `_select_agent`.

**Eviction policy for conversation history:**
System messages are always preserved. When the history exceeds `MAX_HISTORY_SIZE`,
the oldest non-system messages are evicted first.

**Extensibility — `MemoryInterface`:**
`AGIContext` satisfies the `MemoryInterface` structural protocol. Any object
that implements `add_message`, `add_reasoning_chain`, and `get_relevant_context`
can replace `AGIContext` without inheriting from it:

```python
from agi_provider import MemoryInterface, AGIProvider

class RedisMemory:
    def add_message(self, message): ...
    def add_reasoning_chain(self, chain): ...
    def get_relevant_context(self, query) -> str: ...

assert isinstance(RedisMemory(), MemoryInterface)  # True
```

---

### Environment Interface

The provider interacts with the outside world through two channels:

1. **Base provider** — a `BaseChatProvider` instance for LLM inference.
2. **Specialist dispatch** — `_dispatch_to_agent()` routes complex queries to
   domain-specific providers registered in `_AGENT_REGISTRY`.

The `EnvironmentInterface` protocol describes the minimal contract for any LLM
backend:

```python
class EnvironmentInterface(Protocol):
    def complete(self, messages, stream=True) -> Iterable[str] | str: ...
```

This is satisfied by all `BaseChatProvider` subclasses and by mock objects used
in tests.

---

### Multi-Agent Routing

`_AGENT_REGISTRY` maps agent names to capability descriptors:

| Agent                 | Domains     | Provider      | Use-case                       |
|-----------------------|-------------|---------------|--------------------------------|
| `quantum-specialist`  | quantum     | quantum       | Qiskit/PennyLane queries       |
| `code-specialist`     | technical   | lora          | Code generation & debugging    |
| `aria-character`      | aria        | local         | Movement & gesture commands    |
| `ai-specialist`       | ai          | lora          | LLM / LoRA / training topics   |
| `reasoning-specialist`| ai          | agi           | Step-by-step reasoning         |
| `lmstudio-specialist` | (any)       | lmstudio      | General LM Studio inference    |
| `general`             | (any)       | agi           | Fallback                       |

Agent selection uses a weighted score:

```
score = 0.5 × domain_match + 0.3 × intent_match
      + confidence_boost × query_confidence
      + learned_pattern_bonus (decays with 24h half-life)
```

Routing decisions are recorded as learned patterns and reinforced over the
session lifetime.

---

## Async Support

`AGIProvider.async_complete()` provides an async variant backed by
`asyncio.to_thread`, so the blocking synchronous pipeline does not stall an
event loop:

```python
import asyncio
from agi_provider import create_agi_provider

async def main():
    provider, _ = create_agi_provider()
    response = await provider.async_complete(
        [{"role": "user", "content": "Explain LoRA fine-tuning"}]
    )
    print(response)

asyncio.run(main())
```

---

## Security Boundaries

| Concern                    | Mechanism                                      |
|----------------------------|------------------------------------------------|
| Input injection            | `_sanitize_input()` strips control characters  |
| Log injection / XSS        | `_sanitize_for_logging()` HTML-escapes output  |
| History overflow / DoS     | `MAX_HISTORY_SIZE` hard-limit + warning log    |
| Goal overflow              | `MAX_GOALS` hard-limit, oldest evicted first   |
| Reasoning chain overflow   | `MAX_REASONING_CHAINS` rolling window          |
| Error detail leakage       | All exceptions caught; sanitized message logged|

---

## Extensibility Checklist

When adding a new specialist agent:

1. Add an entry to `_AGENT_REGISTRY` with `domains`, `intents`,
   `provider`, `confidence_boost`, `subtask_templates`, and `description`.
2. Add a persona block to `_build_agi_system_prompt` for the new agent name.
3. (Optional) Add an agent-aware temperature entry to `_AGENT_TEMPERATURES`
   inside `_generate_response`.
4. Add or update tests in `tests/test_agi_provider.py`.

When replacing the memory backend:

1. Implement `add_message`, `add_reasoning_chain`, and `get_relevant_context`.
2. Verify `isinstance(your_backend, MemoryInterface)` returns `True`.
3. Assign `agi_provider.context = your_backend` after construction.

---

## Design Rationale

**Why a single file, not a package?**
The AGI provider is a self-contained feature. Splitting it into multiple files
would add import indirection without providing modularity benefits at the
current scale. The `MemoryInterface` and `EnvironmentInterface` protocols
provide the extension points needed for alternative implementations without
requiring physical file separation.

**Why `asyncio.to_thread` instead of native async I/O?**
The base providers use blocking I/O (HTTP, subprocess). `asyncio.to_thread`
gives callers a clean async surface while keeping the synchronous pipeline
unchanged. When providers migrate to native async I/O the `async_complete`
implementation can be updated without changing its public signature.

**Why `runtime_checkable` protocols instead of ABCs?**
Protocols allow structural subtyping — third-party memory backends and
environment adapters can satisfy the interface without inheriting from an
Aria-specific ABC. This reduces coupling and simplifies testing with mock
objects.
