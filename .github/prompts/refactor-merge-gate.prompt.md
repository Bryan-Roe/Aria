---
description: "Use when you are preparing to merge a refactor PR and need an explicit go/no-go decision with evidence-backed blockers and required next action."
name: "Refactor Merge Gate"
argument-hint: "Scope + required invariants + validation evidence + open risks (example: function_app.py + SSE schema + ev-log + none)"
agent: agent
---

Determine whether a refactor is ready to merge and provide an evidence-based decision.

### Inputs
- Refactor scope and changed files
- Verification evidence (contract checks, tests, reviewer checklist, release/handoff notes)
- Declared must-preserve invariants and known risks

### Required behavior
- Return one decision: **GO** or **NO-GO**.
- If NO-GO, list the minimum blocking issues to clear.
- If GO, list residual risks and post-merge watchpoints.
- Tie each decision point to concrete evidence.

### Non-goals unless explicitly requested
- No auto-merging or executing the merge — gate assessment only.
- No reopening closed blockers without new evidence.
- No waiving mandatory evidence requirements for convenience.

### Output format
- **Decision**: GO | NO-GO
- **Rationale**: concise evidence-backed reasoning
- **Blocking gates** (if NO-GO): ordered list with exact fix target
- **Post-merge watchpoints** (if GO): monitoring and rollback cues
- **Optional next command**: one best follow-up slash command

### Allowed next commands
- `/refactor-verify`
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-release-note`
- `/refactor-handoff`
- `/refactor-evidence-log`
- `/refactor-rollback-plan`
- `/refactor-done-check`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-command-cheatsheet`
- `/refactor-next-step`

### Example invocations
- `merge-gate for SSE refactor: verify contract parity, tests, reviewer-checklist`
- `merge-gate for provider cleanup: no API changes expected, one flaky test present`
