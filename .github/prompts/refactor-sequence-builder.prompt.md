---
description: 'Use when you need a full ordered refactor command sequence or runbook from risk profile, constraints, and required gates.'
name: "Refactor Sequence Builder"
argument-hint: "Scope + profile + required gates + constraints (example: function_app.py + standard + verify + no DB changes)"
agent: agent
---

Generate an end-to-end ordered slash-command sequence for the refactor workflow.

### Inputs
- Refactor scope and risk profile (or risk signals)
- Required gates and optional gates
- Constraints (no API changes, preserve SSE, minimal diff, etc.)

### Required behavior
- Produce one linear command sequence from start to finish.
- Include only necessary steps for the stated profile/gates.
- For each step, provide a compact command line and success checkpoint.
- Mark optional branches explicitly without duplicating required path.

### Non-goals unless explicitly requested
- No executing the sequence steps — output the ordered plan only.
- No skipping required gates based on estimated or assumed low risk.
- No adding steps outside the approved refactor prompt suite.

### Output format
- **Profile used**
- **Required path** (ordered list of commands)
- **Optional branches** (if any)
- **Stop conditions** (when to pause and reassess)
- **Final completion check command**
- **Optional next command**: one slash command

### Allowed next commands
- `/refactor-gate-profile`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-precheck`
- `/refactor-safe`
- `/refactor-verify`
- `/refactor-evidence-log`
- `/refactor-artifact-index`
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-release-note`
- `/refactor-handoff`
- `/refactor-merge-gate`
- `/refactor-rollback-plan`
- `/refactor-done-check`
- `/refactor-command-cheatsheet`
- `/refactor-next-step`

### Example invocations
- `contract-sensitive SSE refactor with required verify/reviewer-checklist/merge-gate/release-note`
- `low-risk internal cleanup with minimal mandatory gates`
