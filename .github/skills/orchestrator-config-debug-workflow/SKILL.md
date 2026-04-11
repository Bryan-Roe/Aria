---
name: orchestrator-config-debug-workflow
description: 'Debug YAML-driven orchestrator configuration issues across training, quantum, autonomous, and master orchestrators. Use when dry-runs fail, config changes do not take effect, schedules or thresholds behave unexpectedly, or safety limits are set incorrectly.'
argument-hint: 'Describe the orchestrator, config file, failing key or behavior, and whether dry-run or runtime disagrees.'
---

# Orchestrator Config Debug Workflow

## What This Skill Produces

Use this skill to diagnose and repair YAML/orchestrator mismatches safely. The expected result is:
- a confirmed mapping between script and config file
- a clear explanation of which setting is winning under config precedence
- a minimal config or loader fix validated by dry-run or status artifacts
- preserved safety controls for paid or long-running workflows

## When to Use

Use this skill when you need to:
- debug `autotrain.yaml`, `quantum_autorun.yaml`, `config/autonomous_training.yaml`, or `config/master_orchestrator.yaml`
- investigate why config edits seem ignored
- fix schedule, retry, timeout, or threshold behavior
- validate quantum safety limits or autonomous training settings
- reconcile dry-run behavior with actual runtime status files

Common trigger phrases:
- "the YAML change did nothing"
- "dry-run fails"
- "the wrong threshold is being used"
- "master orchestrator schedule is wrong"
- "autonomous training interval is not respected"
- "quantum cost gate is misconfigured"

## Procedure

1. Identify the exact script/config pair
   - Confirm which script consumes the YAML.
   - Avoid editing the wrong config file just because the names are similar.

2. Validate syntax before semantics
   - Confirm the YAML parses cleanly.
   - Fix indentation, scalar types, and key names before debugging runtime behavior.

3. Trace config precedence explicitly
   - Remember the order: YAML base < CLI flags < per-job YAML < environment variables.
   - If a setting appears ignored, check the higher-precedence layers first.

4. Run the safest validation path
   - Prefer `--dry-run` when the orchestrator supports it.
   - For autonomous training configs, use status/log artifacts when dry-run is not the normal validation path.

5. Check safety-sensitive keys carefully
   - Quantum: `azure_confirm_cost`, qubit limits, shot limits, backend selection.
   - Autonomous: `cycle_interval_minutes`, `epochs_progression`, `min_datasets`, deploy threshold.
   - Master orchestrator: schedules, dependencies, retry logic, timeouts.

6. Verify runtime artifacts after the config change
   - Confirm that status files, logs, or runtime output reflect the new value.
   - Do not assume a successful parse means the new config was actually applied.

7. Preserve operational safety
   - Never loosen paid-hardware or long-running safeguards casually.
   - Keep config edits narrow and reversible.

## Quality Checks

Before finishing, confirm that:
- the correct config file was edited for the intended orchestrator
- YAML syntax and key names are valid
- config precedence explains the observed behavior
- dry-run or runtime artifacts reflect the intended setting
- safety limits and cost gates remain intentional after the fix
