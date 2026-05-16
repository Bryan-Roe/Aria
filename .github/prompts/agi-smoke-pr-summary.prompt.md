---
description: "Generate a reviewer-ready PR summary for AGI smoke CI fixes with evidence, risk, and rollback notes."
name: "AGI Smoke PR Summary"
argument-hint: "Changed files + failure cause + validation outputs + remaining risks"
agent: agent
---

Produce a concise, reviewer-friendly summary for PRs that modify AGI smoke CI behavior.

## Goal
Help reviewers quickly understand what broke, what changed, why it is safe, and how it was verified.

## Required inputs
- Failing symptom before fix
- Files changed
- Validation commands/results
- Any residual risk or follow-up work

## Summary rules
- Focus on behavior and contract impact, not implementation trivia.
- Make evidence explicit (commands + outcomes).
- State risk honestly; do not over-claim certainty.
- Include rollback guidance when workflow behavior changed.

## Output format (required)
### 1) Problem
One paragraph: what failed and user impact (CI reliability/merge confidence).

### 2) Root cause
Bullet list of factual causes.

### 3) What changed
File-by-file bullets with intent.

### 4) Validation evidence
- Commands run
- Key pass/fail outcomes
- Any non-run checks and why

### 5) Risk and mitigation
- Residual risks
- Why current fix is acceptable
- Monitoring/follow-up actions

### 6) Rollback plan
Exact rollback strategy if regressions appear.

### 7) Merge recommendation
`ready` | `needs-follow-up` with one-sentence rationale.

## Example invocations
- `Summarize this AGI smoke CI fix for PR reviewers with rollback details.`
- `Create PR note: persistence endpoint smoke failures fixed by auth setup alignment.`
- `Write merge-readiness summary for agi-smoke workflow hardening changes.`
