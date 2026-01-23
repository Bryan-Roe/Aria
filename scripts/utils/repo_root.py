from pathlib import Path


def get_repo_root(start: Path | None = None) -> Path:
    """Return repository root by walking up until README.md or .git is found."""
    current = Path(start or __file__).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "README.md").exists():
            return candidate
        if (candidate / ".git").exists():
            return candidate if candidate.name != ".git" else candidate.parent
    return current
