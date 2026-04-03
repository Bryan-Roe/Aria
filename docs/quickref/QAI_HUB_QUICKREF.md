# QAI Hub - Quick Reference Card

## 🚀 One-Liners

### Start Hub Server
```powershell
python .\dashboard\serve.py
```
**Hub**: http://localhost:8000/
**Training Dashboard**: http://localhost:8000/unified.html

---

## 📍 Navigation Map

```
http://localhost:8000/
│
├─ / (root) → AUTO REDIRECTS TO → /hub.html ✨
│
├─ /hub.html (Command Center)
│  ├─ Stats Bar: Jobs, Datasets, Models, GPU Usage
│  ├─ Quick Actions: 6 one-click shortcuts
│  └─ System Cards: 8 major systems
│
├─ /unified.html (Training Dashboard)
│  ├─ All Jobs: Live tracking
│  ├─ Models: Leaderboard
│  ├─ Datasets: Browse & validate
│  ├─ Configs: YAML management
│  ├─ Train: 20+ parameters + presets
│  └─ Monitor: GPU real-time
│
└─ API Endpoints (18 total)
   ├─ /status
   ├─ /api/datasets
   ├─ /api/models
   ├─ /api/configs
   ├─ /api/gpu
   ├─ /api/health
   ├─ /api/stats
   └─ ... (see full list below)
```

---

## ⚡ 30-Second Workflows

### 1. Start Training Job
1. Open http://localhost:8000/ → Click "Training Dashboard"
2. Click "Train" tab
3. Fill job name + select dataset
4. Click "Start Training"

**Or use preset**:
1. Click "Quick Test" preset (1 epoch, 100 samples, ~2 min)
2. Click "Start Training"

### 2. Check System Health
```powershell
curl http://localhost:8000/api/health | ConvertFrom-Json
```

### 3. View All Training Jobs
```powershell
curl http://localhost:8000/status | ConvertFrom-Json
```

### 4. Monitor GPU Usage
```powershell
curl http://localhost:8000/api/gpu | ConvertFrom-Json
```

### 5. List Datasets
```powershell
curl http://localhost:8000/api/datasets | ConvertFrom-Json
```

---

## 🎯 Quick Actions (From Hub)

| Icon | Action | Target |
|------|--------|--------|
| 🚀 | Start Training | `/unified.html#train` |
| 📊 | View Datasets | `/unified.html#datasets` |
| 🤖 | Browse Models | `/unified.html#models` |
| 📈 | Monitor GPU | `/unified.html#monitor` |
| ⚛️ | Quantum Jobs | CLI toast message |
| 💬 | Chat Interface | CLI toast message |

---

## 📡 API Endpoints Reference

### Training & Jobs
```http
GET  /status                  # Training job status
POST /api/start-training      # Create new job
GET  /api/history             # Historical data
```

### Datasets & Models
```http
GET /api/datasets             # All datasets + sample counts
GET /api/models               # Trained models
GET /api/configs              # YAML configs
```

### System Monitoring
```http
GET /api/gpu                  # GPU utilization
GET /api/gpu-processes        # GPU process list
GET /api/system               # CPU, RAM, disk
GET /api/processes            # Active Python processes
```

### Health & Stats
```http
GET /api/health               # System health check
GET /api/stats                # Quick summary
```

### Job Details
```http
GET /api/job/:name            # Specific job details
GET /api/logs/:name           # Training logs
```

---

## 🎨 Training Presets

| Preset | Epochs | Samples | Rank | Time | Use Case |
|--------|--------|---------|------|------|----------|
| **Quick Test** | 1 | 100 | 4 | ~2 min | Fast validation |
| **Standard** | 3 | 1,000 | 8 | ~10 min | Good baseline |
| **Full** | 5 | All | 16 | ~60 min | Production quality |
| **Production** | 10 | All | 32 | ~4 hours | Maximum quality |

---

## 🔧 Advanced Training Parameters

### Basic (Always Visible)
- **Job Name**: Unique identifier (lowercase, underscores)
- **Model**: phi35 or qwen25
- **Dataset**: From datasets/chat/*
- **Epochs**: 1-20 (default: 3)
- **Max Samples**: 10-N or -1 for all (default: 1000)
- **Learning Rate**: 1e-5 to 5e-4 (default: 2e-4)

### Advanced (Collapsible)
- **Batch Size**: 1/2/4/8 (default: 2)
- **Gradient Accumulation**: 1-32 (default: 1)
- **Warmup Steps**: 0-N (default: 0)
- **LoRA Rank**: 4-128 (default: 8)
- **LoRA Alpha**: 8-256 (default: 16)
- **LoRA Dropout**: 0.0-0.5 (default: 0.1)
- **Weight Decay**: 0.0-0.5 (default: 0.01)
- **Max Grad Norm**: 0-10 (default: 1.0)
- **Random Seed**: Any integer (default: 42)

### Evaluation
- **Enable Eval**: Checkbox (default: checked)
- **Max Eval Samples**: 10-N (default: 100)
- **Eval Steps**: 10-N (default: 50)

**Total**: 17 configurable parameters

---

## 🌟 System Cards Overview

| System | Icon | Description | Link |
|--------|------|-------------|------|
| **Training Dashboard** | 🎯 | LoRA fine-tuning interface | `/unified.html` |
| **Quantum ML** | ⚛️ | Hybrid quantum-classical | CLI |
| **Chat Interface** | 💬 | Multi-provider chat | CLI |
| **Evaluation Suite** | 📊 | Model assessment | CLI |
| **Dataset Manager** | 🗃️ | Browse & validate | `/unified.html#datasets` |
| **API Gateway** | 🔌 | Azure Functions API | Port 7071 |
| **Resource Monitor** | 📈 | GPU/CPU/RAM tracking | CLI |
| **CI/CD Pipeline** | 🔄 | Testing & deployment | CLI |

---

## 🐛 Quick Troubleshooting

### Hub Not Loading
```powershell
# Check server
Get-Process python | Where-Object {$_.CommandLine -like "*serve.py*"}

# Restart
python .\dashboard\serve.py
```

### Stats Showing "--"
```powershell
# Generate status.json
python .\scripts\autotrain.py --dry-run
```

### API 404 Errors
```powershell
# Verify server is running
curl http://localhost:8000/api/health
```

### GPU Not Detected
```powershell
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 📊 Keyboard Shortcuts (In Hub)

| Key | Action |
|-----|--------|
| **Click Card** | Navigate to system |
| **Click Action** | Execute quick action |
| **F5** | Refresh page (auto-updates stats) |
| **Ctrl+Click** | Open in new tab |

---

## 🎓 Learning Path

### Beginner (Day 1)
1. Start hub server
2. Explore Quick Actions
3. Run "Quick Test" preset
4. View job in "All Jobs" tab

### Intermediate (Week 1)
1. Adjust basic parameters (epochs, samples)
2. Try different presets
3. Save/load configurations
4. Monitor GPU usage

### Advanced (Month 1)
1. Tune advanced parameters
2. Run batch evaluations
3. Use API endpoints
4. Integrate with CI/CD

### Expert (Ongoing)
1. Quantum ML pipeline
2. Custom provider backends
3. Distributed training
4. Production deployment

---

## 📚 Related Documentation

| File | Description |
|------|-------------|
| `QAI_HUB_GUIDE.md` | Full hub documentation (this file's parent) |
| `TRAINING_TAB_ENHANCEMENTS.md` | Training features (450 lines) |
| `TRAINING_TAB_QUICKREF.md` | Training quick reference (350 lines) |
| `DASHBOARD_DEMO.md` | Live demo script |
| `AUTOTRAIN_README.md` | LoRA orchestration |
| `QUANTUM_AUTORUN_README.md` | Quantum jobs |

---

## 💡 Pro Tips

1. **Bookmark the Hub**: http://localhost:8000/ (not unified.html)
2. **Use Presets First**: Validate before custom tuning
3. **Save Configs**: Export JSON for reproducibility
4. **Monitor GPU**: Avoid over-allocation (max 6.1GB VRAM)
5. **Dry-Run Always**: Test orchestrators before real runs
6. **Check Status First**: `curl /api/stats` before starting new jobs
7. **Use Quick Actions**: Faster than navigating cards
8. **Read Tooltips**: Hover over labels for parameter explanations

---

## 🔗 External Resources

- **PennyLane Docs**: https://pennylane.ai/
- **Azure Quantum**: https://quantum.microsoft.com/
- **Hugging Face**: https://huggingface.co/
- **PyTorch**: https://pytorch.org/
- **Azure Functions**: https://docs.microsoft.com/azure/azure-functions/

---

## 📞 Quick Support

### Server Issues
```powershell
# Check logs
Get-Content .\dashboard\serve.py.log -Tail 50
```

### Training Stuck
```powershell
# Check running jobs
python .\scripts\master_orchestrator.py --status
```

### Database Issues
```powershell
# Check SQL connection
curl http://localhost:7071/api/ai/status | ConvertFrom-Json
```

---

**Cheat Sheet Version**: 1.0
**Last Updated**: 2025-11-25
**Print-Friendly**: Yes (A4/Letter)

---

## 🎯 Most Common Commands

```powershell
# Start everything
python .\dashboard\serve.py                          # Hub server
func host start                                      # API gateway

# Training
python .\scripts\autotrain.py --dry-run             # Validate
python .\scripts\autotrain.py                        # Run all jobs

# Quantum
python .\scripts\quantum_autorun.py --dry-run       # Validate
python .\scripts\quantum_autorun.py --job local     # Run local

# Chat
python .\talk-to-ai\src\chat_cli.py --provider azure

# Testing
pytest tests/ -m "not slow and not azure"            # Fast tests
python .\scripts\test_runner.py --all               # All tests

# Monitoring
curl http://localhost:8000/api/stats | ConvertFrom-Json
python .\scripts\resource_monitor.py --snapshot

# Status
python .\scripts\master_orchestrator.py --status    # All systems
curl http://localhost:8000/api/health              # Hub health
```

---

**Quick Access**: Pin this file for instant reference! 📌
