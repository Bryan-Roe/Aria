"""Shared foundation for repository automation agents.

This module provides a small, dependency-light framework that individual
automation agents build on. Each agent performs one concrete, deterministic
repo-maintenance task and reports a structured :class:`AgentResult`.

Conventions (consistent with the rest of the repo):
- Agents write a machine-readable ``status.json`` to
  ``data_out/agents/<agent-name>/status.json``.
- Agents are deterministic and side-effect free with respect to source files
  (they *inspect* the repo and report; they do not modify tracked code).
- Agents register themselves with :func:`register` so a runner can discover
  and execute them.

Usage::

    from scripts.agents.base import AutomationAgent, AgentResult, register

    @register
    class MyAgent(AutomationAgent):
        name = "my-agent"
        description = "Does a useful repo check."

        def run(self) -> AgentResult:
            return self.make_result(status="ok", summary="nothing to do")
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Repo root is three levels up: scripts/agents/base.py -> repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DATA_DIR = REPO_ROOT / "data_out" / "agents"

# Directories that should never be scanned by source-inspecting agents.
DEFAULT_EXCLUDE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "data_out",
        "datasets",
        "build",
        "dist",
        ".tox",
        "site-packages",
    }
)

# Valid overall agent statuses, ordered from healthy to unhealthy.
VALID_STATUSES: tuple[str, ...] = ("ok", "warning", "error")


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentResult:
    """Structured result returned by an automation agent.

    Attributes:
        name: The agent's name.
        status: One of ``ok``, ``warning``, or ``error``.
        summary: A short human-readable description of the outcome.
        findings: A list of structured finding dicts (agent-specific schema).
        metrics: A dict of numeric/string metrics for dashboards.
        timestamp: ISO-8601 UTC time the result was produced.
    """

    name: str
    status: str
    summary: str
    findings: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}; expected one of {VALID_STATUSES}"
            )

    @property
    def ok(self) -> bool:
        """True when the agent reported a healthy (``ok``) status."""
        return self.status == "ok"

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation of the result."""
        return asdict(self)


def iter_source_files(
    root: Path | str | None = None,
    *,
    extensions: Iterable[str] | None = None,
    exclude_dirs: Iterable[str] | None = None,
) -> Iterator[Path]:
    """Yield source files under *root*, skipping excluded directories.

    Args:
        root: Directory to scan. Defaults to the repository root.
        extensions: Iterable of file suffixes to include (e.g. ``{".py"}``).
            Matching is case-insensitive and tolerant of a missing leading dot.
            When ``None``, all files are yielded.
        exclude_dirs: Directory names to skip entirely. Defaults to
            :data:`DEFAULT_EXCLUDE_DIRS`.

    Yields:
        Paths to matching files, in sorted order for deterministic output.
    """
    base = Path(root) if root is not None else REPO_ROOT
    excluded = set(DEFAULT_EXCLUDE_DIRS if exclude_dirs is None else exclude_dirs)

    normalized_exts: set[str] | None
    if extensions is None:
        normalized_exts = None
    else:
        normalized_exts = {
            ("." + e.lstrip(".")).lower() for e in extensions
        }

    if not base.exists():
        return

    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        # Skip any file living inside an excluded directory.
        if any(part in excluded for part in path.parts):
            continue
        if normalized_exts is not None and path.suffix.lower() not in normalized_exts:
            continue
        yield path


class AutomationAgent:
    """Base class for deterministic repository automation agents.

    Subclasses must set :attr:`name` and :attr:`description` and implement
    :meth:`run`. Use :meth:`make_result` to build results and
    :meth:`write_status` to persist them.
    """

    #: Unique, kebab-case identifier for the agent.
    name: str = "automation-agent"
    #: One-line human-readable description.
    description: str = ""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else REPO_ROOT

    # -- contract ---------------------------------------------------------
    def run(self) -> AgentResult:  # pragma: no cover - abstract
        """Execute the agent and return an :class:`AgentResult`."""
        raise NotImplementedError

    # -- helpers ----------------------------------------------------------
    def make_result(
        self,
        *,
        status: str,
        summary: str,
        findings: list[dict] | None = None,
        metrics: dict | None = None,
    ) -> AgentResult:
        """Construct an :class:`AgentResult` tagged with this agent's name."""
        return AgentResult(
            name=self.name,
            status=status,
            summary=summary,
            findings=findings or [],
            metrics=metrics or {},
        )

    def status_path(self) -> Path:
        """Return the path this agent writes its status JSON to."""
        return AGENTS_DATA_DIR / self.name / "status.json"

    def write_status(self, result: AgentResult) -> Path:
        """Persist *result* to ``data_out/agents/<name>/status.json``.

        Returns the path written. Creates parent directories as needed.
        """
        path = self.status_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        return path


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
_AGENT_REGISTRY: dict[str, type[AutomationAgent]] = {}


def register(cls: type[AutomationAgent]) -> type[AutomationAgent]:
    """Class decorator that registers an agent for discovery.

    Raises:
        ValueError: if the agent has no ``name`` or the name is already taken
            by a different class.
    """
    name = getattr(cls, "name", None)
    if not name or name == AutomationAgent.name:
        raise ValueError(f"Agent {cls.__name__} must define a unique 'name'")
    existing = _AGENT_REGISTRY.get(name)
    if existing is not None and existing is not cls:
        raise ValueError(f"Agent name {name!r} already registered by {existing.__name__}")
    _AGENT_REGISTRY[name] = cls
    return cls


def get_registered_agents() -> dict[str, type[AutomationAgent]]:
    """Return a copy of the agent registry keyed by agent name."""
    return dict(_AGENT_REGISTRY)
