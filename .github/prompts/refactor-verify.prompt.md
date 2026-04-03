---
description: "Use when validating a refactor: verify contract parity, detect regressions, and assess merge readiness."
name: "Refactor Verify"
argument-hint: "Refactor scope + expected unchanged behavior + required checks (example: function_app.py + SSE stable + unit,type check)"
agent: agent
---

Validate that a completed refactor preserved required behavior and did not introduce regressions.

Suggested next step:
- Run `/refactor-pr-summary` to convert verification evidence into a reviewer-ready PR description.
- Run `/refactor-reviewer-checklist` to generate role-based merge review gates.
- If flow is unclear, run `/refactor-next-step` for a single recommended next command.
- Run `/refactor-merge-gate` when you need an explicit GO/NO-GO merge decision.
- Run `/refactor-done-check` for a strict final completion verdict.
- Run `/refactor-evidence-log` to persist reusable verification evidence for downstream steps.
- Run `/refactor-workflow-audit` when workflow command/stage drift is suspected.
- Run `/refactor-workflow-registry` to refresh canonical workflow vocabulary.
- Run `/refactor-routing-matrix` to inspect stage-transition topology and routing gaps.

### Inputs
- Refactored code (selected diff or files)
- Declared expectations for unchanged behavior
- Required checks to run (unit tests, type check, contract parity, integration)
- Existing project contracts and testing conventions

### Required behavior
- Compare expected invariants vs observed changes.
- Flag any contract drift (API, schema, route, streaming/status behavior).
- Prioritize findings by severity and confidence.
- Propose minimal remediation steps for each high-priority issue.

### Non-goals unless explicitly requested
- No making code changes to fix discovered regressions — verify and report only.
- No approving merge readiness without complete evidence for all required checks.
- No suppressing or downgrading findings to achieve a passing result.

### Output format
- **Verification summary**: pass/fail by area
- **Contract parity table**: invariant, status, evidence
- **Regression findings**: severity + location + suggested fix
- **Recommended test run set**: focused first, broader second
- **Merge readiness**: ready | needs-fix with concise rationale
- **Optional next command**: one slash command

### Optional next commands
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-merge-gate`
- `/refactor-done-check`
- `/refactor-evidence-log`
- `/refactor-next-step`
- `/refactor-command-cheatsheet`
- `/refactor-workflow-audit`
- `/refactor-workflow-registry`
- `/refactor-routing-matrix`

### Example invocations
- `verify recent /api/chat refactor: SSE event schema must remain identical`
- `verify chat provider cleanup: fallback order and readiness checks unchanged`
