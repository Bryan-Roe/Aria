# Azure Quantum Master Orchestration Script
# Chains batch jobs, cost monitoring, and resource management scripts
# Add notification hooks as needed

param(
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$WorkspaceName = "quantum-ai-workspace",
    [string]$Location = "eastus",
    [string]$TeamsWebhook = '',
    [string]$LogicAppUrl = '',
    [string]$NotifyEmail = '',
    [string]$SmtpServer = '',
    [int]$SmtpPort = 587,
    [switch]$UseSsl,
    [string]$FromEmail = 'no-reply@yourdomain.com'
)

function Info($msg) { Write-Host $msg -ForegroundColor Yellow }
function Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Err($msg) { Write-Host $msg -ForegroundColor Red }

Write-Host "== Azure Quantum Master Orchestration ==" -ForegroundColor Cyan

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

function Send-Email([string]$subject, [string]$body){
    if (-not $NotifyEmail -or -not $SmtpServer) { return }
    try {
        $cred = $null
        if ($env:SMTP_USERNAME -and $env:SMTP_PASSWORD) {
            $secure = ConvertTo-SecureString $env:SMTP_PASSWORD -AsPlainText -Force
            $cred = New-Object System.Management.Automation.PSCredential($env:SMTP_USERNAME, $secure)
        }
        $args = @{ To=$NotifyEmail; Subject=$subject; Body=$body; SmtpServer=$SmtpServer; Port=$SmtpPort; From=$FromEmail }
        if ($UseSsl) { $args.UseSsl = $true }
        if ($cred) { $args.Credential = $cred }
        & "$PSScriptRoot/notify_smtp.ps1" @args | Out-Null
        Info 'Email notification sent.'
    } catch {
        Err "Failed to send email notification: $_"
    }
}

# 1. Resource orchestration
Info "Running resource orchestration..."
& "$PSScriptRoot\quantum_resource_orchestration.ps1" -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName -Location $Location

# 2. Batch job submission
Info "Running batch job automation..."
& "$PSScriptRoot\quantum_batch_jobs.ps1" -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName -Location $Location

# 3. Cost monitoring
Info "Running cost monitoring..."
& "$PSScriptRoot\quantum_cost_monitor.ps1" -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName

# 4. Notifications (optional, no prompt)
$facts = @{ Workspace = $WorkspaceName; ResourceGroup = $ResourceGroup; Location = $Location; When = (Get-Date).ToString('u'); Status = 'Succeeded' }
Send-TeamsNotification -title 'Azure Quantum Orchestration' -message 'Completed successfully.' -facts $facts
Send-LogicAppNotification -message 'Azure Quantum orchestration completed successfully.' -status 'Succeeded'
Send-Email -subject 'Azure Quantum Orchestration: Succeeded' -body "Workspace: $WorkspaceName`nRG: $ResourceGroup`nLocation: $Location`nWhen: $(Get-Date -Format u)"

Ok "Master orchestration complete. All steps chained."
