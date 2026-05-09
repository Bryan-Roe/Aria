# 🚀 Azure Quantum Deployment - Quick Start Guide

## Overview

This guide walks you through deploying your quantum AI workspace to Azure Quantum, enabling you to run quantum circuits on real quantum hardware from IonQ, Quantinuum, and Rigetti.

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Azure subscription (create free: <https://azure.microsoft.com/free/>)
- [ ] Azure CLI installed (`az --version` to verify)
- [ ] Logged into Azure CLI (`az login`)
- [ ] PowerShell or Bash terminal
- [ ] This quantum-ai repository

---

## 📋 Step 1: Azure Subscription Setup

### 1.1 Check Current Subscription

```powershell
# List all subscriptions
az account list --output table

# Show current subscription
az account show
```

### 1.2 Set Active Subscription

```powershell
# Replace <subscription-id> with your subscription ID
az account set --subscription "<subscription-id>"

# Verify it's set
az account show --query "name"
```

### 1.3 Register Quantum Provider

```powershell
# Register Microsoft.Quantum resource provider
az provider register --namespace Microsoft.Quantum

# Check registration status
az provider show -n Microsoft.Quantum --query "registrationState"
```

**Expected output:** `"Registered"`

---

## 📋 Step 2: Configure Your Workspace

### 2.1 Update Configuration File

Edit `config/quantum_config.yaml`:

```yaml
azure:
  subscription_id: "YOUR-SUBSCRIPTION-ID-HERE"  # From az account show
  resource_group: "rg-quantum-ai"
  workspace_name: "quantum-ai-workspace"
  location: "eastus"  # or westus, westeurope
  storage_account: "quantumstorage"  # Must be globally unique
```

**Important:** Change `YOUR-SUBSCRIPTION-ID-HERE` to your actual subscription ID!

### 2.2 Verify Configuration

```powershell
cd c:\Users\Bryan\OneDrive\AI\quantum-ai
python -c "import yaml; print(yaml.safe_load(open('config/quantum_config.yaml'))['azure'])"
```

---

## 📋 Step 3: Deploy Infrastructure

### 3.1 Create Resource Group

```powershell
az group create `
  --name rg-quantum-ai `
  --location eastus
```

### 3.2 Deploy Quantum Workspace

```powershell
cd azure

az deployment group create `
  --resource-group rg-quantum-ai `
  --template-file quantum_workspace.bicep `
  --parameters quantum_workspace.parameters.json
```

**This takes ~2-5 minutes.** You'll see:

- ✅ Storage account created
- ✅ Quantum workspace created
- ✅ Provider connections established

### 3.3 Verify Deployment

```powershell
# List quantum workspaces
az quantum workspace list --resource-group rg-quantum-ai --output table

# Show workspace details
az quantum workspace show `
  --resource-group rg-quantum-ai `
  --workspace-name quantum-ai-workspace
```

---

## 📋 Step 4: Test Connection

### 4.1 Run Connection Test

```powershell
cd ..
python examples\azure_integration.py
```

**Expected output:**

```plaintext
✓ Configuration loaded
✓ Subscription ID found
✓ Attempting Azure connection...
```

### 4.2 Test with Python

```python
from src.azure_quantum_integration import AzureQuantumIntegration

azure = AzureQuantumIntegration()
workspace = azure.connect()
print("✓ Connected to Azure Quantum!")

# List available backends
backends = azure.list_backends()
print(f"Available backends: {backends}")
```

---

## 📋 Step 5: Run Your First Quantum Job

### 5.1 Create a Test Circuit

```python
from qiskit import QuantumCircuit
from src.azure_quantum_integration import AzureQuantumIntegration

# Create Bell state circuit
circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure([0, 1], [0, 1])

# Connect to Azure
azure = AzureQuantumIntegration()
workspace = azure.connect()

# Submit to IonQ simulator (FREE)
job = azure.submit_circuit(
    circuit=circuit,
    shots=100,
    job_name="my_first_quantum_job",
    backend="ionq.simulator"
)

print(f"Job submitted: {job.id}")

# Wait for results
results = azure.get_job_results(job)
print(f"Results: {results}")
```

### 5.2 Expected Results

```plaintext
Job submitted: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Job status: Succeeded
Results: {'00': 48, '11': 52}
```

This confirms entanglement! 🎉

---

## 💰 Cost Management

### Free Tier Options

**Microsoft Simulators:**

- ✅ `ionq.simulator` - FREE, unlimited
- ✅ H-series simulators - FREE tier available
- ✅ Perfect for development and testing

**Always start with simulators to avoid charges!**

### Paid Options

**IonQ (Trapped Ion):**

- Pricing: ~$0.00003 per gate-shot
- Example: 100-gate circuit × 1000 shots = ~$3.00
- Best for: Small algorithms, high fidelity

**Quantinuum (Trapped Ion):**

- Pricing: ~$0.00015 per circuit
- Credits-based system
- Best for: Error correction, complex algorithms

**Rigetti (Superconducting):**

- Contact for enterprise pricing
- Best for: Large-scale optimization

### Set Budget Alerts

```powershell
# Create budget alert (optional)
az consumption budget create `
  --budget-name quantum-ai-budget `
  --amount 100 `
  --time-grain Monthly `
  --resource-group rg-quantum-ai
```

---

## 🔒 Security Best Practices

### 1. Use Service Principal (Recommended for Automation)

```powershell
# Create service principal
az ad sp create-for-rbac `
  --name quantum-ai-sp `
  --role Contributor `
  --scopes /subscriptions/<subscription-id>/resourceGroups/rg-quantum-ai

# Save the output securely (appId, password, tenant)
```

### 2. Store Credentials Securely

#### Option A: Environment Variables

```powershell
$env:AZURE_QUANTUM_WORKSPACE = "quantum-ai-workspace"
$env:AZURE_QUANTUM_RESOURCE_GROUP = "rg-quantum-ai"
```

#### Option B: Azure Key Vault

```powershell
az keyvault create `
  --name quantum-ai-keyvault `
  --resource-group rg-quantum-ai `
  --location eastus
```

### 3. Enable Monitoring

```powershell
# Enable diagnostics
az monitor diagnostic-settings create `
  --name quantum-diagnostics `
  --resource-group rg-quantum-ai `
  --workspace quantum-ai-workspace `
  --logs '[{"category": "JobEvents", "enabled": true}]'
```

---

## 🐛 Troubleshooting

### Issue 1: "Subscription not found"

**Solution:**

```powershell
az login
az account set --subscription "<your-subscription-id>"
```

### Issue 2: "Provider not registered"

**Solution:**

```powershell
az provider register --namespace Microsoft.Quantum
# Wait 2-3 minutes, then:
az provider show -n Microsoft.Quantum --query registrationState
```

### Issue 3: "Storage account name already exists"

**Solution:** Change `storage_account` in `quantum_config.yaml` to a globally unique name:

```yaml
storage_account: "quantumstorage<your-initials><random-number>"
```

### Issue 4: "Authentication failed"

**Solution:**

```powershell
# Clear Azure CLI cache
az account clear
az login
```

### Issue 5: "Workspace creation failed"

**Solution:** Check deployment logs:

```powershell
az deployment group show `
  --resource-group rg-quantum-ai `
  --name <deployment-name>
```

---

## 📊 Monitoring Your Quantum Jobs

### View All Jobs

```powershell
az quantum job list `
  --resource-group rg-quantum-ai `
  --workspace-name quantum-ai-workspace `
  --output table
```

### Check Job Status

```powershell
az quantum job show `
  --resource-group rg-quantum-ai `
  --workspace-name quantum-ai-workspace `
  --job-id <job-id>
```

### Download Job Results

```python
from src.azure_quantum_integration import AzureQuantumIntegration

azure = AzureQuantumIntegration()
workspace = azure.connect()

# Get specific job
job = workspace.get_job("<job-id>")
results = job.get_results()
print(results)
```

---

## 🎯 Next Steps

### Immediate (First Day)

- [ ] Deploy workspace
- [ ] Test connection
- [ ] Run first job on simulator
- [ ] Review job results

### Short-term (First Week)

- [ ] Run quantum classifier on IonQ simulator
- [ ] Submit multiple jobs
- [ ] Monitor costs in Azure Portal
- [ ] Experiment with different providers

### Long-term (First Month)

- [ ] Run on real quantum hardware (IonQ/Quantinuum)
- [ ] Implement job batching
- [ ] Set up automated workflows
- [ ] Compare simulator vs. hardware results

---

## 📚 Additional Resources

### Documentation

- [Azure Quantum Docs](https://learn.microsoft.com/azure/quantum/)
- [IonQ Provider](https://learn.microsoft.com/azure/quantum/provider-ionq)
- [Quantinuum Provider](https://learn.microsoft.com/azure/quantum/provider-quantinuum)

### Tutorials

- [Azure Quantum Quickstart](https://learn.microsoft.com/azure/quantum/get-started-jupyter-notebook)
- [Submit Jobs Tutorial](https://learn.microsoft.com/azure/quantum/how-to-submit-jobs)
- [Cost Management](https://learn.microsoft.com/azure/quantum/azure-quantum-job-costs)

### Community

- [Azure Quantum Forum](https://quantum.microsoft.com/community)
- [GitHub Discussions](https://github.com/microsoft/qsharp/discussions)

---

## ✅ Deployment Checklist

Before going to production:

- [ ] Workspace deployed successfully
- [ ] Connection test passed
- [ ] First job completed on simulator
- [ ] Budget alerts configured
- [ ] Monitoring enabled
- [ ] Security best practices implemented
- [ ] Team trained on quantum concepts
- [ ] Backup plan for job failures

---

## 🎉 Success

If you completed all steps, you now have:

- ✅ Production Azure Quantum workspace
- ✅ Access to real quantum hardware
- ✅ Cost monitoring and security
- ✅ Working examples and templates

**You're ready to run quantum algorithms on real quantum computers!** 🌌

---

**Questions?** Check `azure/DEPLOYMENT.md` for detailed information or run:

```powershell
python examples\azure_integration.py
```

**Cost concerns?** Always test on FREE simulators first:

- `ionq.simulator` - Unlimited free usage
- Perfect for development and validation

**Happy Quantum Computing!** 🚀
