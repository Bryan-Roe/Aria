"""
Quantum Circuit Visualization Tool
Supports both CLI and web-based visualization
"""
import pennylane as qml
import matplotlib.pyplot as plt

try:
    from qiskit import QuantumCircuit
    from qiskit.visualization import circuit_drawer
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    QuantumCircuit = None
from pathlib import Path
from typing import Optional, Union, Literal
import logging
import io
import base64

logger = logging.getLogger(__name__)


class CircuitVisualizer:
    """
    Unified circuit visualization tool for PennyLane and Qiskit.
    """
    
    def __init__(self, output_dir: str = "circuit_visualizations"):
        """
        Initialize visualizer.
        
        Args:
            output_dir: Directory to save visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Circuit visualizer initialized, output: {self.output_dir}")
    
    def visualize_pennylane(
        self,
        qnode: qml.QNode,
        sample_input: Optional[list] = None,
        style: Literal["default", "sketch", "pennylane"] = "pennylane",
        filename: Optional[str] = None,
        show: bool = True
    ) -> str:
        """
        Visualize a PennyLane QNode.
        
        Args:
            qnode: PennyLane QNode to visualize
            sample_input: Sample input for circuit (if parameterized)
            style: Drawing style
            filename: Output filename (None for auto-generate)
            show: Whether to display the plot
            
        Returns:
            Path to saved visualization
        """
        try:
            # Draw circuit
            fig, ax = qml.draw_mpl(qnode, style=style)(sample_input) if sample_input else qml.draw_mpl(qnode, style=style)()
            
            # Save
            if filename is None:
                filename = f"pennylane_circuit_{id(qnode)}.png"
            
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            logger.info(f"PennyLane circuit saved to {filepath}")
            
            if show:
                plt.show()
            else:
                plt.close()
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error visualizing PennyLane circuit: {e}")
            # Fallback to text representation
            return self._text_representation_pennylane(qnode, sample_input, filename)
    
    def visualize_qiskit(
        self,
        circuit,
        style: Literal["mpl", "text", "latex"] = "mpl",
        filename: Optional[str] = None,
        show: bool = True
    ) -> str:
        """
        Visualize a Qiskit QuantumCircuit.
        
        Args:
            circuit: Qiskit QuantumCircuit
            style: Drawing style ('mpl', 'text', 'latex')
            filename: Output filename
            show: Whether to display
            
        Returns:
            Path to saved visualization
        """
        if not QISKIT_AVAILABLE:
            logger.error("Qiskit not installed. Install with: pip install qiskit qiskit-aer")
            return ""
        
        try:
            if filename is None:
                filename = f"qiskit_circuit_{id(circuit)}.png"
            
            filepath = self.output_dir / filename
            
            if style == "mpl":
                fig = circuit_drawer(circuit, output='mpl', style={'backgroundcolor': '#EFEFEF'})
                fig.savefig(filepath, dpi=150, bbox_inches='tight')
                
                if show:
                    plt.show()
                else:
                    plt.close()
            
            elif style == "text":
                text_output = circuit.draw(output='text')
                filepath = filepath.with_suffix('.txt')
                with open(filepath, 'w') as f:
                    f.write(str(text_output))
            
            elif style == "latex":
                latex_output = circuit.draw(output='latex_source')
                filepath = filepath.with_suffix('.tex')
                with open(filepath, 'w') as f:
                    f.write(latex_output)
            
            logger.info(f"Qiskit circuit saved to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error visualizing Qiskit circuit: {e}")
            return self._text_representation_qiskit(circuit, filename)
    
    def _text_representation_pennylane(
        self,
        qnode: qml.QNode,
        sample_input: Optional[list],
        filename: Optional[str]
    ) -> str:
        """Fallback text representation for PennyLane"""
        if filename is None:
            filename = f"pennylane_circuit_{id(qnode)}.txt"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            if sample_input:
                f.write(qml.draw(qnode)(sample_input))
            else:
                f.write(qml.draw(qnode)())
        
        logger.info(f"Text representation saved to {filepath}")
        return str(filepath)
    
    def _text_representation_qiskit(
        self,
        circuit: QuantumCircuit,
        filename: Optional[str]
    ) -> str:
        """Fallback text representation for Qiskit"""
        if filename is None:
            filename = f"qiskit_circuit_{id(circuit)}.txt"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(str(circuit.draw(output='text')))
        
        logger.info(f"Text representation saved to {filepath}")
        return str(filepath)
    
    def compare_circuits(
        self,
        circuits: list,
        labels: list,
        filename: str = "circuit_comparison.png"
    ):
        """
        Compare multiple circuits side-by-side.
        
        Args:
            circuits: List of circuits (PennyLane QNodes or Qiskit circuits)
            labels: Labels for each circuit
            filename: Output filename
        """
        n_circuits = len(circuits)
        fig, axes = plt.subplots(1, n_circuits, figsize=(6 * n_circuits, 4))
        
        if n_circuits == 1:
            axes = [axes]
        
        for i, (circuit, label) in enumerate(zip(circuits, labels)):
            ax = axes[i]
            
            if isinstance(circuit, qml.QNode):
                # PennyLane circuit
                qml.drawer.tape_mpl(circuit.tape)(ax=ax)
                ax.set_title(label, fontsize=12, fontweight='bold')
            
            elif isinstance(circuit, QuantumCircuit):
                # Qiskit circuit
                circuit.draw('mpl', ax=ax)
                ax.set_title(label, fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        logger.info(f"Circuit comparison saved to {filepath}")
        plt.show()
    
    def export_html(
        self,
        circuit,
        title: str = "Quantum Circuit",
        filename: str = "circuit.html"
    ) -> str:
        """
        Export circuit as interactive HTML.
        
        Args:
            circuit: Circuit to export
            title: Page title
            filename: Output HTML filename
            
        Returns:
            Path to HTML file
        """
        filepath = self.output_dir / filename
        
        # Generate circuit image
        if isinstance(circuit, qml.QNode):
            try:
                fig, ax = qml.draw_mpl(circuit)()
                
                # Convert to base64
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode()
                plt.close()
            except:
                img_base64 = None
        else:
            try:
                fig = circuit.draw('mpl')
                
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode()
                plt.close()
            except:
                img_base64 = None
        
        # Generate HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            margin-bottom: 30px;
        }}
        .circuit-image {{
            text-align: center;
            margin: 30px 0;
        }}
        .circuit-image img {{
            max-width: 100%;
            height: auto;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
        }}
        .info {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .info h3 {{
            margin-top: 0;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="circuit-image">
            {'<img src="data:image/png;base64,' + img_base64 + '" alt="Circuit Diagram">' if img_base64 else '<p>Circuit visualization not available</p>'}
        </div>
        
        <div class="info">
            <h3>Circuit Information</h3>
            <p><strong>Type:</strong> {'PennyLane QNode' if isinstance(circuit, qml.QNode) else 'Qiskit QuantumCircuit'}</p>
            <p><strong>Number of qubits:</strong> {circuit.device.num_wires if isinstance(circuit, qml.QNode) else circuit.num_qubits}</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML export saved to {filepath}")
        return str(filepath)


def demo():
    """Demonstrate circuit visualization"""
    print("=" * 70)
    print("  QUANTUM CIRCUIT VISUALIZATION DEMO")
    print("=" * 70)
    
    visualizer = CircuitVisualizer()
    
    # Example 1: Simple PennyLane circuit
    print("\n[1] Visualizing PennyLane circuit...")
    
    dev = qml.device('lightning.qubit', wires=3)
    
    @qml.qnode(dev)
    def circuit(x):
        qml.RY(x[0], wires=0)
        qml.RY(x[1], wires=1)
        qml.CNOT(wires=[0, 1])
        qml.CNOT(wires=[1, 2])
        qml.RZ(x[2], wires=2)
        return qml.expval(qml.PauliZ(0))
    
    sample_input = [0.5, 1.0, 0.3]
    path = visualizer.visualize_pennylane(
        circuit,
        sample_input,
        filename="demo_pennylane.png",
        show=False
    )
    print(f"✓ Saved to: {path}")
    
    # Example 2: Qiskit circuit
    print("\n[2] Visualizing Qiskit circuit...")
    
    qc = QuantumCircuit(3, 3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.measure([0, 1, 2], [0, 1, 2])
    
    path = visualizer.visualize_qiskit(
        qc,
        style="mpl",
        filename="demo_qiskit.png",
        show=False
    )
    print(f"✓ Saved to: {path}")
    
    # Example 3: HTML export
    print("\n[3] Exporting to HTML...")
    
    path = visualizer.export_html(
        circuit,
        title="Variational Quantum Circuit Demo",
        filename="demo_circuit.html"
    )
    print(f"✓ Saved to: {path}")
    
    print("\n" + "=" * 70)
    print("✓ Demo completed!")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo()
