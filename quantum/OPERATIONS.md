# Quantum AI – Operations & Navigation Guide

**Quick navigation for quantum AI workflow tasks.** Use this when you need to find the right command, doc, or workflow.

---

## Cost Tiers at a Glance

| Tier | Backend | Cost | Use When |
| --- | --- | --- | --- |
| 🟢 **Free** | Local (Qiskit Aer, PennyLane) | $0 | Developing, testing, learning locally |
| 🟢 **Free** | Azure simulators | $0 | Validating before real hardware runs |
| 🔴 **Paid** | Real QPU hardware | ~$0.00003–0.00015/gate-shot | Production quantum computing |

**Golden Rule:** Test locally → Validate on free Azure simulator → Run on paid QPU (with explicit cost confirmation)

---

## Find by Task

### 📚 Getting Started / Learning

| I want to... | Command/File | Time |
| --- | --- | --- |
| Understand the project | Read [`README.md`](./README.md) | 10 min |
| See quick examples | Read [`QUICK_REFERENCE.md`](./QUICK_REFERENCE.md) | 5 min |
| Run demo examples | `python examples/train_models.py` | 5 min |
| Learn via interactive UI | `./start_dashboard.sh` → `localhost:5000` | 15 min |
| See hardware results | Read [`HARDWARE_TEST_RESULTS.md`](./HARDWARE_TEST_RESULTS.md) | 10 min |
| Compare providers | Read [`PROVIDER_COMPARISON_RESULTS.md`](./PROVIDER_COMPARISON_RESULTS.md) | 15 min |
| Complete documentation index | Read [`INDEX.md`](./INDEX.md) | 10 min |

### 💻 Local Development (Free)

| I want to... | Command | Duration |
| --- | --- | --- |
| Train a quantum model locally | `python examples/train_models.py` | ~5 min |
| Run a simulation | `python examples/run_simulations.py` | ~2 min |
| Create quantum circuits | `python examples/create_circuits.py` | ~1 min |
| Interactive training dashboard | `./start_dashboard.sh` | ~15 min + |
| Edit hyperparameters | Edit `config/quantum_config.yaml` then retrain | varies |
| Run unit tests | `python ../scripts/test_runner.py --unit` | ~2 min |
| Run integration tests (no Azure) | `pytest -m "not slow and not azure"` | ~5 min |

### 🚀 Concurrent Quantum-LLM Training (NEW)

Run quantum circuits in background while LLM trains in foreground, with periodic parameter synchronization.

| I want to... | Command | Notes |
| --- | --- | --- |
| Run concurrent demo | `python examples/quantum_llm_concurrent_train.py --epochs 3` | Local only (~2 min) |
| Custom epochs | `python examples/quantum_llm_concurrent_train.py --epochs 10 --n-qubits 4` | Adjust n-qubits: 2-6 recommended |
| Tune quantum feedback | `python examples/quantum_llm_concurrent_train.py --quantum-weight 0.2` | Range [0.0-1.0]; default 0.1 |
| See training metrics | Run with `--epochs 5` and observe epoch logs | Prints loss + quantum-task ratio |
| Use custom data | Edit `scripts/quantum_llm_concurrent.py` SimpleLLMModel → load actual dataset | TensorDataset required |

**Architecture:**

- Main thread: LLM training loop (PyTorch)
- Background thread: Quantum circuit executor (PennyLane queued runner)
- Sync mechanism: Atomic parameter exchange every N batches
- Cost: Local/Azure simulators only (no QPU support yet)

**When to use:**

- ✅ Demonstrating hybrid quantum-classical ML
- ✅ Testing parameter feedback loops
- ❌ Production (stability) — use sequential trainer instead

**Performance Tuning:**

For runs >10k epochs, the system implements automatic optimizations:

- **Bounded output queue** (max 100 results): Prevents memory accumulation
- **Periodic drain** (every 10 epochs): Full result collection to prevent backlog
- **Garbage collection** (every 100 epochs): Releases tensor memory
- **Parameter caching**: Reuses cloned attention weights per epoch

**Checkpointing for long runs:**

```bash
# Save checkpoints every 1000 epochs
python examples/quantum_llm_concurrent_train.py \
    --epochs 20000 \
    --checkpoint-dir data_out/quantum_llm_concurrent/checkpoints

# Resume from checkpoint
python examples/quantum_llm_concurrent_train.py \
    --epochs 20000 \
    --resume-from data_out/quantum_llm_concurrent/checkpoints/checkpoint_epoch_5000.pt
```

**Recommended epoch ranges:**

- **3-10 epochs**: Quick validation (< 30 seconds)
- **100-1000 epochs**: Convergence testing (~1-5 minutes)
- **5000-10,000 epochs**: Performance baseline (~5 minutes)
- **20,000+ epochs**: Diminishing returns analysis (use checkpointing!)

**Monitor metrics:**

- `output_pending`: Should stay <100 (bounded queue working)
- Tasks/sec: Should remain constant across epochs (~230 tasks/sec)
- Loss convergence: Plateaus around 0.097-0.099 after 10k epochs

### ☁️ Azure Integration – FREE Simulators

| I want to... | Command | Notes |
| --- | --- | --- |
| Validate orchestrator config | `python ../scripts/quantum_autorun.py --dry-run` | No execution |
| Run on free Azure simulator | `python ../scripts/quantum_autorun.py --job azure_ionq_simulator --config config/quantum/quantum_autorun.yaml` | ✅ FREE, safe |
| Setup Azure workspace | `az login` then read [`AZURE_SETUP_CHECKLIST.md`](./AZURE_SETUP_CHECKLIST.md) | ~20 min |
| Check Azure credentials | `az account show` | Verify logged-in user |
| Deploy infrastructure | Read [`azure/DEPLOYMENT.md`](./azure/DEPLOYMENT.md) | ~30 min |
| Estimate costs (before running) | Use `estimate_quantum_cost` MCP tool or Azure dashboard | Free estimation |

### 🏃 Azure Integration – PAID QPU (Real Quantum Hardware)

⚙️ **Before running paid jobs:**

1. Set `azure_confirm_cost: true` in `config/quantum/quantum_autorun.yaml`
2. Start with ≤100 shots
3. Understand costs: see [Cost estimation](#cost-estimation)

| I want to... | Command | Safety |
| --- | --- | --- |
| Run on IonQ QPU | `python ../scripts/quantum_autorun.py --job azure_ionq_qpu --config config/quantum/quantum_autorun.yaml` | **Requires cost confirmation** |
| Run on Quantinuum QPU | `python ../scripts/quantum_autorun.py --job azure_quantinuum_qpu --config config/quantum/quantum_autorun.yaml` | **Requires cost confirmation** (avoid if possible, see [HARDWARE_TEST_RESULTS.md](./HARDWARE_TEST_RESULTS.md)) |
| Monitor job status | Check Azure Quantum portal or `data_out/quantum_autorun/<job>/status.json` | Real-time |
| Set cost limits/budgets | Use `quantum_cost_monitor.ps1` in `azure/` or Azure portal | Prevents surprises |

### 🛠️ MCP Server (AI Agent Tools)

| I want to... | Command | Tools Available |
| --- | --- | --- |
| Start MCP server | `python quantum_mcp_server.py` | 8 quantum tools |
| See available tools | Run server and ask `(list tools)` | All 8 tools listed |
| Use in Claude/Copilot | Point to `http://localhost:3000` | Full tool set |
| Example client | `python example_mcp_client.py` | Demonstrates all 8 tools |

**8 Available Tools:**

- `create_quantum_circuit` — build circuits
- `simulate_quantum_circuit` — test locally
- `get_quantum_circuit_properties` — query specs
- `connect_azure_quantum` — authenticate
- `list_quantum_backends` — show providers
- `submit_quantum_job` — run on hardware/simulator
- `estimate_quantum_cost` — preview costs
- `train_quantum_classifier` — ML training

### 📊 Dashboard & Visualization

| I want to... | Command | Features |
| --- | --- | --- |
| Interactive web dashboard | `./start_dashboard.sh` | Real-time training plots, hyperparameter tuning, session history |
| View training results | Open `results/` folder | Generated images and plots |
| Export training data | Download from dashboard or read `data_out/` | JSON/CSV formats |

### 📖 Documentation & References

| I need to know... | File | Purpose |
| --- | --- | --- |
| Project overview | [`README.md`](./README.md) | Architecture, features, installation |
| All quick commands | [`QUICK_REFERENCE.md`](./QUICK_REFERENCE.md) | One-liners, file locations, key results |
| Complete file index | [`INDEX.md`](./INDEX.md) | Docs, code, configs, results |
| Hardware test results | [`HARDWARE_TEST_RESULTS.md`](./HARDWARE_TEST_RESULTS.md) | Backend validation, accuracy, recommendations |
| Provider comparison | [`PROVIDER_COMPARISON_RESULTS.md`](./PROVIDER_COMPARISON_RESULTS.md) | Gate analysis, MPS accuracy, known issues |
| Training results | [`TRAINING_SESSION_SUMMARY.md`](./TRAINING_SESSION_SUMMARY.md) | Model performance metrics |
| Deployment steps | [`azure/DEPLOYMENT.md`](./azure/DEPLOYMENT.md) | Azure setup and infrastructure |
| Azure checklist | [`AZURE_SETUP_CHECKLIST.md`](./AZURE_SETUP_CHECKLIST.md) | Prerequisites, verification steps |
| MCP server guide | [`MCP_SERVER_README.md`](./MCP_SERVER_README.md) | How to use quantum tools as MCP |
| Dashboard docs | [`WEB_DASHBOARD_README.md`](./WEB_DASHBOARD_README.md) | UI guide, features, usage |

---

## Cost Estimation

### Local Development (Totally Free)

- Qiskit Aer simulator: unlimited
- PennyLane simulator: unlimited

### Azure Simulator (Free)

- ionq.simulator, quantinuum.sim.*, microsoft.simulator: **$0**

### Real Quantum Hardware (Paid)

- **IonQ:** ~$0.00015 per gate-shot (e.g., 100-qubit circuit, 1000 shots → ~$15)
- **Quantinuum:** ~$0.00003–0.0001 per gate-shot (pricing varies by circuit/shots)

**Example Costs:**

- 4-qubit circuit, 100 shots on IonQ: ~$0.06
- 6-qubit circuit, 1000 shots on IonQ: ~$0.90
- 10-qubit circuit, 1000 shots on IonQ: ~$15

**Safety Gates:**

1. Always test on free simulators first
2. Set `azure_confirm_cost: true` before ANY paid run
3. Use cost estimation tool to preview
4. Start with minimal shots (≤100) on hardware

---

## Key Conventions & Safety Limits

| Item | Limit | Reason |
| --- | --- | --- |
| **Local qubits** | ≤10 | Memory/performance |
| **Default shots** | ≤1000 | Cost control |
| **Circuit cache** | LRU+TTL | Avoid recomputation |
| **MCP timeout** | 60s | Non-blocking operations |
| **Config location** | `config/quantum_config.yaml` | Centralized settings |
| **Data input** | `datasets/` (read-only) | Immutability guarantee |
| **Data output** | `data_out/quantum_autorun/<job>/` (write-only) | Clean separation |
| **Tests (fast)** | `pytest -m "not slow and not azure"` | ~5 min local |
| **Dashboard UI** | `localhost:5000` | After `./start_dashboard.sh` |

---

## Decision Tree: Local vs. Azure vs. QPU

```text
┌─────────────────┐
│ Start here?     │
└────────┬────────┘
         │
    ┌────▼─────────────────────────────┐
    │ Testing/learning/development?    │
    │ YES → Local simulation (FREE)    │
    │ python examples/train_models.py  │
    └────┬──────────────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ Ready for real cloud?      │
    │ YES → Azure SIMULATOR      │
    │ (FREE, same API as QPU)    │
    │ azure_ionq_simulator job   │
    └────┬───────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │ Production quantum run?        │
    │ YES → Set cost confirmation    │
    │ azure_confirm_cost: true       │
    │ Then: azure_ionq_qpu job       │
    └───────────────────────────────┘
```

---

## Troubleshooting

| Problem | Solution |
| --- | --- |
| Can't import PennyLane | Install: `pip install pennylane azure-quantum` |
| Azure login fails | Run: `az login` and verify account |
| Circuit too slow locally | Reduce qubits (≤4) or shots (≤100) for testing |
| Don't know cost | Use `estimate_quantum_cost` MCP tool |
| Hardware result wrong | See [PROVIDER_COMPARISON_RESULTS.md](./PROVIDER_COMPARISON_RESULTS.md) for known issues |
| Want to try different backends | Edit `config/quantum_config.yaml`, section `backend:` |

---

## Next Steps

1. **New to project?** → Start with [`README.md`](./README.md) + `./start_dashboard.sh`
2. **Want to train models?** → Use dashboard or `python examples/train_models.py`
3. **Ready for Azure?** → Follow [`AZURE_SETUP_CHECKLIST.md`](./AZURE_SETUP_CHECKLIST.md)
4. **Using MCP?** → See [`MCP_SERVER_README.md`](./MCP_SERVER_README.md)
5. **Need reference?** → Keep [`QUICK_REFERENCE.md`](./QUICK_REFERENCE.md) handy
6. **Found a bug?** → Check [`HARDWARE_TEST_RESULTS.md`](./HARDWARE_TEST_RESULTS.md) first

---

**Version:** Updated March 2026  
**Status:** Maintained  
**Contact:** See repository CONTRIBUTING.md
