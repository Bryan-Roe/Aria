---
name: incident-postmortem-workflow
description: 'Create a blameless incident postmortem using runtime evidence, logs, status artifacts, and timeline reconstruction for Aria services. Use when an outage, severe degradation, or failed automation cycle needs root-cause analysis and prevention actions.'
argument-hint: 'Describe the incident window, impacted services, observed symptoms, and any known mitigation already applied.'
---

# Incident Postmortem Workflow

## What This Skill Produces

Use this skill to generate a high-quality, blameless postmortem. The expected output is:
- incident summary with impact scope and severity
- evidence-backed timeline of detection, response, mitigation, and recovery
- root cause and contributing factors with confidence level
- prioritized corrective actions with owners, urgency, and verification plan

## When to Use

Use this skill when you need to:
- document an outage or major service degradation
- analyze failed automation/training/orchestration cycles
- capture lessons from provider/DB/resource incidents
- prevent repeat incidents with actionable remediation

Common trigger phrases:
- "write a postmortem"
- "summarize this incident"
- "root cause analysis for outage"
- "document production issue"
- "what happened and how do we prevent it"

## Procedure

1. Collect evidence before interpretation
   - Gather health endpoint snapshots (`/api/ai/status`), relevant logs, and status artifacts under `data_out/`.
   - Capture resource signals (CPU/memory/disk/GPU) and dependency status around incident time.
   - Separate facts from assumptions.

2. Reconstruct a timeline
   - Mark first symptom, detection time, alert time, mitigation actions, and full recovery time.
   - Include uncertainty explicitly when timestamps are incomplete.

3. Quantify impact
   - Identify affected users/systems, duration, failure modes, and business/operational impact.
   - Distinguish primary impact from secondary side effects.

4. Determine root cause and contributors
   - Identify proximate technical trigger and deeper systemic contributors.
   - Classify contributors (code defect, configuration drift, dependency outage, capacity saturation, process gap).
   - Avoid blame language; focus on system behavior and controls.

5. Evaluate response effectiveness
   - What detection worked or failed?
   - What mitigation reduced impact quickly?
   - What delayed diagnosis or recovery?

6. Define corrective and preventive actions
   - Immediate fixes: short-term risk reduction.
   - Preventive controls: tests, observability, automation guardrails, runbooks.
   - Assign owner, priority, due date, and success verification for each action.

7. Close the learning loop
   - Link action items to release-readiness and health-triage workflows.
   - Schedule follow-up review to confirm actions were completed and effective.

## Quality Checks

Before finishing, confirm that:
- timeline is evidence-backed and internally consistent
- impact and severity are quantified
- root cause has clear confidence level and alternatives considered
- actions are owned, prioritized, and testable
- language is blameless and focused on system improvement
