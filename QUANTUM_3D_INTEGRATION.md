# Quantum-3D World Integration

## Overview

The Aria 3D world system is now integrated with quantum models, enabling:

1. **Quantum-powered world generation** - Object placement using quantum superposition
2. **Quantum circuit visualization** - Real quantum circuits rendered as 3D objects
3. **Quantum state tracking** - Objects maintain quantum measurement data
4. **Hybrid classical-quantum rendering** - Seamless fallback to classical methods

## Architecture

```
aria_web/
├── server.py                      # Main server with quantum endpoints
├── quantum_world_generator.py     # Quantum world generation logic
├── quantum-world.html             # Demo UI for quantum features
└── index.html                     # Main Aria character interface

quantum-ai/src/
├── quantum_classifier.py          # Core quantum ML classifier
├── hybrid_qnn.py                  # Quantum neural network
└── azure_quantum_integration.py   # Azure Quantum backend
```

## Features

### 1. Quantum World Generation

Uses quantum circuits to generate naturally distributed object placements:

```python
# Backend: quantum_world_generator.py
generator = get_quantum_generator(n_qubits=4)
world = generator.generate_quantum_world(theme='quantum', count=8, seed=42)
```

**How it works:**
- Creates a quantum circuit with N qubits
- Encodes world parameters (count, seed) into rotation gates
- Uses entanglement (CNOT gates) for correlated positions
- Measures expectation values to determine x, y coordinates
- Maps quantum states [-1, 1] to stage coordinates [5, 95]

**Benefits:**
- Natural distribution without manual spacing algorithms
- Quantum randomness for truly unpredictable layouts
- Deterministic with seed for reproducibility
- Graceful fallback to classical methods if quantum unavailable

### 2. Quantum Circuit Visualization

Renders quantum circuits as interactive 3D objects:

```python
# Visualize a Bell state circuit
world = generator.visualize_quantum_circuit({
    'name': 'bell_state',
    'n_qubits': 4,
    'gates': [
        {'type': 'H', 'qubits': [0]},
        {'type': 'CNOT', 'qubits': [0, 1]},
        {'type': 'RY', 'qubits': [2]}
    ]
})
```

**Circuit elements as objects:**
- ⚛️ Qubits - Horizontal lines across the stage
- 🎯 Hadamard gates (H)
- ❌ Pauli-X gates
- 🌀 Pauli-Y gates
- ⚡ Pauli-Z gates
- 🔗 CNOT gates (entanglement)
- 🔄 Rotation-Y gates
- 🌐 Rotation-Z gates
- 📊 Measurements

### 3. API Endpoints

#### Generate Quantum World
```bash
POST /api/aria/world
Content-Type: application/json

{
  "theme": "quantum",
  "count": 8,
  "seed": 42,
  "use_quantum": true
}
```

**Response:**
```json
{
  "status": "success",
  "theme": "quantum",
  "count": 8,
  "used_quantum": true,
  "objects": {
    "quantum_obj_0": {
      "id": "quantum_obj_0",
      "emoji": "⚛️",
      "position": {"x": 45, "y": 60},
      "state": "on_stage",
      "properties": {
        "scale": 1.2,
        "rotation": 45,
        "quantum_generated": true
      },
      "quantum_state": [-0.8, 0.6, 0.3, -0.4]
    }
  },
  "environment": {
    "theme": "quantum",
    "generation_method": "quantum",
    "quantum_qubits": 4,
    "seed": 42
  }
}
```

#### Visualize Quantum Circuit
```bash
POST /api/aria/quantum/circuit
Content-Type: application/json

{
  "circuit_data": {
    "name": "custom_circuit",
    "n_qubits": 4,
    "gates": [
      {"type": "H", "qubits": [0]},
      {"type": "CNOT", "qubits": [0, 1]}
    ]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "objects": {
    "qubit_0": {
      "emoji": "⚛️",
      "position": {"x": 10, "y": 20},
      "properties": {"type": "qubit", "index": 0}
    },
    "gate_0": {
      "emoji": "🎯",
      "position": {"x": 30, "y": 20},
      "properties": {"type": "gate", "gate_type": "H"}
    }
  },
  "environment": {
    "theme": "quantum_circuit",
    "generation_method": "quantum_visualization",
    "n_qubits": 4
  },
  "circuit_data": { /* original circuit spec */ }
}
```

## Usage

### Quick Start

1. **Start the Aria server:**
```bash
cd aria_web
python server.py
# Server runs on http://localhost:8080
```

2. **Open the quantum demo:**
```
http://localhost:8080/quantum-world.html
```

3. **Generate a quantum world:**
- Select theme (quantum, nature, space, ocean, tech)
- Set object count (4-16)
- Optional: Set seed for reproducibility
- Check "Use Quantum Generation"
- Click "Generate World"

4. **Visualize a quantum circuit:**
- Click "Visualize Circuit" button
- See quantum gates and qubits as interactive objects

### Frontend Integration

```javascript
// Generate quantum world
const response = await fetch('/api/aria/world', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        theme: 'quantum',
        count: 8,
        use_quantum: true,
        seed: Date.now()
    })
});

const data = await response.json();
console.log('Quantum world:', data);

// Visualize circuit
const circuitResponse = await fetch('/api/aria/quantum/circuit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        circuit_data: {
            name: 'my_circuit',
            n_qubits: 4,
            gates: [
                { type: 'H', qubits: [0] },
                { type: 'CNOT', qubits: [0, 1] }
            ]
        }
    })
});

const circuitData = await circuitResponse.json();
console.log('Circuit visualization:', circuitData);
```

### Backend Integration

```python
# In server.py or custom endpoint
from aria_web.quantum_world_generator import get_quantum_generator

# Create generator
generator = get_quantum_generator(n_qubits=4)

# Generate quantum world
world = generator.generate_quantum_world('nature', count=10, seed=12345)

# Access quantum states
for obj_id, obj in world['objects'].items():
    if 'quantum_state' in obj:
        print(f"{obj_id}: {obj['quantum_state']}")

# Visualize custom circuit
circuit = generator.visualize_quantum_circuit({
    'name': 'grover',
    'n_qubits': 3,
    'gates': [
        {'type': 'H', 'qubits': [0]},
        {'type': 'H', 'qubits': [1]},
        {'type': 'H', 'qubits': [2]},
        {'type': 'CNOT', 'qubits': [0, 1]},
        {'type': 'CNOT', 'qubits': [1, 2]}
    ]
})
```

## Dependencies

### Required (for quantum features):
```bash
pip install pennylane torch numpy
```

### Optional (for full functionality):
```bash
pip install qiskit azure-quantum
```

The system **gracefully degrades** if quantum libraries are unavailable:
- Falls back to deterministic classical generation
- Maintains API compatibility
- Logs warnings but continues operation

## Configuration

### Environment Variables

```bash
# Enable quantum features (default: auto-detect)
export QAI_ENABLE_QUANTUM=true

# Quantum backend (default: default.qubit)
export QUANTUM_BACKEND=default.qubit

# Number of qubits for world generation (default: 4)
export QUANTUM_WORLD_QUBITS=4

# Azure Quantum workspace (optional, for real QPU)
export AZURE_QUANTUM_WORKSPACE=your-workspace
export AZURE_QUANTUM_RESOURCE_ID=/subscriptions/.../resourceGroups/.../providers/Microsoft.Quantum/Workspaces/...
```

### Quantum Config File

Located at: `quantum-ai/config/quantum_config.yaml`

```yaml
quantum:
  simulator:
    backend: default.qubit
    shots: 1000
    
ml:
  model:
    n_qubits: 4
    n_layers: 3
    entanglement: circular

azure:
  workspace_name: your-workspace
  resource_group: your-rg
  location: eastus
```

## Performance

### Benchmarks (local simulator)

| Operation | Classical | Quantum | Notes |
|-----------|-----------|---------|-------|
| Generate 8 objects | ~5ms | ~50ms | Includes circuit execution |
| Generate 16 objects | ~10ms | ~100ms | Scales linearly |
| Visualize circuit (4 qubits) | N/A | ~20ms | Circuit complexity dependent |
| Render to stage | ~15ms | ~15ms | No difference (same rendering) |

### Optimization Tips

1. **Reuse generator instance**: `get_quantum_generator()` caches the instance
2. **Limit qubit count**: 4-6 qubits optimal for world generation
3. **Use seeds**: Reproducible results without re-running circuits
4. **Batch operations**: Generate multiple worlds in sequence efficiently

## Advanced Examples

### Custom Quantum Circuit Theme

```python
# Create themed circuit based on world requirements
def create_themed_circuit(theme: str) -> Dict:
    if theme == 'quantum':
        return {
            'name': 'quantum_theme',
            'n_qubits': 6,
            'gates': [
                {'type': 'H', 'qubits': [i]} for i in range(6)
            ] + [
                {'type': 'CNOT', 'qubits': [i, (i+1)%6]} for i in range(6)
            ]
        }
    elif theme == 'space':
        return {
            'name': 'space_theme',
            'n_qubits': 4,
            'gates': [
                {'type': 'RY', 'qubits': [i]} for i in range(4)
            ] + [
                {'type': 'CNOT', 'qubits': [0, 1]},
                {'type': 'CNOT', 'qubits': [2, 3]}
            ]
        }

generator = get_quantum_generator()
world = generator.visualize_quantum_circuit(create_themed_circuit('quantum'))
```

### Hybrid Classical-Quantum Generation

```python
# Use quantum for positions, classical for object selection
generator = get_quantum_generator()
positions = generator.generate_quantum_positions(count=10, seed=42)

# Custom object assignment
theme_objects = ['🌳', '🌸', '🦋', '🌻']
objects = {}
for i, pos in enumerate(positions):
    objects[f'obj_{i}'] = {
        'emoji': theme_objects[i % len(theme_objects)],
        'position': {'x': pos['x'], 'y': pos['y']},
        'quantum_state': pos.get('quantum_state')
    }
```

### Real-time Quantum State Updates

```python
# Continuously measure and update object states
import time

generator = get_quantum_generator()
world = generator.generate_quantum_world('quantum', count=5)

for _ in range(10):  # 10 iterations
    # Re-measure quantum states
    new_positions = generator.generate_quantum_positions(5)
    
    # Update object positions with quantum-driven animation
    for i, (obj_id, obj) in enumerate(world['objects'].items()):
        obj['position'] = {
            'x': new_positions[i]['x'],
            'y': new_positions[i]['y']
        }
        obj['quantum_state'] = new_positions[i]['quantum_state']
    
    # Send to frontend via WebSocket/SSE
    # emit_update(world)
    
    time.sleep(0.5)
```

## Troubleshooting

### Quantum libraries not available

**Symptom:** Server logs "Quantum models unavailable"

**Solution:**
```bash
pip install pennylane torch numpy
# Restart server
cd aria_web && python server.py
```

### Circuit visualization returns empty

**Symptom:** `/api/aria/quantum/circuit` returns no objects

**Solution:**
- Check circuit_data format (must include n_qubits and gates)
- Verify gate types are supported (H, X, Y, Z, CNOT, RY, RZ)
- Review server logs for errors

### Quantum generation slower than expected

**Symptom:** World generation takes >500ms

**Solution:**
- Reduce n_qubits (4 is optimal)
- Use classical generation for real-time updates
- Cache generator instance: `get_quantum_generator()`

### Objects overlapping despite quantum generation

**Symptom:** Objects too close together

**Solution:**
- Quantum positions are naturally distributed but not guaranteed non-overlapping
- Add post-processing:
```python
positions = generator.generate_quantum_positions(count=10)
# Apply minimum distance constraint
adjusted = apply_spacing_constraint(positions, min_distance=10)
```

## Future Enhancements

- [ ] Real QPU integration via Azure Quantum
- [ ] Quantum-driven physics simulation
- [ ] Entanglement visualization (connections between objects)
- [ ] Quantum state collapse on interaction
- [ ] Quantum teleportation between objects
- [ ] Adaptive circuit complexity based on world size
- [ ] WebAssembly quantum simulator for client-side generation

## Contributing

See main repository guidelines. Key areas for contribution:
- New quantum circuit patterns
- Performance optimizations
- Additional visualization styles
- Real-world use cases

## License

Same as parent repository (see root LICENSE file).

## References

- PennyLane: https://pennylane.ai/
- Azure Quantum: https://azure.microsoft.com/en-us/products/quantum/
- Qiskit: https://qiskit.org/
- Aria Character System: See `/aria_web/README.md`
