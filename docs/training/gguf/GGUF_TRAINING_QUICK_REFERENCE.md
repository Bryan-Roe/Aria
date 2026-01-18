# GGUF Training Automation — Quick Reference Card

## One-Liner Commands

```bash
# 🧪 Test (dry-run - safe)
python scripts/gguf_training_automation.py --quick --dry-run

# 🚀 Run quick pipeline (1 model, ~10 min)
python scripts/gguf_training_automation.py --quick

# 🏗️ Run full pipeline (all models, ~1 hour)
python scripts/gguf_training_automation.py --full

# 🔄 Convert existing LoRA model
python scripts/gguf_training_automation.py --convert-only data_out/lora_training/phi35/checkpoint-100

# ✅ Validate GGUF file
python scripts/gguf_training_automation.py --validate deployed_models/phi35_quick_gguf-latest.gguf

# 💬 Chat with deployed model
python talk-to-ai/src/chat_cli.py --provider lora --adapter-path deployed_models/phi35_quick_gguf-latest.gguf --once "test"

# 📊 View results
cat data_out/gguf_training/summary.json

# 🔍 Inspect GGUF file
python scripts/visualize_gguf_simple.py deployed_models/*.gguf
```

---

## 5-Minute Workflow

```
1. Test           5 sec  → python scripts/gguf_training_automation.py --quick --dry-run
2. Train          10 min → python scripts/gguf_training_automation.py --quick
3. Check Results  1 min  → cat data_out/gguf_training/summary.json
4. Use Model      1 min  → python talk-to-ai/src/chat_cli.py --provider lora --adapter-path deployed_models/phi35_quick_gguf-latest.gguf --once "test"
5. Done! 🎉
```

---

## File Locations

| What | Where |
|------|-------|
| **Main Script** | `scripts/gguf_training_automation.py` |
| **Config** | `config/training/gguf_training.yaml` |
| **Results** | `data_out/gguf_training/*/status.json` |
| **Deployed Models** | `deployed_models/*.gguf` |
| **Logs** | `data_out/gguf_training/*/*/*.log` |
| **Quick Start** | `GGUF_AUTOMATION_QUICKSTART.md` |
| **Full Guide** | `GGUF_TRAINING_INTEGRATION_GUIDE.md` |

---

## VS Code Tasks

Press `Ctrl+Shift+P` and type:
- `GGUF: Quick Training` — Run 1 model
- `GGUF: Full Pipeline` — Run all models
- `GGUF: Dry-Run` — Preview (safe)
- `GGUF: Convert Existing Model` — Convert LoRA to GGUF
- `GGUF: Validate Model` — Check GGUF integrity

---

## Quantization Types

| Type | Size | Speed | Quality | Best For |
|------|------|-------|---------|----------|
| q4_0 | 1.5GB | ⚡⚡⚡ | ★★☆☆☆ | Mobile/Edge |
| q5_0 | 2.2GB | ⚡⚡ | ★★★☆☆ | **Recommended** |
| f16 | 6GB | ⚡ | ★★★★☆ | High Quality |
| f32 | 12GB | 🐌 | ★★★★★ | Full Precision |

---

## Exit Codes & Meanings

| Code | Meaning |
|------|---------|
| 0 | Success ✅ |
| 1 | Error ❌ |
| 2 | Config Error |
| 127 | Command Not Found |

---

## Troubleshooting Checklist

- [ ] Training phase: Check `data_out/gguf_training/*/training.log`
- [ ] Conversion failed: Verify base model downloaded
- [ ] Quantization failed: Check disk space
- [ ] Validation failed: Check file size & format
- [ ] Deployment failed: Verify `deployed_models/` exists
- [ ] Out of memory: Use `--quick` or smaller dataset
- [ ] GPU not found: Check `python -c "import torch; print(torch.cuda.is_available())"`

---

## Environment Variables

```bash
# Use CPU only (no GPU)
export CUDA_VISIBLE_DEVICES=""

# Use specific GPU
export CUDA_VISIBLE_DEVICES=0

# Monitor GPU
watch nvidia-smi
```

---

## Daily Automation

Add to crontab:
```bash
0 2 * * * cd /workspaces/AI && python scripts/gguf_training_automation.py --quick
```

---

## Status File Structure

```json
{
  "name": "phi35_quick_gguf",
  "timestamp": "2026-01-17T10:30:00Z",
  "phases": {
    "training": {"success": true, "model_path": "..."},
    "conversion": {"success": true, "gguf_path": "...", "size_mb": 1547},
    "quantization": {"success": true, "quantized_path": "...", "size_mb": 643},
    "validation": {"success": true, "file_size_mb": 643},
    "deployment": {"success": true, "deploy_path": "..."}
  }
}
```

---

## Helpful Aliases

Add to `.bashrc` or `.zshrc`:

```bash
# GGUF Training Automation Aliases
alias gguf-test="python scripts/gguf_training_automation.py --quick --dry-run"
alias gguf-quick="python scripts/gguf_training_automation.py --quick"
alias gguf-full="python scripts/gguf_training_automation.py --full"
alias gguf-status="cat data_out/gguf_training/summary.json | python -m json.tool"
alias gguf-use="python talk-to-ai/src/chat_cli.py --provider lora --adapter-path deployed_models/phi35_quick_gguf-latest.gguf"
alias gguf-logs="tail -f data_out/gguf_training/*/*/status.log"
alias gguf-inspect="python scripts/visualize_gguf_simple.py deployed_models/*.gguf"
```

Then use:
```bash
gguf-test      # Test (dry-run)
gguf-quick     # Run training
gguf-status    # Check results
gguf-use       # Chat with model
```

---

## Resource Requirements

| Phase | CPU | RAM | GPU | Time |
|-------|-----|-----|-----|------|
| Training | 4+ cores | 16GB | 16GB | 5-10 min |
| Conversion | 2+ cores | 8GB | — | 2-5 min |
| Quantization | 2+ cores | 4GB | — | 1-3 min |
| Validation | 1+ core | 1GB | — | 30s |
| Deployment | 1 core | <1GB | — | <1 min |
| **TOTAL** | 4+ cores | 16GB | 16GB | ~20-30 min |

---

## Performance Tips

✅ **Speed Up:**
- Use `--quick` for testing
- Use `q4_0` for fastest inference
- Enable GPU: Check CUDA availability

⚠️ **Avoid:**
- Running multiple full pipelines concurrently
- Using `f32` unless necessary
- Training without GPU backup

💾 **Storage:**
- Quick setup: 5-10 GB
- Full setup: 20-30 GB
- Archive old runs to save space

---

## Documentation Index

1. **This File** — Quick Reference (2 min)
2. **GGUF_AUTOMATION_QUICKSTART.md** — User Guide (5 min)
3. **GGUF_TRAINING_INTEGRATION_GUIDE.md** — Technical (15 min)
4. **GGUF_TRAINING_SETUP_COMPLETE.md** — Setup Info (2 min)
5. **GGUF_TRAINING_COMMANDS_REFERENCE.sh** — Copy-Paste Commands

---

## Support Resources

```bash
# View help
python scripts/gguf_training_automation.py --help

# Check GPU
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# View logs
tail -f data_out/gguf_training/*/*/status.log

# Inspect model
python scripts/visualize_gguf_simple.py deployed_models/*.gguf

# Monitor progress
watch -n 5 'tail -20 data_out/gguf_training/*/*/status.log'
```

---

## Common Workflows

### Scenario 1: First Time Setup
```bash
1. python scripts/gguf_training_automation.py --quick --dry-run  # Preview
2. python scripts/gguf_training_automation.py --quick            # Run
3. cat data_out/gguf_training/summary.json                       # Check
4. python talk-to-ai/src/chat_cli.py --provider lora --adapter-path deployed_models/phi35_quick_gguf-latest.gguf --once "test"
```

### Scenario 2: Production Deployment
```bash
1. python scripts/gguf_training_automation.py --full             # Run all
2. python scripts/gguf_training_automation.py --validate deployed_models/*.gguf  # Validate all
3. tar -czf models_backup.tar.gz deployed_models/                # Backup
4. Deploy deployed_models/ to production
```

### Scenario 3: Scheduled Automation
```bash
# Add to crontab -e:
0 2 * * * cd /workspaces/AI && python scripts/gguf_training_automation.py --quick >> data_out/gguf_daily.log 2>&1
```

---

✨ **Happy Training!** 🚀
