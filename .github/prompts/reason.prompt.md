---
description: "Reason through a problem using chain-of-thought analysis, task decomposition, and self-reflection. Produces structured reasoning with confidence scores and verification steps."
name: "Reason"
argument-hint: "Problem or question to analyze (example: decision + relevant context + constraints or trade-offs)"
agent: agi-reasoning
---

Apply the AGI reasoning framework to analyze and solve the following task.

**Process:**

1. **Analyze** — Classify the query:
   - Complexity: simple | moderate | complex
   - Intent: coding | architecture | debugging | optimization | explanation | creation
   - Domain: quantum | ai | aria | infrastructure | general

2. **Decompose** — Break into ordered subtasks:
   - List each subtask with its dependencies
   - Identify which subtasks can be parallelized
   - Estimate confidence for each subtask

3. **Execute** — Work through each subtask:
   - Show your reasoning at each step
   - Verify assumptions before proceeding
   - Cross-reference with existing codebase patterns

4. **Reflect** — Self-evaluate:
   - Is the solution complete and correct?
   - Does it follow existing codebase conventions?
   - Are there edge cases or failure modes?
   - Am I over-engineering?

5. **Synthesize** — Deliver the result:
   - Clear, actionable output
   - Include verification steps
   - Note any remaining uncertainties

**Codebase context:**
- Provider chain: Azure OpenAI → OpenAI → LMStudio → LoRA → Local
- Config: YAML < CLI < per-job YAML < env vars
- Data: read-only `datasets/`, write-only `data_out/`
- Always `--dry-run` orchestrators first
- Test: `python scripts/test_runner.py --unit`
