#!/usr/bin/env python
"""
Artifact cleanup for data_out/.

Applies retention policies (max age, max count) to old training artifacts,
status JSONs, and log files. Safe by default — use --apply to actually delete.

Usage:
  python scripts/cleanup_artifacts.py                  # Dry-run (preview)
  python scripts/cleanup_artifacts.py --apply          # Actually delete
  python scripts/cleanup_artifacts.py --max-age 14     # Keep last 14 days
  python scripts/cleanup_artifacts.py --max-count 20   # Keep last 20 per dir
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out"

# Directories to clean (relative to data_out/)
CLEANABLE = [
    "autotrain",
    "quantum_autorun",
    "evaluation",
    "test_runner",
    "autonomous_training",
    "aria_automation",
]

# File patterns eligible for cleanup
PATTERNS = ["*.json", "*.log", "*.md", "*.csv"]

# Files to always keep
KEEP_FILES = {"status.json", "latest_results.json"}


def _file_age_days(path: Path) -> float:
    return (time.time() - path.stat().st_mtime) / 86400


def find_candidates(
    max_age_days: int = 30, max_count: int = 50
) -> list[tuple[Path, str]]:
    """Return (path, reason) tuples for files eligible for deletion."""
    candidates: list[tuple[Path, str]] = []

    for dirname in CLEANABLE:
        dirpath = DATA_OUT / dirname
        if not dirpath.is_dir():
            continue

        # Gather all matching files, newest first
        files: list[Path] = []
        for pattern in PATTERNS:
            files.extend(dirpath.glob(pattern))
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        for idx, f in enumerate(files):
            if f.name in KEEP_FILES:
                continue

            age = _file_age_days(f)
            if age > max_age_days:
                candidates.append((f, f"age={int(age)}d > {max_age_days}d"))
            elif idx >= max_count:
                candidates.append((f, f"count={idx + 1} > {max_count}"))

    return candidates


def main() -> None:
    ap = argparse.ArgumentParser(description="Clean old artifacts from data_out/")
    ap.add_argument(
        "--apply", action="store_true", help="Actually delete (default: dry-run)"
    )
    ap.add_argument(
        "--max-age", type=int, default=30, help="Max age in days (default: 30)"
    )
    ap.add_argument(
        "--max-count",
        type=int,
        default=50,
        help="Max files per directory (default: 50)",
    )
    args = ap.parse_args()

    candidates = find_candidates(max_age_days=args.max_age, max_count=args.max_count)

    if not candidates:
        print("✅ No artifacts to clean up.")
        return

    total_bytes = 0
    print(f"{'🗑️  CLEANUP' if args.apply else '👀 DRY RUN'} — {len(candidates)} files\n")

    for path, reason in candidates:
        size = path.stat().st_size
        total_bytes += size
        rel = path.relative_to(REPO_ROOT)
        print(f"  {'DEL' if args.apply else '   '} {rel}  ({size:,} bytes, {reason})")
        if args.apply:
            path.unlink()

    mb = total_bytes / (1024 * 1024)
    print(
        f"\n{'Deleted' if args.apply else 'Would delete'}: {len(candidates)} files, {mb:.2f} MB"
    )

    # Write summary
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "applied": args.apply,
        "files_count": len(candidates),
        "total_bytes": total_bytes,
        "max_age_days": args.max_age,
        "max_count": args.max_count,
    }
    summary_path = DATA_OUT / "cleanup_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
