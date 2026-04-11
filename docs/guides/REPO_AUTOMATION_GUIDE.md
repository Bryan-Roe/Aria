# 🚀 Repository-Wide Automation Guide

Complete automation system for the entire Aria repository.

## Quick Start

```bash
# Start everything
./scripts/start_repo_automation.sh full

# Or use Python directly
python scripts/repo_automation.py --start --daemon

# Check status
./scripts/start_repo_automation.sh status

# Stop all
./scripts/start_repo_automation.sh stop
```

## Components (Current Architecture)

The automation system now uses a lightweight component registry with dynamic enabling and automatic dependency resolution. Some legacy scripts listed previously have been consolidated or made optional.

### 1. Aria Character Automation (`aria`)

- **What**: Aria web server + Aria-specific training loop + backend (Azure Functions) if available
- **Script**: `scripts/aria_automation.py`
- **Health Check Interval**: 60s
- **Auto-Restart**: Yes
- **Dependencies Auto-Installed**: `psutil`

### 2. Autonomous Training System (`training`)

- **What**: Continuous adaptive cycles (dataset discovery + optional download + distributed benchmark training + performance analysis)
- **Script**: `scripts/autonomous_training_orchestrator.py`
- **Health Check Interval**: 5min
- **Auto-Restart**: Yes
- **Integrated**: Dataset auto-discovery (replaces standalone dataset component)
- **Dependencies Auto-Installed**: `pandas`, `torch`, `numpy`, `pyyaml`

### 3. Quantum Computing Workflows (`quantum`)

- **What**: Quantum ML / job submission orchestrator
- **Script**: `scripts/quantum_autorun.py`
- **Enabled When**: `config/quantum/quantum_autorun.yaml` (falls back to root `quantum_autorun.yaml`)
- **Auto-Restart**: No (jobs are typically batch / scheduled)
- **Dependencies**: (Add Azure Quantum SDK when environment configured)

### 4. Model Evaluation System (`evaluation`)

- **What**: Batch model evaluation against curated test sets
- **Script**: `scripts/evaluation_autorun.py`
- **Enabled When**: `config/evaluation/evaluation_autorun.yaml` (falls back to root `evaluation_autorun.yaml`)
- **Dependencies**: `training` component must be running
- **Auto-Restart**: No (designed for batch cycles)
- **Dependencies Auto-Installed**: `scikit-learn`, `numpy`, `matplotlib`, `seaborn`

### 5. Status Dashboard (`monitoring` / optional)

- **What**: Web dashboard for live status (optional)
- **Script**: `scripts/status_dashboard.py`
- **Enabled**: Manually (disabled by default)
- **Dependencies Auto-Installed**: `Flask`, `flask-socketio`, `python-socketio`

### 6. Backup Manager (`backup` / optional)

- **What**: Point-in-time backups of adapters, configs, logs
- **Script**: `scripts/backup_manager.py`
- **Enabled**: Manually (disabled by default; invoke on-demand or via cron)
- **Supports**: Incremental backups (hardlinks) + compression + manifest tracking

### Deprecated / Integrated

- **Dataset Auto-Discovery**: Integrated into `training` component (no separate process)
- **System Health Monitor**: Basic health checking performed internally; full external monitor can be added if needed.

Each component’s dependency set is verified just-in-time; missing packages are installed automatically via `pip` before the component starts. Failures are recorded and the component will not start until resolved (preventing restart loops caused purely by missing dependencies).

## Automatic Dependency Resolution & Conditional Enabling

### How It Works

1. On startup or when starting a component, required packages listed in `ComponentConfig.required_packages` are imported.
2. Missing modules trigger automatic `pip install` attempts.
3. Post-install imports are re-validated; any remaining failures are logged and block component start.
4. Dependency health per component appears in `status.json` under `dependency_status` and in `--status` output with an icon:
   - `🧩` Dependencies satisfied
   - `⚠️` Dependency issue (component may not have started)

### Conditional Enabling

Components are auto-enabled based on presence of configuration files:

- `quantum`: `config/quantum/quantum_autorun.yaml` exists (or root fallback); default disabled.
- `evaluation`: `config/evaluation/evaluation_autorun.yaml` exists (or root fallback); default disabled.
- `training`: always enabled.
- `aria`: always enabled.
- `monitoring`: manual enablement only.
- `backup`: manual enablement only.
- `datasets`: integrated into `training`; no separate component.

### Adding New Components

Update `scripts/repo_automation.py` and include a `required_packages` list. Example:

```python
"my_component": ComponentConfig(
    name="My Custom Service",
    script="scripts/my_service.py",
    command=["python3", "scripts/my_service.py"],
    auto_restart=True,
    health_check_interval=120,
    required_packages=["requests", "rich"],
),
```

### Handling Heavy Dependencies (e.g., `torch`)

- Install attempts are synchronous; large packages may take time.
- To avoid blocking other components, start with smaller ones (`aria`) first or pre-install heavy libs via `pip install -r requirements.txt`.
- If you need GPU variants, pre-install manually (automation will skip if already present).

### Failure Recovery

- If dependency installation fails, a concise error is appended to `errors` in `status.json`.
- Fix by manually installing or adjusting network/proxy settings, then restart the component.

### Security & Safety

- Only standard `pip install <package>` commands are executed—no arbitrary shell code.
- Consider pinning versions in `requirements.txt` for reproducibility in production environments.

## Usage Modes

### Full Automation (Production)

```bash
# Interactive
./scripts/start_repo_automation.sh

# Command line
./scripts/start_repo_automation.sh full

# Background
./scripts/start_repo_automation.sh full --background
```

Starts all 7 components with health monitoring and auto-recovery.

### Aria Only

```bash
./scripts/start_repo_automation.sh aria
```

Just the Aria character automation (server + training).

### Training Pipeline

```bash
./scripts/start_repo_automation.sh training
```

Training + evaluation only.

### Custom Selection

```bash
# Interactive
./scripts/start_repo_automation.sh
# Choose option 4

# Command line
./scripts/start_repo_automation.sh components aria,training,quantum
```

## Monitoring

### Check Status

```bash
# Using wrapper script
./scripts/start_repo_automation.sh status

# Using Python directly
python scripts/repo_automation.py --status
```

Output shows:

- Uptime
- Components running/stopped
- Health check count
- Recent errors

### Status File

```bash
cat data_out/repo_automation/status.json
```

Machine-readable status including:

- Start time
- Uptime in seconds
- Component states
- Error log

### Logs

```bash
# Automation log
tail -f data_out/repo_automation/automation.log

# Individual component logs
tail -f data_out/aria_automation/*.log
tail -f data_out/autotrain/*.log
```

## Operational Smoke Flow

Use this sequence after config or orchestrator changes.

```bash
# 1) Repository integration smoke (local fast gate)
python scripts/integration_smoke.py --json

# 2) CI smoke stage parity check
python scripts/ci_orchestrator.py --integration-smoke

# 3) Focused integration contract tests
python scripts/ci_orchestrator.py --integration-contract-tests

# 4) Core orchestrator dry-run checks
python scripts/ci_orchestrator.py --validate-all

# 5) Unified runtime view (optional continuous watch)
python scripts/status_dashboard.py --watch
```

Shortcut in VS Code: run task `integration:contract-gate` from `.vscode/tasks.json` to execute steps 1-4 in one command.

Shell shortcut: `bash ./scripts/integration_contract_gate.sh` (add `--strict-endpoints` to require local Functions host).

If step 1 fails, fix integration wiring first. If step 1 passes but step 2 or 3 fails, fix CI parity or contract regressions before merging.

## Production Deployment

### Option 1: Systemd Service

Create `/etc/systemd/system/aria-repo-automation.service`:

```ini
[Unit]
Description=Aria Repository Automation
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/Aria
ExecStart=/usr/bin/python3 /path/to/Aria/scripts/repo_automation.py --start --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable aria-repo-automation
sudo systemctl start aria-repo-automation
sudo systemctl status aria-repo-automation
```

### Option 2: Cron (Schedule-Based)

Add to crontab:

```bash
# Full automation every 30 minutes
*/30 * * * * cd /path/to/Aria && ./scripts/start_repo_automation.sh full --background

# Or specific components
0 */6 * * * cd /path/to/Aria && ./scripts/start_repo_automation.sh training --background
```

### Option 3: Docker/Container

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y func-cli

CMD ["python3", "scripts/repo_automation.py", "--start", "--daemon"]
```

## Configuration

### Component Settings

Edit `scripts/repo_automation.py`:

```python
ComponentConfig(
    name="Your Component",
    script="scripts/your_script.py",
    command=["python3", "scripts/your_script.py", "--continuous"],
    auto_restart=True,
    health_check_interval=300,  # seconds
    dependencies=["other_component"],
)
```

### Environment Variables

```bash
# Azure Functions
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"

# Database
export QAI_DB_CONN="your-connection-string"

# Cosmos DB
export QAI_ENABLE_COSMOS=true
export COSMOS_ENDPOINT="your-endpoint"
export COSMOS_KEY="your-key"
```

## Troubleshooting

### Component Won't Start

```bash
# Check dependencies
python scripts/repo_automation.py --status

# Manual test
python scripts/aria_automation.py --help

# Check logs
tail -f data_out/repo_automation/automation.log
```

### Auto-Restart Loop

If a component keeps restarting:

1. Check component-specific logs in `data_out/<component>/`
2. Disable auto-restart: Edit `scripts/repo_automation.py`, set `auto_restart=False`
3. Test component manually

### High Resource Usage

```bash
# Check monitoring
tail -f data_out/system_health_check/health.log

# Disable heavy components
./scripts/start_repo_automation.sh components aria,monitoring

# Adjust health check intervals
# Edit scripts/repo_automation.py, increase health_check_interval
```

### Stopping Stuck Processes

```bash
# Graceful stop
./scripts/start_repo_automation.sh stop

# Force kill
pkill -f repo_automation.py
pkill -f aria_automation.py
pkill -f autotrain.py
```

## Integration with Master Orchestrator

The repo automation works with the existing master orchestrator:

```bash
# Master orchestrator runs scheduled workflows
python scripts/master_orchestrator.py --schedule

# Repo automation provides continuous operation
python scripts/repo_automation.py --start --daemon
```

Use both together:

- **Master Orchestrator**: Scheduled batch jobs (daily training runs, evaluations)
- **Repo Automation**: Continuous services (Aria server, monitoring, backups)

## Advanced Features

### Custom Components

Add to `scripts/repo_automation.py`:

```python
"your_component": ComponentConfig(
    name="Your Custom Component",
    script="scripts/your_script.py",
    command=["python3", "scripts/your_script.py", "--daemon"],
    auto_restart=True,
    health_check_interval=300,
),
```

### Notification Hooks

Add notification on failures:

```python
def on_component_failure(component_name: str):
    # Send email/Slack/Teams notification
    pass
```

### Backup to Cloud

Edit `scripts/backup_manager.py`:

```python
def upload_to_cloud(backup_path: Path):
    # Upload to Azure Blob Storage / AWS S3
    pass
```

## Best Practices

1. **Start Small**: Test with `aria` component first, then add more
2. **Monitor Logs**: Keep an eye on logs during first 24 hours
3. **Resource Limits**: Set resource limits in systemd service
4. **Backup First**: Create manual backup before enabling automation
5. **Test Recovery**: Manually stop components to test auto-restart
6. **Document Changes**: Update this guide when adding custom components

## Support

- **Main Docs**: [README.md](../../README.md)
- **Aria Automation**: [ARIA_AUTOMATION_GUIDE.md](ARIA_AUTOMATION_GUIDE.md)
- **Master Orchestrator**: `scripts/master_orchestrator.py --help`
- **Component Docs**: See individual script help messages

## License

Same as repository - see [README.md](../../README.md)
