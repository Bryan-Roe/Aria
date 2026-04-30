"""Loader and validator for AI projects entry points registry.

Reads scripts/ai_projects_entrypoints.yaml and provides utilities for:
- Listing available projects and their capabilities
- Checking project dependencies
- Verifying entry point availability
- Reporting project status
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class EntryPointsRegistry:
    """Load and query the AI projects entry points registry."""
    
    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize registry from YAML file.
        
        Args:
            registry_path: Path to ai_projects_entrypoints.yaml.
                          Defaults to scripts/ai_projects_entrypoints.yaml
        """
        if registry_path is None:
            # Infer from repo root (go up from shared/core to repo root, then to scripts)
            shared_dir = Path(__file__).parent.parent  # shared/
            repo_root = shared_dir.parent  # repo root
            registry_path = repo_root / "scripts" / "ai_projects_entrypoints.yaml"
        
        self.registry_path = registry_path
        self.data: Dict[str, Any] = {}
        self.projects: Dict[str, Any] = {}
        
        self._load()
    
    def _load(self) -> None:
        """Load registry from YAML file."""
        if not self.registry_path.exists():
            logging.warning(f"Entry points registry not found: {self.registry_path}")
            return
        
        if yaml is None:
            logging.warning("PyYAML not available; entry points registry unavailable")
            return
        
        try:
            with open(self.registry_path, 'r') as f:
                self.data = yaml.safe_load(f) or {}
            self.projects = self.data.get('projects', {})
            logging.info(f"Loaded {len(self.projects)} projects from registry")
        except Exception as e:
            logging.error(f"Failed to load entry points registry: {e}")
    
    def list_projects(self) -> List[str]:
        """Return list of all project names."""
        return list(self.projects.keys())
    
    def get_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get project metadata by name."""
        return self.projects.get(project_name)
    
    def get_entry_point(self, project_name: str, entry_point_name: str) -> Optional[Dict[str, Any]]:
        """Get entry point metadata."""
        project = self.get_project(project_name)
        if not project:
            return None
        
        entry_points = project.get('entry_points', {})
        return entry_points.get(entry_point_name)
    
    def list_entry_points(self, project_name: str) -> List[str]:
        """List all entry points for a project."""
        project = self.get_project(project_name)
        if not project:
            return []
        
        return list(project.get('entry_points', {}).keys())
    
    def get_dependencies(self, project_name: str) -> List[str]:
        """Get list of projects this one depends on."""
        project = self.get_project(project_name)
        if not project:
            return []
        
        return project.get('depends_on', [])
    
    def is_isolated(self, project_name: str) -> bool:
        """Check if project requires separate venv."""
        project = self.get_project(project_name)
        if not project:
            return False
        
        return project.get('venv_isolated', False)
    
    def get_description(self, project_name: str) -> str:
        """Get project description."""
        project = self.get_project(project_name)
        if not project:
            return "(unknown)"
        
        return project.get('description', '(no description)')
    
    def list_by_type(self, entry_type: str) -> Dict[str, List[str]]:
        """List all entry points grouped by type.
        
        Args:
            entry_type: Type to filter by (script, module, server, asgi, mcp)
        
        Returns:
            Dict mapping project names to lists of matching entry point names
        """
        result = {}
        
        for project_name, project in self.projects.items():
            entry_points = project.get('entry_points', {})
            matching = [
                ep_name for ep_name, ep_data in entry_points.items()
                if ep_data.get('type') == entry_type
            ]
            if matching:
                result[project_name] = matching
        
        return result
    
    def get_ports(self) -> Dict[str, int]:
        """Get all server entry points and their ports.
        
        Returns:
            Dict mapping "project:entry_point" to port number
        """
        ports = {}
        
        for project_name, project in self.projects.items():
            entry_points = project.get('entry_points', {})
            for ep_name, ep_data in entry_points.items():
                if 'port' in ep_data:
                    key = f"{project_name}:{ep_name}"
                    ports[key] = ep_data['port']
        
        return ports
    
    def validate_dependencies(self, project_name: str) -> List[str]:
        """Check if all dependencies for a project are available.
        
        Returns:
            List of missing dependencies (empty if all available)
        """
        deps = self.get_dependencies(project_name)
        missing = []
        
        for dep in deps:
            if dep not in self.projects:
                missing.append(dep)
        
        return missing
    
    def status_report(self) -> str:
        """Return a human-readable status report."""
        if not self.data:
            return "Entry points registry not loaded"
        
        lines = [
            "=== AI Projects Entry Points Registry ===",
            f"Version: {self.data.get('metadata', {}).get('version', '?')}",
            f"Total projects: {len(self.projects)}",
            "",
            "Projects:",
        ]
        
        for project_name in sorted(self.projects.keys()):
            project = self.projects[project_name]
            isolated = "isolated" if project.get('venv_isolated') else "shared"
            entry_points = project.get('entry_points', {})
            
            lines.append(f"  {project_name} ({isolated})")
            lines.append(f"    {project.get('description', '(no description)')}")
            lines.append(f"    Entry points: {', '.join(entry_points.keys())}")
        
        return "\n".join(lines)


# Singleton instance (lazy-loaded)
_registry_instance: Optional[EntryPointsRegistry] = None


def get_registry() -> EntryPointsRegistry:
    """Get the singleton entry points registry."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = EntryPointsRegistry()
    return _registry_instance


__all__ = ['EntryPointsRegistry', 'get_registry']
