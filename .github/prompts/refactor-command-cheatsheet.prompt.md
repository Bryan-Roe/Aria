---
description: "Use when you need one exact next command in the refactor workflow; outputs a single copy-ready slash command line."
name: "Refactor Command Cheatsheet"
argument-hint: "Current stage + blocker + desired outcome (example: safe + unclear next step + route to verify)"
agent: agent
---

Given the user's current refactor state, output **exactly one best next slash command** as a single line.

### Inputs
- Current stage (gate-profile/precheck/safe/verify/evidence-log/artifact-index/pr-summary/reviewer-checklist/release-note/handoff/merge-gate/rollback-plan/sequence-builder/workflow-registry/workflow-audit/routing-matrix/command-cheatsheet/next-step/done-check)
- Any blocker or uncertainty
- Desired immediate outcome

### Required behavior
- Return one command only, no alternatives.
- Prefer the shortest viable command that still includes critical constraints.
- If context is incomplete, infer conservatively and include minimal assumptions in the command text.

### Non-goals unless explicitly requested
- No multi-step plans or sequencing — produce one command only.
- No code changes or edits to source files.
- No executing the recommended command — output it for human use.

### Output format
- **Single line only**: `/prompt-name concise arguments...`
- **Optional next command**: one slash command

### Allowed next commands
- `/refactor-precheck`
- `/refactor-safe`
- `/refactor-verify`
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-release-note`
- `/refactor-handoff`
- `/refactor-merge-gate`
- `/refactor-rollback-plan`
- `/refactor-done-check`
- `/refactor-evidence-log`
- `/refactor-gate-profile`
- `/refactor-artifact-index`
- `/refactor-workflow-registry`
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-sequence-builder`
- `/refactor-command-cheatsheet`
- `/refactor-next-step`

Note: use `/refactor-next-step` only when the stage is genuinely ambiguous.

### Example invocations
- `/refactor-safe function_app.py /api/chat: extract SSE helper, preserve payload schema, minimal diff`
- `/refactor-verify verify fallback order unchanged in shared/chat_providers.py, include focused tests`
- `/refactor-routing-matrix strict matrix for refactor prompts, include governance edges`
