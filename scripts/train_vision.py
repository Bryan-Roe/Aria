"""Small, self-contained vision training utility for quick experiments.

Usage examples:
  python scripts/train_vision.py --dataset datasets/vision/toy_shapes --epochs 3 --batch-size 8
  python scripts/train_vision.py --list-datasets

The script will generate a tiny toy dataset when the requested dataset doesn't exist.
It uses pure Pillow + PyTorch (no torchvision) so it remains lightweight for quick local tests.
"""
from __future__ import annotations

import argparse
import math
import random
import shutil
import sys
from pathlib import Path
from typing import Callable, List, Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

try:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, Dataset

    # Optional convenience transforms: prefer torchvision when available
    try:  # pragma: no cover - optional dependency
        import torchvision.transforms as T
        _HAS_TORCHVISION = True
    except Exception:
        T = None
        _HAS_TORCHVISION = False
except Exception as err:  # pragma: no cover - environment dependent
    print("Missing PyTorch -- please install it in your environment (pip install torch)\n", err)
    raise


def generate_toy_shapes_dataset(path: Path, classes=('circle', 'square'), samples_per_class=40, size=(64, 64)):
    """Create a small dataset of synthetic shapes saved as PNGs in class-labeled folders.

    The dataset layout is identical to torchvision.datasets.ImageFolder: root/class_x/*.png
    """
    path = Path(path)
    if path.exists():
        # if already present and non-empty, skip
        non_empty = any(p.is_dir() and any(p.iterdir())
                        for p in path.iterdir())
        if non_empty:
            return path
    # remove and recreate clean dataset
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

    def draw_shape(img: Image.Image, shape: str):
        draw = ImageDraw.Draw(img)
        w, h = img.size
        pad = int(min(w, h) * 0.12)
        bbox = [pad, pad, w - pad, h - pad]
        color = tuple(int(x) for x in np.random.randint(40, 220, size=3))
        if shape == 'circle':
            draw.ellipse(bbox, fill=tuple(color))
        elif shape == 'square':
            draw.rectangle(bbox, fill=tuple(color))
        else:
            draw.polygon([(w//2, pad), (w-pad, h-pad),
                         (pad, h-pad)], fill=tuple(color))

    for cl in classes:
        cl_dir = path / cl
        cl_dir.mkdir(parents=True, exist_ok=True)
        for i in range(samples_per_class):
            img = Image.new('RGB', size, color=(255, 255, 255))
            # add some random backgrounds / noise
            if random.random() < 0.15:
                bg = tuple(int(x) for x in np.random.randint(200, 255, size=3))
                Image.new('RGB', size, color=bg).paste(img)
            draw_shape(img, cl)
            # jitter rotation/resize
            if random.random() < 0.5:
                img = img.rotate(random.uniform(-10, 10),
                                 resample=Image.BILINEAR, expand=False)
            p = cl_dir / f"{cl}_{i:03d}.png"
            img.save(p, format='PNG')

    return path


class SimpleImageFolder(Dataset):
    """Minimal dataset loader for a folder of class subdirectories containing images.

    Accepts PNG/JPG images and returns normalized float tensors in CHW order.
    """

    def __init__(self, root: Path, img_size=(64, 64), transform: Optional[Callable] = None):
        self.root = Path(root)
        self.img_size = img_size
        # transform: callable(PIL.Image) -> tensor (C,H,W)
        self.transform = transform
        classes = [p.name for p in sorted(self.root.iterdir()) if p.is_dir()]
        self.classes = classes
        self.class_to_idx = {c: i for i, c in enumerate(classes)}
        self.samples: List[Tuple[Path, int]] = []
        for c in classes:
            folder = self.root / c
            for f in folder.iterdir():
                if f.suffix.lower() in ('.png', '.jpg', '.jpeg'):
                    self.samples.append((f, self.class_to_idx[c]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        p, lab = self.samples[idx]
        img = Image.open(p).convert('RGB')
        # apply transforms if present (these should return tensors in CHW)
        if self.transform is not None:
            return self.transform(img), int(lab)

        img = img.resize(self.img_size, Image.BILINEAR)
        arr = np.asarray(img, dtype=np.float32) / 255.0
        # CHW
        tensor = torch.from_numpy(arr).permute(2, 0, 1).contiguous()
        return tensor, int(lab)


class TinyConvNet(nn.Module):
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


def train_one_epoch(model, loader, opt, device):
    model.train()
    total = 0
    correct = 0
    loss_sum = 0.0
    criterion = nn.CrossEntropyLoss()
    for xb, yb in loader:
        xb = xb.to(device)
        yb = yb.to(device)
        logits = model(xb)
        loss = criterion(logits, yb)
        opt.zero_grad()
        loss.backward()
        opt.step()
        loss_sum += float(loss.item())
        preds = logits.argmax(dim=1)
        correct += int((preds == yb).sum())
        total += xb.shape[0]
    return loss_sum / max(1, len(loader)), correct / max(1, total)


def eval_one_epoch(model, loader, device):
    model.eval()
    total = 0
    correct = 0
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)
            logits = model(xb)
            preds = logits.argmax(dim=1)
            correct += int((preds == yb).sum())
            total += xb.shape[0]
    return correct / max(1, total)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', type=str, default='datasets/vision/toy_shapes',
                   help='dataset root (class subfolders)')
    p.add_argument('--img-size', type=int, default=64,
                   help='image size (square)')
    p.add_argument('--augment', action='store_true',
                   help='Apply online data augmentation for training')
    p.add_argument('--augment-policy', type=str, default='simple', choices=(
        'simple', 'strong', 'torchvision'), help='Augmentation policy to use')
    p.add_argument('--seed', type=int, default=42,
                   help='random seed for reproducible splits and augmentation')
    p.add_argument('--val-split', type=float, default=0.2,
                   help='Fraction of dataset to reserve for validation (overrides default 80/20)')
    p.add_argument('--export-onnx', type=str, default='',
                   help='Optional path to export ONNX snapshot of the trained model')
    p.add_argument('--epochs', type=int, default=3)
    p.add_argument('--batch-size', type=int, default=8)
    p.add_argument('--lr', type=float, default=1e-3)
    p.add_argument('--out-dir', type=str, default='data_out/vision_training')
    p.add_argument('--samples-per-class', type=int, default=40)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args(argv)

    dataset = Path(args.dataset)
    if not dataset.exists() or not any(dataset.iterdir()):
        print('Dataset not found or empty; generating toy_shapes at', dataset)
        generate_toy_shapes_dataset(
            dataset, samples_per_class=args.samples_per_class, size=(args.img_size, args.img_size))

    # create train/test split
    classes = [d.name for d in sorted(dataset.iterdir()) if d.is_dir()]
    if not classes:
        print('No class subfolders found in', dataset)
        return 2

    all_samples = []
    for c in classes:
        for f in (dataset / c).iterdir():
            if f.suffix.lower() in ('.png', '.jpg', '.jpeg'):
                all_samples.append((f, c))

    random.seed(args.seed)
    random.shuffle(all_samples)
    n = len(all_samples)
    split = max(1, int(n * (1.0 - args.val_split)))
    train_samples = all_samples[:split]
    test_samples = all_samples[split:]

    # Build small folder-views for training so the dataset class remains simple
    tmp_root = Path(args.out_dir) / 'tmp_dataset'
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)
    for pth, cls in train_samples:
        target = tmp_root / cls
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy(pth, target / pth.name)
    # test dir
    tmp_test = tmp_root / '__test'
    for pth, cls in test_samples:
        target = tmp_test / cls
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy(pth, target / pth.name)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Using device:', device)

    # build transforms
    def make_transform(img_size, augment=False, policy='simple'):
        # prefer torchvision transforms when the policy explicitly requests it and torchvision is available
        if policy == 'torchvision' and _HAS_TORCHVISION:
            tr = []
            if augment:
                tr.extend([
                    T.RandomResizedCrop(img_size, scale=(0.8, 1.0)),
                    T.RandomHorizontalFlip(),
                    T.ColorJitter(brightness=0.2, contrast=0.2,
                                  saturation=0.2, hue=0.05),
                ])
            tr.extend([T.Resize(img_size), T.ToTensor()])
            return T.Compose(tr)

        # fallback: basic PIL-based augmentation
        def transform_fn(img: Image.Image):
            if augment:
                # random jitter (flip)
                if random.random() < 0.5:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                # rotation
                if random.random() < 0.35:
                    ang = random.uniform(-15, 15)
                    img = img.rotate(ang, resample=Image.BILINEAR)
                # brightness/contrast
                if random.random() < 0.5:
                    b = random.uniform(0.8, 1.2)
                    img = ImageEnhance.Brightness(img).enhance(b)
                if random.random() < 0.5:
                    c = random.uniform(0.85, 1.15)
                    img = ImageEnhance.Contrast(img).enhance(c)
                # small random crop + resize
                if random.random() < 0.3:
                    w, h = img.size
                    crop_w = int(w * random.uniform(0.8, 1.0))
                    crop_h = int(h * random.uniform(0.8, 1.0))
                    left = random.randint(0, max(0, w - crop_w))
                    top = random.randint(0, max(0, h - crop_h))
                    img = img.crop((left, top, left + crop_w, top + crop_h))
            img = img.resize((img_size, img_size), Image.BILINEAR)
            arr = np.asarray(img, dtype=np.float32) / 255.0
            return torch.from_numpy(arr).permute(2, 0, 1).contiguous()

        return transform_fn

    train_transform = make_transform(
        args.img_size, augment=args.augment, policy=args.augment_policy)
    test_transform = make_transform(
        args.img_size, augment=False, policy=args.augment_policy)

    train_ds = SimpleImageFolder(tmp_root, img_size=(
        args.img_size, args.img_size), transform=train_transform)
    test_ds = SimpleImageFolder(tmp_test, img_size=(
        args.img_size, args.img_size), transform=test_transform)

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size)

    num_classes = len(train_ds.classes)
    model = TinyConvNet(num_classes=num_classes).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    if args.dry_run:
        print('Dry run: ready to train model with', len(train_ds),
              'train samples and', len(test_ds), 'test samples')
        return 0

    epochs = args.epochs
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for e in range(epochs):
        loss, acc = train_one_epoch(model, train_loader, opt, device)
        val_acc = eval_one_epoch(model, test_loader, device)
        print(
            f"Epoch {e+1}/{epochs}  loss={loss:.4f}  train_acc={acc:.3f}  val_acc={val_acc:.3f}")

    ck = out_dir / f"vision_model_epoch{epochs}.pt"
    torch.save({'model': model.state_dict(), 'classes': train_ds.classes}, ck)
    print('Saved checkpoint to', ck)

    # optionally export a simple ONNX snapshot for interop
    if args.export_onnx:
        try:
            dummy = torch.randn(1, 3, args.img_size,
                                args.img_size, device=device)
            onnx_path = Path(args.export_onnx)
            model.cpu()
            torch.onnx.export(model, dummy, str(onnx_path), opset_version=12)
            print('Exported ONNX model to', onnx_path)
        except Exception as e:  # pragma: no cover - environment dependent
            print('Warning: failed to export ONNX model:', e)
    # cleanup temp dataset
    try:
        shutil.rmtree(tmp_root)
    except Exception:
        pass
    return 0

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
