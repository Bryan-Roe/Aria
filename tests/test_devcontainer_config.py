from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_DEVCONTAINER_DIR = Path(__file__).resolve().parents[1] / ".devcontainer"


def test_devcontainer_json_is_valid_json() -> None:
    """devcontainer.json must be valid JSON; the @devcontainers/cli parses it with JSON.parse()."""
    config_path = _DEVCONTAINER_DIR / "devcontainer.json"
    content = config_path.read_text(encoding="utf-8")
    try:
        json.loads(content)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f".devcontainer/devcontainer.json is not valid JSON: {exc}\n"
            "This will cause `devcontainer build` (and the build-and-test CI job) to fail."
        )


def test_devcontainer_lock_json_is_valid_json() -> None:
    """devcontainer-lock.json must be valid JSON with no trailing data.

    A stray closing brace after the root object caused:
        SyntaxError: Unexpected non-whitespace character after JSON at position 2143
    which broke the build-and-test devcontainer CI job.
    """
    lock_path = _DEVCONTAINER_DIR / "devcontainer-lock.json"
    if not lock_path.exists():
        pytest.skip("devcontainer-lock.json not present")
    content = lock_path.read_text(encoding="utf-8")
    try:
        json.loads(content)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f".devcontainer/devcontainer-lock.json is not valid JSON: {exc}\n"
            "Trailing or extra characters after the root object will cause "
            "`devcontainer build` (and the build-and-test CI job) to fail."
        )


def _assert_no_trailing_data(path: Path, content: str) -> None:
    """Assert that *content* contains a single JSON value with only whitespace after it.

    Uses ``JSONDecoder.raw_decode()`` which returns the end-position of the
    parsed value.  Anything remaining after that position (beyond whitespace)
    is trailing data and indicates a corrupted file.
    """
    decoder = json.JSONDecoder()
    try:
        _parsed, end_index = decoder.raw_decode(content)
    except json.JSONDecodeError as exc:
        pytest.fail(f"{path.name} is not valid JSON: {exc}")

    trailing = content[end_index:]
    assert trailing.strip() == "", (
        f"{path.name} has trailing non-whitespace data after the root JSON object "
        f"(at offset {end_index}): {trailing!r}\n"
        "This will cause `devcontainer build` to fail with a SyntaxError."
    )


def test_devcontainer_json_no_trailing_data() -> None:
    """Ensure no extra characters appear after the root JSON object in devcontainer.json."""
    config_path = _DEVCONTAINER_DIR / "devcontainer.json"
    content = config_path.read_text(encoding="utf-8")
    _assert_no_trailing_data(config_path, content)


def test_devcontainer_lock_json_no_trailing_data() -> None:
    """Ensure no extra characters appear after the root JSON object in devcontainer-lock.json.

    Regression test for the stray ``  }`` that caused:
        SyntaxError: Unexpected non-whitespace character after JSON at position 2143
    in CI job 86511118286.
    """
    lock_path = _DEVCONTAINER_DIR / "devcontainer-lock.json"
    if not lock_path.exists():
        pytest.skip("devcontainer-lock.json not present")
    content = lock_path.read_text(encoding="utf-8")
    _assert_no_trailing_data(lock_path, content)


def test_nested_duplicate_tests_have_package_scope() -> None:
    """Nested duplicate test filenames must live in packages to avoid pytest import mismatches."""
    tests_dir = Path(__file__).resolve().parent
    grouped_paths: dict[str, list[Path]] = {}

    for path in tests_dir.rglob("test_*.py"):
        grouped_paths.setdefault(path.name, []).append(path)

    duplicate_groups = [paths for paths in grouped_paths.values() if len(paths) > 1]
    for paths in duplicate_groups:
        for path in paths:
            if path.parent == tests_dir:
                continue
            assert (path.parent / "__init__.py").exists(), (
                f"{path.relative_to(tests_dir)} duplicates a test module basename and must stay in a package "
                "to avoid pytest collection import mismatches in CI."
            )
