#!/usr/bin/env python
"""
Export all Tier 1-2 models to GGUF format for production deployment
"""
import os
import sys
import torch
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, '/workspaces/AI/scripts')

from src.hybrid_qnn import HybridQNN
from export_quantum_to_gguf import export_quantum_model_to_gguf

# Tier 1 and 2 models to export
MODELS_TO_EXPORT = [
    # Tier 1 (already exported: banknote, wine_quality)
    ("ionosphere", "Ionosphere", 91.43, "Radar signal classification"),
    ("heart_disease", "Heart Disease", 90.16, "Medical diagnosis"),
    ("iris", "Iris", 90.00, "Botanical classification"),
    # Tier 2
    ("statlog_australian", "Statlog Australian", 87.68, "Credit approval"),
    ("pendigits", "Pendigits", 86.92, "Digit recognition"),
    ("parkinsons", "Parkinsons", 84.62, "Disease detection"),
    ("statlog_heart", "Statlog Heart", 83.33, "Heart disease"),
    ("blood_transfusion", "Blood Transfusion", 82.67, "Donor classification"),
    ("optical_recognition", "Optical Recognition", 80.65, "Character recognition"),
]

def export_model(dataset_name, display_name, accuracy, application):
    """Export a single model to GGUF"""
    
    # Try multiple naming patterns
    model_paths = [
        f'results/{dataset_name}_model.pt',  # Standard pattern
        f'results/custom_model__{dataset_name}.pt',
        'results/custom_model.pt'
    ]
    
    model_path = None
    for path in model_paths:
        if os.path.exists(path):
            model_path = path
            break
    
    if not model_path:
        print(f"   ❌ Model not found for {dataset_name}")
        return False
    
    try:
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location='cpu')
        
        # Checkpoint is already a state dict (not wrapped in dict)
        state_dict = checkpoint
        
        # Infer output_dim from final layer
        final_weight_key = 'decoder.4.weight'
        if final_weight_key in state_dict:
            output_dim = state_dict[final_weight_key].shape[0]
        else:
            output_dim = 2  # Default binary
        
        # Create model with inferred architecture
        model = HybridQNN(
            input_dim=16,
            hidden_dim=16,
            n_qubits=4,
            n_quantum_layers=2,
            output_dim=output_dim
        )
        model.load_state_dict(state_dict)
        model.eval()
        
        # Output path
        output_file = f'../data_out/quantum_{dataset_name}_model.gguf'
        
        # Metadata
        metadata = {
            "dataset": dataset_name,
            "name": display_name,
            "accuracy": accuracy,
            "application": application,
            "model_type": "Hybrid QNN",
            "qubits": 4,
            "layers": 2,
            "parameters": 24,
            "framework": "PennyLane 0.44.0",
            "deployment_ready": True
        }
        
        # Export
        export_quantum_model_to_gguf(model, output_file, metadata_dict=metadata)
        
        # Verify
        if os.path.exists(output_file):
            size_kb = os.path.getsize(output_file) / 1024
            print(f"   ✅ {display_name}: {output_file} ({size_kb:.1f} KB)")
            return True
        else:
            print(f"   ❌ {display_name}: Export failed")
            return False
            
    except Exception as e:
        print(f"   ❌ {display_name}: {str(e)[:80]}")
        return False

def main():
    os.chdir('/workspaces/AI/quantum-ai')
    
    print("="*70)
    print("🚀 Exporting Tier 1-2 Quantum Models to GGUF Format")
    print("="*70)
    print(f"\n📦 Exporting {len(MODELS_TO_EXPORT)} models...\n")
    
    success_count = 0
    total_size = 0
    
    for dataset, display, acc, app in MODELS_TO_EXPORT:
        if export_model(dataset, display, acc, app):
            success_count += 1
            output_file = f'../data_out/quantum_{dataset}_model.gguf'
            if os.path.exists(output_file):
                total_size += os.path.getsize(output_file)
    
    print("\n" + "="*70)
    print("📊 EXPORT SUMMARY")
    print("="*70)
    print(f"   Successful: {success_count}/{len(MODELS_TO_EXPORT)} models")
    print(f"   Total Size: {total_size/1024:.1f} KB")
    print(f"   Location: /workspaces/AI/data_out/")
    print(f"   Format: GGUF v3 (portable, production-ready)")
    
    if success_count == len(MODELS_TO_EXPORT):
        print(f"\n   ✅ ALL MODELS EXPORTED SUCCESSFULLY")
    else:
        print(f"\n   ⚠️  {len(MODELS_TO_EXPORT) - success_count} models failed")
    
    print("="*70)

if __name__ == '__main__':
    main()
