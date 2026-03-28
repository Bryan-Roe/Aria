"""
Writer-Reviewer Multi-Agent Workflow — Entry Point

Modes
-----
HTTP server (default / --server)
    Wraps the workflow as an HTTP server using azure-ai-agentserver-agentframework.
    Send POST requests with conversation messages; the server streams
    AgentResponseUpdate events from both the Writer and Reviewer agents.

CLI (--cli)
    Runs the workflow once with a single prompt, printing streamed output to
    stdout. Useful for quick local testing without an HTTP client.

Usage
-----
  # HTTP server (production / debug mode)
  python main.py
  python main.py --server

  # CLI smoke test
  python main.py --cli
  python main.py --cli --prompt "Write a haiku about autumn."
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

# Load .env BEFORE importing workflow so env vars are available to workflow.py.
# override=True ensures .env values work even when the process already has
# environment variables set (important for containerised / deployed environments).
load_dotenv(override=True)

from workflow import build_workflow  # noqa: E402  (must follow load_dotenv)

# ---------------------------------------------------------------------------
# HTTP server mode
# ---------------------------------------------------------------------------


def run_server() -> None:
    """Start the HTTP server via azure-ai-agentserver-agentframework."""
    try:
        from azure.ai.agentserver.agentframework import from_agent_framework
    except ImportError as exc:
        print(
            "[ERROR] azure-ai-agentserver-agentframework is not installed.\n"
            "Run: pip install azure-ai-agentserver-core==1.0.0b16 "
            "azure-ai-agentserver-agentframework==1.0.0b16",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    workflow = build_workflow()

    # .as_agent() wraps the workflow so the agentserver can drive it via HTTP.
    agent = workflow.as_agent()

    print("Starting Writer-Reviewer workflow HTTP server …")
    from_agent_framework(agent).run()


# ---------------------------------------------------------------------------
# CLI mode
# ---------------------------------------------------------------------------


async def run_cli(prompt: str) -> None:
    """Run a single-turn through the workflow and stream output to stdout."""
    from agent_framework import AgentResponseUpdate, Message

    workflow = build_workflow()

    print(f"\nUser prompt: {prompt}\n")
    print("=" * 60)

    last_author: str | None = None

    async for event in workflow.run(Message("user", [prompt]), stream=True):
        if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
            update = event.data
            author = update.author_name or "Agent"

            if author != last_author:
                if last_author is not None:
                    print()  # blank line between agents
                print(f"\n--- {author} ---\n")
                last_author = author

            print(update.text, end="", flush=True)

    print("\n" + "=" * 60)
    print("\nWorkflow complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Writer-Reviewer Multi-Agent Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run as HTTP server (this is the default when no flag is given)",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run once in CLI mode (outputs to stdout)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="Write a short blog post about the benefits of morning walks.",
        help="The user prompt to use in CLI mode (ignored in server mode)",
    )
    args = parser.parse_args()

    if args.cli:
        asyncio.run(run_cli(args.prompt))
    else:
        # Default: HTTP server mode
        run_server()


if __name__ == "__main__":
    main()
