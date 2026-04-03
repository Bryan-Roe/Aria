---
description: "Use when you need a concrete rollback/backout plan for a refactor, including triggers, actions, and verification after rollback."
name: "Refactor Rollback Plan"
argument-hint: "Scope + deploy context + risk triggers + rollback constraints (example: fn_app.py + Azure Fn + test fails + git revert)"
agent: agent
---

Create a practical rollback plan for a refactor change set.

### Inputs
- Refactor scope and changed surfaces
- Deployment context (where/when/how it ships)
- Risk triggers and failure signals
- Constraints (data compatibility, migration concerns, time-to-recover goals)

### Required behavior
- Define clear rollback triggers (what signals require backout).
- Provide ordered rollback actions with ownership assumptions.
- Include post-rollback verification checks.
- Distinguish immediate rollback from follow-up remediation.

### Non-goals unless explicitly requested
- No executing the rollback — plan and document only.
- No removing entries for partial-rollback options that may still be needed.
- No overstating rollback safety without supporting evidence.

### Output format
- **Rollback readiness summary**
- **Triggers to rollback**
- **Rollback action sequence**
- **Post-rollback verification**
- **Residual risk after rollback**
- **Optional next command**: one slash command

### Allowed next commands
- `/refactor-merge-gate`
- `/refactor-done-check`
- `/refactor-handoff`
- `/refactor-pr-summary`
- `/refactor-evidence-log`
- `/refactor-artifact-index`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-command-cheatsheet`
- `/refactor-next-step`

### Example invocations
- `rollback plan for SSE refactor in /api/chat with rapid backout requirement`
- `rollback plan for provider fallback cleanup with no schema changes`
