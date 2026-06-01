from pathlib import Path

from scripts.validate_mcp_setup import (
    build_server_params,
    load_mcp_config,
    resolve_workspace_value,
    results_to_json,
    ServerValidationResult,
    strip_jsonc_comments,
)


def test_strip_jsonc_comments_preserves_urls_and_strings():
    text = """
    {
      // comment
      "url": "http://127.0.0.1:11434/v1",
      "label": "value // still string"
    }
    """

    cleaned = strip_jsonc_comments(text)

    assert "comment" not in cleaned
    assert "http://127.0.0.1:11434/v1" in cleaned
    assert "value // still string" in cleaned


def test_load_mcp_config_parses_workspace_config():
    config = load_mcp_config(Path("/workspaces/Aria/.vscode/mcp.json"))

    assert "servers" in config
    assert "quantum-ai" in config["servers"]
    assert "llm-maker" in config["servers"]


def test_resolve_workspace_value_substitutes_workspace_folder():
    workspace = Path("/tmp/example-workspace")

    assert (
        resolve_workspace_value(
            "${workspaceFolder}/scripts/tool.py", workspace
        )
        == "/tmp/example-workspace/scripts/tool.py"
    )


def test_build_server_params_resolves_command_args_env_and_cwd():
    workspace = Path("/tmp/example-workspace")
    params = build_server_params(
        workspace,
        {
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": ["${workspaceFolder}/scripts/task_complete_mcp_server.py"],
            "env": {
                "PYTHONPATH": "${workspaceFolder}/scripts:${workspaceFolder}"
            },
            "cwd": "${workspaceFolder}/scripts",
        },
    )

    assert params.command == "/tmp/example-workspace/.venv/bin/python"
    assert params.args == [
        "/tmp/example-workspace/scripts/task_complete_mcp_server.py"
    ]
    assert params.env == {
        "PYTHONPATH": "/tmp/example-workspace/scripts:/tmp/example-workspace"
    }
    assert params.cwd == "/tmp/example-workspace/scripts"


def test_results_to_json_summarizes_validation_results():
    report = results_to_json(
        [
            ServerValidationResult(
                name="quantum-ai",
                ok=True,
                detail="8 tools: create_quantum_circuit",
                tool_names=["create_quantum_circuit"],
            ),
            ServerValidationResult(
                name="llm-maker",
                ok=False,
                detail="handshake error",
                tool_names=[],
            ),
        ]
    )

    assert report["summary"] == {
        "total": 2,
        "ok": 1,
        "fail": 1,
        "all_ok": False,
    }
    assert report["servers"][0]["name"] == "quantum-ai"
    assert report["servers"][1]["detail"] == "handshake error"
