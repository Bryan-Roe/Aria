import importlib
import sys
from pathlib import Path

import pytest


# Skip entire module if torch/numpy unavailable (required by train_vision)
try:
    import torch  # noqa: F401
    import numpy  # noqa: F401
except ImportError:
    pytest.skip("torch or numpy not available", allow_module_level=True)

train = importlib.import_module('scripts.train_vision')
avatar = importlib.import_module('scripts.vision_avatar_integration')


def test_avatar_inference_small(tmp_path: Path):
    try:
        import torch  # noqa: F401
    except Exception:
        pytest.skip('PyTorch not available')

    ds = tmp_path / 'vision_ds'
    out = tmp_path / 'out'
    train.generate_toy_shapes_dataset(ds, samples_per_class=4, size=(32, 32))

    rc = train.main(['--dataset', str(ds), '--epochs', '1', '--batch-size', '2', '--out-dir', str(out)])
    assert rc == 0

    ck = next(out.glob('vision_model_epoch*.pt'), None)
    assert ck is not None

    # use assets dir as the generated dataset root - script will recursively gather images
    dst_json = out / 'avatar_preds.json'
    results = avatar.run_inference(ck, ds, dst_json, img_size=32, batch_size=4, save_annotated=False, export_features=False)

    assert isinstance(results, dict)
    # ensure at least one file entry present
    assert len(results) > 0
    some_key, some_val = next(iter(results.items()))
    assert 'predicted_label' in some_val
