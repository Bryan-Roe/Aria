---
description: "Use when you are early in a refactor and need to decide required quality gates based on risk and contract surface (internal-only vs contract-affecting)."
name: "Refactor Gate Profile"
argument-hint: "Scope + risk signals + contract touchpoints (example: function_app.py + streaming refactor + /api/chat, /api/tts)"
agent: agent
---

Determine the minimum required refactor gates for this change before final merge decisions.

### Inputs
- Refactor scope and touched areas
- Risk signals (public API touch, SSE/schema changes, provider logic changes, multi-file complexity)
- Contract touchpoints (public routes, schemas, streaming contracts that must not change)
- Constraints (no API changes, minimal diff, preserve fallback order, etc.)

### Required behavior
- Classify refactor profile:
  - **Low-risk internal**
  - **Medium-risk internal**
  - **Contract-sensitive**
  - **High-risk cross-cutting**
- Output a required gate set appropriate for the profile.
- Distinguish mandatory gates vs recommended gates.
- Provide one next command to start execution.

### Non-goals unless explicitly requested
- No code changes or implementation tasks — profile only.
- No adding gates beyond what the stated risk level requires.
- No approving waivers or overriding mandatory gate requirements.

### Output format
- **Profile**: one category only
- **Mandatory gates**
- **Recommended gates**
- **Rationale**: concise mapping from risks to gates
- **Optional next command**: one slash command

### Allowed gates
- precheck
- verify
- reviewer-checklist
- pr-summary
- release-note
- handoff
- merge-gate
- rollback-plan
- evidence-log
- artifact-index
- done-check

### Allowed next commands
- `/refactor-precheck`
- `/refactor-safe`
- `/refactor-verify`
- `/refactor-evidence-log`
- `/refactor-artifact-index`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-sequence-builder`
- `/refactor-next-step`
- `/refactor-command-cheatsheet`

### Example invocations
- `provider fallback cleanup in shared/chat_providers.py with no API changes`
- `SSE event framing refactor touching /api/chat route and web consumers`
