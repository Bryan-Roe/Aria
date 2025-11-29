"""Unit tests for notification_system security fixes."""
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from notification_system import NotificationManager


class TestNotificationManagerSecurity:
    """Test security-related aspects of NotificationManager."""

    def test_macos_escapes_backslashes(self):
        """Verify backslashes are escaped to prevent injection."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            manager._send_macos("Title\\test", "Message\\test")
            
            # Verify subprocess.run was called with escaped backslashes
            call_args = mock_run.call_args[0][0]
            script = call_args[2]  # The script is the 3rd argument
            assert "\\\\" in script  # Escaped backslash

    def test_macos_escapes_quotes(self):
        """Verify double quotes are escaped to prevent injection."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            manager._send_macos('Title"test', 'Message"test')
            
            call_args = mock_run.call_args[0][0]
            script = call_args[2]
            assert '\\"' in script  # Escaped quote

    def test_macos_escapes_newlines(self):
        """Verify newlines are replaced to prevent script termination."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            manager._send_macos("Title\ntest", "Message\rtest")
            
            call_args = mock_run.call_args[0][0]
            script = call_args[2]
            # Newlines should be replaced with spaces
            assert "\n" not in script
            assert "\r" not in script

    def test_macos_command_injection_attempt(self):
        """Verify command injection attempts are neutralized."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # Attempt to inject a command
            malicious_title = '"; do shell script "rm -rf /"'
            manager._send_macos(malicious_title, "Normal message")
            
            call_args = mock_run.call_args[0][0]
            # Verify subprocess was called with list arguments (not shell=True)
            assert isinstance(call_args, list)
            assert call_args[0] == "osascript"
            assert call_args[1] == "-e"

    def test_macos_uses_subprocess_list_args(self):
        """Verify subprocess is called with list arguments, not shell string."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            manager._send_macos("Test", "Message")
            
            # Verify called with list, not shell=True
            call_args = mock_run.call_args
            assert isinstance(call_args[0][0], list)
            # Verify shell is not True (either not present or False)
            kwargs = call_args[1] if len(call_args) > 1 else {}
            assert kwargs.get("shell") is not True

    def test_linux_uses_subprocess_list_args(self):
        """Verify subprocess is called with list arguments, not shell string."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            manager._send_linux("Test", "Message", "info")
            
            call_args = mock_run.call_args
            assert isinstance(call_args[0][0], list)
            kwargs = call_args[1] if len(call_args) > 1 else {}
            assert kwargs.get("shell") is not True

    def test_linux_command_injection_attempt(self):
        """Verify command injection attempts in Linux notifications are safe."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # Attempt to inject a command via title
            malicious_title = "$(rm -rf /)"
            manager._send_linux(malicious_title, "Normal message", "info")
            
            call_args = mock_run.call_args[0][0]
            # With list args, the malicious string is passed as a literal argument
            assert malicious_title in call_args

    def test_macos_timeout_handling(self):
        """Verify timeout is set and handled properly."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="osascript", timeout=5)
            # Should not raise - error is printed instead
            manager._send_macos("Test", "Message")

    def test_linux_timeout_handling(self):
        """Verify timeout is set and handled properly for Linux."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="notify-send", timeout=5)
            # Should not raise - error is printed instead
            manager._send_linux("Test", "Message", "info")

    def test_macos_file_not_found_handling(self):
        """Verify FileNotFoundError is handled when osascript is not available."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("osascript not found")
            # Should not raise - error is printed instead
            manager._send_macos("Test", "Message")

    def test_linux_file_not_found_handling(self):
        """Verify FileNotFoundError is handled when notify-send is not available."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("notify-send not found")
            # Should not raise - error is printed instead
            manager._send_linux("Test", "Message", "info")

    def test_macos_subprocess_has_timeout(self):
        """Verify subprocess.run is called with timeout parameter."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            manager._send_macos("Test", "Message")
            
            kwargs = mock_run.call_args[1]
            assert "timeout" in kwargs
            assert kwargs["timeout"] == 5

    def test_linux_subprocess_has_timeout(self):
        """Verify subprocess.run is called with timeout parameter for Linux."""
        manager = NotificationManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            manager._send_linux("Test", "Message", "info")
            
            kwargs = mock_run.call_args[1]
            assert "timeout" in kwargs
            assert kwargs["timeout"] == 5
