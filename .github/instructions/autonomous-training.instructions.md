---
name: "Autonomous-Training"
description: "Guidance for autonomous training orchestration and model lifecycle"
applyTo: "scripts/autonomous_training*"
---
# Autonomous Training — Implementation Guidance

- Continuous 30-minute training cycles (infinite by default).
- State machine: `discovery → collection → training → analysis → optimization → deployment`.
- Self-discovers datasets by scanning `datasets/quantum`, `datasets/chat`, `datasets/massive_quantum`.
- Adaptive epoch selection: `[25, 50, 100, 200]` based on performance history.
  - Increase epochs if accuracy < 0.70 or plateauing.
- Performance degradation detection: alerts on >5% accuracy drop between cycles.
- Auto-deploy threshold: accuracy > 0.90 (configurable, must be enabled).
- Config: `config/autonomous_training.yaml` (cycle_interval_minutes, epochs_progression, min_datasets).
- Status output: `data_out/autonomous_training_status.json` — `{cycles_completed, best_accuracy, performance_history[], dataset_inventory}`.
- Logs: `data_out/autonomous_training.log`.
- Graceful error handling: continues on failure, logs errors, resumes next cycle.
- Manual trigger: `pkill -USR1 -f autonomous_training` forces immediate cycle.
- Graceful shutdown: `pkill -TERM -f autonomous_training` (not -9).
- Background execution: `nohup python scripts/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &`.
- Data immutability: NEVER modify `datasets/`; all outputs go to `data_out/`.
- Monitoring: `python scripts/monitor_autonomous_training.py --watch`.
- Analytics: `python scripts/training_analytics.py` for trends and plateau detection.
