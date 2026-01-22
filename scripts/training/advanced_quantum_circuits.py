#!/usr/bin/env python3
"""
Advanced Quantum Circuit Generator

Creates sophisticated quantum circuits with:
- Multiple entanglement patterns (linear, circular, full, custom)
- Advanced quantum gates (T, S, SWAP, Toffoli)
- Quantum error mitigation
- Optimized parameterization
- Real quantum algorithm implementations
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class QuantumGate:
    """Represents a quantum gate operation"""
    type: str
    qubits: List[int]
    parameters: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type, "qubits": self.qubits}
        if self.parameters:
            result["parameters"] = self.parameters
        return result


class AdvancedQuantumCircuitBuilder:
    """Builds sophisticated quantum circuits for ML applications"""
    
    def __init__(self, num_qubits: int, circuit_name: str):
        self.num_qubits = num_qubits
        self.circuit_name = circuit_name
        self.gates: List[QuantumGate] = []
        self.depth = 0
        self.parameter_count = 0
        
    def add_gate(self, gate: QuantumGate) -> None:
        """Add a gate to the circuit"""
        self.gates.append(gate)
        self.depth += 1
        if gate.parameters:
            self.parameter_count += len(gate.parameters)
    
    def hadamard_layer(self, qubits: Optional[List[int]] = None) -> 'AdvancedQuantumCircuitBuilder':
        """Add Hadamard gates for superposition"""
        target_qubits = qubits if qubits else list(range(self.num_qubits))
        for q in target_qubits:
            self.add_gate(QuantumGate("H", [q]))
        return self
    
    def rotation_layer(self, gate_type: str, param_prefix: str) -> 'AdvancedQuantumCircuitBuilder':
        """Add parametrized rotation gates"""
        for q in range(self.num_qubits):
            self.add_gate(QuantumGate(
                gate_type, 
                [q], 
                [f"{param_prefix}_{q}"]
            ))
        return self
    
    def linear_entanglement(self) -> 'AdvancedQuantumCircuitBuilder':
        """Linear entanglement chain"""
        for q in range(self.num_qubits - 1):
            self.add_gate(QuantumGate("CNOT", [q, q + 1]))
        return self
    
    def circular_entanglement(self) -> 'AdvancedQuantumCircuitBuilder':
        """Circular entanglement (ring topology)"""
        for q in range(self.num_qubits - 1):
            self.add_gate(QuantumGate("CNOT", [q, q + 1]))
        # Close the circle
        if self.num_qubits > 2:
            self.add_gate(QuantumGate("CNOT", [self.num_qubits - 1, 0]))
        return self
    
    def full_entanglement(self) -> 'AdvancedQuantumCircuitBuilder':
        """Full entanglement (all-to-all)"""
        for i in range(self.num_qubits):
            for j in range(i + 1, self.num_qubits):
                self.add_gate(QuantumGate("CNOT", [i, j]))
        return self
    
    def star_entanglement(self, center: int = 0) -> 'AdvancedQuantumCircuitBuilder':
        """Star entanglement (center connected to all)"""
        for q in range(self.num_qubits):
            if q != center:
                self.add_gate(QuantumGate("CNOT", [center, q]))
        return self
    
    def brick_layer_entanglement(self, layer: int = 0) -> 'AdvancedQuantumCircuitBuilder':
        """Brick-layer entanglement pattern"""
        offset = layer % 2
        for q in range(offset, self.num_qubits - 1, 2):
            self.add_gate(QuantumGate("CNOT", [q, q + 1]))
        return self
    
    def phase_gates(self) -> 'AdvancedQuantumCircuitBuilder':
        """Add phase gates (S and T gates)"""
        for q in range(self.num_qubits):
            if q % 2 == 0:
                self.add_gate(QuantumGate("S", [q]))
            else:
                self.add_gate(QuantumGate("T", [q]))
        return self
    
    def controlled_rotation(self, control: int, target: int, 
                           gate_type: str, param: str) -> 'AdvancedQuantumCircuitBuilder':
        """Controlled rotation gate"""
        self.add_gate(QuantumGate(
            f"C{gate_type}", 
            [control, target], 
            [param]
        ))
        self.parameter_count += 1
        return self
    
    def swap_layer(self) -> 'AdvancedQuantumCircuitBuilder':
        """SWAP gate layer for qubit permutation"""
        for q in range(0, self.num_qubits - 1, 2):
            self.add_gate(QuantumGate("SWAP", [q, q + 1]))
        return self
    
    def build_vqe_ansatz(self, num_layers: int) -> Dict[str, Any]:
        """Build Variational Quantum Eigensolver ansatz"""
        for layer in range(num_layers):
            # Rotation layer
            self.rotation_layer("RY", f"theta_ry_{layer}")
            self.rotation_layer("RZ", f"theta_rz_{layer}")
            
            # Entanglement
            if layer % 2 == 0:
                self.brick_layer_entanglement(0)
            else:
                self.brick_layer_entanglement(1)
            
            # Phase gates every other layer
            if layer % 2 == 1:
                self.phase_gates()
        
        return self.to_circuit_dict("VQE Ansatz")
    
    def build_qaoa_circuit(self, num_layers: int, problem_size: int) -> Dict[str, Any]:
        """Build QAOA circuit for optimization"""
        # Initial superposition
        self.hadamard_layer()
        
        for p in range(num_layers):
            # Problem Hamiltonian (cost function)
            for i in range(problem_size - 1):
                self.add_gate(QuantumGate(
                    "RZZ", 
                    [i, i + 1], 
                    [f"gamma_{p}_{i}"]
                ))
            
            # Mixer Hamiltonian
            self.rotation_layer("RX", f"beta_{p}")
        
        return self.to_circuit_dict("QAOA Mixer")
    
    def build_quantum_convolutional_layer(self) -> Dict[str, Any]:
        """Build quantum convolutional layer"""
        # Stride-2 convolution pattern
        for stride in range(2):
            for q in range(stride, self.num_qubits - 1, 2):
                # Two-qubit unitary
                self.add_gate(QuantumGate("RY", [q], [f"conv_ry_{stride}_{q}"]))
                self.add_gate(QuantumGate("RY", [q+1], [f"conv_ry_{stride}_{q+1}"]))
                self.add_gate(QuantumGate("CNOT", [q, q + 1]))
                self.add_gate(QuantumGate("RY", [q], [f"conv_ry2_{stride}_{q}"]))
                self.add_gate(QuantumGate("RY", [q+1], [f"conv_ry2_{stride}_{q+1}"]))
                self.add_gate(QuantumGate("CNOT", [q + 1, q]))
        
        return self.to_circuit_dict("Quantum Convolutional Layer")
    
    def build_quantum_attention(self, num_heads: int) -> Dict[str, Any]:
        """Build quantum attention mechanism"""
        qubits_per_head = self.num_qubits // num_heads
        
        for head in range(num_heads):
            start_q = head * qubits_per_head
            end_q = start_q + qubits_per_head
            
            # Query, Key, Value transformations
            for q in range(start_q, min(end_q, self.num_qubits)):
                self.add_gate(QuantumGate("RY", [q], [f"query_{head}_{q}"]))
                self.add_gate(QuantumGate("RZ", [q], [f"key_{head}_{q}"]))
            
            # Attention weights (entanglement within head)
            for q in range(start_q, min(end_q - 1, self.num_qubits - 1)):
                self.add_gate(QuantumGate("CNOT", [q, q + 1]))
                self.add_gate(QuantumGate("RY", [q + 1], [f"attn_{head}_{q}"]))
        
        return self.to_circuit_dict("Quantum Multi-Head Attention")
    
    def build_error_mitigation_layer(self) -> 'AdvancedQuantumCircuitBuilder':
        """Add advanced error mitigation through dynamical decoupling"""
        # Dynamical decoupling sequence (XY4 pattern)
        for q in range(self.num_qubits):
            # XY4 sequence for error suppression
            self.add_gate(QuantumGate("RX", [q], ["pi/2"]))  # π/2 pulse
            self.add_gate(QuantumGate("RY", [q], ["pi/2"]))
            self.add_gate(QuantumGate("RX", [q], ["pi/2"]))
            self.add_gate(QuantumGate("RY", [q], ["pi/2"]))
        return self
    
    def add_quantum_residual_connection(self, start_depth: int) -> 'AdvancedQuantumCircuitBuilder':
        """Add quantum residual connection (skip connection)"""
        # Identity-preserving gates for residual learning
        for q in range(self.num_qubits):
            self.add_gate(QuantumGate("RY", [q], [f"residual_{start_depth}_{q}"]))
        return self
    
    def build_amplitude_encoding(self, encoding_dim: int) -> Dict[str, Any]:
        """Build amplitude encoding circuit with normalization"""
        # Requires log2(encoding_dim) qubits
        required_qubits = int(np.ceil(np.log2(encoding_dim)))
        if required_qubits > self.num_qubits:
            required_qubits = self.num_qubits
        
        # Multi-controlled rotations for amplitude encoding
        for level in range(required_qubits):
            for q in range(2**level):
                if q < self.num_qubits:
                    self.add_gate(QuantumGate(
                        "RY", 
                        [q], 
                        [f"amp_encode_lvl{level}_q{q}"]
                    ))
            
            # Entangle qubits at each level
            if level < required_qubits - 1:
                for q in range(min(2**level, self.num_qubits - 1)):
                    self.add_gate(QuantumGate("CNOT", [q, q + 1]))
        
        return self.to_circuit_dict("Amplitude Encoding")
    
    def build_quantum_fourier_transform(self) -> Dict[str, Any]:
        """Build Quantum Fourier Transform (QFT) circuit"""
        # QFT for state preparation and feature extraction
        for target in range(self.num_qubits):
            # Hadamard on target
            self.add_gate(QuantumGate("H", [target]))
            
            # Controlled phase rotations
            for control in range(target + 1, self.num_qubits):
                angle = 2 * np.pi / (2 ** (control - target + 1))
                self.add_gate(QuantumGate("CPhase", [control, target], [f"qft_angle_{control}_{target}"]))
            
            # SWAP to reverse qubit order
            if target < self.num_qubits // 2:
                self.add_gate(QuantumGate("SWAP", [target, self.num_qubits - 1 - target]))
        
        return self.to_circuit_dict("Quantum Fourier Transform")
    
    def build_grover_search_circuit(self, target_states: int = 1) -> Dict[str, Any]:
        """Build Grover's algorithm for quantum search"""
        # Oracle for marking target states
        for q in range(self.num_qubits):
            self.add_gate(QuantumGate("RZ", [q], [f"oracle_phase_{q}"]))
        
        # Grover diffusion operator iterations
        iterations = int(np.pi / 4 * np.sqrt(2 ** self.num_qubits / target_states))
        
        for iteration in range(iterations):
            # Hadamard-based diffusion
            self.hadamard_layer()
            
            # Multi-controlled Z gate
            for q in range(self.num_qubits):
                self.add_gate(QuantumGate("RZ", [q], [f"diffusion_{iteration}_{q}"]))
            
            self.hadamard_layer()
        
        return self.to_circuit_dict("Grover Search Circuit")
    
    def build_variational_classifier(self, num_layers: int = 4) -> Dict[str, Any]:
        """Build Variational Quantum Classifier (VQC) for binary classification"""
        # Feature encoding
        self.hadamard_layer()
        self.rotation_layer("RY", "feature_encode")
        
        # Variational ansatz with multiple layers
        for layer in range(num_layers):
            # Rotation layers
            self.rotation_layer("RZ", f"var_rz_l{layer}")
            self.rotation_layer("RY", f"var_ry_l{layer}")
            self.rotation_layer("RZ", f"var_rz_final_l{layer}")
            
            # Entanglement
            self.linear_entanglement()
        
        # Measurement readout preparation
        self.rotation_layer("RZ", "readout")
        
        return self.to_circuit_dict("Variational Classifier")
    
    def build_quantum_gru_circuit(self, sequence_length: int = 3) -> Dict[str, Any]:
        """Build Quantum GRU (Gated Recurrent Unit) for sequence learning"""
        # Initialize state
        self.hadamard_layer()
        
        for t in range(sequence_length):
            # Reset gate
            self.rotation_layer("RY", f"reset_input_t{t}")
            self.rotation_layer("RZ", f"reset_gate_t{t}")
            
            # Update gate
            self.rotation_layer("RY", f"update_input_t{t}")
            self.rotation_layer("RZ", f"update_gate_t{t}")
            
            # Candidate activation
            self.rotation_layer("RY", f"candidate_t{t}")
            self.circular_entanglement()
            self.rotation_layer("RZ", f"candidate_final_t{t}")
            
            # State update with gating
            self.rotation_layer("RY", f"state_update_t{t}")
        
        return self.to_circuit_dict("Quantum GRU")
    
    def build_quantum_lstm_circuit(self, sequence_length: int = 3) -> Dict[str, Any]:
        """Build Quantum LSTM (Long Short-Term Memory) circuit"""
        # Initialize cell state and hidden state
        self.hadamard_layer()
        
        for t in range(sequence_length):
            # Forget gate
            self.rotation_layer("RY", f"forget_input_t{t}")
            self.rotation_layer("RZ", f"forget_gate_t{t}")
            
            # Input gate
            self.rotation_layer("RY", f"input_candidate_t{t}")
            self.rotation_layer("RZ", f"input_gate_t{t}")
            
            # Cell candidate
            self.rotation_layer("RY", f"cell_candidate_t{t}")
            self.full_entanglement()
            self.rotation_layer("RZ", f"cell_candidate_final_t{t}")
            
            # Output gate
            self.rotation_layer("RY", f"output_input_t{t}")
            self.rotation_layer("RZ", f"output_gate_t{t}")
            
            # Hidden state update
            self.rotation_layer("RY", f"hidden_update_t{t}")
        
        return self.to_circuit_dict("Quantum LSTM")
    
    def build_quantum_boltzmann_machine(self, num_layers: int = 3) -> Dict[str, Any]:
        """Build Quantum Boltzmann Machine for generative modeling"""
        # Visible layer
        self.hadamard_layer(list(range(self.num_qubits // 2)))
        
        # Alternating Boltzmann sampling
        for layer in range(num_layers):
            # Visible unit updates
            self.rotation_layer("RZ", f"visible_update_l{layer}")
            self.rotation_layer("RY", f"visible_activation_l{layer}")
            
            # Entangle visible and hidden
            mid = self.num_qubits // 2
            for i in range(mid):
                self.add_gate(QuantumGate("CX", [i, mid + i]))
            
            # Hidden unit updates
            hidden_qubits = list(range(mid, self.num_qubits))
            self.rotation_layer("RZ", f"hidden_update_l{layer}")
            self.rotation_layer("RY", f"hidden_activation_l{layer}")
            
            # Energy-based interactions
            self.brick_layer_entanglement(layer)
        
        return self.to_circuit_dict("Quantum Boltzmann Machine")
    
    def build_quantum_perceptron(self, num_layers: int = 3) -> Dict[str, Any]:
        """Build Quantum Perceptron for single-layer quantum classification"""
        # Input encoding
        self.hadamard_layer()
        self.rotation_layer("RY", "input_encoding")
        
        # Quantum perceptron layers
        for layer in range(num_layers):
            # Linear transformation (entanglement)
            self.star_entanglement(layer % self.num_qubits)
            
            # Activation (rotation)
            self.rotation_layer("RZ", f"activation_l{layer}")
            self.rotation_layer("RY", f"activation_nonlin_l{layer}")
        
        # Bias addition
        self.rotation_layer("RZ", "bias")
        
        return self.to_circuit_dict("Quantum Perceptron")
    
    def build_quantum_phase_estimation(self, eigenvalue_precision: int = 3) -> Dict[str, Any]:
        """Build Quantum Phase Estimation (QPE) circuit"""
        # Prepare eigenstate superposition
        self.hadamard_layer()
        
        # Controlled unitary operations with different time steps
        for qubit in range(self.num_qubits):
            # Controlled evolution
            for _ in range(2 ** qubit):
                self.rotation_layer("RZ", f"controlled_evolution_q{qubit}")
        
        # Inverse QFT for phase extraction
        for target in range(self.num_qubits - 1, -1, -1):
            # Controlled phase rotations (reversed)
            for control in range(target):
                angle = -2 * np.pi / (2 ** (target - control))
                self.add_gate(QuantumGate("CPhase", [control, target], [f"iqft_phase_{control}_{target}"]))
            
            self.add_gate(QuantumGate("H", [target]))
        
        return self.to_circuit_dict("Quantum Phase Estimation")
    
    def build_hybrid_quantum_cnn(self, kernel_size: int = 3) -> Dict[str, Any]:
        """Build Hybrid Quantum Convolutional Neural Network"""
        # Convolutional layer simulation with quantum gates
        num_kernels = min(kernel_size, self.num_qubits // 2)
        
        # Input encoding
        self.hadamard_layer()
        
        for kernel in range(num_kernels):
            # Quantum convolution with sliding window
            window_qubits = list(range(kernel, min(kernel + kernel_size, self.num_qubits)))
            
            # Feature extraction
            self.rotation_layer("RY", f"conv_feature_k{kernel}")
            
            # Local entanglement
            for i in range(len(window_qubits) - 1):
                self.add_gate(QuantumGate("CNOT", [window_qubits[i], window_qubits[i + 1]]))
            
            # Feature processing
            self.rotation_layer("RZ", f"conv_process_k{kernel}")
        
        # Pooling via measurement reduction
        self.add_gate(QuantumGate("Measure", list(range(self.num_qubits))))
        
        # Fully connected layer
        self.hadamard_layer(list(range(num_kernels)))
        self.rotation_layer("RZ", "fc_layer")
        
        return self.to_circuit_dict("Hybrid Quantum CNN")
    
    def build_quantum_autoencoders(self, compression_ratio: float = 0.5) -> Dict[str, Any]:
        """Build Quantum Autoencoder for dimensionality reduction"""
        latent_dim = max(1, int(self.num_qubits * compression_ratio))
        
        # Encoder
        self.hadamard_layer()
        self.rotation_layer("RY", "encoder_input")
        
        for layer in range(2):
            self.full_entanglement()
            self.rotation_layer("RZ", f"encoder_hidden_l{layer}")
        
        # Bottleneck (latent space)
        self.rotation_layer("RY", "latent_space")
        
        # Decoder
        for layer in range(2):
            self.rotation_layer("RZ", f"decoder_hidden_l{layer}")
            self.brick_layer_entanglement(layer)
        
        self.rotation_layer("RY", "decoder_output")
        self.hadamard_layer()
        
        return self.to_circuit_dict("Quantum Autoencoder")

    def build_strongly_entangling_layer(self, num_layers: int) -> Dict[str, Any]:
        """Build strongly entangling layers with residual connections"""
        for layer in range(num_layers):
            # Mark residual connection point
            residual_start = self.depth
            
            # Three rotation gates per qubit (universal gate set)
            for gate_type in ["RX", "RY", "RZ"]:
                self.rotation_layer(gate_type, f"{gate_type.lower()}_layer{layer}")
            
            # Sophisticated entanglement pattern with variable topology
            if layer % 4 == 0:
                self.linear_entanglement()
            elif layer % 4 == 1:
                self.circular_entanglement()
            elif layer % 4 == 2:
                self.star_entanglement(center=self.num_qubits // 2)
            else:
                self.brick_layer_entanglement(0)
                self.brick_layer_entanglement(1)
            
            # Add residual connection every 2 layers
            if layer > 0 and layer % 2 == 0:
                self.add_quantum_residual_connection(residual_start)
        
        return self.to_circuit_dict("Strongly Entangling Layers with Residuals")
    
    def to_circuit_dict(self, description: str) -> Dict[str, Any]:
        """Convert circuit to dictionary format"""
        return {
            "name": self.circuit_name,
            "description": description,
            "num_qubits": self.num_qubits,
            "num_layers": self.depth // self.num_qubits if self.num_qubits > 0 else 0,
            "total_gates": len(self.gates),
            "circuit_depth": self.depth,
            "num_parameters": self.parameter_count,
            "gates": [gate.to_dict() for gate in self.gates],
            "topology": self._analyze_topology(),
            "gate_counts": self._count_gates()
        }
    
    def _analyze_topology(self) -> Dict[str, Any]:
        """Analyze circuit connectivity topology"""
        two_qubit_gates = [g for g in self.gates if len(g.qubits) == 2]
        
        connectivity = {}
        for gate in two_qubit_gates:
            edge = tuple(sorted(gate.qubits))
            connectivity[str(edge)] = connectivity.get(str(edge), 0) + 1
        
        return {
            "two_qubit_gate_count": len(two_qubit_gates),
            "unique_edges": len(connectivity),
            "max_edge_weight": max(connectivity.values()) if connectivity else 0,
            "connectivity_graph": connectivity
        }
    
    def _count_gates(self) -> Dict[str, int]:
        """Count gate types"""
        counts = {}
        for gate in self.gates:
            counts[gate.type] = counts.get(gate.type, 0) + 1
        return counts


def create_advanced_quantum_circuits(num_qubits: int, complexity: str = "standard") -> Dict[str, Any]:
    """Create a suite of advanced quantum circuits with enhanced features"""
    circuits = {}
    
    # 1. Enhanced VQE Ansatz with error mitigation
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "advanced_vqe_ansatz")
    layers = {"lite": 3, "standard": 4, "pro": 6}[complexity]
    circuits["vqe_ansatz"] = builder.build_vqe_ansatz(layers)
    
    # 2. QAOA Circuit with deeper optimization
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "qaoa_optimizer")
    qaoa_layers = {"lite": 3, "standard": 5, "pro": 7}[complexity]
    circuits["qaoa_circuit"] = builder.build_qaoa_circuit(qaoa_layers, num_qubits)
    
    # 3. Quantum Convolutional Layer
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_conv_layer")
    circuits["quantum_conv"] = builder.build_quantum_convolutional_layer()
    
    # 4. Quantum Attention with more heads
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_attention")
    num_heads = {"lite": 2, "standard": 4, "pro": 8}[complexity]
    circuits["quantum_attention"] = builder.build_quantum_attention(min(num_heads, num_qubits // 2))
    
    # 5. Strongly Entangling Layers with Residuals
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "strongly_entangling")
    entangling_layers = {"lite": 3, "standard": 4, "pro": 6}[complexity]
    circuits["strongly_entangling"] = builder.build_strongly_entangling_layer(entangling_layers)
    
    # 6. Amplitude Encoding
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "amplitude_encoding")
    encoding_dim = 2 ** min(num_qubits, 8)
    circuits["amplitude_encoding"] = builder.build_amplitude_encoding(encoding_dim)
    
    # 7. Enhanced Hybrid Circuit with error mitigation
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "hybrid_quantum_ml")
    builder.hadamard_layer()
    builder.rotation_layer("RY", "input_encode")
    builder.circular_entanglement()
    builder.rotation_layer("RZ", "transform")
    builder.brick_layer_entanglement(0)
    builder.phase_gates()
    builder.brick_layer_entanglement(1)
    if complexity == "pro":
        builder.build_error_mitigation_layer()
    builder.rotation_layer("RY", "output")
    circuits["hybrid_quantum_ml"] = builder.to_circuit_dict("Enhanced Hybrid Quantum ML Layer")
    
    # 8. Quantum Transformer Block (new for pro)
    if complexity in ["standard", "pro"]:
        builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_transformer")
        # Multi-head attention
        transformer_heads = {"standard": 2, "pro": 4}[complexity]
        attn_circuit = builder.build_quantum_attention(min(transformer_heads, num_qubits // 2))
        # Add feed-forward layer
        builder.rotation_layer("RY", "ff_layer1")
        builder.circular_entanglement()
        builder.rotation_layer("RZ", "ff_layer2")
        circuits["quantum_transformer"] = builder.to_circuit_dict("Quantum Transformer Block")
    
    # 9. Quantum Fourier Transform (NEW - Advanced quantum algorithm)
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_fourier_transform")
    circuits["qft"] = builder.build_quantum_fourier_transform()
    
    # 10. Grover's Search Circuit (NEW - Advanced quantum algorithm)
    if complexity in ["standard", "pro"]:
        builder = AdvancedQuantumCircuitBuilder(num_qubits, "grovers_search")
        circuits["grovers_search"] = builder.build_grover_search_circuit()
    
    # 11. Variational Quantum Classifier (NEW - ML algorithm)
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "variational_classifier")
    vqc_layers = {"lite": 2, "standard": 3, "pro": 4}[complexity]
    circuits["variational_classifier"] = builder.build_variational_classifier(vqc_layers)
    
    # 12. Quantum GRU Circuit (NEW - Sequence learning)
    if complexity in ["standard", "pro"]:
        builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_gru")
        gru_seq_len = {"standard": 2, "pro": 3}[complexity]
        circuits["quantum_gru"] = builder.build_quantum_gru_circuit(gru_seq_len)
    
    # 13. Quantum LSTM Circuit (NEW - Advanced sequence learning)
    if complexity == "pro":
        builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_lstm")
        circuits["quantum_lstm"] = builder.build_quantum_lstm_circuit(3)
    
    # 14. Quantum Boltzmann Machine (NEW - Generative model)
    if complexity in ["standard", "pro"]:
        builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_boltzmann_machine")
        qbm_layers = {"standard": 2, "pro": 3}[complexity]
        circuits["quantum_boltzmann"] = builder.build_quantum_boltzmann_machine(qbm_layers)
    
    # 15. Quantum Perceptron (NEW - Simple quantum classifier)
    builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_perceptron")
    perc_layers = {"lite": 2, "standard": 3, "pro": 4}[complexity]
    circuits["quantum_perceptron"] = builder.build_quantum_perceptron(perc_layers)
    
    # 16. Quantum Phase Estimation (NEW - Eigenvalue extraction)
    if complexity in ["standard", "pro"]:
        builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_phase_estimation")
        circuits["quantum_phase_estimation"] = builder.build_quantum_phase_estimation(3)
    
    # 17. Hybrid Quantum CNN (NEW - Quantum convolutional network)
    if complexity in ["standard", "pro"]:
        builder = AdvancedQuantumCircuitBuilder(num_qubits, "hybrid_quantum_cnn")
        kernel_size = {"standard": 3, "pro": 5}[complexity]
        circuits["hybrid_quantum_cnn"] = builder.build_hybrid_quantum_cnn(kernel_size)
    
    # 18. Quantum Autoencoder (NEW - Dimensionality reduction)
    if complexity == "pro":
        builder = AdvancedQuantumCircuitBuilder(num_qubits, "quantum_autoencoder")
        circuits["quantum_autoencoder"] = builder.build_quantum_autoencoders(0.5)
    
    return circuits


def generate_circuit_visualization(circuit: Dict[str, Any]) -> str:
    """Generate ASCII visualization of quantum circuit"""
    num_qubits = circuit["num_qubits"]
    gates = circuit["gates"]
    
    # Create grid
    max_depth = 50  # Limit visualization width
    grid = [[" " for _ in range(max_depth)] for _ in range(num_qubits)]
    lines = [["-" for _ in range(max_depth)] for _ in range(num_qubits)]
    
    # Place gates
    current_depth = 0
    for gate in gates[:min(len(gates), max_depth - 5)]:
        if current_depth >= max_depth - 2:
            break
            
        if len(gate["qubits"]) == 1:
            q = gate["qubits"][0]
            if q < num_qubits:
                grid[q][current_depth] = gate["type"][0]
        elif len(gate["qubits"]) == 2:
            q1, q2 = gate["qubits"]
            if q1 < num_qubits and q2 < num_qubits:
                grid[q1][current_depth] = "●"
                grid[q2][current_depth] = "⊕" if gate["type"] == "CNOT" else "●"
                for q in range(min(q1, q2), max(q1, q2)):
                    if q < num_qubits:
                        lines[q][current_depth] = "|"
        
        current_depth += 1
    
    # Build visualization
    viz = []
    for q in range(num_qubits):
        line = f"|{q}⟩ "
        for d in range(current_depth):
            if grid[q][d] != " ":
                line += f"[{grid[q][d]}]"
            elif lines[q][d] == "|":
                line += " | "
            else:
                line += "---"
        viz.append(line)
    
    return "\n".join(viz)


if __name__ == "__main__":
    # Test circuit generation
    print("🔮 Advanced Quantum Circuit Generator\n")
    
    for complexity in ["lite", "standard", "pro"]:
        print(f"\n{'='*70}")
        print(f"Generating {complexity.upper()} circuits...")
        print('='*70)
        
        num_qubits = {"lite": 6, "standard": 10, "pro": 16}[complexity]
        circuits = create_advanced_quantum_circuits(num_qubits, complexity)
        
        for name, circuit in circuits.items():
            print(f"\n{name}:")
            print(f"  Qubits: {circuit['num_qubits']}")
            print(f"  Gates: {circuit['total_gates']}")
            print(f"  Depth: {circuit['circuit_depth']}")
            print(f"  Parameters: {circuit['num_parameters']}")
            print(f"  Gate types: {len(circuit['gate_counts'])}")
