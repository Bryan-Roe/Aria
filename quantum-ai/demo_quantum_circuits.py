#!/usr/bin/env python3
"""
Unified Quantum Circuit Demo
Demonstrates all new quantum circuit capabilities
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from grover_circuit import GroverCircuit
from enhanced_variational_circuit import EnhancedVariationalCircuit, compare_encodings
from circuit_visualizer import CircuitVisualizer
from azure_quantum_tester import AzureQuantumTester
import torch
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_grover():
    """Demo Grover's algorithm"""
    print("\n" + "=" * 70)
    print("  1. GROVER'S QUANTUM SEARCH ALGORITHM")
    print("=" * 70)
    
    # Search for item 5 in 8-item database
    grover = GroverCircuit(n_qubits=3, shots=1000)
    results = grover.search(marked_states=[5])
    
    print(f"\n✓ Found item '5' with {results['success_probability']:.1%} probability")
    print(f"  Optimal iterations: {grover.n_iterations}")
    print(f"  Search space: {grover.search_space_size} items")
    
    # Visualize amplitude amplification
    try:
        grover.visualize_amplitudes(marked_states=[5])
        print("  Visualization saved: grover_amplification.png")
    except Exception as e:
        logger.warning(f"Visualization skipped: {e}")


def demo_enhanced_vqc():
    """Demo enhanced variational circuits"""
    print("\n" + "=" * 70)
    print("  2. ENHANCED VARIATIONAL CIRCUITS")
    print("=" * 70)
    
    encodings = ["angle", "amplitude", "iqp", "hybrid"]
    test_input = torch.randn(4) * 0.5
    
    print(f"\nTest input: {test_input.tolist()}")
    
    for encoding in encodings:
        circuit = EnhancedVariationalCircuit(
            n_qubits=4,
            n_layers=2,
            encoding=encoding,
            entanglement="pyramid",
            use_data_reuploading=True
        )
        
        output = circuit.forward(test_input)
        info = circuit.get_circuit_info()
        
        print(f"\n  {encoding.upper():12} | params: {info['n_parameters']:3} | depth: ~{info['circuit_depth_estimate']:2} | output shape: {output.shape}")
    
    print("\n✓ All encoding strategies tested successfully")


def demo_visualization():
    """Demo circuit visualization"""
    print("\n" + "=" * 70)
    print("  3. CIRCUIT VISUALIZATION")
    print("=" * 70)
    
    import pennylane as qml
    from qiskit import QuantumCircuit
    
    visualizer = CircuitVisualizer(output_dir="circuit_visualizations")
    
    # PennyLane circuit
    dev = qml.device('lightning.qubit', wires=3)
    
    @qml.qnode(dev)
    def pnl_circuit(x):
        qml.RY(x[0], wires=0)
        qml.RY(x[1], wires=1)
        qml.CNOT(wires=[0, 1])
        qml.CNOT(wires=[1, 2])
        qml.RZ(x[2], wires=2)
        return qml.expval(qml.PauliZ(0))
    
    try:
        path = visualizer.visualize_pennylane(
            pnl_circuit,
            sample_input=[0.5, 1.0, 0.3],
            filename="demo_pennylane.png",
            show=False
        )
        print(f"\n✓ PennyLane circuit: {path}")
    except Exception as e:
        logger.warning(f"PennyLane visualization skipped: {e}")
    
    # Qiskit circuit
    qc = QuantumCircuit(3, 3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.measure([0, 1, 2], [0, 1, 2])
    
    try:
        path = visualizer.visualize_qiskit(
            qc,
            style="mpl",
            filename="demo_qiskit.png",
            show=False
        )
        print(f"✓ Qiskit circuit: {path}")
    except Exception as e:
        logger.warning(f"Qiskit visualization skipped: {e}")
    
    # HTML export
    try:
        path = visualizer.export_html(
            pnl_circuit,
            title="Demo Quantum Circuit",
            filename="demo_circuit.html"
        )
        print(f"✓ HTML export: {path}")
    except Exception as e:
        logger.warning(f"HTML export skipped: {e}")


def demo_azure_quantum():
    """Demo Azure Quantum integration"""
    print("\n" + "=" * 70)
    print("  4. AZURE QUANTUM TESTING")
    print("=" * 70)
    
    try:
        tester = AzureQuantumTester()
        
        # List targets
        print("\nAvailable targets:")
        targets = tester.list_targets()
        for target in targets[:3]:
            print(f"  • {target['id']} ({target['provider']}) - {target['status']}")
        
        # Show test circuits
        circuits = tester.create_test_circuits()
        print(f"\n✓ Created {len(circuits)} test circuits: {list(circuits.keys())}")
        
        print("\nTo run full test suite:")
        print("  tester.run_test_suite(target_name='ionq.simulator', shots=100)")
        
    except Exception as e:
        logger.warning(f"Azure Quantum demo skipped: {e}")
        print("\n⚠️  Azure Quantum requires valid credentials in config/quantum_config.yaml")


def main():
    """Run all demos"""
    print("=" * 70)
    print("  QUANTUM CIRCUIT TOOLBOX DEMO")
    print("=" * 70)
    print("\nDemonstrating 4 new quantum circuit capabilities:")
    print("  1. Grover's Search Algorithm")
    print("  2. Enhanced Variational Circuits (Multiple Encodings)")
    print("  3. Circuit Visualization Tools")
    print("  4. Azure Quantum Testing Framework")
    
    try:
        demo_grover()
    except Exception as e:
        logger.error(f"Grover demo failed: {e}")
    
    try:
        demo_enhanced_vqc()
    except Exception as e:
        logger.error(f"Enhanced VQC demo failed: {e}")
    
    try:
        demo_visualization()
    except Exception as e:
        logger.error(f"Visualization demo failed: {e}")
    
    try:
        demo_azure_quantum()
    except Exception as e:
        logger.error(f"Azure Quantum demo failed: {e}")
    
    print("\n" + "=" * 70)
    print("  DEMO COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("  • Explore individual modules in quantum-ai/src/")
    print("  • Run visualizations: python -m src.circuit_visualizer")
    print("  • Test on Azure: python -m src.azure_quantum_tester")
    print("  • Try Grover search: python -m src.grover_circuit")
    print("=" * 70)


if __name__ == "__main__":
    main()
