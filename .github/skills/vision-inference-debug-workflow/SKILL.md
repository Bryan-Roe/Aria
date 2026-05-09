---
name: vision-inference-debug-workflow
description: "Debug vision inference failures, checkpoint loading issues, expression classification errors, and preprocessing mismatches in scripts/vision_inference.py using the TinyConvNet architecture. Use when expression classification returns wrong labels, confidence is unexpectedly low, checkpoints fail to load, input images produce errors, or a new emotion class needs to be added."
argument-hint: "Describe the symptom: wrong expression label, low confidence scores, checkpoint not found, base64 decode error, wrong input resolution, or need to add a new emotion class."
---

# Vision Inference Debug Workflow

## What This Skill Produces
- Root cause for checkpoint loading failures (search path, missing keys, class_names absent)
- Diagnosis of preprocessing mismatches (wrong input size, missing normalization)
- Verification that inference pipeline returns expected `{label, confidence, scores}` shape
- Guidance for adding new emotion classes (requires retraining)

## When to Use

Trigger phrases:
- "vision inference returns wrong expression"
- "TinyConvNet checkpoint not found"
- "confidence score always low"
- "base64 image inference fails"
- "expression classification incorrect"
- "checkpoint missing class_names"
- "model not loading from data_out"
- "add a new emotion class"
- "vision_inference predict returning unexpected label"
- "input resolution mismatch"
- "VisionInference auto-load failing"

## Procedure

### Step 1 — Verify checkpoint search paths
`VisionInference()` auto-loads the latest `.pt` checkpoint in this order:
```
1. data_out/vision_training/
2. scripts/checkpoints/
3. checkpoints/
```

```bash
# Check all three locations:
ls -lt data_out/vision_training/*.pt 2>/dev/null | head -5
ls -lt scripts/checkpoints/*.pt 2>/dev/null | head -5
ls -lt checkpoints/*.pt 2>/dev/null | head -5

# If empty: no checkpoint exists — model must be trained first
# Most recent .pt file by modification time is loaded
```

### Step 2 — Validate checkpoint format
```python
import torch

checkpoint = torch.load("data_out/vision_training/best_model.pt", map_location="cpu")
print(checkpoint.keys())
# Required keys:
#   model_state_dict  — OrderedDict of weights
#   class_names       — ['happy', 'sad', 'neutral', ...]  ← CRITICAL for label mapping
#   epoch             — int
#   accuracy          — float

# If class_names is missing: checkpoint was saved without it
# Labels will default to numeric indices — add class_names to training save step
```

### Step 3 — Confirm preprocessing matches training

All inputs are resized and normalized before inference:
```python
# Required preprocessing pipeline:
transform = transforms.Compose([
    transforms.Resize((64, 64)),    # ← MUST match training resolution
    transforms.ToTensor(),
    transforms.Normalize(...)       # ← MUST use same mean/std as training
])
# Input tensor shape: (1, C, H, W) = (1, 3, 64, 64)

# If resolution doesn't match: wrong AdaptiveAvgPool2d output → wrong Linear layer shape
# Fix: retrain model or use 64×64 inputs consistently
```

### Step 4 — Test each inference input method
```python
from scripts.vision_inference import VisionInference

vi = VisionInference()

# Option A — PIL Image:
from PIL import Image
img = Image.open("test.jpg")
result = vi.predict(img)

# Option B — Base64 string:
import base64
with open("test.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
result = vi.predict_base64(b64)

# Option C — File path:
result = vi.predict_file("test.jpg")

# Expected result shape:
# {"label": "happy", "confidence": 0.87, "scores": {"happy": 0.87, "sad": 0.08, "neutral": 0.05}}
```

### Step 5 — Review TinyConvNet architecture
```python
# Architecture (must match checkpoint exactly):
# Conv2d(3, 16, kernel_size=3)  → ReLU → MaxPool2d(2)
# Conv2d(16, 32, kernel_size=3) → ReLU → MaxPool2d(2)
# AdaptiveAvgPool2d(4)          → flattens to 32*4*4 = 512
# Linear(512, num_classes)

# If loading a checkpoint gives shape mismatch:
#   → Number of classes in checkpoint != current num_classes
#   → class_names list length must equal num_classes at training time
```

### Step 6 — Check GPU/CPU device handling
```python
# VisionInference auto-detects device at init:
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# If CUDA OOM error: force CPU
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
vi = VisionInference()

# If inference is slow on CPU: normal — TinyConvNet is lightweight, acceptable on CPU
```

### Step 7 — Adding a new emotion class
```
⚠ Adding a new class ALWAYS requires retraining — there is no hot-add path.

Steps:
1. Collect balanced training samples for new class (match existing class sample count)
2. Add class name to class_names list in training script
3. Retrain from scratch (or fine-tune last layer)
4. Save checkpoint with updated class_names
5. Replace checkpoint in data_out/vision_training/
6. VisionInference() will auto-load new checkpoint on next init
```

## Quality Checks
- [ ] Checkpoint found in one of the 3 search paths
- [ ] Checkpoint contains `class_names` key — not just numeric label indices
- [ ] Input images resized to 64×64 before passing to model
- [ ] Normalization parameters match those used during training
- [ ] `result` dict contains `label`, `confidence`, and `scores` keys
- [ ] New emotion classes added via retraining — not patched into existing checkpoint
- [ ] Balanced dataset used for training (equal samples per class)
- [ ] Tests run: `pytest tests/ -m "not slow and not azure" -k vision`
