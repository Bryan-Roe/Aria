---
name: create-hook-workflow
description: "Create, test, and validate VS Code agent hooks in .github/hooks/ — block unsafe tool calls, inject context reminders, or run compliance audits at lifecycle events. Use when: adding a hook, writing hook script, PreToolUse guard, PostToolUse audit, blocking writes to protected paths, requiring approvals before shell commands, adding pip-audit gate, dataset immutability guard, quantum cost gate, create a hook, create hook, new hook, hook for safety, hook to block, hook to audit."
argument-hint: "Describe the policy to enforce: what should be blocked, warned about, or injected, and when."
---

# Create Hook Workflow

## What This Skill Produces

Use this skill to turn a policy need into a tested, production-ready hook. The expected output is:
- a repo-wide policy scan covering root instructions, `.github/instructions/`, existing hooks, related scripts, and recent terminal/conversation signals
- a Python companion script in `.github/hooks/scripts/` with correct exit-code semantics
- a JSON manifest in `.github/hooks/` mapping lifecycle events to the script
- smoke-test results for at least three payloads (block, allow, and inject/warn)
- a summary of what the hook enforces, env-var opt-ins, and any ambiguous decisions for follow-up

## When to Use

Use this skill when you need to:
- guard a protected path or resource from agent writes (e.g. `datasets/` is read-only)
- run a compliance check before or after a file is saved (e.g. `pip-audit` on requirements files)
- inject a context reminder when a prompt or tool call matches a pattern
- enforce cost or safety gates before irreversible operations (e.g. quantum QPU, destructive shell commands)
- review an existing hook that isn't firing or is blocking too aggressively

Common trigger phrases:
- "create a hook"
- "add a hook to block"
- "write a PreToolUse guard"
- "add pip-audit gate"
- "quantum cost gate"
- "dataset immutability hook"
- "inject a reminder"
- "hook to enforce"

## Decision Map

Before writing anything, choose the right event(s) and exit behavior:

| Goal | Events | Exit on match |
|------|--------|---------------|
| Block file write to protected path | `PreToolUse` | 1 (hard block) |
| Run audit before save, warn if fails | `PreToolUse`, `PostToolUse` | 0 (warn) or 1 (opt-in via env var) |
| Inject reminder into conversation | `UserPromptSubmit` | 0 (always) |
| Block agent from stopping prematurely | `Stop` | 1 (conditional) |
| Check written file state after save | `PostToolUse` | 0 (warn) |

**Warn-first default:** Start with exit 0 (warn) unless the risk is catastrophic. Use an env var like `MY_HOOK_BLOCK=true` to let callers opt in to hard-blocking later. This avoids infinite agent retry loops where the agent keeps getting blocked on the fix it's trying to apply.

## Procedure

### 1. Extract policy signals

- Start with a repo-wide policy scan instead of looking at one file in isolation.
- Read root-level guidance first: `.github/copilot-instructions.md`, `AGENTS.md`, and any top-level workflow or safety docs that shape agent behavior.
- Scan `.github/instructions/` for file-scoped rules that may imply a reusable guardrail.
- Scan `.github/hooks/` and `.github/hooks/scripts/` to avoid duplicating existing enforcement.
- Scan recent terminal history and recent conversations for repeated manual checks, recurring warnings, or costly mistakes waiting to happen.
- Inspect adjacent configs or scripts that encode safety expectations, such as orchestrator YAML, test runners, deployment scripts, or compliance scripts.
- Classify each signal: **block** (exit 1), **warn** (print + exit 0), or **inject** (print reminder + exit 0).
- Prefer signals that recur across multiple files or workflows over one-off local conventions.

### 2. Prioritize and scope to 1–3 hooks per session

- Prioritize by consequence severity: data loss > cost > compliance > convenience.
- Prefer hooks whose policy is supported by multiple repo sources, such as both instructions and automation scripts.
- Pick the top 1–3 candidates; defer the rest.
- For each candidate, answer:
  - What tool names trigger it? (file writes, shell, etc.)
  - What pattern in the payload identifies the unsafe case? (path regex, content search, JSON field)
  - Should it block or warn?
  - Does it need a `PostToolUse` companion to catch misses?

### 3. Write the companion Python script

Place at `.github/hooks/scripts/<name>.py`. Follow this structure:

```python
#!/usr/bin/env python3
"""One-line description of what this hook enforces.

Events handled:
  PreToolUse  — describe what it checks
  UserPromptSubmit — describe what it injects (if any)

Exit codes:
  0  → allow / warn only
  1  → block
"""

import json, os, re, sys
from typing import Any

# Constants — put all tunable values here
_PATTERN = re.compile(r"your_pattern_here", re.IGNORECASE)
_WRITE_TOOLS = {"write_file", "create_file", "replace_string_in_file", ...}
_BLOCK = os.environ.get("MY_HOOK_BLOCK", "false").lower() == "true"


def _walk(obj: Any):
    """Recursively yield (key, value) from nested dicts/lists."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    event = os.environ.get("COPILOT_HOOK_EVENT", "PreToolUse")

    if event == "UserPromptSubmit":
        # inject reminder without blocking
        ...
        sys.exit(0)

    if event in ("PreToolUse", "PostToolUse"):
        tool = (payload.get("toolName") or payload.get("name") or "").lower()
        if tool in _WRITE_TOOLS:
            path = payload.get("filePath") or payload.get("path") or ""
            if _PATTERN.search(path):
                if _BLOCK:
                    print("🛑  BLOCKED: ...", file=sys.stderr)
                    sys.exit(1)
                else:
                    print("⚠️  WARNING: ...")

    sys.exit(0)

if __name__ == "__main__":
    main()
```

**Key implementation rules:**
- Always read from `stdin`, never from files or argv.
- Always handle `json.JSONDecodeError` and empty stdin gracefully — exit 0.
- Extract tool name from `payload.get("toolName") or payload.get("name")`, lowercased.
- Extract file path from `payload.get("filePath") or payload.get("path")`.
- Extract shell command from `payload.get("command") or payload.get("cmd")`.
- Print block messages to `stderr`; print warnings/reminders to `stdout`.
- Exit 1 only for hard blocks; exit 0 for everything else including errors.
- Use `_walk(payload)` for deep search across arbitrary payload shapes.

### 4. Write the JSON manifest

Place at `.github/hooks/<name>.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python3 .github/hooks/scripts/<name>.py",
        "timeout": 5
      }
    ]
  }
}
```

**Timeout guidelines:**
- Pure in-process checks (path regex, JSON search): `5` seconds
- Subprocess calls (pip-audit, pytest, linters): `60`–`120` seconds
- Network calls (API checks, Azure auth): `30`–`60` seconds

**Event set recommendations:**
- File-write guard: `PreToolUse` only
- Compliance audit: `PreToolUse` + `PostToolUse` (belt-and-suspenders)
- Reminder injection: `UserPromptSubmit` only
- Completeness gate: `Stop`

### 5. Smoke-test with representative payloads

Run at least three payloads and capture exit codes:

```bash
# Block case — should exit 1
echo '{"toolName":"write_file","filePath":"<protected_path>","content":"..."}' \
  | COPILOT_HOOK_EVENT=PreToolUse python3 .github/hooks/scripts/<name>.py
echo "exit=$?"

# Allow case — should exit 0
echo '{"toolName":"write_file","filePath":"data_out/safe.json","content":"..."}' \
  | COPILOT_HOOK_EVENT=PreToolUse python3 .github/hooks/scripts/<name>.py
echo "exit=$?"

# Inject/warn case — should print reminder, exit 0
echo '{"userMessage":"I want to modify <protected_path>"}' \
  | COPILOT_HOOK_EVENT=UserPromptSubmit python3 .github/hooks/scripts/<name>.py
echo "exit=$?"

# Graceful empty-stdin case — should exit 0 silently
echo '' | python3 .github/hooks/scripts/<name>.py; echo "exit=$?"

# Graceful invalid JSON case — should exit 0 silently
echo 'not json' | python3 .github/hooks/scripts/<name>.py; echo "exit=$?"
```

Expected results:
- Block case: exit 1, block message on stderr
- Allow case: exit 0, no output
- Inject case: exit 0, reminder on stdout
- Empty/invalid: exit 0, no output

### 6. Validate

```bash
cd /workspaces/Aria

# Python syntax
python3 -m py_compile .github/hooks/scripts/<name>.py && echo "✅ syntax OK"

# JSON validity
python3 -c "import json; json.load(open('.github/hooks/<name>.json')); print('✅ JSON OK')"

# Inventory all hooks
find .github/hooks -type f | sort
```

### 7. Summarize and surface ambiguities

After the hook is created and tested, provide:
1. **What it enforces** — in plain language, one sentence per event
2. **How to test it** — copy-paste smoke-test commands
3. **Ambiguous decisions** — at least two questions to refine behavior (e.g. "should this hard-block or warn?", "should Stop be gated too?")
4. **Next hook proposals** — 1–2 related hooks that follow naturally from the same policy signals

## Quality Checks

Before marking the task complete, confirm:
- [ ] Policy signals were gathered from the entire repo scope, not just one instructions file or one prompt
- [ ] Script exits 0 on empty stdin and malformed JSON
- [ ] Script exits 1 only for confirmed block cases — never for errors or parse failures
- [ ] At least three payloads smoke-tested with expected exit codes
- [ ] JSON manifest syntax-checked; timeout is appropriate for operation type
- [ ] `stdin` is the only input surface (no hardcoded paths, no argv, no file reads except PostToolUse disk reads)
- [ ] Constants (patterns, tool names) are at module scope — easy to tune
- [ ] Warn-first default unless risk is catastrophic; env-var opt-in for hard-block
- [ ] Summary includes ambiguous decisions and next hook proposals

## Patterns and Gotchas

**Multiple tool name formats in payloads.** Payloads may use `toolName`, `tool_name`, or `name`. Always normalize with `(payload.get("toolName") or payload.get("tool_name") or payload.get("name") or "").lower()`.

**The `parameters` sub-object.** Some tool payloads nest arguments: `payload["parameters"]["filePath"]`. Check both top-level and under `parameters`.

**Infinite retry loops.** If a hook hard-blocks a write tool and the agent is trying to fix the problem in that very file, it will retry infinitely. Prefer warn-first with an opt-in env var for hard-block. For `Stop` hooks, use a retry counter pattern (see `enforce_task_complete.py` for reference).

**PostToolUse disk reads.** When `PostToolUse` fires, the file has already been saved to disk. The script can `open(path)` directly instead of parsing content from the payload.

**Event detection.** The VS Code agent runner sets `COPILOT_HOOK_EVENT` in the environment before invoking the script. Always read it via `os.environ.get("COPILOT_HOOK_EVENT", "PreToolUse")` — default to the most common event so the script also works when called manually for testing.

**Timeout realism.** `pip-audit` on a large requirements file can take 30–60s on a cold run. Set timeout to `90` for audit-style hooks to avoid false blocks from slow network.

**Repo-wide evidence beats single-file intuition.** If a policy only appears in one speculative comment but is absent from instructions, scripts, tests, and established patterns, treat it as weak evidence. Hooks should encode durable repo conventions, not a one-off hunch.
