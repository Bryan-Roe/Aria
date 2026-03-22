# Quantum LLM Status Tracking & Monitoring

This document explains the Quantum LLM status tracking system, how to monitor training progress, and how to verify checkpoint readiness.

## Overview

The Quantum LLM trainer tracks training state through a JSON status file. This enables:

- **Progress monitoring** during training
- **Checkpoint validation** before inference
- **Error recovery** by persisting state
- **Integration** with orchestration systems

## Status File Schema

The status file (`data_out/quantum_llm_training/status.json`) contains:

```json
{
  "status": "completed|running|idle|failed|not_started",
  "available": true,
  "checkpoint_exists": true,
  "checkpoint_path": "data_out/quantum_llm_training/best_quantum_llm.pt",
  "inference_ready": true,
  "epochs_completed": 5,
  "epochs_requested": 10,
  "best_loss": 0.089,
  "final_loss": 0.123,
  "quantum_available": true,
  "dataset_path": "datasets/chat",
  "mode": "simulated|real",
  "passive_mode": false,
  "started_at": "2026-03-22T09:00:00",
  "completed_at": "2026-03-22T09:15:00",
  "last_updated": "2026-03-22T09:15:00",
  "last_error": null,
  "training_history": [...],
  "quantum_metrics": {...}
}
```

## API Functions

### get_quantum_llm_status()

Load current training status and checkpoint metadata.

```python
from quantum_llm_trainer import get_quantum_llm_status

# Default location
status = get_quantum_llm_status()

# Custom location
status = get_quantum_llm_status(output_dir="data_out/custom_training")

# Check if inference ready
if status['inference_ready']:
    checkpoint = status['checkpoint_path']
    # Load and use model
```

**Returns**: Dictionary with status, checkpoint info, metrics, and error details.

### write_quantum_llm_status()

Persist training status and checkpoint metadata.

```python
from quantum_llm_trainer import write_quantum_llm_status

data = {
    "status": "completed",
    "epochs_completed": 5,
    "best_loss": 0.089,
    "checkpoint_path": "data_out/quantum_llm_training/best_quantum_llm.pt"
}

write_quantum_llm_status(data, output_dir="data_out/quantum_llm_training")
```

**Note**: `last_updated` timestamp is added automatically.

## Command-Line Tools

### Check Status (Human-Readable)

```bash
# Default directory
python scripts/quantum_llm_status_check.py

# Custom directory
python scripts/quantum_llm_status_check.py --output data_out/custom_dir

# Watch mode (auto-refresh every 5 seconds)
python scripts/quantum_llm_status_check.py --watch
```

### Check Status (JSON)

```bash
# Machine-readable JSON output
python scripts/quantum_llm_status_check.py --json

# Pipe to jq for filtering
python scripts/quantum_llm_status_check.py --json | jq '.epochs_completed'
```

## Azure Functions Integration

The `/api/ai/status` endpoint includes quantum LLM readiness:

```bash
curl http://localhost:7071/api/ai/status | jq '.quantum'
```

Response includes:

```json
{
  "quantum": {
    "enabled": true,
    "llm_model_available": true,
    "llm_checkpoint_path": "data_out/quantum_llm_training/best_quantum_llm.pt",
    "inference_ready": true,
    "trainer_status": "completed"
  }
}
```

The `/api/quantum-llm` endpoint returns readiness in responses:

```json
{
  "readiness": {
    "available": true,
    "status": "completed",
    "checkpoint_exists": true,
    "inference_ready": true
  }
}
```

## Training Status States

| State | Meaning | Inference Ready |
|-------|---------|-----------------|
| `not_started` | No training attempted | ✗ |
| `idle` | Training available, not running | ✓ (if checkpoint exists) |
| `running` | Training in progress | ✗ |
| `completed` | Training finished successfully | ✓ (if checkpoint valid) |
| `failed` | Training completed with errors | ✗ |
| `error` | Status read failed | ✗ |

## Checkpoint Resolution

Checkpoints are resolved in priority order:

1. `best_checkpoint_path` from status file
2. `checkpoint_path` from status file
3. `last_checkpoint_path` from status file
4. Default search: `best_quantum_llm.pt`, `quantum_llm_checkpoint.pt`, `final_model.pt`

### Verifying Checkpoint Validity

```python
from quantum_llm_trainer import get_quantum_llm_status

status = get_quantum_llm_status()

if status['checkpoint_exists'] and status['inference_ready']:
    path = status['checkpoint_path']
    print(f"✓ Checkpoint ready at: {path}")
else:
    print("✗ Checkpoint not ready")
    if error := status.get('last_error'):
        print(f"  Error: {error}")
```

## Passive Training Monitoring

When using passive training mode:

```python
trainer = QuantumEnhancedLLMTrainer(config={'passive': True})
await trainer.run_passive_training_loop()
```

Status is updated at each cycle:

```bash
# Monitor in real-time
python scripts/quantum_llm_status_check.py --watch

# Parse specific fields
python scripts/quantum_llm_status_check.py --json | jq '{
  status: .status,
  cycle: .current_cycle,
  epochs: .epochs_completed,
  loss: .final_loss
}'
```

## Troubleshooting

### Checkpoint Not Found

```bash
python scripts/quantum_llm_status_check.py --json | jq '.checkpoint_path'
```

- If `null`: Training hasn't completed or no checkpoint was saved
- If path doesn't exist: Check training output directory
- Solution: Re-run training with proper `--output` directory

### Inference Not Ready

```bash
# Check all readiness indicators
python scripts/quantum_llm_status_check.py --json | jq '{
  checkpoint_exists: .checkpoint_exists,
  status: .status,
  inference_ready: .inference_ready,
  error: .last_error
}'
```

- `status` not "completed" or "idle": Training still running or failed
- `checkpoint_exists` false: No checkpoint file available
- `last_error` set: Review error message

### Status File Missing

```bash
# Check if status file created
ls -la data_out/quantum_llm_training/status.json

# If missing, status will show:
python scripts/quantum_llm_status_check.py --json | jq '.status_file_exists'
```

## Integration Examples

### With Azure Functions

```python
# In function_app.py
from quantum_llm_trainer import get_quantum_llm_status

@app.route(route="api/quantum-llm-ready", methods=["GET"])
def quantum_ready(req):
    status = get_quantum_llm_status()
    return func.HttpResponse(
        json.dumps({"ready": status["inference_ready"]}),
        status_code=200,
        mimetype="application/json"
    )
```

### With Monitoring Systems

```bash
# Export metrics for Prometheus scraping
while true; do
  python scripts/quantum_llm_status_check.py --json | jq '
    "quantum_llm_status{status=\"\(.status)\"} \(.inference_ready | if . then 1 else 0 end)\n"'
  sleep 30
done
```

### With CI/CD Pipelines

```bash
# Check training status before deployment
python scripts/quantum_llm_status_check.py --json | \
  jq --exit-status '
    select(
      (.inference_ready | not) or
      (.checkpoint_exists | not)
    )
  ' && {
    echo "✗ Quantum LLM not ready for deployment"
    exit 1
  } || {
    echo "✓ Quantum LLM ready for deployment"
  }
```

## Best Practices

1. **Check before inference**: Always verify `inference_ready` before loading a model
2. **Monitor training**: Use `--watch` mode to track long-running training cycles
3. **Save status regularly**: The trainer saves status at each epoch (automatic)
4. **Handle errors gracefully**: Check `last_error` field for training failures
5. **Document timestamps**: Use `started_at` and `completed_at` for audit trails
6. **Version checkpoints**: Include commit hash in checkpoint metadata for traceability

## See Also

- [Quantum LLM Trainer](../scripts/quantum_llm_trainer.py) - Core training implementation
- [Azure Functions Integration](../function_app.py) - `/api/quantum-llm` and `/api/ai/status` endpoints
- [Quantum Provider](../ai-projects/chat-cli/src/quantum_provider.py) - Inference with checkpoints
