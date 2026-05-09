# 🚀 Azure Quantum Quick Start Guide

**Run Your Optimized Quantum AI on Real Quantum Hardware!**

---

## 📋 Prerequisites Checklist

Before testing on real quantum hardware, ensure you have:

- [ ] **Azure Account** - [Sign up for free trial](https://azure.microsoft.com/free/) ($200 credit)
- [ ] **Azure CLI** - Installed and logged in (`az login`)
- [ ] **Azure Quantum Workspace** - Deployed (see [Quick Start](#-quick-start-5-minutes))
- [ ] **Quantum Credits** - IonQ/Quantinuum credits purchased or trial credits
- [ ] **Updated Config** - `config/quantum_config.yaml` with your Azure details

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Deploy Azure Quantum Workspace

```powershell
# Navigate to Azure infrastructure directory
cd quantum-ai\azure

# Login to Azure
az login

# Set your subscription
az account set --subscription "<your-subscription-id>"

# Create resource group
az group create --name rg-quantum-ai --location eastus

# Deploy Bicep template
az deployment group create `
  --resource-group rg-quantum-ai `
  --template-file quantum_workspace.bicep `
  --parameters quantum_workspace.parameters.json
```

**Deployment time:** ~2-3 minutes

### Step 2: Update Configuration

Edit `config/quantum_config.yaml`:

```yaml
azure:
  subscription_id: '<your-subscription-id>'  # From: az account show
  resource_group: 'rg-quantum-ai'
  workspace_name: 'quantum-ai-workspace'
  location: 'eastus'
  storage_account: '<your-storage-account-name>'  # From deployment output
```

### Step 3: Authenticate

```powershell
# Simple authentication (development)
az login

# The Azure SDK will automatically use your credentials
```

### Step 4: Run Test Suite

```powershell
# Navigate back to project root
cd ..

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run comprehensive hardware test
python test_azure_quantum.py
```

**Test duration:** 5-15 minutes (depending on backend)

---

## 🎯 What Gets Tested

The `test_azure_quantum.py` script runs **4 comprehensive tests**:

### Test 1: Connection Verification ✅

- Connects to your Azure Quantum workspace
- Lists all available quantum backends
- Verifies authentication

**Expected Output:**

```text
✓ Successfully connected to Azure Quantum!

Available Quantum Backends:
  1. ionq.simulator
  2. ionq.qpu
  3. quantinuum.sim.h1-1sc
  4. quantinuum.qpu.h1-1
```

### Test 2: Bell State on Hardware 🔔

- Submits a simple entanglement test
- Verifies quantum behavior
- **Demonstrates real quantum entanglement!**

**Expected Results:**

```text
Measurement counts:
  00: 487 (48.7%)
  11: 513 (51.3%)

Entanglement Quality: 100%
✓ Excellent quantum entanglement observed!
```

### Test 3: Optimized Circuit (90% Accuracy) 🏆

- Runs your **optimized 3-layer quantum classifier**
- Tests the configuration that achieved 90% accuracy
- Collects 500 shots for statistical analysis

**Circuit Details:**

- **4 qubits** (optimized)
- **3 layers** (87.5% accuracy)
- **Linear entanglement** (82.5% accuracy)
- **Learning rate 0.1** (90% accuracy)

### Test 4: Simulator vs Hardware Comparison 🔬

- Runs same circuit on simulator and real hardware
- Compares ideal vs noisy quantum behavior
- **Demonstrates real-world quantum computing effects!**

---

## 💰 Cost Breakdown

### FREE Options (Start Here!)

| Service | Usage | Cost |
|---------|-------|------|
| **IonQ Simulator** | Unlimited | **$0.00** |
| **Microsoft QC Simulator** | Unlimited | **$0.00** |
| **Azure Storage** | First 5 GB | **$0.00** |
| **Free Trial** | $200 credit | **$0.00** |

**Recommendation:** Use simulators for all development and testing!

### Paid Quantum Hardware

| Provider | Pricing Model | Estimated Cost |
|----------|---------------|----------------|
| **IonQ QPU** | $0.00003 per gate-shot | ~$0.50 per circuit |
| **Quantinuum H1-1** | $0.00015 per circuit | ~$1.50 per circuit |
| **Rigetti** | Per-shot pricing | ~$0.30 per circuit |

**For our optimized circuit:**

- **Gates:** ~24 per circuit
- **Shots:** 500 (configurable)
- **IonQ Cost:** 24 gates × 500 shots × $0.00003 = **~$0.36**

**Budget Tip:** Start with 100 shots ($0.07) to test, then scale up!

---

## 📊 Understanding Results

### Simulator Results (Ideal Quantum Behavior)

```text
Bell State - Simulator:
  00: 50.0%
  11: 50.0%
```

**Perfect 50/50 split** - This is ideal quantum superposition!

### Hardware Results (Real Quantum Computer)

```text
Bell State - Hardware:
  00: 47.3%
  11: 48.9%
  01:  2.1%
  10:  1.7%
```

**Slight noise observed** - This is EXPECTED and NORMAL!

**Why the difference?**

- **Decoherence:** Quantum states decay over time
- **Gate errors:** Physical gate operations aren't perfect (~99.5% fidelity)
- **Measurement errors:** Readout isn't 100% accurate
- **This is REAL quantum computing!** 🎉

### Optimized Circuit Results

```text
Measurement distribution (top 10 states):
  0000:   87 (17.4%) ████████
  1111:   82 (16.4%) ████████
  0101:   45 ( 9.0%) ████
  1010:   43 ( 8.6%) ████
  ...

Quantum State Analysis:
  Unique states measured: 14/16
  Entropy: 3.21 / 4.00
  Distribution uniformity: 80.3%
```

**What This Means:**

- **Multiple states:** Your quantum circuit explores quantum superposition
- **High entropy:** Circuit creates complex quantum states (good for ML!)
- **Uniform distribution:** Well-balanced exploration of state space

---

## 🔧 Troubleshooting

### Error: "Failed to connect to Azure Quantum"

**Solutions:**

1. Verify login: `az login`
2. Check subscription: `az account show`
3. Verify workspace exists:

   ```powershell
   az quantum workspace show -g rg-quantum-ai -n quantum-ai-workspace
   ```

4. Update `quantum_config.yaml` with correct subscription ID

### Error: "No backends available"

**Solutions:**

1. Check provider registration in Azure Portal
2. Ensure workspace has providers enabled (IonQ, Quantinuum)
3. Accept provider terms of service in Azure Portal
4. Wait 5-10 minutes after workspace creation

### Error: "Insufficient credits"

**Solutions:**

1. Use simulators (free): `ionq.simulator`
2. Purchase quantum credits in Azure Portal
3. Use Azure free trial credits ($200)
4. Reduce shots (500 → 100) to lower cost

### Error: "Job failed" or "Circuit execution failed"

**Solutions:**

1. Check circuit depth (too deep = more errors)
2. Reduce shots for initial tests
3. Use simulator first to validate circuit
4. Check Azure Portal for detailed error messages
5. Verify circuit is properly measured (all qubits measured)

### Slow Job Execution

**Normal Behavior:**

- **Simulator:** 10-30 seconds
- **Queue time:** 1-5 minutes (depends on load)
- **Hardware execution:** 2-10 minutes
- **Peak times:** Up to 30 minutes queue

**Tips:**

- Run during off-peak hours (US night time)
- Use smaller shot counts for testing
- Submit multiple jobs in parallel

---

## 🎓 Next Steps After Testing

### 1. Analyze Hardware Results

Compare your hardware results against simulator results:

```powershell
# Check saved results
cd results
ls *.json

# View specific result
cat bell_state_results_<job-id>.json
```

### 2. Scale Up Your Experiments

Try more complex circuits:

```python
# Increase qubits (update quantum_config.yaml)
n_qubits: 6  # Up from 4

# Increase layers
n_layers: 4  # Up from 3

# Increase shots for better statistics
shots: 1000  # Up from 500
```

### 3. Train with Hardware Data

Use real hardware results to train your quantum classifier:

```powershell
# Run training with Azure backend
python .\src\quantum_classifier.py --backend azure --provider ionq.qpu
```

### 4. Compare Providers

Test different quantum hardware:

```python
# IonQ (ion trap, high fidelity)
backend = "ionq.qpu"

# Quantinuum (high quality, more expensive)
backend = "quantinuum.qpu.h1-1"

# Rigetti (superconducting, fast)
backend = "rigetti.qpu.aspen-m-3"
```

### 5. Deploy Production Pipeline

Set up automated quantum ML pipeline:

1. **Data preprocessing** (classical)
2. **Quantum circuit generation** (parameterized)
3. **Hardware submission** (Azure Quantum)
4. **Results aggregation** (classical)
5. **Model update** (hybrid training)

---

## 📚 Additional Resources

### Official Documentation

- [Azure Quantum Overview](https://docs.microsoft.com/azure/quantum/)
- [Qiskit on Azure](https://docs.microsoft.com/azure/quantum/quickstart-microsoft-qiskit)
- [IonQ Documentation](https://ionq.com/docs)
- [Quantinuum Docs](https://www.quantinuum.com/products)

### Your Project Files

- **Deployment Guide:** `azure/DEPLOYMENT.md` (detailed Azure setup)
- **Optimization Report:** `FINAL_OPTIMIZATION_REPORT.md` (90% accuracy results)
- **Training Guide:** `TRAINING_REPORT.md` (7 dataset results)
- **Custom Data:** `CUSTOM_DATASET_GUIDE.md` (use your own data)

### Cost Management

- [Azure Quantum Pricing](https://azure.microsoft.com/pricing/details/azure-quantum/)
- [Cost Calculator](https://azure.microsoft.com/pricing/calculator/)
- [Free Credits](https://azure.microsoft.com/free/)

---

## 🎉 Success Criteria

You've successfully tested on quantum hardware when you see:

✅ **Connection Success**

```text
✓ Successfully connected to Azure Quantum!
```

✅ **Bell State Entanglement**

```text
Entanglement Quality: 80%+
✓ Excellent quantum entanglement observed!
```

✅ **Optimized Circuit Execution**

```text
✓ Job submitted successfully!
Status: JobStatus.COMPLETED
```

✅ **Results Retrieved**

```text
✓ Results saved to results/
```

---

## 💡 Pro Tips

### Cost Optimization

1. **Always test on simulator first** (free, instant)
2. **Start with 100 shots**, scale to 500 only if needed
3. **Optimize circuit depth** before hardware submission
4. **Use batch jobs** to reduce queue time overhead
5. **Monitor spending** in Azure Cost Management

### Performance Optimization

1. **Transpile circuits** before submission (reduce gate count)
2. **Use provider-native gates** (IonQ uses GPI, GPI2, MS)
3. **Minimize circuit depth** (fewer gates = less decoherence)
4. **Calibrate on Bell states** before complex circuits
5. **Run during off-peak hours** for faster queue times

### Best Practices

1. **Save all job IDs** for later retrieval
2. **Log hyperparameters** with each run
3. **Compare multiple providers** (IonQ vs Quantinuum)
4. **Version control results** (Git commit after each run)
5. **Document hardware quirks** you discover

---

## 🚀 You're Ready

You now have everything needed to:

✅ Deploy Azure Quantum workspace
✅ Connect to real quantum hardware
✅ Submit your optimized 90% accuracy circuit
✅ Analyze quantum vs classical results
✅ Scale to production quantum ML

**Run the test now:**

```powershell
python test_azure_quantum.py
```

**Welcome to the quantum computing era!** 🎊

---

*Generated: October 31, 2025*
*Quantum AI Project - Azure Quantum Integration*
*Status: PRODUCTION READY*
