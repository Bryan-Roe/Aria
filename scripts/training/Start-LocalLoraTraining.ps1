param(
    [int]$MaxSamples = 10,
    [int]$Epochs = 1,
    [string]$Config = "local_config.yaml",
    [switch]$Reinstall,
    [switch]$DryRun,
    [string]$LogDir,
    [switch]$TodoistComplete,              # If set, attempt to complete a Todoist task on success
    [string]$TodoistContent = "Run LoRA training (tiny) via VS Code task",
    [string]$TodoistProject = "QAI",
    [string]$TodoistToken                  # Optional; if not provided, will use $env:TODOIST_API_TOKEN
)

$ErrorActionPreference = 'Stop'

# Resolve paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Runner = Join-Path $ScriptDir 'run_local_lora_training.py'

# Default log directory under local_train
if (-not $LogDir) {
    $LogDir = Join-Path $RepoRoot 'AI\microsoft_phi-silica-3.6_v1\local_train\logs'
}

# Ensure log directory exists
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogFile = Join-Path $LogDir ("train_${timestamp}.log")

# Find Python
$pythonCmd = $null
try { $pythonCmd = (Get-Command python -ErrorAction Stop).Source } catch {}
if (-not $pythonCmd) {
    try { $pythonCmd = (Get-Command py -ErrorAction Stop).Source } catch {}
}
if (-not $pythonCmd) {
    Write-Error "Python was not found on PATH. Install Python 3.x or ensure 'python'/'py' is available."
    exit 1
}

# Environment tweaks for Windows
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:PYTHONUTF8 = '1'

# Build argument list
$argsList = @($Runner, '--max-samples', $MaxSamples.ToString(), '--epochs', $Epochs.ToString(), '--config', $Config)
if ($Reinstall) { $argsList += '--reinstall' }
if ($DryRun)    { $argsList += '--dry-run' }

Write-Host "Repo root: $RepoRoot"
Write-Host "Runner: $Runner"
Write-Host "Log file: $LogFile"

# Execute and tee output to log (allow stderr without terminating the script)
$oldEAP = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & $pythonCmd @argsList 2>&1 | Tee-Object -FilePath $LogFile -Append
    $exitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $oldEAP
}

if ($exitCode -ne 0) {
    Write-Error "Training failed with exit code $exitCode (see log: $LogFile)"
    exit $exitCode
}

Write-Host "Training completed successfully. Log: $LogFile"

# Optionally complete a Todoist task by content
if ($TodoistComplete) {
    try {
        $token = if ($TodoistToken) { $TodoistToken } else { $env:TODOIST_API_TOKEN }
        if (-not $token) {
            Write-Warning "Todoist token not provided; skipping task completion. Set -TodoistToken or TODOIST_API_TOKEN."
        } else {
            function Invoke-TodoistApi {
                param(
                    [string]$Method,
                    [string]$Path,
                    [hashtable]$Body
                )
                $uri = "https://api.todoist.com/rest/v2/$Path"
                $headers = @{ Authorization = "Bearer $token" }
                if ($Body) {
                    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 5)
                } else {
                    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
                }
            }

            # Find project by name
            $projects = Invoke-TodoistApi -Method GET -Path 'projects'
            $project = $projects | Where-Object { $_.name -eq $TodoistProject } | Select-Object -First 1
            if (-not $project) { throw "Todoist project '$TodoistProject' not found" }

            # Get tasks in project and find by content substring
            $tasks = Invoke-TodoistApi -Method GET -Path ("tasks?project_id=" + $project.id)
            $match = $tasks | Where-Object { $_.content -eq $TodoistContent } | Select-Object -First 1
            if (-not $match) {
                # Try contains match as fallback
                $match = $tasks | Where-Object { $_.content -like ("*" + $TodoistContent + "*") } | Select-Object -First 1
            }
            if ($match) {
                # Close the task
                Invoke-TodoistApi -Method POST -Path ("tasks/" + $match.id + "/close") | Out-Null
                Write-Host "Todoist task completed: $($match.content) (id=$($match.id))"
            } else {
                Write-Warning "No open Todoist task matched content: '$TodoistContent' in project '$TodoistProject'"
            }
        }
    } catch {
        Write-Warning "Todoist completion step failed: $($_.Exception.Message)"
    }
}
exit 0
