# Aria Automation - Deployment Guide

Complete guide for automating Aria AI character platform with continuous operation, training, and monitoring.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Automation Modes](#automation-modes)
- [Background Service Setup](#background-service-setup)
- [Systemd Integration (Linux)](#systemd-integration-linux)
- [Cron Integration](#cron-integration)
- [Master Orchestrator Integration](#master-orchestrator-integration)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Interactive Mode

```bash
# Start interactive menu
./scripts/start_aria.sh
```

### Command Line Mode

```bash
# Full stack (server + backend + training + monitoring)
./scripts/start_aria.sh full

# Server only
./scripts/start_aria.sh server

# Training only (continuous)
./scripts/start_aria.sh training

# Single training cycle
./scripts/start_aria.sh training --once

# Background mode
./scripts/start_aria.sh full --background

# Check status
./scripts/start_aria.sh status

# Stop all
./scripts/start_aria.sh stop
```

### Direct Python Invocation

```bash
# Full automation
python3 scripts/aria_automation.py --mode full

# Server only
python3 scripts/aria_automation.py --mode server

# Training once
python3 scripts/aria_automation.py --mode training --once

# Check status
python3 scripts/aria_automation.py --status

# Stop all processes
python3 scripts/aria_automation.py --stop
```

---

## 🎯 Automation Modes

### 1. Full Stack Mode (`--mode full`)

**Includes:**

- ✅ Aria web server (port 8080)
- ✅ Azure Functions backend (port 7071)
- ✅ Continuous training (every 30 minutes)
- ✅ Health monitoring (every 60 seconds)
- ✅ Auto-recovery on failures

**Best for:** Production deployment, 24/7 operation

**Usage:**

```bash
python3 scripts/aria_automation.py --mode full
```

**Endpoints:**

- Aria Interface: `http://localhost:8080`
- Auto-Execute: `http://localhost:8080/auto-execute.html`
- Backend API: `http://localhost:7071/api/ai/status`

---

### 2. Server Only Mode (`--mode server`)

**Includes:**

- ✅ Aria web server (port 8080)
- ✅ Health monitoring
- ❌ No training
- ❌ No backend

**Best for:** Development, UI testing, demos

**Usage:**

```bash
python3 scripts/aria_automation.py --mode server
```

---

### 3. Training Only Mode (`--mode training`)

**Includes:**

- ✅ Continuous training cycles
- ✅ Dataset monitoring
- ❌ No web server
- ❌ No backend

**Best for:** Background training, batch processing

**Usage:**

```bash
# Continuous training
python3 scripts/aria_automation.py --mode training

# Single cycle
python3 scripts/aria_automation.py --mode training --once
```

---

## 🌐 Background Service Setup

### Using nohup (Simple)

```bash
# Start in background
nohup python3 scripts/aria_automation.py --mode full \
    > data_out/aria_automation/aria.log 2>&1 &

# Save PID
echo $! > data_out/aria_automation/aria.pid

# Check status
python3 scripts/aria_automation.py --status

# Stop
kill $(cat data_out/aria_automation/aria.pid)
```

### Using screen (Recommended for SSH)

```bash
# Start new screen session
screen -S aria

# Run automation
python3 scripts/aria_automation.py --mode full

# Detach: Ctrl+A, then D

# Reattach
screen -r aria

# List sessions
screen -ls
```

### Using tmux

```bash
# Start new session
tmux new -s aria

# Run automation
python3 scripts/aria_automation.py --mode full

# Detach: Ctrl+B, then D

# Reattach
tmux attach -t aria

# List sessions
tmux ls
```

---

## 🐧 Systemd Integration (Linux)

### 1. Install Service

```bash
# Copy service file
sudo cp config/aria_automation.service /etc/systemd/system/

# Edit with your username and paths
sudo nano /etc/systemd/system/aria_automation.service

# Update these lines:
# User=YOUR_USERNAME
# Group=YOUR_USERNAME
# WorkingDirectory=/path/to/Aria

# Reload systemd
sudo systemctl daemon-reload
```

### 2. Configure Service

Edit `/etc/systemd/system/aria_automation.service`:

```ini
[Service]
User=bryan
Group=bryan
WorkingDirectory=/workspaces/Aria

# Choose mode: full, server, or training
ExecStart=/usr/bin/python3 /workspaces/Aria/scripts/aria_automation.py --mode full
```

### 3. Start Service

```bash
# Enable on boot
sudo systemctl enable aria_automation

# Start now
sudo systemctl start aria_automation

# Check status
sudo systemctl status aria_automation

# View logs
sudo journalctl -u aria_automation -f

# Stop service
sudo systemctl stop aria_automation

# Restart service
sudo systemctl restart aria_automation
```

### 4. Service Management

```bash
# Check if running
sudo systemctl is-active aria_automation

# Check if enabled on boot
sudo systemctl is-enabled aria_automation

# Disable on boot
sudo systemctl disable aria_automation

# View recent logs
sudo journalctl -u aria_automation -n 50

# Follow logs in real-time
sudo journalctl -u aria_automation -f
```

---

## ⏰ Cron Integration

For periodic training without continuous operation:

### 1. Edit Crontab

```bash
crontab -e
```

### 2. Add Scheduled Jobs

```cron
# Run single training cycle every 30 minutes
*/30 * * * * /usr/bin/python3 /workspaces/Aria/scripts/aria_automation.py --mode training --once >> /workspaces/Aria/data_out/aria_automation/cron.log 2>&1

# Start server at boot
@reboot /usr/bin/python3 /workspaces/Aria/scripts/aria_automation.py --mode server >> /workspaces/Aria/data_out/aria_automation/server.log 2>&1

# Daily health check at 2 AM
0 2 * * * /usr/bin/python3 /workspaces/Aria/scripts/aria_automation.py --status >> /workspaces/Aria/data_out/aria_automation/status.log 2>&1

# Weekly full training on Sundays at 3 AM
0 3 * * 0 /workspaces/Aria/scripts/start_aria.sh training --once >> /workspaces/Aria/data_out/aria_automation/weekly.log 2>&1
```

### 3. View Cron Logs

```bash
# View cron log
tail -f data_out/aria_automation/cron.log

# List current crontab
crontab -l

# Remove all cron jobs
crontab -r
```

---

## 🎼 Master Orchestrator Integration

Aria automation integrates with the master orchestrator system.

### Configuration

Edit `config/master_orchestrator.yaml`:

```yaml
orchestrators:
  - name: aria_automation
    script: scripts/aria_automation.py
    enabled: true
    schedule: "*/30 * * * *"  # Every 30 minutes
    priority: 5
    retry_on_failure: 3
    timeout_minutes: 15
    dependencies: []
    flags:
      mode: training
      once: true

workflows:
  # Aria full stack (runs continuously)
  - name: aria_full_stack
    enabled: false  # Enable for 24/7 operation
    trigger: "manual"
    orchestrators:
      - aria_automation
    flags:
      mode: full
    on_success:
      - log_result
    on_failure:
      - restart_aria
      - notify_admin
```

### Running via Master Orchestrator

```bash
# Start master orchestrator
python3 scripts/master_orchestrator.py --workflow aria_full_stack

# Check status
python3 scripts/master_orchestrator.py --status

# Run as daemon
python3 scripts/master_orchestrator.py --daemon
```

---

## 📊 Monitoring & Health Checks

### Status Check

```bash
# View current status
python3 scripts/aria_automation.py --status
```

**Output:**

```
================================================================================
🤖 Aria Automation Status
================================================================================
Mode: full
Started: 2025-11-29T10:30:00
Uptime: 2:15:30
Training Cycles: 4

Components:
  - Aria Server: ✅ Running
  - Functions Backend: ✅ Running
  - Training: ✅ Active

Processes:
  - aria_server (PID 12345): running
  - functions_backend (PID 12346): running
================================================================================
```

### Status File

Status is saved to: `data_out/aria_automation/status.json`

```json
{
  "mode": "full",
  "started": "2025-11-29T10:30:00",
  "uptime_seconds": 8130,
  "server_running": true,
  "backend_running": true,
  "training_active": true,
  "last_health_check": "2025-11-29T12:45:30",
  "processes": [...],
  "training_cycles": 4,
  "errors": []
}
```

### Health Check Endpoints

**Aria Server:**

```bash
curl http://localhost:8080
```

**Functions Backend:**

```bash
curl http://localhost:7071/api/ai/status
```

### Monitoring Script

Create custom monitoring:

```bash
#!/bin/bash
# Check Aria health every 5 minutes

while true; do
    STATUS=$(python3 scripts/aria_automation.py --status 2>&1)

    if [[ $STATUS == *"Running"* ]]; then
        echo "$(date): ✅ Aria healthy"
    else
        echo "$(date): ❌ Aria unhealthy"
        # Send alert (email, Slack, etc.)
    fi

    sleep 300
done
```

---

## 🔧 Troubleshooting

### Issue: Port Already in Use

**Problem:** `Port 8080 already in use`

**Solution:**

```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or stop via automation
python3 scripts/aria_automation.py --stop
```

### Issue: Training Fails

**Problem:** Training cycles fail repeatedly

**Solutions:**

1. Check dataset exists:

   ```bash
   ls datasets/chat/aria_movement/
   ```

2. Validate dataset:

   ```bash
   python3 scripts/validate_datasets.py --category chat
   ```

3. Check logs:

   ```bash
   tail -f data_out/aria_automation/aria_automation.log
   ```

4. Run single training manually:

   ```bash
   python3 scripts/aria_quick_train.py
   ```

### Issue: Server Won't Start

**Problem:** Aria server fails to start

**Solutions:**

1. Check dependencies:

   ```bash
   cd aria_web
   pip3 install -r requirements.txt
   ```

2. Test server manually:

   ```bash
   cd aria_web
   python3 server.py
   ```

3. Check for errors:

   ```bash
   python3 aria_web/server.py 2>&1 | tee server_debug.log
   ```

### Issue: Backend Not Starting

**Problem:** Azure Functions backend won't start

**Solutions:**

1. Install Functions Core Tools:

   ```bash
   # Windows
   npm install -g azure-functions-core-tools@4

   # Linux
   curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
   sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
   sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/dotnetdev.list'
   sudo apt update
   sudo apt install azure-functions-core-tools-4
   ```

2. Check Functions installation:

   ```bash
   func --version
   ```

3. Test Functions manually:

   ```bash
   func host start
   ```

### Issue: Process Zombies

**Problem:** Stopped processes remain in status

**Solution:**

```bash
# Clean PID file
rm data_out/aria_automation/processes.json

# Force stop all
python3 scripts/aria_automation.py --stop

# Kill any remaining processes
pkill -f "aria_automation"
pkill -f "aria.*server.py"
```

### Issue: High Memory Usage

**Problem:** Automation consumes too much memory

**Solutions:**

1. Reduce training frequency (edit config)
2. Use `--once` flag for training
3. Limit training samples:

   ```bash
   # Edit aria_quick_train.py
   # Set max_train_samples to lower value
   ```

### View Logs

```bash
# Automation logs
tail -f data_out/aria_automation/aria_automation.log

# Server logs
tail -f data_out/aria_automation/server.log

# Training logs
tail -f data_out/lora_training/*/last_run.json
```

---

## 📝 Best Practices

### 1. Production Deployment

- ✅ Use systemd for auto-restart
- ✅ Enable monitoring alerts
- ✅ Set resource limits
- ✅ Regular backups
- ✅ Log rotation

### 2. Development

- ✅ Use `--mode server` for testing
- ✅ Use `--once` for training tests
- ✅ Monitor logs in real-time
- ✅ Keep test datasets small

### 3. Resource Management

- ✅ Limit concurrent processes
- ✅ Schedule training during off-hours
- ✅ Monitor disk space
- ✅ Clean old outputs regularly

### 4. Security

- ✅ Run as non-root user
- ✅ Set proper file permissions
- ✅ Firewall rules for ports
- ✅ API key management

---

## 📚 Additional Resources

- **Main README**: `README.md`
- **Aria Web Docs**: `aria_web/README.md`
- **Auto-Execute Guide**: `aria_web/AUTO-EXECUTE.md`
- **Training Guide**: `scripts/README.md`
- **Master Orchestrator**: `ADVANCED_AUTOMATION.md`

---

## 🆘 Support

If issues persist:

1. Check status: `python3 scripts/aria_automation.py --status`
2. View logs: `tail -f data_out/aria_automation/*.log`
3. Test components individually
4. Review error messages in status.json
5. Open GitHub issue with logs

---

**Last Updated:** November 29, 2025
**Version:** 1.0.0
