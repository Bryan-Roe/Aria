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
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional for lightweight prototype usage

    def load_dotenv(*_args, **_kwargs):
        return False


# Load .env eagerly so both the Foundry workflow and local prototype mode can
# read environment configuration consistently.
load_dotenv(override=True)


# ---------------------------------------------------------------------------
# HTTP server mode
# ---------------------------------------------------------------------------


def run_server() -> None:
    """Start the HTTP server via azure-ai-agentserver-agentframework."""
    from workflow import build_workflow

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
    from workflow import build_workflow

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


def run_prototype_monitor(
    watch_dir: str,
    output_dir: str,
    *,
    run_once: bool,
    poll_interval: float,
    max_iterations: int | None,
    run_generated_tests: bool,
) -> None:
    """Run the local folder-monitor prototype workflow."""
    from prototype_workflow import FolderMonitorWorkflow

    workflow = FolderMonitorWorkflow(
        watch_dir=watch_dir,
        output_dir=output_dir,
        run_generated_tests=run_generated_tests,
    )

    print("Starting prototype code-generation workflow")
    print(f"  watch_dir: {Path(watch_dir).resolve()}")
    print(f"  output_dir: {Path(output_dir).resolve()}")
    print(f"  run_generated_tests: {run_generated_tests}")

    if run_once:
        results = workflow.run_once()
        print(f"Processed {len(results)} request(s).")
        for result in results:
            print(
                f"- {result.processed_path.name}: module={result.module_path.name}, "
                f"test={result.test_path.name}"
            )
        return

    processed_count = workflow.watch(
        poll_interval=poll_interval,
        max_iterations=max_iterations,
    )
    print(f"Prototype watcher stopped after processing {processed_count} request(s).")


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
    parser.add_argument(
        "--prototype-monitor",
        action="store_true",
        help="Run the local folder-monitor prototype that generates code and pytest tests",
    )
    parser.add_argument(
        "--prototype-run-once",
        action="store_true",
        help="Process the current watch folder once and exit",
    )
    parser.add_argument(
        "--prototype-watch-dir",
        type=str,
        default="prototype_specs/inbox",
        help="Directory to watch for JSON code-generation requests",
    )
    parser.add_argument(
        "--prototype-output-dir",
        type=str,
        default="prototype_specs/generated",
        help="Directory where generated code/tests/reports are written",
    )
    parser.add_argument(
        "--prototype-poll-interval",
        type=float,
        default=2.0,
        help="Seconds to sleep between prototype watch iterations",
    )
    parser.add_argument(
        "--prototype-max-iterations",
        type=int,
        default=None,
        help="Optional cap on prototype polling iterations",
    )
    parser.add_argument(
        "--prototype-run-generated-tests",
        action="store_true",
        help="Run pytest against each generated test file before archiving the request",
    )
    args = parser.parse_args()

    if args.prototype_monitor:
        run_prototype_monitor(
            watch_dir=args.prototype_watch_dir,
            output_dir=args.prototype_output_dir,
            run_once=args.prototype_run_once,
            poll_interval=args.prototype_poll_interval,
            max_iterations=args.prototype_max_iterations,
            run_generated_tests=args.prototype_run_generated_tests,
        )
    elif args.cli:
        asyncio.run(run_cli(args.prompt))
    else:
        # Default: HTTP server mode
        run_server()


if __name__ == "__main__":
    main()
