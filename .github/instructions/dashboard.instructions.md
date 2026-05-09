---
name: "Dashboard-App"
description: "Guidance for the dashboard web application"
applyTo: "apps/dashboard/**"
---
# Dashboard App — Implementation Guidance

- Web dashboard for monitoring and managing the Aria platform.
- Consumes data from orchestrator status files in `data_out/<orchestrator>/status.json`.
- Key metrics to display:
  - Training cycles completed, best accuracy, performance trends
  - Orchestrator job counts (total, succeeded, failed, running)
  - System health (provider status, SQL pool, Cosmos DB)
  - Resource utilization (CPU, memory, disk, GPU)
- Health endpoint: `GET /api/ai/status` returns comprehensive system diagnostics.
- Status files follow schema: `{total_jobs, succeeded, failed, running, last_updated, avg_duration}`.
- Autonomous training status: `{cycles_completed, best_accuracy, performance_history[], dataset_inventory}`.
- Prefer polling status files over live process introspection.
- Monitoring scripts available: `scripts/status_dashboard.py`, `scripts/resource_monitor.py`, `scripts/training_analytics.py`.
