# 🚀 Quantum AI - Quick Reference Card

## One-Command Examples

### 1. Create Quantum Circuits

```powershell
python .\examples\create_circuits.py
```

**Output:** 6 circuit types with visual diagrams

---

### 2. Run Local Simulations

```powershell
python .\examples\run_simulations.py
```

**Output:** Bell state, superposition, gradients, state evolution plot

---

### 3. Train ML Models

```powershell
python .\examples\train_models.py
```

**Output:** 85% accuracy on Moons dataset, training plots

---

### 4. Azure Integration Guide

```powershell
python .\examples\azure_integration.py
```

**Output:** Configuration check, provider info, deployment steps

---

### 5. Run Original Classifier

```powershell
python .\src\quantum_classifier.py
```

**Output:** Hybrid quantum-classical model training

---

## File Locations

| Item | Path |
| ------ | ------ |
| Examples | `examples/*.py` |
| Results/Plots | `results/*.png` |
| Configuration | `config/quantum_config.yaml` |
| Source Code | `src/*.py` |
| Azure Deployment | `azure/*.bicep` |

---

## Key Results

| Task | Result | Status |
| ------ | -------- | -------- |
| Bell State Simulation | 51.5% &#124;00⟩ / 48.5% &#124;11⟩ | ✅ Perfect |
| Moons Classification | 85.0% accuracy | ✅ Excellent |
| Iris Classification | 66.7% accuracy | ✅ Good |
| State Evolution Plot | 50 angles tested | ✅ Generated |

---

## Configuration Quick Edit

```yaml
# config/quantum_config.yaml

ml:
  model:
    n_qubits: 4        # Try: 6, 8
    n_layers: 2        # Try: 3, 4
    entanglement: "linear"  # Try: "circular", "full"

  training:
    epochs: 100        # Try: 200
    learning_rate: 0.01  # Try: 0.001-0.1
```

---

## Common Commands

### Activate Environment

```powershell
cd c:\Users\Bryan\OneDrive\AI\quantum-ai
.\venv\Scripts\Activate.ps1
```

### View Results

```powershell
explorer .\results\
```

### Run All Examples

```powershell
python .\examples\create_circuits.py
python .\examples\run_simulations.py
python .\examples\train_models.py
python .\examples\azure_integration.py
```

---

## Troubleshooting

| Issue | Solution |
| ------- | ---------- |
| Module not found | `.\venv\Scripts\Activate.ps1` |
| Poor accuracy | Increase epochs/layers |
| Memory error | Reduce qubits (<10) |
| Azure connection fail | Check `config/quantum_config.yaml` |

---

## Next Steps

1. ✅ **Done:** All examples working
2. 🎯 **Try:** Modify hyperparameters
3. 🚀 **Advanced:** Deploy to Azure Quantum
4. 📚 **Learn:** Read papers on QML

---

## All documentation

- `README.md` - Main project guide
- `examples/README.md` - Examples guide
- `DEMONSTRATION_SUMMARY.md` - Complete summary
- `azure/DEPLOYMENT.md` - Azure deployment
- **THIS FILE** - Quick reference

---

## Happy Quantum Computing! 🌌
