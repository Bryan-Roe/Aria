#!/bin/bash

echo "🚀 GPU Setup for PyTorch Training"
echo "=================================="

# Detect system
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS detected - Installing PyTorch with Metal Performance Shaders"
    pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    echo "Note: Metal support requires PyTorch 1.12+ on M1/M2/M3 chips"
    
elif lspci 2>/dev/null | grep -i nvidia >/dev/null; then
    echo "🔷 NVIDIA GPU detected - Installing CUDA-enabled PyTorch"
    pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    
elif lspci 2>/dev/null | grep -i amd >/dev/null; then
    echo "🔴 AMD GPU detected - Installing ROCm-enabled PyTorch"
    pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7
    
else
    echo "⚠️  No GPU hardware detected, but installing CUDA PyTorch for compatibility"
    echo "    Your GPUs will be used automatically when available"
    pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
fi

echo ""
echo "✅ PyTorch GPU installation complete!"
echo ""
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU Count: {torch.cuda.device_count()}')"

