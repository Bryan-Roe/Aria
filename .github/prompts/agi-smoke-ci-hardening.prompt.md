---
description: "Diagnose, fix, and harden AGI smoke CI failures with minimal-risk workflow/test changes and clear merge-readiness evidence."
name: "AGI Smoke CI Hardening"
argument-hint: "CI failure symptoms + failing test names/log excerpt + desired strictness (quick fix or hardening pass)"
agent: disciplined-repo-executor
---

Stabilize the AGI smoke CI workflow and associated smoke tests with a reproducible, evidence-first process.

## Scope
- In scope: `.github/workflows/agi-smoke.yml`, AGI smoke tests under `tests/`, and minimal related code/config touched by the failing contract.
- Out of scope unless explicitly requested: broad refactors, unrelated test suites, non-AGI infrastructure changes.

## Inputs to use
- Failure signal (job name, failing step, traceback, flaky symptom)
- Current workflow config (`.github/workflows/agi-smoke.yml`)
- Test files included in AGI smoke run
- PR context (branch diff and changed files) when available

## Required workflow
1. **Characterize failure**
   - Identify deterministic failure vs flake.
   - Classify root-cause area: environment/dependency, test assumption, app contract drift, workflow misconfiguration.

2. **Reproduce locally (targeted)**
   - Run only the AGI smoke subset first.
   - If failure is flaky, run focused retries to estimate flake probability.

3. **Apply minimum viable fix**
   - Prefer the smallest change that restores contract reliability.
   - Keep workflow pinning and security posture intact.
   - Avoid masking failures (no broad `|| true`, no blanket skips without rationale).

4. **Harden**
   - Add/adjust deterministic guards (fixtures, retries only when justified, explicit env setup, stable assertions).
   - Ensure timeout and failure surfaces remain actionable.

5. **Verify**
   - Re-run AGI smoke subset.
   - If change affects broader contracts, run one additional adjacent check set.

6. **Summarize merge readiness**
   - Provide risk level, residual flake risk, and exact follow-up actions if any.

## Safety and quality constraints
- Preserve least-privilege GitHub Actions permissions.
- Keep immutable data conventions (`datasets/` untouched; outputs to `data_out/`).
- Do not introduce secrets into workflow or test code.
- Do not relax test assertions unless tied to documented contract behavior.

## Output format (required)
- **Root cause**: one-paragraph diagnosis
- **Changes made**: file-by-file bullets
- **Why this fix**: concise rationale vs alternatives
- **Validation evidence**: commands + pass/fail
- **Residual risks**: known limitations or flake caveats
- **Merge recommendation**: `ready` or `needs-follow-up`

## Example invocations
- `Harden AGI smoke CI: persistence auth test is failing intermittently on PR runs.`
- `Fix AGI smoke after route contract change; keep workflow strict and deterministic.`
- `Do a hardening pass on agi-smoke.yml and smoke tests for reliability without reducing coverage.`

## Customization knobs
- **Strictness**: `quick-fix` | `balanced` | `hardening`
- **Validation depth**: smoke-only | smoke+adjacent
- **Risk posture**: conservative (minimal edits) | proactive (add guardrails)
- **Reporting style**: concise PR note | detailed incident-style report