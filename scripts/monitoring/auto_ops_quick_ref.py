#!/usr/bin/env python
"""Auto Operations Quick Ref - Print helpful info about auto ops"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]

QUICK_REF = """
╔═══════════════════════════════════════════════════════════════════════╗
║                 AUTO OPERATIONS VISIBILITY GUIDE                      ║
║                     QAI Workspace Monitoring                          ║
╚═══════════════════════════════════════════════════════════════════════╝

📊 QUICK STATUS COMMANDS
────────────────────────────────────────────────────────────────────────

  View all operations:
    python scripts/monitoring/auto_ops_dashboard.py

  Watch real-time (refreshes every 5s):
    python scripts/monitoring/auto_ops_dashboard.py --watch

  Show only problems/alerts:
    python scripts/monitoring/auto_ops_dashboard.py --problems

  Compact view:
    python scripts/monitoring/auto_ops_dashboard.py --compact

  Export to JSON:
    python scripts/monitoring/auto_ops_dashboard.py --export

VS CODE TASKS (Ctrl+Shift+P → Tasks)
────────────────────────────────────────────────────────────────────────

  • Monitor: Auto Ops Dashboard
  • Monitor: Auto Ops (Watch) [background]
  • Monitor: Auto Ops (Problems Only)
  • Monitor: Auto Ops (Compact)
  • Monitor: Auto Ops (Export JSON)

🤖 AUTO OPERATIONS BY CATEGORY
────────────────────────────────────────────────────────────────────────

LEARNING & TRAINING:
  ├─ Autonomous Training      Status: autonomous_training_status.json
  │  • Continuous 30-min cycles, self-discovery
  │  • Command: pkill -USR1 -f autonomous_training (trigger now)
  │  • Logs: data_out/autonomous_training.log
  │
  ├─ AutoTrain               Status: data_out/autotrain/status.json
  │  • Scheduled training on datasets
  │  • Config: autotrain.yaml, quantum_autorun.yaml
  │  • Multiple jobs in parallel
  │
  └─ GGUF Training           Status: data_out/gguf_training/training_status.json
     • GGUF format + quantum enhancement
     • 9 job variants (quick/prod/HQ, standard/quantum)
     • Output: data_out/gguf_training/

EVALUATION & ANALYSIS:
  ├─ Evaluation AutoRun      Status: data_out/evaluation_autorun/status.json
  │  • Evaluates trained models
  │  • Config: evaluation_autorun.yaml
  │  • Generates metrics: perplexity, accuracy, etc.
  │
  └─ Quantum AutoRun         Status: data_out/quantum_autorun/status.json
     • Quantum circuit simulations + real QPU
     • Config: quantum_autorun.yaml
     • Local simulation first, then Azure backends

SCHEDULING & ORCHESTRATION:
  ├─ Master Orchestrator     Status: data_out/master_orchestrator/status.json
  │  • Coordinates all orchestrators
  │  • Config: config/master_orchestrator.yaml
  │  • Cron schedules + dependencies
  │  • Resource alerts (CPU >80%, disk >85%)
  │
  ├─ Training Scheduler      Status: data_out/training_scheduler/scheduler_state.json
  │  • Nightly/grid training jobs
  │  • Supports: nightly, weekly, custom presets
  │
  └─ Auto Scheduler          Status: data_out/auto_scheduler/schedule.json
     • General-purpose job scheduling
     • Config: config/auto_scheduler.yaml

DEPLOYMENT & PROMOTION:
  └─ Train & Promote         Status: data_out/train_and_promote/pipeline_*.json
     • Full pipeline: train → evaluate → rank → promote
     • Latest: data_out/train_and_promote/pipeline_LATEST
     • Output: promoted models in deployed_models/

CI/CD PIPELINE:
  └─ CI Pipeline             Status: data_out/ci_orchestrator/ci_results.json
     • Validate configs, run tests, prepare deployment
     • Steps: orchestrator validate, unit tests, integration, etc.

⏱️  STATUS INDICATORS
────────────────────────────────────────────────────────────────────────

Status:
  🟢 Running / Active         ⚪ Idle
  ✅ Success                   ❌ Error
  📅 Scheduled                 🔒 Disabled
  ❓ Unknown

Alerts:
  🔴 Critical (CPU >80%, memory >80%, disk >85%)
  ⚠️  Warning (promotion failed, accuracy declined)
  ❌ Error (failed jobs, validation failures)
  📉 Degradation (performance trend)

🚨 ALERT RESPONSES
────────────────────────────────────────────────────────────────────────

If you see:

  🔴 CPU at 95.6%
    → Check: top, ps aux | grep python
    → Solution: Reduce max_workers, scale to off-peak hours

  ⚠️  Promotion failed - check logs
    → File: data_out/train_and_promote/pipeline_*.json
    → Check: deployed_models/ permissions, symlink support

  ❌ CI failed: validate_datasets
    → File: data_out/ci_orchestrator/ci_results.json
    → Command: python scripts/validate_datasets.py --category chat

  📉 Accuracy declined
    → File: data_out/autonomous_training_status.json (performance_history)
    → Possible: dataset drift, hyperparameter issue, model overfitting

📈 MONITORING WORKFLOWS
────────────────────────────────────────────────────────────────────────

Daily Status Check:
  python scripts/monitoring/auto_ops_dashboard.py --compact
  python scripts/monitoring/auto_ops_dashboard.py --problems

Continuous Monitoring (Dev):
  python scripts/monitoring/auto_ops_dashboard.py --watch

Alert-Only Loop (Automation):
  while true; do
    python scripts/monitoring/auto_ops_dashboard.py --problems
    sleep 30
  done

Full System View:
  echo "=== Auto Ops ===" && python scripts/monitoring/auto_ops_dashboard.py
  echo "=== Resources ===" && python scripts/monitoring/resource_monitor.py --snapshot
  echo "=== Orchestrators ===" && python scripts/monitoring/status_dashboard.py

🔗 RELATED COMMANDS
────────────────────────────────────────────────────────────────────────

Start Operations:
  python scripts/training/autonomous_training_orchestrator.py          [background]
  python scripts/orchestrators/master_orchestrator.py --workflow daily_full_pipeline
  python scripts/training/training_scheduler.py --start nightly        [background]

Control Operations:
  pkill -USR1 -f autonomous_training          [trigger immediate cycle]
  pkill -TERM -f autonomous_training          [graceful shutdown]
  pkill -f training_scheduler                 [stop scheduler]

Validate:
  python scripts/orchestrators/ci_orchestrator.py --validate-all       [dry-run]
  python scripts/orchestrators/master_orchestrator.py --dry-run
  python scripts/training/autotrain.py --dry-run

Export:
  python scripts/monitoring/auto_ops_dashboard.py --export
  cat data_out/auto_ops_dashboard.json | jq .

📚 DOCUMENTATION
────────────────────────────────────────────────────────────────────────

Full docs:
  docs/AUTO_OPS_DASHBOARD.md

Status files directory:
  data_out/

Orchestrator configs:
  config/autonomous_training.yaml
  config/master_orchestrator.yaml
  config/training_scheduler.yaml

Script locations:
  scripts/monitoring/auto_ops_dashboard.py      [this dashboard]
  scripts/monitoring/status_dashboard.py        [detailed metrics]
  scripts/monitoring/resource_monitor.py        [CPU/GPU/disk]
  scripts/training/autonomous_training_orchestrator.py
  scripts/orchestrators/master_orchestrator.py
  scripts/orchestrators/ci_orchestrator.py

💡 TIPS
────────────────────────────────────────────────────────────────────────

• Use --watch for real-time development monitoring
• Check --problems first when debugging issues
• Export JSON for integration with CI/CD pipelines
• Combine with `watch` command for terminal dashboard:
    watch -n 5 'python scripts/monitoring/auto_ops_dashboard.py --compact'
• Set up alerts via cron:
    */5 * * * * python scripts/monitoring/auto_ops_dashboard.py --export >> /tmp/ops.log

════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(QUICK_REF)
