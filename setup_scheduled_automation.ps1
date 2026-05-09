# Setup Scheduled Automation for Aria
# This script creates a Windows Task Scheduler job to run automation automatically

param(
    [string]$ScheduleTime = "02:00",  # 2 AM by default
    [string]$Frequency = "Daily",      # Daily by default
    [switch]$Hourly,                   # Run every hour if specified
    [switch]$EveryXMinutes,            # Run every X minutes if specified
    [int]$Minutes = 30                 # Default to every 30 minutes
)

# Require admin privileges
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: This script requires Administrator privileges" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again" -ForegroundColor Yellow
    exit 1
}

$WorkspaceRoot = "c:\Users\Bryan\Aria"
$TaskName = "Aria Automation"
$ScriptPath = Join-Path $WorkspaceRoot "run_automation.py"
$PythonPath = "C:\Users\Bryan\.local\bin\python3.14.exe"
$LogPath = Join-Path $WorkspaceRoot "logs\automation.log"

# Create logs directory if it doesn't exist
$LogDir = Split-Path -Parent $LogPath
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "Created logs directory: $LogDir" -ForegroundColor Green
}

Write-Host "Aria Automation Scheduler Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Found existing task: $TaskName" -ForegroundColor Yellow
    $Response = Read-Host "Replace existing task? (Y/N)"
    
    if ($Response -eq "Y" -or $Response -eq "y") {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Task removed" -ForegroundColor Green
    } else {
        Write-Host "Keeping existing task" -ForegroundColor Yellow
        & schtasks /query /tn $TaskName /fo list
        exit 0
    }
}

# Create task action (what to run)
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkspaceRoot

# Create task trigger based on frequency
if ($Hourly) {
    Write-Host "Setting frequency: Every hour" -ForegroundColor Cyan
    $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddHours(1) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)
} elseif ($EveryXMinutes) {
    Write-Host "Setting frequency: Every $Minutes minutes" -ForegroundColor Cyan
    $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes($Minutes) -RepetitionInterval (New-TimeSpan -Minutes $Minutes) -RepetitionDuration (New-TimeSpan -Days 3650)
} else {
    Write-Host "Setting frequency: Daily at $ScheduleTime" -ForegroundColor Cyan
    $Hour = [int]$ScheduleTime.Split(':')[0]
    $Min = [int]$ScheduleTime.Split(':')[1]
    $Trigger = New-ScheduledTaskTrigger -Daily -At "$($Hour):$($Min)"
}

# Create task settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopOnIdleEnd `
    -RunOnlyIfNetworkAvailable:$false `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

# Create the scheduled task
Write-Host ""
Write-Host "Creating scheduled task..." -ForegroundColor Yellow

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Aria Automation Runner - Automatically runs tests, validation, and environment checks" `
        -Force | Out-Null
    
    Write-Host "✓ Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Task Name: $TaskName"
    Write-Host "  Script: $ScriptPath"
    Write-Host "  Python: $PythonPath"
    Write-Host "  Working Dir: $WorkspaceRoot"
    Write-Host ""
    
    # Show task info
    Write-Host "Current Schedule:" -ForegroundColor Cyan
    Get-ScheduledTask -TaskName $TaskName | Select-Object -Property TaskName, State | Format-Table -AutoSize
    
    $TaskInfo = Get-ScheduledTask -TaskName $TaskName
    $TaskInfo.Triggers | ForEach-Object {
        Write-Host "  Trigger: $($_.CimClass.CimClassName)" -ForegroundColor Cyan
        if ($_.StartBoundary) {
            Write-Host "    Start Time: $($_.StartBoundary)"
        }
        if ($_.Repetition.Interval) {
            Write-Host "    Repeat Every: $($_.Repetition.Interval)"
        }
    }
    
    Write-Host ""
    Write-Host "Next Run:" -ForegroundColor Cyan
    $NextRun = (Get-ScheduledTask -TaskName $TaskName).NextRunTime
    if ($NextRun) {
        Write-Host "  $NextRun" -ForegroundColor Green
    } else {
        Write-Host "  Will be set on next trigger" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "✗ Error creating task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ Scheduled automation setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  View task:    schtasks /query /tn 'Aria Automation' /fo list /v"
Write-Host "  Run now:      schtasks /run /tn 'Aria Automation'"
Write-Host "  Delete task:  schtasks /delete /tn 'Aria Automation' /f"
Write-Host "  View logs:    Get-Content '$LogPath' -Tail 50"
