# Automatic Automation Setup Guide

Your Aria workspace now has **automatic code execution** set up. There are three ways to run automation:

## 1. Manual Execution (On-Demand)

Run on-demand whenever you want:

### Windows
```cmd
cd c:\Users\Bryan\Aria
run_automation.bat
```

### PowerShell
```powershell
cd c:\Users\Bryan\Aria
.\run_automation.ps1
```

### Python
```bash
cd c:\Users\Bryan\Aria
python3.14 run_automation.py
```

---

## 2. Scheduled Execution (Daily at 2 AM)

Automatically runs every day at 2:00 AM using Windows Task Scheduler.

**Status:** ✓ Already configured and active

**What it does:**
- Validates environment
- Checks dependencies  
- Runs test suite
- Performs validation
- Logs all output

**Useful commands:**
```powershell
# View task details
Get-ScheduledTask -TaskName "Aria Automation"

# Run the task now
Start-ScheduledTask -TaskName "Aria Automation"

# View recent runs
Get-ScheduledTaskInfo -TaskName "Aria Automation"

# Delete the task
Unregister-ScheduledTask -TaskName "Aria Automation" -Confirm:$false
```

**View logs from scheduled runs:**
```powershell
# View last 50 lines of automation log
Get-Content "c:\Users\Bryan\Aria\logs\automation.log" -Tail 50
```

---

## 3. Continuous Background Automation

Runs automation continuously in the background at configurable intervals.

### Start Continuous Daemon

**Every 60 minutes (default):**
```bash
python3.14 run_continuous_automation.py
```

**Every 30 minutes:**
```bash
python3.14 run_continuous_automation.py --interval 30
```

**Every 15 minutes:**
```bash
python3.14 run_continuous_automation.py --interval 15
```

### Features
- Configurable interval (default: 60 minutes)
- Graceful shutdown (Ctrl+C)
- Detailed logging
- Non-blocking sleep (responsive to termination)
- Cycle counter and timestamps

### Run in Background (PowerShell)

Start and leave running:
```powershell
Start-Job -FilePath "C:\Users\Bryan\.local\bin\python3.14.exe" -ArgumentList "c:\Users\Bryan\Aria\run_continuous_automation.py"
```

Monitor background jobs:
```powershell
Get-Job | Where-Object {$_.Name -like "*continuous*"}
```

Stop background job:
```powershell
Stop-Job -Name JobName
```

### Run as Windows Service (Advanced)

Create a Windows service that runs the continuous automation:

```powershell
# Install as service (requires NSSM - Non-Sucking Service Manager)
nssm install "Aria Automation Service" `
    "C:\Users\Bryan\.local\bin\python3.14.exe" `
    "c:\Users\Bryan\Aria\run_continuous_automation.py --interval 30"

# Start the service
nssm start "Aria Automation Service"

# View service logs
nssm dump "Aria Automation Service"
```

---

## Logging

All automation runs are logged for debugging and monitoring.

**Log locations:**
- Scheduled tasks: `c:\Users\Bryan\Aria\logs\automation.log`
- Continuous daemon: `c:\Users\Bryan\Aria\logs\continuous_automation.log`

**View recent logs:**
```powershell
# Last 20 lines
Get-Content "c:\Users\Bryan\Aria\logs\*.log" -Tail 20

# Continuous tail (live view)
# PowerShell 7+:
Get-Content "c:\Users\Bryan\Aria\logs\continuous_automation.log" -Wait -Tail 20

# Or use your editor's "tail" feature
```

---

## Configuration

### Change Scheduled Time

Edit the trigger:
```powershell
$Trigger = New-ScheduledTaskTrigger -Daily -At "03:00"  # 3 AM instead of 2 AM
Set-ScheduledTask -TaskName "Aria Automation" -Trigger $Trigger
```

### Disable Scheduled Task (Keep it but don't run)
```powershell
Disable-ScheduledTask -TaskName "Aria Automation"
```

### Enable Scheduled Task
```powershell
Enable-ScheduledTask -TaskName "Aria Automation"
```

---

## Troubleshooting

### Task Not Running

Check these things:
1. Task is enabled: `Get-ScheduledTask -TaskName "Aria Automation" | Select-Object State`
2. Python path is correct: `Test-Path "C:\Users\Bryan\.local\bin\python3.14.exe"`
3. Script exists: `Test-Path "c:\Users\Bryan\Aria\run_automation.py"`
4. Run manually to test: `python3.14 run_automation.py`

### Python Not Found

```powershell
# Find Python
Get-Command python3.14
Get-Command python3
Get-Command python
```

If not found, install Python or update PATH environment variable.

### Permission Denied

Run PowerShell as Administrator:
```powershell
Start-Process powershell -Verb RunAs
```

### View Task Errors

```powershell
# Get detailed task history
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" -MaxEvents 50 | 
    Where-Object {$_.Message -like "*Aria Automation*"} |
    Select-Object TimeCreated, Message
```

---

## Monitoring

### Check Task Status
```powershell
Get-ScheduledTask -TaskName "Aria Automation" | 
    Select-Object TaskName, State, LastRunTime, LastTaskResult
```

### View Last Run Output
```powershell
Get-ScheduledTask -TaskName "Aria Automation" -Verbose
```

### Monitor Continuous Daemon
```powershell
# Watch logs in real-time (PowerShell 7.0+)
Get-Content "c:\Users\Bryan\Aria\logs\continuous_automation.log" -Wait -Tail 30
```

---

## Summary

| Method | Frequency | Setup | Use Case |
| -------- | ----------- | ------- | ---------- |
| **Manual** | On-demand | None | Quick testing |
| **Scheduled** | Daily at 2 AM | ✓ Done | Regular maintenance |
| **Continuous** | Every X minutes | Start script | Real-time monitoring |

**Recommended:**
- Use **Scheduled** for daily maintenance
- Use **Continuous** for development/monitoring
- Use **Manual** for testing/verification

---

## Next Steps

1. ✓ Scheduled automation is active
2. Start continuous daemon: `python3.14 run_continuous_automation.py`
3. Monitor logs: `Get-Content "c:\Users\Bryan\Aria\logs\*.log" -Tail 20 -Wait`
4. View task status: `Get-ScheduledTask -TaskName "Aria Automation"`
