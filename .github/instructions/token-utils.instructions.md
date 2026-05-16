---
applyTo: "**/token_utils.py"
---

# Token Utils — Instruction Guide

## Token Counting

```python
from token_utils import count_messages_tokens, prune_messages

tokens = count_messages_tokens(messages, provider, model, system_prompt)
```

### Counting Priority
1. **tiktoken** — For OpenAI/Azure models (accurate, fast)
2. **AutoTokenizer** — For Hugging Face models (transformers library)
3. **Heuristic** — 1 token ≈ 4 characters (universal fallback)

## Context Window Defaults

| Model | Context Window |
| ------- | --------------- |
| gpt-4o | 128,000 |
| gpt-3.5-turbo | 16,384 |
| Azure default | 16,384 |
| Phi models | 4,096 |

## Message Pruning

```python
pruned_msgs, stats, system_msg = prune_messages(
    messages,
    provider,
    model,
    max_context_tokens=None,      # Auto-detect from model
    reserve_output_tokens=1024,    # Reserve for response
    system_prompt=None
)
```

### Pruning Algorithm (O(n))
1. Pre-compute per-message token counts
2. Always keep system message + most recent messages
3. Remove oldest messages first when over budget
4. Return pruned list + stats

### PruneStats
```python
{
    "original_tokens": int,       # Total before pruning
    "pruned_tokens": int,         # Total after pruning
    "removed_count": int,         # Messages removed
    "budget": int,                # Context window budget
    "reserve_output_tokens": int  # Reserved for response
}
```

## Coding Conventions

- Always reserve output tokens (default 1024) — don't fill the entire context window
- Use model-specific context windows, not hardcoded values
- System messages are never pruned — they're critical for behavior
- Log `PruneStats` when pruning occurs for debugging context issues
- The heuristic fallback (4 chars/token) is intentionally conservative
