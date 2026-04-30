"""CommitSystem — atomic, local-only git commits.

This module never pushes. It also never resets, rebases, or otherwise
rewrites history. Its only job is to stage a known set of paths and
record an atomic commit with a stable, machine-parseable message prefix.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

_logger = logging.getLogger(__name__)

#: All commits made by the bot use this subject prefix so reviewers and
#: tooling can filter them easily.
COMMIT_PREFIX = "chore(aria-bot):"


@dataclass
class CommitSystem:
    """Stage and commit a set of paths produced by the executor."""

    repo_root: Path

    def commit(self, paths: Sequence[Path], message: str) -> Optional[str]:
        """Stage ``paths`` and create a commit. Returns the new commit SHA.

        Returns ``None`` if there is nothing to commit, git is unavailable,
        or the operation fails.
        """

        if not paths:
            return None

        git = shutil.which("git")
        if not git:
            _logger.warning("git binary not found; skipping commit")
            return None

        # Make sure we are inside a git work tree before doing anything.
        if not self._inside_git_repo(git):
            _logger.warning("not inside a git work tree; skipping commit")
            return None

        rel_paths = self._normalize_paths(paths)
        if not rel_paths:
            return None

        try:
            subprocess.run(
                [git, "add", "--", *rel_paths],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            _logger.warning("git add failed: %s", exc.stderr.strip() or exc)
            return None

        # Bail if nothing is actually staged (e.g., transforms were no-ops
        # by the time we reached the commit step).
        diff_check = subprocess.run(
            [git, "diff", "--cached", "--quiet"],
            cwd=self.repo_root,
            check=False,
        )
        if diff_check.returncode == 0:
            _logger.info("nothing staged; skipping commit")
            return None

        subject = f"{COMMIT_PREFIX} {message}".strip()
        try:
            subprocess.run(
                [git, "commit", "-m", subject],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            _logger.warning("git commit failed: %s", exc.stderr.strip() or exc)
            return None

        try:
            sha = subprocess.run(
                [git, "rev-parse", "HEAD"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            return None
        return sha

    # ------------------------------------------------------------------
    def _inside_git_repo(self, git: str) -> bool:
        try:
            proc = subprocess.run(
                [git, "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            return False
        return proc.returncode == 0 and proc.stdout.strip() == "true"

    def _normalize_paths(self, paths: Sequence[Path]) -> list[str]:
        rels: list[str] = []
        repo_root = Path(self.repo_root).resolve()
        for p in paths:
            try:
                rel = Path(p).resolve().relative_to(repo_root)
            except ValueError:
                _logger.debug("ignoring path outside repo root: %s", p)
                continue
            rels.append(rel.as_posix())
        return rels
