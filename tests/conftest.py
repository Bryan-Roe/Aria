"""Pytest configuration for QAI test suite.

This conftest ensures that the scripts package is importable during tests.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add project root to Python path for importing scripts
# Ensure websockets.client is attached to the websockets namespace.
# In Python 3.14, submodules are not auto-attached on parent import; pyppeteer
# requires websockets.client to be accessible as an attribute.
try:
    import websockets
    import websockets.client  # noqa: F401 — forces attachment to websockets namespace
except ImportError:
    pass

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Make apps/aria importable so tests can do `from server import ...` at the top
_ARIA_APP_DIR = str(REPO_ROOT / "apps" / "aria")
if _ARIA_APP_DIR not in sys.path:
    sys.path.insert(0, _ARIA_APP_DIR)

# ==================== FIXTURES ====================


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory for testing"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing"""
    return {
        "id": 1,
        "name": "test",
        "value": 123.45,
        "items": [1, 2, 3],
        "nested": {"key": "value"},
    }


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for testing"""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
    ]


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_training_config():
    """Sample training configuration"""
    return {
        "model": "TinyLlama/TinyLlama-1.1B",
        "dataset": "test_dataset",
        "epochs": 10,
        "batch_size": 8,
        "learning_rate": 1e-4,
        "max_seq_length": 512,
    }


@pytest.fixture
def sample_aria_action():
    """Sample Aria action"""
    return {"action": "move", "direction": "left", "distance": 50}


@pytest.fixture
def sample_aria_world_state():
    """Sample Aria world state"""
    return {
        "position": (0, 0),
        "holding": None,
        "expression": "neutral",
        "objects": [],
        "world_theme": "default",
    }


# ==================== HELPER FUNCTIONS ====================


def assert_valid_json(json_str):
    """Assert that a string is valid JSON"""
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


def assert_dict_keys_exist(data_dict, required_keys):
    """Assert that all required keys exist in a dictionary"""
    for key in required_keys:
        assert key in data_dict, f"Missing required key: {key}"


def assert_valid_provider(provider_name):
    """Assert that provider name is valid"""
    valid_providers = ["azure_openai", "openai", "lmstudio", "local"]
    assert provider_name in valid_providers, f"Invalid provider: {provider_name}"


# ==================== PYTEST HOOKS ====================


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "azure: marks tests that require Azure credentials"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "quantum: marks tests that require quantum backends"
    )
    config.addinivalue_line("markers", "gpu: marks tests that require GPU")
