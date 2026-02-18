# 🚀 Auto Operations Monitoring Suite

**Complete real-time visibility for all your Aria AI operations** — directly in VS Code.

## ✨ What You Get

### 📊 Real-Time Dashboard
- **Live metrics** for all 10+ orchestrators
- **Auto-refresh** every 5 seconds (or pause when needed)
- **Visual status indicators** (🟢 running, ⚪ idle, ✅ success, ❌ error)
- **Alert display** showing problems immediately
- **Progress tracking** for running operations
- **Categorized operations** (Learning, Evaluation, Scheduling, etc.)

### 🔔 Intelligent Alert System
Watches for and alerts on:
- 🔴 **Critical**: CPU >95%, Memory >85%, Disk >85%
- 🔴 **Errors**: Failed jobs, validation failures, deployment issues
- ⚠️ **Warnings**: Accuracy decline, deployment issues
- **Smart cooldown**: 5-minute delay prevents alert spam

### ⌨️ One-Command Launch
```bash
# Interactive menu
python scripts/monitoring/vscode_quickstart.py

# Or use keyboard shortcut
Ctrl+Alt+A          # Start full suite
Ctrl+Alt+D          # Dashboard only
Ctrl+Alt+S          # CLI dashboard
Ctrl+Alt+W          # CLI watch mode
Ctrl+Alt+P          # Problems only
```

### 🎯 Perfect For
- **Continuous monitoring** while developing
- **Rapid issue detection** (problems appear in <5 seconds)
- **Operation orchestration** (see all systems at a glance)
- **Team collaboration** (shared dashboard view)
- **Performance tracking** (metrics and trends)

---

## 🚀 Quick Start (2 Steps)

### Step 1: Start Monitoring
Press `Ctrl+Shift+P` → Run `"Monitor: Quick Setup (Interactive Menu)"`

Or:
```bash
python scripts/monitoring/vscode_quickstart.py --full
```

### Step 2: Open Dashboard
Press `Ctrl+Alt+D` or navigate to `http://localhost:8765`

That's it! You now have:
- ✅ **Real-time dashboard** at localhost:8765
- ✅ **Alert monitor** watching for problems
- ✅ **CLI dashboard** in terminal
- ✅ **Quick keyboard shortcuts** for control

---

## 📋 Usage Patterns

### Development Session
```
1. Open VS Code
2. Ctrl+Alt+A to start all monitoring
3. Keep dashboard open on left, code on right
4. Watch operations run in real-time
5. Alerts appear in terminal immediately
6. Click operation details to see more info
```

### Focused Monitoring
```
1. Ctrl+Alt+D to start dashboard only
2. Open http://localhost:8765 in browser
3. Use Pause/Resume controls as needed
4. Refresh dashboard manually if needed
```

### Problem Investigation
```
1. See alert in terminal
2. Open dashboard to see full context
3. Use Ctrl+Alt+P to show problems only (CLI)
4. Investigate specific failing operation
```

### Morning Check
```
1. Start VS Code
2. Ctrl+Alt+A to start monitoring
3. Ctrl+Alt+D to open dashboard
4. Review status at a glance
5. Check for overnight issues in alerts
```

---

## 🎮 Controls

### Dashboard Controls (in browser)
| Control | Action |
|---------|--------|
| **Pause/Resume Button** | Stop/resume auto-refresh |
| **Refresh Button** | Force immediate update |
| **Status Badge** | Shows "Live" or "Paused" |
| **Scroll Down** | See more operations & alerts |
| **Click Operation** | View detailed metrics *(coming soon)* |

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+Alt+A` | Start full monitoring suite |
| `Ctrl+Alt+D` | Start dashboard server |
| `Ctrl+Alt+S` | Show CLI dashboard |
| `Ctrl+Alt+W` | Watch mode (CLI auto-refresh) |
| `Ctrl+Alt+P` | Problems only (CLI) |
| `Ctrl+Shift+P` | VS Code command palette |

### Menu Options (Interactive)
```
1 - Start Full Suite (dashboard + alerts + CLI)
2 - Start Dashboard Only (web interface)
3 - Start Alert Monitor Only (background)
4 - Show CLI Dashboard (full view)
5 - Show CLI Dashboard (watch mode)
6 - Show CLI Dashboard (problems only)
7 - Show Help & Setup
Q - Quit
```

---

## 🔍 What It Monitors

### Operations Tracked
1. **Autonomous Training** — Continuous learning cycles
2. **AutoTrain** — Manual training orchestration
3. **GGUF Training** — Model conversion & training
4. **Quantum AutoRun** — Quantum job orchestration
5. **Evaluation AutoRun** — Model evaluation pipeline
6. **Master Orchestrator** — All-in-one controller
7. **Training Scheduler** — Nightly/scheduled training
8. **Auto Scheduler** — Automatic scheduling
9. **Train & Promote** — Training with auto-deployment
10. **CI Pipeline** — Continuous integration

### Metrics Displayed
- **Status**: Running, idle, success, error
- **Progress**: Percentage complete, cycles done
- **Metrics**: Accuracy, loss, F1 score, etc.
- **Timings**: Last update, duration, ETA
- **Resources**: CPU, memory, disk usage
- **Alerts**: Any issues detected

---

## 🌐 Components

### Dashboard Server
- **Runs on**: `http://localhost:8765`
- **Language**: Flask (Python)
- **Features**: Real-time updates, pause/resume, theme sync with VS Code
- **Performance**: ~50MB RAM, negligible CPU

### Alert Monitor
- **Checks**: Every 30 seconds
- **Alerts**: CPU, memory, disk, jobs, accuracy
- **Cooldown**: 5 minutes between same alerts
- **Output**: Terminal/output panel

### CLI Dashboard
- **Modes**: Full, compact, watch, problems, JSON
- **Refresh**: 5 seconds in watch mode
- **Output**: Formatted terminal output

### Quickstart Helper
- **Interactive**: Menu-driven setup
- **Auto-install**: Checks dependencies
- **Help**: Comprehensive guides & troubleshooting

---

## 📈 Performance

| Component | Memory | CPU | Network |
|-----------|--------|-----|---------|
| Dashboard Server | ~50MB | <1% | Minimal |
| Alert Monitor | ~30MB | <1% | None |
| CLI Dashboard | ~30MB | <2% | None |
| All Running | ~110MB | <2% | Minimal |

No database required — all data from status JSON files.

---

## 🐛 Troubleshooting

### Dashboard won't load
**Symptom**: `http://localhost:8765` doesn't load
```bash
# Check if server is running
ps aux | grep vs_code_server

# Try manually starting
python scripts/monitoring/vs_code_server.py

# Check if port is free
netstat -tlnp | grep 8765

# If port taken, edit vs_code_server.py and change port
```

### Alerts not showing
**Symptom**: No alerts appearing even when operations fail
```bash
# Check if alert monitor is running
ps aux | grep vs_code_alert_monitor

# View output panel manually
python scripts/monitoring/auto_ops_dashboard.py --problems

# Try manual check
python scripts/monitoring/vs_code_quickstart.py --alerts
```

### Port already in use
**Symptom**: `Address already in use` error
```python
# Edit vs_code_server.py:
def main():
    port = 8766  # Change to different port
```

### Tasks not showing
**Symptom**: Monitor tasks don't appear in `Ctrl+Shift+P`
```bash
# Reload VS Code
Ctrl+Shift+P → "Developer: Reload Window"

# Verify tasks.json is valid JSON
python -m json.tool .vscode/tasks.json
```

---

## 📚 Documentation

- [VSCODE_INTEGRATION.md](VSCODE_INTEGRATION.md) — Complete integration guide
- [AUTO_OPS_VISIBILITY_INDEX.md](AUTO_OPS_VISIBILITY_INDEX.md) — All features & commands
- [docs/AUTO_OPS_DASHBOARD.md](docs/AUTO_OPS_DASHBOARD.md) — CLI dashboard reference
- [docs/QUICK_START.md](docs/QUICK_START.md) — Quick start guide

---

## 🔧 Advanced Configuration

### Change refresh rate (dashboard)
Edit `scripts/monitoring/vs_code_server.py`:
```javascript
refreshInterval = setInterval(loadDashboard, 3000);  // 3 seconds
```

### Change alert cooldown
Edit `scripts/monitoring/vs_code_alert_monitor.py`:
```python
self.alert_cooldown = 60  # 1 minute cooldown
```

### Add custom alerts
In `vs_code_alert_monitor.py`, add to `check_and_alert()`:
```python
if my_condition:
    alerts.append({
        "severity": "warning",
        "title": "My Alert",
        "message": "Alert description"
    })
```

### Change dashboard port
Edit `scripts/monitoring/vs_code_server.py`:
```python
if __name__ == "__main__":
    main(port=8766)  # New port
```

---

## 💡 Tips & Tricks

### Keep Dashboard Always Visible
```
1. Split VS Code: View → Editor Layout → Two Columns
2. Left panel: Code editor
3. Right panel: Open http://localhost:8765 in Simple Browser
4. Now always see operations while coding
```

### Quick Problem Check
```
# Before committing code, check for issues:
Ctrl+Alt+P  # Show problems only
# Wait a few seconds to see any alerts
```

### Monitor Multiple Operations
```
# Left side: Dashboard
# Right side: Terminal with watch mode
Ctrl+Alt+W  # Start watch mode in new terminal
# See both real-time and detailed logs
```

### Export Status
```bash
# Export current status as JSON
python scripts/monitoring/auto_ops_dashboard.py --json

# Use in scripts, monitoring tools, etc.
curl http://localhost:7071/api/ai/status | jq
```

---

## 🚀 What's Next

**Coming Soon**:
- 📊 Historical trends & graphs
- 🎮 Interactive operation control (pause/resume from dashboard)
- 📧 Email notifications for alerts
- 🔗 Slack integration
- 🤖 Auto-remediation (restart failed jobs)
- 📱 Mobile dashboard
- 🔐 Authentication & multi-user access

---

## 🎓 Learning Resources

**New to this repo?** Start here:
1. Run: `python scripts/monitoring/vscode_quickstart.py --help-long`
2. Read: [Copilot Quick Guide](.github/copilot-instructions.md)
3. Try: Ctrl+Alt+A to start monitoring

**Want to dig deeper?**
- Check: [Architecture Overview](docs/ARCHITECTURE.md)
- Review: [Orchestrator Docs](docs/ORCHESTRATORS.md)
- Explore: [Config Files](config/)

---

## ⚡ One-Liners

```bash
# Start everything
Ctrl+Alt+A

# Start dashboard only
python scripts/monitoring/vscode_quickstart.py --server

# Show CLI dashboard (full)
python scripts/monitoring/vscode_quickstart.py --cli

# Show problems only
python scripts/monitoring/vscode_quickstart.py --problems

# Watch mode (auto-refresh)
python scripts/monitoring/vscode_quickstart.py --watch

# Get help
python scripts/monitoring/vscode_quickstart.py --help-long
```

---

**Status**: ✅ Fully Functional  
**Last Updated**: January 19, 2026  
**Version**: 1.0

Start monitoring now: `Ctrl+Alt+A`
