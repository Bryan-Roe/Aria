---
description: "Use when preparing release communication for refactors: generate changelog and release-note text from verified behavior-parity evidence."
name: "Refactor Release Note"
argument-hint: "Audience + scope + user-visible impact + risk notes (example: engineers + function_app.py + no API changes + low risk)"
agent: agent
---

Generate release communication artifacts for a completed refactor.

Optional companion:
- Run `/refactor-workflow-audit` if handoff/release workflow routing appears inconsistent.
- Run `/refactor-workflow-registry` to align release terminology with canonical workflow stages.
- Run `/refactor-routing-matrix` to verify transition coverage before release handoff.

### Inputs
- Selected diff or merged change summary
- Verification evidence (contract parity, test outcomes, risk notes)
- User arguments (audience, scope, tone, detail level, user-visible impact)

### Required behavior
- Distinguish user-visible vs internal-only changes.
- Avoid claiming behavior changes unless explicitly evidenced.
- Keep wording accurate, concise, and confidence-calibrated.
- Include operational caveats when relevant (rollback notes, feature flags, migration notes).

### Non-goals unless explicitly requested
- No marketing copy or unverified capability claims.
- No including breaking changes not confirmed in the evidence log.
- No modifying source code or test files.

### Output format
- **Release note (customer-facing)**: short and plain-language
- **Changelog entry (technical)**: concise bullet(s) with scope and evidence
- **Upgrade/ops notes**: rollout caveats, monitoring pointers, rollback hint
- **No-impact statement**: explicit line when change is internal-only
- **Optional next command**: one slash command

### Optional variants
- Executive summary (1-2 lines)
- Support-team version (issue triage oriented)
- Internal engineering digest (risk + follow-ups)

### Optional next commands
- `/refactor-pr-summary`
- `/refactor-handoff`
- `/refactor-merge-gate`
- `/refactor-done-check`
- `/refactor-next-step`
- `/refactor-command-cheatsheet`
- `/refactor-workflow-audit`
- `/refactor-workflow-registry`
- `/refactor-routing-matrix`

### Example invocations
- `internal-only refactor: no user-facing changes, provide changelog + no-impact statement`
- `SSE refactor with preserved contract: customer-safe release-note + ops caveats`
