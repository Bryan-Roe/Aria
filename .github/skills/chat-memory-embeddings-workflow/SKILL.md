---
name: chat-memory-embeddings-workflow
description: Debug, extend, or tune the semantic chat memory system in shared/chat_memory.py — embedding generation priority chain, similarity search, DB storage, session isolation, and memory injection into conversation context. Use when memory retrieval returns wrong results, embeddings are missing, similarity scores look off, or DB is unavailable and fallback behavior is unclear.
argument-hint: "Describe the issue: wrong memories surfaced, embeddings not stored, similarity broken, DB unavailable, or session isolation wrong."
---

# Chat Memory & Embeddings Workflow

## What This Skill Produces
Root-cause diagnosis and targeted fixes for the semantic memory pipeline: embedding generation, DB storage, cosine similarity search, session isolation, and context injection into the message window.

## When to Use

Trigger phrases:
- "wrong memories injected into chat"
- "embeddings not being stored"
- "fetch_similar_messages returning empty"
- "cosine similarity scores look wrong"
- "memory not working without a DB"
- "session isolation broken — seeing other users' messages"
- "embedding dimension mismatch"
- "chat context has stale memories"
- "generate_embedding returning None"
- "memory fallback not working"

## Procedure

### Step 1 — Check Embedding Provider Chain
The priority order is:
1. **Azure OpenAI** — checks 3 endpoint variants for the embedding API
2. **OpenAI** — standard embedding API
3. **Local hash fallback** — deterministic, fixed 256-dim, L2-normalized (offline, zero-dependency)

Diagnose which tier is active:
```python
from shared.chat_memory import generate_embedding
emb = generate_embedding("test")
print(f"Dimension: {len(emb) if emb else 'None — all providers failed'}")
```
256 dim = local fallback. Larger = real embedding model.

### Step 2 — Verify DB Connectivity
```bash
python -c "from shared.sql_engine import get_engine; e = get_engine(); print(e)"
```
If `QAI_DB_CONN` is unset, `generate_embedding()` and `store_embedding()` degrade gracefully — `store_embedding()` returns `None`, **which is expected**. Never treat a `None` storage return as a crash condition.

### Step 3 — Test Similarity Search Directly
```python
from shared.chat_memory import generate_embedding, fetch_similar_messages
q = generate_embedding("What is quantum computing?")
results = fetch_similar_messages(q, top_k=5, session_id="test-session")
print(results)
```
Empty results can mean: no stored embeddings, dimension mismatch (mixing 256-dim local with 1536-dim Azure), or DB pool exhaustion.

### Step 4 — Check Dimension Consistency
Mixing embedding dimensions **silently breaks similarity** — a 256-dim local embedding will always score nearly 0 cosine similarity against a 1536-dim Azure embedding. If switching providers, re-embed all stored messages or wipe `ChatMessageEmbeddings` before using the new provider.

### Step 5 — Verify Session Isolation
All `fetch_similar_messages` calls should pass `session_id` to avoid cross-user leakage:
```python
similar = fetch_similar_messages(embedding, top_k=5, session_id=request_session_id)
```
If `session_id=None`, the query searches across **all sessions** — a security concern for multi-user deployments.

### Step 6 — Memory Injection Pattern
Correct injection order:
```python
embedding = generate_embedding(user_text)
similar = fetch_similar_messages(embedding, top_k=5, session_id=session_id)
for i, msg in enumerate(similar):
    messages.insert(1, {"role": "system", "content": f"[Memory #{i+1}] {msg['content']}"})
# Then prune AFTER injecting memories
messages, stats, sys_msg = prune_messages(messages, provider, model, max_tokens)
```
Never inject memories after pruning — memories will be the first thing cut.

### Step 7 — Check Pool Saturation
Thread-local connection cache with `MAX_POOL_SIZE = 5`. If many concurrent requests fail:
```bash
curl http://localhost:7071/api/ai/status | jq '.sql_pool'
```
`saturation_alert: true` means ≥80% pool utilization — tune `QAI_SQL_POOL_SIZE`.

## Quality Checks
- [ ] `generate_embedding()` returns a list, or `None` with graceful handling (not an exception)
- [ ] Embedding dimension consistent across all stored messages in deployment
- [ ] `session_id` always passed to `fetch_similar_messages` in multi-user contexts
- [ ] Memory injection happens before `prune_messages`, not after
- [ ] `store_embedding()` `None` return treated as advisory, not fatal
- [ ] DB unavailability degrades to local-hash fallback without crashing
