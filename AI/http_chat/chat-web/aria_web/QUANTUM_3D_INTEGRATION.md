# Quantum-3D World Integration

This integration connects quantum computing models with the Aria 3D character world, enabling:

1. **Quantum State Visualization** - Real-time Bloch sphere rendering in the 3D environment
2. **Quantum-Enhanced Character Behavior** - Use quantum computing to predict character actions
3. **Quantum World Generation** - Generate themed 3D environments using quantum random number generation

## Architecture

### Backend Components

#### `quantum_3d_bridge.py`
Python bridge connecting quantum-ai models with the Aria web server.

**Key Classes:**
- `QuantumCharacterController` - Generates quantum-enhanced character behaviors
- `QuantumWorldGenerator` - Creates 3D worlds using quantum algorithms

**Main Functions:**
- `quantum_predict_behavior(context)` - Predicts next action using hybrid quantum-classical NN
- `quantum_generate_world(theme)` - Generates themed world with quantum randomness
- `quantum_visualize_state()` - Returns Bloch sphere data for visualization

#### `quantum_api_routes.py`
API endpoint handlers for quantum features.

**Endpoints:**
- `GET /api/aria/quantum/state` - Get current quantum state for visualization
- `POST /api/aria/quantum/predict` - Predict behavior using quantum model
- `POST /api/aria/world` (with `use_quantum: true`) - Generate quantum world

### Frontend Components

#### `quantum_visualizer.js`
JavaScript visualization layer rendering quantum states in the 3D world.

**Features:**
- Bloch sphere rendering for up to 4 qubits
- Animated quantum particles with superposition effects
- Entanglement line visualization
- Real-time quantum state updates
- Interactive control panel

**Key Class:**
- `QuantumVisualizer` - Main visualization controller

## Setup & Integration

### 1. Backend Integration

The integration is already set up in `server.py`:

```python
# At the top of server.py
from quantum_3d_bridge import (
    quantum_predict_behavior,
    quantum_generate_world,
    quantum_visualize_state,
    QUANTUM_AVAILABLE
)
```

### 2. Frontend Integration

Add to `index.html` before `</body>`:

```html
<script src="quantum_visualizer.js"></script>
```

### 3. Required Dependencies

Quantum models require:
```bash
pip install pennylane torch numpy pyyaml
```

## Usage

### Enable Quantum Visualization

1. Open Aria web interface: `http://localhost:8080`
2. Click "⚛️ Enable Visualization" in the quantum control panel
3. Bloch spheres and quantum particles will appear in the 3D world

### Quantum Behavior Prediction

```javascript
// From browser console or aria_controller.js
const context = {
    position: characterState.position,
    expression: characterState.mood,
    objects: activeObjects
};

const response = await fetch('/api/aria/quantum/predict', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({context})
});

const prediction = await response.json();
console.log('Quantum predicted action:', prediction.action);
```

### Quantum World Generation

```javascript
const response = await fetch('/api/aria/world', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        theme: 'quantum',
        use_quantum: true
    })
});

const world = await response.json();
console.log('Generated world with quantum RNG:', world);
```

## API Reference

### GET /api/aria/quantum/state

**Response:**
```json
{
  "enabled": true,
  "bloch_vectors": [
    {
      "qubit": 0,
      "x": 0.707,
      "y": 0.0,
      "z": 0.707,
      "theta": 0.785,
      "phi": 0.0
    }
  ],
  "entanglement": 0.65,
  "measurement_probabilities": [0.5, 0.3, 0.1, 0.05, 0.03, 0.01, 0.01, 0.0]
}
```

### POST /api/aria/quantum/predict

**Request:**
```json
{
  "context": {
    "position": {"x": 50, "y": 50},
    "expression": "neutral",
    "objects": {
      "apple": {"position": {"x": 60, "y": 40}, "state": "on_table"}
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": {
    "action": "move",
    "target": {"x": 55, "y": 45},
    "speed": 0.8,
    "confidence": 0.85
  },
  "secondary_actions": ["pickup", "say"],
  "quantum_confidence": 0.85,
  "quantum_state": [0.7, 0.5, 0.3, 0.1, 0.05, 0.02, 0.01, 0.0],
  "method": "quantum"
}
```

### POST /api/aria/world

**Request:**
```json
{
  "theme": "quantum",
  "use_quantum": true
}
```

**Response:**
```json
{
  "status": "success",
  "theme": "quantum",
  "objects": {
    "qubit_sphere_0": {
      "type": "qubit_sphere",
      "position": {"x": 45, "y": 30},
      "scale": 1.2,
      "rotation": 45,
      "color": "hsl(180, 70%, 60%)"
    }
  },
  "environment": {
    "background_color": "hsl(240, 70%, 60%)",
    "ambient_light": 0.7,
    "theme": "quantum"
  },
  "lighting": {
    "main": {"intensity": 0.8, "color": "hsl(180, 70%, 60%)", "angle": 45}
  },
  "effects": ["particle_stream", "quantum_glow", "entanglement_lines"],
  "quantum_seed": [0.8732, 0.2341, 0.9876, 0.1234],
  "method": "quantum"
}
```

## Visualization Elements

### Bloch Spheres
- **Position:** Dynamically placed near character
- **Size:** 80px diameter
- **Animation:** Continuous rotation
- **State Vector:** Rendered as a line from center to surface
- **Color:** Cyan/magenta gradient with glow effects

### Quantum Particles
- **Count:** 20 particles by default
- **Distribution:** Circular pattern around character
- **Animation:** Floating motion with opacity variation
- **Color:** Cyan radial gradient with glow

### Entanglement Lines (Future Enhancement)
- Connect pairs of Bloch spheres showing entangled qubits
- Pulsing animation to indicate quantum correlation

## Quantum Models

### Hybrid Quantum-Classical Neural Network
- **Input:** 2^n_qubits features (default: 16 for 4 qubits)
- **Quantum Layer:** Variational circuit with amplitude encoding
- **Classical Layer:** 32-neuron fully connected layer
- **Output:** 8 behavior dimensions (move, pickup, say, gesture, look, wait, throw, dance)

### Behavior Encoding
Emotions are mapped to quantum states:
```python
{
    'happy': [1, 0, 0, 0],
    'sad': [0, 1, 0, 0],
    'angry': [0, 0, 1, 0],
    'neutral': [0, 0, 0, 1],
    'excited': [0.7, 0, 0, 0.3],
    'surprised': [0.5, 0, 0.5, 0]
}
```

## Fallback Behavior

All quantum features gracefully fallback to classical implementations if:
- Quantum dependencies are unavailable
- Quantum models fail to initialize
- API endpoints encounter errors

**Fallback Strategy:**
1. Quantum prediction → Rule-based behavior generation
2. Quantum world generation → Deterministic world generation with pseudo-RNG
3. Quantum visualization → Display "unavailable" message

## Performance Notes

- **Quantum Model Loading:** ~2-5 seconds initial load
- **Prediction Latency:** ~100-300ms per prediction
- **Visualization Update:** Every 2 seconds (configurable)
- **World Generation:** ~500ms-2s depending on complexity

## Troubleshooting

### "Quantum computing unavailable"
**Cause:** Dependencies not installed or import failed  
**Solution:** Install with `pip install pennylane torch numpy pyyaml`

### "Quantum model initialization failed"
**Cause:** Config file missing or invalid  
**Solution:** Ensure `quantum-ai/config/quantum_config.yaml` exists

### Visualization not appearing
**Cause:** JavaScript not loaded or fetch failed  
**Solution:** Check browser console, ensure server is running on port 8080

### Prediction returns classical fallback
**Cause:** Hybrid model not initialized  
**Solution:** Check server logs for model initialization errors

## Future Enhancements

1. **Multi-Qubit Entanglement Visualization** - Show connections between entangled qubits
2. **Quantum State History** - Timeline view of quantum state evolution
3. **Real Azure Quantum Integration** - Submit jobs to Azure Quantum QPU
4. **Quantum Reinforcement Learning** - Train character behaviors with quantum RL
5. **VQE for World Optimization** - Use Variational Quantum Eigensolver to find optimal world layouts
6. **Quantum Teleportation Effects** - Visual effects when character "teleports" using quantum principles

## Development Commands

```bash
# Start Aria server with quantum integration
cd /workspaces/AI/aria_web
python server.py

# Test quantum endpoints
curl http://localhost:8080/api/aria/quantum/state | jq
curl -X POST http://localhost:8080/api/aria/quantum/predict \
  -H "Content-Type: application/json" \
  -d '{"context": {"position": {"x": 50, "y": 50}, "expression": "happy"}}'

# Test quantum world generation
curl -X POST http://localhost:8080/api/aria/world \
  -H "Content-Type: application/json" \
  -d '{"theme": "quantum", "use_quantum": true}' | jq
```

## Architecture Diagram

```

                 Browser (Frontend)                  │
 │  ┌───────────────
  │         quantum_visualizer.js                  │ │
  │  - Bloch sphere rendering                      │ │
  │  - Quantum particle effects                    │ │
  │  - Control panel UI                            │ │
  └────────────────────────────────────────────────┘ │
  ┌────────────────────────────────────────────────┐ │
  │         aria_controller.js                     │ │
  │  - Character control                           │ │
  │  - Action execution                            │ │
  └────────────────────────────────────────────────┘ │

                   │ HTTP/JSON
mv repo_automation.py aria_automation.py master_orchestrator.py aria_demo.py    aria_quick_train.py automate_aria_movement.py repo_automation.py    automation/  /dev/null>2; \
          aria_web/server.py (Backend)               │
  ┌────────────────────────────────────────────────┐ │
  │      quantum_api_routes.py                     │ │
  │  - /api/aria/quantum/state                     │ │
  │  - /api/aria/quantum/predict                   │ │
  │  - /api/aria/world (quantum mode)              │ │
  └────────────────────────────────────────────────┘ │
 │  ┌────────────────
  │      quantum_3d_bridge.py                      │ │
  │  - QuantumCharacterController                  │ │
  │  - QuantumWorldGenerator                       │ │
 │  └────────────────────────────────────────────────

                   │ Python imports
mv repo_automation.py aria_automation.py master_orchestrator.py aria_demo.py    aria_quick_train.py automate_aria_movement.py repo_automation.py    automation/  /dev/null>2; \
         quantum-ai/src/ (Quantum Models)            │
 │  ┌────────────────────────────────────────────
  │  hybrid_qnn.py - Hybrid quantum-classical NN   │ │
  │  quantum_classifier.py - VQC classifier        │ │
 │  └────
  ┌────────────────────────────────────────────────┐ │
  │  PennyLane - Quantum circuit simulation        │ │
  │  PyTorch - Classical neural network layers     │ │
 │  └────────────────────────────────────

```

## Code Examples

### Custom Quantum Behavior

```python
# In quantum_3d_bridge.py
def custom_quantum_behavior(self, context):
    """Add custom quantum-enhanced behavior."""
    features = self._extract_features(context)
    input_tensor = torch.FloatTensor(features).unsqueeze(0)
    
    # Run through quantum circuit
    quantum_output = self.hybrid_model(input_tensor)
    
    # Custom decoding logic
    if quantum_output[0] > 0.8:
        return {'action': 'dance', 'style': 'quantum_waltz'}
    
    return self._decode_behavior(quantum_output.squeeze().numpy(), context)
```

### Custom World Theme

```python
# In quantum_3d_bridge.py, QuantumWorldGenerator class
def generate_custom_theme(self, theme='nebula'):
    """Generate custom themed world."""
    quantum_random = self._quantum_random_numbers(25)
    
    # Theme-specific object types
    object_types = ['star', 'nebula', 'blackhole', 'wormhole']
    
    # Use quantum RNG for placement
    objects = {}
    for i in range(int(quantum_random[0] * 5) + 3):
        obj_type = object_types[int(quantum_random[i+1] * len(object_types))]
        objects[f'{obj_type}_{i}'] = {
            'type': obj_type,
            'position': {
                'x': quantum_random[i+5] * 100,
                'y': quantum_random[i+10] * 100
            }
        }
    
    return {'objects': objects, 'theme': theme}
```

## Contact & Support

For questions or issues:
1. Check server logs: `tail -f aria_web/server.log`
2. Review quantum-ai documentation in `/quantum-ai/README.md`
3. Test quantum models independently: `python quantum-ai/src/quantum_classifier.py`

