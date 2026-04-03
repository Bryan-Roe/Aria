---
description: "Debug and diagnose issues across the full Aria platform stack — from client JS through Python servers, Azure Functions, training pipelines, and quantum workflows."
name: "Debug"
argument-hint: "Issue description + affected component (example: symptom + stack trace or error + component name)"
agent: full-stack-debugger
---

Systematically debug the described issue using this diagnostic protocol:

**Step 1 — Characterize:**
- What is the exact error or unexpected behavior?
- Which component is affected? (Aria UI, chat API, training, quantum, infra)
- Is it reproducible? What changed recently?

**Step 2 — Quick Health Check:**
- Run `/api/ai/status` for system-wide diagnostics
- Check `data_out/` status files for orchestrator state
- Verify environment variables and dependencies

**Step 3 — Hypothesize & Test:**
Form ranked hypotheses (most likely first):
1. Environment/config issue (missing vars, wrong ports)
2. Dependency issue (missing packages, version conflicts)
3. Logic error (conditions, state, race conditions)
4. Integration issue (API contracts, serialization)

Test each hypothesis with minimal, targeted checks.

**Step 4 — Fix & Verify:**
- Apply the minimum change to fix the root cause
- Run related tests: `pytest tests/ -k "relevant_test" -v`
- Confirm the original issue is resolved
- Check for regressions

**Key ports:** Aria=8080, Functions=7071
**Key files:** `function_app.py`, `apps/aria/server.py`, `shared/chat_providers.py`
