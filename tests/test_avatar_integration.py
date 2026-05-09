import importlib
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
numpy = pytest.importorskip("numpy")

train = importlib.import_module("scripts.training.train_vision")
avatar = importlib.import_module("scripts.inference.vision_avatar_integration")


def test_avatar_inference_small(tmp_path: Path):
    ds = tmp_path / "vision_ds"
    out = tmp_path / "out"
    train.generate_toy_shapes_dataset(ds, samples_per_class=4, size=(32, 32))

    rc = train.main(
        [
            "--dataset",
            str(ds),
            "--epochs",
            "1",
            "--batch-size",
            "2",
            "--out-dir",
            str(out),
        ]
    )
    assert rc == 0

    ck = next(out.glob("vision_model_epoch*.pt"), None)
    assert ck is not None

    # use assets dir as the generated dataset root - script will recursively gather images
    dst_json = out / "avatar_preds.json"
    results = avatar.run_inference(
        ck,
        ds,
        dst_json,
        img_size=32,
        batch_size=4,
        save_annotated=False,
        export_features=False,
    )

    assert isinstance(results, dict)
    # ensure at least one file entry present
    assert len(results) > 0
    some_key, some_val = next(iter(results.items()))
    assert "predicted_label" in some_val
