"""Command-line entrypoint for the Aria core runtime.

Usage:
    python -m core
    python -m core --cycles 3 --sleep 0.5
"""

from __future__ import annotations

import argparse
import json

from core.runner import AriaRunner


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Aria core autonomous runtime")
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of autonomous cycles to run (default: 1).",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.1,
        help="Seconds to sleep between cycles when --cycles > 1.",
    )
    args = parser.parse_args()

    runner = AriaRunner(
        config={"max_cycles": args.cycles, "sleep_seconds": args.sleep})

    if args.cycles <= 1:
        summary = runner.run_once()
        print(json.dumps(summary, indent=2))
        return

    runner.run()


if __name__ == "__main__":
    main()
