$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$logsDir = Join-Path $repo 'AI\microsoft_phi-silica-3.6_v1\local_train\logs'
if (-not (Test-Path $logsDir)) { Write-Information "Logs directory not found: $logsDir" -InformationAction Continue; exit 0 }
$latest = Get-ChildItem -Path $logsDir -Filter 'train_*.log' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) { Write-Information "No training logs found." -InformationAction Continue; exit 0 }
$content = Get-Content -Path $latest.FullName -Raw
$summary = @()
$summary += "# Training Summary ($($latest.Name))"
$summary += ""
$pre = ($content | Select-String -Pattern 'Pre-training perplexity: ([0-9\.]+)') | Select-Object -First 1
$post = ($content | Select-String -Pattern 'Post-training perplexity: ([0-9\.]+)') | Select-Object -First 1
$trainLoss = ($content | Select-String -Pattern "'train_loss': ([0-9\.]+)") | Select-Object -First 1
if ($pre) { $summary += "- Pre-training perplexity: $($pre.Matches[0].Groups[1].Value)" }
if ($post) { $summary += "- Post-training perplexity: $($post.Matches[0].Groups[1].Value)" }
if ($trainLoss) { $summary += "- Train loss: $($trainLoss.Matches[0].Groups[1].Value)" }
$summary += "- Log file: $($latest.FullName)"
$outFile = Join-Path $logsDir 'LATEST_SUMMARY.md'
$summary -join "`n" | Out-File -FilePath $outFile -Encoding utf8
Write-Information "Wrote summary: $outFile" -InformationAction Continue