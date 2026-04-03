#!/usr/bin/env python3
"""Pre-commit hook: ensure CLI scripts add repo root to sys.path before importing local packages.

This script is intentionally simple: it scans files passed on the command line
and fails if a file imports local packages (e.g. `from shared ...` or `import shared`)
but does not include the REPO_ROOT + sys.path insertion pattern.

Run by pre-commit with `files` only including `scripts/*.py` by default.
"""
import re
import sys
from pathlib import Path

PAT_IMPORT_LOCAL = re.compile(r"^\s*(from|import)\s+(shared|shared\.|\.|\w+\.)", re.M)
PAT_REPO_ROOT = re.compile(
    r"REPO_ROOT\s*=\s*Path\(__file__\)\.resolve\(\)\.parent\.parent"
)
PAT_SYS_INSERT = re.compile(r"sys\.path\.insert\(\s*0\s*,\s*str\(REPO_ROOT\)\s*\)")


def check_file(path: Path) -> bool:
    try:
        txt = path.read_text()
    except Exception:
        print(f"Could not read {path}", file=sys.stderr)
        return False

    # If the script imports local/shared modules, enforce the sys.path pattern
    if re.search(r"from\s+shared\b|import\s+shared\b", txt):
        has_root = bool(PAT_REPO_ROOT.search(txt))
        has_insert = bool(PAT_SYS_INSERT.search(txt))
        if not (has_root and has_insert):
            print(
                f"{path}: imports local 'shared' but missing REPO_ROOT sys.path insertion",
                file=sys.stderr,
            )
            return False

    # Otherwise, pass
    return True


def main(argv):
    ok = True
    for f in argv:
        p = Path(f)
        if not check_file(p):
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
