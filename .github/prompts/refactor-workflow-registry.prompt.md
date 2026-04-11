---
description: "Use when you need to define or refresh the canonical refactor workflow registry (stage vocabulary, command inventory, and gate taxonomy)."
name: "Refactor Workflow Registry"
argument-hint: "Current workflow scope + strictness + include deprecated aliases (example: refactor prompts + strict + no)"
agent: agent
---

Generate a canonical registry for the refactor prompt workflow.

### Inputs
- Workflow scope (default: all `refactor-*.prompt.md`)
- Strictness level (strict | practical)
- Whether deprecated aliases should be listed
- Optional transition topology from `/refactor-routing-matrix`

### Required behavior
- Output a normalized stage vocabulary.
- Output a canonical command inventory grouped by intent.
- Output gate taxonomy (mandatory-capable vs optional-supporting gates).
- Flag deprecated or ambiguous terms and suggest replacements.

### Non-goals unless explicitly requested
- No adding experimental stages not yet agreed upon by the workflow owners.
- No removing stages still referenced by other prompts in the suite.
- No executing workflow steps — define and document only.

### Output format
- **Canonical stages**
- **Canonical commands** (grouped)
- **Gate taxonomy**
- **Canonical transitions** (if topology provided)
- **Deprecated aliases** (if any)
- **Update recommendations**: minimal edits for drifted prompts
- **Optional next command**: one slash command

### Allowed next commands
- `/refactor-workflow-audit`
- `/refactor-routing-matrix`
- `/refactor-next-step`
- `/refactor-command-cheatsheet`
- `/refactor-sequence-builder`

### Example invocations
- `build strict canonical registry for all refactor prompts`
- `refresh registry with practical aliases for team adoption`
- `refresh canonical stages/commands using a routing-matrix transition topology`
