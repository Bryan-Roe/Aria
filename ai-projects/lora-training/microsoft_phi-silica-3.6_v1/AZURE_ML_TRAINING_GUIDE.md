# Azure ML Training for Phi-3.6 LoRA Fine-tuning

This guide shows how to train Phi-3.6 LoRA models on Azure Machine Learning with GPU acceleration.

## Prerequisites

### 1. Azure Subscription
- Active Azure subscription
- Contributor or Owner role on the subscription/resource group

### 2. Azure CLI (Recommended)
```powershell
# Install Azure CLI
winget install Microsoft.AzureCLI

# Login
az login

# Set subscription
az account set --subscription "<your-subscription-id>"
```

### 3. Python Dependencies
```powershell
cd AI\microsoft_phi-silica-3.6_v1
pip install azure-ai-ml azure-identity azure-core
```

## Quick Start

### Step 1: Create Azure ML Workspace

**Option A: Azure Portal** (Easiest)
1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Machine Learning"
3. Click "+ Create"
4. Fill in:
   - Subscription: Your subscription
   - Resource group: Create new "rg-phi36-ml"
   - Workspace name: "phi36-ml-workspace"
   - Region: "East US" or "West US 2" (GPU availability)
5. Click "Review + Create"

**Option B: Azure CLI**
```powershell
# Create resource group
az group create --name rg-phi36-ml --location eastus

# Create ML workspace
az ml workspace create `
  --name phi36-ml-workspace `
  --resource-group rg-phi36-ml `
  --location eastus
```

### Step 2: Setup Infrastructure

```powershell
cd AI\microsoft_phi-silica-3.6_v1

# Setup compute cluster and environment
python azure_ml_training.py `
  --action setup `
  --subscription-id "<your-subscription-id>" `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace `
  --vm-size Standard_NC6s_v3
```

This creates:
- GPU compute cluster (auto-scales 0-4 nodes)
- Python environment with all dependencies
- Cost: ~$0/hour when idle (auto-scales to 0)

### Step 3: Upload Dataset

```powershell
# Upload Dolly dataset to Azure ML
python azure_ml_training.py `
  --action upload `
  --subscription-id "<your-subscription-id>" `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace `
  --dataset-path "..\..\datasets\chat\dolly"
```

### Step 4: Submit Training Job

**Quick Test (64 samples, ~5 minutes)**
```powershell
python azure_ml_training.py `
  --action train `
  --subscription-id "<your-subscription-id>" `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace `
  --max-train-samples 64
```

**Full Training (8000 samples, ~2-4 hours)**
```powershell
python azure_ml_training.py `
  --action train `
  --subscription-id "<your-subscription-id>" `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace
```

### Step 5: Monitor Training

After submitting, you'll get a URL like:
```
Monitor at: https://ml.azure.com/runs/<job-name>?wsid=/subscriptions/...
```

Open this in your browser to see:
- Real-time metrics (loss, perplexity)
- GPU utilization
- Training logs
- Resource usage

### Step 6: Register Model (After Training)

```powershell
# Use the job name from training output
python azure_ml_training.py `
  --action register `
  --subscription-id "<your-subscription-id>" `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace `
  --job-name "<job-name-from-training>"
```

## Cost Optimization

### Compute Costs

| VM Size | GPU | Cost/hour | Best For |
|---------|-----|-----------|----------|
| Standard_NC6s_v3 | 1x V100 (16GB) | ~$3.06 | Default (good balance) |
| Standard_NC12s_v3 | 2x V100 (32GB) | ~$6.12 | Faster training |
| Standard_NC24s_v3 | 4x V100 (64GB) | ~$12.24 | Large batches |

**💰 Cost-saving tips:**
1. **Auto-scale to 0**: Cluster scales down when idle (included in setup)
2. **Low-priority VMs**: Add `--tier low_priority` (70-80% discount, may be preempted)
3. **Stop after training**: Compute auto-stops after job completes
4. **Test locally first**: Use `--max-train-samples 64` for validation

### Example Costs

| Scenario | Duration | Cost |
|----------|----------|------|
| Quick test (64 samples) | ~5 min | ~$0.25 |
| Medium run (1000 samples) | ~30 min | ~$1.50 |
| Full training (8000 samples) | ~3 hours | ~$9.00 |

## Advanced Configuration

### Custom VM Sizes

```powershell
# Larger GPU for faster training
python azure_ml_training.py --action setup --vm-size Standard_NC12s_v3

# Low-priority for cost savings (add to training script)
# Edit azure_ml_training.py line 95: tier="low_priority"
```

### Custom Datasets

```powershell
# Upload your own dataset
python azure_ml_training.py `
  --action upload `
  --subscription-id "<your-subscription-id>" `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace `
  --dataset-path ".\my_custom_dataset" `
  --dataset-name my-dataset

# Train with custom dataset
python azure_ml_training.py `
  --action train `
  --dataset-name my-dataset `
  ...
```

### Custom Config

```powershell
# Use different LoRA config
python azure_ml_training.py `
  --action train `
  --config ".\lora\my_custom_lora.yaml" `
  ...
```

## Troubleshooting

### Authentication Errors
```powershell
# Re-authenticate
az login
az account show  # Verify correct subscription
```

### Quota Errors
If you see "insufficient quota for NC-series VMs":
1. Go to Azure Portal
2. Search "Quotas"
3. Filter by "Compute" and your region
4. Request quota increase for "NC-series" VMs

### Dataset Upload Issues
```powershell
# Verify dataset structure
ls ..\..\datasets\chat\dolly\*.json

# Should see train.json and test.json
```

### Training Failures
Check the Azure ML Studio logs:
1. Open the training job URL
2. Go to "Outputs + logs" tab
3. Check `user_logs/std_log.txt`

## Environment Variables

For easier usage, set these in PowerShell profile:

```powershell
# Open profile
notepad $PROFILE

# Add these lines:
$env:AZURE_SUBSCRIPTION_ID = "<your-subscription-id>"
$env:AZURE_RESOURCE_GROUP = "rg-phi36-ml"
$env:AZURE_ML_WORKSPACE = "phi36-ml-workspace"

# Then use simplified commands:
python azure_ml_training.py --action train
```

## Downloading Results

After training completes:

```powershell
# Download from Azure ML Studio UI
# 1. Open job URL
# 2. Go to "Outputs + logs"
# 3. Download "outputs/lora_adapter/" folder

# Or use Azure ML CLI
az ml job download `
  --name <job-name> `
  --workspace-name phi36-ml-workspace `
  --resource-group rg-phi36-ml `
  --output-path .\downloaded_models
```

## Cleanup

When done training:

```powershell
# Delete compute cluster (stops billing)
az ml compute delete `
  --name phi36-gpu-cluster `
  --workspace-name phi36-ml-workspace `
  --resource-group rg-phi36-ml `
  --yes

# Delete entire resource group (removes everything)
az group delete --name rg-phi36-ml --yes
```

## Next Steps

After training:
1. **Test locally**: Download model and test with `scripts/test_lora_model.py`
2. **Deploy to Azure**: Use Azure ML endpoints for production inference
3. **Fine-tune further**: Adjust `lora.yaml` and retrain

## Support

- Azure ML Documentation: https://learn.microsoft.com/azure/machine-learning/
- Phi-3 Documentation: https://huggingface.co/microsoft/Phi-3.5-mini-instruct
- Issues: Check logs in Azure ML Studio
