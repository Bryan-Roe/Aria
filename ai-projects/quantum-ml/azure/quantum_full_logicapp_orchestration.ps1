<#
Azure Quantum Full Orchestration with Logic App + optional Teams/Email notifications

This script chains resource orchestration, batch job submission, and cost monitoring.
It always sends a Logic App notification on success/failure and can optionally send
Teams Adaptive Card and SMTP email notifications when parameters are provided.

Usage examples (PowerShell):
  ./quantum_full_logicapp_orchestration.ps1 -LogicAppUrl "https://.../workflows/..." \
      -ResourceGroup rg-quantum-ai -WorkspaceName quantum-ai-workspace -Location eastus

  ./quantum_full_logicapp_orchestration.ps1 -LogicAppUrl "https://..." \
      -TeamsWebhook "https://outlook.office.com/webhook/..." \
      -NotifyEmail "ops@contoso.com" -SmtpServer "smtp.contoso.com" -UseSsl -FromEmail "no-reply@contoso.com"
#>

param(
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$WorkspaceName = "quantum-ai-workspace",
    [string]$Location = "eastus",
    [Parameter(Mandatory=$true)][string]$LogicAppUrl,
    [string]$TeamsWebhook = '',
    [string]$NotifyEmail = '',
    [string]$SmtpServer = '',
    [int]$SmtpPort = 587,
    [switch]$UseSsl,
    [string]$FromEmail = 'no-reply@yourdomain.com'
)

$ErrorActionPreference = 'Stop'

function Info($m){ Write-Host $m -ForegroundColor Yellow }
function Ok($m){ Write-Host $m -ForegroundColor Green }
function Err($m){ Write-Host $m -ForegroundColor Red }

Write-Host "== Azure Quantum Full Orchestration (Logic App + optional Teams/Email) ==" -ForegroundColor Cyan

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

function Send-Email([string]$subject, [string]$body){
  if (-not $NotifyEmail -or -not $SmtpServer) { return }
  try {
    $cred = $null
    if ($env:SMTP_USERNAME -and $env:SMTP_PASSWORD) {
      $secure = ConvertTo-SecureString $env:SMTP_PASSWORD -AsPlainText -Force
      $cred = New-Object System.Management.Automation.PSCredential($env:SMTP_USERNAME, $secure)
    }
  $mailParams = @{ To=$NotifyEmail; Subject=$subject; Body=$body; SmtpServer=$SmtpServer; Port=$SmtpPort; From=$FromEmail }
  if ($UseSsl) { $mailParams.UseSsl = $true }
  if ($cred) { $mailParams.Credential = $cred }
  & "$PSScriptRoot/notify_smtp.ps1" @mailParams | Out-Null
    Info 'Email notification sent.'
  } catch {
    Err "Failed to send email notification: $_"
  }
}

try {
    # 1. Resource orchestration
    Info "Running resource orchestration..."
    & "$PSScriptRoot/quantum_resource_orchestration.ps1" -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName -Location $Location

    # 2. Batch job submission
    Info "Running batch job automation..."
    & "$PSScriptRoot/quantum_batch_jobs.ps1" -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName -Location $Location

    # 3. Cost monitoring
    Info "Running cost monitoring..."
    & "$PSScriptRoot/quantum_cost_monitor.ps1" -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName

    # 4. Send Logic App notification
    $payload = @{
        message = "Quantum orchestration complete. All jobs and cost monitoring finished.";
        status = 'Succeeded';
        workspace = $WorkspaceName;
        resourceGroup = $ResourceGroup;
        location = $Location;
        time = (Get-Date).ToString('o')
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri $LogicAppUrl -Method Post -Body $payload -ContentType 'application/json'
    Ok "Logic App notification sent. Response: $response"

    # Additional notifications
    $facts = @{ Workspace = $WorkspaceName; ResourceGroup = $ResourceGroup; Location = $Location; When = (Get-Date).ToString('u'); Status = 'Succeeded' }
    Send-TeamsNotification -title 'Azure Quantum Orchestration' -message 'Completed successfully.' -facts $facts
    Send-Email -subject 'Azure Quantum Orchestration: Succeeded' -body "Workspace: $WorkspaceName`nRG: $ResourceGroup`nLocation: $Location`nWhen: $(Get-Date -Format u)"
}
catch {
    Err "Orchestration failed: $_"
    # Failure notification to Logic App
    $payload = @{
        message = "Quantum orchestration failed: $_";
        status = 'Failed';
        workspace = $WorkspaceName;
        resourceGroup = $ResourceGroup;
        location = $Location;
        time = (Get-Date).ToString('o')
    } | ConvertTo-Json
    try { Invoke-RestMethod -Uri $LogicAppUrl -Method Post -Body $payload -ContentType 'application/json' | Out-Null } catch { Err "Failed to send Logic App failure notification: $_" }

    # Optional additional failure notifications
    $facts = @{ Workspace = $WorkspaceName; ResourceGroup = $ResourceGroup; Location = $Location; When = (Get-Date).ToString('u'); Status = 'Failed'; Error = ("$_") }
    Send-TeamsNotification -title 'Azure Quantum Orchestration' -message 'Failed.' -facts $facts
    Send-Email -subject 'Azure Quantum Orchestration: Failed' -body "Failure: $_"
    exit 1
}
