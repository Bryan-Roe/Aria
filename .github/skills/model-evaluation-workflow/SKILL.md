---
name: model-evaluation-workflow
description: 'Plan, run, debug, and summarize model evaluation workflows using batch evaluation scripts and analytics outputs. Use when evaluation jobs fail, metrics look suspicious, timeouts occur, or you need reproducible model-comparison results.'
argument-hint: 'Describe the model(s), dataset, metrics, and the evaluation symptom you want to investigate.'
---

# Model Evaluation Workflow

## What This Skill Produces

Use this skill to run and troubleshoot evaluations with repeatable metrics and machine-readable outputs. The expected result is:
- a clear evaluation objective and metric set
- a reproducible evaluation path (config-driven or discovery-driven)
- focused diagnosis of timeout/subprocess/data issues
- trustworthy aggregated results and a concise summary of findings

## When to Use

Use this skill when you need to:
- evaluate one or more models consistently
- debug `scripts/batch_evaluator.py` or related evaluation scripts
- compare model quality across datasets and metrics
- investigate missing, noisy, or inconsistent evaluation metrics
- diagnose evaluation timeouts or subprocess failures

Common trigger phrases:
- "run model evaluation"
- "compare these models"
- "batch evaluator is failing"
- "why are evaluation metrics weird"
- "training analytics look wrong"
- "evaluation timed out"

## Procedure

1. Define the evaluation contract first
   - Confirm models, dataset, metric list, sample limits, and success criteria.
   - Keep metric goals explicit (for example: accuracy, perplexity, f1).

2. Choose the entry path
   - Use config-driven evaluation (`load_config`) when a YAML spec exists.
   - Use discovery-driven evaluation (`scan_models`) when sweeping available models.

3. Validate inputs and boundaries
   - Confirm dataset paths exist and remain read-only.
   - Confirm model/adapter paths are valid before launching batch runs.
   - Keep outputs under `data_out/batch_evaluator/`.

4. Start small before scaling
   - Begin with a bounded sample size and conservative parallelism.
   - Watch for per-task timeout behavior and subprocess failure surfaces.
   - Avoid maxing concurrency until one focused run succeeds.

5. Isolate failures by layer
   - Config layer: malformed YAML, missing model/dataset fields.
   - Execution layer: subprocess errors, timeout, missing dependencies.
   - Aggregation layer: incomplete result collection or malformed status output.
   - Analytics layer: suspicious trend math or plateau/degradation interpretation.

6. Apply minimal repairs
   - Change only the failing stage first (task creation, execution, aggregation, or analytics).
   - Preserve status and report formats consumed by downstream scripts/dashboards.

7. Verify and summarize
   - Re-run a focused evaluation first, then broader comparisons.
   - Confirm metrics and result counts are consistent with the configured task set.
   - Summarize quality findings, caveats, and next-run recommendations.

## Quality Checks

Before finishing, confirm that:
- evaluation scope and metrics are explicitly stated
- datasets remained read-only and outputs stayed under `data_out/`
- timeout or subprocess issues were diagnosed at root cause level
- aggregated results are complete and internally consistent
- conclusions match the actual measured metrics, not assumptions
