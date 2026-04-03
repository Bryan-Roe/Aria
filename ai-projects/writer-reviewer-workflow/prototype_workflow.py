"""Operational prototype workflow for dynamic code generation.

This module provides a lightweight Python automation loop that watches a folder
for JSON request files, generates Python modules plus pytest tests, and archives
processed requests with a machine-readable report.

The prototype is intentionally deterministic so it is easy to test locally and
does not require Azure or model credentials.
"""

from __future__ import annotations

import json
import keyword
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _sanitize_identifier(value: str, *, fallback: str) -> str:
    """Convert free-form text into a safe Python identifier."""
    text = re.sub(r"\W+", "_", value.strip().lower()).strip("_")
    if not text:
        text = fallback
    if text[0].isdigit():
        text = f"_{text}"
    if keyword.iskeyword(text):
        text = f"{text}_value"
    return text


def _python_literal(value: Any) -> str:
    return repr(value)


@dataclass(slots=True)
class FunctionArgument:
    name: str
    arg_type: str = "Any"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FunctionArgument":
        raw_name = str(payload.get("name", "arg")).strip()
        return cls(
            name=_sanitize_identifier(raw_name, fallback="arg"),
            arg_type=str(payload.get("type", "Any")).strip() or "Any",
        )


@dataclass(slots=True)
class PrototypeRequest:
    module_name: str
    function_name: str
    description: str
    expression: str
    arguments: list[FunctionArgument] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)
    return_type: str = "Any"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PrototypeRequest":
        module_name = _sanitize_identifier(
            str(payload.get("module_name", "generated_module")),
            fallback="generated_module",
        )
        function_name = _sanitize_identifier(
            str(payload.get("function_name", "generated_function")),
            fallback="generated_function",
        )
        arguments = [
            FunctionArgument.from_dict(item)
            for item in payload.get("arguments", [])
            if isinstance(item, dict)
        ]
        if not arguments:
            arguments = [FunctionArgument(name="value", arg_type="Any")]

        examples = payload.get("examples", [])
        if not isinstance(examples, list):
            raise ValueError("examples must be a list of input/output objects")
        if not examples:
            raise ValueError("examples must include at least one input/output case")

        for example in examples:
            if not isinstance(example, dict):
                raise ValueError("each example must be an object")
            if "inputs" not in example or "output" not in example:
                raise ValueError("each example must contain 'inputs' and 'output'")

        expression = str(payload.get("expression", "")).strip()
        if not expression:
            raise ValueError("expression is required")

        return cls(
            module_name=module_name,
            function_name=function_name,
            description=str(payload.get("description", "Generated function")).strip()
            or "Generated function",
            expression=expression,
            arguments=arguments,
            examples=examples,
            return_type=str(payload.get("return_type", "Any")).strip() or "Any",
        )


@dataclass(slots=True)
class PrototypeGenerationResult:
    request_file: Path
    module_path: Path
    test_path: Path
    report_path: Path
    processed_path: Path
    passed_tests: bool


class FolderMonitorWorkflow:
    """Monitor a folder and generate testable Python code from JSON requests."""

    def __init__(
        self,
        watch_dir: str | Path,
        output_dir: str | Path,
        *,
        archive_dir: str | Path | None = None,
        run_generated_tests: bool = False,
        python_executable: str | None = None,
    ) -> None:
        self.watch_dir = Path(watch_dir)
        self.output_dir = Path(output_dir)
        self.archive_dir = (
            Path(archive_dir) if archive_dir else self.watch_dir / "archive"
        )
        self.run_generated_tests = run_generated_tests
        self.python_executable = python_executable or sys.executable

        self.src_dir = self.output_dir / "src"
        self.tests_dir = self.output_dir / "tests"
        self.reports_dir = self.output_dir / "reports"
        self.processed_dir = self.archive_dir / "processed"
        self.failed_dir = self.archive_dir / "failed"

        for directory in [
            self.watch_dir,
            self.src_dir,
            self.tests_dir,
            self.reports_dir,
            self.processed_dir,
            self.failed_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_request(self, spec_path: Path) -> PrototypeRequest:
        payload = json.loads(spec_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("request file must contain a JSON object")
        return PrototypeRequest.from_dict(payload)

    def _render_module(self, request: PrototypeRequest) -> str:
        args_signature = ", ".join(
            f"{arg.name}: {arg.arg_type}" for arg in request.arguments
        )
        return f'''"""Auto-generated module for {request.function_name}."""

from __future__ import annotations

from typing import Any


def {request.function_name}({args_signature}) -> {request.return_type}:
    """{request.description}"""
    return {request.expression}
'''

    def _render_tests(self, request: PrototypeRequest) -> str:
        cases_literal = ",\n    ".join(
            "("
            + _python_literal(example["inputs"])
            + ", "
            + _python_literal(example["output"])
            + ")"
            for example in request.examples
        )
        return f'''"""Auto-generated tests for {request.function_name}."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from {request.module_name} import {request.function_name}


@pytest.mark.parametrize(
    ("inputs", "expected"),
    [
    {cases_literal}
    ],
)
def test_{request.function_name}(inputs, expected):
    assert {request.function_name}(**inputs) == expected
'''

    def _run_pytest_for(self, test_path: Path) -> None:
        completed = subprocess.run(
            [self.python_executable, "-m", "pytest", str(test_path.resolve()), "-q"],
            cwd=self.output_dir,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"generated pytest failed for {test_path.name}: {completed.stdout}\n{completed.stderr}"
            )

    def process_request_file(self, spec_path: str | Path) -> PrototypeGenerationResult:
        spec_path = Path(spec_path)
        request = self._load_request(spec_path)

        module_path = self.src_dir / f"{request.module_name}.py"
        test_path = self.tests_dir / f"test_{request.module_name}.py"
        report_path = self.reports_dir / f"{request.module_name}.json"

        module_path.write_text(self._render_module(request), encoding="utf-8")
        test_path.write_text(self._render_tests(request), encoding="utf-8")

        compile(module_path.read_text(encoding="utf-8"), str(module_path), "exec")
        compile(test_path.read_text(encoding="utf-8"), str(test_path), "exec")

        if self.run_generated_tests:
            self._run_pytest_for(test_path)

        processed_path = self.processed_dir / spec_path.name
        shutil.move(str(spec_path), processed_path)

        report = {
            "request_file": str(processed_path),
            "module_path": str(module_path),
            "test_path": str(test_path),
            "run_generated_tests": self.run_generated_tests,
            "status": "passed",
            "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        return PrototypeGenerationResult(
            request_file=spec_path,
            module_path=module_path,
            test_path=test_path,
            report_path=report_path,
            processed_path=processed_path,
            passed_tests=self.run_generated_tests,
        )

    def _record_failure(self, spec_path: Path, exc: Exception) -> Path:
        failed_path = self.failed_dir / spec_path.name
        if spec_path.exists():
            shutil.move(str(spec_path), failed_path)
        report_path = self.reports_dir / f"{spec_path.stem}.error.json"
        report_path.write_text(
            json.dumps(
                {
                    "request_file": str(failed_path),
                    "status": "failed",
                    "error": str(exc),
                    "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return failed_path

    def run_once(self) -> list[PrototypeGenerationResult]:
        processed: list[PrototypeGenerationResult] = []
        for spec_path in sorted(self.watch_dir.glob("*.json")):
            try:
                processed.append(self.process_request_file(spec_path))
            except Exception as exc:
                self._record_failure(spec_path, exc)
        return processed

    def watch(
        self, poll_interval: float = 2.0, max_iterations: int | None = None
    ) -> int:
        iterations = 0
        processed_count = 0
        while True:
            processed_count += len(self.run_once())
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                return processed_count
            time.sleep(max(poll_interval, 0.1))
