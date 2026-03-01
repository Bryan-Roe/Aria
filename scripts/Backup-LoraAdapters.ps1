$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$final = Join-Path $repo 'lora\local_train\outputs\final'
if (-not (Test-Path $final)) { Write-Information "No final output directory found: $final" -InformationAction Continue; exit 0 }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$destRoot = Join-Path $repo 'lora\data_out\backups'
$dest = Join-Path $destRoot $stamp
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$files = @('adapter_model.safetensors','adapter_config.json','README.md','tokenizer.json','tokenizer_config.json','special_tokens_map.json')
foreach ($f in $files) {
    $src = Join-Path $final $f
    if (Test-Path $src) { Copy-Item $src -Destination (Join-Path $dest $f) -Force }
}
Write-Information "Backup completed to: $dest" -InformationAction Continue