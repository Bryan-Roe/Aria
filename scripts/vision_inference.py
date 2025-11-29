"""Vision inference utilities for expression/emotion classification.

This module provides model loading, preprocessing, and inference functions
that can be used by the Azure Functions endpoint, CLI tools, or other consumers.

Usage:
    from scripts.vision_inference import VisionInference
    
    # Initialize (loads latest checkpoint by default)
    vi = VisionInference()
    
    # Infer from PIL Image
    result = vi.predict(pil_image)
    # {'label': 'happy', 'confidence': 0.92, 'scores': {'happy': 0.92, 'sad': 0.05, ...}}
    
    # Infer from base64
    result = vi.predict_base64(base64_str)
    
    # Infer from file path
    result = vi.predict_file('path/to/image.jpg')
"""
from __future__ import annotations

import base64
import io
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

try:
    import torch
    from torch import nn
except ImportError as err:
    raise ImportError("PyTorch is required for vision inference. Install with: pip install torch") from err


# Default checkpoint locations (prioritize latest training output)
DEFAULT_CHECKPOINT_DIRS = [
    'data_out/vision_training',
    'scripts/checkpoints',
    'checkpoints',
]


class TinyConvNet(nn.Module):
    """Minimal CNN architecture matching train_vision.py.
    
    This must stay in sync with the training script's model definition.
    """
    def __init__(self, in_channels=3, num_classes=2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, 16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        return self.net(x)


class VisionInference:
    """High-level interface for vision model inference."""
    
    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        device: Optional[str] = None,
        img_size: int = 64,
    ):
        """Initialize vision inference.
        
        Args:
            checkpoint_path: Path to .pt checkpoint. If None, searches default locations.
            device: 'cpu', 'cuda', or None (auto-detect).
            img_size: Input image size (square). Default 64x64.
        """
        self.img_size = img_size
        
        # Auto-detect device
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = torch.device(device)
        
        # Find checkpoint
        if checkpoint_path is None:
            checkpoint_path = self._find_latest_checkpoint()
        
        if checkpoint_path is None:
            raise FileNotFoundError(
                "No checkpoint found. Train a model first using scripts/train_vision.py"
            )
        
        self.checkpoint_path = Path(checkpoint_path)
        logging.info(f"Loading vision model from {self.checkpoint_path}")
        
        # Load checkpoint
        ckpt = torch.load(self.checkpoint_path, map_location=self.device, weights_only=True)
        self.classes = ckpt.get('classes', ['class_0', 'class_1'])
        
        # Initialize model
        self.model = TinyConvNet(num_classes=len(self.classes)).to(self.device)
        self.model.load_state_dict(ckpt['model'])
        self.model.eval()
        
        logging.info(f"Model loaded successfully. Classes: {self.classes}")
    
    def _find_latest_checkpoint(self) -> Optional[Path]:
        """Search default locations for the most recent checkpoint."""
        repo_root = Path(__file__).resolve().parent.parent
        
        candidates = []
        for dir_rel in DEFAULT_CHECKPOINT_DIRS:
            dir_path = repo_root / dir_rel
            if dir_path.exists():
                for ckpt in dir_path.glob('*.pt'):
                    candidates.append(ckpt)
        
        if not candidates:
            return None
        
        # Sort by modification time, newest first
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0]
    
    def preprocess(self, img: Image.Image) -> torch.Tensor:
        """Convert PIL Image to normalized tensor (1, C, H, W)."""
        # Ensure RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to expected input size
        img = img.resize((self.img_size, self.img_size), Image.BILINEAR)
        
        # Convert to numpy array and normalize to [0, 1]
        arr = np.asarray(img, dtype=np.float32) / 255.0
        
        # Convert to tensor (C, H, W) and add batch dimension
        tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
        
        return tensor.to(self.device)
    
    def predict(self, img: Image.Image) -> Dict[str, Union[str, float, Dict[str, float]]]:
        """Run inference on a PIL Image.
        
        Args:
            img: PIL Image object
        
        Returns:
            Dictionary with:
                - label: predicted class name
                - confidence: confidence score for predicted class (0-1)
                - scores: dict mapping all class names to their scores
        """
        tensor = self.preprocess(img)
        
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()
        
        # Get top prediction
        pred_idx = int(np.argmax(probs))
        pred_label = self.classes[pred_idx]
        pred_conf = float(probs[pred_idx])
        
        # Build scores dict
        scores = {self.classes[i]: float(probs[i]) for i in range(len(self.classes))}
        
        return {
            'label': pred_label,
            'confidence': pred_conf,
            'scores': scores,
        }
    
    def predict_base64(self, b64_str: str) -> Dict[str, Union[str, float, Dict[str, float]]]:
        """Run inference on a base64-encoded image.
        
        Args:
            b64_str: Base64-encoded image string (PNG, JPG, etc.)
        
        Returns:
            Same as predict()
        """
        # Decode base64 to bytes
        img_bytes = base64.b64decode(b64_str)
        
        # Open as PIL Image
        img = Image.open(io.BytesIO(img_bytes))
        
        return self.predict(img)
    
    def predict_file(self, file_path: str) -> Dict[str, Union[str, float, Dict[str, float]]]:
        """Run inference on an image file.
        
        Args:
            file_path: Path to image file
        
        Returns:
            Same as predict()
        """
        img = Image.open(file_path)
        return self.predict(img)
    
    def predict_batch(self, images: List[Image.Image]) -> List[Dict[str, Union[str, float, Dict[str, float]]]]:
        """Run inference on a batch of PIL Images.
        
        Args:
            images: List of PIL Image objects
        
        Returns:
            List of prediction dictionaries (one per image)
        """
        # Stack preprocessed images into batch
        tensors = [self.preprocess(img) for img in images]
        batch = torch.cat(tensors, dim=0)
        
        with torch.no_grad():
            logits = self.model(batch)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        
        # Build results
        results = []
        for i in range(len(images)):
            pred_idx = int(np.argmax(probs[i]))
            pred_label = self.classes[pred_idx]
            pred_conf = float(probs[i][pred_idx])
            scores = {self.classes[j]: float(probs[i][j]) for j in range(len(self.classes))}
            
            results.append({
                'label': pred_label,
                'confidence': pred_conf,
                'scores': scores,
            })
        
        return results
    
    def get_model_info(self) -> Dict[str, Union[str, List[str], int]]:
        """Get metadata about the loaded model.
        
        Returns:
            Dictionary with checkpoint path, classes, device, etc.
        """
        return {
            'checkpoint_path': str(self.checkpoint_path),
            'classes': self.classes,
            'num_classes': len(self.classes),
            'device': str(self.device),
            'img_size': self.img_size,
        }


def main():
    """CLI tool for testing vision inference."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Vision inference CLI')
    parser.add_argument('image', type=str, help='Path to image file')
    parser.add_argument('--checkpoint', type=str, help='Path to checkpoint (optional)')
    parser.add_argument('--device', type=str, choices=['cpu', 'cuda'], help='Device (auto-detect if not specified)')
    parser.add_argument('--img-size', type=int, default=64, help='Input image size')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Initialize inference
    vi = VisionInference(
        checkpoint_path=args.checkpoint,
        device=args.device,
        img_size=args.img_size,
    )
    
    # Run prediction
    result = vi.predict_file(args.image)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Prediction: {result['label']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print("\nAll scores:")
        for label, score in result['scores'].items():
            print(f"  {label}: {score:.4f}")


if __name__ == '__main__':
    main()
