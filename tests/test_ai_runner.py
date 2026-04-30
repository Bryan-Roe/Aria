"""Comprehensive tests for shared/ai_runner.py."""

from __future__ import annotations

import os
import re
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

import shared.ai_runner as ai_runner


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_chat_cli_path_defined(self):
        assert ai_runner.CHAT_CLI is not None
        assert isinstance(ai_runner.CHAT_CLI, Path)
        assert ai_runner.CHAT_CLI.name == "chat_cli.py"

    def test_log_dir_path_defined(self):
        assert ai_runner.LOG_DIR is not None
        assert isinstance(ai_runner.LOG_DIR, Path)

    def test_ansi_escape_regex_compiled(self):
        assert ai_runner._ANSI_ESCAPE_RE is not None
        # Verify it strips a known ANSI code
        result = ai_runner._ANSI_ESCAPE_RE.sub("", "\x1B[31mRed\x1B[0m")
        assert result == "Red"


# ---------------------------------------------------------------------------
# run_chat_once — error paths
# ---------------------------------------------------------------------------


class TestRunChatOnceErrors:
    def test_raises_file_not_found_if_cli_missing(self, tmp_path):
        with patch.object(ai_runner, "CHAT_CLI", tmp_path / "nonexistent.py"):
            with pytest.raises(FileNotFoundError, match="chat_cli.py not found"):
                ai_runner.run_chat_once("Hello")

    def test_raises_runtime_error_on_nonzero_exit(self, tmp_path):
        # Create a fake CLI script
        fake_cli = tmp_path / "chat_cli.py"
        fake_cli.write_text("import sys; sys.exit(1)")

        with patch.object(ai_runner, "CHAT_CLI", fake_cli):
            with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                with pytest.raises(RuntimeError, match="chat_cli failed"):
                    ai_runner.run_chat_once("Hello")

    def test_raises_on_timeout(self, tmp_path):
        import subprocess

        fake_cli = tmp_path / "chat_cli.py"
        fake_cli.write_text("import time; time.sleep(999)")

        with patch.object(ai_runner, "CHAT_CLI", fake_cli):
            with patch("shared.ai_runner.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 1)):
                with pytest.raises(subprocess.TimeoutExpired):
                    ai_runner.run_chat_once("Hello", timeout=1)


# ---------------------------------------------------------------------------
# run_chat_once — success paths
# ---------------------------------------------------------------------------


class TestRunChatOnceSuccess:
    def _make_mock_result(self, stdout: str, returncode: int = 0):
        m = MagicMock()
        m.returncode = returncode
        m.stdout = stdout
        m.stderr = ""
        return m

    def test_returns_tuple_of_str_and_dict(self):
        mock_result = self._make_mock_result("assistant> Hello there\n")

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                        reply, metadata = ai_runner.run_chat_once("Hi")

        assert isinstance(reply, str)
        assert isinstance(metadata, dict)

    def test_strips_assistant_prefix(self):
        mock_result = self._make_mock_result("assistant> Hello there\n")

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                        reply, _ = ai_runner.run_chat_once("Hi")

        assert reply == "Hello there"

    def test_returns_full_output_without_assistant_prefix(self):
        mock_result = self._make_mock_result("Just some output\n")

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                        reply, _ = ai_runner.run_chat_once("Hi")

        assert reply == "Just some output"

    def test_strips_ansi_codes(self):
        mock_result = self._make_mock_result("\x1B[31massistant> Red text\x1B[0m\n")

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                        reply, _ = ai_runner.run_chat_once("Hi")

        assert "\x1B" not in reply

    def test_metadata_contains_provider(self):
        mock_result = self._make_mock_result("assistant> Hi\n")

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                        _, metadata = ai_runner.run_chat_once("Hi", provider="openai")

        assert metadata["provider"] == "openai"

    def test_metadata_contains_model_when_provided(self):
        mock_result = self._make_mock_result("assistant> Hi\n")

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                        _, metadata = ai_runner.run_chat_once("Hi", model="gpt-4")

        assert metadata["model"] == "gpt-4"

    def test_metadata_no_model_key_when_model_not_provided(self):
        mock_result = self._make_mock_result("assistant> Hi\n")

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                        _, metadata = ai_runner.run_chat_once("Hi")

        assert "model" not in metadata

    def test_provider_defaults_to_local(self):
        """When no provider given and no env var, defaults to 'local'."""
        mock_result = self._make_mock_result("assistant> Hi\n")
        run_calls = []

        def capture_run(*args, **kwargs):
            run_calls.append(args[0])
            return mock_result

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", side_effect=capture_run):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}, clear=False):
                        os.environ.pop("DEFAULT_AI_PROVIDER", None)
                        ai_runner.run_chat_once("Hi")

        assert "--provider" in run_calls[0]
        idx = run_calls[0].index("--provider")
        assert run_calls[0][idx + 1] == "local"

    def test_provider_from_env_var(self):
        mock_result = self._make_mock_result("assistant> Hi\n")
        run_calls = []

        def capture_run(*args, **kwargs):
            run_calls.append(args[0])
            return mock_result

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", side_effect=capture_run):
                    with patch.dict(os.environ, {"DEFAULT_AI_PROVIDER": "azure", "WRITE_AI_RUN_LOG": "0"}):
                        ai_runner.run_chat_once("Hi")

        idx = run_calls[0].index("--provider")
        assert run_calls[0][idx + 1] == "azure"

    def test_system_prompt_passed_when_provided(self):
        mock_result = self._make_mock_result("assistant> Hi\n")
        run_calls = []

        def capture_run(*args, **kwargs):
            run_calls.append(args[0])
            return mock_result

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", side_effect=capture_run):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                        ai_runner.run_chat_once("Hi", system="You are helpful")

        assert "--system" in run_calls[0]

    def test_system_prompt_from_env_when_not_given(self):
        mock_result = self._make_mock_result("assistant> Hi\n")
        run_calls = []

        def capture_run(*args, **kwargs):
            run_calls.append(args[0])
            return mock_result

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", side_effect=capture_run):
                    with patch.dict(os.environ, {"SYSTEM_PROMPT": "Helpful assistant", "WRITE_AI_RUN_LOG": "0"}):
                        ai_runner.run_chat_once("Hi")

        assert "--system" in run_calls[0]

    def test_write_log_enabled_by_default(self, tmp_path):
        mock_result = self._make_mock_result("assistant> Hi\n")
        log_calls = []

        def fake_open(path, mode="r", **kwargs):
            log_calls.append(str(path))
            return open(path, mode, **kwargs)

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.object(ai_runner, "LOG_DIR", tmp_path):
                        with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "1"}):
                            ai_runner.run_chat_once("Hi")

        # A log file should have been created in tmp_path
        log_files = list(tmp_path.glob("auto_run_*.txt"))
        assert len(log_files) == 1

    def test_write_log_disabled(self, tmp_path):
        mock_result = self._make_mock_result("assistant> Hi\n")

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.object(ai_runner, "LOG_DIR", tmp_path):
                        with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                            ai_runner.run_chat_once("Hi")

        log_files = list(tmp_path.glob("auto_run_*.txt"))
        assert len(log_files) == 0

    def test_log_write_failure_does_not_propagate(self, tmp_path):
        """Log write failure should be swallowed, not crash the function."""
        mock_result = self._make_mock_result("assistant> Hi\n")

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    # Make LOG_DIR not writable by raising on mkdir
                    with patch.object(ai_runner, "LOG_DIR", Path("/nonexistent/readonly/logs")):
                        with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "1"}):
                            reply, metadata = ai_runner.run_chat_once("Hi")

        assert reply == "Hi"

    def test_uses_last_assistant_marker_in_output(self):
        """When multiple 'assistant> ' occurrences, uses the last one."""
        output = "assistant> First response\nassistant> Second response"
        mock_result = self._make_mock_result(output)

        with patch.object(ai_runner, "CHAT_CLI", Path("/fake/chat_cli.py")):
            with patch("shared.ai_runner.CHAT_CLI") as mock_cli_path:
                mock_cli_path.exists.return_value = True
                with patch("shared.ai_runner.subprocess.run", return_value=mock_result):
                    with patch.dict(os.environ, {"WRITE_AI_RUN_LOG": "0"}):
                        reply, _ = ai_runner.run_chat_once("Hi")

        assert reply == "Second response"
