#!/usr/bin/env python3
"""
LM Studio MCP Server
Exposes LM Studio local model server via Model Context Protocol

Provides tools for:
- Querying available models
- Sending chat completions to local LM Studio instance
- Managing model context and parameters
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError as e:
    print("Error: MCP package not installed.")
    print("Install with: pip install 'mcp>=0.9.0'")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("Error: httpx package not installed.")
    print("Install with: pip install httpx")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("lmstudio-mcp")

# Default configuration
DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1"
DEFAULT_MODEL = "local-model"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048


class LMStudioClient:
    """Client for interacting with LM Studio local server."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def check_connection(self) -> bool:
        """Check if LM Studio server is reachable."""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False

    async def list_models(self) -> Dict[str, Any]:
        """List available models on LM Studio server."""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            data = response.json()

            models = data.get("data", [])
            model_names = [m.get("id", "unknown") for m in models]

            return {
                "success": True,
                "available_models": model_names,
                "total_models": len(model_names),
                "response": data,
            }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e}",
                "available_models": [],
            }
        except Exception as e:
            return {"success": False, "error": str(e), "available_models": []}

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Send a chat completion request to LM Studio."""
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            if stream:
                # For streaming, return the raw response data
                return {
                    "success": True,
                    "stream": True,
                    "response": data,
                    "model": model,
                }
            else:
                # Extract the message from non-streaming response
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {}).get("content", "")
                stop_reason = choice.get("finish_reason", "unknown")

                return {
                    "success": True,
                    "stream": False,
                    "message": message,
                    "stop_reason": stop_reason,
                    "model": model,
                    "usage": data.get("usage", {}),
                    "response": data,
                }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e}",
                "model": model,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "model": model}

    async def get_server_status(self) -> Dict[str, Any]:
        """Get server status information."""
        try:
            # Try to get models as a status check
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            data = response.json()
            models_count = len(data.get("data", []))

            return {
                "success": True,
                "status": "online",
                "base_url": self.base_url,
                "loaded_models": models_count,
                "current_model": self.model,
            }
        except Exception as e:
            return {
                "success": False,
                "status": "offline",
                "error": str(e),
                "base_url": self.base_url,
            }


# Global client instance
_client: Optional[LMStudioClient] = None


def get_client() -> LMStudioClient:
    """Get or create the global LM Studio client."""
    global _client
    if _client is None:
        base_url = os.getenv("LMSTUDIO_BASE_URL", DEFAULT_BASE_URL)
        model = os.getenv("LMSTUDIO_MODEL", DEFAULT_MODEL)
        temperature = float(os.getenv("LMSTUDIO_TEMPERATURE", DEFAULT_TEMPERATURE))
        max_tokens = int(os.getenv("LMSTUDIO_MAX_TOKENS", DEFAULT_MAX_TOKENS))

        _client = LMStudioClient(
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    return _client


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="list_models",
            description="List all available models on the LM Studio server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="chat_completion",
            description="Send a chat completion request to LM Studio",
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "enum": ["system", "user", "assistant"],
                                    "description": "Message role",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Message content",
                                },
                            },
                            "required": ["role", "content"],
                        },
                        "description": "List of messages for the chat",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model ID (uses default if not specified)",
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Sampling temperature (0.0-2.0, default 0.7)",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens in response (default 2048)",
                    },
                },
                "required": ["messages"],
            },
        ),
        Tool(
            name="server_status",
            description="Get LM Studio server status and configuration",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Call a tool."""
    client = get_client()

    try:
        if name == "list_models":
            result = await client.list_models()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "chat_completion":
            messages = arguments.get("messages", [])
            if not messages:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": "No messages provided"}, indent=2),
                    )
                ]

            model = arguments.get("model")
            temperature = arguments.get("temperature")
            max_tokens = arguments.get("max_tokens")

            result = await client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "server_status":
            result = await client.get_server_status()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2),
                )
            ]

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2),
            )
        ]


async def main():
    """Run the MCP server."""
    client = get_client()

    # Check connection on startup
    logger.info(f"Connecting to LM Studio at {client.base_url}")
    connected = await client.check_connection()

    if connected:
        logger.info("✓ Successfully connected to LM Studio")
        models = await client.list_models()
        logger.info(f"✓ Available models: {models.get('available_models', [])}")
    else:
        logger.warning(f"⚠ Could not connect to LM Studio at {client.base_url}")
        logger.info("Make sure LM Studio is running and the local server is enabled.")

    # Start MCP server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down LM Studio MCP server")
        sys.exit(0)
