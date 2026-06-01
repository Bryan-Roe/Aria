from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ServerValidationResult:
    name: str
    ok: bool
    detail: str
    tool_names: list[str]


@dataclass
class LocalStdioServerParameters:
    command: str
    args: list[str]
    env: dict[str, str]
    cwd: str


def strip_jsonc_comments(text: str) -> str:
    result: list[str] = []
    in_string = False
    escape = False
    index = 0

    while index < len(text):
        char = text[index]

        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue

        if char == "/" and index + 1 < len(text) and text[index + 1] == "/":
            while index < len(text) and text[index] != "\n":
                index += 1
            continue

        result.append(char)
        index += 1

    return "".join(result)


def resolve_workspace_value(value: str, workspace: Path) -> str:
    return value.replace("${workspaceFolder}", str(workspace))


def load_mcp_config(config_path: Path) -> dict[str, Any]:
    text = config_path.read_text(encoding="utf-8")
    return json.loads(strip_jsonc_comments(text))


def build_server_params(
    workspace: Path,
    server_config: dict[str, Any],
) -> Any:
    command = resolve_workspace_value(server_config["command"], workspace)
    args = [
        resolve_workspace_value(arg, workspace)
        for arg in server_config.get("args", [])
    ]
    env = {
        key: resolve_workspace_value(value, workspace)
        for key, value in server_config.get("env", {}).items()
    }
    cwd = resolve_workspace_value(
        server_config.get("cwd", str(workspace)), workspace
    )
    return LocalStdioServerParameters(
        command=command,
        args=args,
        env=env,
        cwd=cwd,
    )


async def validate_server(
    name: str,
    workspace: Path,
    server_config: dict[str, Any],
) -> ServerValidationResult:
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client
    except ImportError:
        return ServerValidationResult(
            name,
            False,
            "mcp package is not installed",
            [],
        )

    params = build_server_params(workspace, server_config)
    try:
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                detail = f"{len(tool_names)} tools: {', '.join(tool_names)}"
                return ServerValidationResult(name, True, detail, tool_names)
    except Exception as exc:
        return ServerValidationResult(name, False, str(exc), [])


async def validate_servers(
    workspace: Path,
    config_path: Path,
    only_server: str | None = None,
) -> list[ServerValidationResult]:
    config = load_mcp_config(config_path)
    servers = config.get("servers", {})
    results: list[ServerValidationResult] = []

    for name, server_config in servers.items():
        if only_server and name != only_server:
            continue
        results.append(await validate_server(name, workspace, server_config))

    return results


def results_to_json(results: list[ServerValidationResult]) -> dict[str, Any]:
    return {
        "summary": {
            "total": len(results),
            "ok": sum(1 for result in results if result.ok),
            "fail": sum(1 for result in results if not result.ok),
            "all_ok": all(result.ok for result in results),
        },
        "servers": [asdict(result) for result in results],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate stdio MCP servers configured in .vscode/mcp.json"
    )
    parser.add_argument(
        "--config",
        default=".vscode/mcp.json",
        help="Path to MCP config file",
    )
    parser.add_argument(
        "--server",
        help="Validate only a single configured server by name",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON output instead of plain text",
    )
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()
    workspace = Path(__file__).resolve().parents[1]
    config_path = (workspace / args.config).resolve()
    results = await validate_servers(workspace, config_path, args.server)

    if not results:
        if args.json:
            print(
                json.dumps(
                    {
                        "summary": {
                            "total": 0,
                            "ok": 0,
                            "fail": 0,
                            "all_ok": False,
                        },
                        "servers": [],
                        "error": (
                            "No MCP servers matched the requested selection."
                        ),
                    },
                    indent=2,
                )
            )
        else:
            print("No MCP servers matched the requested selection.")
        return 1

    if args.json:
        print(json.dumps(results_to_json(results), indent=2))
        return 1 if any(not result.ok for result in results) else 0

    failures = 0
    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"{result.name}: {status} - {result.detail}")
        if not result.ok:
            failures += 1

    return 1 if failures else 0


def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())
