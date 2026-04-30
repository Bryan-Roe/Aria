"""Evaluate a trained TinyConvNet vision checkpoint on a dataset.

Usage:
    python -m scripts.evaluation.evaluate_vision \\
        --checkpoint data_out/vision_training/vision_model_epoch005.pt \\
        --dataset /path/to/dataset \\
        --out-dir data_out/vision_eval
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
except ImportError as exc:
    raise ImportError("PyTorch required: pip install torch") from exc

# Re-use model and dataset from the training module
from scripts.training.train_vision import FolderDataset, TinyConvNet

# ---------------------------------------------------------------------------
# Core evaluation logic
# ---------------------------------------------------------------------------


def _load_checkpoint(checkpoint_path: Path, device: "torch.device"):
    """Load a TinyConvNet checkpoint and return (model, classes, img_size)."""
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)

    # Handle flat state-dict payload (older style)
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        classes = ckpt.get("classes", ["circle", "square"])
        img_size = ckpt.get("img_size", 64)
        num_classes = ckpt.get("num_classes", len(classes))
        in_channels = ckpt.get("in_channels", 3)
        model = TinyConvNet(in_channels=in_channels, num_classes=num_classes).to(device)
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        # Bare state-dict (legacy)
        model = TinyConvNet(in_channels=3, num_classes=2).to(device)
        model.load_state_dict(ckpt)
        classes = ["circle", "square"]
        img_size = 64

    model.eval()
    return model, classes, img_size


def evaluate(
    checkpoint_path: Path,
    dataset_path: Path,
    out_dir: Path,
    img_size: int = 64,
    batch_size: int = 32,
    show_examples: int = 0,
    device: Optional["torch.device"] = None,
) -> dict:
    """Run evaluation and write results.json; returns the results dict."""
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model, classes, ckpt_img_size = _load_checkpoint(checkpoint_path, device)
    # img_size may differ from ckpt_img_size; AdaptiveAvgPool handles any resolution
    ds = FolderDataset(dataset_path, img_size=img_size)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, drop_last=False)

    all_preds: list[int] = []
    all_labels: list[int] = []
    all_confs: list[float] = []

    with torch.no_grad():
        for imgs, labels in loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            probs = torch.softmax(logits, dim=1)
            preds = probs.argmax(dim=1).cpu().tolist()
            confs = probs.max(dim=1).values.cpu().tolist()
            lbls = labels.tolist() if hasattr(labels, "tolist") else list(labels)
            all_preds.extend(preds)
            all_labels.extend(lbls)
            all_confs.extend(confs)

    total = len(all_labels)
    correct = sum(p == l for p, l in zip(all_preds, all_labels))
    accuracy = correct / max(total, 1)

    # Per-class accuracy
    per_class: dict[str, dict] = {}
    for cls_idx, cls_name in enumerate(ds.classes):
        cls_total = sum(1 for l in all_labels if l == cls_idx)
        cls_correct = sum(
            1 for p, l in zip(all_preds, all_labels) if l == cls_idx and p == l
        )
        per_class[cls_name] = {
            "total": cls_total,
            "correct": cls_correct,
            "accuracy": cls_correct / max(cls_total, 1),
        }

    results = {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "mean_confidence": float(np.mean(all_confs)) if all_confs else 0.0,
        "checkpoint": str(checkpoint_path),
        "dataset": str(dataset_path),
        "classes": classes,
        "per_class": per_class,
    }

    if show_examples > 0:
        examples = []
        for i in range(min(show_examples, total)):
            examples.append(
                {
                    "index": i,
                    "predicted": (
                        ds.classes[all_preds[i]]
                        if all_preds[i] < len(ds.classes)
                        else str(all_preds[i])
                    ),
                    "actual": (
                        ds.classes[all_labels[i]]
                        if all_labels[i] < len(ds.classes)
                        else str(all_labels[i])
                    ),
                    "confidence": all_confs[i],
                }
            )
        results["examples"] = examples

    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(
        f"[evaluate_vision] accuracy={accuracy:.3f} ({correct}/{total}) → {results_path}"
    )
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def run_eval(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a TinyConvNet checkpoint")
    parser.add_argument(
        "--checkpoint", required=True, help="Path to .pt checkpoint file"
    )
    parser.add_argument(
        "--dataset", required=True, help="Path to dataset root directory"
    )
    parser.add_argument("--out-dir", default="data_out/vision_eval")
    parser.add_argument("--img-size", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--show-examples", type=int, default=0)
    parsed = parser.parse_args(args)

    out_dir = Path(parsed.out_dir)
    checkpoint_path = Path(parsed.checkpoint)
    dataset_path = Path(parsed.dataset)

    if not checkpoint_path.exists():
        print(
            f"[evaluate_vision] ERROR: checkpoint not found: {checkpoint_path}",
            file=sys.stderr,
        )
        return 1
    if not dataset_path.exists():
        print(
            f"[evaluate_vision] ERROR: dataset not found: {dataset_path}",
            file=sys.stderr,
        )
        return 1

    try:
        evaluate(
            checkpoint_path=checkpoint_path,
            dataset_path=dataset_path,
            out_dir=out_dir,
            img_size=parsed.img_size,
            batch_size=parsed.batch_size,
            show_examples=parsed.show_examples,
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[evaluate_vision] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run_eval())
