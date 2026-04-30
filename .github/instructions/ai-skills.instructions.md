---
name: "AI-Skills-Workflow"
description: "Skill routing guidance for AI feature planning, implementation, evaluation, and safety hardening."
applyTo: "function_app.py,shared/**/*.py,ai-projects/**/*.py,scripts/**/*.py,apps/**/*.js,apps/**/*.ts"
---
# AI Skills Workflow Routing

Use this instruction to pick the right skill for AI-heavy work in Aria.

## Default Skill Selection

- **Planning a new AI capability** (requirements, scope, rollout, fallback design)
  - Use: `ai-feature-planning-workflow`
- **Implementing/changing agentic behavior** (tool calls, orchestration, schema contracts)
  - Use: `ai-agent-implementation-workflow`
- **Comparing quality of prompts/models/providers** (metrics and reproducible evaluation)
  - Use: `ai-response-evaluation-workflow`
- **Hardening for safety/abuse** (injection defense, output controls, guardrails)
  - Use: `ai-safety-guardrails-workflow`

## Combined Usage Patterns

- New feature from idea to ship:
  1) `ai-feature-planning-workflow`
  2) `ai-agent-implementation-workflow`
  3) `ai-response-evaluation-workflow`
  4) `ai-safety-guardrails-workflow`

- Regression triage on AI responses:
  1) `ai-response-evaluation-workflow`
  2) `ai-agent-implementation-workflow`
  3) `ai-safety-guardrails-workflow` (if abuse/safety symptoms exist)

## Repository-Specific Constraints

- Preserve provider detection/fallback semantics used by chat providers.
- Keep SSE contracts stable for streaming endpoints.
- Never modify `datasets/`; write outputs to `data_out/`.
- Keep telemetry optional/non-blocking.
- Prefer targeted verification after each meaningful change.

## Minimum Verification Standard

After AI-related changes, run at least one focused check relevant to touched files:

- `python scripts/test_runner.py --unit`
- or a focused pytest command for affected modules
- and, for endpoint changes, a quick route/contract smoke check
