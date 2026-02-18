#!/bin/bash
# GPU PyTorch Installation Script
# Auto-detects GPU hardware and installs the appropriate PyTorch version

set -e

echo "=========================================="
echo "🚀 GPU PyTorch Installation"
echo "=========================================="

# Detect OS and GPU
detect_gpu() {
    echo "🔍 Detecting GPU hardware..."
    
    # Check for NVIDIA
    if command -v nvidia-smi &> /dev/null; then
        echo "✅ NVIDIA GPU detected"
        return 1  # NVIDIA
    fi
    
    # Check for Apple Silicon
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if sysctl -a | grep -q "hw.optional.arm64"; then
            echo "✅ Apple Silicon detected"
            return 3  # Apple
        fi
    fi
    
    # Check for AMD (Linux)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v rocm-smi &> /dev/null; then
            echo "✅ AMD GPU detected"
            return 2  # AMD
        fi
    fi
    
    echo "⚠️  No GPU detected"
    return 0  # No GPU
}

# Install for NVIDIA
install_nvidia() {
    echo ""
    echo "📦 Installing PyTorch with CUDA 11.8 support..."
    echo "This may take 5-10 minutes..."
    echo ""
    
    pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    
    echo ""
    echo "✅ NVIDIA PyTorch installed with CUDA 11.8"
}

# Install for AMD
install_amd() {
    echo ""
    echo "📦 Installing PyTorch with ROCm 5.7 support..."
    echo "This may take 5-10 minutes..."
    echo ""
    
    pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7
    
    echo ""
    echo "✅ AMD PyTorch installed with ROCm 5.7"
}

# Install for Apple
install_apple() {
    echo ""
    echo "📦 Installing PyTorch with Apple Metal support..."
    echo "This may take 5-10 minutes..."
    echo ""
    
    pip install --upgrade torch torchvision torchaudio
    
    echo ""
    echo "✅ Apple PyTorch installed with Metal Performance Shaders"
}

# Verify installation
verify_installation() {
    echo ""
    echo "🧪 Verifying GPU support..."
    echo ""
    
    python3 << 'PYEOF'
import torch
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
if hasattr(torch.backends, 'mps'):
    print(f"Apple Metal (MPS) Available: {torch.backends.mps.is_available()}")
PYEOF
}

# Main
echo ""
detect_gpu
gpu_type=$?

case $gpu_type in
    1)
        install_nvidia
        ;;
    2)
        install_amd
        ;;
    3)
        install_apple
        ;;
    *)
        echo "❌ No GPU detected. Using CPU-only PyTorch."
        echo ""
        echo "If you have a GPU:"
        echo "  • NVIDIA: Install CUDA Toolkit from https://developer.nvidia.com/cuda-downloads"
        echo "  • AMD: Install ROCm from https://rocmdocs.amd.com/en/docs/deploy/linux/index.html"
        echo "  • Apple: Ensure you're on macOS 12.3+ with Apple Silicon"
        exit 1
        ;;
esac

verify_installation

echo ""
echo "=========================================="
echo "✅ GPU PyTorch Installation Complete"
echo "=========================================="
echo ""
echo "🚀 Ready to train on GPU!"
echo ""
echo "To start training with GPU:"
echo "  python scripts/training/autotrain.py"
echo "  python scripts/training/autonomous_training_orchestrator.py"
