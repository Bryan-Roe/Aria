# GGUF Training Automation — Integration Guide

## Overview

The GGUF Training Automation system provides a complete, end-to-end pipeline for:

1. **Training** — Fine-tune models using existing `autotrain.py`
2. **Conversion** — Convert trained models to GGUF binary format
3. **Quantization** — Reduce model size (q4_0, q5_0, f16, f32)
4. **Validation** — Verify GGUF integrity and format
5. **Deployment** — Automatically deploy to `deployed_models/`

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         GGUF Training Automation System                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Phase 1: Training                                      │
│  ├─ Uses: scripts/autotrain.py                         │
│  ├─ Config: config/training/autotrain.yaml             │
│  └─ Output: data_out/lora_training/                    │
│                                                         │
│  Phase 2: GGUF Conversion                              │
│  ├─ Loads: Trained LoRA model + base model             │
│  ├─ Merges: Adapters with base weights                 │
│  └─ Output: *.gguf (binary format)                     │
│                                                         │
│  Phase 3: Quantization                                 │
│  ├─ Method: llama.cpp quantize or fallback             │
│  ├─ Types: q4_0, q5_0, f16, f32                        │
│  └─ Output: *-q4_0.gguf (compressed)                   │
│                                                         │
│  Phase 4: Validation                                   │
│  ├─ Checks: Magic number, version, tensors             │
│  ├─ Uses: GGUF file format spec                        │
│  └─ Output: Validation report                          │
│                                                         │
│  Phase 5: Deployment                                   │
│  ├─ Target: deployed_models/                           │
│  ├─ Naming: {name}-latest.gguf                         │
│  └─ Output: Production-ready models                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## File Structure

```
/workspaces/AI/
├── scripts/
│   ├── gguf_training_automation.py     ← Main orchestrator
│   ├── autotrain.py                    ← Phase 1 (training)
│   ├── export_quantum_to_gguf.py       ← Phase 2 reference
│   └── visualize_gguf_simple.py        ← Inspection tool
│
├── config/training/
│   ├── autotrain.yaml                  ← Training config
│   └── gguf_training.yaml              ← GGUF pipeline config
│
├── data_out/
│   ├── lora_training/                  ← Training outputs
│   │   └── phi35/checkpoint-100/
│   └── gguf_training/                  ← GGUF pipeline outputs
│       ├── phi35_quick_gguf/
│       │   └── 2026-01-17T10:30:00Z/
│       │       ├── status.json         ← Job results
│       │       ├── phi35_quick_gguf.gguf
│       │       └── phi35_quick_gguf-q4_0.gguf
│       └── summary.json                ← Overall summary
│
├── deployed_models/                    ← Production models
│   ├── phi35_quick_gguf-latest.gguf
│   └── model-manifest.json
│
├── GGUF_AUTOMATION_QUICKSTART.md       ← User guide
└── GGUF_TRAINING_INTEGRATION_GUIDE.md  ← This file
```

---

## Command Reference

### Quick Commands

```bash
# 1. Dry-run (show what would execute)
python scripts/gguf_training_automation.py --quick --dry-run

# 2. Run quick pipeline (1 model)
python scripts/gguf_training_automation.py --quick

# 3. Run full pipeline (all models)
python scripts/gguf_training_automation.py --full

# 4. Convert existing LoRA model
python scripts/gguf_training_automation.py \
  --convert-only data_out/lora_training/phi35/checkpoint-100

# 5. Validate GGUF file
python scripts/gguf_training_automation.py \
  --validate deployed_models/phi35_quick_gguf-latest.gguf

# 6. Run specific jobs
python scripts/gguf_training_automation.py \
  --jobs phi35_quick_gguf qwen25_quick_gguf
```

### VS Code Integration

Press `Ctrl+Shift+P` and search for:
- `Tasks: Run Task → GGUF: Quick Training`
- `Tasks: Run Task → GGUF: Full Pipeline`
- `Tasks: Run Task → GGUF: Dry-Run`
- `Tasks: Run Task → GGUF: Convert Existing Model`
- `Tasks: Run Task → GGUF: Validate Model`

---

## Usage Scenarios

### Scenario 1: First-Time Setup (Quick Test)

```bash
# 1. Dry-run to see what will happen
python scripts/gguf_training_automation.py --quick --dry-run

# 2. Run the pipeline
python scripts/gguf_training_automation.py --quick

# 3. Check results
cat data_out/gguf_training/summary.json

# 4. Use the model
python talk-to-ai/src/chat_cli.py \
  --provider lora \
  --adapter-path deployed_models/phi35_quick_gguf-latest.gguf \
  --once "What is GGUF?"
```

### Scenario 2: Production Deployment

```bash
# 1. Run full pipeline with all models
python scripts/gguf_training_automation.py --full

# 2. Validate all outputs
for gguf in deployed_models/*.gguf; do
  python scripts/gguf_training_automation.py --validate "$gguf"
done

# 3. Archive models
tar -czf deployed_models.tar.gz deployed_models/
```

### Scenario 3: Convert Existing Model to GGUF

```bash
# You have a trained LoRA adapter from previous run
# Skip training, just convert & deploy

python scripts/gguf_training_automation.py \
  --convert-only data_out/lora_training/phi35/checkpoint-100

# Model now at: deployed_models/convert_only-latest.gguf
```

### Scenario 4: Automated Daily Training

Create `daily-gguf-train.sh`:

```bash
#!/bin/bash
cd /workspaces/AI
timestamp=$(date +%Y%m%d_%H%M%S)
python scripts/gguf_training_automation.py --quick \
  | tee "data_out/gguf_training_daily_${timestamp}.log"
```

Add to crontab:
```bash
0 2 * * * /path/to/daily-gguf-train.sh
```

---

## Configuration

### Global Settings

Edit `config/training/gguf_training.yaml`:

```yaml
global:
  quantization_default: q4_0      # Default quantization
  validate_default: true          # Always validate
  deploy_default: false           # Don't auto-deploy
  export_type: safetensors        # Export format
```

### Add Custom Job

```yaml
jobs:
  - name: my_custom_model
    base_model: my-org/my-base-model
    quantization_type: q5_0
    validate: true
    deploy: false
```

### Change Quantization Strategy

```yaml
quantization_presets:
  q4_0:
    description: "Smallest, fastest"
    reduction: 0.4
    
  q5_0:
    description: "Balanced"
    reduction: 0.6
    
  f16:
    description: "High quality"
    reduction: 0.8
```

---

## Output & Results

### Status JSON Structure

`data_out/gguf_training/<job>/<timestamp>/status.json`:

```json
{
  "name": "phi35_quick_gguf",
  "timestamp": "2026-01-17T10:30:00Z",
  "output_dir": "...",
  "phases": {
    "training": {
      "success": true,
      "model_path": "..."
    },
    "conversion": {
      "success": true,
      "gguf_path": "phi35_quick_gguf.gguf",
      "size_mb": 1547.3
    },
    "quantization": {
      "success": true,
      "quantized_path": "phi35_quick_gguf-q4_0.gguf",
      "size_mb": 643.2
    },
    "validation": {
      "success": true,
      "file_size_mb": 643.2,
      "gguf_version": 3,
      "tensor_count": 324
    },
    "deployment": {
      "success": true,
      "deploy_path": "/workspaces/AI/deployed_models/phi35_quick_gguf-latest.gguf"
    }
  }
}
```

### Log Files

Each job has detailed logs:

- `training.log` — AutoTrain output
- `conversion.log` — GGUF conversion details
- `quantization.log` — Quantization process
- `validation.log` — Format validation results
- `status.log` — Complete execution timeline

---

## Integration with Existing Systems

### With AutoTrain

The GGUF automation uses `scripts/autotrain.py` for Phase 1:

```python
# Inside gguf_training_automation.py
cmd = [
    sys.executable,
    str(REPO_ROOT / "scripts" / "autotrain.py"),
    "--job", job.name
]
```

**Benefit:** Reuses all existing training configurations in `config/training/autotrain.yaml`.

### With Chat CLI

Use GGUF models with chat:

```bash
python talk-to-ai/src/chat_cli.py \
  --provider lora \
  --adapter-path deployed_models/phi35_quick_gguf-latest.gguf \
  --once "Test message"
```

### With Azure Functions

Add GGUF model inference endpoint:

```python
# In function_app.py
@app.route("api/gguf-chat", methods=["POST"])
def gguf_chat(req: func.HttpRequest):
    # Load model from deployed_models/
    model_path = DEPLOYED / "phi35_quick_gguf-latest.gguf"
    # Run inference...
```

### With Quantum Training

Convert quantum models to GGUF:

```bash
# Quantum outputs in data_out/quantum_training/
# Convert to GGUF for broader compatibility
python scripts/gguf_training_automation.py \
  --convert-only data_out/quantum_training/best_model
```

---

## Performance Considerations

### Training Time

- **Quick**: ~5-15 minutes (1 model, small dataset)
- **Full**: ~30-60 minutes (2-3 models, multi-level quantization)

### Disk Space

- **Training artifacts**: ~2-5 GB (temporary, can be deleted)
- **GGUF files**: ~1-10 GB depending on quantization
- **Quantized models**: ~40-80% reduction from original

### Memory Requirements

- **Training phase**: 16 GB+ GPU memory (if using CUDA)
- **Conversion phase**: 8-16 GB RAM
- **Quantization phase**: 4-8 GB RAM
- **Validation phase**: <1 GB

### GPU Acceleration

Training automatically uses GPU if available:

```python
# In autotrain.yaml
device: cuda  # Uses GPU if available, falls back to CPU
```

---

## Troubleshooting

### Phase Failures

**Training fails**
```bash
# Check autotrain logs
cat data_out/autotrain/phi35_quick_gguf/*/stdout.log

# Validate config
python scripts/autotrain.py --dry-run
```

**Conversion fails**
```bash
# Check if base model is downloaded
huggingface-cli ls-repo-files microsoft/Phi-3.5-mini-instruct

# Verify LoRA adapter
ls -la data_out/lora_training/phi35/checkpoint-100/
```

**Quantization fails**
```bash
# Check if llama.cpp is installed
which quantize

# Fallback method will be used automatically
# Check quantization.log for details
```

**Validation fails**
```bash
# Inspect GGUF file
python scripts/visualize_gguf_simple.py deployed_models/*.gguf

# Check file integrity
file deployed_models/*.gguf
```

### Deployment Issues

**Models not deployed**
```bash
# Check deploy flag in config
grep "deploy:" config/training/gguf_training.yaml

# Manually deploy
cp data_out/gguf_training/*/*/phi35-q4_0.gguf deployed_models/
```

**Out of Disk Space**
```bash
# Clean old training artifacts
rm -rf data_out/lora_training/*/checkpoint-*

# Compress and archive
tar -czf archive.tar.gz data_out/gguf_training/
```

---

## Advanced Configuration

### Custom Quantization Pipeline

Edit `gguf_training_automation.py`:

```python
def quantize_gguf(self, job, gguf_path):
    # Add custom quantization logic
    if job.quantization_type == "custom":
        # Your quantization code here
        pass
```

### Parallel Job Execution

Modify for concurrent runs:

```python
from concurrent.futures import ThreadPoolExecutor

def run_all_parallel(self):
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(self.run_job, job) for job in self.jobs]
        return [f.result() for f in futures]
```

### Model Benchmarking

Add inference benchmarks:

```bash
# Compare model performance
for model in deployed_models/*.gguf; do
  time python -c "
    # Load and run inference
    pass
  "
done
```

---

## Monitoring & Observability

### Real-Time Progress

```bash
# Watch training progress
watch -n 5 'cat data_out/gguf_training/*/*/status.log | tail -20'

# Monitor resource usage
watch -n 2 'nvidia-smi'
```

### Status Dashboard

```bash
# Generate report
python scripts/results_exporter.py \
  --dir data_out/gguf_training \
  --format markdown \
  --output report.md
```

### Automated Alerts

Configure notifications (optional):

```yaml
# config/notification_config.yaml
notifications:
  email:
    enabled: true
    on_success: false
    on_failure: true
  slack:
    enabled: false
```

---

## Best Practices

✅ **DO:**
- Run `--dry-run` before first execution
- Validate outputs with `--validate`
- Keep `deployed_models/` backed up
- Monitor disk space during training
- Use `--quick` for testing, `--full` for production

❌ **DON'T:**
- Run multiple full pipelines concurrently on same GPU
- Delete training artifacts immediately (keep for rollback)
- Use `f32` quantization unless absolutely necessary
- Train without backup of existing models
- Modify `data_out/gguf_training/` files directly

---

## See Also

- [GGUF_AUTOMATION_QUICKSTART.md](../GGUF_AUTOMATION_QUICKSTART.md) — Quick reference
- [GPU_TRAINING_SUMMARY.md](../GPU_TRAINING_SUMMARY.md) — GPU setup guide
- [scripts/gguf_training_automation.py](../scripts/gguf_training_automation.py) — Source code
- [config/training/gguf_training.yaml](../config/training/gguf_training.yaml) — Configuration
- [GGUF spec](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md) — Format documentation
