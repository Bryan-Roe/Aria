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

## Components

### 1. Aria Character Automation

- **What**: Aria web server + continuous training
- **Script**: `scripts/aria_automation.py`
- **Health Check**: Every 60s
- **Auto-Restart**: Yes

### 2. LoRA Training Pipeline

- **What**: Automated LoRA fine-tuning with dataset rotation
- **Script**: `scripts/autotrain.py`
- **Health Check**: Every 5min
- **Auto-Restart**: Yes

### 3. Quantum Computing Workflows

- **What**: Quantum ML pipelines and job management
- **Script**: `scripts/quantum_autorun.py`
- **Health Check**: Every 10min
- **Auto-Restart**: Yes

### 4. Model Evaluation System

- **What**: Continuous evaluation of trained models
- **Script**: `scripts/evaluation_autorun.py`
- **Dependencies**: Training pipeline
- **Health Check**: Every 5min
- **Auto-Restart**: Yes

### 5. Dataset Auto-Discovery

- **What**: Automatic dataset collection from OpenML/HuggingFace/Kaggle
- **Script**: `scripts/collect_more_datasets.py`
- **Health Check**: Every 1hr
- **Auto-Restart**: Yes

### 6. System Health Monitor

- **What**: Resource monitoring, alerts, auto-recovery
- **Script**: `scripts/system_health_check.py`
- **Health Check**: Every 60s
- **Auto-Restart**: Yes

### 7. Backup Manager

- **What**: Automated backups of models, datasets, configs
- **Script**: `scripts/backup_manager.py`
- **Schedule**: Daily
- **Retention**: 30 days

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

- **Main Docs**: [README.md](../README.md)
- **Aria Automation**: [ARIA_AUTOMATION_GUIDE.md](ARIA_AUTOMATION_GUIDE.md)
- **Master Orchestrator**: `scripts/master_orchestrator.py --help`
- **Component Docs**: See individual script help messages

## License

Same as repository - see [LICENSE](../LICENSE)
