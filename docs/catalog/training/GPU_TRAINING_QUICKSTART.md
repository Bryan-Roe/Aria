# 🚀 GPU Training Quick Start Guide

Your training is fully configured for GPU acceleration. Here's how to run it on your machine:

## Prerequisites

### Step 1: Install GPU-Enabled PyTorch

Run this once on your machine (not in the cloud environment):

```bash
# Automatically detect and install GPU PyTorch
bash install_gpu_pytorch.sh

# OR manually for your GPU type:

# NVIDIA (CUDA 11.8)
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# AMD (ROCm 5.7)
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7

# Apple Silicon (M1/M2/M3)
pip install --upgrade torch torchvision torchaudio

# CPU only (fallback)
pip install torch torchvision torchaudio
```

### Step 2: Verify GPU Support

```bash
python scripts/gpu_config.py
```

Expected output:
```
✅ Using device: cuda
✅ CUDA (NVIDIA GPUs):
   Available: YES
   Device Count: 2
   GPU 0: NVIDIA RTX A6000
           Compute Capability: 8.6
           Total Memory: 48.0 GB
   GPU 1: NVIDIA RTX A6000
           Total Memory: 48.0 GB
```

## Quick Start: Train on GPU

### Fastest: Single Command GPU Training

```bash
# Auto-detect GPU and start training
python scripts/setup_gpu_training.py && python scripts/training/autotrain.py
```

### Option 1: GPU Autotrain (14 Jobs, ~2-4 hours)

```bash
python scripts/training/autotrain.py --config config/training/autotrain.yaml
```

**What it does:**
- Runs 14 LoRA fine-tuning jobs in parallel
- Models: Phi-3.5, Qwen2.5
- Datasets: Chat, quantum, mixed
- GPU: Automatically uses all available GPUs
- Output: `data_out/autotrain/status.json`

**Monitor progress:**
```bash
# In another terminal
watch -n 1 tail -20 data_out/autotrain/status.json
nvidia-smi -l 1  # Monitor GPU usage
```

### Option 2: Continuous Autonomous Training

```bash
# Runs 30-minute training cycles indefinitely
nohup python scripts/training/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &

# Monitor
tail -f data_out/autonomous_training.log
watch -n 5 'cat data_out/autonomous_training_status.json | python -m json.tool'
```

**Features:**
- Self-discovers datasets (1,191+ quantum datasets available)
- Adaptive epochs: Increases if accuracy plateau
- Auto-deploy best models
- Graceful error recovery
- Logs to `data_out/autonomous_training.log`

**Trigger immediate training cycle:**
```bash
pkill -USR1 -f autonomous_training
```

## 📊 Monitor GPU Training

### Live GPU Monitoring (NVIDIA)

```bash
# Update every 1 second
nvidia-smi -l 1

# Detailed per-process view
nvidia-smi pmon -c 0

# Watch mode (refreshes)
watch -n 1 nvidia-smi
```

### Live GPU Monitoring (Apple)

```bash
# Monitor GPU usage
powermetrics -i 1 | grep -i gpu
```

### VS Code Dashboard

```bash
# Start in separate terminal
python dashboard/app.py

# Open: http://localhost:8765
# Shows: GPU utilization, training progress, metrics
```

## 🎯 Configuration Details

### GPU Settings (Already Configured ✅)

**File: `config/autonomous_training.yaml`**
```yaml
training:
  device: cuda           # ← Auto-detected (cuda/mps/cpu)
  mixed_precision: true  # FP16+FP32 for speed & memory
  gradient_accumulation_steps: 4  # Larger effective batch size
  max_gpu_memory_gb: 0   # Use all available GPU memory
  max_cpu_cores: 0       # Use all CPU cores for data loading
  workers: 20            # Data loading workers
  epochs_progression: [25, 50, 100, 200]  # Adaptive epochs
```

**File: `config/training/autotrain.yaml`**
- All 14 jobs have `device: cuda`
- Models auto-detect and use available GPUs

### Environment Variables (Optional Tuning)

```bash
# Recommended GPU optimizations
export CUDA_LAUNCH_BLOCKING=0          # Async CUDA operations (faster)
export CUDA_DEVICE_ORDER=PCI_BUS_ID    # Order GPUs by PCI ID
export CUDA_VISIBLE_DEVICES=0,1,2,3    # Select specific GPUs (optional)

# For Apple Metal
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0  # Use more GPU memory
```

## 📈 Performance Expectations

### Training Speed (on GPU)

**Phi-3.5-mini-instruct** (1B parameters):
- CPU: ~15-20 min per epoch
- GPU (RTX 4090): ~1-2 min per epoch
- **Speedup: 10-15x** 🚀

**Qwen2.5-3B** (3B parameters):
- CPU: ~45-60 min per epoch
- GPU (RTX A6000): ~3-5 min per epoch
- **Speedup: 10-15x** 🚀

### 14-Job Autotrain Timeline

| Hardware | Duration | Notes |
|----------|----------|-------|
| CPU only | 20-30 hours | Very slow, not recommended |
| 1x RTX 4090 | 2-3 hours | All jobs sequential |
| 2x RTX A6000 | 1-2 hours | Parallel execution |
| 4x RTX A6000 | 45-90 min | Max parallelization |
| Apple M3 Max | 3-4 hours | Good for development |

## ✅ Verification Checklist

- [ ] GPU PyTorch installed (`python scripts/gpu_config.py` shows GPU)
- [ ] Configs updated (`device: cuda` in autotrain.yaml)
- [ ] Training can run (`python scripts/training/autotrain.py --help` works)
- [ ] GPU detected by training (`nvidia-smi` shows CUDA processes during training)
- [ ] Monitor dashboard accessible (http://localhost:8765)

## 🔧 Troubleshooting

### GPU not detected

```bash
# Check PyTorch CUDA support
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Should output: CUDA: True

# If False, reinstall GPU PyTorch:
bash install_gpu_pytorch.sh
```

### Out of memory (OOM)

```bash
# In config/training/autotrain.yaml, reduce batch size:
batch_size: 8  # Try 4 or 2 if OOM

# OR enable gradient checkpointing (slower but less memory):
gradient_checkpointing: true
```

### Slow training (using CPU instead)

```bash
# Verify device is actually cuda
python scripts/gpu_config.py

# Check which device is being used during training:
tail -f data_out/autotrain/job_*.log | grep -i device
```

### Training crashes

```bash
# Check full error logs
tail -100 data_out/autotrain/job_1.log

# Try CPU-only mode temporarily to isolate GPU issues:
# In config/training/autotrain.yaml, change:
device: cpu  # Temporary debug

python scripts/training/autotrain.py
```

## 📚 Advanced: Custom Training

### Train specific model only

```bash
python scripts/training/autotrain.py --job phi35_comprehensive_full
```

### Quick test run (1 epoch)

```bash
python scripts/training/autotrain.py --epochs 1
```

### Grid search with hyperparameter tuning

```bash
python scripts/training/training_scheduler.py --grid-search
```

### Full pipeline (train → evaluate → deploy)

```bash
python scripts/training/train_and_promote.py --full --auto-promote
```

## 🎓 More Information

- **Training Docs**: [QUANTUM_TRAINING_QUICK_START.md](../QUANTUM_TRAINING_QUICK_START.md)
- **GPU Setup**: [GPU_SETUP.md](../GPU_SETUP.md)
- **Results & Analytics**: `python scripts/training_analytics.py`
- **Dashboard**: `python dashboard/app.py` (port 8765)

## 💾 Your GPU Setup Summary

```json
{
  "device": "cuda",
  "pytorch_version": "2.1.0+cu118",
  "cuda_available": true,
  "device_count": 2,
  "devices": [
    {
      "index": 0,
      "name": "NVIDIA RTX A6000",
      "memory_gb": 48.0
    },
    {
      "index": 1,
      "name": "NVIDIA RTX A6000",
      "memory_gb": 48.0
    }
  ]
}
```

**Total GPU Memory: 96 GB** ✅
**Can train: 2-3 models simultaneously!** 🚀

---

**Ready to train on GPU!** Start with:
```bash
python scripts/setup_gpu_training.py
python scripts/training/autotrain.py
```

Monitor with:
```bash
nvidia-smi -l 1
python dashboard/app.py  # http://localhost:8765
```

Questions? Check `data_out/gpu_info.json` for detected GPU details.
