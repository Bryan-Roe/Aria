param(
  [Parameter(Mandatory=$true)][string]$To,
  [Parameter(Mandatory=$true)][string]$Subject,
  [Parameter(Mandatory=$true)][string]$Body,
  [Parameter(Mandatory=$true)][string]$SmtpServer,
  [int]$Port = 587,
  [switch]$UseSsl,
  [PSCredential]$Credential,
  [string]$From = 'no-reply@yourdomain.com'
)

# Note: Send-MailMessage is deprecated; consider MailKit for production. This is a pragmatic default.
Send-MailMessage -To $To -From $From -Subject $Subject -Body $Body -SmtpServer $SmtpServer -Port $Port -UseSsl:$UseSsl.IsPresent -Credential $Credential
Write-Host 'SMTP email sent.' -ForegroundColor Green
