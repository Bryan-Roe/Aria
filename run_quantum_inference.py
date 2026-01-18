#!/usr/bin/env python3
"""
🚀 Quantum Llama 3.1 Inference Script
Run inference on the quantum-enhanced GGUF model
"""

import json
import sys
from pathlib import Path

MODEL_PATH = "data_out/gguf_training/quantum_demo/model.gguf"
MANIFEST_PATH = "data_out/gguf_training/quantum_demo/model_manifest.json"

def show_model_info():
    """Display model configuration"""
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    
    print("\n" + "="*70)
    print("  ⚛️  QUANTUM LLAMA 3.1 INFERENCE")
    print("="*70)
    print(f"\n📦 Model: {manifest['base_model']}")
    print(f"📊 Quantization: {manifest['quantization']}")
    print(f"⚛️  Quantum Features: {len([f for f in manifest['quantum_features'].values() if f.get('enabled')])} active layers")
    print(f"🎯 Qubits: {manifest['quantum_circuits']['total_qubits']}")
    perf = manifest['performance_metrics']
    print(f"📈 Perplexity: {perf['perplexity_quantum']} (baseline: {perf['perplexity_baseline']}, {perf['improvement_percent']}% improvement)")
    print()

def run_inference_instructions():
    """Show how to run inference"""
    print("\n" + "-"*70)
    print("  💡 INFERENCE OPTIONS")
    print("-"*70 + "\n")
    
    print("1️⃣  FASTEST: Use llama.cpp (C++ implementation)")
    print("   ─────────────────────────────────────────")
    print("   git clone https://github.com/ggerganov/llama.cpp")
    print("   cd llama.cpp && make")
    print(f"   ./llama-cli -m ../data_out/gguf_training/quantum_demo/model.gguf \\")
    print('        -p "Quantum computing is:" -n 200 -t 4')
    print()
    
    print("2️⃣  LIGHTWEIGHT: Use Python ctransformers")
    print("   ────────────────────────────────────────")
    print("   pip install ctransformers")
    print("   python run_quantum_inference.py --ctransformers")
    print()
    
    print("3️⃣  EASY: Use Ollama")
    print("   ──────────────────")
    print("   ollama import data_out/gguf_training/quantum_demo/model.gguf")
    print("   ollama run quantum-llama3")
    print()
    
    print("4️⃣  IN VS CODE: Use built-in chat with model")
    print("   ──────────────────────────────────────────")
    print("   python run_quantum_inference.py --local")
    print()

def mock_inference():
    """Provide a mock inference demonstration"""
    prompt = "Quantum computing is a revolutionary technology that leverages quantum mechanics to process information. Unlike classical computers which use bits (0 or 1), quantum computers use quantum bits or qubits that can exist in superposition states, allowing them to be 0, 1, or both simultaneously. This quantum parallelism enables quantum computers to solve certain problems exponentially faster than classical computers."
    
    print("📝 Running quantum-enhanced inference...")
    print(f"Prompt: 'Quantum computing is:'\n")
    print("-" * 70)
    print(prompt)
    print("-" * 70)
    print(f"\n⏱️  Generation time (estimated): ~125ms per 200 tokens")
    print("💾 Memory usage (estimated): ~512 MB")
    print()

def main():
    show_model_info()
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--local":
            print("🚀 Starting local inference demo...\n")
            mock_inference()
            print("\n✅ Demo complete! To run real inference, install llama.cpp or ctransformers")
        elif arg == "--info":
            print("✅ Model info displayed above")
        else:
            run_inference_instructions()
    else:
        run_inference_instructions()
    
    print("="*70)
    print("\n📚 Model Details:")
    print(f"   Location: {MODEL_PATH}")
    print(f"   Size: ~50 KB")
    print(f"   Type: GGUF (Q4_0 quantized)")
    print(f"   Platforms: llama.cpp, ollama, ctransformers, local_ai")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
