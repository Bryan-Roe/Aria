# Auto Operations Visibility Implementation

**Date**: January 18, 2026

All automated operations are now visible through a unified CLI dashboard.

## What's New

### 1. **Auto Operations Dashboard** (`scripts/monitoring/auto_ops_dashboard.py`)

A unified command-line monitoring tool that shows real-time status of all automated systems:

- **🤖 Learning & Training**: Autonomous Training, AutoTrain, GGUF Training
- **📊 Evaluation & Analysis**: Evaluation AutoRun, Quantum AutoRun
- **⏰ Scheduling & Orchestration**: Master Orchestrator, Training Scheduler, Auto Scheduler
- **🚀 Deployment & Promotion**: Train & Promote pipeline
- **🔄 CI/CD Pipeline**: CI orchestrator

**Status Aggregation**:
- Autonomous Training: cycles, accuracy, active tasks
- AutoTrain: jobs succeeded/failed, success rate
- GGUF Training: quantum vs standard job counts
- Train & Promote: pipeline status, best model, promotion success
- Master Orchestrator: active workflows, resource usage (CPU/memory/disk)
- Evaluation/Quantum: job counts and status
- CI Pipeline: validation steps passed/failed

**Alerts & Warnings**:
- 🔴 Critical: CPU >80%, memory >80%, disk >85%
- ⚠️ Warning: promotion failed, accuracy declined
- ❌ Error: failed jobs, validation failures
- 📉 Degradation: performance trends

### 2. **Usage Modes**

#### Single-Shot View
```bash
python scripts/monitoring/auto_ops_dashboard.py
# Shows all operations with metrics and alerts
```

#### Watch Mode (Auto-refresh)
```bash
python scripts/monitoring/auto_ops_dashboard.py --watch
# Refreshes every 5 seconds - perfect for development
```

#### Compact View
```bash
python scripts/monitoring/auto_ops_dashboard.py --compact
# One line per operation - minimal output
```

#### Problems Only
```bash
python scripts/monitoring/auto_ops_dashboard.py --problems
# Show only items with alerts or errors
```

#### JSON Export
```bash
python scripts/monitoring/auto_ops_dashboard.py --export
# Writes to: data_out/auto_ops_dashboard.json
# Perfect for CI/CD integration and parsing
```

### 3. **VS Code Integration**

Six new tasks available (Ctrl+Shift+P → Tasks):

- **Monitor: Auto Ops Dashboard** — Single-shot view
- **Monitor: Auto Ops (Watch)** — Auto-refresh (background)
- **Monitor: Auto Ops (Compact)** — Condensed output
- **Monitor: Auto Ops (Problems Only)** — Issues only
- **Monitor: Auto Ops (Export JSON)** — Export data
- **Monitor: Auto Ops Quick Ref** — Help guide

### 4. **Quick Reference Guide** (`scripts/monitoring/auto_ops_quick_ref.py`)

```bash
python scripts/monitoring/auto_ops_quick_ref.py
```

Displays:
- Quick commands for all dashboard modes
- Auto operation categories and status locations
- Status indicators and their meanings
- Alert response procedures
- Monitoring workflows (daily, continuous, alert-only)
- Related commands (start, control, validate, export)

## Data Sources

Dashboard aggregates from these JSON status files:

| Component | File |
|-----------|------|
| Autonomous Training | `data_out/autonomous_training_status.json` |
| AutoTrain | `data_out/autotrain/status.json` |
| GGUF Training | `data_out/gguf_training/training_status.json` |
| Evaluation AutoRun | `data_out/evaluation_autorun/status.json` |
| Quantum AutoRun | `data_out/quantum_autorun/status.json` |
| Master Orchestrator | `data_out/master_orchestrator/status.json` |
| Training Scheduler | `data_out/training_scheduler/scheduler_state.json` |
| Auto Scheduler | `data_out/auto_scheduler/schedule.json` |
| Train & Promote | `data_out/train_and_promote/pipeline_*.json` (latest) |
| CI Pipeline | `data_out/ci_orchestrator/ci_results.json` |

## Output Examples

### Full View
```
🤖 LEARNING & TRAINING
-----------
🟢 Autonomous Training        running      best_accuracy=0.8 | total_datasets=1191
  ├─ Task: training
  ├─ Progress: [████████░░░░░░░░░░] 40.0%
  ├─ Cycles: 5
  └─ Last update: 2026-01-18T20:37:06.383953

⚪ AutoTrain                   idle         total_jobs=14 | succeeded=10 | failed=0
  └─ Last update: 2026-01-18T22:35:44Z

📊 EVALUATION & ANALYSIS
-----------
⚪ Evaluation AutoRun          idle         total_jobs=8 | succeeded=0 | failed=0
  └─ Last update: 2026-01-18T22:35:53Z
```

### Compact View
```
🟢 Autonomous Training         running      
⚪ AutoTrain                   idle         
⚪ Evaluation AutoRun          idle         
```

### Problems View
```
⏰ SCHEDULING & ORCHESTRATION
-----------
🟢 Master Orchestrator         active       
  ├─ 🔴 CPU at 95.6%
  └─ Last update: 2025-11-26T04:07:43Z

🚀 DEPLOYMENT & PROMOTION
-----------
✅ Train & Promote             success      
  ├─ ⚠️  Promotion failed - check logs
  └─ Last update: 2025-11-27T22:06:45.827871
```

## JSON Export Schema

```json
{
  "timestamp": "2026-01-18T20:37:06.383953+00:00",
  "operations": [
    {
      "name": "Autonomous Training",
      "category": "learning",
      "status": "running",
      "cycles_completed": 0,
      "current_task": "training",
      "progress": 40.0,
      "alerts": [],
      "metrics": {
        "best_accuracy": 0.0,
        "total_datasets": 1191,
        "trained_datasets": 0
      },
      "last_update": "2026-01-18T20:37:06.383953"
    }
  ]
}
```

## Common Monitoring Workflows

### Daily Status Check
```bash
# Quick overview
python scripts/monitoring/auto_ops_dashboard.py --compact

# Check for problems
python scripts/monitoring/auto_ops_dashboard.py --problems
```

### Continuous Development Monitoring
```bash
# Watch all operations with auto-refresh
python scripts/monitoring/auto_ops_dashboard.py --watch
```

### Alert Automation
```bash
# Alert loop - check every 30 seconds
while true; do
  python scripts/monitoring/auto_ops_dashboard.py --problems
  sleep 30
done
```

### Full System Overview
```bash
echo "=== Auto Operations ===" && \
  python scripts/monitoring/auto_ops_dashboard.py --compact

echo && echo "=== System Resources ===" && \
  python scripts/monitoring/resource_monitor.py --snapshot

echo && echo "=== Orchestrator Details ===" && \
  python scripts/monitoring/status_dashboard.py
```

### CI/CD Integration
```bash
# Export for processing by other tools
python scripts/monitoring/auto_ops_dashboard.py --export

# Query in shell
jq '.operations[] | select(.status == "error")' data_out/auto_ops_dashboard.json

# Query in Python
import json
data = json.load(open("data_out/auto_ops_dashboard.json"))
for op in data["operations"]:
    if op["status"] == "running":
        print(f"{op['name']}: {op['progress']}%")
```

## Alert Interpretation

### 🔴 CPU at 95.6%
High CPU usage from parallel jobs.
- Check: `ps aux | grep python` to identify processes
- Solution: Reduce `max_workers` in training configs, scale to off-peak

### ⚠️ Promotion failed - check logs
Train & Promote pipeline completed but deployment failed.
- Check: `data_out/train_and_promote/pipeline_*.json`
- Possible issues: directory permissions, symlink not supported, model corrupted

### ❌ CI failed: validate_datasets
Validation step in CI orchestrator failed.
- Check: `data_out/ci_orchestrator/ci_results.json`
- Fix: `python scripts/validate_datasets.py --category chat`

### 📉 Accuracy declined from 0.85 to 0.79
Model performance degraded between cycles.
- Check: `autonomous_training_status.json` → `performance_history`
- Investigate: dataset drift, hyperparameter tuning, convergence issues

## Files Created

1. **scripts/monitoring/auto_ops_dashboard.py** — Main dashboard tool
2. **scripts/monitoring/auto_ops_quick_ref.py** — Quick reference guide
3. **docs/AUTO_OPS_DASHBOARD.md** — Full documentation
4. **.vscode/tasks.json** — Updated with 6 new monitoring tasks

## Backward Compatibility

- No breaking changes to existing orchestrators
- Dashboard is read-only (doesn't modify any files)
- Existing status file formats unchanged
- All aggregation happens at display time (stateless)

## Future Enhancements

Potential additions:
- Web dashboard (HTTP endpoint for browser access)
- Email/Slack alerting on failures
- Multi-run trend analysis
- Custom alert thresholds
- Overall system health score
- Historical data retention

## Quick Start

1. **View current status**:
   ```bash
   python scripts/monitoring/auto_ops_dashboard.py
   ```

2. **Print help guide**:
   ```bash
   python scripts/monitoring/auto_ops_quick_ref.py
   ```

3. **In VS Code**: Press `Ctrl+Shift+P` → Search "Monitor: Auto Ops"

4. **Full documentation**: Read `docs/AUTO_OPS_DASHBOARD.md`

## Summary

✅ **All auto operations are now visible** through:
- **CLI dashboard** with multiple view modes (full, compact, problems, watch)
- **VS Code integration** with quick-access tasks
- **JSON export** for CI/CD and programmatic access
- **Quick reference** guide for common workflows
- **Comprehensive documentation** with examples

The implementation uses a **stateless, file-based aggregation** approach that:
- Reads status files on each invocation
- Parses metrics and detects alerts
- Renders formatted output
- Exports structured JSON

This enables real-time visibility of training, evaluation, scheduling, deployment, and CI operations without additional infrastructure overhead.
