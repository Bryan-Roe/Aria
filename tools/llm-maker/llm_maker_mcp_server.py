"""
LLM Maker MCP Server
Exposes tool creation and execution capabilities via Model Context Protocol
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import MCP dependencies
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool as MCPTool, TextContent
except ImportError as e:
    print("Error: MCP package not installed.")
    print("\nTo install MCP dependencies, run:")
    print("  pip install -r requirements.txt")
    print(f"\nDetails: {e}")
    sys.exit(1)

# Import LLM Maker components
from src.tool_maker import ToolMaker
from src.tool_validator import ToolValidator
from src.tool_executor import ToolExecutor
from src.tool_registry import ToolRegistry, Tool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
app = Server("llm-maker-mcp")
maker = ToolMaker()
validator = ToolValidator()
executor = ToolExecutor()
registry = ToolRegistry()


@app.list_tools()
async def list_tools() -> list[MCPTool]:
    """List available MCP tools"""
    return [
        MCPTool(
            name="create_tool",
            description="Create a new Python tool from natural language description",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Function name (valid Python identifier)"
                    },
                    "description": {
                        "type": "string",
                        "description": "What the tool should do"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameter names and types (e.g., {'n': 'int', 'text': 'str'})"
                    },
                    "return_type": {
                        "type": "string",
                        "description": "Expected return type",
                        "default": "Any"
                    },
                    "examples": {
                        "type": "array",
                        "description": "Optional list of example inputs/outputs",
                        "items": {"type": "object"}
                    }
                },
                "required": ["name", "description", "parameters"]
            }
        ),
        MCPTool(
            name="execute_tool",
            description="Execute a registered tool with given arguments",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_id": {
                        "type": "string",
                        "description": "Tool ID or name"
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Arguments to pass to the tool"
                    }
                },
                "required": ["tool_id", "arguments"]
            }
        ),
        MCPTool(
            name="list_registered_tools",
            description="List all registered tools in the registry",
            inputSchema={
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "description": "Optional filter by tags",
                        "items": {"type": "string"}
                    }
                }
            }
        ),
        MCPTool(
            name="get_tool",
            description="Get details of a specific tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_id": {
                        "type": "string",
                        "description": "Tool ID or name"
                    }
                },
                "required": ["tool_id"]
            }
        ),
        MCPTool(
            name="delete_tool",
            description="Delete a tool from the registry",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_id": {
                        "type": "string",
                        "description": "Tool ID to delete"
                    }
                },
                "required": ["tool_id"]
            }
        ),
        MCPTool(
            name="validate_tool",
            description="Validate a tool for safety",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_id": {
                        "type": "string",
                        "description": "Tool ID or name"
                    }
                },
                "required": ["tool_id"]
            }
        ),
        MCPTool(
            name="registry_stats",
            description="Get statistics about the tool registry",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "create_tool":
            return await handle_create_tool(arguments)
        elif name == "execute_tool":
            return await handle_execute_tool(arguments)
        elif name == "list_registered_tools":
            return await handle_list_tools(arguments)
        elif name == "get_tool":
            return await handle_get_tool(arguments)
        elif name == "delete_tool":
            return await handle_delete_tool(arguments)
        elif name == "validate_tool":
            return await handle_validate_tool(arguments)
        elif name == "registry_stats":
            return await handle_registry_stats(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error handling {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_create_tool(args: dict) -> list[TextContent]:
    """Handle create_tool command"""
    name = args["name"]
    description = args["description"]
    parameters = args["parameters"]
    return_type = args.get("return_type", "Any")
    examples = args.get("examples", [])
    
    logger.info(f"Creating tool: {name}")
    
    tool = maker.create_tool(
        name=name,
        description=description,
        parameters=parameters,
        return_type=return_type,
        examples=examples
    )
    
    if tool:
        tool_id = registry.register(tool)
        result = {
            "success": True,
            "tool_id": tool_id,
            "name": tool.name,
            "message": f"Tool '{name}' created and registered successfully",
            "code": tool.code
        }
    else:
        result = {
            "success": False,
            "error": "Failed to create tool - validation errors or generation failure"
        }
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_execute_tool(args: dict) -> list[TextContent]:
    """Handle execute_tool command"""
    tool_id = args["tool_id"]
    arguments = args["arguments"]
    
    # Get tool by ID or name
    tool = registry.get(tool_id)
    if not tool:
        tool = registry.get_by_name(tool_id)
    
    if not tool:
        result = {"success": False, "error": f"Tool '{tool_id}' not found"}
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    logger.info(f"Executing tool: {tool.name}")
    
    # Execute the tool
    exec_result = executor.execute(tool.code, tool.name, arguments)
    
    # Update statistics
    if exec_result.get("success"):
        registry.update_stats(tool.id)
    
    return [TextContent(type="text", text=json.dumps(exec_result, indent=2))]


async def handle_list_tools(args: dict) -> list[TextContent]:
    """Handle list_registered_tools command"""
    tags = args.get("tags", None)
    
    tools = registry.list_tools(tags=tags)
    
    result = {
        "count": len(tools),
        "tools": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "return_type": t.return_type,
                "validated": t.validated,
                "execution_count": t.execution_count,
                "created_at": t.created_at
            }
            for t in tools
        ]
    }
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_get_tool(args: dict) -> list[TextContent]:
    """Handle get_tool command"""
    tool_id = args["tool_id"]
    
    tool = registry.get(tool_id)
    if not tool:
        tool = registry.get_by_name(tool_id)
    
    if not tool:
        result = {"success": False, "error": f"Tool '{tool_id}' not found"}
    else:
        result = {
            "success": True,
            "tool": tool.to_dict()
        }
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_delete_tool(args: dict) -> list[TextContent]:
    """Handle delete_tool command"""
    tool_id = args["tool_id"]
    
    success = registry.delete(tool_id)
    
    result = {
        "success": success,
        "message": f"Tool deleted" if success else f"Tool '{tool_id}' not found"
    }
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_validate_tool(args: dict) -> list[TextContent]:
    """Handle validate_tool command"""
    tool_id = args["tool_id"]
    
    tool = registry.get(tool_id)
    if not tool:
        tool = registry.get_by_name(tool_id)
    
    if not tool:
        result = {"success": False, "error": f"Tool '{tool_id}' not found"}
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    is_valid, errors = validator.validate(tool.code)
    
    result = {
        "tool_id": tool.id,
        "tool_name": tool.name,
        "is_valid": is_valid,
        "errors": errors if not is_valid else []
    }
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_registry_stats(args: dict) -> list[TextContent]:
    """Handle registry_stats command"""
    stats = registry.get_stats()
    return [TextContent(type="text", text=json.dumps(stats, indent=2))]


async def main():
    """Run the MCP server"""
    logger.info("Starting LLM Maker MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
