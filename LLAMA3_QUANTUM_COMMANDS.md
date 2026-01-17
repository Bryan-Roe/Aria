# 🚀 LLaMA 3 + Quantum ML - Command Reference

## One-Command Cheat Sheet

```bash
# 👀 Preview (no GPU needed)
python scripts/gguf_training_automation.py --quick --dry-run

# ⚡ Train quick quantum LLaMA 3 (5-10 min)
python scripts/gguf_training_automation.py --quick --jobs llama3_quantum_quick

# 🎯 Train all quantum models (40-60 min)
python scripts/gguf_training_automation.py --full --quantum

# 💬 Use trained model
python talk-to-ai/src/chat_cli.py --model-path deployed_models/llama3_quantum_prod-latest.gguf
```

## Model Selection Guide

### For Testing/Experimentation
```bash
python scripts/gguf_training_automation.py --quick --jobs llama3_quantum_quick
# Result: ~2.5 GB GGUF, optimized for speed, reasonable quality
```

### For Production
```bash
python scripts/gguf_training_automation.py --full --jobs llama3_quantum_prod
# Result: ~3.5 GB GGUF, balanced quality/speed, deployable
```

### For Research/Maximum Quality
```bash
python scripts/gguf_training_automation.py --full --jobs llama3_hq_quantum
# Result: ~16 GB GGUF, highest quality, slower inference
```

### For Edge/Mobile Devices
```bash
python scripts/gguf_training_automation.py --full --jobs llama3_light_quantum
# Result: ~0.4 GB GGUF, fast on mobile, lower quality
```

## Training Pipeline Phases

```
Step 1: Quantum Enhancement ⚛️
        ↓
Step 2: LoRA Training 🧠
        ↓
Step 3: GGUF Conversion 🔄
        ↓
Step 4: Quantization ⚙️
        ↓
Step 5: Validation ✅
        ↓
Step 6: Deployment 📦
```

## Feature Matrix

| Feature | Quick | Prod | HQ | Light |
|---------|-------|------|----|----|
| variational_encoding | ✓ | ✓ | ✓ | ✓ |
| quantum_attention | ✓ | ✓ | ✓ | ✗ |
| entanglement_layer | ✓ | ✓ | ✓ | ✗ |
| quantum_classifier_head | ✗ | ✓ | ✓ | ✗ |
| full_quantum_stack | ✗ | ✗ | ✓ | ✗ |
| multi_head_quantum_attention | ✗ | ✗ | ✓ | ✗ |
| adaptive_entanglement | ✗ | ✗ | ✓ | ✗ |
| lightweight_quantum_attention | ✗ | ✗ | ✗ | ✓ |

## Environment Setup

```bash
# Verify Python installation
python --version

# Verify YAML config loads
python -c "import yaml; yaml.safe_load(open('config/training/gguf_training.yaml'))"

# Check available models
python scripts/gguf_training_automation.py --quick --dry-run | grep llama3
```

## Workflow Examples

### Example 1: Complete Training Cycle
```bash
# Step 1: Dry-run
python scripts/gguf_training_automation.py --quick --dry-run

# Step 2: Train
python scripts/gguf_training_automation.py --quick --jobs llama3_quantum_quick

# Step 3: Check results
ls -lh deployed_models/llama3_quantum_quick-latest.gguf

# Step 4: Test
python talk-to-ai/src/chat_cli.py \
  --model-path deployed_models/llama3_quantum_quick-latest.gguf
```

### Example 2: Compare Models
```bash
# Train baseline
python scripts/gguf_training_automation.py --quick --jobs phi35_quick_gguf

# Train quantum variant
python scripts/gguf_training_automation.py --quick --jobs llama3_quantum_quick

# Compare files
ls -lh deployed_models/phi35_quick_gguf-latest.gguf deployed_models/llama3_quantum_quick-latest.gguf
```

### Example 3: Full Production Setup
```bash
# Train all quantum models
python scripts/gguf_training_automation.py --full --quantum

# Verify all deployed
ls -lh deployed_models/*llama3*.gguf

# Total size
du -sh deployed_models/
```

## File Management

### Check Training Status
```bash
# Latest results
cat data_out/gguf_training/llama3_quantum_quick/*/status.json | jq .

# Live logs
tail -f data_out/gguf_training/llama3_quantum_quick/*/status.log

# Quantum config
cat data_out/gguf_training/llama3_quantum_quick/*/quantum_enhancements/quantum_config.json | jq .
```

### Cleanup Old Models
```bash
# Remove old training runs (keep deployed models)
rm -rf data_out/gguf_training/llama3_quantum_quick/

# Keep only latest deployed
ls -lh deployed_models/*llama3*.gguf
```

## Advanced Options

### Custom Configuration
```bash
# Create custom config
cp config/training/gguf_training.yaml my_custom.yaml
# Edit my_custom.yaml...

# Use custom config
python scripts/gguf_training_automation.py --full --config my_custom.yaml
```

### Train Specific Jobs
```bash
# Single job
python scripts/gguf_training_automation.py --full --jobs llama3_quantum_prod

# Multiple specific jobs
python scripts/gguf_training_automation.py --full \
  --jobs llama3_quantum_quick llama3_quantum_prod llama3_light_quantum
```

### Filter by Criteria
```bash
# All quantum models
python scripts/gguf_training_automation.py --full --quantum

# All non-quantum models
python scripts/gguf_training_automation.py --full --jobs phi35_quick_gguf qwen25_quick_gguf
```

## Integration Examples

### With Chat CLI
```bash
# Interactive chat
python talk-to-ai/src/chat_cli.py \
  --model-path deployed_models/llama3_quantum_prod-latest.gguf

# One-shot query
python talk-to-ai/src/chat_cli.py \
  --model-path deployed_models/llama3_quantum_prod-latest.gguf \
  --once "What is quantum computing?"
```

### With Aria Web Interface
```bash
# Start Aria with quantum LLaMA 3
cd aria_web
python server.py --model ../deployed_models/llama3_quantum_prod-latest.gguf

# Open browser: http://localhost:8080
```

### With Azure Functions
```bash
# Start functions
func host start

# Make API call
curl http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello quantum AI",
    "model": "llama3_quantum_prod"
  }'
```

## Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: yaml` | `pip install pyyaml` |
| CUDA out of memory | Use `llama3_light_quantum` instead |
| Model file too large | Use `q4_0` quantization |
| Slow quantization | Skip with `quantization_type: f32` |
| Model download fails | `huggingface-cli login` |

## Performance Expectations

### Training Time
- **Quick**: 5-10 minutes per model (GPU)
- **Prod**: 10-20 minutes per model (GPU)
- **HQ**: 15-30 minutes per model (GPU)
- **Light**: 3-5 minutes per model (GPU)

### Output Sizes
- **Q4 (Quick)**: ~2-3 GB
- **Q5 (Prod)**: ~3-4 GB
- **F16 (HQ)**: ~15-16 GB
- **Q4 (Light)**: ~0.3-0.5 GB

### Memory Requirements
- **During Training**: 8-16 GB VRAM
- **During Inference**: 2-8 GB RAM (depends on model)

## Documentation

| Document | Purpose |
|----------|---------|
| [LLAMA3_QUANTUM_INTEGRATION.md](LLAMA3_QUANTUM_INTEGRATION.md) | Comprehensive guide |
| [LLAMA3_QUANTUM_QUICK_REFERENCE.md](LLAMA3_QUANTUM_QUICK_REFERENCE.md) | Quick reference |
| [LLAMA3_QUANTUM_IMPLEMENTATION_SUMMARY.md](LLAMA3_QUANTUM_IMPLEMENTATION_SUMMARY.md) | Technical summary |
| This file | Command reference |

## Common Workflows

### Minimal (Just Test)
```bash
python scripts/gguf_training_automation.py --quick --dry-run
```

### Standard (Train One Model)
```bash
python scripts/gguf_training_automation.py --quick --jobs llama3_quantum_quick
```

### Full (Train All Quantum)
```bash
python scripts/gguf_training_automation.py --full --quantum
```

### Extended (Everything)
```bash
python scripts/gguf_training_automation.py --full
```

## Support

Need help? Check:
1. Training logs: `tail -f data_out/gguf_training/<job>/**/*.log`
2. Status file: `cat data_out/gguf_training/<job>/*/status.json`
3. Full docs: [LLAMA3_QUANTUM_INTEGRATION.md](LLAMA3_QUANTUM_INTEGRATION.md)

---

**Last Updated**: January 17, 2026
**Status**: ✅ Production Ready

