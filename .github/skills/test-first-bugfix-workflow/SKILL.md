---
name: test-first-bugfix-workflow
description: 'Fix regressions by reproducing them with the smallest failing test or smoke case first, then implementing the minimal repair and rerunning focused checks. Use when a bug, flaky behavior, or failing test needs disciplined reproduction and verification.'
argument-hint: 'Describe the bug, failing test, subsystem, or behavior to reproduce first.'
---

# Test-First Bugfix Workflow

## What This Skill Produces

Use this skill to convert an observed bug into a reproducible failing check, then a verified fix. The expected result is:
- a concrete reproduction path
- the smallest practical failing test or smoke check
- a minimal code change tied directly to the reproduced failure
- focused regression coverage after the fix

## When to Use

Use this skill when you need to:
- fix a regression without guessing
- turn a manual repro into a repeatable test
- narrow a flaky failure to one layer of the system
- repair behavior while avoiding broad refactors
- improve confidence in a bug fix before wider validation

Common trigger phrases:
- "write a failing test first"
- "fix this regression"
- "reproduce then patch"
- "I need a minimal bugfix"
- "make the failing behavior testable"
- "turn this repro into a test"

## Procedure

1. Capture the bug precisely
   - Write down the exact input, environment, endpoint, command, or sequence that fails.
   - Separate the symptom from the suspected root cause.

2. Choose the narrowest verification layer
   - Prefer a unit or focused integration test before full end-to-end coverage.
   - If a test is not practical yet, start with a deterministic smoke check and convert it into a test as soon as possible.

3. Reproduce before fixing
   - Run the smallest existing relevant test or request path.
   - Confirm the failure is real and repeatable before editing code.

4. Add or tighten the failing check
   - Create a test that captures the broken behavior with minimal setup.
   - Keep the assertion specific to the regression instead of encoding unrelated behavior.

5. Implement the smallest fix
   - Change only the code needed to make the failing check pass.
   - Avoid opportunistic refactors while the regression is being repaired.

6. Re-run focused verification
   - Re-run the new failing check first.
   - Then run the closest adjacent tests or repository test runner path needed for confidence.
   - Use `scripts/test_runner.py --unit` or focused `pytest` runs where appropriate.

7. Finish with regression protection
   - Check whether another nearby edge case deserves one additional assertion or test.
   - Summarize the repro, fix, and verification path clearly.

## Quality Checks

Before finishing, confirm that:
- the bug was reproduced before the code change
- the new or tightened test would fail without the fix
- the code change is smaller than the surrounding bug description
- focused tests pass after the repair
- the final summary explains both the bug and the verification
