---
description: "Rapidly triage AGI smoke CI failures and produce a ranked root-cause hypothesis plus next action plan."
name: "AGI Smoke Triage"
argument-hint: "Failing job/test + key log excerpt + context (PR, branch, recent change)"
agent: full-stack-debugger
---

Perform a fast, evidence-first triage for AGI smoke CI failures.

## Goal
Determine the most likely root cause quickly, minimize guesswork, and return a concrete next-step plan.

## Scope
- In scope: `.github/workflows/agi-smoke.yml`, AGI smoke tests, and directly-related contract code.
- Out of scope: broad remediation or large refactors (unless explicitly requested).

## Triage protocol
1. **Capture failure signature**
   - Extract exact failing test/step, error class, and first relevant stack frame.
   - Note deterministic vs intermittent behavior.

2. **Classify likely domain**
   - Environment/dependency mismatch
   - Workflow config issue
   - Contract drift (routes, payload, auth, SSE)
   - Test fragility / timing / flake

3. **Rank top hypotheses (1–3)**
   - For each: confidence, why it fits evidence, and fastest falsification check.

4. **Recommend immediate action**
   - Propose the shortest command/check sequence to confirm root cause.
   - Include one fallback path if first check fails.

## Constraints
- No speculative code edits.
- No assertion weakening without explicit contract rationale.
- Keep recommendations minimal and reproducible.

## Output format (required)
- **Failure signature**
- **Likely domain**
- **Ranked hypotheses** (with confidence)
- **Fastest verification steps** (commands/checks)
- **Recommended next move** (single best action)

## Example invocations
- `Triage AGI smoke: test_agi_persistence_auth fails with 401 on PR build.`
- `Quick triage for agi-smoke.yml timeout in Run AGI smoke tests step.`
- `Diagnose intermittent SSE DONE marker failure in local AGI integration smoke.`
