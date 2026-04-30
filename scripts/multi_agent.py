#!/usr/bin/env python3
"""
Multi-Agent Coordinator — runs multiple autonomous code agents in parallel.

Each agent works on a separate task. Results are collected and reported together.

Usage:
    # Run a set of tasks from a JSON file
    python scripts/multi_agent.py --tasks-file tasks.json --llm-type ollama

    # Pass tasks directly on the command line
    python scripts/multi_agent.py \
        --task "Add docstrings to shared/chat_memory.py" \
        --task "Fix failing test_quantum_autorun tests" \
        --llm-type ollama --dry-run

    # Limit parallel workers (default: 3)
    python scripts/multi_agent.py --tasks-file tasks.json --workers 2

Tasks JSON format:
    [
        {"task": "Add docstrings to shared/chat_memory.py"},
        {"task": "Fix failing tests", "llm_type": "ollama", "model": "codellama"},
        {"task": "Clean unused imports", "dry_run": true}
    ]
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repo root and scripts dir are on path before importing local modules
_REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_BOOTSTRAP))
if str(_REPO_ROOT_BOOTSTRAP / "scripts") not in sys.path:
    sys.path.insert(1, str(_REPO_ROOT_BOOTSTRAP / "scripts"))

_consensus_mod = importlib.import_module("shared.consensus_engine")
consensus_from_task_results = _consensus_mod.consensus_from_task_results
_agent_mod = importlib.import_module("autonomous_code_agent")
AgentState = _agent_mod.AgentState
CodeAgent = _agent_mod.CodeAgent

REPO_ROOT = Path(__file__).parent.parent
DATA_OUT = REPO_ROOT / "data_out" / "multi_agent"

_LOGGER = logging.getLogger(__name__)


@dataclass
class AgentJob:
    """Single job definition for a multi-agent run."""

    task: str
    llm_type: str = "ollama"
    model: Optional[str] = None
    files: Optional[List[str]] = None
    dry_run: bool = False
    skip_tests: bool = False


@dataclass
class MultiAgentReport:
    """Aggregated results from a multi-agent run."""

    run_id: str
    started_at: str
    completed_at: str
    total_tasks: int
    succeeded: int
    failed: int
    rolled_back: int
    tests_skipped_tasks: int
    total_files_modified: int
    total_tokens_estimated: int
    total_duration_seconds: float
    consensus: Dict[str, Any]
    tasks: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, output_dir: Path = DATA_OUT) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"report_{self.run_id}.json"
        with open(report_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        # Also write latest.json for easy access
        latest_path = output_dir / "latest.json"
        with open(latest_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        return report_path


def _run_single_job(job: AgentJob) -> Any:
    """Execute one job in a worker thread."""
    _LOGGER.info(f"Worker starting task: {job.task[:60]}")
    try:
        agent = CodeAgent(llm_type=job.llm_type, model=job.model)
        state = agent.execute_task(
            job.task,
            forced_files=job.files,
            dry_run=job.dry_run,
            skip_tests=job.skip_tests,
        )
        return state
    except Exception as e:
        _LOGGER.error(f"Worker error for task '{job.task}': {e}")
        # Return a failed state
        now = datetime.now().isoformat()
        return AgentState(
            task_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            task_description=job.task,
            status="failed",
            llm_type=job.llm_type,
            files_modified=[],
            tests_run=0,
            tests_passed=0,
            tests_failed=0,
            reasoning="",
            commits=[],
            errors=[str(e)],
            started_at=now,
            updated_at=now,
        )


def run_parallel(
    jobs: List[AgentJob],
    max_workers: int = 3,
    verbose: bool = False,
) -> MultiAgentReport:
    """Run a list of agent jobs in parallel and return aggregated report."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    started_at = datetime.now().isoformat()
    _start = time.monotonic()

    _LOGGER.info(
        f"Multi-agent run {run_id}: {len(jobs)} tasks, " f"max_workers={max_workers}"
    )

    completed_states: List[Any] = []

    with ThreadPoolExecutor(
        max_workers=max_workers, thread_name_prefix="agent"
    ) as pool:
        futures = {pool.submit(_run_single_job, job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                state = future.result()
                completed_states.append(state)
                status_icon = "✓" if state.status == "complete" else "✗"
                print(
                    f"  {status_icon} [{state.status:12s}] {job.task[:55]}"
                    + (
                        f" ({state.duration_seconds}s)"
                        if state.duration_seconds
                        else ""
                    )
                )
                if verbose and state.errors:
                    for err in state.errors:
                        print(f"         error: {err}")
            except Exception as e:
                print(f"  ✗ [exception   ] {job.task[:55]} — {e}")

    total_duration = round(time.monotonic() - _start, 2)

    succeeded = sum(1 for s in completed_states if s.status == "complete")
    failed = sum(1 for s in completed_states if s.status == "failed")
    rolled_back = sum(1 for s in completed_states if s.rollback_performed)
    tests_skipped_tasks = sum(1 for s in completed_states if s.tests_skipped)
    total_files = sum(len(s.files_modified) for s in completed_states)
    total_tokens = sum(s.tokens_estimated for s in completed_states)

    consensus = consensus_from_task_results(
        {
            f"task_{idx + 1}": {"status": state.status}
            for idx, state in enumerate(completed_states)
        }
    )

    report = MultiAgentReport(
        run_id=run_id,
        started_at=started_at,
        completed_at=datetime.now().isoformat(),
        total_tasks=len(jobs),
        succeeded=succeeded,
        failed=failed,
        rolled_back=rolled_back,
        tests_skipped_tasks=tests_skipped_tasks,
        total_files_modified=total_files,
        total_tokens_estimated=total_tokens,
        total_duration_seconds=total_duration,
        consensus={
            "reached": consensus.reached,
            "winner": consensus.winner,
            "winner_ratio": round(consensus.winner_ratio, 4),
            "reason": consensus.reason,
            "support_count": consensus.support_count,
            "vote_count": consensus.vote_count,
            "scores": consensus.scores,
        },
        tasks=[s.to_dict() for s in completed_states],
    )

    return report


def _load_jobs_from_file(
    path: str,
    default_llm: str,
    default_dry_run: bool,
    default_skip_tests: bool,
) -> List[AgentJob]:
    """Load job definitions from a JSON file."""
    with open(path) as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise ValueError("Tasks JSON file must contain a top-level array")
    jobs = []
    for item in raw:
        if isinstance(item, str):
            # Simple string form
            jobs.append(
                AgentJob(
                    task=item,
                    llm_type=default_llm,
                    dry_run=default_dry_run,
                    skip_tests=default_skip_tests,
                )
            )
        elif isinstance(item, dict):
            jobs.append(
                AgentJob(
                    task=item["task"],
                    llm_type=item.get("llm_type", default_llm),
                    model=item.get("model"),
                    files=item.get("files"),
                    # CLI flags act as hard overrides: if CLI says True, always True
                    dry_run=default_dry_run or item.get("dry_run", False),
                    skip_tests=default_skip_tests or item.get("skip_tests", False),
                )
            )
        else:
            raise ValueError(f"Invalid task entry: {item!r}")
    return jobs


def _print_summary(report: MultiAgentReport) -> None:
    width = 68
    print("\n" + "=" * width)
    print(" MULTI-AGENT RUN SUMMARY ".center(width, "="))
    print("=" * width)
    print(f"  Run ID          : {report.run_id}")
    print(f"  Total tasks     : {report.total_tasks}")
    print(f"  Succeeded       : {report.succeeded}")
    print(f"  Failed          : {report.failed}")
    print(f"  Rolled back     : {report.rolled_back}")
    print(f"  Tests skipped   : {report.tests_skipped_tasks}")
    print(f"  Files modified  : {report.total_files_modified}")
    print(f"  ~Tokens used    : {report.total_tokens_estimated}")
    print(f"  Wall-clock time : {report.total_duration_seconds}s")
    print(
        "  Consensus       : "
        f"reached={report.consensus.get('reached')} "
        f"winner={report.consensus.get('winner')} "
        f"ratio={report.consensus.get('winner_ratio')} "
        f"reason={report.consensus.get('reason')}"
    )
    print("=" * width + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Agent Coordinator — run several autonomous code agents in parallel"
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--tasks-file",
        type=str,
        metavar="PATH",
        help="JSON file with task definitions (array of task strings or objects)",
    )
    source.add_argument(
        "--task",
        action="append",
        dest="tasks",
        metavar="TASK",
        help="Task description (can be repeated for multiple tasks)",
    )
    parser.add_argument(
        "--llm-type",
        type=str,
        default="ollama",
        choices=["ollama", "lmstudio", "echo"],
        help="Default LLM backend for all tasks",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Default model name for all tasks",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Maximum parallel workers (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyse without modifying files",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip per-task validation tests (auto-enabled for --dry-run)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DATA_OUT),
        help="Directory for report JSON files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show per-task error details in output",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(threadName)s %(levelname)s %(message)s",
    )

    # Build job list
    jobs: List[AgentJob] = []
    effective_skip_tests = args.skip_tests or args.dry_run
    if args.tasks_file:
        try:
            jobs = _load_jobs_from_file(
                args.tasks_file,
                args.llm_type,
                args.dry_run,
                effective_skip_tests,
            )
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"Error loading tasks file: {e}")
            sys.exit(1)
    elif args.tasks:
        for t in args.tasks:
            jobs.append(
                AgentJob(
                    task=t,
                    llm_type=args.llm_type,
                    model=args.model,
                    dry_run=args.dry_run,
                    skip_tests=effective_skip_tests,
                )
            )
    else:
        parser.print_help()
        print("\nError: provide --task or --tasks-file")
        sys.exit(1)

    if not jobs:
        print("No tasks to run.")
        sys.exit(0)

    output_dir = Path(args.output_dir)
    print(
        f"\nRunning {len(jobs)} task(s) with up to {args.workers} parallel worker(s)..."
    )
    if args.dry_run:
        print("  [DRY RUN — no files will be modified]\n")
    if effective_skip_tests:
        print("  [TESTS SKIPPED for this run]\n")
    else:
        print()

    report = run_parallel(jobs, max_workers=args.workers, verbose=args.verbose)
    report_path = report.save(output_dir)
    _print_summary(report)
    print(f"Report saved: {report_path}")

    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()
