---
name: repo-change-workflow
description: 'Systematic workflow for debugging issues, implementing features, refactoring safely, and validating code changes in this repository. Use when you need to investigate code, create a short todo checklist, make incremental edits, run targeted tests, and finish with verified results.'
argument-hint: 'Describe the bug, feature, subsystem, or files to investigate.'
---

# Repo Change Workflow

## What This Skill Produces

Use this skill to turn a loosely defined coding task into a small, verified change set. The expected output is:
- a clear understanding of the requested behavior and constraints
- a short, visible todo list with action-oriented steps
- incremental edits that follow repository conventions
- targeted verification after each meaningful change
- a final summary of files changed, checks run, and follow-up risks

## When to Use

Use this skill when you need to:
- debug a bug or failing behavior
- implement a small or medium feature safely
- refactor existing code without drifting from repo conventions
- investigate an unfamiliar subsystem before editing
- make code changes that must be tested and summarized clearly

Common trigger phrases:
- "debug this issue"
- "fix this bug"
- "implement this feature"
- "refactor this safely"
- "investigate and patch"
- "make the change and verify it"

## Procedure

1. Understand the request
   - Identify the expected behavior, constraints, edge cases, and likely failure modes.
   - If the request is underspecified, ask a small number of focused questions before editing.

2. Load the right context
   - Read repository instructions and any path-specific instructions that apply to the files you may change.
   - Inspect nearby code, configs, tests, and integration points before deciding on an approach.
   - Prefer existing project patterns over introducing a new abstraction.

3. Plan visibly
   - Create a concise todo list with action-oriented steps.
   - Keep at most one step marked in progress.
   - Update the checklist as work advances so progress is explicit.

4. Implement incrementally
   - Make the smallest practical change that can prove or fix the behavior.
   - Preserve existing style, file organization, and public APIs unless the task explicitly requires otherwise.
   - Avoid unrelated cleanup while a behavior change is in flight.

5. Verify frequently
   - Run the smallest useful test, lint, type-check, or smoke check tied to the change.
   - Re-run targeted verification after each meaningful edit.
   - If a check fails, debug the root cause instead of layering on speculative fixes.

6. Handle decision points deliberately
   - If multiple approaches are possible, choose the simplest option that matches current repository conventions.
   - If the issue spans multiple files or the architecture is unclear, expand investigation before editing.
   - If a new environment variable becomes required, check for a root `.env` file and add placeholders if it is missing.
   - If the work is Azure-specific, load Azure guidance before generating or deploying Azure code.

7. Finish cleanly
   - Re-check the original intent and look for hidden edge cases.
   - Add or adjust tests when behavior changes.
   - Mark every todo item as completed, skipped, or blocked with a reason.
   - Summarize what changed, how it was verified, and any follow-up recommendations.

## Quality Checks

Before considering the task complete, confirm that:
- the todo list reflects the actual work performed
- verification covers the changed behavior or files
- unrelated files were not reformatted or modified without reason
- repository conventions were followed instead of replaced
- the final summary includes verification status and any remaining caveats
