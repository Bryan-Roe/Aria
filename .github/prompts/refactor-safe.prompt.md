---
description: "Use when implementing a refactor: keep behavior stable, minimize diff risk, and include verification evidence."
name: "Safe Refactor"
argument-hint: "Target + goals + constraints (example: scope + goal + invariant)"
agent: agent
---

Safely refactor the selected code or file scope using the user's arguments as hard constraints.

Optional workflow:
- Run `/refactor-precheck` first for risk mapping and invariants.
- Run `/refactor-verify` after edits to confirm behavior parity.
- Run `/refactor-pr-summary` to produce a reviewer-ready PR description.
- If uncertain at any point, run `/refactor-next-step` to choose the best next command.
- For one-line command output, run `/refactor-command-cheatsheet`.
- If process routing feels inconsistent, run `/refactor-workflow-audit`.
- If stage/command canon is unclear, run `/refactor-workflow-registry`.
- If stage-transition topology is unclear, run `/refactor-routing-matrix`.

### Argument normalization
- Parse arguments into: **target**, **primary goal**, **must-preserve constraints**, and **validation expectations**.
- If any of these are missing, infer conservatively from selected context and state assumptions explicitly before editing.
- Treat explicit phrases like "no API changes", "preserve SSE", "do not rename public symbols", or "minimal diff" as strict requirements.

### Inputs
- Selected code and surrounding file context
- User-provided slash-command arguments (target, goals, constraints)
- Existing project conventions and instruction files

### Required behavior
- Preserve externally visible behavior by default, but allow clearly low-risk quality improvements when they do not alter public contracts.
- Keep changes minimal and incremental.
- Avoid unrelated formatting churn.
- Preserve public routes, API contracts, and streaming/status schemas.
- Do not introduce hardcoded secrets.
- Maintain dataset immutability (`datasets/` read-only, outputs in `data_out/`).

### Non-goals unless explicitly requested
- No broad architecture rewrites.
- No large-scale renaming across unrelated modules.
- No dependency additions unless clearly justified by the requested refactor.

### Required workflow
1. Identify current behavior and likely regressions.
2. Propose a short edit plan and apply changes incrementally.
3. Add or update tests only where needed to protect behavior.
4. Run broader validation when feasible, and at minimum run focused checks for touched areas.
5. Summarize risk, what changed, and how it was verified.

### Output format
- **Assumptions from arguments**: normalized interpretation of user inputs
- **Summary**: what was refactored and why
- **Files changed**: concise per-file purpose
- **Behavior parity check**: what remained intentionally unchanged
- **Validation run**: tests/checks executed and results
- **Residual risks / follow-ups**: any caveats and optional next steps
- **Optional next command**: one slash command

### Optional next commands
- `/refactor-precheck`
- `/refactor-verify`
- `/refactor-pr-summary`
- `/refactor-reviewer-checklist`
- `/refactor-handoff`
- `/refactor-next-step`
- `/refactor-command-cheatsheet`
- `/refactor-workflow-audit`
- `/refactor-workflow-registry`
- `/refactor-routing-matrix`

### Example invocations
- `function_app.py /api/chat: extract helper for SSE event framing, preserve wire format, no route changes`
- `shared/chat_providers.py: deduplicate readiness checks, keep fallback order unchanged`
- `apps/aria/server.py: simplify command parsing branch logic, preserve request/response schema`
