---
name: quantum-mcp-safety-workflow
description: "Develop and debug `ai-projects/quantum-ml/quantum_mcp_server.py` with strict safety gates for simulator-first execution, paid QPU confirmation, timeout/shot limits, and cache correctness. Use when MCP quantum tools fail, cost confirmation is bypassed, backend selection is wrong, or tool calls stall."
argument-hint: "Describe the failing MCP tool call, backend (local/simulator/QPU), and whether cost-gate, timeout, or cache behavior is incorrect."
---

# Quantum MCP Safety Workflow

## What This Skill Produces

Use this skill to keep quantum MCP operations safe, deterministic, and debuggable. The expected result is:

- reliable tool behavior across local/simulator/QPU backends
- enforced paid-hardware confirmation gates
- bounded execution (shots/qubits/timeouts)
- stable cache-assisted performance without stale correctness bugs

## When to Use

Use this skill when you need to:

- debug `quantum_mcp_server.py` tool failures
- fix backend routing between local simulation and Azure backends
- enforce or repair `confirm_cost=true` behavior for QPU jobs
- investigate timeout, shot-limit, or qubit-limit violations
- diagnose cache misses/hits causing incorrect or stale responses

Common trigger phrases:

- "MCP quantum tool failed"
- "QPU job ran without confirmation"
- "simulator works but QPU path fails"
- "quantum tool call times out"
- "cache returns stale circuit results"
- "backend list/selection is wrong"

## Procedure

1. Reproduce on the safest backend first
   - Validate with local simulator or free Azure simulator before touching paid QPU.
   - Confirm failure exists in minimal tool call path.

2. Verify safety boundaries explicitly
   - Respect local qubit/shot limits and per-call timeout.
   - Confirm real hardware paths require `confirm_cost=true`.
   - Keep orchestrator and tool-level cost gates aligned.

3. Isolate failing tool stage
   - Circuit creation/simulation stage.
   - Azure connect/list backend stage.
   - Job submission/polling stage.
   - Cost estimation/confirmation stage.

4. Validate backend semantics
   - Free simulators should not require paid confirmation.
   - Paid QPU targets must enforce confirmation and conservative initial shots.
   - Avoid implicit backend fallthrough that hides misconfiguration.

5. Audit cache behavior
   - Confirm cache key includes fields that affect correctness.
   - Verify TTL/LRU eviction works as intended.
   - Ensure cache is a performance optimization, not a source of truth.

6. Apply minimal fix in failing layer
   - Keep endpoint/tool contracts stable.
   - Avoid broad refactors across unrelated tools in one change.

7. Re-verify in progression order
   - local simulator -> free Azure simulator -> paid QPU path (if explicitly requested).

## Quality Checks

Before finishing, confirm that:

- simulator-first validation passes before QPU attempts
- paid hardware requires explicit `confirm_cost=true`
- timeout and shot/qubit limits remain enforced
- cache behavior improves performance without stale correctness issues
- backend selection logic is explicit and explainable
