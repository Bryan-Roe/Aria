#!/usr/bin/env python
"""
Shared utilities for script setup and common patterns.

This module provides common functionality used across multiple scripts
to reduce code duplication:
- Repository path detection and setup
- Argument parsing helpers
- Common script patterns
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def get_repo_root(script_file: Optional[str] = None) -> Path:
    """
    Get the repository root directory.

    Args:
        script_file: Optional __file__ value from the calling script.
                    If not provided, uses this module's location.

    Returns:
        Path to the repository root directory

    Examples:
        # From a script in scripts/ directory
        repo_root = get_repo_root(__file__)

        # Auto-detect from this module
        repo_root = get_repo_root()
    """
    if script_file:
        # Script is in scripts/ subdirectory, parent is repo root
        script_path = Path(script_file).resolve()
        return script_path.parent.parent
    else:
        # This file is in shared/ subdirectory, parent is repo root
        return Path(__file__).resolve().parent.parent


def setup_path(script_file: Optional[str] = None, *additional_paths: str) -> Path:
    """
    Setup sys.path to include repository root and optional additional paths.

    This ensures imports from shared/ and other top-level modules work correctly.

    Args:
        script_file: Optional __file__ value from the calling script
        *additional_paths: Additional relative paths to add (from repo root)

    Returns:
        Path to the repository root directory

    Examples:
        # Add repo root to path
        repo_root = setup_path(__file__)

        # Add repo root and specific subdirectory
        repo_root = setup_path(__file__, "ai-projects/quantum-ml/src")

        # Then import from shared
        from shared.evaluation_utils import load_jsonl
    """
    repo_root = get_repo_root(script_file)

    # Add repo root if not already in path
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    # Add additional paths
    for rel_path in additional_paths:
        full_path = str(repo_root / rel_path)
        if full_path not in sys.path:
            sys.path.insert(0, full_path)

    return repo_root


def get_data_out_dir(script_file: str, subdir: Optional[str] = None) -> Path:
    """
    Get the standard data_out directory for a script's outputs.

    Args:
        script_file: __file__ value from the calling script
        subdir: Optional subdirectory name (defaults to script name without .py)

    Returns:
        Path to the data_out directory for this script

    Examples:
        # Creates data_out/my_script/
        output_dir = get_data_out_dir(__file__)

        # Creates data_out/custom_name/
        output_dir = get_data_out_dir(__file__, "custom_name")
    """
    repo_root = get_repo_root(script_file)
    script_name = Path(script_file).stem

    if subdir is None:
        subdir = script_name

    output_dir = repo_root / "data_out" / subdir
    return output_dir
