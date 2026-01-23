# VS Code Auto Operations - Quick Reference Card

**Keep this handy while monitoring**

---

## ⚡ KEYBOARD SHORTCUTS

```
Ctrl+Alt+A   START ALL MONITORING (Dashboard + Alerts + CLI)
Ctrl+Alt+D   Start Dashboard Server Only
Ctrl+Alt+S   Show CLI Dashboard (full view)
Ctrl+Alt+W   Show CLI Dashboard (watch mode)
Ctrl+Alt+P   Show CLI Dashboard (problems only)
```

---

## 🌐 DASHBOARD

**URL**: `http://localhost:8765`

**Controls**:
- `[PAUSE]` — Stop auto-refresh
- `[RESUME]` — Resume auto-refresh
- `[REFRESH]` — Update now
- Scroll down — See more operations
- Status badge — Shows "Live" or "Paused"

**Interpretation**:
- 🟢 Green = Running
- ⚪ Gray = Idle
- ✅ Checkmark = Success
- ❌ Red X = Error
- 📊 Progress bar = % complete

---

## 🔔 ALERTS

**Shown in**: Output panel (Ctrl+Shift+U)

**Alert types**:
- 🔴 CPU >95% (CRITICAL)
- 🔴 Memory >85% (CRITICAL)
- 🔴 Disk >85% (CRITICAL)
- 🔴 Job failed (ERROR)
- ⚠️ Accuracy down (WARNING)

**Cooldown**: 5 minutes between same alerts (prevents spam)

---

## 📊 OPERATIONS (10 Total)

| Name | Type | Status File |
|------|------|------------|
| **Autonomous Training** | Learning | `autonomous_training_status.json` |
| **AutoTrain** | Learning | `autotrain/status.json` |
| **GGUF Training** | Learning | `gguf_training/training_status.json` |
| **Quantum AutoRun** | Evaluation | `quantum_autorun/status.json` |
| **Evaluation AutoRun** | Evaluation | `evaluation_autorun/status.json` |
| **Master Orchestrator** | Scheduling | `master_orchestrator/status.json` |
| **Training Scheduler** | Scheduling | `training_scheduler/scheduler_state.json` |
| **Auto Scheduler** | Scheduling | `auto_scheduler/schedule.json` |
| **Train & Promote** | Deployment | `train_and_promote/pipeline_*.json` |
| **CI Pipeline** | CI/CD | `ci_orchestrator/ci_results.json` |

---

## 🎯 COMMON TASKS

### I want to...

**See everything at once**
```
Ctrl+Alt+A
Then: http://localhost:8765
```

**Check for problems**
```
Ctrl+Alt+P
```

**Monitor in real-time**
```
Ctrl+Alt+W
```

**Get detailed status**
```
Ctrl+Alt+S
```

**Share with team**
```
Share URL: http://localhost:8765
```

**Check one operation**
```
Ctrl+Alt+S
Find operation name
See full details
```

---

## 📈 DASHBOARD METRICS

**Per Operation**:
- **Status**: running | idle | success | error
- **Progress**: 0-100%
- **Metrics**: accuracy, F1, cycles, job counts
- **Duration**: time elapsed
- **Last Update**: timestamp
- **Alerts**: any issues

**Summary at Top**:
- Running: Count of active jobs
- Success: Count of completed jobs
- Failed: Count of failed jobs
- Alerts: Count of detected issues

---

## 🚀 QUICK START

**Step 1**: Press `Ctrl+Alt+A` (takes 2 seconds)

**Step 2**: Open `http://localhost:8765` (in browser)

**Step 3**: Watch operations run in real-time

**That's it!** ✅

---

## 🛠️ TROUBLESHOOTING

**Dashboard won't load**
```
1. Check: Is server running?
   ps aux | grep vs_code_server
2. Try: Restart - Ctrl+Alt+D
3. Check port: curl http://localhost:8765
```

**Alerts not showing**
```
1. Check: Output panel (Ctrl+Shift+U)
2. Try: Ctrl+Alt+P (problems)
3. Restart: Stop all, then Ctrl+Alt+A
```

**Port 8765 in use**
```
1. Edit: scripts/monitoring/vs_code_server.py
2. Change: port = 8765 → 8766
3. Restart: Ctrl+Alt+D
4. New URL: http://localhost:8766
```

**Tasks don't show**
```
Ctrl+Shift+P → Developer: Reload Window
Then: Ctrl+Shift+P → Tasks: Run Task
```

---

## 📋 RESPONSE GUIDE

**When you see**... | **Check**... | **Do**...
---|---|---
🔴 High CPU | Dashboard | Reduce batch size or pause training
🔴 High Memory | Dashboard | Stop other processes
🔴 Disk Full | Dashboard | Clean up old models
❌ Job Failed | Ctrl+Alt+P | Check logs, restart job
⚠️ Accuracy Down | Dashboard | Review training metrics
🟢 Running | Nothing | Keep monitoring

---

## 💾 USEFUL COMMANDS

```bash
# Full dashboard
python scripts/monitoring/auto_ops_dashboard.py

# Watch mode (auto-refresh)
python scripts/monitoring/auto_ops_dashboard.py --watch

# Problems only
python scripts/monitoring/auto_ops_dashboard.py --problems

# Compact view
python scripts/monitoring/auto_ops_dashboard.py --compact

# Export JSON
python scripts/monitoring/auto_ops_dashboard.py --json

# Interactive setup
python scripts/monitoring/vscode_quickstart.py

# Verify installation
python scripts/monitoring/verify_setup.py

# Help
python scripts/monitoring/vscode_quickstart.py --help-long
```

---

## ✅ DAILY ROUTINE

**Morning**:
1. `Ctrl+Alt+A` (start all)
2. `Ctrl+Alt+D` (open dashboard)
3. Check: Any overnight issues?
4. Keep dashboard visible

**During Work**:
1. Watch dashboard
2. React to alerts
3. Monitor progress

**End of Day**:
1. `Ctrl+Alt+S` (check final status)
2. Note any issues
3. Stop monitoring (if desired)

---

## 📚 DOCUMENTATION

Quick Reference: **This card**

Getting Started: `docs/GETTING_STARTED_VSCODE.md`

Complete Guide: `docs/VSCODE_INTEGRATION.md`

All Features: `docs/AUTO_OPS_MONITORING_SUITE.md`

---

## 🎯 KEY TAKEAWAYS

✅ Press `Ctrl+Alt+A` to start everything
✅ Open `http://localhost:8765` for dashboard
✅ Use `Ctrl+Alt+P` to check for problems
✅ Alerts appear in Output panel automatically
✅ Keep dashboard visible while working
✅ Respond to 🔴 CRITICAL alerts immediately

---

## 📞 HELP

**Interactive Help**:
```bash
python scripts/monitoring/vscode_quickstart.py --help-long
```

**Verify Setup**:
```bash
python scripts/monitoring/verify_setup.py
```

**Quick Status**:
```bash
python scripts/monitoring/auto_ops_dashboard.py
```

---

**Remember**: `Ctrl+Alt+A` starts everything! 🚀

Print this card and keep it near your desk for quick reference.

Last Updated: January 19, 2026
