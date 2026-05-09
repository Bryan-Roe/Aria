---
name: ai-response-evaluation-workflow
description: "Evaluate AI responses with repeatable metrics, dataset discipline, and comparison-ready reporting for quality, safety, and reliability decisions."
argument-hint: "Describe what to evaluate (accuracy/relevance/safety/latency), dataset source, and pass criteria."
---

# AI Response Evaluation Workflow

## What This Skill Produces

Use this skill to evaluate AI output quality in a reproducible way. The expected output is:

- explicit evaluation questions and metrics
- curated test set or dataset slice definition
- repeatable execution steps
- summarized results with pass/fail interpretation
- concrete follow-up actions for regressions

## When to Use

Use this skill when you need to:

- compare two model/provider/prompt variants
- investigate quality regressions
- define release gates for AI behavior
- validate schema adherence and factuality trends
- produce evidence for go/no-go decisions

Common trigger phrases:

- "evaluate model responses"
- "compare these prompts/providers"
- "quality seems worse"
- "set acceptance metrics"
- "build a reliability report"

## Procedure

1. Set evaluation objective
   - Define decision to be made (ship, rollback, iterate).
   - Choose metrics that directly support that decision.

2. Scope dataset and sampling
   - Use representative scenarios and edge cases.
   - Keep dataset immutable during a run; record version/source.

3. Define scoring method
   - Specify automatic checks vs manual review criteria.
   - Establish thresholds for pass/warn/fail.

4. Execute reproducibly
   - Run evaluation with fixed config and documented command.
   - Capture artifacts and summary metrics for comparison.

5. Analyze deltas
   - Compare against baseline and inspect worst failures.
   - Separate systemic regressions from isolated outliers.

6. Recommend actions
   - Propose prompt/model/config changes tied to evidence.
   - Define next validation run to confirm improvements.

## Quality Checks

Before finishing, confirm that:

- metrics map to product decisions
- dataset scope and version are explicit
- pass/fail thresholds are declared
- outputs are reproducible and comparable
- recommendations are evidence-based
