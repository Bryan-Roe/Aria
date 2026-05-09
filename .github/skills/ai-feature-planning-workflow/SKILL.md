---
name: ai-feature-planning-workflow
description: "Plan AI features from problem statement to measurable rollout criteria, including model/provider assumptions, fallback behavior, and validation checkpoints."
argument-hint: "Describe the AI feature goal, user scenario, constraints, and target surfaces (CLI/API/UI)."
---

# AI Feature Planning Workflow

## What This Skill Produces

Use this skill to convert an AI feature request into an implementation-ready plan. The expected output is:

- clear objective and user outcomes
- explicit assumptions about model/provider/runtime
- staged implementation plan with dependencies
- risk controls for fallback, cost, and reliability
- concrete validation and success metrics

## When to Use

Use this skill when you need to:

- design a new AI capability end-to-end
- scope a model-powered feature before coding
- break ambiguous AI requests into executable phases
- define acceptance criteria for AI behavior
- align rollout strategy with observability and safety

Common trigger phrases:

- "plan this AI feature"
- "design an implementation plan"
- "how should we build this agent behavior"
- "break this AI request into tasks"
- "what should we validate before rollout"

## Procedure

1. Clarify intent and constraints
   - Define who the user is, what success means, and what failure looks like.
   - Capture latency/cost/privacy constraints and expected interaction mode.

2. Map system boundaries
   - Identify all touched layers (frontend, API, provider adapters, memory, telemetry).
   - Note public contracts that must remain stable.

3. Choose model/provider strategy
   - Select primary execution path and fallback order.
   - Document readiness checks and degraded-mode behavior.

4. Break into implementation phases
   - Phase by dependency order: contract → backend logic → UI wiring → validation.
   - Keep each phase testable in isolation.

5. Define validation gates
   - Add smoke checks, targeted tests, and health signals per phase.
   - Ensure behavior is measurable in logs/status artifacts.

6. Specify rollout and rollback
   - Include feature-flag path where relevant.
   - Define rollback conditions and recovery actions.

## Quality Checks

Before finishing, confirm that:

- plan includes explicit success criteria and non-goals
- provider/model assumptions are documented
- fallback and failure behavior is intentional
- verification is tied to concrete commands/tests
- rollout risks and rollback triggers are explicit
