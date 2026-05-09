# Azure Quantum Workspace - Portal Creation Guide

## Why Portal Creation?

After extensive testing, we've encountered **provider validation issues** with Bicep/ARM deployments:

- `InvalidProvider: Provider with id 'Microsoft' was not found`
- `InvalidSku: Sku with id 'pay-as-you-go-cred' was not found`
- API version and provider ID mismatches

The **Azure Portal automatically configures providers** correctly, avoiding these issues.

## Quick Create Steps (5 minutes)

### 1. Open Azure Portal

Navigate to: <https://portal.azure.com>

### 2. Create Azure Quantum Resource

1. Click **Create a resource**
2. Search for **"Azure Quantum"**
3. Click **Azure Quantum** tile → **Create**

### 3. Use Quick Create

1. **Subscription**: Select `Azure subscription 1` (a07fbd16-e722-446d-8efd-0681e85b725c)
2. **Resource Group**:
   - Select existing: `rg-quantum-ai` ✓ (already created)
3. **Workspace Name**: `quantum-ai-workspace`
4. **Region**: `East US`
5. **Storage Account**: Let Azure create automatically
6. Click **Quick create** button

**Quick create automatically adds**:

- ✅ IonQ provider (pay-as-you-go)
- ✅ Quantinuum provider (pay-as-you-go)
- ✅ Rigetti provider (pay-as-you-go)
- ✅ Microsoft Quantum Computing provider (free simulators)

### 4. Wait for Deployment

- Deployment typically takes **2-3 minutes**
- You'll see "Deployment in progress..." notification
- Wait for **"Your deployment is complete"**

### 5. Verify Workspace

1. Go to **Resource Groups** → `rg-quantum-ai`
2. You should see:
   - `quantum-ai-workspace` (Azure Quantum workspace)
   - Storage account (auto-generated name like `quantumstorage...`)
3. Click on `quantum-ai-workspace`
4. In the left menu, click **Providers** tab
5. Verify these providers are listed:
   - IonQ
   - Quantinuum
   - Rigetti
   - Microsoft Quantum Computing

## After Creation: Update Config

Once created, the deployment script will automatically detect and configure the workspace for local use.

Run:

```powershell
.\deploy_simple.ps1 -AutoYes
```

This will:

1. Detect the existing workspace
2. Update `config/quantum_config.yaml` with workspace details
3. Verify connectivity
4. Optionally run tests

## Next Steps

After portal creation:

1. ✅ Workspace is ready for quantum jobs
2. Run simulator tests: `python src/quantum_classifier.py`
3. Submit to Azure Quantum: `python src/azure_quantum_integration.py`
4. Optionally run test suite: `pytest tests/` (if tests exist)

## Cost Management

**Free resources** (no charges):

- Microsoft Quantum Computing simulators
- IonQ/Quantinuum/Rigetti syntax checkers and simulators

**Paid resources** (charges apply):

- IonQ Aria/Forte hardware: ~USD 12-98 per execution + gate costs
- Quantinuum H2: ~USD 0.00015 per circuit execution
- Rigetti QPUs: USD 0.02 per 10ms execution time

**Recommendation**: Start with free simulators, test thoroughly before moving to hardware.

## Troubleshooting

### Issue: Can't find Azure Quantum in search

**Solution**: Ensure you're in the correct Azure subscription. Some regions/subscriptions may have limited access.

### Issue: Deployment fails

**Solution**:

1. Check you have **Owner** or **Contributor** role on the subscription
2. Verify `rg-quantum-ai` resource group exists
3. Try **Advanced create** if Quick create fails

### Issue: No providers available

**Solution**: Providers are added automatically with Quick create. If missing:

1. Go to workspace → **Providers** tab
2. Click **Add** for each provider
3. Select billing plan (default is pay-as-you-go)

## Reference

- Portal docs: <https://learn.microsoft.com/en-us/azure/quantum/how-to-create-workspace>
- Pricing: <https://learn.microsoft.com/en-us/azure/quantum/pricing>
- Provider list: <https://learn.microsoft.com/en-us/azure/quantum/qc-target-list>
