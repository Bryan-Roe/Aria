from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import chat_cli  # noqa: E402


class _FakeProvider:
    def __init__(self) -> None:
        self.user_messages: list[str] = []

    def complete(self, messages, stream: bool = True):
        last_user = next(message["content"] for message in reversed(messages) if message["role"] == "user")
        self.user_messages.append(last_user)
        return f"reply to: {last_user}"


class _FailingProvider:
    def complete(self, messages, stream: bool = True):
        raise RuntimeError("LM Studio unavailable")


class _PartiallyFailingProvider:
    def complete(self, messages, stream: bool = True):
        def gen():
            yield "partial reply"
            raise RuntimeError("stream interrupted")

        return gen()


class ChatCliTests(unittest.TestCase):
    def test_parser_accepts_autonomous_arguments(self) -> None:
        parser = chat_cli.build_arg_parser()

        args = parser.parse_args(
            [
                "--interactive",
                "--autonomous",
                "--auto-seed",
                "Start here",
                "--auto-followup",
                "Keep going",
                "--auto-delay",
                "0.5",
                "--max-turns",
                "3",
            ]
        )

        self.assertTrue(args.interactive)
        self.assertTrue(args.autonomous)
        self.assertEqual(args.auto_seed, "Start here")
        self.assertEqual(args.auto_followup, "Keep going")
        self.assertEqual(args.auto_delay, 0.5)
        self.assertEqual(args.max_turns, 3)

    def test_autonomous_chat_runs_without_input(self) -> None:
        provider = _FakeProvider()
        args = SimpleNamespace(
            provider="local",
            model=None,
            system="Stay concise.",
            once=None,
            autonomous=True,
            auto_seed="Initial task",
            auto_followup="Keep going",
            auto_delay=0.0,
            max_turns=3,
        )

        with (
            patch.object(
                chat_cli,
                "detect_provider",
                return_value=(
                    provider,
                    SimpleNamespace(name="fake", model="fake-model"),
                ),
            ),
            patch(
                "builtins.input",
                side_effect=AssertionError("input() should not be called in autonomous mode"),
            ),
            redirect_stdout(io.StringIO()),
        ):
            exit_code = chat_cli.autonomous_chat(args)

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            provider.user_messages,
            ["Initial task", "Keep going", "Keep going"],
        )

    def test_main_dispatches_to_autonomous_mode(self) -> None:
        with (
            patch.object(chat_cli, "autonomous_chat", return_value=0) as autonomous_chat,
            patch.object(
                chat_cli,
                "interactive_chat",
                side_effect=AssertionError("interactive mode should not run"),
            ),
        ):
            exit_code = chat_cli.main(
                [
                    "--auto-seed",
                    "Start",
                    "--max-turns",
                    "1",
                ]
            )

        self.assertEqual(exit_code, 0)
        autonomous_chat.assert_called_once()

    def test_main_defaults_to_autonomous_mode(self) -> None:
        with (
            patch.object(chat_cli, "autonomous_chat", return_value=0) as autonomous_chat,
            patch.object(
                chat_cli,
                "interactive_chat",
                side_effect=AssertionError("interactive mode should not run"),
            ),
        ):
            exit_code = chat_cli.main([])

        self.assertEqual(exit_code, 0)
        autonomous_chat.assert_called_once()

    def test_main_interactive_override_uses_interactive_mode(self) -> None:
        with (
            patch.object(chat_cli, "interactive_chat", return_value=0) as interactive_chat,
            patch.object(
                chat_cli,
                "autonomous_chat",
                side_effect=AssertionError("autonomous mode should not run"),
            ),
        ):
            exit_code = chat_cli.main(["--interactive"])

        self.assertEqual(exit_code, 0)
        interactive_chat.assert_called_once()

    def test_stream_assistant_reply_returns_error_text_when_provider_raises(
        self,
    ) -> None:
        with redirect_stdout(io.StringIO()):
            reply = chat_cli.stream_assistant_reply(
                _FailingProvider(),
                [{"role": "user", "content": "Hello"}],
            )

        self.assertIn("[provider error:", reply)
        self.assertIn("LM Studio unavailable", reply)

    def test_stream_assistant_reply_preserves_partial_output_on_stream_failure(
        self,
    ) -> None:
        with redirect_stdout(io.StringIO()):
            reply = chat_cli.stream_assistant_reply(
                _PartiallyFailingProvider(),
                [{"role": "user", "content": "Hello"}],
            )

        self.assertIn("partial reply", reply)
        self.assertIn("[provider error:", reply)
        self.assertIn("stream interrupted", reply)

    def test_interactive_save_reports_message_count(self) -> None:
        provider = _FakeProvider()
        args = SimpleNamespace(
            provider="local",
            model=None,
            system="Stay concise.",
        )

        with (
            patch.object(
                chat_cli,
                "detect_provider",
                return_value=(
                    provider,
                    SimpleNamespace(name="fake", model="fake-model"),
                ),
            ),
            patch.object(chat_cli, "save_conversation", return_value=Path("/tmp/chat.jsonl")) as save_conversation,
            patch("builtins.input", side_effect=["/save", "/exit"]),
            redirect_stdout(io.StringIO()) as stdout,
        ):
            exit_code = chat_cli.interactive_chat(args)

        self.assertEqual(exit_code, 0)
        save_conversation.assert_called_once()
        self.assertIn("Saved 1 message(s) to /tmp/chat.jsonl", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
