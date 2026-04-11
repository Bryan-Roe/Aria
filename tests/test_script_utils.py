"""Test suite for shared/script_utils.py.

Tests cover get_repo_root, setup_path, and get_data_out_dir.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


from shared.script_utils import get_data_out_dir, get_repo_root, setup_path

# ---------------------------------------------------------------------------
# get_repo_root
# ---------------------------------------------------------------------------


class TestGetRepoRoot:
    def test_without_script_file_returns_repo_root(self):
        """Called without argument, returns parent of the shared/ directory."""
        root = get_repo_root()
        # shared/ lives directly in the repo root
        assert (root / "shared").is_dir()

    def test_with_script_file_from_scripts_dir(self, tmp_path):
        """A file inside a scripts/ subdirectory should give tmp_path as root."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        fake_script = scripts_dir / "my_script.py"
        fake_script.write_text("# script", encoding="utf-8")
        root = get_repo_root(str(fake_script))
        assert root == tmp_path

    def test_returns_path_object(self):
        """
        Verifies that get_repo_root() returns an object of type Path.
        """
        root = get_repo_root()
        assert isinstance(root, Path)

    def test_with_script_file_path_object(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        fake_script = scripts_dir / "my_script.py"
        fake_script.write_text("# script", encoding="utf-8")
        root = get_repo_root(fake_script)
        assert root == tmp_path


# ---------------------------------------------------------------------------
# setup_path
# ---------------------------------------------------------------------------


class TestSetupPath:
    def test_adds_repo_root_to_sys_path(self):
        root = setup_path()
        root_str = str(root)
        assert root_str in sys.path

    def test_returns_repo_root(self):
        root = setup_path()
        assert isinstance(root, Path)
        assert (root / "shared").is_dir()

    def test_idempotent_when_root_already_in_path(self):
        """Calling setup_path twice should not duplicate the entry."""
        root = setup_path()
        root_str = str(root)
        count_before = sys.path.count(root_str)
        setup_path()
        count_after = sys.path.count(root_str)
        assert count_after == count_before

    def test_adds_additional_paths(self, tmp_path, monkeypatch):
        """Additional relative paths should appear in sys.path."""
        # Use a temporary directory as a fake repo root to keep the test isolated
        extras_dir = tmp_path / "extras"
        extras_dir.mkdir()
        monkeypatch.setattr(
            "shared.script_utils.get_repo_root", lambda *args, **kwargs: tmp_path
        )
        monkeypatch.setattr(
            "shared.script_utils.get_repo_root", lambda *_args, **_kwargs: tmp_path
        )
        result = setup_path(None, "extras")
        expected = str(extras_dir)
        assert expected in sys.path

    def test_script_file_variant_returns_root(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        fake_script = scripts_dir / "my_script.py"
        fake_script.write_text("# script", encoding="utf-8")
        # When the result points at a temp dir, sys.path mutation is fine
        result = setup_path(str(fake_script))
        assert result == tmp_path


# ---------------------------------------------------------------------------
# get_data_out_dir
# ---------------------------------------------------------------------------


class TestGetDataOutDir:
    def test_defaults_to_script_stem(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        fake_script = scripts_dir / "my_pipeline.py"
        fake_script.write_text("# script", encoding="utf-8")
        out = get_data_out_dir(str(fake_script))
        assert out == tmp_path / "data_out" / "my_pipeline"

    def test_custom_subdir(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        fake_script = scripts_dir / "my_pipeline.py"
        fake_script.write_text("# script", encoding="utf-8")
        out = get_data_out_dir(str(fake_script), "custom_name")
        assert out == tmp_path / "data_out" / "custom_name"

    def test_returns_path_object(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        fake_script = scripts_dir / "pipe.py"
        fake_script.write_text("# s", encoding="utf-8")
        out = get_data_out_dir(str(fake_script))
        assert isinstance(out, Path)

    def test_does_not_create_directory(self, tmp_path):
        """get_data_out_dir should only compute the path, not create it."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        fake_script = scripts_dir / "pipe.py"
        fake_script.write_text("# s", encoding="utf-8")
        out = get_data_out_dir(str(fake_script))
        assert not out.exists()
