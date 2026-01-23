# 📖 Aria Documentation Index

**Complete Setup Delivered** | January 23, 2026

---

## 🎯 Choose Your Path

### 👤 I'm New to Aria
Start here → **[START_HERE.md](START_HERE.md)** (2-minute overview)

### 🚀 I Want to Start Everything Right Now
Copy-paste this:
```bash
bash /workspaces/AI/scripts/start_aria_full.sh
```
Then open: **http://localhost:8080**

### 📋 I Need Step-by-Step Setup Instructions
Read → **[ARIA_SETUP_GUIDE.md](ARIA_SETUP_GUIDE.md)** (detailed, all components)

### 📚 I Want Quick Reference Commands
Check → **[ARIA_QUICK_REFERENCE.md](ARIA_QUICK_REFERENCE.md)** (copy-paste cards)

### 🔍 I Need Comprehensive Deployment Details
See → **[ARIA_DEPLOYMENT_READY.md](ARIA_DEPLOYMENT_READY.md)** (full deployment guide)

### 📊 I Want the Complete System Overview
View → **[ARIA_COMPLETE_SETUP_SUMMARY.md](ARIA_COMPLETE_SETUP_SUMMARY.md)** (full summary)

### 🐛 I Need to Diagnose Issues
Run → **`python /workspaces/AI/scripts/aria_diagnostic.py`**

---

## 📂 File Organization

### 📄 Documentation Files
- `START_HERE.md` — Quick start (2 min)
- `ARIA_SETUP_GUIDE.md` — Complete setup (detailed)
- `ARIA_QUICK_REFERENCE.md` — Command reference (copy-paste)
- `ARIA_DEPLOYMENT_READY.md` — Deployment guide (comprehensive)
- `ARIA_COMPLETE_SETUP_SUMMARY.md` — System overview (full)
- `ARIA_DOCUMENTATION_INDEX.md` — This file

### 🔧 Tools & Scripts
- `scripts/aria_diagnostic.py` — Full system diagnostic
- `scripts/start_aria_full.sh` — One-command startup

### ⚙️ Configuration Files
- `local.settings.json` — Chat provider configuration
- `config/autonomous_training.yaml` — Training orchestrator
- `quantum_autorun.yaml` — Quantum jobs
- `config/master_orchestrator.yaml` — Master coordination

### 📦 Core Components
- `aria_web/server.py` — Web interface (port 8080)
- `function_app.py` — Azure Functions API (port 7071)
- `talk-to-ai/src/chat_cli.py` — Chat CLI
- `quantum-ai/quantum_mcp_server.py` — Quantum ML server
- `scripts/training/autonomous_training_orchestrator.py` — Training orchestrator
- `scripts/monitoring/auto_ops_dashboard.py` — Monitoring dashboard

---

## 🚀 Quick Start Commands

### Start Everything
```bash
bash /workspaces/AI/scripts/start_aria_full.sh
```

### Start Individual Components
```bash
# Aria Web UI
cd /workspaces/AI/aria_web && python server.py

# Azure Functions
cd /workspaces/AI && func host start

# Autonomous Training
python /workspaces/AI/scripts/training/autonomous_training_orchestrator.py

# Quantum MCP Server
python /workspaces/AI/quantum-ai/quantum_mcp_server.py

# Monitoring Dashboard
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --watch
```

### Test Components
```bash
# Test chat
python /workspaces/AI/talk-to-ai/src/chat_cli.py --provider local --once "Hello"

# Test web API
curl http://localhost:8080/api/aria/state

# Test functions
curl http://localhost:7071/api/ai/status | jq .

# Full diagnostic
python /workspaces/AI/scripts/aria_diagnostic.py
```

---

## 🌐 Web Interfaces

| URL | Purpose |
|-----|---------|
| http://localhost:8080 | Aria Character UI (3D avatar) |
| http://localhost:8080/auto-execute.html | Auto-Execute Planner |
| http://localhost:8080/quantum-world.html | Quantum World Visualization |
| http://localhost:7071/api/ai/status | Functions Health Check |

---

## 📚 Architecture Overview

```
Aria Web (8080) ↔ Multi-Provider Chat ↔ Azure Functions (7071)
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
    Training         Quantum ML      Monitoring
  (30-min cycles)    (MCP Server)    (Dashboard)
```

---

## 💬 Example Aria Commands

Once running at http://localhost:8080:

```
move left
move right
wave
dance
jump
say hello
pickup ball
throw
look around
```

---

## ⚙️ Configuration Options

### Chat Provider Setup
Edit `/workspaces/AI/local.settings.json`:
- **Local Echo** — Already working, zero config
- **Azure OpenAI** — Add 4 env vars (AZURE_OPENAI_*)
- **OpenAI** — Add 1 env var (OPENAI_API_KEY)
- **LMStudio** — Set LMSTUDIO_BASE_URL

### GPU Training (Optional)
Edit `/workspaces/AI/config/autonomous_training.yaml`:
```yaml
training:
  device: cuda              # Enable GPU
  max_gpu_memory_gb: 0      # Use all available
```

---

## 🐛 Troubleshooting Quick Guide

| Issue | Check | Fix |
|-------|-------|-----|
| Port 8080 in use | `lsof -i :8080` | `pkill -f aria_web` |
| Port 7071 in use | `lsof -i :7071` | `pkill -f "func host"` |
| Chat shows "local" only | `curl http://localhost:7071/api/ai/status \| jq .provider` | Configure env vars |
| Training not starting | Check log: `tail -f data_out/autonomous_training.log` | Verify YAML config |
| GPU not detected | `python -c "import torch; print(torch.cuda.is_available())"` | Install CUDA |

See **[ARIA_QUICK_REFERENCE.md](ARIA_QUICK_REFERENCE.md)** Card 7 for full troubleshooting guide.

---

## 📊 Monitoring

### Live Dashboard
```bash
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --watch
```

### View Logs
```bash
# Training logs
tail -f /workspaces/AI/data_out/autonomous_training.log

# Training status (JSON)
watch -n 5 'cat /workspaces/AI/data_out/autonomous_training_status.json | python -m json.tool'
```

### Control Training
```bash
# Trigger immediate cycle
pkill -USR1 -f autonomous_training

# Graceful shutdown
pkill -f 'aria_web\|func host\|autonomous_training'
```

---

## ✅ System Status

### All Systems Verified
- ✅ Python 3.14.0 ready
- ✅ All projects present
- ✅ Dependencies installed
- ✅ Chat provider working
- ✅ All ports available
- ✅ Configurations ready
- ✅ Documentation complete
- ✅ Tools tested

Run full diagnostic:
```bash
python /workspaces/AI/scripts/aria_diagnostic.py
```

---

## 📞 Support Resources

### Inside This Repository
- `.github/copilot-instructions.md` — Architecture & patterns
- `.github/instructions/` — Component-specific guidance
- `README.md` — Project overview

### Documentation Files
All detailed in this index. Start with appropriate file for your path.

### Built-in Diagnostic Tool
```bash
python /workspaces/AI/scripts/aria_diagnostic.py
```
Provides full system verification with next steps.

---

## 🎯 Next Steps

1. **Read** → [START_HERE.md](START_HERE.md) (2 minutes)
2. **Choose** → Pick your starting option:
   - Run everything: `bash /workspaces/AI/scripts/start_aria_full.sh`
   - Test first: `python /workspaces/AI/scripts/aria_diagnostic.py`
   - Learn setup: Read [ARIA_SETUP_GUIDE.md](ARIA_SETUP_GUIDE.md)
3. **Open** → http://localhost:8080 (when running)
4. **Monitor** → `python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --watch`

---

## 🎉 Summary

You have a **complete, production-ready Aria system** with:

✅ Interactive 3D web interface  
✅ Multi-provider chat (4 backends)  
✅ Autonomous continuous training  
✅ Quantum ML integration  
✅ Real-time monitoring  
✅ Comprehensive documentation  

**Ready to deploy!** Choose your path above and begin. 🚀

---

*Generated: January 23, 2026 | System: Python 3.14.0 | Status: ✅ Verified & Ready*
