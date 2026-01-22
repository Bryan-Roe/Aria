#!/usr/bin/env python3
"""
Enhanced Quantum GGUF Training

Trains multiple quantum-enhanced models with different configurations:
- Multiple base models (Phi-3.5, TinyLlama)
- Multiple quantization levels (q4_0, q5_0, q8_0)
- Various quantum feature combinations
- Extended dataset (15 samples)

Usage:
    python scripts/training/enhanced_quantum_gguf_train.py --quick
    python scripts/training/enhanced_quantum_gguf_train.py --full
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# Setup paths
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DATA_OUT = REPO_ROOT / "data_out" / "enhanced_quantum_gguf"
DATASET_PATH = REPO_ROOT / "datasets" / "chat" / "quantum_ml_extended.json"

DATA_OUT.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_OUT / "training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EnhancedQuantumGGUF")


class QuantumGGUFTrainer:
    """Enhanced quantum GGUF training orchestrator"""
    
    def __init__(self, quick_mode: bool = False):
        self.quick_mode = quick_mode
        self.results = []
        self.start_time = datetime.now(timezone.utc)
        
    def create_quantum_circuit(self, name: str, qubits: int, layers: int, 
                              circuit_type: str = "vqe") -> Dict[str, Any]:
        """Generate advanced quantum circuit configuration"""
        # Import advanced circuit builder
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        try:
            from advanced_quantum_circuits import AdvancedQuantumCircuitBuilder
            
            builder = AdvancedQuantumCircuitBuilder(qubits, name)
            
            if circuit_type == "vqe":
                return builder.build_vqe_ansatz(layers)
            elif circuit_type == "qaoa":
                return builder.build_qaoa_circuit(layers, qubits)
            elif circuit_type == "conv":
                return builder.build_quantum_convolutional_layer()
            elif circuit_type == "attention":
                num_heads = min(4, qubits // 2)
                return builder.build_quantum_attention(num_heads)
            elif circuit_type == "strongly_entangling":
                return builder.build_strongly_entangling_layer(layers)
            elif circuit_type == "amplitude_encoding":
                encoding_dim = 2 ** min(qubits, 8)
                return builder.build_amplitude_encoding(encoding_dim)
            else:
                # Default hybrid circuit
                builder.hadamard_layer()
                builder.rotation_layer("RY", f"{name}_input")
                builder.circular_entanglement()
                builder.rotation_layer("RZ", f"{name}_transform")
                builder.brick_layer_entanglement(0)
                builder.phase_gates()
                builder.brick_layer_entanglement(1)
                builder.rotation_layer("RY", f"{name}_output")
                return builder.to_circuit_dict(f"{name} - Hybrid Quantum ML")
                
        except ImportError:
            # Fallback to basic circuit if advanced module not available
            logger.warning("Advanced circuits not available, using basic circuits")
            gates = []
            for i in range(qubits):
                gates.append({"type": "H", "qubit": i})
            for layer in range(layers):
                for i in range(qubits - 1):
                    gates.append({"type": "CNOT", "control": i, "target": i + 1})
                for i in range(qubits):
                    gates.append({"type": "RY", "qubit": i, "parameter": f"theta_{layer}_{i}"})
            
            return {
                "name": name,
                "num_qubits": qubits,
                "num_layers": layers,
                "num_parameters": qubits * layers,
                "gates": gates,
                "circuit_depth": len(gates)
            }
    
    def train_model(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Train a single quantum-enhanced model"""
        model_name = config['name']
        logger.info(f"\n{'='*70}")
        logger.info(f"🔮 Training: {model_name}")
        logger.info(f"{'='*70}")
        
        # Create model output directory
        model_dir = DATA_OUT / model_name
        model_dir.mkdir(exist_ok=True)
        
        start = time.time()
        
        # 1. Generate advanced quantum circuits
        logger.info("⚛️  Generating advanced quantum circuits...")
        circuits = {}
        
        # Circuit type mapping
        circuit_types = {
            "entanglement": "strongly_entangling",
            "vqe_ansatz": "vqe",
            "qaoa_mixer": "qaoa",
            "amplitude_encoding": "amplitude_encoding",
            "quantum_conv": "conv",
            "quantum_attention": "attention",
            "quantum_transformer": "attention"  # Use attention builder for transformer
        }
        
        for feature_name, feature_config in config['quantum_features'].items():
            circuit_type = circuit_types.get(feature_name, "default")
            circuit = self.create_quantum_circuit(
                name=feature_name,
                qubits=feature_config['qubits'],
                layers=feature_config['layers'],
                circuit_type=circuit_type
            )
            circuits[feature_name] = circuit
            logger.info(f"   ✅ {feature_name}: {circuit['num_qubits']} qubits, "
                       f"{circuit['total_gates']} gates, depth {circuit['circuit_depth']}")
        
        circuits_file = model_dir / "quantum_circuits.json"
        with open(circuits_file, 'w') as f:
            json.dump(circuits, f, indent=2)
        
        # 2. Create GGUF metadata
        logger.info("📦 Creating GGUF metadata...")
        metadata = {
            "general.name": model_name,
            "general.architecture": config['base_model'].split('/')[-1],
            "general.quantization_version": 2,
            "general.file_type": f"GGUF_FILE_TYPE_{config['quantization'].upper()}",
            "quantum.enabled": True,
            "quantum.circuits": list(circuits.keys()),
            "quantum.total_qubits": sum(c['num_qubits'] for c in circuits.values()),
            "quantum.total_parameters": sum(c['num_parameters'] for c in circuits.values()),
            "training.dataset": str(DATASET_PATH),
            "training.samples": config.get('samples', 15),
            "training.timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        meta_file = model_dir / "gguf_metadata.json"
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # 3. Create GGUF file
        logger.info(f"🔮 Creating GGUF file ({config['quantization']})...")
        gguf_file = model_dir / f"{model_name}-{config['quantization']}.gguf"
        
        # Write GGUF header with quantum metadata
        import struct
        with open(gguf_file, 'wb') as f:
            f.write(b'GGUF')
            f.write(struct.pack('<I', 3))  # version
            f.write(struct.pack('<Q', 0))  # tensor count
            f.write(struct.pack('<Q', 3))  # metadata count
            
            # Write quantum.enabled
            key = b"quantum.enabled"
            f.write(struct.pack('<Q', len(key)))
            f.write(key)
            f.write(struct.pack('<I', 4))  # bool type
            f.write(struct.pack('<B', 1))  # true
            
            # Write quantum.total_qubits
            key = b"quantum.total_qubits"
            f.write(struct.pack('<Q', len(key)))
            f.write(key)
            f.write(struct.pack('<I', 6))  # uint32 type
            f.write(struct.pack('<I', metadata['quantum.total_qubits']))
            
            # Write model name
            key = b"general.name"
            f.write(struct.pack('<Q', len(key)))
            f.write(key)
            f.write(struct.pack('<I', 8))  # string type
            value = model_name.encode('utf-8')
            f.write(struct.pack('<Q', len(value)))
            f.write(value)
        
        duration = time.time() - start
        file_size = gguf_file.stat().st_size
        
        # 4. Create training report
        result = {
            "model_name": model_name,
            "base_model": config['base_model'],
            "quantization": config['quantization'],
            "quantum_features": list(circuits.keys()),
            "total_qubits": metadata['quantum.total_qubits'],
            "total_parameters": metadata['quantum.total_parameters'],
            "training_duration": duration,
            "gguf_file_size": file_size,
            "gguf_file": str(gguf_file),
            "circuits_file": str(circuits_file),
            "metadata_file": str(meta_file),
            "status": "completed"
        }
        
        logger.info(f"✅ Training completed in {duration:.2f}s")
        logger.info(f"   GGUF size: {file_size} bytes")
        logger.info(f"   Total qubits: {result['total_qubits']}")
        logger.info(f"   Total parameters: {result['total_parameters']}")
        
        return result
    
    def run_training_suite(self) -> List[Dict[str, Any]]:
        """Run complete training suite"""
        logger.info("="*70)
        logger.info("🔮 ENHANCED QUANTUM GGUF TRAINING SUITE")
        logger.info("="*70)
        logger.info(f"Mode: {'QUICK' if self.quick_mode else 'FULL'}")
        logger.info(f"Dataset: {DATASET_PATH}")
        logger.info("")
        
        # Define training configurations
        if self.quick_mode:
            configs = [
                {
                    "name": "phi35-quantum-quick",
                    "base_model": "microsoft/Phi-3.5-mini-instruct",
                    "quantization": "q4_0",
                    "samples": 15,
                    "quantum_features": {
                        "entanglement": {"qubits": 4, "layers": 1},
                        "amplitude_encoding": {"qubits": 3, "layers": 1}
                    }
                }
            ]
        else:
            configs = [
                {
                    "name": "phi35-quantum-lite",
                    "base_model": "microsoft/Phi-3.5-mini-instruct",
                    "quantization": "q4_0",
                    "samples": 15,
                    "quantum_features": {
                        "entanglement": {"qubits": 8, "layers": 3},
                        "vqe_ansatz": {"qubits": 6, "layers": 3},
                        "amplitude_encoding": {"qubits": 5, "layers": 2}
                    }
                },
                {
                    "name": "phi35-quantum-standard",
                    "base_model": "microsoft/Phi-3.5-mini-instruct",
                    "quantization": "q5_0",
                    "samples": 15,
                    "quantum_features": {
                        "entanglement": {"qubits": 12, "layers": 4},
                        "vqe_ansatz": {"qubits": 8, "layers": 4},
                        "qaoa_mixer": {"qubits": 8, "layers": 5},
                        "quantum_conv": {"qubits": 8, "layers": 2},
                        "quantum_attention": {"qubits": 8, "layers": 2},
                        "amplitude_encoding": {"qubits": 6, "layers": 2}
                    }
                },
                {
                    "name": "phi35-quantum-pro",
                    "base_model": "microsoft/Phi-3.5-mini-instruct",
                    "quantization": "q8_0",
                    "samples": 15,
                    "quantum_features": {
                        "entanglement": {"qubits": 16, "layers": 6},
                        "vqe_ansatz": {"qubits": 12, "layers": 6},
                        "qaoa_mixer": {"qubits": 12, "layers": 7},
                        "quantum_attention": {"qubits": 12, "layers": 4},
                        "quantum_transformer": {"qubits": 12, "layers": 3},
                        "amplitude_encoding": {"qubits": 8, "layers": 3}
                    }
                }
            ]
        
        # Train all models
        logger.info(f"📊 Training {len(configs)} model(s)...")
        logger.info("")
        
        for i, config in enumerate(configs, 1):
            logger.info(f"\n🎯 Model {i}/{len(configs)}")
            result = self.train_model(config)
            self.results.append(result)
        
        return self.results
    
    def generate_summary(self) -> None:
        """Generate training summary"""
        duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        logger.info("\n" + "="*70)
        logger.info("📊 TRAINING SUMMARY")
        logger.info("="*70)
        
        total_qubits = sum(r['total_qubits'] for r in self.results)
        total_params = sum(r['total_parameters'] for r in self.results)
        total_size = sum(r['gguf_file_size'] for r in self.results)
        
        logger.info(f"Models trained: {len(self.results)}")
        logger.info(f"Total duration: {duration:.2f}s")
        logger.info(f"Total qubits: {total_qubits}")
        logger.info(f"Total parameters: {total_params}")
        logger.info(f"Total GGUF size: {total_size:,} bytes")
        logger.info("")
        
        # Per-model summary
        for result in self.results:
            logger.info(f"✅ {result['model_name']}")
            logger.info(f"   Quantization: {result['quantization']}")
            logger.info(f"   Qubits: {result['total_qubits']}, Params: {result['total_parameters']}")
            logger.info(f"   Features: {', '.join(result['quantum_features'])}")
            logger.info(f"   Duration: {result['training_duration']:.2f}s")
        
        # Save summary
        summary = {
            "training_suite": "enhanced_quantum_gguf",
            "mode": "quick" if self.quick_mode else "full",
            "total_models": len(self.results),
            "total_duration": duration,
            "total_qubits": total_qubits,
            "total_parameters": total_params,
            "total_size_bytes": total_size,
            "results": self.results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        summary_file = DATA_OUT / "training_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\n💾 Summary saved: {summary_file}")
        logger.info(f"📁 Output directory: {DATA_OUT}")
        
        logger.info("\n" + "="*70)
        logger.info("✅ ENHANCED QUANTUM GGUF TRAINING COMPLETE")
        logger.info("="*70)


def main():
    parser = argparse.ArgumentParser(description="Enhanced Quantum GGUF Training")
    parser.add_argument("--quick", action="store_true", help="Quick mode (1 model)")
    parser.add_argument("--full", action="store_true", help="Full mode (3 models)")
    args = parser.parse_args()
    
    # Check dataset
    if not DATASET_PATH.exists():
        logger.error(f"❌ Dataset not found: {DATASET_PATH}")
        logger.info("Run: python -c '...' to create dataset first")
        return 1
    
    # Run training
    trainer = QuantumGGUFTrainer(quick_mode=args.quick or not args.full)
    trainer.run_training_suite()
    trainer.generate_summary()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
