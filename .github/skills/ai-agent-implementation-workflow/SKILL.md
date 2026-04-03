---
name: ai-agent-implementation-workflow
description: "Implement agentic behaviors safely with clear tool boundaries, deterministic contracts, and incremental verification across prompts, tools, and orchestration code."
argument-hint: "Describe the agent behavior to implement, required tools, and expected output schema."
---

# AI Agent Implementation Workflow

## What This Skill Produces

Use this skill to implement or update agent behavior with stable contracts. The expected result is:

- explicit agent goal and decision boundaries
- predictable tool invocation flow
- schema-safe outputs for downstream consumers
- graceful fallback when tools/providers fail
- targeted tests or smoke checks proving behavior

## When to Use

Use this skill when you need to:

- add a new agent workflow
- refine tool usage logic for an existing agent
- fix agent output/schema instability
- harden retry/fallback behavior in agent loops
- align agent behavior across CLI/API/UI surfaces

Common trigger phrases:

- "implement this agent behavior"
- "add tool-calling to the agent"
- "fix unstable agent responses"
- "make the agent robust"
- "agent output schema keeps breaking"

## Procedure

1. Define contract first
   - Lock input/output schema and required fields.
   - Clarify what is best-effort vs required behavior.

2. Constrain tool boundaries
   - List which tools can be called and for what reasons.
   - Keep side-effecting actions explicit and auditable.

3. Implement minimal orchestration
   - Prefer small deterministic control flow over deep branching.
   - Make retries bounded and reason-aware.

4. Handle degraded mode intentionally
   - Return actionable errors when hard requirements are missing.
   - Use safe fallback only when it preserves contract meaning.

5. Verify behavior incrementally
   - Add focused tests/smokes for primary path + fallback path.
   - Confirm output schema is stable across paths.

6. Validate integration surface
   - Ensure consuming endpoints/UI can parse new outputs.
   - Avoid silent breaking changes in event/JSON structure.

## Quality Checks

Before finishing, confirm that:

- output schema is deterministic and documented
- tool usage boundaries are explicit
- retries/fallbacks are bounded and observable
- failures are actionable, not silent
- integration consumers remain compatible
