"""Unit tests for quantum-ai/web_app.py path traversal security fixes."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

import pytest

# Import the module under test
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "quantum-ai"))


@pytest.fixture
def client():
    """Create Flask test client."""
    from web_app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestGetResultDetailSecurity:
    """Test path traversal prevention in get_result_detail endpoint."""

    def test_valid_filename_format(self, client):
        """Verify valid filename format is accepted."""
        # This will return 404 since file doesn't exist, but shouldn't return 400
        response = client.get('/api/results/training_20250101_120000.json')
        # Should not be 400 (invalid format) - filename format is valid
        assert response.status_code in [404, 200]  # 404 if file doesn't exist

    def test_valid_filename_with_dashes(self, client):
        """Verify filename with dashes passes validation."""
        response = client.get('/api/results/my-training-results.json')
        assert response.status_code in [404, 200]

    def test_valid_filename_with_underscores(self, client):
        """Verify filename with underscores passes validation."""
        response = client.get('/api/results/my_training_results.json')
        assert response.status_code in [404, 200]

    def test_rejects_path_traversal_parent_dir(self, client):
        """Verify path traversal with ../ is rejected."""
        response = client.get('/api/results/../../../etc/passwd')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid filename" in data.get("error", "")

    def test_rejects_path_traversal_config(self, client):
        """Verify path traversal to config files is rejected."""
        response = client.get('/api/results/../config.json')
        assert response.status_code == 400

    def test_rejects_filename_with_spaces(self, client):
        """Verify filename with spaces is rejected."""
        response = client.get('/api/results/file%20with%20spaces.json')
        assert response.status_code == 400

    def test_rejects_filename_without_json_extension(self, client):
        """Verify filename without .json extension is rejected."""
        response = client.get('/api/results/training_results.txt')
        assert response.status_code == 400

    def test_rejects_filename_with_double_extension(self, client):
        """Verify filename with double extension is rejected."""
        response = client.get('/api/results/file.json.exe')
        assert response.status_code == 400

    def test_rejects_absolute_path(self, client):
        """Verify absolute path is rejected."""
        response = client.get('/api/results//etc/passwd.json')
        assert response.status_code == 400

    def test_rejects_null_bytes(self, client):
        """Verify null bytes in filename are rejected."""
        response = client.get('/api/results/file%00.json')
        assert response.status_code == 400

    def test_rejects_dot_files(self, client):
        """Verify dot files are rejected."""
        response = client.get('/api/results/.htaccess.json')
        assert response.status_code == 400


class TestLoadCheckpointSecurity:
    """Test path traversal prevention in load_checkpoint endpoint."""

    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        from web_app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_rejects_missing_checkpoint_path(self, client):
        """Verify missing checkpoint path is rejected."""
        response = client.post('/api/load_checkpoint',
                               json={},
                               content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "No checkpoint path provided" in data.get("error", "")

    def test_rejects_empty_checkpoint_path(self, client):
        """Verify empty checkpoint path is rejected."""
        response = client.post('/api/load_checkpoint',
                               json={"checkpoint_path": ""},
                               content_type='application/json')
        # Empty path should fail at some validation step
        assert response.status_code in [400, 403, 404]

    def test_rejects_path_traversal_attempt(self, client):
        """Verify path traversal outside checkpoints directory is rejected."""
        response = client.post('/api/load_checkpoint',
                               json={"checkpoint_path": "../../../etc/passwd"},
                               content_type='application/json')
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "must be within checkpoints directory" in data.get("error", "")

    def test_rejects_absolute_path_outside_checkpoints(self, client):
        """Verify absolute paths outside checkpoints are rejected."""
        response = client.post('/api/load_checkpoint',
                               json={"checkpoint_path": "/etc/passwd"},
                               content_type='application/json')
        assert response.status_code == 403

    def test_valid_checkpoint_path_returns_404_if_not_exists(self, client):
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
