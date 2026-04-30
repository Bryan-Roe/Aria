---
name: runtime-hotfix-workflow
description: 'Triage and fix production/runtime errors from traceback logs with minimal patches, focused verification, and deployment reconciliation. Use when you have stack traces, startup failures, container logs, import-time crashes, or stale-deploy symptoms.'
argument-hint: 'Paste traceback/logs, runtime context, and expected behavior.'
---

# Runtime Hotfix Workflow

## What This Skill Produces

Use this skill to turn a raw runtime error into a safe, deployable fix. The expected output is:
- a precise root cause mapped to file and line
- a minimal patch at the true failure point
- focused verification commands with clear pass/fail
- deployment reconciliation notes when stale artifacts are involved

## When to Use

Use this skill when you need to:
- resolve startup/import-time crashes from container logs
- fix API/runtime errors where tracebacks point to signature or contract mismatch
- diagnose why local code works but deployed code still fails
- patch urgent regressions without broad refactors

Common trigger phrases:
- "runtime error"
- "traceback"
- "container logs"
- "startup failure"
- "works locally but fails in deployment"
- "hotfix this now"

## Procedure

1. Extract the concrete failing frame
   - Identify file, line number, failing symbol/signature, and immediate exception class.
   - Ignore downstream noise unless the top frame is ambiguous.

2. Confirm code-vs-deploy state
   - Search for the failing pattern in current workspace files.
   - If mismatch exists between logs and workspace, treat as likely stale deployment.

3. Patch minimally at the failing point
   - Change only the arguments/contracts needed to satisfy runtime behavior.
   - Avoid speculative refactors or style-only edits.

4. Run focused verification
   - Syntax check the touched file(s).
   - Import/startup smoke check the exact runtime path.
   - One direct function-level check for the failing behavior where possible.

5. Reconcile deployment if needed
   - Ensure modified files are tracked/staged/committed.
   - Provide exact push/restart/rebuild steps and what log line should disappear.

6. Report with operator clarity
   - Root cause
   - Files changed
   - Verification evidence
   - Deployment actions
   - Residual risk

## Quality Checks

Before finishing, confirm that:
- the traceback signature no longer appears in local smoke checks
- touched files are minimal and directly related to the failure
- staged/committed state reflects the fix when deployment is involved
- guidance includes exact next operator actions for production rollout
