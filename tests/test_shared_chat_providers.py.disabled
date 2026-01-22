"""Tests for shared/chat_providers.py"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from shared.chat_providers import (
    detect_provider,
    get_chat_client,
    validate_provider_config,
    PROVIDER_PRIORITY
)


class TestProviderDetection:
    """Test provider detection logic"""
    
    def test_detect_explicit_provider(self):
        """Test explicit provider selection"""
        provider = detect_provider(explicit_provider="openai")
        assert provider == "openai"
    
    def test_detect_lmstudio_with_env(self):
        """Test LMStudio detection via env var"""
        with patch.dict(os.environ, {"LMSTUDIO_BASE_URL": "http://localhost:1234"}):
            provider = detect_provider()
            assert provider == "lmstudio"
    
    def test_detect_azure_openai_with_full_config(self):
        """Test Azure OpenAI detection with all required env vars"""
        env = {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
            "AZURE_OPENAI_API_VERSION": "2023-05-15"
        }
        with patch.dict(os.environ, env):
            provider = detect_provider()
            assert provider == "azure_openai"
    
    def test_detect_azure_openai_missing_key(self):
        """Test Azure OpenAI requires all config"""
        env = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
            "AZURE_OPENAI_API_VERSION": "2023-05-15"
        }
        with patch.dict(os.environ, env, clear=True):
            provider = detect_provider()
            assert provider != "azure_openai"
    
    def test_detect_openai_with_api_key(self):
        """Test OpenAI detection via API key"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            provider = detect_provider()
            assert provider == "openai"
    
    def test_detect_local_fallback(self):
        """Test fallback to local provider when no config"""
        with patch.dict(os.environ, {}, clear=True):
            provider = detect_provider()
            assert provider == "local"
    
    def test_provider_priority_order(self):
        """Test that provider priority is correct"""
        # LMStudio should have higher priority than Azure
        assert PROVIDER_PRIORITY.index("lmstudio") < PROVIDER_PRIORITY.index("azure_openai")


class TestValidateProviderConfig:
    """Test provider configuration validation"""
    
    def test_validate_azure_openai_config(self):
        """Test Azure OpenAI config validation"""
        config = {
            "api_key": "test-key",
            "endpoint": "https://test.openai.azure.com/",
            "deployment": "test-deployment",
            "api_version": "2023-05-15"
        }
        assert validate_provider_config("azure_openai", config)
    
    def test_validate_openai_config(self):
        """Test OpenAI config validation"""
        config = {"api_key": "sk-test"}
        assert validate_provider_config("openai", config)
    
    def test_validate_lmstudio_config(self):
        """Test LMStudio config validation"""
        config = {"base_url": "http://localhost:1234"}
        assert validate_provider_config("lmstudio", config)
    
    def test_validate_invalid_config(self):
        """Test validation fails with missing required fields"""
        config = {"deployment": "test"}
        assert not validate_provider_config("azure_openai", config)
    
    def test_validate_unknown_provider(self):
        """Test validation for unknown provider"""
        config = {"test": "value"}
        result = validate_provider_config("unknown_provider", config)
        assert not result


class TestGetChatClient:
    """Test chat client creation"""
    
    @patch("shared.chat_providers.OpenAI")
    def test_get_openai_client(self, mock_openai):
        """Test OpenAI client creation"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            mock_openai.return_value = Mock()
            client = get_chat_client("openai")
            assert client is not None
    
    @patch("shared.chat_providers.AzureOpenAI")
    def test_get_azure_openai_client(self, mock_azure):
        """Test Azure OpenAI client creation"""
        env = {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
            "AZURE_OPENAI_API_VERSION": "2023-05-15"
        }
        with patch.dict(os.environ, env):
            mock_azure.return_value = Mock()
            client = get_chat_client("azure_openai")
            assert client is not None
    
    def test_get_local_client(self):
        """Test local client creation"""
        client = get_chat_client("local")
        assert client is not None
        # Local client should be a simple mock
        assert hasattr(client, "chat" if hasattr(client, "chat") else "__call__")


class TestProviderFallback:
    """Test provider fallback chain"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_fallback_chain_no_providers(self):
        """Test fallback to local when no providers configured"""
        provider = detect_provider()
        assert provider == "local"
    
    @patch.dict(os.environ, {"LMSTUDIO_BASE_URL": "http://localhost:1234", "OPENAI_API_KEY": "sk-test"})
    def test_lmstudio_priority_over_openai(self):
        """Test LMStudio has priority over OpenAI"""
        provider = detect_provider()
        assert provider == "lmstudio"


class TestProviderErrors:
    """Test error handling in provider detection and validation"""
    
    def test_invalid_provider_name(self):
        """Test invalid provider name"""
        with pytest.raises((ValueError, KeyError)):
            detect_provider(explicit_provider="invalid_provider")
    
    def test_config_missing_required_fields(self):
        """Test config with missing required fields"""
        incomplete_config = {"api_key": "test"}
        result = validate_provider_config("azure_openai", incomplete_config)
        assert not result
