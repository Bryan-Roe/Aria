"""Vision avatar integration — run TinyConvNet inference over a directory of images.

Usage:
    python -m scripts.inference.vision_avatar_integration \\
        --checkpoint data_out/vision_training/vision_model_epoch005.pt \\
        --images /path/to/images \\
        --output preds.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
except ImportError as exc:
    raise ImportError("PyTorch required: pip install torch") from exc

from scripts.training.train_vision import TinyConvNet, _load_image

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


class _ImageFileDataset(Dataset):
    """Dataset that loads all images found recursively under a directory."""

    def __init__(self, root: Path, img_size: int = 64) -> None:
        self.img_size = img_size
        self.paths: list[Path] = [
            p for p in sorted(root.rglob("*")) if p.suffix.lower() in _IMAGE_EXTS
        ]

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, idx: int):
        arr = _load_image(self.paths[idx], self.img_size)
        return torch.tensor(arr, dtype=torch.float32), str(self.paths[idx])


def _load_checkpoint(checkpoint_path: Path, device: "torch.device"):
    """Return (model, classes)."""
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        classes = ckpt.get("classes", ["circle", "square"])
        num_classes = ckpt.get("num_classes", len(classes))
        in_channels = ckpt.get("in_channels", 3)
        img_size = ckpt.get("img_size", 64)
        model = TinyConvNet(in_channels=in_channels, num_classes=num_classes).to(device)
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        model = TinyConvNet(in_channels=3, num_classes=2).to(device)
        model.load_state_dict(ckpt)
        classes = ["circle", "square"]
        img_size = 64
    model.eval()
    return model, classes, img_size


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_inference(
    checkpoint: Path,
    images_dir: Path,
    output_json: Path,
    img_size: int = 64,
    batch_size: int = 32,
    save_annotated: bool = False,
    export_features: bool = False,
) -> Dict[str, dict]:
    """Run inference on all images under *images_dir*.

    Returns a dict keyed by image path string; each value is a dict with at
    least ``predicted_label`` and ``confidence``.
    """
    checkpoint = Path(checkpoint)
    images_dir = Path(images_dir)
    output_json = Path(output_json)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, classes, ckpt_img_size = _load_checkpoint(checkpoint, device)

    ds = _ImageFileDataset(images_dir, img_size=img_size)
    if len(ds) == 0:
        print(
            f"[avatar_integration] WARNING: no images found under {images_dir}",
            file=sys.stderr,
        )
        output_json.parent.mkdir(parents=True, exist_ok=True)
        results: dict[str, dict] = {}
        with open(output_json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        return results

    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, drop_last=False)
    results = {}

    feature_hook_output: list[torch.Tensor] = []

    if export_features:
        # Hook the penultimate layer (Flatten output) to capture embeddings
        def _hook(module, inp, out):  # noqa: ARG001
            feature_hook_output.append(out.detach().cpu())

        # The Flatten layer is at index 6 in TinyConvNet.net
        _handle = model.net[6].register_forward_hook(_hook)

    with torch.no_grad():
        for imgs, paths in loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            probs = torch.softmax(logits, dim=1)
            preds = probs.argmax(dim=1).cpu().tolist()
            confs = probs.max(dim=1).values.cpu().tolist()
            all_scores = probs.cpu().tolist()

            for path_str, pred_idx, conf, scores in zip(
                paths, preds, confs, all_scores
            ):
                entry: dict = {
                    "predicted_label": (
                        classes[pred_idx] if pred_idx < len(classes) else str(pred_idx)
                    ),
                    "predicted_index": pred_idx,
                    "confidence": conf,
                    "scores": {
                        classes[i]: float(s)
                        for i, s in enumerate(scores)
                        if i < len(classes)
                    },
                }
                results[path_str] = entry

    if export_features and feature_hook_output:
        model.net[6]._forward_hooks.clear()  # type: ignore[attr-defined]
        all_feats = torch.cat(feature_hook_output, dim=0)
        paths_list = list(results.keys())
        for i, path_str in enumerate(paths_list):
            if i < all_feats.shape[0]:
                results[path_str]["features"] = all_feats[i].tolist()

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"[avatar_integration] {len(results)} images → {output_json}")
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(args=None) -> int:
    parser = argparse.ArgumentParser(
        description="Run vision model inference on an image directory"
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--images", required=True, help="Directory to scan for images")
    parser.add_argument("--output", default="data_out/avatar_preds.json")
    parser.add_argument("--img-size", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--save-annotated", action="store_true")
    parser.add_argument("--export-features", action="store_true")
    parsed = parser.parse_args(args)

    run_inference(
        checkpoint=Path(parsed.checkpoint),
        images_dir=Path(parsed.images),
        output_json=Path(parsed.output),
        img_size=parsed.img_size,
        batch_size=parsed.batch_size,
        save_annotated=parsed.save_annotated,
        export_features=parsed.export_features,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
