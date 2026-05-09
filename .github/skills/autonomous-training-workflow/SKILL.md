---
name: autonomous-training-workflow
description: 'Debug, tune, or extend the self-managing training lifecycle in `scripts/autonomous_training_orchestrator.py` and related configs. Use when training cycles stall, dataset discovery looks wrong, adaptive epochs misbehave, degradation alerts fire, or promotion logic needs safe changes.'
argument-hint: 'Describe the autonomous training symptom, cycle behavior, dataset issue, metric drift, or promotion/deployment problem.'
---

# Autonomous Training Workflow

## What This Skill Produces

Use this skill to investigate and safely modify the autonomous training lifecycle. The expected result is:
- a clear diagnosis of which stage in the cycle is failing or behaving unexpectedly
- a minimal fix or tuning change that preserves continuous operation and graceful recovery
- preserved dataset immutability, status reporting, and safety thresholds
- targeted verification through dry-run style checks, logs, status files, and focused tests

## When to Use

Use this skill when you need to:
- debug `scripts/autonomous_training_orchestrator.py`
- tune dataset discovery, collection, or adaptive epoch selection
- investigate performance degradation alerts or plateau detection
- adjust promotion or deployment thresholds safely
- diagnose broken status reporting, logs, or background-cycle behavior

Common trigger phrases:
- "autonomous training is stuck"
- "the training cycle is misbehaving"
- "dataset discovery is wrong"
- "adaptive epochs are not being selected correctly"
- "promotion or deployment happened unexpectedly"
- "degradation alerts keep firing"

## Procedure

1. Identify the failing stage in the state machine
   - Place the issue inside one stage first: discovery, collection, training, analysis, optimization, or deployment.
   - Use logs and status artifacts to avoid debugging the whole loop at once.

2. Inspect status and observability outputs before editing
   - Check `data_out/autonomous_training_status.json` for cycle counters, best accuracy, performance history, and dataset inventory.
   - Review `data_out/autonomous_training.log` for the exact stage, exception, or repeated warning.
   - Treat these artifacts as the source of truth for cycle behavior.

3. Preserve continuous-operation guarantees
   - Keep graceful error handling so a failed cycle does not permanently stop future cycles.
   - Preserve manual trigger and graceful shutdown behavior.
   - Avoid changes that make the orchestrator brittle or single-failure fatal unless explicitly required.

4. Respect training and data conventions
   - Keep `datasets/` read-only.
   - Write outputs and machine-readable status only under `data_out/`.
   - Preserve the adaptive-epochs model unless the task explicitly changes the optimization policy.

5. Change thresholds and automation carefully
   - Treat promotion thresholds, degradation alerts, and optimization triggers as safety-sensitive controls.
   - If changing thresholds, verify both the intended effect and the fallback behavior when metrics are missing or noisy.
   - Avoid altering multiple lifecycle policies in one patch unless they are tightly coupled.

6. Implement the smallest durable fix
   - Prefer local, stage-specific repairs over broad orchestrator rewrites.
   - Keep status JSON schema and log semantics stable when possible.
   - Preserve background execution compatibility and monitoring expectations.

7. Verify with artifacts and focused checks
   - Reproduce the issue using logs, a limited run, or the smallest relevant invocation path.
   - Confirm status updates and lifecycle transitions remain consistent after the change.
   - Run focused tests or validation commands tied to the affected stage.

## Quality Checks

Before finishing, confirm that:
- the failing lifecycle stage is identified explicitly
- `datasets/` remains untouched and outputs still land under `data_out/`
- logs and status files remain meaningful and machine-readable
- safety thresholds and promotion logic remain intentional
- the fix preserves continuous operation and graceful recovery
