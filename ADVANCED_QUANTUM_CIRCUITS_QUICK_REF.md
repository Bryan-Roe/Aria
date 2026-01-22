# 🔮 Advanced Quantum Circuits - Quick Reference

**Quick access guide for quantum circuit architectures and training**

---

## 🚀 Quick Start

### Test Circuit Generation
```bash
# See all circuit types with statistics
python scripts/training/advanced_quantum_circuits.py
```

### Train Models with Advanced Circuits
```bash
# Quick training (3 models, ~1.4s)
python scripts/training/enhanced_quantum_gguf_train.py --full

# View results
cat data_out/enhanced_quantum_gguf/training_summary.json | python -m json.tool
```

---

## 🎯 Circuit Types

### 1. **VQE Ansatz** (Optimization)
```
Qubits: 6-8
Layers: 3-4
Gates: 50-94
Purpose: Ground state optimization, molecular simulations
```

### 2. **QAOA Circuit** (Combinatorial Optimization)
```
Qubits: 6-8
Layers: 3-5
Gates: 67-83
Purpose: Graph problems, scheduling, routing
```

### 3. **Quantum Convolutional** (Feature Extraction)
```
Qubits: 6
Gates: 30-54
Purpose: Image/pattern recognition, spatial features
```

### 4. **Quantum Attention** (Sequence Processing)
```
Qubits: 6-8
Heads: 1-4
Gates: 22-36
Purpose: NLP, time-series, sequence modeling
```

### 5. **Strongly Entangling** (Maximum Expressibility)
```
Qubits: 6-12
Layers: 2-5
Gates: 47-189
Purpose: Universal quantum approximation
```

### 6. **Amplitude Encoding** (Data Loading)
```
Qubits: 4-6
Encoding Dim: 16-64
Gates: 17-42
Purpose: Classical data → quantum state
```

### 7. **Hybrid Quantum-ML** (General Purpose)
```
Qubits: 6-16
Gates: 41-111
Purpose: Combined quantum-classical ML
```

---

## 📊 Model Configurations

### Lite Model (10 qubits, 47 params)
```yaml
quantum_features:
  entanglement: {qubits: 6, layers: 2}    # Strongly entangling
  amplitude_encoding: {qubits: 4, layers: 1}
quantization: q4_0
training_time: ~0.9s
```

### Standard Model (24 qubits, 139 params)
```yaml
quantum_features:
  entanglement: {qubits: 8, layers: 3}
  vqe_ansatz: {qubits: 6, layers: 3}
  quantum_conv: {qubits: 6, layers: 2}
  amplitude_encoding: {qubits: 4, layers: 2}
quantization: q5_0
training_time: ~0.1s
```

### Pro Model (42 qubits, 328 params)
```yaml
quantum_features:
  entanglement: {qubits: 12, layers: 4}
  vqe_ansatz: {qubits: 8, layers: 4}
  qaoa_mixer: {qubits: 8, layers: 5}
  quantum_attention: {qubits: 8, layers: 2}
  amplitude_encoding: {qubits: 6, layers: 2}
quantization: q8_0
training_time: ~0.09s
```

---

## 🔧 Circuit Builder API

### Basic Usage
```python
from advanced_quantum_circuits import AdvancedQuantumCircuitBuilder

# Create builder
builder = AdvancedQuantumCircuitBuilder(num_qubits=8, circuit_name="my_circuit")

# Build circuit
circuit = builder\
    .hadamard_layer()\
    .rotation_layer("RY", "input")\
    .circular_entanglement()\
    .phase_gates()\
    .build_vqe_ansatz(num_layers=3)
```

### Entanglement Patterns
```python
# Linear: 0→1, 1→2, 2→3, ...
builder.linear_entanglement()

# Circular: Linear + last→first
builder.circular_entanglement()

# Star: center→all others
builder.star_entanglement(center=0)

# Brick-layer: Alternating pairs
builder.brick_layer_entanglement(layer=0)  # Even pairs
builder.brick_layer_entanglement(layer=1)  # Odd pairs

# Full: All-to-all
builder.full_entanglement()
```

### Pre-built Circuits
```python
# VQE (variational eigensolver)
circuit = builder.build_vqe_ansatz(num_layers=3)

# QAOA (optimization)
circuit = builder.build_qaoa_circuit(num_layers=3, problem_size=8)

# Quantum convolution
circuit = builder.build_quantum_convolutional_layer()

# Multi-head attention
circuit = builder.build_quantum_attention(num_heads=2)

# Strongly entangling
circuit = builder.build_strongly_entangling_layer(num_layers=3)

# Amplitude encoding
circuit = builder.build_amplitude_encoding(encoding_dim=256)
```

---

## 📈 Performance Metrics

### Training Speed
```
Lite:     0.93s (10 qubits, 47 params)
Standard: 0.14s (24 qubits, 139 params)
Pro:      0.09s (42 qubits, 328 params)
Total:    1.40s for all 3 models
```

### Improvement Over Basic Circuits
```
Parameters:  514 vs 108  = 4.76x ↑
Qubits:      76 vs 60    = 1.27x ↑
Gate Types:  8 vs 3      = 2.67x ↑
Circuits:    7 vs 3      = 2.33x ↑
Max Depth:   189 vs 50   = 3.78x ↑
Patterns:    4 vs 1      = 4.00x ↑
```

### Gate Distribution (Pro Model)
```
RY:   156 gates (36%)  - Y-axis rotations
RZ:   96 gates  (22%)  - Z-axis rotations
CNOT: 98 gates  (23%)  - Entanglement
RX:   40 gates  (9%)   - X-axis rotations
RZZ:  32 gates  (7%)   - Two-qubit Z rotation
S:    6 gates   (1%)   - Phase gate
T:    4 gates   (1%)   - π/8 phase gate
```

---

## 🎨 Circuit Visualization

### VQE Ansatz Pattern
```
|0⟩ [RY][RZ][●]---[RY][RZ][●]---[RY][RZ]
|1⟩ [RY][RZ][⊕][●][RY][RZ][⊕][●][RY][RZ]
|2⟩ [RY][RZ]---[⊕][RY][RZ]---[⊕][RY][RZ]
```

### QAOA Pattern
```
|0⟩ [H][RZZ]------[RX][RZZ]------[RX]
|1⟩ [H][RZZ][RZZ] [RX][RZZ][RZZ] [RX]
|2⟩ [H]-----[RZZ] [RX]-----[RZZ] [RX]
     ^^^^^^^^^^^^      ^^^^^^^^^^^^
     Problem H.        Mixer H.
```

### Quantum Attention (2 heads)
```
Head 0:
|0⟩ [RY][RZ][●]---[RY]
|1⟩ [RY][RZ][⊕][●][RY]
|2⟩ [RY][RZ]---[⊕][RY]

Head 1:
|3⟩ [RY][RZ][●]---[RY]
|4⟩ [RY][RZ][⊕][●][RY]
|5⟩ [RY][RZ]---[⊕][RY]
```

---

## 🔍 Circuit Analysis Tools

### Get Circuit Statistics
```python
import json
from pathlib import Path

# Load circuit data
circuits_file = Path("data_out/enhanced_quantum_gguf/phi35-quantum-pro/quantum_circuits.json")
with open(circuits_file) as f:
    circuits = json.load(f)

# Analyze each circuit
for name, circuit in circuits.items():
    print(f"{name}:")
    print(f"  Qubits: {circuit['num_qubits']}")
    print(f"  Gates: {circuit['total_gates']}")
    print(f"  Depth: {circuit['circuit_depth']}")
    print(f"  Parameters: {circuit['num_parameters']}")
    print(f"  Gate counts: {circuit['gate_counts']}")
    print(f"  Topology: {circuit['topology']}")
```

### Generate Circuit Visualization
```python
from advanced_quantum_circuits import generate_circuit_visualization

# Load and visualize
viz = generate_circuit_visualization(circuit)
print(viz)
```

---

## 🧪 Testing & Validation

### Validate Circuit Generation
```bash
# Test all complexity levels
python scripts/training/advanced_quantum_circuits.py

# Expected output:
# - Lite: 6 qubits, 7 circuit types
# - Standard: 10 qubits, 7 circuit types
# - Pro: 16 qubits, 7 circuit types
```

### Inspect Training Output
```bash
# View GGUF files
ls -lh data_out/enhanced_quantum_gguf/*/phi35-*.gguf

# Check circuit definitions
cat data_out/enhanced_quantum_gguf/phi35-quantum-pro/quantum_circuits.json | jq '.entanglement'

# Verify metadata
cat data_out/enhanced_quantum_gguf/phi35-quantum-pro/gguf_metadata.json | jq '.quantum_info'
```

### Compare Models
```python
import json

models = ["lite", "standard", "pro"]
for model in models:
    path = f"data_out/enhanced_quantum_gguf/phi35-quantum-{model}/quantum_circuits.json"
    with open(path) as f:
        data = json.load(f)
    
    total_gates = sum(c['total_gates'] for c in data.values())
    total_qubits = sum(c['num_qubits'] for c in data.values())
    
    print(f"{model.upper()}: {total_qubits}q, {total_gates} gates")
```

---

## 🚀 Advanced Usage

### Custom Circuit Configuration
```python
# Edit enhanced_quantum_gguf_train.py, add new config:
{
    "name": "custom-quantum-model",
    "base_model": "microsoft/Phi-3.5-mini-instruct",
    "quantization": "q5_0",
    "samples": 15,
    "quantum_features": {
        "vqe_ansatz": {"qubits": 10, "layers": 5},
        "quantum_attention": {"qubits": 8, "layers": 3},
        "qaoa_mixer": {"qubits": 12, "layers": 4}
    }
}
```

### Add New Circuit Type
```python
# In advanced_quantum_circuits.py:
def build_custom_circuit(self, param1, param2) -> Dict[str, Any]:
    """Build custom quantum circuit"""
    # Your circuit logic here
    self.hadamard_layer()
    self.rotation_layer("RY", "custom_param")
    # ... more gates ...
    return self.to_circuit_dict("Custom Circuit Description")
```

### Integrate with Training
```python
# In enhanced_quantum_gguf_train.py, update circuit_types:
circuit_types = {
    "custom_circuit": "custom",  # Add your mapping
    # ... existing mappings ...
}

# In create_quantum_circuit(), add case:
elif circuit_type == "custom":
    return builder.build_custom_circuit(param1, param2)
```

---

## 📚 Key Files

### Source Code
- `scripts/training/advanced_quantum_circuits.py` - Circuit builder module
- `scripts/training/enhanced_quantum_gguf_train.py` - Training orchestrator

### Output
- `data_out/enhanced_quantum_gguf/training_summary.json` - Training results
- `data_out/enhanced_quantum_gguf/*/quantum_circuits.json` - Circuit definitions
- `data_out/enhanced_quantum_gguf/*/phi35-*.gguf` - Trained models

### Documentation
- `ADVANCED_QUANTUM_CIRCUITS_COMPLETE.md` - Full documentation
- `QUANTUM_GGUF_TRAINING_COMPLETE.md` - Basic circuits (reference)

---

## 💡 Tips & Best Practices

### Circuit Design
- Start with 6-8 qubits for testing
- Use brick-layer entanglement for better connectivity
- Add phase gates (S/T) for richer gate set
- Alternate entanglement patterns across layers

### Performance
- More qubits ≠ better performance (check classical simulation limits)
- Circuit depth impacts noise (keep < 200 gates for NISQ devices)
- Use q4_0 for edge deployment, q8_0 for accuracy

### Debugging
- Use `--dry-run` to validate configs
- Check circuit topology with `circuit['topology']`
- Visualize circuits before training
- Monitor gate counts per circuit type

---

## 🎯 Common Patterns

### Hybrid Quantum-Classical Layer
```python
builder\
    .hadamard_layer()              # Superposition
    .rotation_layer("RY", "input") # Classical data encoding
    .circular_entanglement()       # Quantum processing
    .rotation_layer("RZ", "hidden")# Quantum features
    .brick_layer_entanglement(0)   # More entanglement
    .rotation_layer("RY", "output")# Readout layer
```

### Optimization Circuit (VQE + QAOA)
```python
vqe = builder.build_vqe_ansatz(layers=3)
qaoa = builder.build_qaoa_circuit(layers=3, problem_size=8)
# Use VQE for ground state, QAOA for combinatorial
```

### Feature Extraction Pipeline
```python
# Encode → Convolve → Attend → Classify
encode = builder.build_amplitude_encoding(encoding_dim=256)
conv = builder.build_quantum_convolutional_layer()
attn = builder.build_quantum_attention(num_heads=2)
# Extract features hierarchically
```

---

**For detailed documentation, see [ADVANCED_QUANTUM_CIRCUITS_COMPLETE.md](ADVANCED_QUANTUM_CIRCUITS_COMPLETE.md)**
