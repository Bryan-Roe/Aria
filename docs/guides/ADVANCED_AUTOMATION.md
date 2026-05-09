# Advanced Automation System

Comprehensive orchestration and automation layer for QAI workspace with multi-level automation capabilities.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Auto-Scheduler (Top Level)                │
│  - Cron-based scheduling                                     │
│  - Event-based triggers                                      │
│  - Resource-aware execution                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│            Master Orchestrator (Workflow Layer)              │
│  - Coordinates sub-orchestrators                             │
│  - Dependency management                                     │
│  - Success/failure handlers                                  │
└────┬───────────────┬───────────────┬────────────────────────┘
     │               │               │
┌────▼──────┐  ┌────▼──────┐  ┌────▼──────┐
│ AutoTrain │  │  Quantum  │  │ Evaluation│
│           │  │  AutoRun  │  │  AutoRun  │
└───────────┘  └───────────┘  └───────────┘
```

## Orchestrator Levels

### Level 1: Domain Orchestrators (Job Execution)
- **autotrain.py** - LoRA fine-tuning jobs
- **quantum_autorun.py** - Quantum training jobs
- **evaluation_autorun.py** - Model evaluation jobs

### Level 2: Master Orchestrator (Workflow Coordination)
- **master_orchestrator.py** - Coordinates workflows across orchestrators
- Dependencies, priorities, timeouts
- Success/failure handlers
- Resource monitoring

### Level 3: CI/CD Orchestrator (Quality Gates)
- **ci_orchestrator.py** - Parallel validation
- Unit & integration tests
- Code quality checks
- Deployment preparation

### Level 4: Auto-Scheduler (Time-Based Automation)
- **auto_scheduler.py** - Cron-based scheduling
- Persistent state
- Auto-retry logic
- Failure notifications

## Quick Start

### 1. Run Quick Validation (All Orchestrators)

```powershell
# Validate all configurations in parallel (fast)
python .\scripts\ci_orchestrator.py --validate-all
```

**Output**: Validates autotrain, quantum_autorun, evaluation_autorun in parallel (~1 second)

### 2. Run Master Orchestrator Workflow

```powershell
# Run quick validation workflow (dry-run all orchestrators)
python .\scripts\master_orchestrator.py --workflow quick_validation

# Run daily full pipeline (actual training)
python .\scripts\master_orchestrator.py --workflow daily_full_pipeline
```

### 3. Schedule Automated Runs

```powershell
# Add scheduled job (requires pip install croniter)
python .\scripts\auto_scheduler.py --schedule "daily_training" --workflow "daily_full_pipeline" --cron "0 2 * * *"

# Start scheduler daemon
python .\scripts\auto_scheduler.py --start

# Check scheduled jobs
python .\scripts\auto_scheduler.py --list
```

### 4. Run Full CI Pipeline

```powershell
# Complete CI/CD validation + tests + preparation
python .\scripts\ci_orchestrator.py --ci-pipeline
```

## VS Code Tasks

All orchestrators available as VS Code tasks (Ctrl+Shift+P → "Run Task"):

| Task | Command |
|------|---------|
| **Run: Evaluation AutoRun (dry-run)** | Validate evaluation jobs |
| **Run: Evaluation AutoRun (all)** | Run all evaluation jobs |
| **Run: CI Validate All** | Validate all orchestrators in parallel |
| **Run: CI Pipeline** | Full CI/CD pipeline execution |
| **Run: Master Orchestrator - Quick Validation** | Quick workflow validation |
| **Run: Master Orchestrator - Status** | Show orchestrator status |
| **Run: Model Deployer - Scan** | Scan for deployable models |
| **Run: Model Deployer - Deploy Best** | Auto-deploy best model |
| **Run: Resource Monitor - Snapshot** | Capture resource snapshot |
| **Run: Resource Monitor - Stream** | Real-time resource monitoring |
| **Run: Batch Evaluator - Scan** | Scan and evaluate all models |
| **Run: Results Exporter - Export to Markdown** | Export all results to Markdown |
| **Run: Auto Scheduler - List** | List scheduled jobs |
| **Run: CI Validate All** | Parallel validation of all orchestrators |
| **Run: CI Pipeline** | Full CI/CD pipeline |
| **Run: Master Orchestrator - Quick Validation** | Run quick_validation workflow |
| **Run: Master Orchestrator - Status** | Show master orchestrator status |

## Configuration Files

### master_orchestrator.yaml

Defines workflows and orchestrator coordination:

```yaml
workflows:
  - name: daily_full_pipeline
    enabled: true
    trigger: schedule
    schedule: "0 1 * * *"  # Daily at 1 AM
    orchestrators:
      - autotrain
      - quantum_autorun
      - evaluation_autorun
    on_success:
      - notify_slack
      - deploy_best_models
    on_failure:
      - notify_slack
      - create_issue
```

### Workflow Patterns

#### Quick Validation (CI/CD)
Dry-run all orchestrators in sequence, fail fast on errors.

```powershell
python .\scripts\master_orchestrator.py --workflow quick_validation
```

#### Daily Full Pipeline
Run training → quantum → evaluation with notifications.

```powershell
python .\scripts\master_orchestrator.py --workflow daily_full_pipeline
```

#### Weekly Comprehensive
Full datasets, all jobs, comprehensive reports.

```powershell
python .\scripts\master_orchestrator.py --workflow weekly_comprehensive
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: QAI CI Pipeline

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pyyaml pytest

      - name: Validate All Orchestrators
        run: python scripts/orchestrators/ci_orchestrator.py --validate-all

      - name: Run Unit Tests
        run: python scripts/orchestrators/ci_orchestrator.py --quick-test

      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: ci-results
          path: data_out/ci_orchestrator/
```

### Azure Pipelines Example

```yaml
trigger:
  - main

pool:
  vmImage: 'windows-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'

- script: pip install pyyaml pytest
  displayName: 'Install dependencies'

- script: python scripts/orchestrators/ci_orchestrator.py --validate-all
  displayName: 'Validate orchestrators'

- script: python scripts/orchestrators/ci_orchestrator.py --ci-pipeline
  displayName: 'Run CI pipeline'

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: 'data_out/ci_orchestrator'
    artifactName: 'ci-results'
```

## Auto-Scheduler Commands

### Schedule a Job

```powershell
# Daily at 2 AM
python .\scripts\auto_scheduler.py --schedule "daily_training" --workflow "daily_full_pipeline" --cron "0 2 * * *"

# Every 6 hours
python .\scripts\auto_scheduler.py --schedule "frequent_eval" --workflow "quick_validation" --cron "0 */6 * * *"

# Weekly on Sundays at midnight
python .\scripts\auto_scheduler.py --schedule "weekly_full" --workflow "weekly_comprehensive" --cron "0 0 * * 0"
```

### Manage Scheduled Jobs

```powershell
# List all jobs
python .\scripts\auto_scheduler.py --list

# Enable/disable job
python .\scripts\auto_scheduler.py --enable "daily_training"
python .\scripts\auto_scheduler.py --disable "daily_training"

# Remove job
python .\scripts\auto_scheduler.py --remove "daily_training"

# Check status
python .\scripts\auto_scheduler.py --status
```

### Run as Daemon

```powershell
# Start in foreground
python .\scripts\auto_scheduler.py --start

# With custom check interval (default 60 seconds)
python .\scripts\auto_scheduler.py --start --check-interval 30
```

**Note**: Install `croniter` for cron scheduling: `pip install croniter`

## Master Orchestrator Commands

### List Available Resources

```powershell
# List all orchestrators
python .\scripts\master_orchestrator.py --list-orchestrators

# List all workflows
python .\scripts\master_orchestrator.py --list-workflows

# Show current status
python .\scripts\master_orchestrator.py --status
```

### Run Workflows

```powershell
# Quick validation (dry-run all)
python .\scripts\master_orchestrator.py --workflow quick_validation

# Daily full pipeline
python .\scripts\master_orchestrator.py --workflow daily_full_pipeline

# Weekly comprehensive
python .\scripts\master_orchestrator.py --workflow weekly_comprehensive
```

### Run Individual Orchestrators

```powershell
# Run single orchestrator through master
python .\scripts\master_orchestrator.py --orchestrator autotrain
python .\scripts\master_orchestrator.py --orchestrator quantum_autorun
python .\scripts\master_orchestrator.py --orchestrator evaluation_autorun
```

### Daemon Mode

```powershell
# Run as background service (checks schedules every 60s)
python .\scripts\master_orchestrator.py --daemon

# Custom check interval
python .\scripts\master_orchestrator.py --daemon --check-interval 120
```

## CI Orchestrator Commands

### Validation

```powershell
# Validate all orchestrators (parallel, ~1 second)
python .\scripts\ci_orchestrator.py --validate-all
```

### Testing

```powershell
# Quick test (unit tests only)
python .\scripts\ci_orchestrator.py --quick-test

# Full test suite (unit + integration)
python .\scripts\ci_orchestrator.py --full-test
```

### Deployment

```powershell
# Prepare deployment artifacts
python .\scripts\ci_orchestrator.py --prepare-deployment
```

### Full Pipeline

```powershell
# Run complete CI/CD pipeline
python .\scripts\ci_orchestrator.py --ci-pipeline
```

**Steps**: Validation → Unit Tests → Dataset Validation → Code Quality → Security Scan → Integration Tests → Deployment Preparation

## Output Structure

```
data_out/
├── master_orchestrator/
│   ├── status.json                           # Global status
│   ├── quick_validation_<timestamp>.json     # Workflow results
│   └── <orchestrator_name>/
│       └── <timestamp>/
│           └── stdout.log                    # Execution logs
│
├── ci_orchestrator/
│   ├── ci_results.json                       # CI pipeline results
│   └── deployment_artifacts.json             # Deployment manifest
│
└── auto_scheduler/
    ├── schedule.json                         # Scheduled jobs config
    └── state.json                            # Scheduler state (last runs, etc.)
```

## Status JSON Schema

### Master Orchestrator Status

```json
{
  "generated_at": "2025-11-22T17:30:00Z",
  "orchestrators": [
    {
      "name": "autotrain",
      "script": "scripts/training/autotrain.py",
      "enabled": true,
      "schedule": "0 2 * * *",
      "priority": 1,
      "dependencies": [],
      "last_run": "20251122T173000Z",
      "last_status": "succeeded"
    }
  ],
  "workflows": [
    {
      "name": "quick_validation",
      "enabled": true,
      "trigger": "manual",
      "orchestrators": ["autotrain", "quantum_autorun", "evaluation_autorun"]
    }
  ],
  "resource_usage": {
    "cpu_percent": 25.3,
    "memory_percent": 45.8,
    "disk_percent": 62.1
  }
}
```

### CI Orchestrator Results

```json
{
  "generated_at": "2025-11-22T17:30:00Z",
  "total_steps": 7,
  "succeeded": 6,
  "failed": 0,
  "skipped": 1,
  "results": [
    {
      "name": "validate_orchestrators",
      "status": "succeeded",
      "duration_sec": 1.2,
      "critical": true
    }
  ]
}
```

### Auto-Scheduler State

```json
{
  "scheduler_running": true,
  "total_jobs": 3,
  "enabled_jobs": 2,
  "disabled_jobs": 1,
  "jobs": [
    {
      "name": "daily_training",
      "workflow": "daily_full_pipeline",
      "cron": "0 2 * * *",
      "enabled": true,
      "last_run": "2025-11-22T02:00:15Z",
      "last_status": "succeeded",
      "next_run": "2025-11-23 02:00:00",
      "run_count": 15,
      "consecutive_failures": 0
    }
  ]
}
```

## Advanced Features

### Dependency Management

Master orchestrator handles dependencies automatically:

```yaml
orchestrators:
  - name: evaluation_autorun
    dependencies: [autotrain, quantum_autorun]  # Wait for these
```

### Resource Limits

```yaml
resource_limits:
  max_concurrent_orchestrators: 2
  max_cpu_percent: 80
  max_memory_gb: 16
  pause_on_resource_exhaustion: true
```

### Auto-Retry Logic

```yaml
orchestrators:
  - name: autotrain
    retry_on_failure: 3  # Retry up to 3 times
    timeout_minutes: 240 # 4 hour timeout
```

### Failure Handling

Auto-scheduler disables jobs after consecutive failures:

```python
max_consecutive_failures: 3  # Disable after 3 failures
notify_on_failure: true      # Send notification
```

## Monitoring & Notifications

### Slack Integration (Placeholder)

```yaml
notifications:
  slack_enabled: true
  webhook_url: "${SLACK_WEBHOOK_URL}"
  notify_on_failure: true
  notify_on_success: false
```

### Email Notifications (Placeholder)

```yaml
notifications:
  email_enabled: true
  to: "${ADMIN_EMAIL}"
  notify_on_failure: true
  notify_on_degradation: true
```

## Troubleshooting

### Orchestrator Not Running

```powershell
# Check master orchestrator status
python .\scripts\master_orchestrator.py --status

# Check specific orchestrator
python .\scripts\autotrain.py --dry-run
```

### Scheduler Not Triggering

```powershell
# Install croniter
pip install croniter

# Check schedule syntax
python .\scripts\auto_scheduler.py --list

# Verify next_run time is set
```

### CI Pipeline Failures

```powershell
# Run individual steps
python .\scripts\ci_orchestrator.py --validate-all
python .\scripts\ci_orchestrator.py --quick-test

# Check results
type data_out\ci_orchestrator\ci_results.json
```

### Resource Exhaustion

Master orchestrator monitors resources (requires `psutil`):

```powershell
# Install psutil
pip install psutil

# Check status with resource usage
python .\scripts\master_orchestrator.py --status
```

## Best Practices

1. **Start with dry-run**: Always validate before execution
2. **Use CI orchestrator**: For pre-commit/pre-push validation
3. **Schedule wisely**: Avoid overlapping resource-intensive jobs
4. **Monitor logs**: Check `data_out/` for execution details
5. **Enable notifications**: Get alerts for failures
6. **Resource limits**: Set appropriate limits for your hardware
7. **Backup regularly**: Automated backups in `master_orchestrator.yaml`

## Integration Examples

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
python scripts/orchestrators/ci_orchestrator.py --validate-all
exit $?
```

### Continuous Deployment

```powershell
# Run after successful training
python .\scripts\ci_orchestrator.py --prepare-deployment

# Deploy if validation passes
if ($LASTEXITCODE -eq 0) {
    # Deploy to Azure Functions, etc.
}
```

### Performance Monitoring

```powershell
# Scheduled performance check
python .\scripts\auto_scheduler.py --schedule "perf_check" --workflow "quick_validation" --cron "*/30 * * * *"
```

## Future Enhancements

- [ ] Proper cron parser without croniter dependency
- [ ] Slack/Email notification implementation
- [ ] Web dashboard for monitoring
- [ ] Distributed execution across machines
- [ ] GPU resource aware scheduling
- [ ] Model performance tracking
- [ ] Automatic hyperparameter tuning integration
- [ ] Cost estimation and budgeting
- [ ] Rollback on deployment failure

## New Advanced Features

### Model Deployment with Quality Gates

**model_deployer.py** - Automatically deploy trained models with validation:

```powershell
# Scan for trained models and check quality gates
python .\scripts\model_deployer.py --scan

# Deploy best model with canary strategy
python .\scripts\model_deployer.py --deploy best --strategy canary

# Check deployment status
python .\scripts\model_deployer.py --status

# Rollback to previous version
python .\scripts\model_deployer.py --rollback v1_20251122_123456
```

**Features**:
- Quality gate validation (accuracy > 0.75, loss < 0.5)
- Model scoring and ranking
- Deployment strategies: direct, canary, blue-green
- Version tracking and rollback
- Model registry with metadata

### Real-Time Resource Monitoring

**resource_monitor.py** - Monitor system resources with alerts:

```powershell
# Capture single snapshot
python .\scripts\resource_monitor.py --snapshot

# Stream real-time monitoring (60s)
python .\scripts\resource_monitor.py --stream --duration 60

# View historical data (last 24 hours)
python .\scripts\resource_monitor.py --history --hours 24

# Export to CSV
python .\scripts\resource_monitor.py --export csv

# Set custom alert threshold
python .\scripts\resource_monitor.py --set-threshold cpu_percent 85
```

**Features**:
- CPU, memory, disk, GPU monitoring
- Threshold-based alerts
- Historical data collection (JSONL format)
- Export to CSV/JSON
- Integration with orchestrators

### Batch Model Evaluation

**batch_evaluator.py** - Parallel evaluation of multiple models:

```powershell
# Scan and evaluate all trained models
python .\scripts\batch_evaluator.py --scan-models --evaluate-all

# Compare specific models
python .\scripts\batch_evaluator.py --compare lora_v1 lora_v2 quantum_v1

# Export results to Markdown report
python .\scripts\batch_evaluator.py --export markdown --output report.md

# Export to JSON
python .\scripts\batch_evaluator.py --export json
```

**Features**:
- Parallel evaluation (ThreadPoolExecutor)
- Support for LoRA, Azure, OpenAI, Local, Quantum models
- Result aggregation and ranking
- Multi-format export (JSON, Markdown)
- Side-by-side comparison

### Multi-Format Results Export

**results_exporter.py** - Export orchestrator results to multiple formats:

```powershell
# Export autotrain results to CSV
python .\scripts\results_exporter.py --source autotrain --format csv

# Export quantum results to Markdown
python .\scripts\results_exporter.py --source quantum_autorun --format markdown

# Export all orchestrators to Excel
python .\scripts\results_exporter.py --all --format excel

# Compare orchestrators in HTML
python .\scripts\results_exporter.py --compare autotrain quantum_autorun --format html
```

**Supported formats**:
- JSON (machine-readable)
- CSV (spreadsheet import)
- Excel (requires openpyxl)
- Markdown (documentation)
- HTML (web reports)

### CI/CD Integration

**GitHub Actions workflow** - Automated CI on every commit:

`.github/workflows/ci-pipeline.yml` includes:
- Validation on push/PR
- Daily training runs (scheduled)
- Auto-deployment of best models
- Artifact uploads

**Trigger CI manually**:
```powershell
# Run full CI pipeline locally
python .\scripts\ci_orchestrator.py --ci-pipeline
```

**Git hooks** - Pre-commit validation:
```powershell
# Copy sample hook (manual installation)
# .git\hooks\pre-commit.sample contains validation logic
```

## Enhanced Orchestrator Integration

### Chain Orchestrators with Dependencies

Master orchestrator now supports more complex workflows:

```yaml
# master_orchestrator.yaml
workflows:
  - name: full_ml_pipeline
    description: "Complete ML pipeline with deployment"
    trigger: manual
    orchestrators:
      - autotrain          # Step 1: Train models
      - evaluation_autorun # Step 2: Evaluate models (depends on autotrain)
      - model_deploy       # Step 3: Deploy best model
    on_success:
      - deploy_best_model
      - send_notification
```

### Schedule Workflows with Cron

```powershell
# Schedule daily training at 2 AM
python .\scripts\auto_scheduler.py --schedule "daily_training" --workflow "daily_full_pipeline" --cron "0 2 * * *"

# Schedule evaluation every 6 hours
python .\scripts\auto_scheduler.py --schedule "eval_check" --workflow "quick_validation" --cron "0 */6 * * *"

# Enable/disable jobs
python .\scripts\auto_scheduler.py --disable daily_training
python .\scripts\auto_scheduler.py --enable daily_training

# Start scheduler daemon
python .\scripts\auto_scheduler.py --start --check-interval 300
```

### Batch Evaluate Multiple Models

```powershell
# Create batch evaluation config
# batch_eval_config.yaml:
evaluation_tasks:
  - model_id: lora_v1
    model_type: lora
    model_path: data_out/lora_training/lora_v1
    dataset: datasets/chat/mixed_chat
    metrics: [accuracy, perplexity, bleu]
    max_samples: 100

# Run batch evaluation
python .\scripts\batch_evaluator.py --config batch_eval_config.yaml
```

### Export Results to Multiple Formats

```powershell
# Export single orchestrator
python .\scripts\results_exporter.py --source autotrain --format markdown --output autotrain_report.md

# Export all orchestrators comparison
python .\scripts\results_exporter.py --all --format html --output comparison.html

# Filter by status
python .\scripts\results_exporter.py --source quantum_autorun --format csv --filter-status succeeded
```

## Related Documentation

- `AUTOTRAIN_README.md` - LoRA training orchestrator
- `QUANTUM_AUTORUN_README.md` - Quantum training orchestrator
- `EVALUATION_AUTORUN_README.md` - Model evaluation orchestrator
- `QUICK_REFERENCE.md` - Quick command reference
- `PRODUCTION_DEPLOYMENT_PLAN.md` - Deployment guide
