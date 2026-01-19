# GGUF Training Automation Quick Reference

## What is GGUF?

**GGUF (GGUQ Universal Format)** is an efficient model format for:
- ✅ Reduced file size through quantization (40-80% smaller)
- ✅ Faster inference with llama.cpp and compatible engines
- ✅ Multi-platform support (CPU, GPU, mobile)
- ✅ Hardware optimization (AVX, CUDA, Metal)

**Quantization types:**
- `q4_0` — 4-bit quantization (⚡ fastest, smallest, lower quality)
- `q5_0` — 5-bit quantization (good balance)
- `f16` — 16-bit float (high quality, medium size)
- `f32` — Full precision (best quality, largest file)

---

## Quick Start

### 1️⃣ Run Quick Training → GGUF Pipeline
```bash
cd /workspaces/AI
python scripts/training/gguf_training_automation.py --quick
```

**What happens:**
- Trains Phi-3.5 model (quick job)
- Converts to GGUF format
- Quantizes to q4_0
- Validates the output
- Model saved to `data_out/gguf_training/phi35_quick_gguf/`

### 2️⃣ Run Full Pipeline (All Models)
```bash
python scripts/training/gguf_training_automation.py --full
```

**Includes:**
- Phi-3.5 and Qwen 2.5 models
- Multiple quantization levels (q4_0, q5_0, f16)
- Automatic deployment to `deployed_models/`
- Comprehensive validation

### 3️⃣ Dry-Run (Show What Would Execute)
```bash
python scripts/training/gguf_training_automation.py --quick --dry-run
```

Shows all steps without executing them.

---

## Advanced Usage

### Convert Existing LoRA Model to GGUF
```bash
python scripts/training/gguf_training_automation.py \
  --convert-only data_out/lora_training/phi35/checkpoint-100
```

Skips training, only runs conversion → quantization → validation → deployment.

### Validate GGUF File
```bash
python scripts/training/gguf_training_automation.py --validate deployed_models/phi35-latest.gguf
```

Checks:
- ✓ GGUF magic number
- ✓ File version
- ✓ Tensor count
- ✓ File integrity

### Specific Jobs Only
```bash
python scripts/training/gguf_training_automation.py --jobs phi35_quick_gguf qwen25_quick_gguf
```

---

## Pipeline Phases

### Phase 1: Training
- Uses existing `scripts/training/autotrain.py`
- Trains LoRA adapters on your dataset
- Output: `data_out/lora_training/<job_name>/`

### Phase 2: GGUF Conversion
- Loads trained LoRA model
- Merges with base model
- Exports to GGUF binary format
- Output: `*.gguf` file

### Phase 3: Quantization
- Reduces model size through quantization
- Supports: q4_0, q5_0, f16, f32
- Output: `*-<quantization_type>.gguf`

### Phase 4: Validation
- Verifies GGUF file integrity
- Checks magic number (0x46554747)
- Counts tensors
- Validates file format

### Phase 5: Deployment
- Copies validated model to `deployed_models/`
- Creates backup of previous version
- Optional: Creates symlink for easy access
- Output: `deployed_models/<name>-latest.gguf`

---

## Output Structure

```
data_out/gguf_training/
├── phi35_quick_gguf/
│   └── 2026-01-17T10:30:00Z/
│       ├── training.log              # Training phase output
│       ├── conversion.log             # GGUF conversion logs
│       ├── quantization.log           # Quantization details
│       ├── validation.log             # Validation results
│       ├── status.log                 # Complete execution log
│       ├── status.json                # Machine-readable status
│       ├── phi35_quick_gguf.gguf      # Converted GGUF
│       └── phi35_quick_gguf-q4_0.gguf # Quantized version
├── qwen25_quick_gguf/
│   └── ...
└── summary.json                       # Overall pipeline summary

deployed_models/
├── phi35_quick_gguf-latest.gguf       # Latest phi35 model
├── qwen25_quick_gguf-latest.gguf      # Latest qwen25 model
└── model-manifest.json                # Model inventory
```

---

## Status Files

### Individual Job Status
`data_out/gguf_training/<job_name>/<timestamp>/status.json`

```json
{
  "name": "phi35_quick_gguf",
  "timestamp": "2026-01-17T10:30:00Z",
  "output_dir": "/workspaces/AI/data_out/gguf_training/phi35_quick_gguf/...",
  "phases": {
    "training": {
      "success": true,
      "model_path": "/workspaces/AI/data_out/lora_training/phi35/..."
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

### Pipeline Summary
`data_out/gguf_training/summary.json`

Shows overall results for all jobs in one run.

---

## Integration with Existing Tools

### Use GGUF Models with Chat CLI
```bash
python talk-to-ai/src/chat_cli.py \
  --provider lora \
  --adapter-path deployed_models/phi35_quick_gguf-latest.gguf \
  --once "Hello, world!"
```

### Inspect GGUF Files
```bash
python scripts/visualize_gguf_simple.py deployed_models/phi35_quick_gguf-latest.gguf
```

Shows:
- Model architecture
- Tensor dimensions
- Parameter count
- Estimated inference requirements

### Export Analysis to Markdown
```bash
python scripts/visualize_gguf_simple.py \
  deployed_models/phi35_quick_gguf-latest.gguf \
  --md data_out/gguf_analysis.md
```

---

## Troubleshooting

### ❌ "GGUF conversion failed"
- Check training phase output: `cat data_out/gguf_training/<job>/*/conversion.log`
- Ensure base model is downloaded: `huggingface-cli download <model_id>`
- Verify LoRA adapter path is correct

### ❌ "Quantization failed"
- Check if llama.cpp is installed: `which quantize`
- Fallback quantization will be used automatically
- Check `quantization.log` for details

### ❌ "Validation failed"
- File may be corrupted during conversion
- Check file size: `ls -lh deployed_models/*.gguf`
- Re-run conversion phase with `--convert-only`

### ⚠️ Out of Memory During Training
- Use smaller dataset: Edit autotrain.yaml
- Reduce batch size
- Use `--quick` instead of `--full`

### 🔍 Debug Mode
```bash
# Run with full logging
python scripts/training/gguf_training_automation.py --quick 2>&1 | tee debug.log

# Check phase logs individually
cat data_out/gguf_training/phi35_quick_gguf/*/training.log
cat data_out/gguf_training/phi35_quick_gguf/*/conversion.log
cat data_out/gguf_training/phi35_quick_gguf/*/validation.log
```

---

## Performance & Optimization

### Model Sizes (Approximate)
For 3B parameter models:

| Quantization | Size  | Speed      | Quality |
|--------------|-------|------------|---------|
| q4_0         | 1.5GB | ⚡⚡⚡    | ★★☆☆☆ |
| q5_0         | 2.2GB | ⚡⚡     | ★★★☆☆ |
| f16          | 6GB   | ⚡        | ★★★★☆ |
| f32          | 12GB  | 🐌        | ★★★★★ |

### Recommended Quantizations

**For deployment:**
- `q4_0` — CPU/mobile devices
- `q5_0` — Balanced (recommended)
- `f16` — High-quality requirements

**For inference speed:**
- `q4_0` — Fastest
- `q5_0` — Good balance
- `f16` — Slower but better quality

---

## Configuration

Edit `config/training/gguf_training.yaml` to:
- Add new jobs
- Change default quantization
- Configure deployment behavior
- Set validation checks

Example: Add custom job
```yaml
jobs:
  - name: my_custom_model
    base_model: my-org/my-model
    quantization_type: q5_0
    validate: true
    deploy: true
```

---

## Automation with Cron/Scheduler

### Daily GGUF Training (Linux/Mac)
```bash
# Add to crontab
0 2 * * * cd /workspaces/AI && python scripts/training/gguf_training_automation.py --quick >> data_out/gguf_training.log 2>&1
```

### Windows Task Scheduler
```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "python" -Argument "scripts\gguf_training_automation.py --quick"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
Register-ScheduledTask -TaskName "GGUF-Training" -Action $action -Trigger $trigger
```

---

## VS Code Integration

Added tasks in `.vscode/tasks.json`:

```bash
# Run from command palette (Ctrl+Shift+P)
Tasks: Run Task → GGUF: Quick Training
Tasks: Run Task → GGUF: Full Pipeline
Tasks: Run Task → GGUF: Dry-Run
Tasks: Run Task → GGUF: Validate Model
```

---

## Next Steps

1. **First run:** `python scripts/training/gguf_training_automation.py --quick --dry-run`
2. **Then execute:** `python scripts/training/gguf_training_automation.py --quick`
3. **Check results:** Open `data_out/gguf_training/summary.json`
4. **Use model:** `python talk-to-ai/src/chat_cli.py --provider lora --adapter-path deployed_models/phi35_quick_gguf-latest.gguf --once "test"`
5. **Automate:** Add to cron/scheduler for continuous training

---

## See Also

- [GPU_TRAINING_SUMMARY.md](../GPU_TRAINING_SUMMARY.md) — GPU setup & progressive training
- [scripts/training/autotrain.py](../scripts/training/autotrain.py) — LoRA training orchestrator
- [scripts/visualize_gguf_simple.py](../scripts/visualize_gguf_simple.py) — GGUF inspection tool
- [config/training/gguf_training.yaml](../config/training/gguf_training.yaml) — Configuration
