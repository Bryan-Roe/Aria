from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPO_ROOT / "ai-projects" / "writer-reviewer-workflow"
PROTOTYPE_MODULE = WORKFLOW_ROOT / "prototype_workflow.py"
MAIN_SCRIPT = WORKFLOW_ROOT / "main.py"


def _load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_request(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "module_name": "string_tools",
                "function_name": "join_with_dash",
                "description": "Join two strings with a dash.",
                "arguments": [
                    {"name": "left", "type": "str"},
                    {"name": "right", "type": "str"},
                ],
                "return_type": "str",
                "expression": "f'{left}-{right}'",
                "examples": [
                    {
                        "inputs": {"left": "alpha", "right": "beta"},
                        "output": "alpha-beta",
                    },
                    {
                        "inputs": {"left": "aria", "right": "repo"},
                        "output": "aria-repo",
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.mark.unit
def test_folder_monitor_generates_module_tests_and_report(tmp_path: Path) -> None:
    prototype = _load_module(PROTOTYPE_MODULE, "writer_reviewer_prototype")
    workflow = prototype.FolderMonitorWorkflow(
        watch_dir=tmp_path / "inbox",
        output_dir=tmp_path / "generated",
        run_generated_tests=False,
    )

    request_path = workflow.watch_dir / "join_request.json"
    _write_request(request_path)

    results = workflow.run_once()

    assert len(results) == 1
    result = results[0]
    assert result.module_path.exists()
    assert result.test_path.exists()
    assert result.report_path.exists()
    assert result.processed_path.exists()
    assert not request_path.exists()

    generated = _load_module(result.module_path, "generated_string_tools")
    assert generated.join_with_dash("a", "b") == "a-b"

    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["module_path"].endswith("string_tools.py")


@pytest.mark.unit
def test_main_prototype_run_once_generates_testable_code(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    output_dir = tmp_path / "out"
    inbox.mkdir(parents=True, exist_ok=True)
    _write_request(inbox / "dynamic_request.json")

    proc = subprocess.run(
        [
            sys.executable,
            str(MAIN_SCRIPT),
            "--prototype-monitor",
            "--prototype-run-once",
            "--prototype-watch-dir",
            str(inbox),
            "--prototype-output-dir",
            str(output_dir),
            "--prototype-run-generated-tests",
        ],
        cwd=WORKFLOW_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    assert "Processed 1 request(s)." in proc.stdout
    assert (output_dir / "src" / "string_tools.py").exists()
    assert (output_dir / "tests" / "test_string_tools.py").exists()
    assert (inbox / "archive" / "processed" / "dynamic_request.json").exists()
