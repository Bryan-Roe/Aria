"""
Task definitions and specializations for autonomous code agent.

This module defines task categories and provides specialized prompts/strategies
for different types of work the agent can perform.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskCategory(Enum):
    """Types of tasks the agent can handle."""

    BUG_FIX = "bug_fix"
    FEATURE = "feature"
    REFACTOR = "refactor"
    TEST = "test"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CLEANUP = "cleanup"


@dataclass
class TaskDefinition:
    """Definition of a specialized task."""

    category: TaskCategory
    title: str
    description: str
    file_patterns: List[str]  # Which files to look at
    success_criteria: List[str]
    risk_level: str  # low, medium, high
    estimated_complexity: str  # simple, moderate, complex
    prompt_template: str

    def get_specialized_prompt(self, user_task: str) -> str:
        """Get the specialized prompt for this task category."""
        return self.prompt_template.format(task=user_task)


# Task templates by category
BUG_FIX_PROMPT = """You are an expert debugging agent. Your task is to:
{task}

Steps:
1. Understand the reported bug or failing test
2. Identify the root cause by reading relevant code
3. Make minimal, targeted fixes
4. Add test cases to prevent regression
5. Verify the fix doesn't break other tests

Focus on:
- Root cause, not symptoms
- Minimal changes
- Clear commit messages explaining the fix
- Preserving existing functionality
"""

FEATURE_PROMPT = """You are a feature development agent. Your task is to:
{task}

Steps:
1. Understand the feature requirements
2. Identify necessary files and interfaces
3. Implement the feature with proper error handling
4. Add comprehensive tests
5. Update documentation
6. Ensure backward compatibility

Focus on:
- Clean API design
- Error handling and validation
- Test coverage
- Documentation
- No breaking changes
"""

REFACTOR_PROMPT = """You are a code refactoring agent. Your task is to:
{task}

Steps:
1. Understand current structure and pain points
2. Identify improvement opportunities
3. Refactor incrementally to maintain functionality
4. Ensure all tests pass
5. Document the improvements

Focus on:
- Maintainability
- DRY principle
- Readability
- No behavior changes
- Comprehensive test validation
"""

TEST_PROMPT = """You are a test development agent. Your task is to:
{task}

Steps:
1. Understand what needs testing
2. Identify test scenarios and edge cases
3. Write comprehensive test cases
4. Ensure tests follow project conventions
5. Validate all tests pass

Focus on:
- High coverage
- Edge cases and errors
- Clear test names
- Good assertions
- Following pytest patterns
"""

SECURITY_PROMPT = """You are a security-focused agent. Your task is to:
{task}

Steps:
1. Identify security issues or requirements
2. Research best practices
3. Implement security fixes or features
4. Add security-specific tests
5. Document security rationale

Focus on:
- Input validation
- Injection prevention
- Authentication/authorization
- Secrets handling
- Secure defaults
- Security test coverage
"""

PERFORMANCE_PROMPT = """You are a performance optimization agent. Your task is to:
{task}

Steps:
1. Identify performance issues or targets
2. Profile or analyze current performance
3. Implement optimizations
4. Verify improvements with before/after metrics
5. Ensure no functional regression

Focus on:
- Measurable improvements
- No correctness changes
- Clear performance comments
- Before/after documentation
- Test coverage maintenance
"""

DOCUMENTATION_PROMPT = """You are a documentation agent. Your task is to:
{task}

Steps:
1. Identify documentation gaps or improvements
2. Write clear, complete documentation
3. Add code examples where relevant
4. Update existing documentation for consistency
5. Validate links and references

Focus on:
- Clarity and completeness
- Examples and use cases
- Proper formatting
- Link accuracy
- Consistency with existing docs
"""

CLEANUP_PROMPT = """You are a code cleanup agent. Your task is to:
{task}

Steps:
1. Identify cleanup opportunities
2. Remove dead code, unused imports, etc.
3. Fix formatting and style issues
4. Update deprecations
5. Validate all tests still pass

Focus on:
- Dead code removal
- Unused imports
- Style consistency
- Deprecation updates
- No functional changes
"""

# Task definition database
TASK_DEFINITIONS: Dict[TaskCategory, TaskDefinition] = {
    TaskCategory.BUG_FIX: TaskDefinition(
        category=TaskCategory.BUG_FIX,
        title="Bug Fix",
        description="Fix bugs and failing tests",
        file_patterns=["tests/", "src/", "scripts/"],
        success_criteria=[
            "Failing test now passes",
            "No new test failures",
            "Root cause identified and fixed",
            "Fix is minimal and focused",
        ],
        risk_level="medium",
        estimated_complexity="moderate",
        prompt_template=BUG_FIX_PROMPT,
    ),
    TaskCategory.FEATURE: TaskDefinition(
        category=TaskCategory.FEATURE,
        title="Feature Development",
        description="Implement new features",
        file_patterns=["src/", "scripts/", "tests/"],
        success_criteria=[
            "Feature works as specified",
            "All tests pass",
            "Documentation added",
            "No breaking changes",
        ],
        risk_level="high",
        estimated_complexity="complex",
        prompt_template=FEATURE_PROMPT,
    ),
    TaskCategory.REFACTOR: TaskDefinition(
        category=TaskCategory.REFACTOR,
        title="Code Refactoring",
        description="Refactor code for maintainability",
        file_patterns=["src/", "scripts/", "tests/"],
        success_criteria=[
            "Code is more readable",
            "All tests pass",
            "No behavior changes",
            "Improved structure documented",
        ],
        risk_level="medium",
        estimated_complexity="moderate",
        prompt_template=REFACTOR_PROMPT,
    ),
    TaskCategory.TEST: TaskDefinition(
        category=TaskCategory.TEST,
        title="Test Development",
        description="Add or improve tests",
        file_patterns=["tests/"],
        success_criteria=[
            "Tests are comprehensive",
            "All new tests pass",
            "Coverage improved",
            "Tests follow conventions",
        ],
        risk_level="low",
        estimated_complexity="moderate",
        prompt_template=TEST_PROMPT,
    ),
    TaskCategory.SECURITY: TaskDefinition(
        category=TaskCategory.SECURITY,
        title="Security Hardening",
        description="Improve security",
        file_patterns=["src/", "scripts/", "tests/"],
        success_criteria=[
            "Security issue resolved",
            "No new vulnerabilities introduced",
            "Security tests added",
            "Secure patterns documented",
        ],
        risk_level="high",
        estimated_complexity="complex",
        prompt_template=SECURITY_PROMPT,
    ),
    TaskCategory.PERFORMANCE: TaskDefinition(
        category=TaskCategory.PERFORMANCE,
        title="Performance Optimization",
        description="Optimize performance",
        file_patterns=["src/", "scripts/", "tests/"],
        success_criteria=[
            "Measurable performance improvement",
            "No correctness regressions",
            "Tests pass",
            "Performance gains documented",
        ],
        risk_level="medium",
        estimated_complexity="complex",
        prompt_template=PERFORMANCE_PROMPT,
    ),
    TaskCategory.DOCUMENTATION: TaskDefinition(
        category=TaskCategory.DOCUMENTATION,
        title="Documentation",
        description="Write or improve documentation",
        file_patterns=["docs/", "*.md", "*.rst"],
        success_criteria=[
            "Documentation is clear",
            "Examples work correctly",
            "No broken links",
            "Consistent with style guide",
        ],
        risk_level="low",
        estimated_complexity="simple",
        prompt_template=DOCUMENTATION_PROMPT,
    ),
    TaskCategory.CLEANUP: TaskDefinition(
        category=TaskCategory.CLEANUP,
        title="Code Cleanup",
        description="Clean up code and remove technical debt",
        file_patterns=["src/", "scripts/"],
        success_criteria=[
            "Dead code removed",
            "Imports cleaned up",
            "Style consistent",
            "All tests pass",
        ],
        risk_level="low",
        estimated_complexity="simple",
        prompt_template=CLEANUP_PROMPT,
    ),
}


def get_task_definition(category: TaskCategory) -> Optional[TaskDefinition]:
    """Get task definition by category."""
    return TASK_DEFINITIONS.get(category)


def detect_task_category(task_description: str) -> TaskCategory:
    """Detect task category from description using keywords."""
    task_lower = task_description.lower()

    # Check for category keywords (specific before generic)
    if any(word in task_lower for word in ["bug", "fix", "broken", "failing", "error"]):
        return TaskCategory.BUG_FIX
    elif any(word in task_lower for word in ["security", "secure", "vulnerability"]):
        return TaskCategory.SECURITY
    elif any(
        word in task_lower for word in ["performance", "optimize", "fast", "speed"]
    ):
        return TaskCategory.PERFORMANCE
    elif any(
        word in task_lower for word in ["test", "coverage", "unit test", "assertion"]
    ):
        return TaskCategory.TEST
    elif any(word in task_lower for word in ["document", "doc", "readme", "comment"]):
        return TaskCategory.DOCUMENTATION
    elif any(word in task_lower for word in ["cleanup", "dead code", "unused import"]):
        return TaskCategory.CLEANUP
    elif any(word in task_lower for word in ["refactor", "improve", "redesign"]):
        return TaskCategory.REFACTOR
    elif any(word in task_lower for word in ["feature", "implement", "add", "new"]):
        return TaskCategory.FEATURE
    else:
        # Default to bug fix if can't detect
        return TaskCategory.BUG_FIX


def get_specialized_prompt(task_description: str) -> str:
    """Get a specialized prompt based on task description."""
    category = detect_task_category(task_description)
    definition = get_task_definition(category)

    if definition is None:
        # Fallback to generic prompt
        return f"Complete this task: {task_description}"

    return definition.get_specialized_prompt(task_description)


def get_task_guidance(task_description: str) -> Dict[str, Any]:
    """Get comprehensive guidance for a task."""
    category = detect_task_category(task_description)
    definition = get_task_definition(category)

    if definition is None:
        return {"category": "unknown", "guidance": "Unable to determine task type"}

    return {
        "category": category.value,
        "title": definition.title,
        "description": definition.description,
        "file_patterns": definition.file_patterns,
        "success_criteria": definition.success_criteria,
        "risk_level": definition.risk_level,
        "estimated_complexity": definition.estimated_complexity,
        "specialized_prompt": definition.get_specialized_prompt(task_description),
    }


# Example usage
if __name__ == "__main__":
    # Example 1: Auto-detect and get guidance
    task = "Fix the failing test_quantum_autorun test"
    guidance = get_task_guidance(task)
    print(f"Task: {task}")
    print(f"Category: {guidance['category']}")
    print(f"Risk Level: {guidance['risk_level']}")
    print(f"Complexity: {guidance['estimated_complexity']}")
    print(f"\nSuccess Criteria:")
    for criteria in guidance["success_criteria"]:
        print(f"  ✓ {criteria}")

    print("\n" + "=" * 60 + "\n")

    # Example 2: Different task
    task2 = "Add security validation to circuit_id input parameters"
    guidance2 = get_task_guidance(task2)
    print(f"Task: {task2}")
    print(f"Category: {guidance2['category']}")
    print(f"Risk Level: {guidance2['risk_level']}")
