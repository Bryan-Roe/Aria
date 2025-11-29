# Azure ML Training Setup Guide

Complete guide to training AI models on Azure Machine Learning.

## 🚀 Quick Start

### Prerequisites Checklist

- ✅ Azure CLI installed (version 2.78.0 detected)
- ✅ Azure subscription active ("Azure subscription 1")
- ⚠️ Azure ML workspace configuration needed

### Step 1: Configure Azure ML Workspace

You need to update `.env` file with your Azure ML workspace details:

```powershell
# Get your subscription ID
az account show --query id -o tsv

# List available resource groups
az group list --query "[].name" -o table

# List ML workspaces (if you have one)
az ml workspace list --query "[].{Name:name, ResourceGroup:resourceGroup}" -o table
```

**Update `.env` file** with these values:
```env
AZURE_ML_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_ML_RESOURCE_GROUP=<your-resource-group>
AZURE_ML_WORKSPACE=<your-workspace-name>
```

### Step 2: Create Azure ML Workspace (if needed)

If you don't have a workspace yet:

```powershell
# Create resource group (skip if you have one)
az group create --name "qai-ml-rg" --location "eastus"

# Create Azure ML workspace
az ml workspace create --name "qai-ml-workspace" --resource-group "qai-ml-rg"
```

### Step 3: Create Compute Cluster

Azure ML requires compute resources for training:

```powershell
# Create CPU compute cluster (low cost for testing)
az ml compute create --name "cpu-cluster" `
    --type amlcompute `
    --size Standard_D2_v2 `
    --min-instances 0 `
    --max-instances 4 `
    --resource-group "<your-resource-group>" `
    --workspace-name "<your-workspace-name>"

# OR create GPU compute cluster (for faster training)
az ml compute create --name "gpu-cluster" `
    --type amlcompute `
    --size Standard_NC6 `
    --min-instances 0 `
    --max-instances 2 `
    --resource-group "<your-resource-group>" `
    --workspace-name "<your-workspace-name>"
```

**Cost Note**: Clusters auto-scale to 0 when idle, so you only pay when training.

## 📝 Training Workflows

### Option A: Automated Pipeline (Recommended)

Our `automated_training_pipeline.py` handles everything:

```powershell
# Generate Azure ML job spec (dry run - no training)
python .\scripts\automated_training_pipeline.py --azure-ml-spec --quick --models phi,qwen

# This creates: .azureml/job_<timestamp>.yaml
```

**What it includes**:

- Environment setup (Python packages, dependencies)
- Training script configuration
- Compute target selection
- Data handling
- Model registration

**Validate and submit**:
```powershell
# Validate the generated spec
python .\scripts\azureml_ci_validate.py

# Submit to Azure ML
python .\scripts\azureml_ci_validate.py --submit
```

### Option B: Direct Azure ML SDK

For custom training with full control:

```python
from azure.ai.ml import MLClient, command, Input
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential

# Connect to workspace
ml_client = MLClient(
    credential=DefaultAzureCredential(),
    subscription_id="<your-subscription-id>",
    resource_group_name="<your-resource-group>",
    workspace_name="<your-workspace-name>"
)

# Configure training job
job = command(
    code="./AI/microsoft_phi-silica-3.6_v1",
    command="python scripts/train_lora.py --dataset ../../datasets/chat/mixed_chat --epochs 3",
    environment="azureml://registries/azureml/environments/sklearn-1.5/labels/latest",
    compute="cpu-cluster",
    display_name="phi-lora-training",
    experiment_name="lora-finetuning"
)

# Submit job
returned_job = ml_client.jobs.create_or_update(job)
print(f"Job URL: {returned_job.studio_url}")
```

### Option C: Azure ML Studio UI

1. Navigate to [Azure ML Studio](https://ml.azure.com)
2. Select your workspace
3. Go to **Jobs** → **Create** → **Command job**
4. Upload training code
5. Select compute cluster
6. Configure environment and parameters
7. Submit

## 🎯 Training Scenarios

### Scenario 1: Quick Phi Model Training

```powershell
# Generate data and train Phi-3.5-mini with LoRA
python .\scripts\automated_training_pipeline.py `
    --azure-ml-spec `
    --quick `
    --models phi `
    --azure-ml-compute "cpu-cluster"

# Validate and submit
python .\scripts\azureml_ci_validate.py --submit
```

**Expected cost**: ~$0.10-0.50 for quick training (100 samples, 1 epoch)

### Scenario 2: Multi-Model Training

```powershell
# Train both Phi and Qwen models
python .\scripts\automated_training_pipeline.py `
    --azure-ml-spec `
    --models phi,qwen `
    --samples 500 `
    --azure-ml-compute "gpu-cluster"

python .\scripts\azureml_ci_validate.py --submit
```

### Scenario 3: Full Training Pipeline

```powershell
# Complete training with evaluation
python .\scripts\automated_training_pipeline.py `
    --azure-ml-spec `
    --models phi,qwen `
    --samples 1000 `
    --azure-ml-compute "gpu-cluster" `
    --azure-ml-experiment "production-training"

python .\scripts\azureml_ci_validate.py --submit
```

## 📊 Monitoring Training

### Via Azure CLI

```powershell
# List recent jobs
az ml job list --resource-group "<your-rg>" --workspace-name "<your-workspace>"

# Get job status
az ml job show --name "<job-name>" --resource-group "<your-rg>" --workspace-name "<your-workspace>"

# Stream job logs
az ml job stream --name "<job-name>" --resource-group "<your-rg>" --workspace-name "<your-workspace>"
```

### Via Azure ML Studio

1. Go to [ml.azure.com](https://ml.azure.com)
2. Navigate to **Jobs**
3. Click on your job to see:
   - Real-time logs
   - Metrics and charts
   - Resource utilization
   - Model artifacts

## 🔧 Best Practices

### 1. Environment Management

- Use **curated environments** for faster startup (no Docker build needed)
- Common curated environments:
  - `AzureML-sklearn-1.5` - Scikit-learn
  - `AzureML-pytorch-2.0` - PyTorch
  - `AzureML-tensorflow-2.7` - TensorFlow

### 2. Cost Optimization

- Start with **CPU clusters** for testing ($0.096/hour for Standard_D2_v2)
- Use **GPU clusters** only for large models ($0.90/hour for Standard_NC6)
- Set `min_instances=0` for auto-shutdown
- Use **serverless compute** for one-off jobs (no cluster management)

### 3. Data Management

- Upload datasets to **Azure Blob Storage**
- Register datasets in Azure ML for versioning
- Use **direct mode** for small datasets
- Use **mount mode** for large datasets

### 4. Job Configuration

- Use **experiment names** to group related runs
- Add **tags** for filtering and search
- Enable **early termination** for hyperparameter tuning
- Configure **output paths** for model artifacts

## 🛠️ Troubleshooting

### Issue: "az ml command not found"

```powershell
# Install Azure ML CLI extension
az extension add --name ml
```

### Issue: "Authentication failed"

```powershell
# Login to Azure
az login

# Set subscription
az account set --subscription "<subscription-id>"
```

### Issue: "Compute target not found"

```powershell
# List available compute
az ml compute list --resource-group "<your-rg>" --workspace-name "<your-workspace>"

# Create compute if needed (see Step 3 above)
```

### Issue: "Environment preparation taking too long"

- Use curated environments instead of custom Docker images
- Pre-register custom environments to avoid rebuild on each job

### Issue: "Job failed with out of memory"

- Reduce batch size in training script
- Use larger VM size for compute
- Consider distributed training for large models

## 📚 Additional Resources

### Microsoft Documentation
- [Azure ML Training Overview](https://learn.microsoft.com/azure/machine-learning/how-to-train-model)
- [Configure Training Jobs](https://learn.microsoft.com/azure/machine-learning/how-to-set-up-training-targets)
- [Managed Compute](https://learn.microsoft.com/azure/machine-learning/how-to-create-attach-compute-studio)
- [Distributed Training](https://learn.microsoft.com/azure/machine-learning/how-to-train-distributed-gpu)

### QAI Scripts
- `scripts/automated_training_pipeline.py` - Multi-model training orchestrator
- `scripts/azureml_ci_validate.py` - Job spec validation and submission
- `scripts/parallel_train.py` - Parallel training for multiple configs
- `AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py` - LoRA fine-tuning

### Pricing
- [Azure ML Pricing Calculator](https://azure.microsoft.com/pricing/details/machine-learning/)
- Estimated costs for QAI training:
  - Quick test (100 samples): ~$0.10
  - Small training (1000 samples): ~$0.50-1.00
  - Full training (10000 samples): ~$5-10

## 🎓 Next Steps

1. **Complete Step 1** - Configure `.env` with your Azure ML workspace
2. **Test connection** - Run `az ml workspace show --name "<workspace>" --resource-group "<rg>"`
3. **Create compute** - Set up CPU cluster for initial testing
4. **Generate job spec** - Run automated_training_pipeline with `--azure-ml-spec`
5. **Submit first job** - Use azureml_ci_validate.py to submit
6. **Monitor in Studio** - Watch your training in Azure ML Studio

---

**Need Help?** Check logs in Azure ML Studio or run with `--help` flag on any script.
