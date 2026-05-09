import importlib
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
numpy = pytest.importorskip("numpy")

train = importlib.import_module("scripts.training.train_vision")
eval_mod = importlib.import_module("scripts.evaluation.evaluate_vision")


@pytest.mark.parametrize("samples_per_class", [6])
def test_evaluate_small(tmp_path: Path, samples_per_class):
    ds = tmp_path / "vision_ds"
    out = tmp_path / "out"
    # create toy dataset
    train.generate_toy_shapes_dataset(
        ds, samples_per_class=samples_per_class, size=(32, 32)
    )

    # train a tiny model to get a checkpoint
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
    assert ck is not None and ck.exists()

    # run evaluation
    rc2 = eval_mod.run_eval(
        [
            "--checkpoint",
            str(ck),
            "--dataset",
            str(ds),
            "--out-dir",
            str(out / "eval_out"),
            "--img-size",
            "32",
            "--show-examples",
            "2",
        ]
    )
    assert rc2 == 0
    res_json = out / "eval_out" / "results.json"
    assert res_json.exists()
