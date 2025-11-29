"""Evaluate a trained vision model and produce visualizations.

Produces a JSON summary and (optionally) a confusion matrix image and a folder of example predictions.

Usage:
  python scripts/evaluate_vision.py --checkpoint data_out/vision_training/vision_model_epoch1.pt --dataset datasets/vision/toy_shapes --out-dir data_out/vision_eval --show-examples 8

The script will work without matplotlib/sklearn (it will compute metrics and save JSON) but will produce plots when those packages are available.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import torch
except Exception as e:  # pragma: no cover - tests will skip if no torch
    print('PyTorch is required for evaluation:', e)
    raise

from PIL import Image, ImageDraw, ImageFont

try:
    import numpy as np
except Exception:
    np = None

try:
    import sklearn.metrics as skm
    _HAS_SKLEARN = True
except Exception:
    skm = None
    _HAS_SKLEARN = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    _HAS_PLOTTING = True
except Exception:
    plt = None
    sns = None
    _HAS_PLOTTING = False

from scripts.train_vision import SimpleImageFolder, TinyConvNet


def load_checkpoint(ck_path: Path):
    ck = torch.load(str(ck_path), map_location='cpu', weights_only=True)
    model_state = ck.get('model') or ck
    classes = ck.get('classes') or ck.get('class_names') or []
    return model_state, classes


def infer(model, loader, device):
    model.eval()
    preds = []
    gts = []
    paths = []
    with torch.no_grad():
        for batch, _labels in loader:
            # when using custom transform the dataset may return PIL images (predict mode)
            if isinstance(batch, list) or hasattr(batch, 'dtype') is False:
                # assume dataset yields (tensor, label) in which case loader returns contiguous tensors
                # fallback: attempt to convert non-tensor entries
                pass
            xb = batch.to(device)
            logits = model(xb)
            ps = logits.argmax(dim=1).cpu().tolist()
            preds.extend(ps)
            gts.extend(_labels.tolist())
        # attempt to retrieve file paths from dataset
    return preds, gts


def run_eval(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', type=str, required=True)
    ap.add_argument('--dataset', type=str, required=True)
    ap.add_argument('--img-size', type=int, default=64)
    ap.add_argument('--out-dir', type=str, default='data_out/vision_eval')
    ap.add_argument('--batch-size', type=int, default=16)
    ap.add_argument('--show-examples', type=int, default=8, help='Number of example images to save (random sample)')
    args = ap.parse_args(argv)

    ck_path = Path(args.checkpoint)
    if not ck_path.exists():
        print('Checkpoint not found:', ck_path)
        return 2

    model_state, classes = load_checkpoint(ck_path)
    if not classes:
        print('Checkpoint did not include class names; aborting')
        return 3

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = TinyConvNet(num_classes=len(classes)).to(device)
    model.load_state_dict(model_state)

    ds = Path(args.dataset)
    if not ds.exists():
        print('Dataset path does not exist:', ds)
        return 4

    # Use the simple loader without augmentation
    from scripts.train_vision import SimpleImageFolder

    loader_ds = SimpleImageFolder(ds, img_size=(args.img_size, args.img_size))
    loader = torch.utils.data.DataLoader(loader_ds, batch_size=args.batch_size)

    # run inference
    preds, gts = [], []
    paths = [str(p[0]) for p in loader_ds.samples]
    model.eval()
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device)
            out = model(xb)
            ps = out.argmax(dim=1).cpu().tolist()
            preds.extend(ps)
            gts.extend(yb.tolist())

    # compute metrics
    total = len(preds)
    correct = sum(1 for p, g in zip(preds, gts) if p == g)
    acc = correct / total if total else 0.0

    results: Dict = {
        'checkpoint': str(ck_path),
        'dataset': str(ds),
        'num_samples': total,
        'accuracy': float(acc),
        'classes': list(classes),
    }

    # confusion matrix
    if _HAS_SKLEARN:
        cm = skm.confusion_matrix(gts, preds, labels=list(range(len(classes))))
        results['confusion_matrix'] = cm.tolist()
        results['classification_report'] = skm.classification_report(gts, preds, target_names=classes, output_dict=True)
    else:
        # simple confusion matrix fallback
        k = len(classes)
        cm = [[0] * k for _ in range(k)]
        for g, p in zip(gts, preds):
            cm[g][p] += 1
        results['confusion_matrix'] = cm

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # save results
    (out_dir / 'results.json').write_text(json.dumps(results, indent=2))

    # plotting
    if _HAS_PLOTTING and _HAS_SKLEARN:
        try:
            plt.figure(figsize=(max(6, len(classes) * 0.6), max(4, len(classes) * 0.35)))
            sns.heatmap(skm.confusion_matrix(gts, preds), annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
            plt.xlabel('Predicted')
            plt.ylabel('Actual')
            plt.title(f'Confusion matrix (acc={acc:.3f})')
            plt.tight_layout()
            plt_path = out_dir / 'confusion_matrix.png'
            plt.savefig(str(plt_path))
            plt.close()
            print('Saved confusion matrix to', plt_path)
        except Exception as e:
            print('Warning: failed to plot confusion matrix (matplotlib/seaborn issue):', e)

    # Save example predictions (random sample)
    sample_n = min(args.show_examples, total)
    if sample_n > 0:
        idxs = random.sample(range(total), sample_n)
        samples_dir = out_dir / 'examples'
        samples_dir.mkdir(exist_ok=True)
        # load a small pillow font if available
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        for i, idx in enumerate(idxs):
            pth = paths[idx]
            gt = classes[gts[idx]]
            pred = classes[preds[idx]]
            try:
                im = Image.open(pth).convert('RGB')
            except Exception:
                continue
            draw = ImageDraw.Draw(im)
            txt = f'GT: {gt}  P: {pred}'
            draw.rectangle([(0, 0), (im.width, 18)], fill=(0, 0, 0, 120))
            draw.text((4, 1), txt, fill=(255, 255, 255), font=font)
            outp = samples_dir / f'example_{i:02d}_{Path(pth).name}'
            im.save(outp)

    print('Evaluation summary: samples=%d  accuracy=%.4f' % (total, acc))
    print('Results written to', out_dir)

    return 0


if __name__ == '__main__':
    raise SystemExit(run_eval())
