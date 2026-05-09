# Azure Quantum Setup Checklist

## Complete these steps to test your optimized quantum AI on real hardware

---

## ✅ Step-by-Step Setup (15 minutes)

### Step 1: Azure Account Setup (5 min)

- [ ] **Sign up for Azure** (if you don't have an account)
  - Go to: <https://azure.microsoft.com/free/>
  - Get $200 free credit (valid for 30 days)
  - No credit card required for free services

- [ ] **Install Azure CLI** (if not installed)

  ```powershell
  # Check if installed
  az --version

  # If not installed, download from:
  # https://aka.ms/installazurecliwindows
  ```

- [ ] **Login to Azure**

  ```powershell
  az login
  # Opens browser for authentication
  ```

- [ ] **Get your subscription ID**

  ```powershell
  # View your subscriptions
  az account list --output table

  # Copy the SubscriptionId - you'll need this!
  ```

### Step 2: Deploy Azure Quantum Workspace (5 min)

- [ ] **Navigate to Azure directory**

  ```powershell
  cd c:\Users\Bryan\OneDrive\AI\quantum-ai\azure
  ```

- [ ] **Update parameters file**

  Edit `quantum_workspace.parameters.json` and update:
  - `workspaceName`: Must be globally unique (e.g., `quantum-ai-bryan-2025`)
  - `storageAccountName`: Must be globally unique, lowercase, no hyphens (e.g., `quantumstoragebr2025`)

  **Example:**

  ```json
  {
    "workspaceName": {
      "value": "quantum-ai-bryan-2025"
    },
    "storageAccountName": {
      "value": "quantumstoragebr2025"
    }
  }
  ```

- [ ] **Set your subscription**

  ```powershell
  az account set --subscription "<your-subscription-id>"
  ```

- [ ] **Create resource group**

  ```powershell
  az group create --name rg-quantum-ai --location eastus
  ```

- [ ] **Deploy workspace**

  ```powershell
  az deployment group create `
    --resource-group rg-quantum-ai `
    --template-file quantum_workspace.bicep `
    --parameters quantum_workspace.parameters.json `
    --name quantum-deployment-$(Get-Date -Format 'yyyyMMddHHmmss')
  ```

  ⏱️ **This takes 2-3 minutes** - wait for "Succeeded"

- [ ] **Verify deployment**

  ```powershell
  # Check workspace was created
  az quantum workspace show `
    --resource-group rg-quantum-ai `
    --name quantum-ai-bryan-2025 `
    --output table
  ```

### Step 3: Update Configuration (2 min)

- [ ] **Edit quantum config**

  Open: `c:\Users\Bryan\OneDrive\AI\quantum-ai\config\quantum_config.yaml`

  Update the `azure` section:

  ```yaml
  azure:
    subscription_id: '<paste-your-subscription-id-here>'
    resource_group: 'rg-quantum-ai'
    workspace_name: 'quantum-ai-bryan-2025'  # Match what you deployed
    location: 'eastus'
    storage_account: 'quantumstoragebr2025'  # Match what you deployed
  ```

- [ ] **Save the file** (Ctrl+S)

### Step 4: Install Dependencies (1 min)

- [ ] **Activate virtual environment**

  ```powershell
  cd c:\Users\Bryan\OneDrive\AI\quantum-ai
  .\venv\Scripts\Activate.ps1
  ```

- [ ] **Install Azure Quantum packages**

  ```powershell
  pip install azure-quantum azure-identity qiskit-aer
  ```

### Step 5: Run Tests! (2 min)

- [ ] **Start with connection test**

  ```powershell
  python test_azure_quantum.py
  ```

- [ ] **Follow the interactive prompts**
  - Test 1: Verifies connection ✓
  - Test 2: Runs Bell state on hardware 🔔
  - Test 3: Tests your optimized circuit 🏆

---

## 🎯 Quick Start (Already have Azure?)

If you already have an Azure subscription:

```powershell
# 1. Login
az login

# 2. Deploy workspace (replace with unique names)
cd quantum-ai\azure
az group create --name rg-quantum-ai --location eastus
az deployment group create `
  --resource-group rg-quantum-ai `
  --template-file quantum_workspace.bicep `
  --parameters quantum_workspace.parameters.json

# 3. Update config/quantum_config.yaml with your details

# 4. Run test
cd ..
python test_azure_quantum.py
```

---

## 💰 Cost Estimate

### FREE Tier (Recommended for Testing)

- **IonQ Simulator**: Unlimited free usage ✅
- **Microsoft Simulator**: Unlimited free usage ✅
- **Storage**: First 5 GB free ✅
- **Azure Free Trial**: $200 credit ✅

#### Total for testing with simulators: $0.00

### Quantum Hardware (Optional)

- **IonQ QPU**: ~$0.36 per circuit (500 shots)
- **Quantinuum**: ~$1.50 per circuit
- **Start with simulator, upgrade when ready!**

---

## ⚠️ Important Notes

### Workspace Names Must Be Unique

- `workspace_name`: Can include letters, numbers, hyphens
- `storage_account`: Lowercase letters and numbers only (3-24 chars)
- If deployment fails with "name already exists", try different names

### Supported Regions

Azure Quantum is available in:

- **East US** (recommended - most providers)
- **West US**
- **West Europe**
- **North Europe**

### Provider Availability

After deployment, you'll have access to:

- ✅ **IonQ Simulator** (free, always available)
- ✅ **Microsoft QC Simulator** (free, always available)
- 💰 **IonQ QPU** (requires credits)
- 💰 **Quantinuum** (requires credits)

---

## 🔧 Troubleshooting

### "az: command not found"

**Solution:** Install Azure CLI from <https://aka.ms/installazurecliwindows>

### "Deployment failed: InvalidTemplate"

**Solution:** Check `quantum_workspace.parameters.json` syntax (must be valid JSON)

### "Name already exists"

**Solution:** Change workspace name and storage account name to something unique

### "Insufficient permissions"

**Solution:** Ensure you're logged in with an account that can create resources

### "No subscriptions found"

**Solution:**

1. Create Azure account at <https://azure.microsoft.com/free/>
2. Run `az login` again

---

## 📊 What Happens During Deployment?

The Bicep template creates:

1. **Storage Account** - Stores quantum job data
2. **Quantum Workspace** - Main quantum computing resource
3. **Quantum Providers** - Connections to IonQ, Quantinuum, Microsoft
4. **Resource Tags** - For organization and cost tracking

**Total Resources:** 4
**Deployment Time:** 2-3 minutes
**Monthly Cost (with free simulators):** ~$0.02-$0.05

---

## ✅ Success Indicators

You're ready when you see:

```text
✓ Successfully connected to Azure Quantum!

Available Quantum Backends:
  1. ionq.simulator
  2. ionq.qpu
  3. microsoft.estimator
```

---

## 🎉 Next Steps After Setup

Once deployed and tested:

1. **Run Bell State Test** - Verify quantum entanglement
2. **Test Optimized Circuit** - Your 90% accuracy configuration
3. **Compare Simulator vs Hardware** - See real quantum effects
4. **Scale Up** - Try 6-8 qubit circuits
5. **Deploy to Production** - Automate quantum ML pipeline

---

## 📚 Documentation Reference

- **Quick Start Guide**: `AZURE_QUANTUM_QUICKSTART.md`
- **Detailed Deployment**: `azure/DEPLOYMENT.md`
- **Test Script**: `test_azure_quantum.py`
- **Configuration**: `config/quantum_config.yaml`

---

## 💬 Need Help?

**Common Questions:**

**Q: Do I need quantum hardware credits?**
A: No! Start with free simulators (`ionq.simulator`). Only use hardware when you're ready to see real quantum effects.

**Q: How much will this cost?**
A: Testing with simulators is **completely free**. Real hardware costs ~$0.36 per circuit.

**Q: How long does testing take?**
A: Simulator results in 10-30 seconds. Hardware takes 2-10 minutes (includes queue time).

**Q: Can I use my existing Azure subscription?**
A: Yes! Just update `quantum_config.yaml` with your subscription ID.

**Q: What if deployment fails?**
A: Check troubleshooting section above. Most issues are due to unique naming requirements.

---

## 🚀 Ready to Test on Quantum Hardware?

**Start here:**

```powershell
# Make sure you're in the right directory
cd c:\Users\Bryan\OneDrive\AI\quantum-ai

# Run the complete test suite
python test_azure_quantum.py
```

**You'll test:**

- ✅ Connection to Azure Quantum
- 🔔 Bell state entanglement
- 🏆 Your optimized 90% accuracy circuit
- 🔬 Simulator vs hardware comparison

**Total time:** 10-15 minutes
**Cost (with simulator):** $0.00

---

*Let's run quantum ML on real quantum computers!* 🎊

---

**Current Status:**

- [x] Optimized configuration (90% accuracy)
- [x] Test scripts created
- [x] Documentation complete
- [ ] Azure workspace deployed ← **YOU ARE HERE**
- [ ] Hardware tested
- [ ] Production deployed
