---
description: "Audit AGI smoke tests for flakiness, quantify instability, and propose deterministic hardening steps without reducing coverage."
name: "AGI Smoke Flake Audit"
argument-hint: "Target tests/workflow + observed intermittent failures + desired confidence threshold"
agent: full-stack-debugger
---

Run a structured flake audit for AGI smoke CI and return an actionable stabilization plan.

## Goal
Identify flaky behavior, measure confidence, and recommend the smallest deterministic fixes.

## Scope
- AGI smoke workflow and test subset only.
- Adjacent checks only when needed to validate contract assumptions.

## Audit workflow
1. **Define sample set**
   - Select target tests/steps and run count (e.g., 10/20 iterations).

2. **Measure stability**
   - Record pass/fail frequency, error signatures, and timing variance.

3. **Cluster failure modes**
   - Group by root-cause pattern (timing, env drift, network dependency, nondeterministic assertion, shared state leakage).

4. **Propose hardening changes**
   - Prefer deterministic fixtures/setup, explicit waits with bounded timeout, stable assertions, and state isolation.
   - Use retries only when root cause cannot be removed immediately, and document trade-offs.

5. **Estimate residual flake risk**
   - Provide expected improvement and confidence level.

## Guardrails
- Do not reduce meaningful coverage to make CI green.
- Do not hide failures with broad retries or ignored exit codes.
- Keep changes minimal and reversible.

## Output format (required)
- **Audit target**
- **Run matrix** (iterations, pass/fail counts)
- **Failure clusters**
- **Recommended hardening plan** (prioritized)
- **Expected impact** (flake-rate delta)
- **Residual risk + follow-ups**

## Example invocations
- `Audit flakiness in AGI persistence smoke tests with 20-run sample and 95% confidence target.`
- `Find intermittent failures in AGI SSE smoke and propose deterministic fixes only.`
- `Run a flake audit for agi-smoke.yml and return a prioritized hardening plan.`
