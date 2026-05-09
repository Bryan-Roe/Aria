---
description: "Use when you need to audit refactor prompt suite consistency (stages, allowed commands, and handoff links) and report minimal fixes."
name: "Refactor Workflow Audit"
argument-hint: "Prompt set scope + expected stages + strictness (example: refactor prompts + all 19 stages + strict)"
agent: agent
---

Audit the refactor prompt suite for consistency and suggest minimal corrective edits.

### Inputs
- Target prompt set (default: refactor-*.prompt.md)
- Optional canonical registry from `/refactor-workflow-registry`
- Optional transition map from `/refactor-routing-matrix`
- Expected stage vocabulary and command inventory
- Strictness preference (strict | practical)

### Required behavior
- Detect drift in stage labels, allowed command lists, and cross-prompt references.
- Identify missing links between adjacent workflow steps.
- Propose minimal, concrete text edits (no unnecessary rewrites).
- Classify findings by severity (blocker, warning, note).

### Non-goals unless explicitly requested
- No making prompt edits or rewrites — report findings only.
- No redefining stage semantics — audit existing definitions only.
- No flagging style preferences as structural blockers.

### Output format
- **Audit summary**
- **Consistency findings**: file, issue, severity, fix
- **Command inventory parity**: expected vs present
- **Transition parity**: expected vs present (if transition map provided)
- **Recommended patch plan**: smallest ordered edit set
- **Optional next command**: one command only

### Optional next commands
- `/refactor-workflow-registry`
- `/refactor-routing-matrix`
- `/refactor-command-cheatsheet`
- `/refactor-sequence-builder`
- `/refactor-next-step`

### Example invocations
- `audit refactor prompts for stage-list drift after adding merge-gate and done-check`
- `strict audit of allowed command parity across all refactor prompts`
- `audit transition parity against a routing-matrix baseline after workflow updates`
