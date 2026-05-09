---
description: "Use when you need a stage-to-command routing matrix for refactor prompts, including primary transitions and optional governance paths."
name: "Refactor Routing Matrix"
argument-hint: "Scope + strictness + include optional governance edges (example: refactor prompts + strict + yes)"
agent: agent
---

Generate a normalized routing matrix for the refactor prompt suite.

### Inputs
- Prompt scope (default: all `refactor-*.prompt.md`)
- Strictness (strict | practical)
- Include optional governance edges (`workflow-registry`, `workflow-audit`) yes/no

### Required behavior
- Build a stage-to-next-command matrix with explicit transition type:
  - `primary` (normal workflow progression)
  - `optional` (context-dependent)
  - `governance` (audit/registry maintenance)
- Flag orphan stages (no useful outgoing transitions) and dead-end commands.
- Highlight asymmetric transitions where reverse/adjacent navigation is unexpectedly missing.
- Recommend minimal edits to fix discovered routing gaps.

### Non-goals unless explicitly requested
- No recommending workflow changes or reordering established stages.
- No including commands outside the established refactor prompt suite.
- No executing transitions — produce the routing map only.

### Output format
- **Routing matrix**: stage, next-command, transition-type, rationale
- **Orphans/dead ends**
- **Asymmetry findings**
- **Minimal patch recommendations**
- **Optional next command**: one slash command

### Allowed next commands
- `/refactor-workflow-audit`
- `/refactor-workflow-registry`
- `/refactor-sequence-builder`
- `/refactor-command-cheatsheet`
- `/refactor-next-step`

### Example invocations
- `strict routing matrix for all refactor prompts with governance edges`
- `practical routing matrix focusing on merge/done/handoff transitions`
