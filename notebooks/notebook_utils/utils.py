"""Utility helpers for randomness, directories, and JSON I/O."""

import json
import random
from pathlib import Path
from typing import TypeAlias

import numpy as np

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def set_seed(s: int | None) -> None:
    """Seed Python and NumPy random number generators."""
    random.seed(s)
    np.random.seed(s)


def ensure_dir(p: str | Path) -> None:
    """Create a directory path if it does not already exist."""
    Path(p).mkdir(parents=True, exist_ok=True)


def save_json(path: str | Path, obj: JsonValue) -> None:
    """Save an object as formatted JSON using UTF-8."""
    path_obj = Path(path)
    json_text: str = json.dumps(obj, indent=2)
    path_obj.write_text(json_text, encoding="utf-8")


def load_json(path: str | Path) -> JsonValue:
    """Load and return JSON content from a UTF-8 encoded file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
