"""Risk management for the Aria self-modifying loop.

The :class:`RiskManager` is the gatekeeper for all proposed changes. Every
upgrade plan must pass risk assessment before the executor is allowed to
modify a file. The defaults are conservative on purpose; loosening them
should be a deliberate, reviewed change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence

# Paths that must never be touched by the autonomous loop. These are
# encoded here (not just in YAML) so misconfiguration cannot disable them.
_DEFAULT_PROTECTED_PREFIXES: tuple[str, ...] = (
    ".git/",
    ".github/agents/",
    "datasets/",
    "data_out/",
    "local.settings.json",
    "secrets/",
    "AI/",
)

# Filenames that are sensitive even outside the protected prefixes above.
_DEFAULT_PROTECTED_NAMES: frozenset[str] = frozenset(
    {
        ".env",
        ".env.local",
        "local.settings.json",
        "id_rsa",
        "id_ed25519",
    }
)

# Hard cap on file size we are willing to inspect/modify. Anything larger is
# considered out of scope for the deterministic loop.
_MAX_FILE_BYTES = 512 * 1024  # 512 KiB

# Hard cap on the number of bytes a single plan is allowed to change. This
# guards against analyzers producing huge edits by mistake.
_MAX_PLAN_DELTA_BYTES = 16 * 1024  # 16 KiB


@dataclass(frozen=True)
class RiskAssessment:
    """Outcome of evaluating a proposed change."""

    allowed: bool
    reasons: tuple[str, ...] = ()

    @classmethod
    def allow(cls) -> "RiskAssessment":
        return cls(allowed=True, reasons=())

    @classmethod
    def deny(cls, *reasons: str) -> "RiskAssessment":
        return cls(allowed=False, reasons=tuple(reasons))


@dataclass
class RiskManager:
    """Evaluate whether a proposed change is safe to apply."""

    repo_root: Path
    protected_prefixes: Sequence[str] = field(
        default_factory=lambda: list(_DEFAULT_PROTECTED_PREFIXES)
    )
    protected_names: Sequence[str] = field(
        default_factory=lambda: list(_DEFAULT_PROTECTED_NAMES)
    )
    max_file_bytes: int = _MAX_FILE_BYTES
    max_plan_delta_bytes: int = _MAX_PLAN_DELTA_BYTES

    def __post_init__(self) -> None:
        self.repo_root = Path(self.repo_root).resolve()
        # Always include the hard-coded defaults even if a caller passed in
        # a narrower list. This prevents accidental privilege widening.
        merged_prefixes = set(self.protected_prefixes) | set(_DEFAULT_PROTECTED_PREFIXES)
        self.protected_prefixes = tuple(sorted(merged_prefixes))
        merged_names = set(self.protected_names) | set(_DEFAULT_PROTECTED_NAMES)
        self.protected_names = tuple(sorted(merged_names))

    # ------------------------------------------------------------------
    # Path-level checks
    # ------------------------------------------------------------------
    def is_path_protected(self, path: Path) -> bool:
        """Return True if ``path`` is inside a protected location."""

        try:
            rel = self._relative(path)
        except ValueError:
            # Anything outside the repo root is automatically protected.
            return True

        rel_posix = rel.as_posix()
        if rel.name in self.protected_names:
            return True
        for prefix in self.protected_prefixes:
            if rel_posix == prefix.rstrip("/") or rel_posix.startswith(prefix):
                return True
        return False

    def assess_file(self, path: Path) -> RiskAssessment:
        """Assess whether a single file is eligible for modification."""

        if self.is_path_protected(path):
            return RiskAssessment.deny(f"path is protected: {self._safe_display(path)}")

        if not path.exists():
            return RiskAssessment.deny(f"file does not exist: {self._safe_display(path)}")

        if path.is_symlink():
            return RiskAssessment.deny(f"refusing to modify symlink: {self._safe_display(path)}")

        if not path.is_file():
            return RiskAssessment.deny(f"not a regular file: {self._safe_display(path)}")

        try:
            size = path.stat().st_size
        except OSError as exc:  # pragma: no cover - filesystem race
            return RiskAssessment.deny(f"unable to stat file: {exc}")

        if size > self.max_file_bytes:
            return RiskAssessment.deny(
                f"file exceeds size cap ({size} > {self.max_file_bytes} bytes)"
            )

        return RiskAssessment.allow()

    # ------------------------------------------------------------------
    # Diff-level checks
    # ------------------------------------------------------------------
    def assess_change(self, path: Path, original: bytes, modified: bytes) -> RiskAssessment:
        """Assess a proposed in-memory file rewrite."""

        file_assessment = self.assess_file(path)
        if not file_assessment.allowed:
            return file_assessment

        if original == modified:
            return RiskAssessment.deny("no-op change")

        delta = abs(len(modified) - len(original))
        if delta > self.max_plan_delta_bytes:
            return RiskAssessment.deny(
                f"change delta exceeds cap ({delta} > {self.max_plan_delta_bytes} bytes)"
            )

        return RiskAssessment.allow()

    # ------------------------------------------------------------------
    # Iteration helpers
    # ------------------------------------------------------------------
    def iter_candidate_files(self, suffixes: Iterable[str] = (".py", ".md", ".yaml", ".yml")) -> List[Path]:
        """Yield repo files that pass the path-level safety filter.

        Used by the analyzer to scope its scan. We deliberately walk the
        filesystem instead of shelling out to ``git ls-files`` so the loop
        works in non-git checkouts (e.g., unit tests).
        """

        wanted = {s.lower() for s in suffixes}
        results: List[Path] = []
        for root, dirs, files in os.walk(self.repo_root):
            # Prune protected directories early.
            pruned: list[str] = []
            for d in dirs:
                rel = (Path(root, d).relative_to(self.repo_root)).as_posix() + "/"
                if any(rel == p or rel.startswith(p) for p in self.protected_prefixes):
                    continue
                pruned.append(d)
            dirs[:] = pruned

            for name in files:
                p = Path(root, name)
                if p.suffix.lower() not in wanted:
                    continue
                if self.is_path_protected(p):
                    continue
                results.append(p)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _relative(self, path: Path) -> Path:
        return Path(path).resolve().relative_to(self.repo_root)

    def _safe_display(self, path: Path) -> str:
        try:
            return self._relative(path).as_posix()
        except ValueError:
            return str(path)
