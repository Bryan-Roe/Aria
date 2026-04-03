---
name: test-suite-triage-workflow
description: 'Triage failing test runs quickly by isolating suite scope, marker filters, environment prerequisites, and flaky boundaries before code edits. Use when pytest failures are broad/noisy, CI and local results differ, or endpoint/E2E tests fail due to setup and not logic regressions.'
argument-hint: 'Describe the failing command, markers/suites involved, and whether failure reproduces locally, in CI, or both.'
---

# Test Suite Triage Workflow

## What This Skill Produces

Use this skill to separate real regressions from environment/scope noise. The expected result is:
- a narrowed failing test surface
- explicit prerequisite checks for the target suite
- root-cause classification (logic regression vs setup issue vs flake)
- a focused repair/mitigation path with minimal reruns

## When to Use

Use this skill when you need to:
- triage failing pytest runs in local or CI contexts
- isolate failures by marker (`slow`, `azure`, `integration`) or suite
- debug Aria endpoint/E2E tests requiring running services
- reconcile passing unit tests with failing integration/browser tests

Common trigger phrases:
- "tests are failing everywhere"
- "passes locally but fails in CI"
- "pytest is noisy"
- "which failures are real regressions"
- "integration tests fail due to setup"
- "E2E test can’t reach server"

## Procedure

1. Start with scope reduction
   - Re-run the smallest failing suite first, not the whole test matrix.
   - Use marker filters to separate environment-heavy tests from core logic.

2. Classify the failing layer
   - Unit failure: likely code regression.
   - Integration failure: often contract/dependency/setup.
   - E2E/browser failure: frequently service availability or route/static issues.

3. Validate prerequisites before code edits
   - Confirm required services/ports for Aria or Functions tests.
   - Confirm env vars (`ARIA_SERVER_URL`, `PYTHONPATH`, provider keys if needed).
   - Confirm test data paths and non-modification of `datasets/`.

4. Compare local and CI assumptions
   - Check marker selection and command differences.
   - Check OS/runtime/dependency mismatches when reproduction diverges.

5. Fix or quarantine with evidence
   - For real regressions: patch minimally and re-run targeted tests.
   - For setup issues: fix test harness/configuration, not product logic.
   - For flakes: capture repeatability and add stabilization before broad reruns.

6. Rebuild confidence incrementally
   - Targeted failing tests first.
   - Nearby suite next.
   - Full relevant runner (`scripts/test_runner.py --unit` / `--all`) last.

7. Record triage result clearly
   - Document failing class, root cause, and what verification was run.
   - Avoid declaring green based on one non-representative run.

## Quality Checks

Before finishing, confirm that:
- failing tests were narrowed before fixes
- suite prerequisites were validated explicitly
- logic regressions were separated from environment/setup failures
- reruns progressed from narrow to broad scope
- final status reflects actual test surface, not partial runs
