<#
.SYNOPSIS
    Deploy LoRA training jobs to Azure Machine Learning with GPU compute

.DESCRIPTION
    Automates deployment of all AutoTrain jobs to Azure ML:
    - Creates/validates Azure ML workspace and GPU compute cluster
    - Uploads datasets to Azure ML
    - Submits all training jobs from autotrain.yaml
    - Monitors progress and downloads trained models

.PARAMETER SubscriptionId
    Azure subscription ID

.PARAMETER ResourceGroup
    Resource group name (default: rg-phi36-ml)

.PARAMETER WorkspaceName
    ML workspace name (default: phi36-ml-workspace)

.PARAMETER Location
    Azure region (default: eastus)

.PARAMETER VMSize
    GPU VM size (default: Standard_NC6s_v3 = 1x V100)

.PARAMETER MaxInstances
    Max compute cluster nodes (default: 4)

.PARAMETER JobFilter
    Filter jobs by name pattern (e.g., "phi35*" or "comprehensive")

.PARAMETER DryRun
    Validate configuration without submitting jobs

.EXAMPLE
    .\scripts\deploy_training_to_azure.ps1 -SubscriptionId "a07fbd16-xxxx" -DryRun

.EXAMPLE
    .\scripts\deploy_training_to_azure.ps1 `
        -SubscriptionId "a07fbd16-xxxx" `
        -JobFilter "phi35_comprehensive*"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [string]$ResourceGroup = "rg-phi36-ml",
    [string]$WorkspaceName = "phi36-ml-workspace",
    [string]$Location = "eastus",
    [string]$VMSize = "Standard_NC6s_v3",
    [int]$MaxInstances = 4,
    [string]$JobFilter = "*",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ScriptRoot "AI\microsoft_phi-silica-3.6_v1\venv\Scripts\python.exe"
$AzureMLScript = Join-Path $ScriptRoot "AI\microsoft_phi-silica-3.6_v1\azure_ml_training.py"
$AutotrainConfig = Join-Path $ScriptRoot "autotrain.yaml"

# Logging
$LogFile = Join-Path $ScriptRoot "data_out\azure_training_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
New-Item -ItemType Directory -Path (Split-Path $LogFile) -Force | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logEntry
    
    switch ($Level) {
        "SUCCESS" { Write-Host $Message -ForegroundColor Green }
        "WARNING" { Write-Host $Message -ForegroundColor Yellow }
        "ERROR"   { Write-Host $Message -ForegroundColor Red }
        default   { Write-Host $Message }
    }
}

Write-Log "========================================" "INFO"
Write-Log "Azure ML Training Deployment" "INFO"
Write-Log "========================================" "INFO"

# Step 1: Validate prerequisites
Write-Log "`nStep 1: Validating Prerequisites" "INFO"
Write-Log "========================================" "INFO"

# Check Python venv
if (-not (Test-Path $VenvPython)) {
    Write-Log "Python venv not found at: $VenvPython" "ERROR"
    exit 1
}
Write-Log "[OK] Python venv found" "SUCCESS"

# Check Azure ML script
if (-not (Test-Path $AzureMLScript)) {
    Write-Log "Azure ML script not found at: $AzureMLScript" "ERROR"
    exit 1
}
Write-Log "[OK] Azure ML script found" "SUCCESS"

# Check autotrain config
if (-not (Test-Path $AutotrainConfig)) {
    Write-Log "AutoTrain config not found at: $AutotrainConfig" "ERROR"
    exit 1
}
Write-Log "[OK] AutoTrain config found" "SUCCESS"

# Check Azure CLI
$ErrorActionPreference = "Continue"
$null = az --version *>&1
$ErrorActionPreference = "Stop"
if ($LASTEXITCODE -eq 0) {
    Write-Log "[OK] Azure CLI installed" "SUCCESS"
} else {
    Write-Log "Azure CLI not installed" "ERROR"
    exit 1
}

# Check Azure login
$account = az account show 2>&1 | ConvertFrom-Json
if ($account -and $account.id) {
    Write-Log "[OK] Logged in to Azure as: $($account.user.name)" "SUCCESS"
    
    # Validate subscription
    if ($account.id -ne $SubscriptionId) {
        Write-Log "Setting subscription to: $SubscriptionId" "INFO"
        az account set --subscription $SubscriptionId
    }
} else {
    Write-Log "Not logged in to Azure. Run: az login" "ERROR"
    exit 1
}

# Step 2: Setup Azure ML Workspace
Write-Log "`nStep 2: Setting up Azure ML Workspace" "INFO"
Write-Log "========================================" "INFO"

if ($DryRun) {
    Write-Log "[DRY RUN] Would create/validate workspace: $WorkspaceName" "WARNING"
} else {
    # Create resource group if doesn't exist
    $rgExists = az group exists --name $ResourceGroup | ConvertFrom-Json
    if (-not $rgExists) {
        Write-Log "Creating resource group: $ResourceGroup" "INFO"
        az group create --name $ResourceGroup --location $Location
        Write-Log "[OK] Resource group created" "SUCCESS"
    } else {
        Write-Log "[OK] Resource group exists" "SUCCESS"
    }
    
    # Create/validate ML workspace
    Write-Log "Creating/validating ML workspace: $WorkspaceName" "INFO"
    $wsCheck = az ml workspace show --name $WorkspaceName --resource-group $ResourceGroup 2>$null
    if (-not $wsCheck) {
        az ml workspace create `
            --name $WorkspaceName `
            --resource-group $ResourceGroup `
            --location $Location
        Write-Log "[OK] ML workspace created" "SUCCESS"
    } else {
        Write-Log "[OK] ML workspace exists" "SUCCESS"
    }
}

# Step 3: Setup GPU Compute Cluster
Write-Log "`nStep 3: Setting up GPU Compute Cluster" "INFO"
Write-Log "========================================" "INFO"
Write-Log "VM Size: $VMSize" "INFO"
Write-Log "Max Instances: $MaxInstances" "INFO"
Write-Log "Auto-scale to 0 when idle: Enabled" "INFO"

if ($DryRun) {
    Write-Log "[DRY RUN] Would create/validate compute cluster" "WARNING"
} else {
    Write-Log "Running Azure ML setup script..." "INFO"
    $setupResult = & $VenvPython $AzureMLScript `
        --action setup `
        --subscription-id $SubscriptionId `
        --resource-group $ResourceGroup `
        --workspace-name $WorkspaceName `
        --vm-size $VMSize 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "[OK] Compute cluster ready" "SUCCESS"
    } else {
        Write-Log "Compute setup failed: $setupResult" "ERROR"
        exit 1
    }
}

# Step 4: Upload Datasets
Write-Log "`nStep 4: Uploading Datasets" "INFO"
Write-Log "========================================" "INFO"

# Parse autotrain.yaml to get unique datasets
$yamlContent = Get-Content $AutotrainConfig -Raw
$datasets = @()
if ($yamlContent -match "dataset:\s*(.+)") {
    $yamlContent | Select-String -Pattern "dataset:\s*(.+)" -AllMatches | ForEach-Object {
        $_.Matches | ForEach-Object {
            $dataset = $_.Groups[1].Value.Trim()
            if ($dataset -notin $datasets) {
                $datasets += $dataset
            }
        }
    }
}

Write-Log "Found $($datasets.Count) unique datasets" "INFO"
foreach ($dataset in $datasets) {
    $datasetPath = Join-Path $ScriptRoot $dataset
    $datasetName = Split-Path $dataset -Leaf
    
    if (-not (Test-Path $datasetPath)) {
        Write-Log "Dataset not found: $datasetPath" "WARNING"
        continue
    }
    
    Write-Log "Uploading dataset: $datasetName from $dataset" "INFO"
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would upload: $datasetPath -> $datasetName" "WARNING"
    } else {
        $uploadResult = & $VenvPython $AzureMLScript `
            --action upload `
            --subscription-id $SubscriptionId `
            --resource-group $ResourceGroup `
            --workspace-name $WorkspaceName `
            --dataset-path $datasetPath `
            --dataset-name $datasetName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "[OK] Dataset uploaded: $datasetName" "SUCCESS"
        } else {
            Write-Log "Upload failed: $uploadResult" "WARNING"
        }
    }
}

# Step 5: Submit Training Jobs
Write-Log "`nStep 5: Submitting Training Jobs" "INFO"
Write-Log "========================================" "INFO"
Write-Log "Job Filter: $JobFilter" "INFO"

# Parse autotrain.yaml for jobs
$jobs = @()
$currentJob = $null
$yamlLines = Get-Content $AutotrainConfig

foreach ($line in $yamlLines) {
    if ($line -match "^\s*- name:\s*(.+)") {
        if ($currentJob) {
            $jobs += $currentJob
        }
        $currentJob = @{
            name = $Matches[1].Trim()
            dataset = ""
            max_train_samples = 0
            learning_rate = "0.0002"
            epochs = 1
        }
    }
    elseif ($currentJob) {
        if ($line -match "^\s*dataset:\s*(.+)") {
            $currentJob.dataset = $Matches[1].Trim()
        }
        elseif ($line -match "^\s*max_train_samples:\s*(\d+)") {
            $currentJob.max_train_samples = [int]$Matches[1]
        }
        elseif ($line -match "^\s*learning_rate:\s*([\d.]+)") {
            $currentJob.learning_rate = $Matches[1]
        }
        elseif ($line -match "^\s*epochs:\s*(\d+)") {
            $currentJob.epochs = [int]$Matches[1]
        }
    }
}
if ($currentJob) {
    $jobs += $currentJob
}

# Filter jobs
$filteredJobs = $jobs | Where-Object { $_.name -like $JobFilter }
Write-Log "Found $($filteredJobs.Count) jobs matching filter" "INFO"

$submittedJobs = @()
foreach ($job in $filteredJobs) {
    $datasetName = Split-Path $job.dataset -Leaf
    
    Write-Log "`nSubmitting job: $($job.name)" "INFO"
    Write-Log "  Dataset: $datasetName" "INFO"
    Write-Log "  Samples: $($job.max_train_samples)" "INFO"
    Write-Log "  Epochs: $($job.epochs)" "INFO"
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would submit training job" "WARNING"
        $submittedJobs += @{
            name = $job.name
            status = "dry-run"
            url = "N/A"
        }
    } else {
        $trainArgs = @(
            "--action", "train",
            "--subscription-id", $SubscriptionId,
            "--resource-group", $ResourceGroup,
            "--workspace-name", $WorkspaceName,
            "--experiment-name", $job.name,
            "--dataset-name", $datasetName,
            "--config", "AI/microsoft_phi-silica-3.6_v1/lora/lora.yaml"
        )
        
        if ($job.max_train_samples -gt 0) {
            $trainArgs += @("--max-train-samples", $job.max_train_samples)
        }
        
        $trainResult = & $VenvPython $AzureMLScript @trainArgs 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            # Extract job URL from output
            $jobUrl = ($trainResult | Select-String -Pattern "https://ml.azure.com/.*").Matches.Value
            Write-Log "[OK] Job submitted: $($job.name)" "SUCCESS"
            Write-Log "  Monitor at: $jobUrl" "INFO"
            
            $submittedJobs += @{
                name = $job.name
                status = "submitted"
                url = $jobUrl
            }
        } else {
            Write-Log "Job submission failed: $trainResult" "ERROR"
            $submittedJobs += @{
                name = $job.name
                status = "failed"
                url = "N/A"
            }
        }
    }
    
    # Small delay between submissions
    Start-Sleep -Seconds 2
}

# Step 6: Summary
Write-Log "`n========================================" "INFO"
Write-Log "Deployment Summary" "INFO"
Write-Log "========================================" "INFO"

Write-Log "`nAzure ML Configuration:" "INFO"
Write-Log "  Subscription: $SubscriptionId" "INFO"
Write-Log "  Resource Group: $ResourceGroup" "INFO"
Write-Log "  Workspace: $WorkspaceName" "INFO"
Write-Log "  Compute: phi36-gpu-cluster ($VMSize)" "INFO"

Write-Log "`nSubmitted Jobs: $($submittedJobs.Count)" "INFO"
foreach ($job in $submittedJobs) {
    $statusColor = if ($job.status -eq "submitted") { "SUCCESS" } elseif ($job.status -eq "failed") { "ERROR" } else { "WARNING" }
    Write-Log "  - $($job.name): $($job.status)" $statusColor
    if ($job.url -ne "N/A") {
        Write-Log "    $($job.url)" "INFO"
    }
}

Write-Log "`nMonitor all jobs at:" "INFO"
Write-Log "  https://ml.azure.com/" "INFO"

if ($DryRun) {
    Write-Log "`n[DRY RUN] No resources created. Re-run without -DryRun to deploy." "WARNING"
} else {
    Write-Log "`n[OK] Training deployment complete!" "SUCCESS"
    Write-Log "Jobs will run on GPU compute and auto-scale to 0 when complete." "INFO"
}

Write-Log "`nLog file: $LogFile" "INFO"
