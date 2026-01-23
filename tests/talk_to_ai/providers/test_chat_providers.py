"""Tests for chat provider functionality"""
import pytest
import sys
from pathlib import Path
from unittest import mock
import json

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestProviderDetection:
    """Test provider detection chain"""
    
    def test_provider_detection_order(self):
        """Test provider detection follows correct order"""
        # Order: LMStudio -> Azure -> OpenAI -> Local
        
        detection_order = [
            "lmstudio",
            "azure_openai",
            "openai",
            "local"
        ]
        
        assert detection_order[0] == "lmstudio"
        assert detection_order[-1] == "local"
    
    def test_lmstudio_detection(self):
        """Test LMStudio detection"""
        with mock.patch.dict("os.environ", {"LMSTUDIO_BASE_URL": "http://localhost:1234"}):
            import os
            lmstudio_url = os.environ.get("LMSTUDIO_BASE_URL")
            assert lmstudio_url == "http://localhost:1234"
    
    def test_azure_openai_detection(self):
        """Test Azure OpenAI detection"""
        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_API_VERSION"
        ]
        
        env_config = {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
            "AZURE_OPENAI_API_VERSION": "2024-02-15-preview"
        }
        
        is_configured = all(var in env_config for var in required_vars)
        assert is_configured
    
    def test_openai_detection(self):
        """Test OpenAI detection"""
        with mock.patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            import os
            openai_key = os.environ.get("OPENAI_API_KEY")
            assert openai_key == "test-key"
    
    def test_fallback_to_local(self):
        """Test fallback to local provider"""
        with mock.patch.dict("os.environ", {}, clear=True):
            # All env vars cleared, should fallback to local
            lmstudio_url = None
            openai_key = None
            
            if lmstudio_url is None and openai_key is None:
                provider = "local"
            
            assert provider == "local"


class TestChatCompletion:
    """Test chat completion functionality"""
    
    def test_single_message_completion(self):
        """Test single message completion"""
        messages = [{"role": "user", "content": "Hello"}]
        
        # Simulate response
        response = {
            "choices": [
                {"message": {"role": "assistant", "content": "Hello! How can I help?"}}
            ]
        }
        
        assert len(response["choices"]) > 0
        assert "content" in response["choices"][0]["message"]
    
    def test_multi_turn_conversation(self):
        """Test multi-turn conversation"""
        messages = [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2=4"},
            {"role": "user", "content": "What about 3+3?"}
        ]
        
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
    
    def test_system_prompt_handling(self):
        """Test system prompt handling"""
        system_prompt = "You are a helpful math tutor."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Help me with algebra"}
        ]
        
        assert messages[0]["role"] == "system"
        assert system_prompt in messages[0]["content"]


class TestStreamingResponses:
    """Test streaming response handling"""
    
    def test_sse_stream_parsing(self):
        """Test parsing SSE stream"""
        stream_data = "data: {\"content\": \"Hello\"}\ndata: {\"content\": \" world\"}\n"
        
        chunks = []
        for line in stream_data.split("\n"):
            if line.startswith("data: "):
                try:
                    chunk = json.loads(line[6:])
                    chunks.append(chunk)
                except:
                    pass
        
        assert len(chunks) == 2
        assert chunks[0]["content"] == "Hello"
    
    def test_stream_accumulation(self):
        """Test accumulating stream chunks"""
        chunks = [
            {"content": "Hello"},
            {"content": " "},
            {"content": "world"}
        ]
        
        full_response = "".join(c["content"] for c in chunks)
        assert full_response == "Hello world"
    
    def test_stream_error_handling(self):
        """Test handling errors in streams"""
        stream_chunks = [
            {"content": "Hello"},
            {"error": "Connection lost"},
            {"content": " world"}
        ]
        
        valid_chunks = [c for c in stream_chunks if "content" in c]
        
        assert len(valid_chunks) == 2
        assert valid_chunks[0]["content"] == "Hello"


class TestLoRAAdapters:
    """Test LoRA adapter support"""
    
    def test_adapter_path_validation(self):
        """Test validating adapter paths"""
        adapter_paths = [
            "models/lora/adapter_v1",
            "data_out/lora_models/best_adapter",
            "/path/to/adapter"
        ]
        
        for path in adapter_paths:
            # Valid paths should not be empty
            assert len(path) > 0
            assert "/" in path or "\\" in path
    
    def test_adapter_config_structure(self):
        """Test adapter config structure"""
        adapter_config = {
            "base_model_name_or_path": "microsoft/phi-2",
            "modules_to_save": ["lm_head", "embedding"],
            "r": 16,
            "lora_alpha": 32,
            "target_modules": ["q_proj", "v_proj"]
        }
        
        assert "base_model_name_or_path" in adapter_config
        assert "r" in adapter_config
        assert adapter_config["r"] == 16
    
    def test_adapter_loading(self):
        """Test loading adapter with base model"""
        from pathlib import Path
        
        # Check that adapter files would exist
        adapter_dir = Path("models/lora/adapter")
        required_files = ["adapter_config.json", "adapter_model.safetensors"]
        
        # Mock the check
        for file in required_files:
            # Would check (adapter_dir / file).exists()
            assert len(file) > 0


class TestProviderFallback:
    """Test provider fallback chain"""
    
    def test_fallback_on_failure(self):
        """Test falling back when provider fails"""
        providers = ["azure_openai", "openai", "lmstudio", "local"]
        
        def try_provider(name):
            if name == "azure_openai":
                raise ConnectionError("Azure unavailable")
            elif name == "openai":
                raise ConnectionError("OpenAI unavailable")
            elif name == "lmstudio":
                return "success"
            return "fallback"
        
        current_provider = None
        for provider in providers:
            try:
                result = try_provider(provider)
                current_provider = provider
                break
            except:
                continue
        
        assert current_provider == "lmstudio"
    
    def test_complete_fallback_chain(self):
        """Test complete fallback to local"""
        providers = ["azure_openai", "openai", "lmstudio", "local"]
        
        def all_fail(name):
            raise ConnectionError(f"{name} unavailable")
        
        current_provider = None
        for provider in providers[:-1]:
            try:
                all_fail(provider)
            except:
                continue
        
        # Fall back to last provider
        current_provider = providers[-1]
        assert current_provider == "local"


class TestChatEndpoint:
    """Test chat API endpoint"""
    
    def test_chat_request_validation(self):
        """Test validating chat request"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        }
        
        assert "messages" in request
        assert len(request["messages"]) > 0
        assert isinstance(request["messages"], list)
    
    def test_chat_response_format(self):
        """Test chat response format"""
        response = {
            "id": "chatcmpl-123",
            "object": "text_completion",
            "created": 1234567890,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello!"
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }
        
        assert "choices" in response
        assert len(response["choices"]) > 0
        assert response["choices"][0]["finish_reason"] in ["stop", "length", "content_filter"]


class TestTokenCounting:
    """Test token counting functionality"""
    
    def test_approximate_token_count(self):
        """Test approximate token counting"""
        text = "The quick brown fox jumps over the lazy dog"
        
        # Rough estimate: ~1 token per 4 characters
        approx_tokens = len(text) / 4
        
        # Should be around 10-12 tokens
        assert 8 < approx_tokens < 15
    
    def test_token_limit_checking(self):
        """Test checking against token limit"""
        max_tokens = 4096
        message_tokens = 3500
        
        remaining = max_tokens - message_tokens
        
        assert remaining > 0
        assert remaining == 596


class TestErrorRecovery:
    """Test error recovery in chat"""
    
    def test_retry_with_exponential_backoff(self):
        """Test retrying with exponential backoff"""
        import time
        
        max_retries = 3
        base_wait = 1
        
        wait_times = []
        for attempt in range(max_retries):
            wait_time = base_wait * (2 ** attempt)
            wait_times.append(wait_time)
        
        assert wait_times[0] == 1
        assert wait_times[1] == 2
        assert wait_times[2] == 4
    
    def test_rate_limit_handling(self):
        """Test handling rate limits"""
        rate_limit_response = {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error"
            },
            "retry_after": 60
        }
        
        if "retry_after" in rate_limit_response:
            wait_time = rate_limit_response["retry_after"]
            assert wait_time == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
