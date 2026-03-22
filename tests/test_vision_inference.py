"""Tests for vision inference utilities and endpoints.

Tests cover:
"""  # noqa: F401

from __future__ import annotations

from typing import Any
import importlib.util
import base64
import io
import pytest
from pathlib import Path
from unittest.mock import patch

# Ensure repository root is on the path so 'scripts' is importable as a package
import sys
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

# Detect required optional dependencies early and skip tests if missing
np_spec = importlib.util.find_spec("numpy")
torch_spec = importlib.util.find_spec("torch")
vision_inf_spec = importlib.util.find_spec("scripts.vision_inference")

pil_spec = importlib.util.find_spec("PIL")

missing: list[str] = []

# Predeclare names for static analysis & defaults
VisionInference: Any = None
TinyConvNet: Any = None
np: Any = None
Image: Any = None
torch_available: bool = False
if np_spec is None:
    missing.append("numpy")
if torch_spec is None:
    missing.append("torch")
if vision_inf_spec is None:
    missing.append("scripts.vision_inference")
if pil_spec is None:
    missing.append("Pillow (PIL)")

if missing:
    pytestmark = pytest.mark.skip(
        reason=f"Missing dependencies: {', '.join(missing)}")
else:
    import numpy as np
    import torch as _torch
    from PIL import Image as _Image
    from scripts.vision_inference import VisionInference as _VisionInference, TinyConvNet as _TinyConvNet

    # Bind names in a way static checkers can understand
    VisionInference = _VisionInference
    TinyConvNet = _TinyConvNet
    Image = _Image
    torch = _torch
    torch_available = True


@pytest.fixture
def dummy_checkpoint(tmp_path: Path) -> tuple[Path, list[str]]:
    """Create a minimal checkpoint for testing."""
    if not torch_available:
        pytest.skip("PyTorch not available")
    model = TinyConvNet(num_classes=3)  # type: ignore
    classes = ['happy', 'sad', 'neutral']
    from typing import Dict
    checkpoint: Dict[str, Any] = {
        'model': model.state_dict(),  # type: ignore
        'classes': classes
    }
    ckpt_path = tmp_path / "test_checkpoint.pt"
    torch.save(checkpoint, ckpt_path)  # type: ignore
    return ckpt_path, classes


@pytest.fixture
def test_image() -> Image.Image:
    """Create a simple test image."""
    img_array = np.random.randint(0, 255, size=(64, 64, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, mode='RGB')
    return img


@pytest.fixture
def test_image_base64(test_image: Image.Image) -> str:
    """Convert test image to base64 string."""
    buffer = io.BytesIO()
    test_image.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    b64_str = base64.b64encode(img_bytes).decode('ascii')
    return b64_str


class TestTinyConvNet:
    """Test the CNN architecture."""

    def test_model_initialization(self) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        model2 = TinyConvNet(num_classes=2)  # type: ignore
        assert model2 is not None
        model5 = TinyConvNet(num_classes=5)  # type: ignore
        assert model5 is not None

    def test_forward_pass(self) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        model = TinyConvNet(num_classes=3)  # type: ignore
        batch = torch.randn(4, 3, 64, 64)  # type: ignore
        output = model.forward(batch)  # type: ignore
        assert output.shape == (4, 3)  # type: ignore

    def test_different_input_sizes(self) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        model = TinyConvNet(num_classes=3)  # type: ignore
        out1 = model.forward(torch.randn(1, 3, 64, 64))  # type: ignore
        assert out1.shape == (1, 3)  # type: ignore
        out2 = model.forward(torch.randn(1, 3, 128, 128))  # type: ignore
        assert out2.shape == (1, 3)  # type: ignore


class TestVisionInference:
    """Test VisionInference class ."""

    def test_initialization_with_checkpoint(self, dummy_checkpoint: tuple[Path, list[str]]) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference already imported at module level when available
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        assert str(vi.checkpoint_path) == str(ckpt_path)
        assert vi.classes == classes
        assert str(vi.device) == 'cpu'

    def test_initialization_without_checkpoint_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        monkeypatch.setattr(
            'scripts.vision_inference.DEFAULT_CHECKPOINT_DIRS',
            [str(tmp_path / 'nonexistent')]
        )
        with pytest.raises(FileNotFoundError, match="No checkpoint found"):
            VisionInference()  # type: ignore

    def test_device_autodetection(self, dummy_checkpoint: tuple[Path, list[str]]) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path))  # type: ignore
        expected_device = 'cuda' if torch.cuda.is_available() else 'cpu'
        assert str(vi.device) == expected_device

    def test_preprocess(self, dummy_checkpoint: tuple[Path, list[str]], test_image: Image.Image) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu', img_size=64)  # type: ignore
        tensor = vi.preprocess(test_image)  # type: ignore
        assert tensor.shape == (1, 3, 64, 64)  # type: ignore
        min_val = tensor.min().item()
        max_val = tensor.max().item()
        assert 0.0 - 1e-2 <= min_val <= 1.0 + 1e-2
        assert 0.0 - 1e-2 <= max_val <= 1.0 + 1e-2

    def test_preprocess_converts_mode(self, dummy_checkpoint: tuple[Path, list[str]]) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        gray_img = Image.new('L', (64, 64), color=128)
        tensor = vi.preprocess(gray_img)  # type: ignore
        assert tensor.shape[1] == 3  # type: ignore

    def test_predict(self, dummy_checkpoint: tuple[Path, list[str]], test_image: Image.Image) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        result = vi.predict(test_image)  # type: ignore
        assert 'label' in result
        assert 'confidence' in result
        assert 'scores' in result
        assert result['label'] in classes
        assert isinstance(result['confidence'], float)
        assert 0.0 <= result['confidence'] <= 1.0
        assert set(result['scores'].keys()) == set(classes)  # type: ignore
        scores_sum = sum(result['scores'].values())  # type: ignore
        assert abs(scores_sum - 1.0) < 0.01

    def test_predict_base64(self, dummy_checkpoint: tuple[Path, list[str]], test_image_base64: str) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        result = vi.predict_base64(test_image_base64)  # type: ignore
        assert 'label' in result
        assert result['label'] in classes

    def test_predict_file(self, dummy_checkpoint: tuple[Path, list[str]], test_image: Image.Image, tmp_path: Path) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        img_path = tmp_path / "test.png"
        test_image.save(img_path)
        result = vi.predict_file(str(img_path))  # type: ignore
        assert 'label' in result
        assert result['label'] in classes

    def test_predict_batch(self, dummy_checkpoint: tuple[Path, list[str]]) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        images = [Image.fromarray(np.random.randint(0, 255, size=(
            64, 64, 3), dtype=np.uint8), mode='RGB') for _ in range(3)]
        results = vi.predict_batch(images)  # type: ignore
        assert len(results) == 3
        for result in results:
            assert 'label' in result
            assert 'confidence' in result
            assert 'scores' in result
            assert result['label'] in classes

    def test_get_model_info(self, dummy_checkpoint: tuple[Path, list[str]]) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu', img_size=128)  # type: ignore
        info = vi.get_model_info()  # type: ignore
        assert info['checkpoint_path'] == str(ckpt_path)
        assert info['classes'] == classes
        assert info['num_classes'] == len(classes)
        assert 'cpu' in str(info['device'])
        assert info['img_size'] == 128

    def test_find_latest_checkpoint(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_dir = tmp_path / "data_out" / "vision_training"
        ckpt_dir.mkdir(parents=True)
        monkeypatch.setattr(
            'scripts.vision_inference.DEFAULT_CHECKPOINT_DIRS',
            ['data_out/vision_training']
        )
        import time
        old_ckpt = ckpt_dir / "model_old.pt"
        import torch
        torch.save({'model': {}, 'classes': ['a', 'b']}, old_ckpt)
        time.sleep(0.01)
        new_ckpt = ckpt_dir / "model_new.pt"
        torch.save({'model': {}, 'classes': ['a', 'b']}, new_ckpt)
        with patch('scripts.vision_inference.Path') as mock_path:
            mock_path.return_value.resolve.return_value.parent.parent = tmp_path
            vi_instance = VisionInference.__new__(
                VisionInference)  # type: ignore
            result = vi_instance._find_latest_checkpoint()  # type: ignore
        assert result is None or getattr(result, 'suffix', None) == '.pt'


class TestVisionInferenceErrors:
    """Test error handling in vision inference."""

    def test_invalid_base64(self, dummy_checkpoint: tuple[Path, list[str]]) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        with pytest.raises(Exception):
            vi.predict_base64("not_valid_base64!!!")  # type: ignore

    def test_invalid_file_path(self, dummy_checkpoint: tuple[Path, list[str]]) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        with pytest.raises(FileNotFoundError):
            vi.predict_file("/nonexistent/path/image.jpg")  # type: ignore

    def test_corrupted_image_data(self, dummy_checkpoint: tuple[Path, list[str]]) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        bad_data = base64.b64encode(b"not an image").decode('ascii')
        with pytest.raises(Exception):
            vi.predict_base64(bad_data)  # type: ignore


class TestIntegration:
    """Integration tests simulating endpoint usage."""

    def test_full_inference_pipeline(self, dummy_checkpoint: tuple[Path, list[str]], test_image: Image.Image) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        # VisionInference imported at module level
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        result = vi.predict(test_image)  # type: ignore
        assert result['label'] in classes
        assert isinstance(result['confidence'], float)
        assert 0.0 <= result['confidence'] <= 1.0
        scores: dict[str, float] = result['scores']  # type: ignore
        assert isinstance(scores, dict)
        assert len(scores) == len(classes)
        top_class = max(scores, key=lambda k: scores[k])  # type: ignore
        assert result['label'] == top_class
        assert result['confidence'] == scores[top_class]  # type: ignore

    def test_model_caching_simulation(self, dummy_checkpoint: tuple[Path, list[str]], test_image: Image.Image) -> None:
        if not torch_available:
            pytest.skip("PyTorch not available")
        ckpt_path, _ = dummy_checkpoint
        vi1 = VisionInference(checkpoint_path=str(
            ckpt_path), device='cpu')  # type: ignore
        result1 = vi1.predict(test_image)  # type: ignore
        result2 = vi1.predict(test_image)  # type: ignore
        assert 'label' in result1
        assert 'label' in result2


@pytest.mark.skipif(not torch_available, reason="PyTorch not available")
def test_cli_import() -> None:
    from scripts.vision_inference import main  # type: ignore
    assert callable(main)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
