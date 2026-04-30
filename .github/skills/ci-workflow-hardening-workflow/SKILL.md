---
name: ci-workflow-hardening-workflow
description: 'Audit and harden GitHub Actions workflows and local composite actions for reliability, safety, and maintainability. Use when CI is flaky, workflow contracts drift, duplicate logic appears, or actions/workflows need normalization.'
argument-hint: 'Describe the workflow files, failing behavior, and hardening target (reliability, safety, consistency, or speed).'
---

# CI Workflow Hardening Workflow

## What This Skill Produces

Use this skill to improve Actions quality without changing product logic. The expected output is:
- a focused list of workflow/action weaknesses
- reusable-action extraction opportunities
- minimal hardening edits
- validation evidence (YAML parse + targeted contract checks)

## When to Use

Use this skill when you need to:
- reduce flaky or brittle workflow behavior
- normalize duplicated CI setup steps
- tighten reliability around shell scripts and contract gates
- improve maintainability of `.github/workflows/*` and `.github/actions/*`

Common trigger phrases:
- "harden CI"
- "workflow is flaky"
- "fix old workflows"
- "add reusable action"
- "normalize GitHub Actions"

## Procedure

1. Inventory current CI assets
   - List workflow files and composite actions.
   - Identify duplication hotspots (repeated setup, repeated script calls).

2. Detect hardening opportunities
   - Missing `set -euo pipefail` in shell blocks.
   - Repeated ad-hoc script invocation that should be a composite action.
   - Weak validation around YAML parsing, workflow keys, or test gate invocations.

3. Apply minimal structural improvements
   - Add or update composite actions for repeated patterns.
   - Keep workflow behavior equivalent unless a bug/failure mode requires a change.
   - Avoid broad trigger/event redesign in the same patch.

4. Validate changes
   - Parse modified `action.yml`/workflow YAML.
   - Run targeted gate checks relevant to changed paths.
   - Ensure paths and inputs are command-ready and documented.

5. Summarize for operators
   - What was hardened
   - Why it reduces risk
   - How to consume the new action/flow

## Quality Checks

Before finishing, confirm that:
- behavior is equivalent unless intentionally fixed
- new actions include README usage examples
- YAML is syntactically valid
- reusable logic moved out of workflows is documented
