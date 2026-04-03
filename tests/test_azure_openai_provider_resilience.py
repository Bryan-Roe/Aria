"""Unit tests for AzureOpenAIProvider payload sanitization in chat_providers."""

from __future__ import annotations

import importlib
import unittest.mock
from typing import Any

import pytest

chat_providers: Any = importlib.import_module("chat_providers")


def _make_azure_provider(fake_client):
    """Return an AzureOpenAIProvider with a mocked SDK client."""
    provider = object.__new__(chat_providers.AzureOpenAIProvider)
    provider.client = fake_client
    provider.deployment = "gpt-azure-test"
    provider.temperature = 0.7
    provider.max_output_tokens = None
    return provider


@pytest.mark.unit
def test_azure_openai_sanitizes_whitespace_only_text_blocks_before_sdk_call() -> None:
    """Whitespace-only text blocks should be removed before Azure SDK invocation."""
    fake_client = unittest.mock.MagicMock()
    mock_resp = unittest.mock.MagicMock()
    mock_resp.choices[0].message.content = "ok"
    fake_client.chat.completions.create.return_value = mock_resp

    provider = _make_azure_provider(fake_client)
    result = provider.complete(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "  \n\t  "},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/azure.png"},
                    },
                    {"type": "text", "text": " keep this azure text "},
                ],
            }
        ],
        stream=False,
    )

    assert result == "ok"
    call_kwargs = fake_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-azure-test"
    assert call_kwargs["messages"] == [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/azure.png"},
                },
                {"type": "text", "text": "keep this azure text"},
            ],
        }
    ]


@pytest.mark.unit
def test_azure_openai_sanitizes_whitespace_only_input_text_blocks_before_sdk_call() -> (
    None
):
    """Whitespace-only input_text blocks should be removed before Azure SDK invocation."""
    fake_client = unittest.mock.MagicMock()
    mock_resp = unittest.mock.MagicMock()
    mock_resp.choices[0].message.content = "ok"
    fake_client.chat.completions.create.return_value = mock_resp

    provider = _make_azure_provider(fake_client)
    result = provider.complete(
        [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "  \n\t  "},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/azure.png"},
                    },
                    {"type": "input_text", "text": " keep this azure too "},
                ],
            }
        ],
        stream=False,
    )

    assert result == "ok"
    call_kwargs = fake_client.chat.completions.create.call_args[1]
    assert call_kwargs["messages"] == [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/azure.png"},
                },
                {"type": "input_text", "text": "keep this azure too"},
            ],
        }
    ]
