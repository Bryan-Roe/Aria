#!/usr/bin/env bash
# GGUF Training Quick Commands Reference
# Paste these commands into your terminal to automate GGUF training

# ==============================================================================
# 🎯 GGUF TRAINING AUTOMATION COMMANDS
# ==============================================================================

# Navigate to workspace
cd /workspaces/AI

# ==============================================================================
# 1. DRY-RUN (Safe to test, shows what would happen)
# ==============================================================================

# Quick test (1 model, no execution)
python scripts/gguf_training_automation.py --quick --dry-run

# Full test (all models, no execution)
python scripts/gguf_training_automation.py --full --dry-run


# ==============================================================================
# 2. QUICK TRAINING (Fast - single model)
# ==============================================================================

# Train Phi-3.5 → GGUF → Quantize → Validate → Deploy
python scripts/gguf_training_automation.py --quick

# View results
cat data_out/gguf_training/summary.json


# ==============================================================================
# 3. FULL PIPELINE (Comprehensive - all models)
# ==============================================================================

# Train all configured models with different quantizations
python scripts/gguf_training_automation.py --full

# View all results
cat data_out/gguf_training/summary.json


# ==============================================================================
# 4. CONVERT EXISTING LORA MODEL (Skip training)
# ==============================================================================

# Convert a previously trained LoRA model to GGUF
python scripts/gguf_training_automation.py \
  --convert-only data_out/lora_training/phi35/checkpoint-100

# Or use your own path:
# python scripts/gguf_training_automation.py \
#   --convert-only /path/to/your/lora/model


# ==============================================================================
# 5. VALIDATE GGUF FILE (Check integrity)
# ==============================================================================

# Validate a GGUF file
python scripts/gguf_training_automation.py \
  --validate deployed_models/phi35_quick_gguf-latest.gguf

# Validate multiple models
for gguf in deployed_models/*.gguf; do
  echo "Validating: $gguf"
  python scripts/gguf_training_automation.py --validate "$gguf"
done


# ==============================================================================
# 6. RUN SPECIFIC JOBS ONLY
# ==============================================================================

# Run only phi35 models
python scripts/gguf_training_automation.py --jobs phi35_quick_gguf

# Run multiple specific jobs
python scripts/gguf_training_automation.py \
  --jobs phi35_quick_gguf qwen25_quick_gguf


# ==============================================================================
# 7. MONITOR PROGRESS & VIEW LOGS
# ==============================================================================

# Watch training in real-time
watch -n 5 'tail -20 data_out/gguf_training/*/*/status.log'

# View specific phase logs
cat data_out/gguf_training/phi35_quick_gguf/*/training.log
cat data_out/gguf_training/phi35_quick_gguf/*/conversion.log
cat data_out/gguf_training/phi35_quick_gguf/*/quantization.log
cat data_out/gguf_training/phi35_quick_gguf/*/validation.log

# View machine-readable results
cat data_out/gguf_training/phi35_quick_gguf/*/status.json | python -m json.tool


# ==============================================================================
# 8. INSPECT DEPLOYED MODELS
# ==============================================================================

# List deployed GGUF models
ls -lh deployed_models/*.gguf

# Inspect model details
python scripts/visualize_gguf_simple.py deployed_models/phi35_quick_gguf-latest.gguf

# Export model analysis to markdown
python scripts/visualize_gguf_simple.py \
  deployed_models/phi35_quick_gguf-latest.gguf \
  --md data_out/gguf_analysis.md


# ==============================================================================
# 9. USE DEPLOYED MODELS
# ==============================================================================

# Chat with deployed GGUF model
python talk-to-ai/src/chat_cli.py \
  --provider lora \
  --adapter-path deployed_models/phi35_quick_gguf-latest.gguf \
  --once "What is GGUF and why is it useful?"

# Interactive chat session
python talk-to-ai/src/chat_cli.py \
  --provider lora \
  --adapter-path deployed_models/phi35_quick_gguf-latest.gguf


# ==============================================================================
# 10. MAINTENANCE & CLEANUP
# ==============================================================================

# Archive old GGUF training artifacts
tar -czf data_out/gguf_training_archive.tar.gz data_out/gguf_training/

# Clean old training checkpoints (CAREFUL!)
# rm -rf data_out/lora_training/*/checkpoint-*

# Backup deployed models
cp -r deployed_models deployed_models_backup_$(date +%Y%m%d)

# View disk usage
du -sh data_out/gguf_training/
du -sh deployed_models/


# ==============================================================================
# 11. AUTOMATION (Scheduled Training)
# ==============================================================================

# Run daily at 2 AM (add to crontab)
# 0 2 * * * cd /workspaces/AI && python scripts/gguf_training_automation.py --quick

# Add to crontab (Linux/Mac):
# crontab -e
# Then paste:
# 0 2 * * * cd /workspaces/AI && python scripts/gguf_training_automation.py --quick >> data_out/gguf_training_daily.log 2>&1


# ==============================================================================
# 12. TROUBLESHOOTING
# ==============================================================================

# Check Python environment
python --version
pip list | grep -E "torch|transformers|peft"

# Validate configuration
python scripts/autotrain.py --dry-run

# Check GPU availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Monitor GPU usage
watch -n 1 nvidia-smi

# Check disk space
df -h | grep /workspaces


# ==============================================================================
# 13. VS CODE INTEGRATION
# ==============================================================================

# In VS Code, press Ctrl+Shift+P and search for:
# - Tasks: Run Task → GGUF: Quick Training
# - Tasks: Run Task → GGUF: Full Pipeline
# - Tasks: Run Task → GGUF: Dry-Run
# - Tasks: Run Task → GGUF: Convert Existing Model
# - Tasks: Run Task → GGUF: Validate Model


# ==============================================================================
# 📚 DOCUMENTATION
# ==============================================================================

# Read the quick start guide
cat GGUF_AUTOMATION_QUICKSTART.md

# Read the integration guide
cat GGUF_TRAINING_INTEGRATION_GUIDE.md

# Read setup complete summary
cat GGUF_TRAINING_SETUP_COMPLETE.md

# View script help
python scripts/gguf_training_automation.py --help


# ==============================================================================
# 🚀 RECOMMENDED WORKFLOW
# ==============================================================================

# 1. Start with dry-run to understand the process
python scripts/gguf_training_automation.py --quick --dry-run

# 2. Run quick training to test
python scripts/gguf_training_automation.py --quick

# 3. Check results
cat data_out/gguf_training/summary.json

# 4. Use the model
python talk-to-ai/src/chat_cli.py \
  --provider lora \
  --adapter-path deployed_models/phi35_quick_gguf-latest.gguf \
  --once "test"

# 5. Set up daily automation (optional)
echo "0 2 * * * cd /workspaces/AI && python scripts/gguf_training_automation.py --quick" | crontab -
