"""Vision model training script — trains TinyConvNet on a folder dataset.

Dataset layout expected:
    <root>/
        <class_name>/
            img_0001.png
            ...

Usage:
    python -m scripts.training.train_vision \\
        --dataset /path/to/dataset \\
        --epochs 10 \\
        --batch-size 32 \\
        --out-dir data_out/vision_training
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
except ImportError as exc:
    raise ImportError("PyTorch required: pip install torch") from exc


# ---------------------------------------------------------------------------
# Model definition — must stay in sync with scripts/vision_inference.py
# ---------------------------------------------------------------------------


class TinyConvNet(nn.Module):
    """Minimal CNN for expression/shape classification."""

    def __init__(self, in_channels: int = 3, num_classes: int = 2) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, 16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(32, num_classes),
        )

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        return self.net(x)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class FolderDataset(Dataset):
    """Simple folder-based image dataset."""

    def __init__(self, root: Path, img_size: int = 64) -> None:
        root = Path(root)
        self.img_size = img_size
        self.classes = sorted(d.name for d in root.iterdir() if d.is_dir())
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.samples: list[tuple[Path, int]] = []
        for cls in self.classes:
            for f in (root / cls).iterdir():
                if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    self.samples.append((f, self.class_to_idx[cls]))
        random.shuffle(self.samples)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        img_arr = _load_image(path, self.img_size)
        return torch.tensor(img_arr, dtype=torch.float32), label


# ---------------------------------------------------------------------------
# Image I/O helpers
# ---------------------------------------------------------------------------


def _load_image(path: Path, size: int) -> np.ndarray:
    """Load image → float32 CHW array normalised to [0, 1]."""
    from PIL import Image as _Image  # type: ignore[import]

    img = _Image.open(path).convert("RGB").resize((size, size))
    arr = np.array(img, dtype=np.float32) / 255.0  # HWC
    return np.transpose(arr, (2, 0, 1))  # CHW


def _save_png(arr: np.ndarray, path: Path) -> None:
    """Save HxWxC uint8 array as PNG using Pillow."""
    from PIL import Image as _Image  # type: ignore[import]

    _Image.fromarray(arr).save(path)


# ---------------------------------------------------------------------------
# Synthetic dataset generator
# ---------------------------------------------------------------------------


def generate_toy_shapes_dataset(
    root: Path,
    samples_per_class: int = 20,
    size: tuple[int, int] = (64, 64),
) -> None:
    """Create a synthetic circle/square dataset for testing."""
    root = Path(root)
    h, w = size
    rng = np.random.default_rng(42)

    for cls in ("circle", "square"):
        (root / cls).mkdir(parents=True, exist_ok=True)

    for i in range(samples_per_class):
        # --- Circle ---
        img = np.zeros((h, w, 3), dtype=np.uint8)
        cy, cx = h // 2, w // 2
        radius = min(h, w) // 4
        ys, xs = np.ogrid[:h, :w]
        mask = (ys - cy) ** 2 + (xs - cx) ** 2 <= radius**2
        img[mask] = 255
        noise = rng.integers(0, 30, img.shape, dtype=np.uint8)
        img = np.clip(img.astype(np.int32) + noise.astype(np.int32), 0, 255).astype(
            np.uint8
        )
        _save_png(img, root / "circle" / f"img_{i:04d}.png")

        # --- Square ---
        img = np.zeros((h, w, 3), dtype=np.uint8)
        margin = max(2, min(h, w) // 4)
        img[margin : h - margin, margin : w - margin] = 255
        noise = rng.integers(0, 30, img.shape, dtype=np.uint8)
        img = np.clip(img.astype(np.int32) + noise.astype(np.int32), 0, 255).astype(
            np.uint8
        )
        _save_png(img, root / "square" / f"img_{i:04d}.png")


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------


def _train_epoch(
    model: TinyConvNet,
    loader: DataLoader,
    optimizer: "torch.optim.Optimizer",
    criterion: "nn.Module",
    device: "torch.device",
) -> tuple[float, float]:
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    for imgs, labels in loader:
        imgs = imgs.to(device)
        labels = (
            torch.tensor(labels, dtype=torch.long, device=device)
            if not isinstance(labels, torch.Tensor)
            else labels.to(device)
        )
        optimizer.zero_grad()
        logits = model(imgs)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(labels)
        preds = logits.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += len(labels)
    n = max(total, 1)
    return total_loss / n, correct / n


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Train TinyConvNet vision classifier")
    parser.add_argument(
        "--dataset", required=True, help="Path to dataset root directory"
    )
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--out-dir", default="data_out/vision_training")
    parser.add_argument("--img-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate only, skip training"
    )
    parsed = parser.parse_args(args)

    out_dir = Path(parsed.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = Path(parsed.dataset)
    if not dataset_path.exists():
        print(
            f"[train_vision] ERROR: dataset not found: {dataset_path}", file=sys.stderr
        )
        return 1

    ds = FolderDataset(dataset_path, img_size=parsed.img_size)
    if len(ds) == 0:
        print("[train_vision] ERROR: no images found in dataset", file=sys.stderr)
        return 1

    if parsed.dry_run:
        print(
            f"[train_vision] dry-run OK — {len(ds)} images, "
            f"{len(ds.classes)} classes: {ds.classes}"
        )
        return 0

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    loader = DataLoader(ds, batch_size=parsed.batch_size, shuffle=True, drop_last=False)
    model = TinyConvNet(in_channels=3, num_classes=len(ds.classes)).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=parsed.lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(1, parsed.epochs + 1):
        loss, acc = _train_epoch(model, loader, optimizer, criterion, device)
        print(
            f"[train_vision] epoch {epoch}/{parsed.epochs}  loss={loss:.4f}  acc={acc:.3f}"
        )
        ckpt_path = out_dir / f"vision_model_epoch{epoch:03d}.pt"
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "classes": ds.classes,
                "num_classes": len(ds.classes),
                "in_channels": 3,
                "img_size": parsed.img_size,
                "loss": loss,
                "accuracy": acc,
            },
            ckpt_path,
        )
        print(f"[train_vision] checkpoint → {ckpt_path}")

    print(f"[train_vision] training complete ({parsed.epochs} epochs).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
