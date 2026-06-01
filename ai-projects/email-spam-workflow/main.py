"""Email spam classification workflow entry point.

Modes
-----
HTTP server (default / --server)
    Exposes the workflow through the Azure AI Agent Server wrapper so it can
    be debugged with AI Toolkit Agent Inspector.

CLI (--cli)
    Runs a single email through the workflow and prints streamed node output to
    stdout for quick local checks.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional fallback for minimal setups

    def load_dotenv(*_args, **_kwargs):
        return False


load_dotenv(override=False)


def run_server() -> None:
    """Start the workflow as an HTTP server for Agent Inspector."""
    from workflow import build_workflow

    try:
        from azure.ai.agentserver.agentframework import from_agent_framework
    except ImportError as exc:
        print(
            "[ERROR] azure-ai-agentserver-agentframework is not installed.\n" "Run: pip install -r requirements.txt",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    workflow = build_workflow()
    agent = workflow.as_agent()

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    print("Starting Email Spam workflow HTTP server ...")
    from_agent_framework(agent).run()


async def run_cli(email_text: str) -> None:
    """Run the workflow once and stream node output to stdout."""
    from agent_framework import AgentResponseUpdate, Message
    from workflow import build_workflow

    workflow = build_workflow()

    print("\nEmail input:\n")
    print(email_text)
    print("\n" + "=" * 60)

    last_author: str | None = None

    async for event in workflow.run(Message("user", [email_text]), stream=True):
        if event.type != "output" or not isinstance(event.data, AgentResponseUpdate):
            continue

        update = event.data
        author = update.author_name or "Agent"

        if author != last_author:
            if last_author is not None:
                print()
            print(f"\n--- {author} ---\n")
            last_author = author

        print(update.text, end="", flush=True)

    print("\n" + "=" * 60)
    print("\nWorkflow complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Email spam classification workflow")
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run as HTTP server (default when no explicit mode is provided)",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run a one-shot CLI classification",
    )
    parser.add_argument(
        "--email",
        type=str,
        default=(
            "Subject: Limited Time Offer!\n\n"
            "You have been selected for an exclusive prize. Click "
            "https://suspicious.example/claim-now to verify your account "
            "and receive 90% off today only."
        ),
        help="Raw email content for CLI mode",
    )
    args = parser.parse_args()

    if args.cli:
        asyncio.run(run_cli(args.email))
    else:
        run_server()


if __name__ == "__main__":
    main()
