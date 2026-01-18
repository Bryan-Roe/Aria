#!/usr/bin/env python3
"""
Export Quantum AI Models to GGUF Format

Converts trained quantum models to GGUF format for broader compatibility
with llama.cpp and other inference engines.
"""

import json
import os
import struct
import numpy as np
import torch
import pickle
from pathlib import Path
from typing import Dict, List, Tuple


class GGUFWriter:
    """Write models to GGUF format"""
    
    # GGUF format constants
    GGUF_MAGIC = 0x46554747  # "GGUF" in hex
    GGUF_VERSION = 3
    GGUF_ENDIAN = 1  # little-endian
    
    GGML_TYPE_F32 = 0
    GGML_TYPE_F16 = 1
    GGML_TYPE_Q4_0 = 2
    
    def __init__(self, filename: str):
        self.filename = filename
        self.file = None
        self.tensors: Dict[str, Tuple[np.ndarray, str]] = {}
        self.metadata = {}
        
    def add_tensor(self, name: str, tensor: np.ndarray, dtype: str = "f32"):
        """Add a tensor to export"""
        self.tensors[name] = (tensor, dtype)
        print(f"  ✓ Added tensor: {name} {tensor.shape} ({dtype})")
        
    def add_metadata(self, key: str, value):
        """Add metadata key-value pair"""
        self.metadata[key] = value
        
    def write(self):
        """Write GGUF file"""
        print(f"\n📝 Writing GGUF file: {self.filename}")
        
        with open(self.filename, 'wb') as f:
            # Write header
            f.write(struct.pack('<I', self.GGUF_MAGIC))
            f.write(struct.pack('<I', self.GGUF_VERSION))
            f.write(struct.pack('<I', self.GGUF_ENDIAN))
            
            # Write metadata count
            f.write(struct.pack('<Q', len(self.metadata)))
            
            # Write metadata
            for key, value in self.metadata.items():
                self._write_metadata_kv(f, key, value)
            
            # Write tensor count
            f.write(struct.pack('<Q', len(self.tensors)))
            
            # Write tensor info
            for name, (tensor, dtype) in self.tensors.items():
                self._write_tensor_info(f, name, tensor, dtype)
            
            # Align to 32-byte boundary
            pos = f.tell()
            align = (32 - (pos % 32)) % 32
            f.write(b'\x00' * align)
            
            # Write tensor data
            for name, (tensor, dtype) in self.tensors.items():
                data = self._convert_tensor(tensor, dtype)
                f.write(data)
                print(f"  ✓ Written: {name} ({len(data)} bytes)")
        
        size_mb = os.path.getsize(self.filename) / (1024 * 1024)
        print(f"  ✅ File written: {size_mb:.2f} MB")
        
    def _write_metadata_kv(self, f, key: str, value):
        """Write a metadata key-value pair"""
        # Key length (u32) + key (string)
        key_bytes = key.encode('utf-8')
        f.write(struct.pack('<I', len(key_bytes)))
        f.write(key_bytes)
        
        # Value type and data
        if isinstance(value, str):
            val_bytes = value.encode('utf-8')
            f.write(struct.pack('<I', 3))  # string type
            f.write(struct.pack('<Q', len(val_bytes)))
            f.write(val_bytes)
        elif isinstance(value, int):
            f.write(struct.pack('<I', 7))  # i64 type
            f.write(struct.pack('<q', value))
        elif isinstance(value, float):
            f.write(struct.pack('<I', 4))  # f32 type
            f.write(struct.pack('<f', value))
            
    def _write_tensor_info(self, f, name: str, tensor: np.ndarray, dtype: str):
        """Write tensor metadata"""
        name_bytes = name.encode('utf-8')
        f.write(struct.pack('<I', len(name_bytes)))
        f.write(name_bytes)
        
        # Shape
        f.write(struct.pack('<I', len(tensor.shape)))
        for dim in reversed(tensor.shape):  # GGUF uses reverse shape
            f.write(struct.pack('<Q', dim))
        
        # Data type
        if dtype == "f32":
            f.write(struct.pack('<I', self.GGML_TYPE_F32))
        elif dtype == "f16":
            f.write(struct.pack('<I', self.GGML_TYPE_F16))
        else:
            f.write(struct.pack('<I', self.GGML_TYPE_F32))
        
        # File offset placeholder
        f.write(struct.pack('<Q', 0))
        
    def _convert_tensor(self, tensor: np.ndarray, dtype: str) -> bytes:
        """Convert tensor to bytes"""
        if dtype == "f32":
            return tensor.astype(np.float32).tobytes()
        elif dtype == "f16":
            return tensor.astype(np.float16).tobytes()
        else:
            return tensor.astype(np.float32).tobytes()


def export_quantum_model_to_gguf(model_path: str, output_gguf: str, metadata: Dict = None):
    """Export quantum model to GGUF format"""
    
    print("=" * 70)
    print("🔄 QUANTUM AI MODEL → GGUF EXPORT")
    print("=" * 70)
    
    # Load model
    print(f"\n📂 Loading model from: {model_path}")
    if not os.path.exists(model_path):
        print(f"  ❌ Model file not found: {model_path}")
        return False
    
    try:
        model_state = torch.load(model_path, map_location='cpu')
        print(f"  ✅ Loaded {len(model_state)} tensors")
    except Exception as e:
        print(f"  ❌ Error loading model: {e}")
        return False
    
    # Create GGUF writer
    writer = GGUFWriter(output_gguf)
    
    # Add metadata
    if metadata:
        for key, value in metadata.items():
            writer.add_metadata(key, value)
    
    writer.add_metadata("general.name", "Quantum AI Model")
    writer.add_metadata("general.architecture", "hybrid-qnn")
    writer.add_metadata("general.type", "model")
    
    # Add tensors
    print("\n📊 Processing tensors...")
    for name, tensor in model_state.items():
        if isinstance(tensor, torch.Tensor):
            np_tensor = tensor.cpu().numpy()
        else:
            np_tensor = np.array(tensor)
        
        # Flatten if needed
        if len(np_tensor.shape) > 2:
            np_tensor = np_tensor.reshape(-1)
        
        writer.add_tensor(name, np_tensor, dtype="f32")
    
    # Write GGUF file
    writer.write()
    
    print("\n" + "=" * 70)
    print("✅ EXPORT COMPLETE!")
    print(f"  Output: {output_gguf}")
    print("=" * 70)
    
    return True


def export_quantum_ensemble_to_gguf(models_dir: str, output_gguf: str):
    """Export multiple quantum models as an ensemble"""
    
    print("=" * 70)
    print("🔄 QUANTUM AI ENSEMBLE → GGUF EXPORT")
    print("=" * 70)
    
    models_path = Path(models_dir)
    model_files = list(models_path.glob("*/custom_model.pt"))
    
    if not model_files:
        print(f"  ❌ No models found in {models_dir}")
        return False
    
    print(f"\n📂 Found {len(model_files)} models")
    
    writer = GGUFWriter(output_gguf)
    
    # Metadata
    writer.add_metadata("general.name", "Quantum AI Ensemble")
    writer.add_metadata("general.architecture", "hybrid-qnn-ensemble")
    writer.add_metadata("general.type", "ensemble")
    writer.add_metadata("ensemble.model_count", len(model_files))
    
    tensor_count = 0
    
    # Load and add all models
    for idx, model_file in enumerate(model_files, 1):
        print(f"\n  [{idx}/{len(model_files)}] {model_file.parent.name}")
        
        try:
            model_state = torch.load(model_file, map_location='cpu')
            
            for name, tensor in model_state.items():
                if isinstance(tensor, torch.Tensor):
                    np_tensor = tensor.cpu().numpy()
                else:
                    np_tensor = np.array(tensor)
                
                # Flatten if needed
                if len(np_tensor.shape) > 2:
                    np_tensor = np_tensor.reshape(-1)
                
                # Add model index to tensor name
                prefixed_name = f"model_{idx:02d}.{name}"
                writer.add_tensor(prefixed_name, np_tensor, dtype="f32")
                tensor_count += 1
        except Exception as e:
            print(f"    ⚠️  Error loading: {e}")
    
    # Write GGUF file
    print(f"\n📊 Total tensors to write: {tensor_count}")
    writer.write()
    
    print("\n" + "=" * 70)
    print("✅ ENSEMBLE EXPORT COMPLETE!")
    print(f"  Output: {output_gguf}")
    print(f"  Models combined: {len(model_files)}")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    import sys
    
    # Export best banknote model
    banknote_model = "/workspaces/AI/quantum-ai/results/custom_model.pt"
    banknote_gguf = "/workspaces/AI/data_out/quantum_banknote_perfect_model.gguf"
    
    metadata = {
        "task": "Banknote Authentication",
        "accuracy": "100.00%",
        "dataset": "Banknote Authentication (UCI)",
        "samples": "1371",
        "features": "4",
        "qubits": "4",
        "framework": "PennyLane + PyTorch",
    }
    
    export_quantum_model_to_gguf(banknote_model, banknote_gguf, metadata)
