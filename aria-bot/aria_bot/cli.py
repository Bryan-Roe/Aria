"""Command-line interface for the Aria self-modifying loop.

Run a single cycle with::

    python -m aria_bot                 # dry-run, no writes
    python -m aria_bot --apply         # write fixes to disk (no commit)
    python -m aria_bot --apply --commit  # also create a local git commit
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

from .orchestrator import run_cycle


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aria_bot",
        description="Run one self-modifying repository cycle (rules-based, deterministic).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to operate on (default: current working directory).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write fixes to disk. Without this flag the run is dry-run.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Create a local git commit for applied changes (requires --apply).",
    )
    parser.add_argument(
        "--max-plans",
        type=int,
        default=50,
        help="Cap on the number of plans applied per cycle.",
    )
    parser.add_argument(
        "--status-path",
        type=Path,
        default=None,
        help="Override the status.json output location.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the JSON summary (status file is still written).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: INFO).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.commit and not args.apply:
        print("error: --commit requires --apply", file=sys.stderr)
        return 2

    result = run_cycle(
        repo_root=args.repo_root,
        apply=args.apply,
        commit=args.commit,
        max_plans=args.max_plans,
        status_path=args.status_path,
    )

    if not args.quiet:
        summary = {
            "totals": result.to_dict()["totals"],
            "validation_ok": result.validation_ok,
            "commit_sha": result.commit_sha,
            "notes": result.notes,
            "apply": result.apply,
            "commit": result.commit,
        }
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")

    return 0 if result.validation_ok else 1


if __name__ == "__main__":  # pragma: no cover - module entrypoint
    raise SystemExit(main())
