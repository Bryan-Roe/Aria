---
description: "Use at the end of a refactor workflow: run a strict final done-check and report whether all required artifacts and gates are complete."
name: "Refactor Done Check"
argument-hint: "Scope + required gates + available artifacts"
agent: agent
---

Perform a strict final completion check for a refactor change set.

### Inputs
- Refactor scope and constraints
- Optional gate profile from `/refactor-gate-profile`
- Optional evidence log from `/refactor-evidence-log`
- Optional artifact index from `/refactor-artifact-index`
- Available artifacts from prior prompts (precheck, verify, PR summary, reviewer checklist, release note, merge gate, handoff)
- Required gates for this change

### Required behavior
- Evaluate completion status against required gates.
- Return one verdict: **DONE** or **NOT DONE**.
- If NOT DONE, list exact missing artifacts or unresolved blockers.
- If DONE, provide a concise final readiness statement and any residual watchpoints.

### Output format
- **Verdict**: DONE | NOT DONE
- **Gate status table**: gate, status, evidence
- **Missing items** (if any): minimal required next steps
- **Optional next command**: one command only (or `none` if truly complete)

### Allowed next commands
- `/refactor-verify`
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-release-note`
- `/refactor-merge-gate`
- `/refactor-handoff`
- `/refactor-evidence-log`
- `/refactor-artifact-index`
- `/refactor-command-cheatsheet`
- `/refactor-next-step`
- `/refactor-gate-profile`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`

### Example invocations
- `done-check for /api/chat refactor: require verify + reviewer-checklist + merge-gate + release-note`
- `done-check for internal provider cleanup: no user-facing note required`
