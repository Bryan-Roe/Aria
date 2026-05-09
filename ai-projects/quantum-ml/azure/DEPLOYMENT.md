# Azure Quantum Workspace Deployment Guide

This guide explains how to deploy the Azure Quantum workspace infrastructure for the Quantum AI project.

## Prerequisites

1. **Azure Subscription**: Active Azure subscription with appropriate permissions
2. **Azure CLI**: Install from [https://docs.microsoft.com/cli/azure/install-azure-cli](https://docs.microsoft.com/cli/azure/install-azure-cli)
3. **Bicep**: Install Bicep CLI (comes with Azure CLI 2.20.0+)

## Architecture

The deployment creates the following resources:

- **Azure Quantum Workspace**: Main quantum computing workspace
- **Storage Account**: For storing quantum job data and results
- **Log Analytics Workspace**: For monitoring and diagnostics
- **Application Insights**: For tracking quantum job execution

### Quantum Providers

The workspace is configured with the following providers:

1. **IonQ**: Ion trap quantum computers (pay-as-you-go)
2. **Quantinuum**: High-fidelity quantum computers (pay-as-you-go)
3. **Microsoft QC**: Quantum simulators (free tier)

## Deployment Steps

### 1. Login to Azure

```powershell
az login
```

### 2. Set Your Subscription

```powershell
az account set --subscription "<your-subscription-id>"
```

### 3. Create Resource Group

```powershell
az group create `
  --name rg-quantum-ai `
  --location eastus
```

### 4. Review and Update Parameters

Edit `quantum_workspace.parameters.json` to customize:

- `location`: Azure region
- `workspaceName`: Unique workspace name
- `storageAccountName`: Unique storage account name
- `tags`: Resource tags

### 5. Validate Deployment

```powershell
az deployment group validate `
  --resource-group rg-quantum-ai `
  --template-file quantum_workspace.bicep `
  --parameters quantum_workspace.parameters.json
```

### 6. Deploy Infrastructure

```powershell
az deployment group create `
  --resource-group rg-quantum-ai `
  --template-file quantum_workspace.bicep `
  --parameters quantum_workspace.parameters.json `
  --name quantum-deployment-$(Get-Date -Format 'yyyyMMddHHmmss')
```

### 7. Retrieve Deployment Outputs

```powershell
az deployment group show `
  --resource-group rg-quantum-ai `
  --name quantum-deployment-<timestamp> `
  --query properties.outputs
```

## Post-Deployment Configuration

### 1. Update Configuration File

After deployment, update `config/quantum_config.yaml` with your Azure details:

```yaml
azure:
  subscription_id: "<your-subscription-id>"
  resource_group: "rg-quantum-ai"
  workspace_name: "quantum-ai-workspace"
  location: "eastus"
  storage_account: "<your-storage-account-name>"
```

### 2. Configure Authentication

Set up Azure authentication using one of these methods:

#### Option A: Azure CLI (Development)

```powershell
az login
```

#### Option B: Service Principal (Production)

```powershell
# Create service principal
az ad sp create-for-rbac `
  --name "quantum-ai-sp" `
  --role "Contributor" `
  --scopes /subscriptions/<subscription-id>/resourceGroups/rg-quantum-ai

# Set environment variables
$env:AZURE_CLIENT_ID="<client-id>"
$env:AZURE_CLIENT_SECRET="<client-secret>"
$env:AZURE_TENANT_ID="<tenant-id>"
```

#### Option C: Managed Identity (Azure Services)

If running on Azure services (VM, Container Instances, etc.), use managed identity:

```powershell
az identity create `
  --name quantum-ai-identity `
  --resource-group rg-quantum-ai

# Assign role to managed identity
az role assignment create `
  --assignee <identity-principal-id> `
  --role "Contributor" `
  --scope /subscriptions/<subscription-id>/resourceGroups/rg-quantum-ai
```

### 3. Verify Workspace Access

Test the connection using the Python SDK:

```python
from azure.quantum import Workspace
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
workspace = Workspace(
    subscription_id="<your-subscription-id>",
    resource_group="rg-quantum-ai",
    name="quantum-ai-workspace",
    credential=credential
)

print(f"Connected to workspace: {workspace.name}")
print(f"Available targets: {[t.name for t in workspace.get_targets()]}")
```

## Cost Management

### Estimated Costs

- **Storage Account**: ~$0.02/GB/month
- **Log Analytics**: ~$2.30/GB ingested
- **Application Insights**: First 5GB/month free
- **Quantum Jobs**: Varies by provider
  - IonQ: ~$0.00003 per gate-shot
  - Quantinuum: ~$0.00015 per circuit execution
  - Microsoft Simulators: Free

### Cost Optimization Tips

1. **Use Simulators for Development**: Test on free Microsoft simulators first
2. **Optimize Circuits**: Minimize gate count before running on hardware
3. **Monitor Usage**: Use Azure Cost Management dashboard
4. **Set Budgets**: Create budget alerts in Azure portal
5. **Delete When Not Needed**: Remove workspace if not actively used

## Monitoring and Diagnostics

### View Quantum Job Logs

```powershell
az monitor log-analytics query `
  --workspace <workspace-id> `
  --analytics-query "AzureDiagnostics | where ResourceProvider == 'MICROSOFT.QUANTUM'" `
  --timespan P1D
```

### Application Insights Queries

Access Application Insights in Azure Portal to:

- Track job execution times
- Monitor success/failure rates
- Analyze performance metrics
- Set up alerts for failures

## Cleanup

To delete all resources:

```powershell
az group delete --name rg-quantum-ai --yes --no-wait
```

## Troubleshooting

### Issue: Workspace Creation Fails

**Solution**: Ensure Azure Quantum is available in your region. Supported regions:

- East US
- West US
- West Europe
- North Europe

### Issue: Authentication Errors

**Solution**:

1. Verify Azure CLI login: `az account show`
2. Check RBAC permissions
3. Ensure service principal has Contributor role

### Issue: Provider Not Available

**Solution**: Some providers may require:

1. Registration with the provider
2. Credits to be purchased
3. Terms of service acceptance

## Additional Resources

- [Azure Quantum Documentation](https://docs.microsoft.com/azure/quantum/)
- [Qiskit on Azure Quantum](https://docs.microsoft.com/azure/quantum/quickstart-microsoft-qiskit)
- [Azure Quantum Pricing](https://azure.microsoft.com/pricing/details/azure-quantum/)
- [Bicep Documentation](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)

## Support

For issues with:

- **Azure Quantum**: Create support ticket in Azure Portal
- **This Project**: Open GitHub issue or contact project maintainers
