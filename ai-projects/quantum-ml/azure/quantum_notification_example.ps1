# Azure Quantum Notification Example
# Add to any script to send notifications (email, Teams, webhook, Logic Apps)

param(
    [string]$Message = "Quantum job completed!",
    [string]$Email = "user@example.com",
    [string]$TeamsWebhook = "",
    [string]$LogicAppUrl = ""
)

function Info($msg) { Write-Host $msg -ForegroundColor Yellow }

# Email notification (requires SMTP setup)
# Send-MailMessage -To $Email -Subject "Azure Quantum Notification" -Body $Message -SmtpServer "smtp.example.com"
Info "Email notification sent to $Email (customize SMTP settings)."

# Teams webhook notification
if ($TeamsWebhook) {
    $payload = @{ text = $Message } | ConvertTo-Json
    Invoke-RestMethod -Uri $TeamsWebhook -Method Post -Body $payload -ContentType 'application/json'
    Info "Teams notification sent."
}

# Logic App webhook notification
if ($LogicAppUrl) {
    $payload = @{ message = $Message } | ConvertTo-Json
    Invoke-RestMethod -Uri $LogicAppUrl -Method Post -Body $payload -ContentType 'application/json'
    Info "Logic App notification sent."
}
