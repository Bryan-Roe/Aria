---
name: quantum-pipeline-debug-workflow
description: 'Debug quantum ML pipelines, orchestrators, MCP tooling, simulator runs, Azure Quantum handoff, and cost-gated execution. Use when quantum jobs fail, dry-runs disagree with runtime behavior, simulator/QPU paths diverge, or MCP circuit workflows break.'
argument-hint: 'Describe the quantum job, simulator issue, MCP tool failure, backend mismatch, or cost-gate problem.'
---

# Quantum Pipeline Debug Workflow

## What This Skill Produces

Use this skill to diagnose and fix quantum pipeline issues without skipping safety gates. The expected result is:
- a reproducible failure in a local simulator, orchestrator run, or MCP tool path
- a focused diagnosis across orchestration, circuit generation, backend selection, and result handling
- a minimal repair that preserves cost controls and data-output conventions
- targeted verification through dry-run, simulator checks, and focused tests

## When to Use

Use this skill when you need to:
- debug `scripts/quantum_autorun.py` behavior
- investigate failures in `ai-projects/quantum-ml/quantum_mcp_server.py`
- fix backend selection between local simulation, Azure simulators, and real QPU paths
- diagnose cost-estimation, submission, or result polling problems
- repair quantum classifier or dashboard workflow issues

Common trigger phrases:
- "the quantum pipeline is failing"
- "dry-run passes but the job breaks"
- "the simulator and Azure path disagree"
- "the MCP quantum tool is broken"
- "quantum backend selection is wrong"
- "why did this QPU job or cost gate fail"

## Procedure

1. Reproduce with the safest path first
   - Start from the smallest failing path: local simulator, orchestrator dry-run, or a single MCP tool invocation.
   - Prefer free local or simulator execution before touching Azure hardware.

2. Confirm the execution tier
   - Determine whether the issue is in local simulation, Azure simulator, or real QPU flow.
   - Do not jump to paid hardware debugging until the same logic behaves correctly in local or free simulator paths.

3. Check orchestration and config assumptions
   - Inspect the relevant YAML and CLI inputs before changing code.
   - Preserve config precedence: YAML base, CLI flags, per-job YAML, then environment variables.
   - Keep `datasets/` read-only and preserve outputs under `data_out/quantum_autorun/<job>/`.

4. Preserve cost and safety gates
   - For real hardware paths, keep explicit confirmation requirements such as `azure_confirm_cost: true`.
   - Start with conservative shots and qubit counts when reproducing backend-specific behavior.
   - Never remove or bypass cost checks just to make a job run.

5. Isolate the failing layer
   - If the problem is circuit creation or simulation, inspect the circuit and backend logic first.
   - If the problem is Azure handoff, inspect connection, backend selection, submission, cost estimation, and polling separately.
   - If the problem is the MCP server, verify whether the failure is inside a tool implementation or the server integration boundary.

6. Implement the smallest repair
   - Change only the failing layer whenever possible.
   - Preserve simulator-first workflow and keep local limits reasonable.
   - Avoid mixing dashboard, orchestrator, and MCP refactors in one patch unless the failure clearly spans them.

7. Verify progressively
   - Re-run dry-run or local simulation first.
   - Then validate with an Azure simulator if the bug is cloud-path specific.
   - Only validate against real QPU flows when the user explicitly needs it and the safety gates remain intact.
   - Use focused tests or fast local test markers where possible.

## Quality Checks

Before finishing, confirm that:
- the failure reproduces in the safest possible tier first
- cost gates and paid-hardware safeguards remain intact
- datasets were not modified and outputs still land in `data_out/`
- the selected backend and execution tier are explainable
- the fix is validated through dry-run, simulator checks, or targeted tests before any QPU run
