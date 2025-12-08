"""Unit tests for quantum-ai/web_app.py path traversal security fixes."""
import importlib.util
import sys
from pathlib import Path
from typing import Any

from typing import Any, Generator
from flask.testing import FlaskClient
import json

import pytest

# Import the module under test
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "quantum-ai"))


# Dynamically import web_app from quantum-ai/web_app.py (file lives in the quantum-ai/ dir)
web_app_path = REPO_ROOT / "quantum-ai" / "web_app.py"
spec = importlib.util.spec_from_file_location("web_app", str(web_app_path))
if spec is None:
    raise ImportError(f"Could not load spec for {web_app_path}")
web_app = importlib.util.module_from_spec(spec)
sys.modules["web_app"] = web_app
spec.loader.exec_module(web_app)


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Create Flask test client."""
    app = web_app.app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestGetResultDetailSecurity:
    """Test path traversal prevention in get_result_detail endpoint."""

    def test_rejects_encoded_path_traversal(self, client: Any):
        """Verify encoded ../ is rejected (e.g. %2e%2e for ..)"""
        response = client.get('/api/results/%2e%2e%2fetc%2fpasswd')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid filename" in data.get("error", "")

    def test_rejects_unicode_path_traversal(self, client: Any):
        """Verify unicode traversal attempts are rejected."""
        # U+202E (RTL override) can be used in some attacks
        response = client.get('/api/results/\u202Eetc/passwd')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid filename" in data.get("error", "")

    def test_rejects_dot_slash_normalization(self, client: Any):
        """Verify dot-slash normalization attempts are rejected."""
        response = client.get('/api/results/././../etc/passwd')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid filename" in data.get("error", "")

    def test_valid_filename_with_alphanumeric_and_timestamp(self, client: Any):
        """Verify filename with alphanumeric prefix and timestamp is accepted."""
        # This will return 404 since file doesn't exist, but shouldn't return 400
        response = client.get('/api/results/training_20250101_120000.json')
        # Should not be 400 (invalid format) - filename format is valid
        assert response.status_code in [404, 200]  # 404 if file doesn't exist

    def test_valid_filename_with_dashes(self, client: Any):
        """Verify filename with dashes passes validation."""
        response = client.get('/api/results/my-training-results.json')
        # Should be processed by filename validator (no 400 for invalid format)
        assert response.status_code in [404, 200]
        # Validate the request wasn't rejected by the filename validation logic
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            data = json.loads(response.data)
            error_msg = (data.get("error") or data.get("message") or "")
            # Ensure validator did not flag it as invalid filename
            assert "Invalid filename" not in error_msg
            # If 404, it should be due to missing file, not invalid format
            if response.status_code == 404 and error_msg:
                assert any(word in error_msg.lower()
                           for word in ["not found", "missing", "no such"])
        else:
            # Non-JSON fallback: make sure no validation error marker is present
            body_text = response.data.decode("utf-8", errors="ignore")
            assert "Invalid filename" not in body_text

    def test_valid_filename_with_underscores(self, client: Any):
        """Verify filename with underscores passes validation."""
        response = client.get('/api/results/my_training_results.json')
        assert response.status_code in [404, 200]

    def test_rejects_path_traversal_parent_dir(self, client: Any):
        """Verify path traversal with ../ is rejected."""
        response = client.get('/api/results/../../../etc/passwd')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid filename" in data.get("error", "")

    def test_rejects_path_traversal_config(self, client: Any):
        """Verify path traversal to config files is rejected."""
        response = client.get('/api/results/../config.json')
        assert response.status_code == 400

    def test_rejects_filename_with_spaces(self, client: Any):
        """Verify filename with spaces is rejected."""
        response = client.get('/api/results/file%20with%20spaces.json')
        assert response.status_code == 400

    def test_rejects_filename_without_json_extension(self, client: Any):
        """Verify filename without .json extension is rejected."""
        response = client.get('/api/results/training_results.txt')
        assert response.status_code == 400

    def test_rejects_filename_with_double_extension(self, client: Any):
        """Verify filename with double extension is rejected."""
        response = client.get('/api/results/file.json.exe')
        assert response.status_code == 400

    def test_rejects_absolute_path(self, client: Any):
        """Verify absolute path is rejected."""
        response = client.get('/api/results//etc/passwd.json')
        assert response.status_code == 400

    def test_rejects_null_bytes(self, client: Any):
        """Verify null bytes in filename are rejected."""
        response = client.get('/api/results/file%00.json')
        assert response.status_code == 400

    def test_rejects_dot_files(self, client: Any):
        """Verify dot files are rejected."""
        response = client.get('/api/results/.htaccess.json')
        assert response.status_code == 400


class TestLoadCheckpointSecurity:
    """Test path traversal prevention in load_checkpoint endpoint."""

    def test_rejects_missing_checkpoint_path(self, client: Any):
        """Verify missing checkpoint path is rejected."""
        response = client.post('/api/load_checkpoint',
                               json={},
                               content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "No checkpoint path provided" in data.get("error", "")

    def test_rejects_empty_checkpoint_path(self, client: Any):
        """Verify empty checkpoint path is rejected."""
        response = client.post('/api/load_checkpoint',
                               json={"checkpoint_path": ""},
                               content_type='application/json')
        # Empty path should fail at some validation step
        assert response.status_code in [400, 403, 404]

    def test_rejects_path_traversal_attempt(self, client: Any):
        """Verify path traversal outside checkpoints directory is rejected."""
        response = client.post('/api/load_checkpoint',
                               json={"checkpoint_path": "../../../etc/passwd"},
                               content_type='application/json')
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "must be within checkpoints directory" in data.get("error", "")

    def test_rejects_absolute_path_outside_checkpoints(self, client: Any):
        """Verify absolute paths outside checkpoints are rejected."""
        response = client.post('/api/load_checkpoint',
                               json={"checkpoint_path": "/etc/passwd"},
                               content_type='application/json')
        assert response.status_code == 403

    def test_valid_checkpoint_path_returns_404_if_not_exists(self, client: Any):
        """Verify valid checkpoint path within directory returns 404 if file doesn't exist."""
        # Create checkpoints dir path
        checkpoint_dir = REPO_ROOT / "quantum-ai" / "checkpoints"
        valid_path = str(checkpoint_dir / "nonexistent_checkpoint.npz")

        response = client.post('/api/load_checkpoint',
                               json={"checkpoint_path": valid_path},
                               content_type='application/json')
        # Should be 404 (not found) not 403 (forbidden) since path is valid but file doesn't exist
        assert response.status_code == 404


class TestPathContainmentFallback:
    """Test that path containment check works on different Python versions."""

    def test_is_relative_to_fallback_logic(self):
        """Test the fallback logic for Python < 3.9."""
        from pathlib import Path

        # Test case: valid relative path
        allowed_dir = Path("/app/results")
        valid_path = Path("/app/results/file.json")

        # Simulate is_relative_to check with fallback
        if hasattr(valid_path, "is_relative_to"):
            assert valid_path.is_relative_to(allowed_dir)
        else:
            try:
                valid_path.relative_to(allowed_dir)
                is_valid = True
            except ValueError:
                is_valid = False
            assert is_valid

    def test_fallback_rejects_traversal(self):
        """Test that fallback correctly rejects path traversal."""
        from pathlib import Path

        allowed_dir = Path("/app/results")
        invalid_path = Path("/etc/passwd")

        # Simulate is_relative_to check with fallback
        if hasattr(invalid_path, "is_relative_to"):
            assert not invalid_path.is_relative_to(allowed_dir)
        else:
            try:
                invalid_path.relative_to(allowed_dir)
                is_valid = True
            except ValueError:
                is_valid = False
            assert not is_valid
