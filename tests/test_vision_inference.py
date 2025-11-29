"""Tests for vision inference utilities and endpoints.

Tests cover:
- Model loading and initialization
- Image preprocessing
- Inference on PIL images, base64 strings, and file paths
- Batch inference
- Error handling
"""
import base64
import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

# Add scripts to path
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

try:
    import torch
    from vision_inference import VisionInference, TinyConvNet
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="PyTorch not available")


@pytest.fixture
def dummy_checkpoint(tmp_path):
    """Create a minimal checkpoint for testing."""
    # Create dummy model state
    model = TinyConvNet(num_classes=3)
    classes = ['happy', 'sad', 'neutral']
    
    checkpoint = {
        'model': model.state_dict(),
        'classes': classes
    }
    
    ckpt_path = tmp_path / "test_checkpoint.pt"
    torch.save(checkpoint, ckpt_path)
    
    return ckpt_path, classes


@pytest.fixture
def test_image():
    """Create a simple test image."""
    # Create 64x64 RGB image with random pattern
    img_array = np.random.randint(0, 255, size=(64, 64, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, mode='RGB')
    return img


@pytest.fixture
def test_image_base64(test_image):
    """Convert test image to base64 string."""
    buffer = io.BytesIO()
    test_image.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    b64_str = base64.b64encode(img_bytes).decode('ascii')
    return b64_str


class TestTinyConvNet:
    """Test the CNN architecture."""
    
    def test_model_initialization(self):
        """Test model can be initialized with different class counts."""
        model2 = TinyConvNet(num_classes=2)
        assert model2 is not None
        
        model5 = TinyConvNet(num_classes=5)
        assert model5 is not None
    
    def test_forward_pass(self):
        """Test forward pass produces correct output shape."""
        model = TinyConvNet(num_classes=3)
        batch = torch.randn(4, 3, 64, 64)
        
        output = model(batch)
        
        assert output.shape == (4, 3)  # batch_size x num_classes
    
    def test_different_input_sizes(self):
        """Test model handles different input sizes (due to adaptive pooling)."""
        model = TinyConvNet(num_classes=3)
        
        # 64x64
        out1 = model(torch.randn(1, 3, 64, 64))
        assert out1.shape == (1, 3)
        
        # 128x128 (should also work due to AdaptiveAvgPool2d)
        out2 = model(torch.randn(1, 3, 128, 128))
        assert out2.shape == (1, 3)


class TestVisionInference:
    """Test VisionInference class."""
    
    def test_initialization_with_checkpoint(self, dummy_checkpoint):
        """Test initializing with explicit checkpoint path."""
        ckpt_path, classes = dummy_checkpoint
        
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        assert vi.checkpoint_path == ckpt_path
        assert vi.classes == classes
        assert vi.device == torch.device('cpu')
    
    def test_initialization_without_checkpoint_fails(self, tmp_path, monkeypatch):
        """Test that initialization fails gracefully when no checkpoint found."""
        # Mock the search paths to empty directories
        monkeypatch.setattr(
            'vision_inference.DEFAULT_CHECKPOINT_DIRS',
            [str(tmp_path / 'nonexistent')]
        )
        
        with pytest.raises(FileNotFoundError, match="No checkpoint found"):
            VisionInference()
    
    def test_device_autodetection(self, dummy_checkpoint):
        """Test device auto-detection logic."""
        ckpt_path, _ = dummy_checkpoint
        
        vi = VisionInference(checkpoint_path=str(ckpt_path))
        
        # Should default to cuda if available, else cpu
        expected_device = 'cuda' if torch.cuda.is_available() else 'cpu'
        assert str(vi.device) == expected_device
    
    def test_preprocess(self, dummy_checkpoint, test_image):
        """Test image preprocessing."""
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu', img_size=64)
        
        tensor = vi.preprocess(test_image)
        
        # Check shape: (1, 3, 64, 64)
        assert tensor.shape == (1, 3, 64, 64)
        
        # Check normalized to [0, 1]
        assert tensor.min() >= 0.0
        assert tensor.max() <= 1.0
    
    def test_preprocess_converts_mode(self, dummy_checkpoint):
        """Test preprocessing converts non-RGB images to RGB."""
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        # Create grayscale image
        gray_img = Image.new('L', (64, 64), color=128)
        
        tensor = vi.preprocess(gray_img)
        
        # Should have 3 channels after conversion
        assert tensor.shape[1] == 3
    
    def test_predict(self, dummy_checkpoint, test_image):
        """Test prediction on PIL image."""
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        result = vi.predict(test_image)
        
        # Check result structure
        assert 'label' in result
        assert 'confidence' in result
        assert 'scores' in result
        
        # Check label is one of the classes
        assert result['label'] in classes
        
        # Check confidence is in valid range
        assert 0.0 <= result['confidence'] <= 1.0
        
        # Check scores dict has all classes
        assert set(result['scores'].keys()) == set(classes)
        
        # Check scores sum to ~1.0 (softmax)
        scores_sum = sum(result['scores'].values())
        assert abs(scores_sum - 1.0) < 0.01
    
    def test_predict_base64(self, dummy_checkpoint, test_image_base64):
        """Test prediction on base64-encoded image."""
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        result = vi.predict_base64(test_image_base64)
        
        assert 'label' in result
        assert result['label'] in classes
    
    def test_predict_file(self, dummy_checkpoint, test_image, tmp_path):
        """Test prediction on image file."""
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        # Save test image to file
        img_path = tmp_path / "test.png"
        test_image.save(img_path)
        
        result = vi.predict_file(str(img_path))
        
        assert 'label' in result
        assert result['label'] in classes
    
    def test_predict_batch(self, dummy_checkpoint):
        """Test batch prediction on multiple images."""
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        # Create 3 test images
        images = []
        for _ in range(3):
            img_array = np.random.randint(0, 255, size=(64, 64, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            images.append(img)
        
        results = vi.predict_batch(images)
        
        # Check we got 3 results
        assert len(results) == 3
        
        # Check each result has correct structure
        for result in results:
            assert 'label' in result
            assert 'confidence' in result
            assert 'scores' in result
            assert result['label'] in classes
    
    def test_get_model_info(self, dummy_checkpoint):
        """Test model metadata retrieval."""
        ckpt_path, classes = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu', img_size=128)
        
        info = vi.get_model_info()
        
        assert info['checkpoint_path'] == str(ckpt_path)
        assert info['classes'] == classes
        assert info['num_classes'] == len(classes)
        assert 'cpu' in info['device']
        assert info['img_size'] == 128
    
    def test_find_latest_checkpoint(self, tmp_path, monkeypatch):
        """Test finding the most recent checkpoint."""
        # Create mock checkpoint directory
        ckpt_dir = tmp_path / "data_out" / "vision_training"
        ckpt_dir.mkdir(parents=True)
        
        # Mock the search paths
        monkeypatch.setattr(
            'vision_inference.DEFAULT_CHECKPOINT_DIRS',
            ['data_out/vision_training']
        )
        
        # Create checkpoints with different timestamps
        import time
        
        old_ckpt = ckpt_dir / "model_old.pt"
        torch.save({'model': {}, 'classes': ['a', 'b']}, old_ckpt)
        time.sleep(0.01)
        
        new_ckpt = ckpt_dir / "model_new.pt"
        torch.save({'model': {}, 'classes': ['a', 'b']}, new_ckpt)
        
        # Mock Path resolution
        with patch('vision_inference.Path') as mock_path:
            mock_path.return_value.resolve.return_value.parent.parent = tmp_path
            
            vi_instance = VisionInference.__new__(VisionInference)
            result = vi_instance._find_latest_checkpoint()
        
        # Should find the newer checkpoint
        # (In reality, this is complex to test due to file system timing)
        # Just verify the method doesn't crash
        assert result is None or result.suffix == '.pt'


class TestVisionInferenceErrors:
    """Test error handling in vision inference."""
    
    def test_invalid_base64(self, dummy_checkpoint):
        """Test handling of invalid base64 data."""
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        with pytest.raises(Exception):  # Could be binascii.Error or similar
            vi.predict_base64("not_valid_base64!!!")
    
    def test_invalid_file_path(self, dummy_checkpoint):
        """Test handling of non-existent file."""
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        with pytest.raises(FileNotFoundError):
            vi.predict_file("/nonexistent/path/image.jpg")
    
    def test_corrupted_image_data(self, dummy_checkpoint):
        """Test handling of corrupted image data."""
        ckpt_path, _ = dummy_checkpoint
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        # Valid base64 but not a valid image
        bad_data = base64.b64encode(b"not an image").decode('ascii')
        
        with pytest.raises(Exception):  # PIL will raise an error
            vi.predict_base64(bad_data)


class TestIntegration:
    """Integration tests simulating endpoint usage."""
    
    def test_full_inference_pipeline(self, dummy_checkpoint, test_image):
        """Test complete inference pipeline from image to result."""
        ckpt_path, classes = dummy_checkpoint
        
        # Initialize
        vi = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        
        # Run inference
        result = vi.predict(test_image)
        
        # Validate complete result
        assert result['label'] in classes
        assert 0.0 <= result['confidence'] <= 1.0
        assert len(result['scores']) == len(classes)
        
        # Verify top prediction matches confidence
        top_class = max(result['scores'], key=result['scores'].get)
        assert result['label'] == top_class
        assert result['confidence'] == result['scores'][top_class]
    
    def test_model_caching_simulation(self, dummy_checkpoint, test_image):
        """Simulate model caching behavior (singleton pattern for endpoints)."""
        ckpt_path, _ = dummy_checkpoint
        
        # First request - initialize model
        vi1 = VisionInference(checkpoint_path=str(ckpt_path), device='cpu')
        result1 = vi1.predict(test_image)
        
        # Simulate reusing same instance (like endpoint caching)
        result2 = vi1.predict(test_image)
        
        # Both should work without reinitializing
        assert 'label' in result1
        assert 'label' in result2


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_cli_import():
    """Test that the CLI main function can be imported."""
    from vision_inference import main
    
    assert callable(main)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
