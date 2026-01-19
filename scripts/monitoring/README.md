# Auto Operations Monitoring Suite

**Real-time visibility for all Aria AI automated operations**

Located in: `scripts/monitoring/`

## 📋 Files in This Directory

### Core Tools

#### `auto_ops_dashboard.py` (620 lines)
**Main CLI dashboard with multiple view modes**

Usage:
```bash
python auto_ops_dashboard.py              # Full view
python auto_ops_dashboard.py --watch      # Auto-refresh
python auto_ops_dashboard.py --compact    # Minimal
python auto_ops_dashboard.py --problems   # Issues only
python auto_ops_dashboard.py --json       # Export JSON
```

Features:
- Aggregates 10 orchestrator status files
- Multiple output modes (full, compact, watch, problems, JSON)
- Alert detection (CPU, memory, disk, failures, degradation)
- Color-coded output (green = ok, red = critical)
- Real-time status from all operations
- Auto-refresh every 5 seconds in watch mode

Data sources: `data_out/*/status.json`

---

#### `vs_code_server.py` (360 lines)
**Flask web server providing real-time dashboard**

Usage:
```bash
python vs_code_server.py                  # Starts on localhost:8765
```

Features:
- Serves interactive HTML dashboard
- Real-time metrics from all operations
- Auto-refresh every 5 seconds (configurable)
- Pause/resume refresh controls
- Theme support (VS Code light/dark modes)
- Categorized operation display
- Alert section
- JSON API endpoint (`/api/status`)

Access: `http://localhost:8765`

---

#### `vs_code_alert_monitor.py` (115 lines)
**Background service monitoring for alerts**

Usage:
```bash
python vs_code_alert_monitor.py           # Runs in background
```

Features:
- Checks every 30 seconds
- Detects: High CPU >95%, memory >85%, disk >85%, failed jobs, accuracy decline
- 5-minute cooldown prevents alert spam
- Color-coded severity (critical, error, warning)
- Outputs to terminal (integrates with VS Code output panel)
- Graceful error handling

---

#### `vscode_quickstart.py` (370 lines)
**Interactive launcher and setup helper**

Usage:
```bash
python vscode_quickstart.py                # Interactive menu
python vscode_quickstart.py --server       # Start server only
python vscode_quickstart.py --alerts       # Start alerts only
python vscode_quickstart.py --cli          # Show CLI dashboard
python vscode_quickstart.py --full         # Start full suite
python vscode_quickstart.py --help-long    # Show detailed help
```

Features:
- Interactive menu with 7 options
- Auto-installs missing dependencies
- Comprehensive help system
- One-command startup
- Error handling and recovery

---

#### `verify_setup.py` (280 lines)
**Installation verification checklist**

Usage:
```bash
python verify_setup.py
```

Checks:
- Python version (3.7+)
- Flask & Flask-CORS installed
- All scripts present
- tasks.json valid
- Documentation complete
- Port 8765 available
- Status files exist

---

### Supporting Tools

#### `auto_ops_quick_ref.py`
**Quick reference helper (displays commands and usage)**

Usage:
```bash
python auto_ops_quick_ref.py
```

---

## 🚀 Quick Start

### Start All Monitoring (Recommended)
```bash
python vscode_quickstart.py --full
```

Or in VS Code:
```
Ctrl+Alt+A
```

### Start Dashboard Only
```bash
python vs_code_server.py
# Then open: http://localhost:8765
```

Or in VS Code:
```
Ctrl+Alt+D
```

### Show CLI Dashboard
```bash
python auto_ops_dashboard.py
```

Or in VS Code:
```
Ctrl+Alt+S  (full view)
Ctrl+Alt+W  (watch mode)
Ctrl+Alt+P  (problems only)
```

---

## 📊 What Gets Monitored

### 10 Automated Systems

**Learning (3)**:
- Autonomous Training
- AutoTrain
- GGUF Training

**Evaluation (2)**:
- Quantum AutoRun
- Evaluation AutoRun

**Scheduling (3)**:
- Master Orchestrator
- Training Scheduler
- Auto Scheduler

**Deployment (1)**:
- Train & Promote

**CI/CD (1)**:
- CI Pipeline

### Metrics Tracked Per Operation
- Status (running, idle, success, error)
- Progress (% complete)
- Cycles/iterations
- Accuracy/metrics
- Resource usage (CPU, memory, disk)
- Last update time
- Duration
- Alert status

---

## 🔧 Configuration

### Modify Dashboard Server Port

Edit `vs_code_server.py`:
```python
if __name__ == "__main__":
    app.run(host='localhost', port=8765)  # Change 8765 to desired port
```

### Modify Alert Check Interval

Edit `vs_code_alert_monitor.py`:
```python
check_interval = 30  # Change to desired seconds
```

### Modify Alert Cooldown

Edit `vs_code_alert_monitor.py`:
```python
self.alert_cooldown = 300  # 5 minutes, change to desired seconds
```

### Modify Dashboard Refresh Rate

Edit `vs_code_server.py` (in HTML template):
```javascript
refreshInterval = setInterval(loadDashboard, 5000);  // 5 seconds, change as needed
```

---

## 🔔 Alert Types

Monitored automatically every 30 seconds:

| Alert | Threshold | Severity |
|-------|-----------|----------|
| CPU Usage | >95% | CRITICAL 🔴 |
| Memory Usage | >85% | CRITICAL 🔴 |
| Disk Usage | >85% | CRITICAL 🔴 |
| Failed Jobs | status == "failed" | ERROR 🔴 |
| Accuracy Decline | current < previous * 0.95 | WARNING ⚠️ |

**Cooldown**: 5 minutes between duplicate alerts (prevents spam)

---

## 📈 Performance

| Component | Memory | CPU | Network |
|-----------|--------|-----|---------|
| Dashboard Server | ~50MB | <1% | Minimal |
| Alert Monitor | ~30MB | <1% | Minimal |
| CLI Dashboard | ~30MB | <2% | None |
| **All Running** | ~110MB | <2% | Minimal |

No database required — all data from status JSON files.

---

## 🐛 Troubleshooting

### Dashboard won't load

**Check if server is running**:
```bash
ps aux | grep vs_code_server
netstat -tlnp | grep 8765
```

**Try manually starting**:
```bash
python vs_code_server.py
```

**Check if port is free**:
```bash
# Try different port - edit vs_code_server.py
python vs_code_server.py  # Should show which port
```

### Alerts not appearing

**Check if monitor is running**:
```bash
ps aux | grep vs_code_alert_monitor
```

**Check output panel**:
```
VS Code: Ctrl+Shift+U (opens output panel)
Select: "Monitor" from dropdown
```

**Try manual check**:
```bash
python auto_ops_dashboard.py --problems
```

### Dependencies missing

**Install required packages**:
```bash
pip install flask flask-cors
```

**Verify installation**:
```bash
python verify_setup.py
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `docs/VSCODE_INTEGRATION.md` | Complete integration guide |
| `docs/AUTO_OPS_MONITORING_SUITE.md` | All monitoring features |
| `docs/GETTING_STARTED_VSCODE.md` | Getting started guide |
| `AUTO_OPS_VISIBILITY_INDEX.md` | Master index |
| `VSCODE_AUTO_OPS_COMPLETE_SETUP.md` | Complete setup guide |
| `VSCODE_QUICK_REFERENCE.md` | Quick reference card |

---

## 🎯 Common Workflows

### Monitor While Developing

```bash
# 1. Start everything
python vscode_quickstart.py --full

# 2. Split screen: Code | Dashboard
# Code on left, http://localhost:8765 on right

# 3. Watch operations in real-time while coding
# Alerts appear in output panel automatically
```

### Quick Problem Check

```bash
# Show only issues/alerts
python auto_ops_dashboard.py --problems

# Or CLI with Ctrl+Alt+P
```

### Share Dashboard with Team

```bash
# 1. Start monitoring
python vscode_quickstart.py --full

# 2. Share URL
http://localhost:8765

# 3. Team opens URL (no setup needed)
# 4. All see real-time dashboard
```

### Export for CI/CD

```bash
# Export current status as JSON
python auto_ops_dashboard.py --json

# Use in scripts/pipelines
curl http://localhost:7071/api/ai/status | jq
```

---

## ⚡ One-Liners

```bash
# Start everything
python vscode_quickstart.py --full

# Interactive menu
python vscode_quickstart.py

# Start server only
python vs_code_server.py

# Start alerts only
python vs_code_alert_monitor.py

# CLI full view
python auto_ops_dashboard.py

# CLI watch mode
python auto_ops_dashboard.py --watch

# CLI problems only
python auto_ops_dashboard.py --problems

# Verify setup
python verify_setup.py

# Show help
python vscode_quickstart.py --help-long
```

---

## 🚀 Getting Started

1. **Verify setup**:
   ```bash
   python verify_setup.py
   ```

2. **Install dependencies** (if needed):
   ```bash
   pip install flask flask-cors
   ```

3. **Start monitoring**:
   ```bash
   python vscode_quickstart.py --full
   ```

4. **Open dashboard**:
   ```
   http://localhost:8765
   ```

5. **Watch operations** run in real-time!

---

## 📞 Support

**Need help?**
```bash
python vscode_quickstart.py --help-long
```

**Troubleshooting**:
```bash
python verify_setup.py
```

**Check status**:
```bash
python auto_ops_dashboard.py
```

**Documentation**: See links above

---

## 🎉 You're Ready!

All tools are ready to use. Choose your preferred interface:

- **Web Dashboard**: `python vs_code_server.py`
- **CLI Terminal**: `python auto_ops_dashboard.py`
- **Interactive Menu**: `python vscode_quickstart.py`
- **All At Once**: `python vscode_quickstart.py --full`

**In VS Code**: `Ctrl+Alt+A` to start everything

Start monitoring now! 🚀
