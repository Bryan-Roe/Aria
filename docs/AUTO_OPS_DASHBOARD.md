# Auto Operations Dashboard

**Real-time CLI visibility for all automated operations in the QAI workspace**

## Overview

The Auto Operations Dashboard provides a unified command-line interface to monitor all automated systems running in your QAI workspace:

- **🤖 Learning & Training**: Autonomous training, AutoTrain, GGUF training
- **📊 Evaluation & Analysis**: Evaluation AutoRun, Quantum AutoRun  
- **⏰ Scheduling & Orchestration**: Master Orchestrator, Training Scheduler, Auto Scheduler
- **🚀 Deployment & Promotion**: Train & Promote pipeline, model promotions
- **🔄 CI/CD Pipeline**: CI orchestrator status

Each operation shows:
- Current status (running, idle, success, error, scheduled)
- Progress metrics (cycles completed, jobs succeeded/failed, accuracy)
- Active tasks and current progress
- Alerts and warnings (high resource usage, failures, promotion issues)
- Last update timestamp

## Quick Start

### View Current Status (Single-shot)
```bash
python scripts/monitoring/auto_ops_dashboard.py
```

### Watch Mode (Auto-refresh every 5 seconds)
```bash
python scripts/monitoring/auto_ops_dashboard.py --watch
```

Press `Ctrl+C` to exit watch mode.

### Compact View (Condensed output)
```bash
python scripts/monitoring/auto_ops_dashboard.py --compact
```

### Problems Only (Show items with issues)
```bash
python scripts/monitoring/auto_ops_dashboard.py --problems
```

### Export to JSON
```bash
python scripts/monitoring/auto_ops_dashboard.py --export
# Writes to: data_out/auto_ops_dashboard.json
```

## VS Code Integration

Quick access tasks are available:

- **Monitor: Auto Ops Dashboard** — Single-shot view
- **Monitor: Auto Ops (Watch)** — Auto-refresh mode (background)
- **Monitor: Auto Ops (Compact)** — Condensed output
- **Monitor: Auto Ops (Problems Only)** — Show issues only
- **Monitor: Auto Ops (Export JSON)** — Export for parsing

Run via Command Palette: `Ctrl+Shift+P` → Tasks → Select task

## Output Format

### Full View (Default)
Shows detailed metrics for each operation:
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
```

### Compact View
Minimal output, one line per operation:
```
🟢 Autonomous Training         running      
⚪ AutoTrain                   idle         
```

### Status Indicators
- 🟢 Running/Active
- ⚪ Idle
- ✅ Success
- ❌ Error/Failed
- 📅 Scheduled
- 🔒 Disabled
- ❓ Unknown

### Alert Types
- 🔴 Critical (CPU/memory/disk >80%)
- ⚠️  Warning (promotion failed, accuracy declined)
- ❌ Errors (failed jobs, CI failures)
- 📉 Degradation (performance declined)
- 📁 Disk space warnings

## Data Sources

The dashboard aggregates from these sources:

| Component | File | Status Type |
|-----------|------|-------------|
| Autonomous Training | `data_out/autonomous_training_status.json` | Learning |
| AutoTrain | `data_out/autotrain/status.json` | Learning |
| GGUF Training | `data_out/gguf_training/training_status.json` | Learning |
| Evaluation AutoRun | `data_out/evaluation_autorun/status.json` | Evaluation |
| Quantum AutoRun | `data_out/quantum_autorun/status.json` | Evaluation |
| Master Orchestrator | `data_out/master_orchestrator/status.json` | Scheduling |
| Training Scheduler | `data_out/training_scheduler/scheduler_state.json` | Scheduling |
| Auto Scheduler | `data_out/auto_scheduler/schedule.json` | Scheduling |
| Train & Promote | `data_out/train_and_promote/pipeline_*.json` (latest) | Deployment |
| CI Pipeline | `data_out/ci_orchestrator/ci_results.json` | CI/CD |

## JSON Export Schema

When using `--export`, the output follows this schema:

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
        "total_datasets": 1191
      },
      "last_update": "2026-01-18T20:37:06.383953"
    }
  ]
}
```

## Monitoring Workflows

### Daily Status Check
```bash
# Quick overview of all operations
python scripts/monitoring/auto_ops_dashboard.py --compact

# Check for problems
python scripts/monitoring/auto_ops_dashboard.py --problems
```

### Continuous Monitoring (Development)
```bash
# Watch all operations with 5s refresh
python scripts/monitoring/auto_ops_dashboard.py --watch
```

### CI/Integration
```bash
# Export for processing by other tools
python scripts/monitoring/auto_ops_dashboard.py --export
# Use data_out/auto_ops_dashboard.json in your pipeline
```

### Alert Workflow
```bash
# Show only items with issues/alerts
while true; do
  python scripts/monitoring/auto_ops_dashboard.py --problems
  sleep 30
done
```

## Alert Interpretation

### 🔴 CPU at 95.6%
The Master Orchestrator is running many jobs in parallel. Consider:
- Reducing `max_workers` in training configs
- Scaling orchestrator execution to off-peak hours
- Checking for runaway processes: `ps aux | grep python`

### ⚠️ Promotion failed - check logs
The Train & Promote pipeline completed but model promotion failed. Check:
- `data_out/train_and_promote/pipeline_*.json` (latest) for error details
- Directory permissions in `deployed_models/`
- Symlink support (Windows may fail on symlinks)

### ❌ CI failed: validate_datasets
A CI validation step failed. Check:
- `data_out/ci_orchestrator/ci_results.json` for detailed error
- Dataset integrity: `python scripts/validate_datasets.py --category chat`
- Test logs: `data_out/test_runner/`

### 📉 Accuracy declined from 0.85 to 0.79
Model performance degraded between cycles. Investigate:
- Recent dataset changes or contamination
- Hyperparameter tuning (learning rate, dropout)
- Model convergence on specific data patterns
- Check `autonomous_training_status.json` → `performance_history`

## Programmatic Usage

### Parse JSON Export in Shell
```bash
python scripts/monitoring/auto_ops_dashboard.py --export

# Get all operations with errors
jq '.operations[] | select(.status == "error")' data_out/auto_ops_dashboard.json

# Extract metrics for one operation
jq '.operations[] | select(.name == "Train & Promote") | .metrics' data_out/auto_ops_dashboard.json

# Check for high CPU usage alert
jq '.operations[] | select(.alerts[] | contains("CPU"))' data_out/auto_ops_dashboard.json
```

### In Python
```python
import json
from pathlib import Path

dashboard = json.loads(Path("data_out/auto_ops_dashboard.json").read_text())

for op in dashboard["operations"]:
    if op["status"] == "running":
        print(f"{op['name']}: {op['progress']}% complete")
    if op["alerts"]:
        print(f"  Alerts: {', '.join(op['alerts'])}")
```

## Combining with Other Monitoring Tools

### With Resource Monitor
```bash
# Side-by-side: operations + resources
echo "=== Auto Operations ===" && python scripts/monitoring/auto_ops_dashboard.py --compact
echo && echo "=== System Resources ===" && python scripts/monitoring/resource_monitor.py --snapshot
```

### With Status Dashboard
```bash
# More detailed orchestrator-level view
python scripts/monitoring/status_dashboard.py

# Then get the auto ops view for real-time context
python scripts/monitoring/auto_ops_dashboard.py
```

## Troubleshooting

### Dashboard shows "unknown" for all operations
Status files haven't been created yet. Ensure orchestrators have run:
```bash
# Trigger operations
python scripts/orchestrators/ci_orchestrator.py --validate-all
python scripts/orchestrators/master_orchestrator.py --status
```

### Progress bar doesn't move
Timestamp parsing issue. Check that `autonomous_training_status.json` has valid ISO format timestamps:
```bash
cat data_out/autonomous_training_status.json | jq '.active_tasks[0].started_at'
# Should output: "2026-01-18T20:37:07.085103"
```

### Missing status files for specific operations
Operations may not be enabled. Check configs:
- `config/autonomous_training.yaml` — Enable/disable autonomous training
- `config/master_orchestrator.yaml` — Configure orchestrator schedules
- `GGUF_training` requires: `scripts/training/gguf_training_automation.py`

## Architecture

The dashboard uses a **file-based status aggregation** pattern:

1. Each orchestrator writes its status to a JSON file in `data_out/`
2. Dashboard reads all status files on each invocation
3. Parses metrics and detects alerts
4. Renders formatted output or exports JSON

This design allows:
- **Real-time status** without database dependencies
- **Integration flexibility** (any tool can consume JSON)
- **Offline inspection** (export JSON, analyze later)
- **Extensibility** (add new orchestrators by adding parsers)

## Future Enhancements

Planned additions:
- Web dashboard (HTTP endpoint for browser access)
- Alerting (email/Slack notifications on failures)
- Trend analysis (multi-run performance tracking)
- Custom alert rules (user-defined thresholds)
- Health scoring (overall system health metric)

## See Also

- [Status Dashboard](../README.md) — Detailed orchestrator metrics
- [Resource Monitor](../monitoring/resource_monitor.py) — CPU/GPU/disk usage
- [Master Orchestrator](../orchestrators/master_orchestrator.py) — Schedule management
- [Autonomous Training](../training/autonomous_training_orchestrator.py) — Continuous learning
