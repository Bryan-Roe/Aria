"""Unit tests for ai-projects/quantum-ml/web_app.py path traversal and session-limit security fixes."""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Generator

import pytest

pytest.importorskip("flask", reason="flask is not installed")
from flask.testing import FlaskClient  # noqa: E402

# Import the module under test
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ai-projects" / "quantum-ml"))

# Dynamically import web_app from ai-projects/quantum-ml/web_app.py
web_app_path = REPO_ROOT / "ai-projects" / "quantum-ml" / "web_app.py"
spec = importlib.util.spec_from_file_location("web_app", str(web_app_path))
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for {web_app_path}")
web_app = importlib.util.module_from_spec(spec)
sys.modules["web_app"] = web_app
spec.loader.exec_module(web_app)


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Create Flask test client."""
    app = web_app.app
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


class TestGetResultDetailSecurity:
    """Test path traversal prevention in get_result_detail endpoint."""

    def test_rejects_encoded_path_traversal(self, client: Any):
        """Verify encoded ../ is rejected (e.g. %2e%2e for ..)."""
        response = client.get("/api/results/%2e%2e%2fetc%2fpasswd")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid filename" in data.get("error", "")

    def test_rejects_unicode_path_traversal(self, client: Any):
        """Verify unicode traversal attempts are rejected."""
        response = client.get("/api/results/\u202Eetc/passwd")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid filename" in data.get("error", "")

    def test_rejects_dot_slash_normalization(self, client: Any):
        """Verify dot-slash normalization attempts are rejected."""
        response = client.get("/api/results/././../etc/passwd")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid filename" in data.get("error", "")

    def test_valid_filename_with_alphanumeric_and_timestamp(self, client: Any):
        """Verify valid filename format is accepted by validator."""
        response = client.get("/api/results/training_20250101_120000.json")
        assert response.status_code in [404, 200]

    def test_valid_filename_with_dashes(self, client: Any):
        """Verify filename with dashes passes validation."""
        response = client.get("/api/results/my-training-results.json")
        assert response.status_code in [404, 200]
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            data = json.loads(response.data)
            error_msg = (data.get("error") or data.get("message") or "")
            assert "Invalid filename" not in error_msg
            if response.status_code == 404 and error_msg:
                assert any(
                    word in error_msg.lower() for word in ["not found", "missing", "no such"]
                )
        else:
            body_text = response.data.decode("utf-8", errors="ignore")
            assert "Invalid filename" not in body_text

    def test_valid_filename_with_underscores(self, client: Any):
        """Verify filename with underscores passes validation."""
        response = client.get("/api/results/my_training_results.json")
        assert response.status_code in [404, 200]

    def test_rejects_path_traversal_parent_dir(self, client: Any):
        """Verify path traversal with ../ is rejected."""
        response = client.get("/api/results/../../../etc/passwd")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid filename" in data.get("error", "")

    def test_rejects_path_traversal_config(self, client: Any):
        """Verify path traversal to config files is rejected."""
        response = client.get("/api/results/../config.json")
        assert response.status_code == 400

    def test_rejects_filename_with_spaces(self, client: Any):
        """Verify filename with spaces is rejected."""
        response = client.get("/api/results/file%20with%20spaces.json")
        assert response.status_code == 400

    def test_rejects_filename_without_json_extension(self, client: Any):
        """Verify filename without .json extension is rejected."""
        response = client.get("/api/results/training_results.txt")
        assert response.status_code == 400

    def test_rejects_filename_with_double_extension(self, client: Any):
        """Verify filename with double extension is rejected."""
        response = client.get("/api/results/file.json.exe")
        assert response.status_code == 400

    def test_rejects_absolute_path(self, client: Any):
        """Verify absolute path is rejected."""
        response = client.get("/api/results//etc/passwd.json")
        assert response.status_code == 400

    def test_rejects_null_bytes(self, client: Any):
        """Verify null bytes in filename are rejected."""
        response = client.get("/api/results/file%00.json")
        assert response.status_code == 400

    def test_rejects_dot_files(self, client: Any):
        """Verify dot files are rejected."""
        response = client.get("/api/results/.htaccess.json")
        assert response.status_code == 400


class TestLoadCheckpointSecurity:
    """Test path traversal prevention in load_checkpoint endpoint."""

    def test_rejects_non_object_json_body(self, client: Any):
        """Verify non-object payloads are rejected before path handling."""
        response = client.post(
            "/api/load_checkpoint",
            json=["not", "an", "object"],
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "expected JSON object" in data.get("error", "")

    def test_rejects_missing_checkpoint_path(self, client: Any):
        """Verify missing checkpoint path is rejected."""
        response = client.post(
            "/api/load_checkpoint", json={}, content_type="application/json"
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "No checkpoint path provided" in data.get("error", "")

    def test_rejects_empty_checkpoint_path(self, client: Any):
        """Verify empty checkpoint path is rejected."""
        response = client.post(
            "/api/load_checkpoint",
            json={"checkpoint_path": ""},
            content_type="application/json",
        )
        assert response.status_code in [400, 403, 404]

    def test_rejects_path_traversal_attempt(self, client: Any):
        """Verify path traversal outside checkpoints directory is rejected."""
        response = client.post(
            "/api/load_checkpoint",
            json={"checkpoint_path": "../../../etc/passwd"},
            content_type="application/json",
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "must be within checkpoints directory" in data.get("error", "")

    def test_rejects_absolute_path_outside_checkpoints(self, client: Any):
        """Verify absolute paths outside checkpoints are rejected."""
        response = client.post(
            "/api/load_checkpoint",
            json={"checkpoint_path": "/etc/passwd"},
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_valid_checkpoint_path_returns_404_if_not_exists(self, client: Any):
        """Verify valid checkpoint path within directory returns 404 if file doesn't exist."""
        checkpoint_dir = REPO_ROOT / "ai-projects" / "quantum-ml" / "checkpoints"
        valid_path = str(checkpoint_dir / "nonexistent_checkpoint.npz")

        response = client.post(
            "/api/load_checkpoint",
            json={"checkpoint_path": valid_path},
            content_type="application/json",
        )
        assert response.status_code == 404


class TestPathContainmentFallback:
    """Test that path containment check works on different Python versions."""

    def test_is_relative_to_fallback_logic(self):
        """Test the fallback logic for Python < 3.9."""
        allowed_dir = Path("/app/results")
        valid_path = Path("/app/results/file.json")

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
        allowed_dir = Path("/app/results")
        invalid_path = Path("/etc/passwd")

        if hasattr(invalid_path, "is_relative_to"):
            assert not invalid_path.is_relative_to(allowed_dir)
        else:
            try:
                invalid_path.relative_to(allowed_dir)
                is_valid = True
            except ValueError:
                is_valid = False
            assert not is_valid


@pytest.mark.unit
class TestSessionLimits:
    """Session resource-limit guards in web_app.start_training()."""

    def test_rejects_non_object_json_body(self, client: Any) -> None:
        """Returns 400 when request payload is not a JSON object."""
        resp = client.post(
            "/api/train/start",
            json=["not", "an", "object"],
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "expected JSON object" in data.get("error", "")

    def test_rejects_too_many_active_sessions(self, client: Any) -> None:
        """Returns 429 when active session count is at MAX_ACTIVE_SESSIONS."""
        import time
        from unittest.mock import patch

        class _FakeSession:
            def __init__(self, status: str) -> None:
                self.status = status
                self.start_time = time.time()
                self.end_time = None

        fake_sessions = {f"s{i}": _FakeSession("running") for i in range(2)}

        with (
            patch.object(web_app, "MAX_ACTIVE_SESSIONS", 2),
            patch.object(web_app, "training_sessions", fake_sessions),
        ):
            resp = client.post(
                "/api/train/start",
                json={"dataset": "test", "n_qubits": 2, "n_layers": 1},
                content_type="application/json",
            )
        assert resp.status_code == 429
        body = json.loads(resp.data)
        assert (
            "active" in body.get("error", "").lower()
            or "session" in body.get("error", "").lower()
        )

    def test_rejects_at_total_session_cap(self, client: Any) -> None:
        """Returns 429 when the total sessions dict is at MAX_TOTAL_SESSIONS."""
        import time
        from unittest.mock import patch

        class _FakeSession:
            def __init__(self) -> None:
                self.status = "completed"
                self.start_time = time.time()
                self.end_time = time.time()

        fake_sessions = {"s0": _FakeSession()}

        with (
            patch.object(web_app, "MAX_TOTAL_SESSIONS", 1),
            patch.object(web_app, "training_sessions", fake_sessions),
        ):
            resp = client.post(
                "/api/train/start",
                json={"dataset": "test", "n_qubits": 2, "n_layers": 1},
                content_type="application/json",
            )
        assert resp.status_code == 429

    def test_prune_removes_old_completed_sessions(self) -> None:
        """_prune_old_sessions() removes completed sessions older than TTL."""
        import time
        from unittest.mock import patch

        class _FakeSession:
            def __init__(self, status: str, end_time: float) -> None:
                self.status = status
                self.end_time = end_time

        stale_sid = "stale"
        fake_sessions = {stale_sid: _FakeSession(
            "completed", time.time() - 100)}

        with (
            patch.object(web_app, "SESSION_TTL_SECONDS", 10),
            patch.object(web_app, "training_sessions", fake_sessions),
        ):
            web_app._prune_old_sessions()

        assert stale_sid not in fake_sessions

    def test_prune_keeps_active_sessions(self) -> None:
        """_prune_old_sessions() never removes sessions still running."""
        import time
        from unittest.mock import patch

        class _FakeSession:
            def __init__(self) -> None:
                self.status = "running"
                self.end_time = time.time() - 200

        active_sid = "active"
        fake_sessions = {active_sid: _FakeSession()}

        with (
            patch.object(web_app, "SESSION_TTL_SECONDS", 1),
            patch.object(web_app, "training_sessions", fake_sessions),
        ):
            web_app._prune_old_sessions()

        assert active_sid in fake_sessions
