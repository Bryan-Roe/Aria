---
description: "Turn a repeated workflow into a high-quality reusable .prompt.md with clear inputs, outputs, and execution style."
name: "Create Reusable Prompt"
argument-hint: "Task pattern + typical inputs + desired output style + scope (workspace or personal)"
agent: agent
---

You are designing a reusable prompt file (`.prompt.md`) from a repeatable workflow.

## Goal
Create a prompt that is specific enough to be reliable and general enough to be reused.

## Inputs to extract
From the user request (and recent conversation context), extract:
1. **Core repeated task** (what is done over and over)
2. **Implicit inputs** (selected code, file paths, stack traces, file type, branch, etc.)
3. **Expected output format/style** (checklist, patch, summary, commands, tone, strictness)

## Authoring requirements
- Produce a complete `.prompt.md` with frontmatter and body.
- Keep frontmatter fields explicit: `description`, `name`, `argument-hint`, `agent`.
- Make instructions operational (ordered steps, validation criteria, failure handling).
- Include constraints/safety boundaries relevant to the task.
- Avoid vague language such as “be helpful”; prefer concrete, testable directives.

## Output contract
Return:
1. The full prompt file content
2. 2–3 example invocations
3. A short “Customization knobs” section (what users can tune safely)

## Quality bar
Before finalizing, self-check:
- Is scope clear (what it does / does not do)?
- Are required inputs obvious?
- Is output shape deterministic enough for repeated use?
- Are safety constraints explicit?
- Could a teammate use this without extra explanation?

If details are missing, ask only the minimum clarifying questions needed to finalize.