---
description: "Use when you need a canonical artifact index for refactor workflow outputs (what exists, where it lives, and which step produced it)."
name: "Refactor Artifact Index"
argument-hint: "Scope + completed steps + known artifacts (example: function_app.py + safe + evidence-log, gate-profile)"
agent: agent
---

Create a canonical index of all artifacts produced in a refactor workflow.

### Inputs
- Refactor scope and current stage
- Completed prompts/steps
- Known artifacts and references

### Required behavior
- Normalize artifact names and categories.
- Map each artifact to producer step, purpose, and current status.
- Mark missing-but-required artifacts.
- Provide one best next command to close the biggest gap.

### Non-goals unless explicitly requested
- No renaming or relocating existing artifacts — index only.
- No creating new artifacts outside of the established workflow steps.
- No code changes or source file edits.

### Output format
- **Artifact index table**: artifact, produced-by, status, location/reference, purpose
- **Required missing artifacts**
- **Stale/superseded artifacts**
- **Optional next command**: one slash command

### Typical artifacts
- Gate profile
- Precheck notes
- Verification report
- Evidence log
- PR summary
- Reviewer checklist
- Release note draft
- Rollback plan
- Merge gate decision
- Handoff package
- Done-check verdict

### Allowed next commands
- `/refactor-evidence-log`
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-release-note`
- `/refactor-rollback-plan`
- `/refactor-merge-gate`
- `/refactor-handoff`
- `/refactor-done-check`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-command-cheatsheet`
- `/refactor-next-step`

### Example invocations
- `artifact-index after verify + evidence-log + pr-summary`
- `artifact-index before merge for contract-sensitive refactor`
