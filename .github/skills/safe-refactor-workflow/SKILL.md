---
name: safe-refactor-workflow
description: 'Refactor multi-file code safely while preserving public routes, provider behavior, status-file schemas, dataset immutability, and test expectations. Use when extracting helpers, renaming modules or symbols, normalizing paths, or simplifying code without changing intended behavior.'
argument-hint: 'Describe the refactor goal, affected files, and the contracts that must remain unchanged.'
---

# Safe Refactor Workflow

## What This Skill Produces

Use this skill to restructure code without silently breaking contracts. The expected result is:
- a clear list of invariants that must not change
- a narrow sequence of structural edits
- targeted validation proving behavior is unchanged
- a concise summary of refactor scope and preserved contracts

## When to Use

Use this skill when you need to:
- extract duplicated logic into helpers
- rename files, modules, functions, or symbols safely
- normalize paths or imports without changing behavior
- simplify a subsystem while preserving API/output contracts
- clean up architecture across multiple files with low regression risk

Common trigger phrases:
- "refactor this safely"
- "clean this up without changing behavior"
- "extract a helper"
- "rename this across the repo"
- "normalize these paths"
- "reduce duplication but keep contracts stable"

## Procedure

1. Write down the invariants first
   - Public endpoints and route names.
   - Provider detection/fallback behavior.
   - `status.json` schemas and output locations.
   - Dataset immutability (`datasets/` stays read-only).
   - Required adapter or asset file names.

2. Snapshot current behavior
   - Identify one or more smoke checks that represent the contract.
   - Prefer targeted tests or endpoint requests over broad assumptions.

3. Refactor one seam at a time
   - Extract helpers or rename symbols in the smallest coherent slice.
   - Keep one semantic change per step where possible.
   - Prefer precise renames over manual search/replace when available.

4. Preserve contract boundaries explicitly
   - Do not change payload shapes, status-file fields, or routing patterns unless the task requires it.
   - Keep fallback behavior and error handling equivalent while moving code.

5. Re-validate after each meaningful step
   - Re-run the focused smoke check immediately.
   - Stop and diagnose before continuing if an invariant breaks.

6. Clean up only after structure is stable
   - Remove dead code or duplicated fragments once the new structure passes checks.
   - Avoid combining cleanup with behavior changes.

7. Finish with a contract audit
   - Re-check all preserved invariants.
   - Summarize what moved, what stayed stable, and what verification was run.

## Quality Checks

Before finishing, confirm that:
- preserved invariants were listed before edits began
- contracts stayed stable across routes, providers, status files, and datasets
- validation was run after each meaningful refactor step
- no behavior change slipped in under the label of cleanup
- the final summary distinguishes structural change from functional change
