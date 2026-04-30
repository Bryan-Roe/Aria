# Robust Orchestration with Strict Mode, Logging, and Retries

param(
  [string]$ResourceGroup = 'rg-quantum-ai',
  [string]$WorkspaceName = 'quantum-ai-workspace',
  [string]$Location = 'eastus',
  [string]$TranscriptPath = "$PSScriptRoot/../logs/orchestration_$(Get-Date -Format yyyyMMdd_HHmmss).log",
  [string]$TeamsWebhook = '',
  [string]$LogicAppUrl = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not (Test-Path (Split-Path $TranscriptPath))) { New-Item -ItemType Directory -Path (Split-Path $TranscriptPath) -Force | Out-Null }
Start-Transcript -Path $TranscriptPath -Force | Out-Null

function Info($m){ Write-Host $m -ForegroundColor Yellow }
function Ok($m){ Write-Host $m -ForegroundColor Green }
function Err($m){ Write-Host $m -ForegroundColor Red }

function Invoke-WithRetry([scriptblock]$Action, [int]$MaxRetries=3, [int]$DelaySeconds=10){
  for($i=1;$i -le $MaxRetries;$i++){
    try { & $Action; return } catch { if($i -eq $MaxRetries){ throw } else { Start-Sleep -Seconds $DelaySeconds } }
  }
}

# Notification helpers (optional)
function Send-TeamsNotification([string]$title, [string]$message, [hashtable]$facts){
  if (-not $TeamsWebhook) { return }
  try {
    & "$PSScriptRoot/teams_adaptive_card.ps1" -WebhookUrl $TeamsWebhook -Title $title -Message $message -Facts $facts | Out-Null
    Info 'Teams notification sent.'
  } catch {
    Err "Failed to send Teams notification: $_"
  }
}

function Send-LogicAppNotification([string]$message, [string]$status){
  if (-not $LogicAppUrl) { return }
  try {
    $payload = @{
      message = $message;
      status = $status;
      workspace = $WorkspaceName;
      resourceGroup = $ResourceGroup;
      location = $Location;
      time = (Get-Date).ToString('o')
    } | ConvertTo-Json
    Invoke-RestMethod -Uri $LogicAppUrl -Method Post -Body $payload -ContentType 'application/json' | Out-Null
    Info 'Logic App notification sent.'
  } catch {
    Err "Failed to send Logic App notification: $_"
  }
}

try{
  Info 'Resource orchestration'
  Invoke-WithRetry { & "$PSScriptRoot/quantum_resource_orchestration.ps1" -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName -Location $Location }

  Info 'Batch jobs'
  Invoke-WithRetry { & "$PSScriptRoot/quantum_batch_jobs.ps1" -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName -Location $Location }

  Info 'Cost monitoring'
  & "$PSScriptRoot/quantum_cost_monitor.ps1" -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName
  Ok 'Orchestration completed.'

  # Success notifications (optional)
  $facts = @{ Workspace = $WorkspaceName; ResourceGroup = $ResourceGroup; Location = $Location; When = (Get-Date).ToString('u'); Status = 'Succeeded' }
  Send-TeamsNotification -title 'Azure Quantum Orchestration' -message 'Completed successfully.' -facts $facts
  Send-LogicAppNotification -message 'Azure Quantum orchestration completed successfully.' -status 'Succeeded'
}
catch{
  Err "Failure: $_"
  # Failure notifications (optional)
  $facts = @{ Workspace = $WorkspaceName; ResourceGroup = $ResourceGroup; Location = $Location; When = (Get-Date).ToString('u'); Status = 'Failed'; Error = ("$_") }
  Send-TeamsNotification -title 'Azure Quantum Orchestration' -message 'Failed.' -facts $facts
  Send-LogicAppNotification -message ("Azure Quantum orchestration failed: $_") -status 'Failed'
  exit 1
}
finally{
  Stop-Transcript | Out-Null
}
