#!/usr/bin/env python
"""
Quantum-3D Bridge for Aria Character
Integrates quantum computing models with the 3D character world.
"""

import json
import logging
import numpy as np
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import asyncio

# Add quantum-ai to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "quantum-ai" / "src"))

try:
    from quantum_classifier import QuantumClassifier
    from hybrid_qnn import QuantumLayer, HybridQNN
    import torch
    QUANTUM_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✓ Quantum models loaded successfully")
except Exception as e:
    QUANTUM_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠ Quantum models unavailable: {e}")

logger = logging.getLogger(__name__)


class QuantumCharacterController:
    """
    Uses quantum computing to generate character behaviors and world states.
    """
    
    def __init__(self, n_qubits: int = 4, n_layers: int = 2):
        """Initialize quantum-enhanced character controller."""
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.quantum_state = None
        self.emotion_history = []
        self.max_history = 10
        
        if QUANTUM_AVAILABLE:
            try:
                # Initialize quantum classifier for emotion/behavior prediction
                config_path = REPO_ROOT / "quantum-ai" / "config" / "quantum_config.yaml"
                if config_path.exists():
                    self.quantum_model = QuantumClassifier(str(config_path))
                else:
                    logger.warning("Quantum config not found, using defaults")
                    self.quantum_model = None
                
                # Initialize hybrid model for complex behaviors
                self.hybrid_model = None
                self._init_hybrid_model()
                
                logger.info(f"✓ Quantum controller initialized: {n_qubits} qubits, {n_layers} layers")
            except Exception as e:
                logger.error(f"Failed to initialize quantum models: {e}")
                self.quantum_model = None
                self.hybrid_model = None
        else:
            self.quantum_model = None
            self.hybrid_model = None
    
    def _init_hybrid_model(self):
        """Initialize hybrid quantum-classical neural network."""
        try:
            if not QUANTUM_AVAILABLE:
                return
            
            # Create hybrid model for behavior generation
            self.hybrid_model = HybridQNN(
                n_qubits=self.n_qubits,
                n_qlayers=self.n_layers,
                n_classical=32,
                n_output=8,  # 8 behavior dimensions
                device="default.qubit"
            )
            logger.info("✓ Hybrid quantum-classical model initialized")
        except Exception as e:
            logger.warning(f"Hybrid model initialization failed: {e}")
            self.hybrid_model = None
    
    def encode_emotion_state(self, emotion: str, intensity: float = 1.0) -> np.ndarray:
        """
        Encode emotion into quantum state representation.
        
        Args:
            emotion: Emotion name (happy, sad, angry, neutral, etc.)
            intensity: Emotion intensity [0, 1]
            
        Returns:
            Quantum state vector
        """
        # Emotion encoding scheme
        emotion_map = {
            'happy': [1, 0, 0, 0],
            'sad': [0, 1, 0, 0],
            'angry': [0, 0, 1, 0],
            'neutral': [0, 0, 0, 1],
            'excited': [0.7, 0, 0, 0.3],
            'calm': [0, 0, 0, 1],
            'surprised': [0.5, 0, 0.5, 0],
            'confused': [0, 0.5, 0, 0.5]
        }
        
        base_state = emotion_map.get(emotion.lower(), [0, 0, 0, 1])
        state = np.array(base_state) * intensity
        
        # Normalize for quantum state
        norm = np.linalg.norm(state)
        if norm > 0:
            state = state / norm
        
        return state
    
    def quantum_behavior_prediction(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use quantum computing to predict character behavior.
        
        Args:
            context: Current world state (position, objects, recent actions)
            
        Returns:
            Predicted behavior actions
        """
        if not QUANTUM_AVAILABLE or self.hybrid_model is None:
            return self._fallback_behavior(context)
        
        try:
            # Extract features from context
            features = self._extract_features(context)
            
            # Convert to torch tensor
            input_tensor = torch.FloatTensor(features).unsqueeze(0)
            
            # Run through hybrid quantum-classical network
            with torch.no_grad():
                output = self.hybrid_model(input_tensor)
                behavior_scores = output.squeeze().numpy()
            
            # Decode behavior scores into actions
            actions = self._decode_behavior(behavior_scores, context)
            
            return {
                'action': actions['primary'],
                'secondary_actions': actions['secondary'],
                'quantum_confidence': float(np.max(behavior_scores)),
                'quantum_state': behavior_scores.tolist(),
                'method': 'quantum'
            }
            
        except Exception as e:
            logger.warning(f"Quantum prediction failed: {e}, using fallback")
            return self._fallback_behavior(context)
    
    def _extract_features(self, context: Dict[str, Any]) -> List[float]:
        """Extract numerical features from world context."""
        features = []
        
        # Position features
        pos = context.get('position', {'x': 0, 'y': 0})
        features.extend([pos['x'] / 100.0, pos['y'] / 100.0])
        
        # Object proximity features
        objects = context.get('objects', {})
        closest_dist = 100.0
        object_count = len(objects)
        
        for obj_data in objects.values():
            obj_pos = obj_data.get('position', {'x': 50, 'y': 50})
            dist = np.sqrt((pos['x'] - obj_pos['x'])**2 + (pos['y'] - obj_pos['y'])**2)
            closest_dist = min(closest_dist, dist)
        
        features.extend([closest_dist / 100.0, object_count / 10.0])
        
        # Emotion state features
        emotion = context.get('expression', 'neutral')
        emotion_vector = self.encode_emotion_state(emotion)
        features.extend(emotion_vector.tolist())
        
        # Pad or truncate to required size (2^n_qubits)
        target_size = 2 ** self.n_qubits
        while len(features) < target_size:
            features.append(0.0)
        features = features[:target_size]
        
        return features
    
    def _decode_behavior(self, scores: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        """Decode quantum output scores into character actions."""
        # Behavior dimension meanings
        behaviors = ['move', 'pickup', 'say', 'gesture', 'look', 'wait', 'throw', 'dance']
        
        # Get top 3 behaviors
        top_indices = np.argsort(scores)[-3:][::-1]
        
        primary_action = behaviors[top_indices[0]]
        secondary_actions = [behaviors[i] for i in top_indices[1:]]
        
        # Generate specific action parameters based on context
        action_details = self._generate_action_details(primary_action, context, scores[top_indices[0]])
        
        return {
            'primary': action_details,
            'secondary': secondary_actions
        }
    
    def _generate_action_details(self, action: str, context: Dict[str, Any], confidence: float) -> Dict[str, Any]:
        """Generate detailed action parameters."""
        result = {'action': action, 'confidence': float(confidence)}
        
        if action == 'move':
            # Quantum-influenced movement direction
            angle = np.random.random() * 2 * np.pi * confidence
            distance = 10 + (confidence * 20)
            pos = context.get('position', {'x': 50, 'y': 50})
            result['target'] = {
                'x': pos['x'] + np.cos(angle) * distance,
                'y': pos['y'] + np.sin(angle) * distance
            }
            result['speed'] = 0.5 + (confidence * 0.5)
            
        elif action == 'pickup':
            # Find nearest object
            objects = context.get('objects', {})
            if objects:
                nearest_obj = list(objects.keys())[0]
                result['object_id'] = nearest_obj
            
        elif action == 'say':
            # Quantum-influenced dialogue
            phrases = [
                "I sense quantum fluctuations!",
                "The superposition is fascinating!",
                "Entanglement detected!",
                "My quantum state is evolving!",
                "Wave function collapsed beautifully!"
            ]
            result['text'] = phrases[int(confidence * len(phrases)) % len(phrases)]
            result['emotion'] = 'excited' if confidence > 0.7 else 'curious'
            
        elif action == 'gesture':
            gestures = ['wave', 'dance', 'jump', 'spin']
            result['gesture_type'] = gestures[int(confidence * len(gestures)) % len(gestures)]
        
        return result
    
    def _fallback_behavior(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Classical fallback behavior generation."""
        return {
            'action': {'action': 'wait', 'duration': 1.0},
            'secondary_actions': ['look'],
            'quantum_confidence': 0.0,
            'quantum_state': None,
            'method': 'classical_fallback'
        }
    
    def visualize_quantum_state(self) -> Dict[str, Any]:
        """
        Generate 3D visualization data for quantum state.
        
        Returns:
            Visualization configuration for frontend
        """
        if not QUANTUM_AVAILABLE or self.quantum_state is None:
            return {
                'enabled': False,
                'message': 'Quantum visualization unavailable'
            }
        
        try:
            # Generate Bloch sphere coordinates for each qubit
            bloch_vectors = []
            
            # Simulate quantum state (placeholder for actual computation)
            n_qubits = min(self.n_qubits, 4)  # Visualize up to 4 qubits
            
            for i in range(n_qubits):
                # Generate quantum state parameters
                theta = np.random.random() * np.pi
                phi = np.random.random() * 2 * np.pi
                
                # Bloch sphere coordinates
                x = np.sin(theta) * np.cos(phi)
                y = np.sin(theta) * np.sin(phi)
                z = np.cos(theta)
                
                bloch_vectors.append({
                    'qubit': i,
                    'x': float(x),
                    'y': float(y),
                    'z': float(z),
                    'theta': float(theta),
                    'phi': float(phi)
                })
            
            return {
                'enabled': True,
                'bloch_vectors': bloch_vectors,
                'entanglement': self._calculate_entanglement(),
                'measurement_probabilities': self._get_measurement_probs()
            }
            
        except Exception as e:
            logger.error(f"Quantum visualization failed: {e}")
            return {'enabled': False, 'error': str(e)}
    
    def _calculate_entanglement(self) -> float:
        """Calculate entanglement measure (placeholder)."""
        return np.random.random()  # Replace with actual entanglement calculation
    
    def _get_measurement_probs(self) -> List[float]:
        """Get measurement probability distribution."""
        n_states = 2 ** self.n_qubits
        probs = np.random.dirichlet(np.ones(n_states))
        return probs.tolist()[:8]  # Return first 8 for visualization


class QuantumWorldGenerator:
    """Generate 3D world elements using quantum algorithms."""
    
    def __init__(self, n_qubits: int = 4):
        self.n_qubits = n_qubits
        logger.info(f"QuantumWorldGenerator initialized with {n_qubits} qubits")
    
    def generate_quantum_world(self, theme: str = "default") -> Dict[str, Any]:
        """
        Generate a themed 3D world using quantum random number generation.
        
        Args:
            theme: World theme (quantum, forest, city, space, etc.)
            
        Returns:
            World configuration with objects and environment
        """
        if not QUANTUM_AVAILABLE:
            return self._classical_world_generation(theme)
        
        try:
            # Use quantum RNG for true randomness
            quantum_random = self._quantum_random_numbers(20)
            
            # Generate objects based on quantum random numbers
            objects = self._generate_quantum_objects(quantum_random, theme)
            
            # Generate environment based on theme
            environment = self._generate_quantum_environment(quantum_random, theme)
            
            return {
                'theme': theme,
                'objects': objects,
                'environment': environment,
                'lighting': self._generate_lighting(quantum_random),
                'effects': self._generate_effects(quantum_random, theme),
                'quantum_seed': quantum_random[:4],
                'method': 'quantum'
            }
            
        except Exception as e:
            logger.warning(f"Quantum world generation failed: {e}")
            return self._classical_world_generation(theme)
    
    def _quantum_random_numbers(self, count: int) -> List[float]:
        """Generate truly random numbers using quantum circuits."""
        # Placeholder for actual quantum RNG
        # In production, use Azure Quantum RNG or local quantum simulator
        return np.random.random(count).tolist()
    
    def _generate_quantum_objects(self, random_vals: List[float], theme: str) -> Dict[str, Dict]:
        """Generate world objects using quantum randomness."""
        object_types = {
            'quantum': ['qubit_sphere', 'entangled_pair', 'quantum_gate', 'superposition_cloud'],
            'forest': ['tree', 'rock', 'flower', 'mushroom', 'log'],
            'city': ['building', 'car', 'bench', 'lamp', 'fountain'],
            'space': ['asteroid', 'satellite', 'star', 'planet', 'comet'],
            'default': ['cube', 'sphere', 'cylinder', 'pyramid']
        }
        
        available_objects = object_types.get(theme, object_types['default'])
        objects = {}
        
        # Generate 3-6 objects
        n_objects = int(random_vals[0] * 3) + 3
        
        for i in range(min(n_objects, len(random_vals) - 5)):
            obj_type = available_objects[int(random_vals[i] * len(available_objects))]
            obj_id = f"{obj_type}_{i}"
            
            objects[obj_id] = {
                'type': obj_type,
                'position': {
                    'x': 10 + (random_vals[i + 1] * 80),
                    'y': 20 + (random_vals[i + 2] * 60)
                },
                'scale': 0.5 + (random_vals[i + 3] * 1.5),
                'rotation': random_vals[i + 4] * 360,
                'color': self._quantum_color(random_vals[i + 5])
            }
        
        return objects
    
    def _generate_quantum_environment(self, random_vals: List[float], theme: str) -> Dict[str, Any]:
        """Generate environment settings."""
        return {
            'background_color': self._quantum_color(random_vals[10]),
            'ambient_light': 0.3 + (random_vals[11] * 0.5),
            'theme': theme,
            'weather': self._get_weather(random_vals[12], theme)
        }
    
    def _generate_lighting(self, random_vals: List[float]) -> Dict[str, Any]:
        """Generate lighting configuration."""
        return {
            'main': {
                'intensity': 0.5 + (random_vals[13] * 0.5),
                'color': self._quantum_color(random_vals[14]),
                'angle': random_vals[15] * 360
            },
            'ambient': 0.2 + (random_vals[16] * 0.3)
        }
    
    def _generate_effects(self, random_vals: List[float], theme: str) -> List[str]:
        """Generate visual effects."""
        effects = []
        
        if theme == 'quantum':
            effects = ['particle_stream', 'quantum_glow', 'entanglement_lines']
        elif theme == 'space':
            effects = ['stars', 'nebula', 'cosmic_dust']
        elif random_vals[17] > 0.7:
            effects = ['sparkles', 'glow']
        
        return effects
    
    def _quantum_color(self, random_val: float) -> str:
        """Generate color from quantum random value."""
        hue = int(random_val * 360)
        return f"hsl({hue}, 70%, 60%)"
    
    def _get_weather(self, random_val: float, theme: str) -> str:
        """Get weather condition."""
        if theme in ['space', 'quantum']:
            return 'clear'
        
        weathers = ['clear', 'cloudy', 'rain', 'snow', 'fog']
        return weathers[int(random_val * len(weathers))]
    
    def _classical_world_generation(self, theme: str) -> Dict[str, Any]:
        """Fallback classical world generation."""
        return {
            'theme': theme,
            'objects': {},
            'environment': {'background_color': '#87ceeb'},
            'lighting': {'main': {'intensity': 0.8}},
            'effects': [],
            'method': 'classical_fallback'
        }


# Singleton instances
_quantum_controller = None
_quantum_world_gen = None


def get_quantum_controller() -> QuantumCharacterController:
    """Get or create quantum controller singleton."""
    global _quantum_controller
    if _quantum_controller is None:
        _quantum_controller = QuantumCharacterController(n_qubits=4, n_layers=2)
    return _quantum_controller


def get_quantum_world_generator() -> QuantumWorldGenerator:
    """Get or create quantum world generator singleton."""
    global _quantum_world_gen
    if _quantum_world_gen is None:
        _quantum_world_gen = QuantumWorldGenerator(n_qubits=4)
    return _quantum_world_gen


# Convenience functions for server integration
def quantum_predict_behavior(context: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper for quantum behavior prediction."""
    controller = get_quantum_controller()
    return controller.quantum_behavior_prediction(context)


def quantum_generate_world(theme: str = "default") -> Dict[str, Any]:
    """Wrapper for quantum world generation."""
    generator = get_quantum_world_generator()
    return generator.generate_quantum_world(theme)


def quantum_visualize_state() -> Dict[str, Any]:
    """Wrapper for quantum state visualization."""
    controller = get_quantum_controller()
    return controller.visualize_quantum_state()
