"""Test suite for refactored provider response handling.

This test validates that the extracted helper methods in BaseChatProvider
maintain the same behavior as the original inline implementations.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

from chat_providers import BaseChatProvider

# Add talk-to-ai to path
sys.path.insert(
    0, str(Path(__file__).parent.parent / "ai-projects" / "chat-cli" / "src")
)


def test_handle_openai_streaming_response():
    """Test that streaming response handler correctly extracts content."""
    # Create mock streaming response with typical OpenAI chunk structure
    mock_chunk1 = Mock()
    mock_chunk1.choices = [Mock()]
    mock_chunk1.choices[0].delta = Mock()
    mock_chunk1.choices[0].delta.content = "Hello"

    mock_chunk2 = Mock()
    mock_chunk2.choices = [Mock()]
    mock_chunk2.choices[0].delta = Mock()
    mock_chunk2.choices[0].delta.content = " world"

    mock_chunk3 = Mock()
    mock_chunk3.choices = [Mock()]
    mock_chunk3.choices[0].delta = Mock()
    # Empty content should be skipped
    mock_chunk3.choices[0].delta.content = None

    mock_response = [mock_chunk1, mock_chunk2, mock_chunk3]

    # Test the helper method
    result = list(BaseChatProvider._handle_openai_streaming_response(mock_response))

    assert result == ["Hello", " world"]
    print("✓ Streaming response handler works correctly")


def test_handle_openai_streaming_response_resilience():
    """Test that streaming handler is resilient to malformed chunks."""
    # Create response with some malformed chunks
    mock_chunk1 = Mock()
    mock_chunk1.choices = [Mock()]
    mock_chunk1.choices[0].delta = Mock()
    mock_chunk1.choices[0].delta.content = "Good"

    # Malformed chunk - accessing delta.content will raise AttributeError
    mock_chunk2 = Mock()
    mock_chunk2.choices = [Mock()]
    mock_chunk2.choices[0].delta = Mock(spec=[])  # Empty spec means no attributes

    mock_chunk3 = Mock()
    mock_chunk3.choices = [Mock()]
    mock_chunk3.choices[0].delta = Mock()
    mock_chunk3.choices[0].delta.content = " data"

    mock_response = [mock_chunk1, mock_chunk2, mock_chunk3]

    # Should not raise, should skip malformed chunk
    result = list(BaseChatProvider._handle_openai_streaming_response(mock_response))

    # Both good chunks should be returned (malformed chunk is skipped or yields nothing)
    assert "Good" in result
    assert " data" in result
    print("✓ Streaming handler is resilient to malformed chunks")


def test_handle_openai_non_streaming_response():
    """Test that non-streaming response handler correctly extracts content."""
    # Create mock non-streaming response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Complete response"

    result = BaseChatProvider._handle_openai_non_streaming_response(mock_response)

    assert result == "Complete response"
    print("✓ Non-streaming response handler works correctly")


def test_handle_openai_non_streaming_response_empty():
    """Test that non-streaming handler returns empty string for None content."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = None

    result = BaseChatProvider._handle_openai_non_streaming_response(mock_response)

    assert result == ""
    print("✓ Non-streaming handler handles None content")


def test_handle_openai_non_streaming_response_resilience():
    """Test that non-streaming handler is resilient to malformed response."""
    # Malformed response - missing structure
    mock_response = Mock()
    # No choices attribute - should be caught by exception handler

    result = BaseChatProvider._handle_openai_non_streaming_response(mock_response)

    assert result == ""
    print("✓ Non-streaming handler is resilient to errors")


if __name__ == "__main__":
    print("Testing refactored provider response handling...\n")

    test_handle_openai_streaming_response()
    test_handle_openai_streaming_response_resilience()
    test_handle_openai_non_streaming_response()
    test_handle_openai_non_streaming_response_empty()
    test_handle_openai_non_streaming_response_resilience()

    print("\n✅ All provider response handling tests passed!")
