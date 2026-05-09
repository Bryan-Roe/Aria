---
description: "Use when you are conducting refactor review and need role-based API/perf/testing/security checklists with evidence-driven checks."
name: "Refactor Reviewer Checklist"
argument-hint: "Refactor scope + key invariants + reviewer roles (example: function_app.py + SSE schema + backend, security)"
agent: agent
---

Generate a role-based review checklist tailored to the selected refactor diff.

Optional companion:
- Run `/refactor-workflow-audit` if review flow commands/stages seem inconsistent.
- Run `/refactor-workflow-registry` to align review terms with canonical workflow vocabulary.
- Run `/refactor-routing-matrix` to validate review-stage transition paths.

### Inputs
- Selected diff or changed files
- User arguments (scope, invariants, risky areas, reviewer roles)
- Existing contract expectations (routes, schemas, SSE/status behavior, public symbols)

### Required behavior
- Produce concrete, verifiable checks (avoid vague advice).
- Separate checks by reviewer role.
- Include expected evidence for each check (tests, logs, code locations, behavior observations).
- Prioritize checks that protect externally visible behavior.

### Non-goals unless explicitly requested
- No conducting the review — produce the checklist only.
- No prescribing approval or rejection decisions — flag issues, not verdicts.
- No adding checks unrelated to the stated reviewer roles and risk surface.

### Output format
- **Overview**: 1-2 lines on refactor risk profile
- **Role-based checklist**:
  - **API/Contract reviewer**
  - **Performance reviewer**
  - **Testing/QA reviewer**
  - **Security reviewer**
- **Critical must-pass gates**: blockers before merge
- **Nice-to-have checks**: optional but valuable
- **Review completion criteria**: explicit done definition
- **Optional next command**: one slash command

### Checklist item structure
For each item include:
- Check
- Why it matters
- Evidence to request
- Pass/fail signal

### Optional next commands
- `/refactor-verify`
- `/refactor-pr-summary`
- `/refactor-merge-gate`
- `/refactor-done-check`
- `/refactor-handoff`
- `/refactor-next-step`
- `/refactor-command-cheatsheet`
- `/refactor-workflow-audit`
- `/refactor-workflow-registry`
- `/refactor-routing-matrix`

### Example invocations
- `chat SSE refactor: API + QA + security checklist, preserve event payload shape`
- `provider cleanup: contract and regression-focused reviewer-checklist`
