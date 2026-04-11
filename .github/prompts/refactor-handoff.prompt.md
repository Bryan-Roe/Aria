---
description: "Use when handing off refactor work: produce a concise status package with decisions, evidence, blockers, and exact next command."
name: "Refactor Handoff"
argument-hint: "Current stage + completed artifacts + blocker + owner handoff context (example: verify + ev-log + test fails + backend)"
agent: agent
---

Create a handoff-ready refactor status package for another engineer (or for later continuation).

### Inputs
- Current workflow stage and completed prompts
- Artifacts produced (precheck notes, diff summary, verification outcomes, PR summary, release note draft)
- Open blockers, assumptions, and unresolved risks
- Owner handoff context (next owner, priority, escalation path)

### Required behavior
- Capture what is done vs what remains, with no ambiguity.
- Include evidence references (contracts checked, tests run, findings).
- Include or reference a canonical artifact map from `/refactor-artifact-index` when available.
- Provide exactly one recommended next command for continuation.
- Keep it scannable and action-oriented.

### Non-goals unless explicitly requested
- No continuing the refactor — produce the handoff document only.
- No speculative decisions not yet made during the current phase.
- No resolving open blockers — document them for the next owner.

### Output format
- **Current stage**
- **Completed artifacts**
- **Key decisions and invariants**
- **Evidence snapshot** (tests/checks/findings)
- **Open risks/blockers**
- **Optional next command**: one slash command
- **Definition of done for next step**

### Allowed next commands
- `/refactor-precheck`
- `/refactor-safe`
- `/refactor-verify`
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-release-note`
- `/refactor-merge-gate`
- `/refactor-rollback-plan`
- `/refactor-evidence-log`
- `/refactor-artifact-index`
- `/refactor-done-check`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-command-cheatsheet`
- `/refactor-next-step`

### Example invocations
- `handoff after verify: parity mostly green, one flaky test remains`
- `handoff after pr-summary: need reviewer-checklist + release-note before merge`
