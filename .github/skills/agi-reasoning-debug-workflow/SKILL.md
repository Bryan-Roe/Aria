---
name: agi-reasoning-debug-workflow
description: "Debug AGI provider reasoning chains, task decomposition, self-reflection loops, context overflow, and Aria tag injection. Use when AGI responses are shallow, reasoning steps are missing, complexity classification is wrong, chain-of-thought produces incorrect breakdowns, or Aria movement tags are absent from responses."
argument-hint: "Describe the symptom: reasoning chain missing, wrong complexity class, Aria tags absent, response quality degraded, context too large, or decomposition pattern incorrect."
---

# AGI Reasoning Debug Workflow

## What This Skill Produces
- Root cause for reasoning pipeline failures (wrong complexity class, missing steps, bad decompose template)
- Diagnosis of context overflow (MAX_HISTORY_SIZE=50, MAX_REASONING_CHAINS=10)
- Verification that Aria movement tags are injected when domain is `aria`
- Targeted fix recommendations with exact method names and thresholds

## When to Use

Trigger phrases:
- "AGI response is shallow / not reasoning properly"
- "chain-of-thought not showing up"
- "task decomposition looks wrong"
- "Aria movement tags missing from response"
- "self-reflection not firing"
- "AGI context is too large"
- "reasoning depth not high enough"
- "intent detection classified wrong"
- "domain detection wrong"
- "agi_provider not improving answer"
- "AGI goals or learned patterns overflowing"

## Procedure

### Step 1 — Identify the canonical file
```bash
# Root-level agi_provider.py is a compatibility SHIM only
# Canonical logic lives here:
cat ai-projects/chat-cli/src/agi_provider.py | head -60
```
Never edit the root-level shim for logic changes.

### Step 2 — Trace the core pipeline order
The pipeline runs sequentially:
1. `_analyze_query()` — classifies complexity + detects intent + domain
2. `_decompose_task()` — splits complex queries into sub-tasks
3. `_reason()` — runs reasoning chain based on depth
4. `_reflect_and_improve()` — self-reflection pass over the answer

If output is shallow, check which stage is being skipped by adding `verbose=True` to the `create_agi_provider()` factory call.

### Step 3 — Check complexity classification
```python
# simple:   < 10 words AND no keywords
# moderate: 10-30 words OR contains some keywords
# complex:  > 30 words OR keywords: implement, architect, debug, refactor

# If classified too simple, user query is short — prompt should include more context
# If classified too complex, reduce prompt length or strip keywords
```

### Step 4 — Verify decomposition template by intent

| Intent | Decomposition steps |
|--------|----------------------|
| coding | requirements → design → implement → edge cases → test |
| explanation | define → examples → relationships → summary |
| creation | concept → outline → details → review |
| question | direct → elaborate → examples → summary |

If decomposition steps don't match intent, check `_decompose_task()` intent detection logic.

### Step 5 — Check Aria tag injection for `aria` domain
```python
# Self-reflection checks for missing Aria tags when domain == "aria"
# Expected tags: [aria:walk:left], [aria:jump], [aria:wave], [aria:dance]

# Verify domain detection is returning "aria" for character queries
# Fix: ensure query text contains "Aria" or action verbs that trigger aria domain
```

### Step 6 — Inspect memory limits
```python
MAX_HISTORY_SIZE    = 50   # conversation_history entries — prune if exceeded
MAX_REASONING_CHAINS = 10  # ReasoningStep records — old chains are dropped
MAX_GOALS           = 5    # active goals in AGIContext

# If reasoning feels repetitive: MAX_REASONING_CHAINS may be saturated
# Clear via: agi_provider.context.reasoning_chains.clear()
```

### Step 7 — Validate input sanitization
```python
# _sanitize_input() strips control characters and enforces:
MAX_INPUT_LENGTH = 10000  # characters (not tokens)

# Inputs longer than 10000 chars are truncated before reaching the reasoning pipeline
# Symptom: reasoning is about the wrong part of a long document
# Fix: chunk input before passing to AGI provider
```

## Quality Checks
- [ ] Editing canonical `ai-projects/chat-cli/src/agi_provider.py`, not the root shim
- [ ] `verbose=True` passed to factory to expose reasoning chain in logs
- [ ] Complexity classification verified against actual word count and keyword presence
- [ ] Decomposition template matches the detected intent
- [ ] Aria domain queries produce `[aria:*]` tags in the response
- [ ] `MAX_HISTORY_SIZE`, `MAX_REASONING_CHAINS`, `MAX_GOALS` respected — no unbounded growth
- [ ] Input > 10000 chars is chunked before `create_agi_provider()` receives it
- [ ] Tests run: `pytest tests/ -m "not slow and not azure" -k agi`
