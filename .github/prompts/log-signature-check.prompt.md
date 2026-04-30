---
description: "Check whether runtime/container log signatures match current source files and flag stale-deploy risk"
name: "Log Signature Check"
argument-hint: "Paste traceback/log block and target file path"
agent: full-stack-debugger
---
You are validating runtime log signatures against current source.

Input:
- `{{input}}` = traceback or container logs + file/module path(s).

Task:
1. Extract the strongest log signature (file, line, function/symbol, exception).
2. Locate matching or conflicting code in workspace.
3. Classify result as:
   - `match` (source likely still broken),
   - `mismatch` (stale deployment likely),
   - `insufficient evidence`.
4. Provide the smallest next action.

Output format:
- **Signature extracted**
- **Source comparison**
- **Classification**
- **Next action** (single most effective step)

Constraints:
- Do not propose large rewrites.
- Keep output concise and operator-ready.
