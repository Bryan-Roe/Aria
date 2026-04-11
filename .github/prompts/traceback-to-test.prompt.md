---
description: "Convert a production traceback into a focused regression test and minimal code fix workflow"
name: "Traceback to Test"
argument-hint: "Paste traceback + relevant file/module context"
agent: full-stack-debugger
---
You are turning a traceback into a reproducible regression test.

Input:
- `{{input}}` = traceback/logs plus relevant module, function, or endpoint context.

Goal:
1. Reproduce the failure with the smallest failing test or smoke case.
2. Implement the minimum fix.
3. Re-run focused verification to prove regression is resolved.

Procedure:
1. Parse traceback and isolate failing frame (file, line, symbol, exception class).
2. Draft the smallest test that reproduces exactly that failure mode.
3. Identify current behavior vs expected behavior.
4. Apply a minimal patch (no unrelated cleanup).
5. Run targeted tests:
   - new regression test
   - nearest existing suite for touched code
6. Summarize the regression guard added.

Output format:
- **Failure contract** (what broke)
- **New test** (path + intent)
- **Fix summary** (path + minimal change)
- **Verification** (commands + pass/fail)
- **Residual risk** (one line)

Constraints:
- Keep tests deterministic and narrow.
- Prefer explicit assertions over broad integration flows.
- Preserve public API behavior unless traceback demands a contract correction.
