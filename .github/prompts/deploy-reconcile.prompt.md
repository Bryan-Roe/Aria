---
description: "Reconcile local fixes with deployed runtime state and produce exact push/restart/rebuild actions"
name: "Deploy Reconcile"
argument-hint: "Paste symptom + logs + branch/deploy context"
agent: full-stack-debugger
---
You are reconciling a code/deployment mismatch.

Input:
- `{{input}}` = symptom, logs, deployment target (HF Space, Azure Function, container), and current branch status.

Task:
1. Determine if the issue is caused by code defects, stale deployment artifacts, or both.
2. Identify the minimal required actions to converge runtime with source of truth.
3. Provide precise operator commands and expected log changes.

Procedure:
1. Extract the current runtime signature from logs (file, line, API mismatch, exception).
2. Compare against workspace source:
   - Is the failing signature present locally?
   - Are fixed files tracked/staged/committed?
3. If mismatch indicates stale deployment:
   - provide exact `git` steps (status, add, commit, push)
   - provide platform restart/rebuild steps
4. If code fix is still required:
   - propose smallest patch and focused validation checks
5. Return a deployment checklist with clear stop/go criteria.

Output format:
- **Diagnosis** (code bug vs stale deploy vs mixed)
- **Evidence** (2-4 bullets)
- **Required actions** (ordered commands)
- **Expected confirmation** (specific log line or behavior)
- **Fallback action** (if still failing)

Constraints:
- Keep advice deterministic and command-ready.
- Do not suggest broad refactors during incident reconciliation.
