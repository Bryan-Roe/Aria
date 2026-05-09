---
description: "Analyze and optimize AI system performance"
name: "Optimize"
argument-hint: "Target component + bottleneck description (example: component name + observed issue + baseline metrics)"
agent: agent
---
# Optimize

Analyze and optimize AI system performance across the Aria platform.

## Performance Analysis

### Quick Health Check
```bash
curl http://localhost:7071/api/ai/status | jq
python scripts/system_health_check.py
```

### Resource Monitoring
```bash
python scripts/resource_monitor.py --snapshot    # CPU/memory/disk/GPU
python scripts/training_analytics.py             # Training trends
python scripts/status_dashboard.py --watch       # Live orchestrator status
```

### Token Budget Optimization
- Review `prune_messages()` stats: original_tokens, pruned_tokens, removed_count
- Adjust `max_context_tokens` and `reserve_output_tokens` per provider
- Context window: gpt-4o (128k), gpt-3.5-turbo (16.3k), phi (4k)

### Embedding Performance
- Azure OpenAI embeddings: most accurate, API cost
- OpenAI embeddings: good fallback
- Local hash: deterministic 256-dim, zero-cost, less semantic

### SQL Pool Optimization
- Default pool size: 10 (configurable via `QAI_SQL_POOL_SIZE`)
- Health endpoint warns at ≥80% saturation
- Connection pooling: thread-per-connection + shared pool (MAX_POOL_SIZE=5)

## Common Bottlenecks

| Issue | Diagnostic | Fix |
|-------|-----------|-----|
| Slow responses | Check provider latency in /api/ai/status | Switch to faster provider or reduce max_tokens |
| Memory overflow | Monitor `prune_messages()` stats | Lower max_context_tokens |
| DB pool exhaustion | Check pool saturation in /api/ai/status | Increase QAI_SQL_POOL_SIZE |
| Training stalled | `scripts/training_analytics.py` | Adjust epochs or learning rate |
| GPU OOM | `scripts/resource_monitor.py` | Reduce batch_size |

## Autonomous Training Optimization
- Epoch progression: `[25, 50, 100, 200]` — auto-escalates on plateau
- Performance degradation alerts: > 5% accuracy drop between cycles
- Adaptive dataset selection based on performance history

Optimize: {{input}}
