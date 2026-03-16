---
name: "AGI-Provider"
description: "Guidance for AGI provider implementation and reasoning system"
applyTo: "**/agi_provider.py"
---
# AGI Provider — Implementation Guidance

- `AGIProvider` wraps any `BaseChatProvider` with reasoning, decomposition, and self-reflection.
- Factory: `create_agi_provider(model, temperature, max_output_tokens, enable_chain_of_thought, enable_self_reflection, enable_task_decomposition, reasoning_depth, verbose)`.
- Core pipeline: `_analyze_query()` → `_decompose_task()` → `_reason()` → `_reflect_and_improve()`.
- Query complexity classification: simple (<10 words, no keywords), moderate, complex (keywords: implement, architect, debug, refactor).
- Intent detection: movement, coding, explanation, creation, question, general.
- Domain detection: quantum, ai, aria, technical, general.
- Decomposition templates vary by intent (coding: requirements→design→implement→edge cases→test; explanation: define→examples→relationships→summary).
- Self-reflection checks: response length, question completeness, missing Aria tags for Aria-domain queries.
- Security: `_sanitize_input()` strips control chars, enforces `MAX_INPUT_LENGTH=10000`. `_sanitize_for_logging()` for safe log output.
- Memory limits: `MAX_HISTORY_SIZE=50`, `MAX_REASONING_CHAINS=10`, `MAX_GOALS=5`.
- `AGIContext` stores: `conversation_history`, `reasoning_chains`, `goals`, `learned_patterns`.
- `ReasoningStep` dataclass: `step_type`, `content`, `confidence`, `metadata`.
- Aria movement tags: `[aria:walk:left]`, `[aria:jump]`, `[aria:wave]`, `[aria:dance]`, etc.
- Root-level `agi_provider.py` is a compatibility shim — canonical implementation lives in `ai-projects/chat-cli/src/agi_provider.py`.
- Tests: prefer `pytest tests/ -m "not slow and not azure"`.
