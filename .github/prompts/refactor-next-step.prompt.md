---
description: "Use when unsure what to run next in the refactor workflow: recommends the next slash prompt and arguments."
name: "Refactor Next Step"
argument-hint: "Current stage + current artifact + blocker (example: safe + gate-profile + none)"
agent: agent
---

Given the current refactor stage, recommend the **single best next slash prompt** and provide a ready-to-use invocation.

### Inputs
- Current stage and what was already completed
- Current artifact quality (precheck notes, diff quality, verification status, PR draft status)
- Any blocker or uncertainty

### Required behavior
- Recommend exactly one next prompt from `### Allowed next commands`.
- Explain why this is the highest-value next move.
- Provide one concrete invocation string tailored to the user's context.
- If inputs are incomplete, infer conservatively and state assumptions.

### Non-goals unless explicitly requested
- No executing the recommended command — recommend only.
- No multi-step plans — one next step at a time.
- No code changes or source file edits.

### Output format
- **Optional next command**: one prompt only
- **Why now**: 2-4 bullets
- **Invocation template**: copy-ready command text
- **Success criteria**: what “done” looks like for this step

### Allowed next commands
- `/refactor-precheck`
- `/refactor-safe`
- `/refactor-verify`
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-release-note`
- `/refactor-command-cheatsheet`
- `/refactor-handoff`
- `/refactor-merge-gate`
- `/refactor-rollback-plan`
- `/refactor-done-check`
- `/refactor-evidence-log`
- `/refactor-artifact-index`
- `/refactor-gate-profile`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-sequence-builder`
- `/refactor-next-step`

### Example invocations
- `finished precheck, have invariants, ready to edit`
- `refactor complete, tests partly run, not sure if to verify or write pr-summary`
- `workflow feels inconsistent across prompts; need the best next command to diagnose routing drift`
