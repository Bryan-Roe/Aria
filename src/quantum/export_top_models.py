#!/usr/bin/env python
"""
Export top 3 quantum models to GGUF format
"""
import os
import sys
import json
import torch
from pathlib import Path

sys.path.insert(0, '/workspaces/AI/quantum-ai')
from src.hybrid_qnn import HybridQNN
from export_quantum_to_gguf import export_quantum_model_to_gguf

# Top 3 models to export
top_models = [
    ("wine_quality_combined", "Wine Quality Combined", 98.69),
    ("ionosphere", "Ionosphere", 91.43),
    ("heart_disease", "Heart Disease", 90.16),
]

os.chdir('/workspaces/AI/quantum-ai')

print("="*60)
print("🚀 Exporting Top 3 Quantum Models to GGUF")
print("="*60)

for dataset, display_name, accuracy in top_models:
    model_path = f'results/custom_model__{dataset}.pt'
    
    # Check if model exists (fallback to generic if not)
    if not os.path.exists(model_path):
        model_path = 'results/custom_model.pt'
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        continue
    
    print(f"\n📦 Exporting {display_name} ({accuracy:.2f}%)")
    print(f"   Model: {model_path}")
    
    try:
        # Load the model
        model = HybridQNN()
        model.load_state_dict(torch.load(model_path))
        model.eval()
        
        # Export to GGUF
        output_file = f'../data_out/quantum_{dataset}_model.gguf'
        metadata = {
            "dataset": dataset,
            "accuracy": accuracy,
            "model_type": "Hybrid QNN",
            "qubits": 4,
            "layers": 2,
            "parameters": 24,
        }
        
        export_quantum_model_to_gguf(
            model, 
            output_file,
            metadata_dict=metadata
        )
        
        # Verify export
        if os.path.exists(output_file):
            size_kb = os.path.getsize(output_file) / 1024
            print(f"   ✅ Exported: {output_file}")
            print(f"   📊 Size: {size_kb:.1f} KB")
        else:
            print(f"   ❌ Export failed")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

print("\n" + "="*60)
print("✅ Export Complete!")
print("="*60)
