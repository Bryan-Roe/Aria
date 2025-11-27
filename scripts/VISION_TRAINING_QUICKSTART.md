Vision Training Quickstart
=========================

This small script is intended for quick local exploration and experiments with visual models. It creates a tiny toy dataset of colored shapes and trains a tiny convolutional network so you can sanity-check your environment, GPU support, and the training flow.

Usage
-----

1. Generate a toy dataset & train for 1 epoch:

   python scripts/train_vision.py --dataset datasets/vision/toy_shapes --epochs 1 --batch-size 8

2. Dry-run to validate your environment (no training):

   python scripts/train_vision.py --dataset datasets/vision/toy_shapes --dry-run

Options
-------
- --dataset: Root path of a dataset with class subfolders. If missing the script generates a small toy dataset.
- --img-size: Resize input images (square) — default 64.
- --epochs: Number of epochs to train.
- --batch-size: Batch size.
- --out-dir: Where to save checkpoints & temporary files (default: data_out/vision_training)
- --dry-run: Don't run training; useful to validate configuration

Notes
-----
- The script intentionally avoids torchvision to make it lightweight and portable.
- For anything more than toy experiments use your standard training pipelines (e.g., torchvision, albumentations, larger models).
