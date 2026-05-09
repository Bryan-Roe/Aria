# Training Tab - Quick Reference Card

## 🚀 Quick Start (30 seconds)

### For Testing Pipeline
```
1. Open: http://localhost:8000/unified.html
2. Click "Train" tab
3. Enter job name: test_run_001
4. Select dataset from dropdown
5. Click "⚡ Quick Test" preset button
6. Click "🚀 Start Training"
```

### For Production Training
```
1. Open: http://localhost:8000/unified.html
2. Click "Train" tab
3. Enter descriptive job name: prod_chatbot_v2
4. Select dataset with >1k samples
5. Click "🚀 Production" preset button
6. Review estimates (time & VRAM)
7. Click "🚀 Start Training"
8. Switch to "Jobs" tab to monitor
```

## 📋 Quick Presets Comparison

| Preset | Epochs | Samples | LoRA Rank | Time | Use Case |
|--------|--------|---------|-----------|------|----------|
| ⚡ Quick Test | 1 | 100 | 4 | ~2 min | Pipeline testing |
| 📊 Standard | 3 | 1k | 8 | ~10 min | Iterative dev |
| 🏆 Full | 5 | All | 16 | ~60 min | Thorough training |
| 🚀 Production | 10 | All | 32 | ~4 hours | Production quality |

## 🎯 Common Workflows

### Experiment Workflow
```
1. Load dataset → 2. Quick preset → 3. Train → 4. Evaluate
   ↓
5. Adjust params → 6. Save config → 7. Retrain → 8. Compare
```

### Production Workflow
```
1. Select best dataset → 2. Production preset → 3. Tweak advanced
   ↓
4. Save config → 5. Train → 6. Evaluate → 7. Deploy
```

### Hyperparameter Tuning
```
1. Standard preset → 2. Save as baseline.json
   ↓
3. Toggle "Advanced Options" → 4. Modify LoRA rank
   ↓
5. Save as variant_rank16.json → 6. Train → 7. Compare results
```

## ⚙️ Advanced Options Explained

### When to Adjust

**Batch Size** ↑
- More GPU memory available
- Want faster training
- Dataset is large (>10k samples)

**LoRA Rank** ↑
- Model underfitting
- Complex task (reasoning, multilingual)
- Have extra training time

**Learning Rate** ↓
- Training unstable (loss spikes)
- Fine-tuning pre-trained adapter
- Small dataset (<500 samples)

**Gradient Accumulation** ↑
- Batch size limited by memory
- Want larger effective batch
- Training is too noisy

**Weight Decay** ↑
- Model overfitting
- Training loss << eval loss
- Dataset has duplicates

## 🔍 Validation Rules

### Job Name
- ✅ `my_test_job`, `prod_v2`, `exp_rank_16`
- ❌ `My Test`, `prod-v2`, `exp rank 16`
- Rule: lowercase, numbers, underscores only

### Epochs
- Range: 1-20
- Recommended: 3-5 for most tasks
- Warning: >10 shows confirmation dialog

### Max Samples
- Min: 10 (or -1 for all)
- Recommended: Start with 1000, scale up
- -1 = Use entire dataset

## 💾 Config Management

### Save Config
```
Purpose: Backup successful configs
Format: JSON file with all parameters
Usage: Share with team, version control
Location: Downloads folder
```

### Load Config
```
Purpose: Restore previous settings
Format: .json files exported via "Save"
Usage: Reproduce results, iterate on proven configs
Action: Opens file picker
```

## 📊 Estimates Explained

### Time Estimate
```
Based on:
- Training samples
- Batch size
- Number of epochs
- ~0.5 seconds per step estimate

Example:
1000 samples, batch 2, 3 epochs
= (1000/2) × 3 × 0.5s = ~12 minutes
```

### VRAM Estimate
```
Based on:
- Base model size (~3.5 GB)
- LoRA rank (additional 0.5 GB per 8 rank)

Example:
LoRA rank 16
= 3.5 + (16/8 × 0.5) = ~4.5 GB
```

## ⌨️ Keyboard Shortcuts

| Key | Action | Tab |
|-----|--------|-----|
| `6` | Switch to Train tab | Any |
| `r` | Refresh data | Any |
| `a` | Toggle auto-refresh | Any |
| `d` | Toggle dark mode | Any |

## 🐛 Troubleshooting

### Dataset dropdown empty
- **Check**: Datasets tab loads correctly
- **Fix**: Verify `datasets/chat/` folder has subfolders with train.json/test.json

### "Failed to start training" error
- **Check**: Job name follows rules (lowercase, underscores)
- **Fix**: Review validation messages, correct highlighted fields

### Estimates seem wrong
- **Cause**: First-time estimate uses defaults
- **Fix**: Adjust one parameter (epochs) to recalculate

### Advanced options won't expand
- **Check**: Click the "🔧 Advanced Options" header
- **Visual**: Arrow icon changes ▼ → ▲

### Config load doesn't populate fields
- **Check**: File is valid JSON
- **Fix**: Use files exported via "Save Config" button

## 📈 Performance Tips

### Faster Training
1. ↑ Batch size (if memory allows)
2. ↓ Max samples (use subset for testing)
3. ↓ LoRA rank (use 4-8 for quick runs)

### Better Quality
1. ↑ Epochs (5-10 typical)
2. ↑ LoRA rank (16-32 for complex tasks)
3. ↑ Max samples (use full dataset)
4. Enable evaluation (catch overfitting early)

### Memory Optimization
1. ↓ Batch size to 1
2. ↑ Gradient accumulation (simulate larger batch)
3. ↓ LoRA rank to minimum (4)

## 🎓 Learning Path

### Beginner (Day 1)
1. Use Quick Test preset
2. Observe job progress in Jobs tab
3. Try Standard preset with different datasets

### Intermediate (Week 1)
1. Open Advanced Options
2. Experiment with LoRA rank (8 → 16)
3. Compare results, save successful configs

### Advanced (Month 1)
1. Custom parameter combinations
2. Hyperparameter sweeps (save multiple configs)
3. Production deployments with optimized settings

## 📚 Related Documentation

- **Full Guide**: `TRAINING_TAB_ENHANCEMENTS.md`
- **Training Orchestration**: `AUTOTRAIN_README.md`
- **Dashboard Overview**: `DASHBOARD_ENHANCEMENTS.md`
- **Server Setup**: `DATABASE_INTEGRATION_GUIDE.md`

## 🎉 Feature Highlights

✨ **20+ New Features**
- Advanced options (collapsible)
- Real-time estimates
- 4 quick presets
- Config save/load
- Enhanced validation

🚀 **Production Ready**
- Comprehensive error handling
- Smart defaults
- Professional UX
- Team-friendly config sharing

🎯 **User-Centric**
- Tooltips on every field
- Clear validation messages
- Dynamic feedback
- Beginner to expert support

---

**Quick Access**: http://localhost:8000/unified.html → Train Tab

**Help**: Hover over any field for tooltip guidance

**Status**: ✅ All systems operational

*Last Updated: November 25, 2025*
