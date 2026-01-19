# Getting Started: VS Code Auto Operations

**Complete guide to monitoring all your Aria AI operations from VS Code**

## ⚡ 30-Second Start

1. **Open VS Code**
2. Press: `Ctrl+Alt+A`
3. Wait 2 seconds
4. Open: `http://localhost:8765` in your browser
5. Done! Dashboard is live

**That's it!** You now have:
- 📊 Real-time dashboard
- 🔔 Alert monitoring
- 📋 CLI view
- ⚠️ Issue alerts

---

## 🎯 What You'll See

```
┌─────────────────────────────────────────────────────┐
│                  Auto Operations                    │
│                                                     │
│  Last Updated: 2026-01-19 00:03:00 UTC            │
│                                                     │
│  📊 Summary                                         │
│  ├─ Running: 3  ✅ Success: 7  ❌ Failed: 0        │
│  └─ ⚠️  Alerts: 1 (CPU high)                        │
│                                                     │
│  🎓 Learning (3 operations)                        │
│  ├─ 🟢 Autonomous Training    [████████░░] 80%    │
│  ├─ ⚪ AutoTrain              [waiting...]          │
│  └─ ✅ GGUF Training          [completed]           │
│                                                     │
│  📈 Evaluation (2 operations)                       │
│  ├─ ✅ Quantum AutoRun        [accuracy: 0.92]     │
│  └─ ✅ Evaluation AutoRun     [F1: 0.88]           │
│                                                     │
│  ... more operations below ...                     │
└─────────────────────────────────────────────────────┘
```

---

## 📖 Common Workflows

### I Want to Monitor While Developing

```bash
# Step 1: Start everything
Ctrl+Alt+A

# Step 2: Open VS Code split view
View → Editor Layout → Two Columns

# Step 3: Dashboard on right
Ctrl+K Ctrl+O
# Type: http://localhost:8765

# Step 4: Code on left, dashboard on right
# Watch operations in real-time while coding
```

### I Want to Check for Problems Quickly

```bash
# Show only issues/alerts
Ctrl+Alt+P

# Or in dashboard:
# Just scroll to "Alerts" section
# Problems highlighted in red
```

### I Want Live Alerts

```bash
# Alerts already running in background
# View them in: Output panel

# To see output:
Ctrl+Shift+U  (opens Output panel)

# Select: "Monitor" from dropdown
# Watch for 🔴 [CRITICAL] and ⚠️ [WARNING]
```

### I Want to Understand an Operation

```bash
# 1. Open CLI dashboard
Ctrl+Alt+S

# 2. Look for operation name
# Shows full details:
#  - Status
#  - Progress
#  - Metrics
#  - Last update
#  - Any errors

# 3. Or check web dashboard
# Click operation card to see details
```

---

## 🎮 Controls & Commands

### Keyboard Shortcuts

| Shortcut | Does | Example |
|----------|------|---------|
| `Ctrl+Alt+A` | Start full suite | All systems go |
| `Ctrl+Alt+D` | Start dashboard | Web interface |
| `Ctrl+Alt+S` | CLI dashboard | Terminal view |
| `Ctrl+Alt+W` | Watch mode | Auto-refresh |
| `Ctrl+Alt+P` | Problems only | Show issues |

### VS Code Command Palette (`Ctrl+Shift+P`)

```
Tasks: Run Task → Pick monitor task
```

Available tasks:
- `Monitor: Auto Ops Dashboard` — One-time view
- `Monitor: Auto Ops (Watch)` — Background refresh
- `Monitor: Auto Ops (Compact)` — Minimal view
- `Monitor: Auto Ops (Problems Only)` — Issues only
- `Monitor: Quick Setup (Interactive Menu)` — Interactive help
- `Monitor: Dashboard Server (VS Code)` — Start web server
- `Monitor: Alert Monitor (Background)` — Start alerts
- `Monitor: Start Full VS Code Suite` — All systems

### Dashboard Controls (in browser)

| Control | Does |
|---------|------|
| **Pause** button | Stop auto-refresh |
| **Resume** button | Resume auto-refresh |
| **Refresh** button | Update now |
| Status badge | Shows "Live" or "Paused" |
| Scroll down | See more operations |
| Click operation | View details (coming soon) |

---

## 📊 Understanding the Dashboard

### Operation Status Indicators

| Icon | Meaning |
|------|---------|
| 🟢 | Running right now |
| ⚪ | Idle (not running) |
| ✅ | Completed successfully |
| ❌ | Failed or error |
| ⏳ | Waiting/queued |
| 📊 | In progress |

### Metrics Shown

**For each operation:**
- **Status**: Current state
- **Progress**: % complete (if running)
- **Cycles**: Number of cycles/iterations completed
- **Accuracy**: Model performance (if applicable)
- **Last Update**: When this was last updated
- **Duration**: How long it ran/is running
- **Alerts**: Any issues detected

### Alert Types

| Alert | Color | Severity |
|-------|-------|----------|
| CPU >95% | Red | 🔴 Critical |
| Memory >85% | Red | 🔴 Critical |
| Disk >85% | Red | 🔴 Critical |
| Job failed | Red | 🔴 Error |
| Accuracy down | Orange | ⚠️ Warning |

---

## 🔍 Monitoring Each Operation

### Autonomous Training
- **What**: Continuous self-learning, 30-min cycles
- **Metrics**: cycles_completed, best_accuracy, dataset_count
- **Alerts**: accuracy decline, resource constraints
- **Status file**: `data_out/autonomous_training_status.json`

### AutoTrain
- **What**: Manual training orchestration (12 jobs)
- **Metrics**: total_jobs, succeeded, failed, running
- **Alerts**: job failures, resource constraints
- **Status file**: `data_out/autotrain/status.json`

### GGUF Training
- **What**: Quantum-enhanced model training
- **Metrics**: training_jobs, conversion_progress
- **Alerts**: conversion failures, disk space
- **Status file**: `data_out/gguf_training/training_status.json`

### Quantum AutoRun
- **What**: Quantum simulations & real hardware
- **Metrics**: job_queue, success_rate, hardware_type
- **Alerts**: QPU errors, cost warnings
- **Status file**: `data_out/quantum_autorun/status.json`

### Evaluation AutoRun
- **What**: Model evaluation & benchmarking
- **Metrics**: eval_jobs, accuracy, F1_score
- **Alerts**: eval failures, metric regressions
- **Status file**: `data_out/evaluation_autorun/status.json`

### Master Orchestrator
- **What**: Coordinates all systems
- **Metrics**: active_jobs, total_jobs, success_rate
- **Alerts**: orchestration errors, job hangs
- **Status file**: `data_out/master_orchestrator/status.json`

### Train & Promote
- **What**: Training with auto-deployment
- **Metrics**: train_accuracy, eval_accuracy, deployment_status
- **Alerts**: promotion failures, performance drop
- **Status file**: `data_out/train_and_promote/pipeline_*.json`

### Training Scheduler
- **What**: Scheduled/nightly training
- **Metrics**: scheduled_jobs, completed, success_rate
- **Alerts**: schedule misses, job failures
- **Status file**: `data_out/training_scheduler/scheduler_state.json`

### CI Pipeline
- **What**: Continuous validation & testing
- **Metrics**: tests_run, passed, failed, coverage
- **Alerts**: test failures, coverage drop
- **Status file**: `data_out/ci_orchestrator/ci_results.json`

---

## 🚨 Understanding Alerts

### Alert Flow

```
Operation Runs
    ↓
Every 30 seconds: Alert Monitor checks
    ↓
Detects issue? (CPU >95%, job failed, etc.)
    ↓
Yes → Check cooldown (5 min timeout)
    ↓
Not in cooldown? → Send alert
    ↓
Alert appears in:
  • Output panel (terminal)
  • Dashboard (red alert section)
  • VS Code status bar (coming soon)
```

### What Triggers Alerts

**Every 30 seconds, monitor checks:**

1. **CPU Usage**
   - Critical: >95%
   - Warning: >80%

2. **Memory Usage**
   - Critical: >85%
   - Warning: >75%

3. **Disk Space**
   - Critical: >85% used
   - Warning: >70% used

4. **Failed Operations**
   - Checks: job_status == "failed"
   - Alert level: error

5. **Accuracy Decline**
   - Checks: current_accuracy < previous * 0.95
   - Alert level: warning

### How to Respond to Alerts

**Step 1: See the alert**
```
Output panel shows:
🔴 [CRITICAL] High CPU Usage
   └─ CPU at 96.5%
```

**Step 2: Check dashboard**
```
Ctrl+Alt+D
Look for red alerts at top of dashboard
```

**Step 3: Investigate operation**
```
Ctrl+Alt+P  (show problems)
Find which operation is affected
```

**Step 4: Take action**
```
Based on alert:
- High CPU? Reduce batch size or pause training
- High memory? Stop other processes
- Disk full? Clean up old models
- Job failed? Check logs: tail -f data_out/*/status.json
```

---

## 📈 Monitoring Best Practices

### Daily Routine

```
Morning:
1. Start work: Ctrl+Alt+A
2. Open dashboard: Ctrl+Alt+D
3. Quick check: Any overnight issues?
4. Keep dashboard visible

During Development:
1. Split screen: Code | Dashboard
2. Watch metrics update in real-time
3. React to alerts immediately

End of Day:
1. Check final status: Ctrl+Alt+S
2. Note any issues for tomorrow
3. Stop monitoring: Ctrl+Shift+U → Stop Tasks
```

### Interpretation Guide

```
🟢 Running (green)
  → Normal operation, continue monitoring

⚪ Idle (gray)
  → Waiting for next cycle, check last status

✅ Success (checkmark)
  → Operation completed, review metrics

❌ Error (X)
  → Investigation needed
  → Check logs: data_out/*/logs/
  → Check alert: Ctrl+Alt+P

High Progress %
  → On track, check ETA

Low Progress %
  → May be stuck or slow
  → Check resources: Ctrl+Alt+D → scroll for CPU/memory

Multiple 🔴
  → Possible cascading failure
  → Stop Master Orchestrator and investigate
```

---

## 🔧 Customization

### Change Update Frequency

**Edit** `scripts/monitoring/vs_code_server.py`:
```python
# Change this line:
refreshInterval = setInterval(loadDashboard, 5000);  // 5 seconds

# To:
refreshInterval = setInterval(loadDashboard, 2000);  // 2 seconds
```

### Change Alert Cooldown

**Edit** `scripts/monitoring/vs_code_alert_monitor.py`:
```python
# Change this:
self.alert_cooldown = 300  # 5 minutes

# To:
self.alert_cooldown = 60   # 1 minute
```

### Change Dashboard Port

**Edit** `scripts/monitoring/vs_code_server.py`:
```python
if __name__ == "__main__":
    app.run(host='localhost', port=8765)  # Change 8765
```

---

## 🐛 Troubleshooting

### "Dashboard not loading"

**Check 1**: Is the server running?
```bash
ps aux | grep vs_code_server
# Should show Python process running
```

**Check 2**: Is port free?
```bash
netstat -tlnp | grep 8765
# Should show LISTENING
```

**Check 3**: Try manually:
```bash
python scripts/monitoring/vs_code_server.py
```

**Check 4**: Use different port:
```python
# Edit vs_code_server.py:
app.run(host='localhost', port=8766)  # Try 8766
```

### "Alerts not appearing"

**Check**: Is alert monitor running?
```bash
ps aux | grep vs_code_alert_monitor
# Should show Python process
```

**Try manually**:
```bash
python scripts/monitoring/vs_code_alert_monitor.py
```

### "Tasks don't show up"

**Solution**: Reload VS Code
```
Ctrl+Shift+P → Developer: Reload Window
```

### "Can't find keyboard shortcuts"

**Check**: Are keybindings installed?
```
VS Code → Settings → Keyboard Shortcuts
Search: "Ctrl+Alt+A"
```

**If missing**: Copy from `.vscode/keybindings-auto-ops.json`
```
1. Open: Ctrl+Shift+P → "Preferences: Open Keyboard Shortcuts (JSON)"
2. Add contents from `.vscode/keybindings-auto-ops.json`
3. Reload: Ctrl+Shift+P → Developer: Reload Window
```

---

## 📚 More Information

| Topic | File |
|-------|------|
| Complete integration guide | [docs/VSCODE_INTEGRATION.md](../docs/VSCODE_INTEGRATION.md) |
| Monitoring suite features | [docs/AUTO_OPS_MONITORING_SUITE.md](../docs/AUTO_OPS_MONITORING_SUITE.md) |
| All automation features | [AUTO_OPS_VISIBILITY_INDEX.md](../AUTO_OPS_VISIBILITY_INDEX.md) |
| CLI dashboard reference | [docs/AUTO_OPS_DASHBOARD.md](../docs/AUTO_OPS_DASHBOARD.md) |
| Implementation details | [docs/AUTO_OPS_VISIBILITY_IMPLEMENTATION.md](../docs/AUTO_OPS_VISIBILITY_IMPLEMENTATION.md) |

---

## 💡 Pro Tips

1. **Always start with**: `Ctrl+Alt+A` (starts all monitoring)

2. **Keep dashboard open**: Split screen makes monitoring effortless

3. **Watch alerts closely**: 5-minute response window for critical issues

4. **Export for CI/CD**: `python auto_ops_dashboard.py --json` for pipelines

5. **Share dashboard**: Open http://localhost:8765 to share with team

6. **Quick problem check**: `Ctrl+Alt+P` before committing code

7. **Use watch mode**: `Ctrl+Alt+W` for continuous updates

8. **Check resource usage**: Dashboard shows CPU/memory/disk at a glance

---

## ⚡ One-Command Start

Copy & paste this to get started immediately:

```bash
python scripts/monitoring/vscode_quickstart.py --full
```

Or just press: `Ctrl+Alt+A`

---

**Ready?** Start monitoring: `Ctrl+Alt+A`

Questions? Check: `python scripts/monitoring/vscode_quickstart.py --help-long`
