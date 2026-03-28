#!/usr/bin/env python3
"""
Lightweight test watcher: monitors Python files and reruns pytest on changes.

Usage:
    python3 scripts/test_watcher.py --path tests --cmd "pytest tests -q"

This script uses polling (no external deps) so it works in CI/dev containers.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def scan_files(paths, exts=(".py",)):
    files = {}
    for p in paths:
        p = Path(p)
        if p.is_file():
            files[str(p)] = p.stat().st_mtime
        else:
            for f in p.rglob("*"):
                if f.suffix in exts and f.is_file():
                    files[str(f)] = f.stat().st_mtime
    return files


def run_command(cmd):
    print(f"\n=== Running: {cmd} ===")
    try:
        proc = subprocess.Popen(cmd, shell=True)
        proc.communicate()
        rc = proc.returncode
        print(f"=== Finished (exit {rc}) ===\n")
    except KeyboardInterrupt:
        print("Interrupted during test run")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", nargs="*", default=["tests", "apps", "shared", "scripts"],
                        help="Paths to watch (files or directories)")
    parser.add_argument("--cmd", default="pytest tests -q",
                        help="Command to run on changes")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Polling interval seconds")
    args = parser.parse_args()

    watch_paths = [Path(p) for p in args.paths]
    print("Watching paths:", ", ".join(str(p) for p in watch_paths))
    print("Command:", args.cmd)

    last_snapshot = scan_files(watch_paths)
    try:
        # Run once at start
        run_command(args.cmd)
        while True:
            time.sleep(args.poll_interval)
            snapshot = scan_files(watch_paths)
            changed = False
            # Check for new/modified files
            for f, m in snapshot.items():
                if f not in last_snapshot or last_snapshot[f] != m:
                    print(f"Detected change: {f}")
                    changed = True
                    break
            # Check for deleted files
            if not changed:
                for f in list(last_snapshot.keys()):
                    if f not in snapshot:
                        print(f"Detected removal: {f}")
                        changed = True
                        break

            if changed:
                last_snapshot = snapshot
                run_command(args.cmd)
    except KeyboardInterrupt:
        print("Test watcher stopped by user")


if __name__ == "__main__":
    main()
