---
description: "Use when opening a refactor PR: generate a concise reviewer-friendly summary with parity evidence and test results."
name: "Refactor PR Summary"
argument-hint: "Scope + rationale + key unchanged contracts + validation results (example: fn_app.py + SSE helper + /api/chat + passed)"
agent: agent
---

Create a high-quality pull request summary for a refactor change set.

Optional companion:
- Run `/refactor-reviewer-checklist` to generate a role-based review checklist for the same diff.
- If unsure about sequencing, run `/refactor-next-step`.
- Run `/refactor-release-note` to generate customer/internal release communication.
- Run `/refactor-handoff` to package status and the exact next action for a teammate.
- Run `/refactor-merge-gate` for an explicit GO/NO-GO decision before merging.
- Run `/refactor-rollback-plan` to document concrete backout triggers and actions.
- Run `/refactor-workflow-audit` if workflow-stage or command routing looks inconsistent.
- Run `/refactor-workflow-registry` to normalize stage/command terms before handoff.
- Run `/refactor-routing-matrix` to validate transition topology before handoff.

### Inputs
- Selected diff, changed files, and commit context
- User arguments describing scope and rationale
- Known unchanged contracts and invariants (API shapes, routes, streaming/status behavior)
- Validation outcomes (focused and broader checks)

### Required behavior
- Keep the summary concise but complete for reviewers.
- Separate **what changed** from **what intentionally did not change**.
- Highlight risk areas and how they were mitigated.
- Avoid fluff; prefer verifiable statements tied to evidence.

### Non-goals unless explicitly requested
- No modifying source code or test files.
- No fabricating test results — summarize actual evidence only.
- No including speculative improvements not yet implemented.

### Output format
- **Title suggestion**: one-line PR title
- **Why**: problem or maintenance goal
- **What changed**: grouped by file/area
- **Behavior parity / invariants preserved**: explicit checklist
- **Validation**: tests/checks run + outcomes
- **Risk & rollback notes**: known caveats and backout path
- **Reviewer checklist**: 3-7 concrete review points
- **Optional next command**: one slash command

### Optional add-ons when provided
- Release note snippet
- Changelog entry draft
- Follow-up tasks (if deferred cleanup exists)

### Optional next commands
- `/refactor-reviewer-checklist`
- `/refactor-release-note`
- `/refactor-merge-gate`
- `/refactor-rollback-plan`
- `/refactor-handoff`
- `/refactor-done-check`
- `/refactor-next-step`
- `/refactor-command-cheatsheet`
- `/refactor-workflow-audit`
- `/refactor-workflow-registry`
- `/refactor-routing-matrix`

### Example invocations
- `chat streaming refactor: summarize helper extraction, preserve SSE schema, include tests`
- `provider cleanup PR: document fallback-order parity and readiness-check validation`
