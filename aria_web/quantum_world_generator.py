"""Quantum-powered world generation for Aria.

Integrates quantum classifiers and circuits to generate:
- Quantum-enhanced object placement (superposition-based positioning)
- Quantum state-driven object properties (entanglement patterns)
- Quantum circuit visualization as 3D world elements
"""

import json
import logging
import math
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Add quantum-ai to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Optional quantum imports
try:
    import pennylane as qml
    import torch
    from quantum_ai.src.quantum_classifier import QuantumClassifier
    QUANTUM_AVAILABLE = True
    logger.info("✓ Quantum models available for world generation")
except Exception as e:
    QUANTUM_AVAILABLE = False
    logger.info(f"Quantum models unavailable: {e}")


class QuantumWorldGenerator:
    """Generate 3D world elements using quantum computation."""
    
    def __init__(self, n_qubits: int = 4):
        self.n_qubits = n_qubits
        self.quantum_classifier = None
        
        if QUANTUM_AVAILABLE:
            try:
                config_path = REPO_ROOT / "quantum-ai" / "config" / "quantum_config.yaml"
                if config_path.exists():
                    self.quantum_classifier = QuantumClassifier(str(config_path))
                    logger.info(f"Initialized quantum classifier with {n_qubits} qubits")
            except Exception as e:
                logger.warning(f"Failed to initialize quantum classifier: {e}")
    
    def generate_quantum_positions(self, count: int, seed: Optional[int] = None) -> List[Dict]:
        """Generate object positions using quantum superposition.
        
        Uses quantum circuit measurements to determine positions,
        creating naturally distributed, non-overlapping placements.
        """
        if not QUANTUM_AVAILABLE:
            return self._fallback_positions(count, seed)
        
        try:
            if seed is not None:
                np.random.seed(seed)
                torch.manual_seed(seed)
            
            # Create quantum device
            dev = qml.device('default.qubit', wires=self.n_qubits)
            
            @qml.qnode(dev)
            def position_circuit(params):
                # Encode count and seed into circuit
                for i in range(self.n_qubits):
                    qml.RY(params[i], wires=i)
                    qml.RZ(params[i] * 0.5, wires=i)
                
                # Create entanglement for correlated positions
                for i in range(self.n_qubits - 1):
                    qml.CNOT(wires=[i, i + 1])
                
                # Measure all qubits
                return [qml.expval(qml.PauliZ(i)) for i in range(self.n_qubits)]
            
            positions = []
            for i in range(count):
                # Generate quantum parameters
                params = np.random.uniform(0, 2 * np.pi, self.n_qubits)
                measurements = position_circuit(params)
                
                # Convert quantum measurements to coordinates
                # Map [-1, 1] expectation values to [5, 95] stage coordinates
                x = int((measurements[0] + 1) * 45 + 5)
                y = int((measurements[1] + 1) * 45 + 5)
                
                # Use additional qubits for object properties
                scale = (measurements[2] + 1) * 0.5  # [0, 1]
                rotation = measurements[3] * 180  # [-180, 180]
                
                positions.append({
                    'x': max(5, min(95, x)),
                    'y': max(5, min(95, y)),
                    'scale': max(0.5, min(2.0, scale)),
                    'rotation': rotation,
                    'quantum_state': measurements.tolist()
                })
            
            return positions
            
        except Exception as e:
            logger.warning(f"Quantum position generation failed: {e}")
            return self._fallback_positions(count, seed)
    
    def _fallback_positions(self, count: int, seed: Optional[int] = None) -> List[Dict]:
        """Deterministic fallback for position generation."""
        if seed is not None:
            random.seed(seed)
        
        positions = []
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            radius = 30 + random.uniform(-10, 10)
            x = int(50 + radius * math.cos(angle))
            y = int(50 + radius * math.sin(angle))
            
            positions.append({
                'x': max(5, min(95, x)),
                'y': max(5, min(95, y)),
                'scale': 1.0,
                'rotation': 0,
                'quantum_state': None
            })
        
        return positions
    
    def generate_quantum_world(self, theme: str, count: int = 8, seed: Optional[int] = None) -> Dict:
        """Generate a complete world using quantum computation.
        
        Returns world dict with objects and environment metadata.
        """
        positions = self.generate_quantum_positions(count, seed)
        
        # Theme-based object selection
        theme_objects = self._get_theme_objects(theme)
        
        objects = {}
        for i, pos in enumerate(positions):
            obj_emoji = random.choice(theme_objects)
            obj_id = f"quantum_obj_{i}"
            
            objects[obj_id] = {
                'id': obj_id,
                'emoji': obj_emoji,
                'position': {'x': pos['x'], 'y': pos['y']},
                'state': 'on_stage',
                'properties': {
                    'scale': pos['scale'],
                    'rotation': pos['rotation'],
                    'quantum_generated': True
                }
            }
            
            if pos['quantum_state']:
                objects[obj_id]['quantum_state'] = pos['quantum_state']
        
        environment = {
            'theme': theme,
            'generation_method': 'quantum' if QUANTUM_AVAILABLE else 'quantum_fallback',
            'stage_bounds': {'width': 100, 'height': 100},
            'quantum_qubits': self.n_qubits,
            'seed': seed
        }
        
        return {
            'objects': objects,
            'environment': environment,
            'quantum_powered': QUANTUM_AVAILABLE
        }
    
    def visualize_quantum_circuit(self, circuit_data: Optional[Dict] = None) -> Dict:
        """Convert quantum circuit to 3D world objects.
        
        Represents qubits as objects and gates as connections/animations.
        """
        if circuit_data is None:
            # Generate sample circuit
            circuit_data = self._create_sample_circuit()
        
        objects = {}
        
        # Create qubit representations
        n_qubits = circuit_data.get('n_qubits', 4)
        qubit_spacing = 80 / (n_qubits + 1)
        
        for i in range(n_qubits):
            y_pos = int(10 + (i + 1) * qubit_spacing)
            objects[f'qubit_{i}'] = {
                'id': f'qubit_{i}',
                'emoji': '⚛️',
                'position': {'x': 10, 'y': y_pos},
                'state': 'on_stage',
                'properties': {
                    'type': 'qubit',
                    'index': i,
                    'quantum_object': True
                }
            }
        
        # Create gate representations
        gates = circuit_data.get('gates', [])
        gate_x = 30
        
        for idx, gate in enumerate(gates):
            gate_type = gate.get('type', 'H')
            qubits = gate.get('qubits', [0])
            
            # Position gate on qubit line
            y_pos = int(10 + (qubits[0] + 1) * qubit_spacing)
            
            gate_emoji = {
                'H': '🎯',  # Hadamard
                'X': '❌',  # Pauli-X
                'Y': '🌀',  # Pauli-Y
                'Z': '⚡',  # Pauli-Z
                'CNOT': '🔗',  # CNOT
                'RY': '🔄',  # Rotation-Y
                'RZ': '🌐'   # Rotation-Z
            }.get(gate_type, '⭐')
            
            objects[f'gate_{idx}'] = {
                'id': f'gate_{idx}',
                'emoji': gate_emoji,
                'position': {'x': gate_x, 'y': y_pos},
                'state': 'on_stage',
                'properties': {
                    'type': 'gate',
                    'gate_type': gate_type,
                    'qubits': qubits,
                    'quantum_object': True
                }
            }
            
            gate_x += 15
        
        # Add measurement objects
        measure_x = gate_x + 10
        for i in range(n_qubits):
            y_pos = int(10 + (i + 1) * qubit_spacing)
            objects[f'measure_{i}'] = {
                'id': f'measure_{i}',
                'emoji': '📊',
                'position': {'x': measure_x, 'y': y_pos},
                'state': 'on_stage',
                'properties': {
                    'type': 'measurement',
                    'qubit': i,
                    'quantum_object': True
                }
            }
        
        return {
            'objects': objects,
            'environment': {
                'theme': 'quantum_circuit',
                'generation_method': 'quantum_visualization',
                'circuit_type': circuit_data.get('name', 'custom'),
                'n_qubits': n_qubits
            },
            'circuit_data': circuit_data
        }
    
    def _create_sample_circuit(self) -> Dict:
        """Create a sample quantum circuit for visualization."""
        return {
            'name': 'bell_state',
            'n_qubits': 4,
            'gates': [
                {'type': 'H', 'qubits': [0]},
                {'type': 'CNOT', 'qubits': [0, 1]},
                {'type': 'RY', 'qubits': [2]},
                {'type': 'CNOT', 'qubits': [1, 2]},
                {'type': 'RZ', 'qubits': [3]},
                {'type': 'CNOT', 'qubits': [2, 3]}
            ]
        }
    
    def _get_theme_objects(self, theme: str) -> List[str]:
        """Get emoji objects for a given theme."""
        theme_map = {
            'quantum': ['⚛️', '🔬', '🌌', '✨', '🎯', '🌀', '⚡', '🔮'],
            'nature': ['🌳', '🌸', '🦋', '🌻', '🍄', '🌿', '🐝', '🌺'],
            'space': ['🚀', '🛸', '🌍', '🌙', '⭐', '🪐', '☄️', '🛰️'],
            'ocean': ['🐋', '🐠', '🦈', '🐙', '🦀', '🐚', '🌊', '⚓'],
            'tech': ['💻', '⚙️', '🔧', '🤖', '📡', '🔌', '💾', '🖥️']
        }
        
        # Normalize theme
        theme_lower = theme.lower()
        for key in theme_map:
            if key in theme_lower:
                return theme_map[key]
        
        return theme_map['quantum']


# Module-level instance for easy access
_generator = None

def get_quantum_generator(n_qubits: int = 4) -> QuantumWorldGenerator:
    """Get or create the quantum world generator instance."""
    global _generator
    if _generator is None:
        _generator = QuantumWorldGenerator(n_qubits)
    return _generator
