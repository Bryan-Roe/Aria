---
name: token-budget-debug-workflow
description: "Debug token counting errors, context window overflow, aggressive message pruning, and incorrect budget calculations across tiktoken, AutoTokenizer, and heuristic counting paths. Use when responses truncate early, context overflows, too many messages are pruned, or token counts differ between providers."
argument-hint: "Describe the symptom: context overflow, messages truncated, pruning removing too many messages, token count mismatch between providers, or system prompt being dropped."
---

# Token Budget Debug Workflow

## What This Skill Produces
- Root cause for token counting mismatches across tiktoken / AutoTokenizer / heuristic paths
- Diagnosis of incorrect `reserve_output_tokens` or context window defaulting
- Explanation of why messages were or weren't pruned using `PruneStats`
- Targeted fix with correct model name, window size, and reserve value

## When to Use

Trigger phrases:
- "response is getting cut off"
- "context window overflow"
- "too many messages being removed"
- "token count seems wrong"
- "system prompt disappeared from messages"
- "conversation is being truncated too aggressively"
- "token counting falls back to heuristic"
- "prune_messages removing recent messages"
- "context budget calculation wrong"
- "token count differs between Azure and OpenAI"
- "token_utils not using tiktoken"
- "messages pruned even though context is small"

## Procedure

### Step 1 — Identify which counting path is executing
```python
from token_utils import count_messages_tokens

# Priority order:
# 1. tiktoken     — OpenAI/Azure models (fast, accurate)
# 2. AutoTokenizer — Hugging Face models (transformers required)
# 3. Heuristic    — 1 token ≈ 4 characters (universal fallback)

# To force tiktoken: ensure tiktoken is installed and model is an OpenAI model name
# To force AutoTokenizer: pass HuggingFace model name (e.g. "microsoft/phi-2")
# Heuristic fires when both libraries fail or model is unrecognized
```

### Step 2 — Verify context window is not defaulting incorrectly
```python
# Known context windows:
MODEL_DEFAULTS = {
    "gpt-4o":          128_000,
    "gpt-3.5-turbo":   16_384,
    "azure_default":   16_384,
    "phi":              4_096,
}

# If the wrong default is applied, token budget will be too small/large
# Symptom: pruning happening on short conversations
# Fix: pass explicit model name to count_messages_tokens() and prune_messages()
```

### Step 3 — Capture and inspect PruneStats
```python
pruned_msgs, stats, system_msg = prune_messages(
    messages,
    provider="azure",
    model="gpt-4o",
    max_context_tokens=None,       # None = auto-detect from model
    reserve_output_tokens=1024,    # Always reserve for response
    system_prompt=None
)

print(stats)
# {
#   "original_tokens": 5200,
#   "pruned_tokens": 3900,
#   "removed_count": 4,
#   "budget": 127000,               # 128000 - 1024
#   "reserve_output_tokens": 1024
# }
```
If `removed_count` is unexpectedly high, compare `original_tokens` to `budget`.

### Step 4 — Check system message preservation
```python
# System messages are NEVER pruned — they survive any prune run
# If system_msg is None after prune_messages():
#   → The input messages list had no role="system" entry
#   → Check that system_prompt kwarg was passed OR messages[0]["role"] == "system"
```

### Step 5 — Audit reserve_output_tokens

The default reserve is 1024 tokens. If the model needs long completions:
```python
# For large code generation, increase reserve:
reserve_output_tokens = 4096  # leaves more room for structured output

# Never set reserve to 0 — model needs space to produce [DONE]
# Symptom: response truncates at exactly one token from window edge
```

### Step 6 — Debug heuristic fallback accuracy

When tiktoken is not available:
```python
# Heuristic: 1 token ≈ 4 chars (intentionally conservative)
# Dense code or JSON will have more tokens than the heuristic predicts
# Symptom: context overflows despite prune_messages() reporting budget OK

# Fix: install tiktoken
pip install tiktoken

# Verify it loads:
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4o")
print(enc.encode("hello world"))
```

### Step 7 — Log PruneStats on every prune
```python
# Coding convention: always log stats when pruning occurs
if stats["removed_count"] > 0:
    logger.info(f"Messages pruned: {stats}")
```
This creates an audit trail for debugging truncation issues in production.

## Quality Checks
- [ ] Model name passed explicitly — not relying on default window size
- [ ] `reserve_output_tokens` set appropriately for expected completion length (≥ 1024)
- [ ] System prompt present in messages or passed via `system_prompt` kwarg
- [ ] `PruneStats` logged when `removed_count > 0`
- [ ] tiktoken installed for OpenAI/Azure paths (confirm via `import tiktoken`)
- [ ] Heuristic fallback acknowledged if non-OpenAI model is used
- [ ] Memory injection (from chat_memory) done BEFORE `prune_messages()` call
- [ ] Tests run: `pytest tests/ -m "not slow and not azure" -k token`
