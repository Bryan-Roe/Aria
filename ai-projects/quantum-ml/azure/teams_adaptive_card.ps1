param(
  [Parameter(Mandatory=$true)][string]$WebhookUrl,
  [string]$Title = 'Azure Quantum Notification',
  [string]$Message = 'Job completed',
  [hashtable]$Facts = @{},
  [string]$Color = '#2EB886'
)

# Build Adaptive Card payload
$factArray = @()
foreach ($k in $Facts.Keys) { $factArray += @{ title = "$k"; value = "$($Facts[$k])" } }

$card = @{
  type = 'message';
  attachments = @(@{
    contentType = 'application/vnd.microsoft.card.adaptive';
    content = @{
      '$schema' = 'http://adaptivecards.io/schemas/adaptive-card.json';
      type = 'AdaptiveCard';
      version = '1.3';
      body = @(
        @{ type='TextBlock'; text=$Title; weight='Bolder'; size='Medium' },
        @{ type='TextBlock'; text=$Message; wrap=$true },
        @{ type='FactSet'; facts=$factArray }
      )
    }
  })
}

Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body ($card | ConvertTo-Json -Depth 10) -ContentType 'application/json'
Write-Host 'Teams Adaptive Card posted.' -ForegroundColor Green
