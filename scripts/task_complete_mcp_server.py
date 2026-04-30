#!/usr/bin/env python3
"""Minimal MCP server providing a task_complete tool."""
import json
import sys


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        method = msg.get("method", "")
        msg_id = msg.get("id")

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "task-complete-server", "version": "1.0.0"},
                },
            }
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "task_complete",
                            "description": "Mark the current task as complete. Call this when all work is done.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "summary": {
                                        "type": "string",
                                        "description": "Brief summary of what was completed",
                                    }
                                },
                                "required": [],
                            },
                        }
                    ]
                },
            }
        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            if tool_name == "task_complete":
                summary = args.get("summary", "Task marked complete.")
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": f"task_complete: {summary}"}
                        ],
                        "isError": False,
                    },
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                }
        elif method == "notifications/initialized":
            continue
        else:
            if msg_id is not None:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            else:
                continue

        print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()
