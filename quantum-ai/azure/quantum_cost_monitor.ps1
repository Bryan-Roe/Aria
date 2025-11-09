# Azure Quantum Cost Monitoring Script
# Summarizes job costs for recent jobs using CLI

param(
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$WorkspaceName = "quantum-ai-workspace"
)

function Info($msg) { Write-Host $msg -ForegroundColor Yellow }
function Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Err($msg) { Write-Host $msg -ForegroundColor Red }

Write-Host "== Azure Quantum Cost Monitoring ==" -ForegroundColor Cyan

# List recent jobs
$jobs = az quantum job list --resource-group $ResourceGroup --workspace-name $WorkspaceName --output json | ConvertFrom-Json
if (-not $jobs) { Err "No jobs found."; exit 1 }

foreach ($job in $jobs) {
    $id = $job.id
    $target = $job.target
    $status = $job.status
    $cost = $job.billingInformation.totalCharges
    Write-Host "Job: $id | Target: $target | Status: $status | Cost: $cost" -ForegroundColor White
}

Ok "Cost monitoring complete."
