---
description: "Use when planning a refactor: assess invariants, regression hotspots, and validation strategy before code changes."
name: "Refactor Precheck"
argument-hint: "Target + intent + constraints (example: scope + goal + invariant)"
agent: agent
---

Analyze the selected code and produce a **pre-refactor risk map** before any edits are made.

Suggested next step:
- Execute `/refactor-safe` with the must-preserve invariants from this precheck.
- If blocked or unsure, run `/refactor-next-step`.
- If workflow stages/commands feel inconsistent, run `/refactor-workflow-audit`.
- If canonical stage/command vocabulary is unclear, run `/refactor-workflow-registry`.
- If transition paths between stages are unclear, run `/refactor-routing-matrix`.

### Inputs
- Selected code and nearby context
- User arguments (target, intent, constraints)
- Relevant project conventions and contracts

### Required behavior
- Do **not** implement code changes in this step.
- Identify externally visible contracts to preserve (routes, schemas, streaming protocol, public symbols).
- Highlight likely regression zones (state flow, branching logic, side effects, error paths).
- Recommend a smallest-safe refactor slice and rollback strategy.

### Output format
- **Scope understanding**: what will and will not be touched
- **Must-preserve invariants**: explicit contract checklist
- **Risk matrix**: risk, impact, confidence, mitigation
- **Validation plan**: focused tests + broader checks to run
- **Go / no-go note**: whether to proceed now, and why
- **Optional next command**: one slash command

### Optional next commands
- `/refactor-safe`
- `/refactor-next-step`
- `/refactor-command-cheatsheet`
- `/refactor-workflow-audit`
- `/refactor-workflow-registry`
- `/refactor-routing-matrix`

### Example invocations
- `function_app.py chat stream: extract event-framing helper, preserve SSE payload shape`
- `shared/chat_providers.py: remove duplication in fallback checks, no behavior changes`
