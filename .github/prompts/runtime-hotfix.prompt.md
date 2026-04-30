---
description: "Fix runtime errors from logs by applying the smallest safe patch and verifying import/startup"
name: "Runtime Hotfix"
argument-hint: "Paste traceback + runtime context (e.g., platform/container + target file)"
agent: full-stack-debugger
---
You are fixing a **live runtime error** from logs.

Input:
- `{{input}}` = traceback/log excerpt and environment context.

Goal:
1. Isolate the most likely root cause from the traceback.
2. Apply the **smallest safe code change**.
3. Verify with targeted checks.
4. Return a deployment-ready summary.

Workflow:
1. Parse traceback and identify:
   - failing file + line
   - exact API/contract mismatch
   - whether issue is code regression vs stale deployment
2. Read only the minimal relevant files first.
3. Patch the specific failure point (avoid unrelated refactors).
4. Run focused verification:
   - syntax check (`python -m py_compile <file>`)
   - import/smoke check for startup path
   - one direct function-level smoke call if applicable
5. If logs suggest stale deployment, explicitly report:
   - why the deployed artifact is stale
   - exact push/redeploy steps
6. If fix exists locally but untracked, stage/commit with a precise message.

Output format:
- **Root cause** (1-2 bullets)
- **Files changed** (with brief why)
- **Verification** (commands + pass/fail)
- **Deployment actions** (only if needed)
- **Residual risk** (single line)

Constraints:
- Keep changes minimal and reversible.
- Preserve existing provider/fallback behavior and public interfaces unless traceback requires otherwise.
- Prefer deterministic checks over long broad test runs.

Use this repo’s conventions for status reporting and concise operator guidance.
