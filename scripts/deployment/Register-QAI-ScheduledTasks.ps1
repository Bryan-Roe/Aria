param(
    [string]$DailyAt = "02:00",
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function New-Task {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Name,
        [string]$ScheduleArgs,
        [string]$Command
    )
    $taskName = "\\QAI\$Name"
    $taskArgs = @(
        '/Create','/TN', $taskName,
        '/TR', $Command,
        '/F','/RL','HIGHEST','/SC'
    ) + $ScheduleArgs.Split(' ')

    $cmd = 'schtasks.exe ' + ($taskArgs | ForEach-Object { if ($_.Contains(' ')) { '"' + $_ + '"' } else { $_ } } | Out-String).Trim()
    Write-Information $cmd -InformationAction Continue
    if (-not $DryRun) {
        if ($PSCmdlet.ShouldProcess($taskName, 'Register scheduled task')) {
            & schtasks.exe @taskArgs | Write-Information -InformationAction Continue
        }
    }
}

# Resolve paths
$repo = Split-Path -Parent $PSScriptRoot
$startScript = Join-Path $repo 'scripts\Start-LocalLoraTraining.ps1'
$backupScript = Join-Path $repo 'scripts\Backup-LoraAdapters.ps1'
$analyzeScript = Join-Path $repo 'scripts\Analyze-TrainingLogs.ps1'

if (-not (Test-Path $startScript)) { throw "Start script not found: $startScript" }

# Ensure auxiliary scripts exist (backup/analyze may be optional but we try to create tasks)
if (-not (Test-Path $backupScript)) { Write-Information "Backup script not found: $backupScript (task will still be created if path later exists)" -InformationAction Continue }
if (-not (Test-Path $analyzeScript)) { Write-Information "Analyze script not found: $analyzeScript (task will still be created if path later exists)" -InformationAction Continue }

# Nightly training command
$nightlyCmd = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$startScript`" -MaxSamples 10 -Epochs 1 -TodoistComplete"
New-Task -Name 'NightlyTraining' -ScheduleArgs ("DAILY /ST $DailyAt /RU SYSTEM") -Command $nightlyCmd

# Weekly backup (Fridays 03:00)
$backupCmd = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$backupScript`""
New-Task -Name 'WeeklyBackup' -ScheduleArgs 'WEEKLY /D FRI /ST 03:00 /RU SYSTEM' -Command $backupCmd

# Weekly log analysis (Mondays 08:50)
$analyzeCmd = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$analyzeScript`""
New-Task -Name 'WeeklyLogAnalysis' -ScheduleArgs 'WEEKLY /D MON /ST 08:50 /RU SYSTEM' -Command $analyzeCmd

Write-Information "Scheduled task registration complete. If SYSTEM registration fails, rerun elevated (Run as Administrator)." -InformationAction Continue