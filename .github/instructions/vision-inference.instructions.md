---
applyTo: "scripts/vision_inference.py"
---

# Vision Inference — Instruction Guide

## TinyConvNet Architecture

```python
class TinyConvNet(nn.Module):
    # Conv2d(3, 16) → ReLU → MaxPool2d
    # Conv2d(16, 32) → ReLU → MaxPool2d
    # AdaptiveAvgPool2d(4)
    # Linear(32*4*4, num_classes)
```

## Inference Pipeline

```python
vi = VisionInference()                      # Auto-loads latest checkpoint
result = vi.predict(pil_image)              # PIL Image input
result = vi.predict_base64(b64_string)      # Base64 string input
result = vi.predict_file(file_path)         # File path input
# Returns: {label: str, confidence: float, scores: Dict[str, float]}
```

## Preprocessing

- Resize to 64×64
- Normalize pixel values
- Convert to tensor shape (1, C, H, W)

## Checkpoint Management

Search order for `.pt` files:
1. `data_out/vision_training/`
2. `scripts/checkpoints/`
3. `checkpoints/`

Checkpoint format:
```python
{
    'model_state_dict': OrderedDict,
    'class_names': ['happy', 'sad', ...],
    'epoch': int,
    'accuracy': float
}
```

## Coding Conventions

- Always include `class_names` in checkpoints for portability
- Input resolution must match training resolution (64×64)
- Auto-detect GPU/CPU device at initialization
- New expression classes require retraining — update class_names list
- Use balanced datasets for training (equal samples per class)
