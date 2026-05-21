# AI Capability Runbook

## Scope
Operational controls for AI quality, fallback behavior, latency, memory relevance, and safety guardrails.

## Enable / Disable

- Guardrails:
  - Enable: `QAI_AI_GUARDRAILS_ENABLED=true`
  - Disable: `QAI_AI_GUARDRAILS_ENABLED=false`
- Memory relevance:
  - `QAI_MEMORY_MIN_SIMILARITY` (default `0.2`)
  - `QAI_MEMORY_TOP_K` (default `5`)
- Standard prompt:
  - `QAI_STANDARD_SYSTEM_PROMPT` to override the default concise safety-first system prompt.

## Diagnostics

1. Check health and capability metrics:
   - `GET /api/ai/status`
   - `GET /api/ai/capabilities`
2. Check dashboard page:
   - `apps/dashboard/ai-capabilities.html`
3. Inspect capability event log:
   - `data_out/ai_capabilities/events.jsonl`

## Key Indicators

- `metrics.fallback_count`: provider fallback frequency
- `metrics.latency_ms_p50` / `metrics.latency_ms_p95`: latency trend
- `metrics.safety_blocked_input` / `metrics.safety_blocked_output`: guardrail activity
- `metrics.memory_injected` vs `metrics.memory_candidates`: memory usefulness proxy

## Rollback Triggers

Rollback (or disable new controls) when any of these occur:

- sustained quality degradation in evaluation checks
- fallback spikes after deployment
- latency p95 regression beyond acceptable SLO
- safety false positives significantly blocking valid traffic

## Recovery Actions

1. Disable guardrails temporarily if false positives are confirmed:
   - `QAI_AI_GUARDRAILS_ENABLED=false`
2. Relax memory filtering:
   - lower `QAI_MEMORY_MIN_SIMILARITY` incrementally
3. Constrain memory fan-in:
   - lower `QAI_MEMORY_TOP_K`
4. Re-run targeted checks:
   - `python -m pytest tests/test_chat_memory.py tests/test_function_app_endpoints.py -q --tb=short`
   - `python -m pytest ai-projects/chat-cli/src/test_chat_providers.py tests/test_agi_provider.py -q --tb=short`
