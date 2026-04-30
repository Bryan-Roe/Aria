#!/usr/bin/env python3
"""Pre-commit hook: ensure docs referencing scripts/ include the CLI sys.path guidance.

This script checks Markdown files passed on the command line. If a file
contains references to `scripts/` (code spans or plain text), the file must
also contain at least one of the following tokens that indicate the guidance
is present: `REPO_ROOT`, `sys.path.insert(0, str(REPO_ROOT))`, or
"CLI scripts".

Return code 0 on success, 1 on failure.
"""
import re
import sys
from pathlib import Path

PAT_SCRIPTS_REF = re.compile(r"`?scripts/[^`\s]*`?|\bscripts/\w+")
PAT_GUIDANCE = re.compile(r"REPO_ROOT|sys\.path\.insert\(|CLI scripts", re.I)


def check_file(path: Path) -> bool:
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"ERROR: could not read {path}: {exc}", file=sys.stderr)
        return False

    if PAT_SCRIPTS_REF.search(txt):
        if not PAT_GUIDANCE.search(txt):
            print(
                f"{path}: references 'scripts/' but does not include CLI sys.path guidance (e.g. REPO_ROOT or sys.path.insert)",
                file=sys.stderr,
            )
            return False

    return True


def main(argv):
    ok = True

    paths_to_check = []
    # If no files provided (manual run), scan common documentation locations
    if not argv:
        patterns = [
            "README.md",
            "CONTRIBUTING.md",
            "AGENT_QUICKSTART.md",
            "scripts/README.md",
            "docs/**/*.md",
            ".github/instructions/**/*.md",
            ".github/skills/**/*.md",
            "apps/**/*.md",
            "ai-projects/**/README.md",
            "docs/quickref/**/*.md",
        ]
        for pat in patterns:
            for p in Path(".").glob(pat):
                paths_to_check.append(p)
    else:
        for f in argv:
            paths_to_check.append(Path(f))

    # Deduplicate while preserving order
    seen = set()
    uniq_paths = []
    for p in paths_to_check:
        try:
            rp = p.resolve()
        except Exception:
            rp = p
        if rp in seen:
            continue
        seen.add(rp)
        uniq_paths.append(p)

    for p in uniq_paths:
        # Only check markdown files
        if not p.exists() or p.suffix.lower() not in (".md",):
            continue
        if not check_file(p):
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
