---
description: "Use when you need a canonical evidence log for refactors (invariants checked, tests run, findings, and residual risks) reusable across verify/merge/done steps."
name: "Refactor Evidence Log"
argument-hint: "Scope + invariants + checks run + outcomes (example: function_app.py + SSE schema + verify + all passed)"
agent: agent
---

Create a structured evidence log for a refactor change set.

### Inputs
- Refactor scope and expected invariants
- Checks executed (tests, contract checks, manual verifications)
- Findings (pass/fail, severity, confidence)
- Residual risks and watchpoints

### Required behavior
- Produce evidence that is concise, traceable, and reusable.
- Separate verified facts from assumptions.
- Capture unresolved items with explicit owner/action where possible.
- Keep format stable for handoff and merge decisions.

### Non-goals unless explicitly requested
- No modifying or backdating existing evidence entries.
- No running new tests — document what has already been executed.
- No speculative findings — only confirmed, reproducible observations.

### Output format
- **Scope summary**
- **Invariant checks**: invariant, status, evidence
- **Checks run**: command/check, result, notes
- **Findings**: severity, impact, remediation status
- **Residual risks**
- **Optional next command**: one command only

### Allowed next commands
- `/refactor-verify`
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-merge-gate`
- `/refactor-done-check`
- `/refactor-handoff`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-command-cheatsheet`
- `/refactor-next-step`

### Example invocations
- `evidence log for /api/chat SSE helper extraction with contract parity checks`
- `evidence log for provider fallback cleanup with no API changes`
