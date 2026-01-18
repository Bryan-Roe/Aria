# GGUF Training Automation — Setup Complete ✅

## What Was Created

I've automated GGUF training for your Aria platform with a complete, production-ready pipeline:

### 1. **Main Orchestrator Script**
📁 `scripts/gguf_training_automation.py` (500+ lines)

**Features:**
- ✅ Automated 5-phase pipeline (train → convert → quantize → validate → deploy)
- ✅ Dry-run mode for safe testing
- ✅ Comprehensive logging and status tracking
- ✅ Error recovery and graceful fallbacks
- ✅ JSON status files for machine-readable results
- ✅ Integration with existing `autotrain.py`

### 2. **Configuration Files**
📁 `config/training/gguf_training.yaml`

Defines:
- GGUF training jobs with base models
- Quantization presets (q4_0, q5_0, f16, f32)
- Deployment options
- Validation checks

### 3. **VS Code Tasks** (5 new tasks)
Added to `.vscode/tasks.json`:
- `GGUF: Quick Training`
- `GGUF: Full Pipeline`
- `GGUF: Dry-Run`
- `GGUF: Convert Existing Model`
- `GGUF: Validate Model`

**Access:** Press `Ctrl+Shift+P` → Search `GGUF`

### 4. **Documentation**
📄 `GGUF_AUTOMATION_QUICKSTART.md` — User-friendly guide
📄 `GGUF_TRAINING_INTEGRATION_GUIDE.md` — Technical integration details

---

## Quick Start (60 Seconds)

### Option A: Dry-Run (See What Would Happen)
```bash
cd /workspaces/AI
python scripts/gguf_training_automation.py --quick --dry-run
```

### Option B: Quick Training (One Model)
```bash
python scripts/gguf_training_automation.py --quick
```

**What happens:**
1. Trains Phi-3.5 model using existing `autotrain.py`
2. Converts to GGUF format
3. Quantizes to q4_0 (highly compressed)
4. Validates the output
5. Deploys to `deployed_models/`

**Estimated time:** 5-15 minutes

### Option C: Full Pipeline (All Models)
```bash
python scripts/gguf_training_automation.py --full
```

**Trains & deploys:**
- Phi-3.5 (q4_0, q5_0, f16)
- Qwen 2.5 (q4_0, q5_0, f16)

**Estimated time:** 30-60 minutes

---

## Pipeline Overview

```
┌──────────────────────────────────────────────────────────┐
│          5-Phase GGUF Training Automation               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 1️⃣  TRAINING (5-10 min)                                 │
│    └─ Trains LoRA adapter on your dataset              │
│    └─ Uses: scripts/autotrain.py                       │
│    └─ Output: Trained model weights                    │
│                                                          │
│ 2️⃣  GGUF CONVERSION (2-5 min)                           │
│    └─ Merges LoRA adapter with base model              │
│    └─ Converts to GGUF binary format                   │
│    └─ Output: model.gguf (~1.5 GB)                     │
│                                                          │
│ 3️⃣  QUANTIZATION (1-3 min)                              │
│    └─ Compresses model (q4_0, q5_0, f16, f32)         │
│    └─ Reduces size by 40-80%                           │
│    └─ Output: model-q4_0.gguf (~600 MB)               │
│                                                          │
│ 4️⃣  VALIDATION (30 sec)                                 │
│    └─ Verifies GGUF file integrity                     │
│    └─ Checks format compliance                         │
│    └─ Output: Validation report                        │
│                                                          │
│ 5️⃣  DEPLOYMENT (<1 min)                                 │
│    └─ Copies to deployed_models/                       │
│    └─ Creates symlinks & backups                       │
│    └─ Output: Production-ready model                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Output Structure

After running, you'll have:

```
data_out/gguf_training/
├── phi35_quick_gguf/
│   └── 2026-01-17T10:30:00Z/
│       ├── status.json              ← Results (machine-readable)
│       ├── status.log               ← Execution log
│       ├── training.log             ← Phase 1 details
│       ├── conversion.log           ← Phase 2 details
│       ├── quantization.log         ← Phase 3 details
│       ├── validation.log           ← Phase 4 details
│       ├── phi35_quick_gguf.gguf    ← Converted model
│       └── phi35_quick_gguf-q4_0.gguf  ← Quantized (deployed)
└── summary.json                    ← Overall results

deployed_models/
├── phi35_quick_gguf-latest.gguf   ← Ready for production
└── model-manifest.json            ← Model inventory
```

---

## Key Features

### ✨ Automatic Integration
- Uses your existing training configs in `autotrain.yaml`
- Reuses `autotrain.py` for Phase 1 (no duplication)
- Compatible with all existing models and datasets

### 🔄 Smart Fallbacks
- If `llama.cpp quantize` unavailable → fallback quantization
- If training fails → skips to conversion (for existing models)
- Graceful error handling throughout

### 📊 Comprehensive Tracking
- JSON status files for each job
- Overall pipeline summary
- Detailed logs for each phase
- Human-readable reports

### 🎯 Flexible Modes
- `--quick` — Test with 1 model
- `--full` — Production with all models
- `--dry-run` — Preview without executing
- `--convert-only` — Skip training, convert existing model
- `--validate` — Check GGUF file integrity

### 🚀 VS Code Integration
Run from Command Palette (`Ctrl+Shift+P`):
- Type `GGUF` to see all available tasks
- Click to run directly without terminal

---

## Usage Examples

### 1. Test the System (Safe)
```bash
python scripts/gguf_training_automation.py --quick --dry-run
# Shows: "Would execute: ... [DRY-RUN]"
# Doesn't actually run anything
```

### 2. Train & Deploy One Model
```bash
python scripts/gguf_training_automation.py --quick
# Trains, converts, quantizes, validates, deploys
# Model ready at: deployed_models/phi35_quick_gguf-latest.gguf
```

### 3. Convert Existing LoRA Model
```bash
python scripts/gguf_training_automation.py \
  --convert-only data_out/lora_training/my_model/checkpoint-100
# Skips training, goes straight to conversion
```

### 4. Validate GGUF File
```bash
python scripts/gguf_training_automation.py \
  --validate deployed_models/phi35_quick_gguf-latest.gguf
# Checks file integrity and format compliance
```

### 5. Use Model with Chat CLI
```bash
python talk-to-ai/src/chat_cli.py \
  --provider lora \
  --adapter-path deployed_models/phi35_quick_gguf-latest.gguf \
  --once "Hello, GGUF model!"
# Chat with the deployed GGUF model
```

---

## Configuration

### Edit Training Jobs
File: `config/training/gguf_training.yaml`

```yaml
jobs:
  - name: my_model
    base_model: microsoft/Phi-3.5-mini-instruct
    quantization_type: q4_0
    validate: true
    deploy: false
```

### Change Default Quantization
```yaml
global:
  quantization_default: q5_0  # Changed from q4_0
```

### Add New Job
```yaml
jobs:
  - name: new_job_name
    base_model: new-org/new-model
    quantization_type: q5_0
    validate: true
    deploy: true
```

---

## Status & Results

### Quick Status Check
```bash
# View last job's results
cat data_out/gguf_training/summary.json

# View specific job results
cat data_out/gguf_training/phi35_quick_gguf/*/status.json
```

### Check Deployed Models
```bash
# List available models
ls -lh deployed_models/*.gguf

# Inspect model details
python scripts/visualize_gguf_simple.py deployed_models/phi35_quick_gguf-latest.gguf
```

---

## Troubleshooting

### ❓ "Dry-run shows [DRY-RUN] messages"
→ Normal! Just showing what would execute. Remove `--dry-run` to actually run.

### ❓ "Model path not found"
→ Ensure training phase completed. Check `training.log` in job directory.

### ❓ "GGUF conversion failed"
→ Check conversion.log. Ensure base model is downloaded from HuggingFace.

### ❓ "Out of memory"
→ Edit `autotrain.yaml` to use smaller dataset or reduce batch size.

### ❓ "Where are my GGUF files?"
→ Check: `deployed_models/` (production) or `data_out/gguf_training/` (all phases)

---

## Next Steps

### 1. Try It Now (Quick)
```bash
python scripts/gguf_training_automation.py --quick --dry-run
```

### 2. Run Full Pipeline
```bash
python scripts/gguf_training_automation.py --quick
```

### 3. Check Results
```bash
cat data_out/gguf_training/summary.json
```

### 4. Use the Model
```bash
python talk-to-ai/src/chat_cli.py \
  --provider lora \
  --adapter-path deployed_models/phi35_quick_gguf-latest.gguf \
  --once "test"
```

### 5. Automate (Optional)
Add to cron for daily training:
```bash
0 2 * * * cd /workspaces/AI && python scripts/gguf_training_automation.py --quick
```

---

## Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `scripts/gguf_training_automation.py` | ✨ NEW | Main orchestrator (500+ lines) |
| `config/training/gguf_training.yaml` | ✨ NEW | GGUF job configuration |
| `.vscode/tasks.json` | 🔄 UPDATED | Added 5 new tasks |
| `GGUF_AUTOMATION_QUICKSTART.md` | ✨ NEW | User guide |
| `GGUF_TRAINING_INTEGRATION_GUIDE.md` | ✨ NEW | Technical documentation |

---

## Key Concepts

### GGUF Format
Binary format optimized for inference engines (llama.cpp, etc.)
- Smaller file size (quantization)
- Faster loading
- Better hardware utilization

### Quantization Types
- **q4_0** (smallest, fastest) → Use for: Mobile, constrained resources
- **q5_0** (balanced) → Use for: Most cases (recommended)
- **f16** (high quality) → Use for: Quality-critical applications
- **f32** (full precision) → Use for: Research, benchmarks

### Phase Breakdown
1. **Train** — Fine-tune on your data
2. **Convert** — GGUF binary format
3. **Quantize** — Compress for inference
4. **Validate** — Verify integrity
5. **Deploy** — Ready for production

---

## Support & Documentation

📖 **Comprehensive guides:**
- `GGUF_AUTOMATION_QUICKSTART.md` — 5-minute quick start
- `GGUF_TRAINING_INTEGRATION_GUIDE.md` — Deep technical guide
- `GPU_TRAINING_SUMMARY.md` — GPU setup & optimization
- `scripts/gguf_training_automation.py` — Fully documented source code

🎯 **Quick commands:**
```bash
# See all available commands
python scripts/gguf_training_automation.py --help

# Check existing GGUF file
python scripts/visualize_gguf_simple.py <file.gguf>

# View task in VS Code (Ctrl+Shift+P)
Tasks: Run Task → GGUF: *
```

---

## You're All Set! 🎉

Everything is ready to automate GGUF training. Start with:

```bash
cd /workspaces/AI
python scripts/gguf_training_automation.py --quick --dry-run
```

Or use VS Code: Press `Ctrl+Shift+P` → Type `GGUF`

Questions? Check the documentation files listed above. Happy training! 🚀
