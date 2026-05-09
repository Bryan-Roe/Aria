# Azure Quantum Deployment Guide

## Prerequisites

1. **Azure CLI** installed and configured
2. **Azure subscription** with appropriate permissions
3. **Resource group** created (or will be created)

## Deployment Steps

### 1. Login to Azure

```bash
az login
az account set --subscription <your-subscription-id>
```

### 2. Create Resource Group (if not exists)

```bash
az group create \
  --name quantum-ai-rg \
  --location eastus
```

### 3. Deploy Azure Quantum Workspace

```bash
az deployment group create \
  --resource-group quantum-ai-rg \
  --template-file quantum_workspace.bicep \
  --parameters quantum_workspace.parameters.json
```

### 4. Verify Deployment

```bash
# List Quantum workspaces
az quantum workspace list \
  --resource-group quantum-ai-rg \
  --output table

# Show workspace details
az quantum workspace show \
  --resource-group quantum-ai-rg \
  --name quantum-ai-workspace
```

### 5. Get Workspace Resource ID

```bash
az quantum workspace show \
  --resource-group quantum-ai-rg \
  --name quantum-ai-workspace \
  --query id \
  --output tsv
```

Copy the resource ID and set it as an environment variable:

```powershell
# PowerShell
$env:AZURE_QUANTUM_RESOURCE_ID = "<your-resource-id>"

# Bash
export AZURE_QUANTUM_RESOURCE_ID="<your-resource-id>"
```

## Cost Management

### Free Tier Options

- **Microsoft QIO (Learn & Develop)**: Free tier available
- **IonQ Simulator**: Free
- **Quantinuum Simulator**: Free

### Paid Options

- **IonQ QPU**: ~$0.30 per gate-shot
- **Quantinuum H1**: ~$0.00015 per gate (H1-1) or $0.00025 (H1-2)

### Cost Estimation

Before running on real hardware:

```python
from src.azure_quantum_integration import AzureQuantumManager

azure_qm = AzureQuantumManager()
azure_qm.connect()

# Estimate cost
cost = azure_qm.estimate_cost(circuit, backend_name='ionq.qpu')
print(cost)
```

## Monitoring

### View Jobs in Azure Portal

1. Navigate to Azure Portal
2. Go to your Quantum workspace
3. Click on "Job management"
4. View job history and status

### Using Azure CLI

```bash
# List jobs
az quantum job list \
  --resource-group quantum-ai-rg \
  --workspace-name quantum-ai-workspace

# Get job output
az quantum job output \
  --job-id <job-id> \
  --resource-group quantum-ai-rg \
  --workspace-name quantum-ai-workspace
```

## Troubleshooting

### Provider Not Available

If a provider is not available in your region:

```bash
# Check available locations
az quantum workspace list-locations --output table

# Update location in parameters.json
```

### Authentication Issues

```bash
# Clear cached credentials
az account clear

# Login again
az login

# Verify subscription
az account show
```

### Quota Issues

Some quantum providers require application:

1. Visit [Azure Quantum portal](https://quantum.microsoft.com/)
2. Request access to specific providers
3. Wait for approval (usually 1-2 business days)

## Cleanup

To delete all resources:

```bash
az group delete \
  --name quantum-ai-rg \
  --yes \
  --no-wait
```

## Additional Resources

- [Azure Quantum Documentation](https://learn.microsoft.com/azure/quantum/)
- [Quantum Provider Documentation](https://learn.microsoft.com/azure/quantum/provider-support)
- [Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
