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
- --augment: Enable simple online data augmentation for training (flip/rotate/brightness/contrast/crop)
- --augment-policy: Augmentation policy: 'simple' (PIL fallback), 'strong', or 'torchvision' (uses torchvision.transforms when available)
- --seed: Random seed for reproducible splits and augmentation
- --val-split: Fraction to reserve for validation (default 0.2)
- --export-onnx: Optional path to export an ONNX snapshot of the trained model

Evaluation & visualization
------------------------

The training script will now optionally apply augmentations (see --augment and --augment-policy). When torchvision is available and you select the 'torchvision' policy the script will prefer torchvision transforms.

Use the evaluation helper to inspect a model checkpoint and create visual artifacts:

   python scripts/evaluate_vision.py --checkpoint data_out/vision_training/vision_model_epoch3.pt --dataset datasets/vision/toy_shapes --out-dir data_out/vision_eval --show-examples 8

This will write a results.json with accuracy, a confusion matrix image (when matplotlib/seaborn are installed), and annotated example images for quick inspection.

Avatar integration
------------------

If you have a folder of avatar assets you can run a quick inference pass to label assets and export features (for clustering / retrieval):

   python scripts/vision_avatar_integration.py --checkpoint data_out/vision_training/vision_model_epoch3.pt --assets-dir path/to/avatar_assets --out-json data_out/avatar_predictions.json --export-features

Notes
-----

For anything more than toy experiments use your standard training pipelines (e.g., torchvision, albumentations, larger models). The scripts here are intentionally compact to aid experimentation and provenance.
