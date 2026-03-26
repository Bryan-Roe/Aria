#!/usr/bin/env python3
"""
Autonomous Code Agent - Uses local LLM to work on repository tasks.

This agent:
1. Takes a task description
2. Uses local LLM (Ollama/LMStudio) to understand and plan work
3. Reads relevant repo files
4. Makes code changes with safety validation
5. Runs tests to verify changes
6. Commits changes to git if tests pass

Usage:
    python scripts/autonomous_code_agent.py --task "fix failing test" --llm-type=ollama
    python scripts/autonomous_code_agent.py --task "improve code quality" --llm-type=lmstudio
"""

from __future__ import annotations

import os
import sys
import json
import subprocess
import logging
import time
import traceback
import importlib
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import argparse
import urllib.request
import urllib.error

# Make sibling script modules importable (e.g., autonomous_agent_tasks.py)
_SCRIPT_DIR = Path(__file__).parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    _tasks_mod = importlib.import_module("autonomous_agent_tasks")
    get_task_guidance = getattr(_tasks_mod, "get_task_guidance", None)
except Exception:
    get_task_guidance = None  # type: ignore[assignment]

_LOGGER = logging.getLogger(__name__)

# Configuration
DEFAULT_LM_STUDIO_URL = os.getenv(
    "LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
DEFAULT_LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "local-model")
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

REPO_ROOT = Path(__file__).parent.parent
DATA_OUT = REPO_ROOT / "data_out" / "autonomous_agent"
STATUS_FILE = DATA_OUT / "status.json"

# Safety constraints
MAX_FILE_SIZE = 100_000  # bytes
MAX_CHANGES_PER_FILE = 5
MAX_TASK_TOKENS = 2000
MIN_TEST_PASSING_RATE = 0.8  # 80% tests must pass


@dataclass
class AgentState:
    """Current state of the agent's work."""
    task_id: str
    task_description: str
    status: str  # planning, implementing, testing, complete, failed
    llm_type: str
    files_modified: List[str]
    tests_run: int
    tests_passed: int
    tests_failed: int
    reasoning: str
    commits: List[str]
    errors: List[str]
    started_at: str
    updated_at: str
    # Tracking fields
    task_category: str = "unknown"
    duration_seconds: float = 0.0
    tokens_estimated: int = 0
    rollback_performed: bool = False
    dry_run: bool = False
    tests_skipped: bool = False
    plan: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.updated_at = datetime.now().isoformat()

    def mark_file_modified(self, filepath: str) -> None:
        if filepath not in self.files_modified:
            self.files_modified.append(filepath)
        self.updated_at = datetime.now().isoformat()

    def save(self, status_file: Path = STATUS_FILE) -> None:
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class RepositoryContext:
    """Information about the repository structure and state."""

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.git_available = self._check_git_available()
        self.current_branch = self._get_current_branch()
        self.uncommitted_changes = self._get_uncommitted_changes()

    def _check_git_available(self) -> bool:
        """Check if git is available."""
        try:
            subprocess.run(["git", "--version"],
                           capture_output=True, check=True, cwd=self.repo_root)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _get_current_branch(self) -> str:
        """Get current git branch."""
        if not self.git_available:
            return "unknown"
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _get_uncommitted_changes(self) -> List[str]:
        """Get list of uncommitted changes."""
        if not self.git_available:
            return []
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                check=True,
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

    def file_exists(self, filepath: str) -> bool:
        """Check if file exists in repo."""
        full_path = self.repo_root / filepath
        return full_path.exists() and full_path.is_file()

    def read_file(self, filepath: str) -> Optional[str]:
        """Safely read file from repo."""
        full_path = self.repo_root / filepath
        if not full_path.exists():
            return None
        if not full_path.is_file():
            return None
        if full_path.stat().st_size > MAX_FILE_SIZE:
            return f"# File too large ({full_path.stat().st_size} bytes)"

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except (UnicodeDecodeError, PermissionError) as e:
            return f"# Error reading file: {e}"

    def list_files_matching(self, pattern: str, max_files: int = 20) -> List[str]:
        """Find files matching pattern."""
        import glob

        results = []
        for match in glob.glob(str(self.repo_root / pattern), recursive=True):
            rel_path = str(Path(match).relative_to(self.repo_root))
            if not rel_path.startswith("."):
                results.append(rel_path)
            if len(results) >= max_files:
                break
        return results

    def get_git_status(self) -> str:
        """Get git status."""
        if not self.git_available:
            return "Git not available"
        try:
            result = subprocess.run(
                ["git", "status"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                check=True,
            )
            return result.stdout[:500]  # Truncate
        except subprocess.CalledProcessError:
            return "Unable to get git status"


def _estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token)."""
    return max(1, len(text) // 4)


class EchoLLMClient:
    """Test/echo LLM client — returns canned planning responses without requiring a running LLM."""

    def __init__(self, base_url: str = "", model: str = "echo", llm_type: str = "echo"):
        self.base_url = base_url
        self.model = model
        self.llm_type = llm_type
        self._call_count = 0

    def query(self, prompt: str, max_tokens: int = 2000) -> str:
        self._call_count += 1
        # Return different helpful responses depending on what the prompt contains.
        prompt_lower = prompt.lower()
        if "list" in prompt_lower and "file" in prompt_lower:
            # File identification call
            return "scripts/autonomous_code_agent.py\nscripts/autonomous_agent_tasks.py"
        if "step" in prompt_lower or "plan" in prompt_lower or "analyze" in prompt_lower:
            # Planning call
            return (
                "[Echo Plan]\n"
                "1. Understand the task requirements\n"
                "2. Identify the files that need modification\n"
                "3. Implement changes with proper error handling\n"
                "4. Validate with tests\n"
                "5. Commit changes with descriptive message\n"
                "Risks: low — echo mode returns no actual modifications"
            )
        # Generic response
        return f"[Echo Response {self._call_count}] Acknowledged: {prompt[:80]}"

    def is_available(self) -> bool:
        return True


class LocalLLMClient:
    """Simple HTTP client for local LLM servers (Ollama, LMStudio)."""

    def __init__(self, base_url: str, model: str, llm_type: str = "ollama"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.llm_type = llm_type
        _LOGGER.info(
            f"Initialized {llm_type} client: {base_url} model={model}")

    def query(self, prompt: str, max_tokens: int = 2000) -> str:
        """Query the local LLM."""
        try:
            if self.llm_type == "ollama":
                return self._query_ollama(prompt, max_tokens)
            elif self.llm_type == "lmstudio":
                return self._query_lmstudio(prompt, max_tokens)
            else:
                return f"Unknown LLM type: {self.llm_type}"
        except Exception as e:
            _LOGGER.error(f"Error querying LLM: {e}\n{traceback.format_exc()}")
            return f"Error: {str(e)}"

    def _query_ollama(self, prompt: str, max_tokens: int) -> str:
        """Query Ollama API."""
        import json as json_module

        url = f"{self.base_url}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "num_predict": max_tokens,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json_module.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json_module.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip()
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}: {e}")

    def _query_lmstudio(self, prompt: str, max_tokens: int) -> str:
        """Query LM Studio API (OpenAI-compatible)."""
        import json as json_module

        url = f"{self.base_url}/chat/completions"
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json_module.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json_module.loads(response.read().decode("utf-8"))
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                return ""
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot connect to LM Studio at {self.base_url}: {e}")

    def is_available(self) -> bool:
        """Check if LLM is available."""
        try:
            response = self.query("test", max_tokens=10)
            return response is not None and len(response) > 0
        except Exception:
            return False


class CodeAgent:
    """Autonomous agent for code repository tasks."""

    def __init__(self, llm_type: str = "ollama", model: Optional[str] = None):
        self.llm_type = llm_type.lower()
        self.model = model

        if self.llm_type == "ollama":
            self.llm: Union[LocalLLMClient, EchoLLMClient] = LocalLLMClient(
                base_url=DEFAULT_OLLAMA_URL,
                model=self.model or DEFAULT_OLLAMA_MODEL,
                llm_type="ollama",
            )
        elif self.llm_type == "lmstudio":
            self.llm = LocalLLMClient(
                base_url=DEFAULT_LM_STUDIO_URL,
                model=self.model or DEFAULT_LMSTUDIO_MODEL,
                llm_type="lmstudio",
            )
        elif self.llm_type == "echo":
            self.llm = EchoLLMClient(model=self.model or "echo")
        else:
            raise ValueError(
                f"Unknown LLM type: {llm_type}. Choose: ollama, lmstudio, echo")

        self.repo = RepositoryContext()
        self.state: Optional[AgentState] = None
        self._total_tokens = 0
        self._original_file_contents: Dict[str, Optional[str]] = {}
        self._init_logging()

    def _init_logging(self) -> None:
        """Initialize logging."""
        DATA_OUT.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(DATA_OUT / "agent.log")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        _LOGGER.addHandler(handler)
        _LOGGER.setLevel(logging.DEBUG)

    def _llm_query(self, prompt: str, max_tokens: int = MAX_TASK_TOKENS) -> str:
        """Query LLM and track token usage."""
        response = self.llm.query(prompt, max_tokens)
        self._total_tokens += _estimate_tokens(prompt) + \
            _estimate_tokens(response)
        if self.state:
            self.state.tokens_estimated = self._total_tokens
        return response

    def plan_task(self, task_description: str) -> str:
        """Use LLM to plan the task, using category-specialized prompts."""
        try:
            if get_task_guidance is not None:
                guidance = get_task_guidance(task_description)
            else:
                guidance = {}
            task_category = guidance.get("category", "unknown")
            specialized_intro = guidance.get("specialized_prompt", "")
            file_hints = guidance.get("file_patterns", [])
            if self.state:
                self.state.task_category = task_category
        except Exception:
            specialized_intro = ""
            file_hints = []
            task_category = "unknown"

        file_patterns_note = (
            f"Likely search patterns: {', '.join(file_hints)}\n" if file_hints else ""
        )

        prompt = (
            f"{specialized_intro}\n\n" if specialized_intro else ""
        ) + f"""You are an expert code agent working on a Python repository.

Task: {task_description}
{file_patterns_note}
Provide a concise action plan:
1. Main goal
2. Key files to modify
3. Step-by-step implementation plan
4. Validation approach
5. Risk mitigation"""

        _LOGGER.info(f"Planning task [{task_category}]: {task_description}")
        reasoning = self._llm_query(prompt, max_tokens=MAX_TASK_TOKENS)
        if self.state:
            self.state.reasoning = reasoning
            self.state.plan = reasoning
        return reasoning

    def identify_files(self, task_description: str) -> List[str]:
        """Identify which files are relevant to the task."""
        prompt = f"""Based on this task: {task_description}

List the most relevant file paths in this Python/repo repository that likely need to be reviewed or modified.

Repository structure hints:
- scripts/* - orchestration scripts
- tests/* - unit tests
- ai-projects/chat-cli/src/* - chat provider code
- apps/* - web applications
- shared/* - shared utilities
- function_app.py - Azure Functions endpoints

Respond with ONLY a list of file paths relative to repo root (one per line). No explanations, no leading slashes."""

        response = self._llm_query(prompt, max_tokens=500)
        files = []
        for line in response.split("\n"):
            line = line.strip().lstrip("/")
            if line and not line.startswith("#") and not line.startswith("["):
                if self.repo.file_exists(line):
                    files.append(line)

        _LOGGER.info(f"Identified {len(files)} relevant file(s): {files}")
        return files[:5]  # Limit to 5 files

    def read_context(self, filepath: str) -> str:
        """Read file context for the agent."""
        content = self.repo.read_file(filepath)
        if content is None:
            return f"# File not found: {filepath}"
        return f"# File: {filepath}\n\n{content}"

    def _snapshot_file(self, filepath: str) -> None:
        """Capture the current file content once so rollbacks preserve user work."""
        if filepath in self._original_file_contents:
            return
        full_path = self.repo.repo_root / filepath
        if full_path.exists() and full_path.is_file():
            self._original_file_contents[filepath] = full_path.read_text(
                encoding="utf-8"
            )
        else:
            self._original_file_contents[filepath] = None

    def _restore_modified_files(self) -> bool:
        """Restore only the files this agent changed, preserving unrelated edits."""
        restored = False
        for filepath, original_content in self._original_file_contents.items():
            full_path = self.repo.repo_root / filepath
            try:
                if original_content is None:
                    if full_path.exists():
                        full_path.unlink()
                else:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(original_content, encoding="utf-8")
                restored = True
            except OSError as exc:
                _LOGGER.error(f"Failed to restore {filepath}: {exc}")
        if restored and self.state:
            self.state.rollback_performed = True
        return restored

    def implement_changes(self, task_description: str, files: List[str]) -> List[str]:
        """Use LLM to implement code changes in identified files."""
        modified = []
        for filepath in files:
            content = self.repo.read_file(filepath)
            if content is None:
                _LOGGER.warning(f"Skipping {filepath}: not found")
                continue

            # Limit content sent to LLM to avoid token overflow
            truncated = content[:4000]
            suffix_note = (
                f"\n# ... (truncated, {len(content)} bytes total)"
                if len(content) > 4000 else ""
            )

            prompt = f"""Task: {task_description}

File: {filepath}
Current content:
```
{truncated}{suffix_note}
```

Provide the COMPLETE updated file content implementing the task changes.
Return ONLY the file content — no explanation, no markdown fences, no commentary.
If no changes are needed for this file, return the original content unchanged."""

            _LOGGER.info(f"Requesting LLM changes for {filepath}")
            new_content = self._llm_query(prompt, max_tokens=MAX_TASK_TOKENS)

            if not new_content or len(new_content) < 20:
                _LOGGER.warning(
                    f"LLM returned empty/short response for {filepath}, skipping")
                continue

            # Remove accidental markdown fences if present
            stripped = new_content.strip()
            if stripped.startswith("```"):
                lines = stripped.split("\n")
                # Drop first and last fence lines
                inner = lines[1:]
                if inner and inner[-1].strip() == "```":
                    inner = inner[:-1]
                new_content = "\n".join(inner)

            try:
                full_path = self.repo.repo_root / filepath
                self._snapshot_file(filepath)
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(new_content, encoding="utf-8")
                if self.state is not None:
                    self.state.mark_file_modified(filepath)
                modified.append(filepath)
                _LOGGER.info(f"Updated {filepath} ({len(new_content)} bytes)")
            except OSError as e:
                _LOGGER.error(f"Failed to write {filepath}: {e}")

        return modified

    def run_tests(self) -> Dict[str, Any]:
        """Run test suite to validate changes."""
        _LOGGER.info("Running tests...")

        repo_root = self.repo.repo_root
        test_script = repo_root / "scripts" / "test_runner.py"
        if not test_script.exists():
            _LOGGER.warning("Test runner not found, skipping tests")
            return {"total": 0, "passed": 0, "failed": 0, "success": False}

        try:
            import re

            result = subprocess.run(
                [sys.executable, str(test_script), "--unit"],
                capture_output=True,
                text=True,
                cwd=repo_root,
                timeout=300,
            )

            output = result.stdout + result.stderr
            _LOGGER.debug(f"Test output: {output[:500]}")

            # Best-effort parse of pytest summary
            total = 0
            passed = 0
            failed = 0

            collected_match = re.search(
                r"collected\s+(\d+)\s+items(?:\s*/\s*(\d+)\s+deselected)?",
                output,
            )
            if collected_match:
                collected = int(collected_match.group(1))
                deselected = int(collected_match.group(
                    2)) if collected_match.group(2) else 0
                total = max(0, collected - deselected)

            passed_match = re.search(r"(\d+)\s+passed", output)
            failed_match = re.search(r"(\d+)\s+failed", output)
            error_match = re.search(r"(\d+)\s+error", output)

            if passed_match:
                passed = int(passed_match.group(1))
            fail_count = 0
            if failed_match:
                fail_count += int(failed_match.group(1))
            if error_match:
                fail_count += int(error_match.group(1))
            failed = fail_count

            test_results = {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success": result.returncode == 0,
                "output": output[:500],
            }
            return test_results

        except subprocess.TimeoutExpired:
            _LOGGER.error("Tests timed out")
            return {"total": 0, "passed": 0, "failed": 0, "success": False, "error": "timeout"}
        except Exception as e:
            _LOGGER.error(f"Error running tests: {e}")
            return {"total": 0, "passed": 0, "failed": 0, "success": False, "error": str(e)}

    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> bool:
        """Commit changes to git."""
        if not self.repo.git_available:
            _LOGGER.warning("Git not available, skipping commit")
            return False

        files_to_stage = files or (self.state.files_modified if self.state else [])
        if not files_to_stage:
            _LOGGER.warning("No agent-modified files provided for commit")
            return False

        try:
            # Stage only files the agent modified to avoid scooping up user work.
            subprocess.run(
                ["git", "add", "--"] + files_to_stage,
                cwd=self.repo.repo_root,
                check=True,
                capture_output=True,
            )

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo.repo_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                _LOGGER.info(f"Committed changes: {commit_hash}")
                if self.state:
                    self.state.commits.append(commit_hash)
                return True
            else:
                _LOGGER.warning(f"Commit failed: {result.stderr}")
                return False

        except Exception as e:
            _LOGGER.error(f"Error committing changes: {e}")
            return False

    def execute_task(
        self,
        task_description: str,
        dry_run: bool = False,
        skip_tests: bool = False,
    ) -> AgentState:
        """Execute a task end-to-end with rollback safety."""
        task_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        _start = time.monotonic()

        self.state = AgentState(
            task_id=task_id,
            task_description=task_description,
            status="planning",
            llm_type=self.llm_type,
            files_modified=[],
            tests_run=0,
            tests_passed=0,
            tests_failed=0,
            reasoning="",
            commits=[],
            errors=[],
            started_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            dry_run=dry_run,
        )
        self._total_tokens = 0

        _LOGGER.info(
            f"Starting task {task_id} (dry_run={dry_run}): {task_description}")
        self.state.save()

        # ── Phase 1: Plan ────────────────────────────────────────────────────
        try:
            self.state.status = "planning"
            self.state.save()
            reasoning = self.plan_task(task_description)
            _LOGGER.info(f"Planning complete: {reasoning[:200]}")
        except Exception as e:
            self.state.add_error(f"Planning failed: {e}")
            self.state.status = "failed"
            self.state.duration_seconds = time.monotonic() - _start
            self.state.save()
            return self.state

        # ── Phase 2: Identify files ──────────────────────────────────────────
        try:
            files = self.identify_files(task_description)
            _LOGGER.info(f"Identified files: {files}")
        except Exception as e:
            self.state.add_error(f"File identification failed: {e}")
            self.state.status = "failed"
            self.state.duration_seconds = time.monotonic() - _start
            self.state.save()
            return self.state

        # ── Phase 3: Implement ───────────────────────────────────────────────
        self.state.status = "implementing"
        self.state.save()
        self._original_file_contents = {}
        if dry_run:
            _LOGGER.info("Dry-run mode: skipping file modifications")
            for f in files:
                _LOGGER.info(f"  Would read/modify: {f}")
        else:
            try:
                self.implement_changes(task_description, files)
            except Exception as e:
                self.state.add_error(f"Implementation failed: {e}")
                _LOGGER.error(f"Implementation error: {e}")

        # ── Phase 4: Test ────────────────────────────────────────────────────
        tests_passed = False
        if skip_tests:
            self.state.tests_skipped = True
            tests_passed = True
            _LOGGER.info("Skipping tests as requested (skip_tests=True)")
        else:
            self.state.status = "testing"
            self.state.save()
            try:
                test_results = self.run_tests()
                self.state.tests_run = test_results.get("total", 0)
                self.state.tests_passed = test_results.get("passed", 0)
                self.state.tests_failed = test_results.get("failed", 0)
                tests_passed = test_results.get("success", False)
                _LOGGER.info(
                    f"Tests: passed={tests_passed} results={test_results}")
                if not tests_passed:
                    self.state.add_error("Validation tests failed")
            except Exception as e:
                self.state.add_error(f"Testing failed: {e}")

        # ── Rollback if tests failed ─────────────────────────────────────────
        if not dry_run and not tests_passed and self.state.files_modified:
            _LOGGER.warning(
                "Tests failed after implementation — rolling back changes")
            try:
                if self._restore_modified_files():
                    _LOGGER.info("Rollback complete (restored original file snapshots)")
            except Exception as rb_err:
                _LOGGER.error(f"Rollback failed: {rb_err}")

        # ── Phase 5: Commit ──────────────────────────────────────────────────
        if (
            not dry_run
            and tests_passed
            and self.state.files_modified
            and not self.state.errors
        ):
            try:
                commit_msg = f"agent/{task_id}: {task_description[:60]}"
                self.commit_changes(commit_msg, files=self.state.files_modified)
            except Exception as e:
                self.state.add_error(f"Commit failed: {e}")

        self.state.status = "complete" if not self.state.errors else "failed"
        self.state.duration_seconds = round(time.monotonic() - _start, 2)
        self.state.tokens_estimated = self._total_tokens
        self.state.save()
        _LOGGER.info(
            f"Task {task_id} complete in {self.state.duration_seconds}s "
            f"(~{self._total_tokens} tokens)"
        )
        return self.state


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Code Agent - works on repo tasks using local LLM"
    )
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        help="Task description for the agent to work on",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Specific model to use (defaults to provider-specific model)",
    )
    parser.add_argument(
        "--llm-type",
        type=str,
        default="ollama",
        choices=["ollama", "lmstudio", "echo"],
        help="Type of local LLM to use (echo = no LLM required, for testing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyse but don't modify files or commit",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip validation test execution (useful for fast dry-runs)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run agent
    try:
        agent = CodeAgent(llm_type=args.llm_type, model=args.model)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Check if LLM is available
    if not agent.llm.is_available():
        print(
            f"Error: {args.llm_type} LLM is not available at the configured URL")
        if args.llm_type == "ollama":
            print("Configure: export OLLAMA_BASE_URL=http://127.0.0.1:11434")
            print("Or install Ollama from https://ollama.ai")
        elif args.llm_type == "lmstudio":
            print("Configure: export LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1")
            print("Or download LM Studio from https://lmstudio.ai")
        sys.exit(1)

    # Execute task
    state = agent.execute_task(
        args.task,
        dry_run=args.dry_run,
        skip_tests=args.skip_tests,
    )

    # Print summary
    print("\n" + "=" * 60)
    print(f"Task: {state.task_description}")
    print(f"Status: {state.status}")
    print(f"Files modified: {len(state.files_modified)}")
    print(f"Tests run: {state.tests_run}")
    print(f"Tests passed: {state.tests_passed}")
    print(f"Tests failed: {state.tests_failed}")
    print(f"Tests skipped: {state.tests_skipped}")
    print(f"Commits: {len(state.commits)}")
    if state.errors:
        print(f"Errors: {len(state.errors)}")
        for error in state.errors[:3]:
            print(f"  - {error}")
    print("=" * 60)

    # Exit code
    sys.exit(0 if state.status == "complete" else 1)


if __name__ == "__main__":
    main()
