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

vision = importlib.import_module('scripts.training.train_vision')


@pytest.mark.parametrize('samples_per_class', [6])
def test_generate_and_train(tmp_path: Path, samples_per_class):
    # Skip if torch isn't installed in the environment running the tests.
    try:
        import torch  # noqa: F401
    except Exception:
        pytest.skip('PyTorch not available in this environment')

    ds = tmp_path / 'vision_ds'
    out = tmp_path / 'out'
    # generate a tiny toy dataset
    vision.generate_toy_shapes_dataset(ds, samples_per_class=samples_per_class, size=(32, 32))

    assert ds.exists()
    # do a dry run first - should return 0
    rc = vision.main(['--dataset', str(ds), '--epochs', '1', '--batch-size', '2', '--out-dir', str(out), '--dry-run'])
    assert rc == 0

    # actual short training to produce a checkpoint
    rc = vision.main(['--dataset', str(ds), '--epochs', '1', '--batch-size', '2', '--out-dir', str(out)])
    assert rc == 0

    ck = next(out.glob('vision_model_epoch*.pt'), None)
    assert ck is not None and ck.exists()
