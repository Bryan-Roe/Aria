"""
LM Studio MCP Server

A Model Context Protocol (MCP) server for interacting with LM Studio,
a local LLM server that provides an OpenAI-compatible API.

Exposes tools for:
- Listing available models
- Sending chat completions
- Checking server status
"""

__version__ = "0.1.0"
__author__ = "Aria Team"
__license__ = "MIT"

try:
    from lmstudio_mcp_server import LMStudioClient, get_client

    __all__ = ["LMStudioClient", "get_client"]
except ImportError:
    __all__ = []
