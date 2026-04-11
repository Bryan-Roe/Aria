"""
Tool Maker - Generates tools using LLMs
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Add parent directory to path to import shared modules
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from shared.chat_providers import BaseChatProvider, detect_provider

# Use try/except for imports to handle both package and direct execution
try:
    from .tool_registry import Tool
    from .tool_validator import ToolValidator
except ImportError:
    from tool_registry import Tool
    from tool_validator import ToolValidator

logger = logging.getLogger(__name__)


class ToolMaker:
    """Generates Python tools using LLMs"""

    SYSTEM_PROMPT = """You are a Python code generator that creates safe, efficient functions.

Rules:
1. Generate ONLY Python function code, no explanations
2. Function must be self-contained with no external dependencies except: math, json, re, datetime, collections, itertools, functools, typing
3. Include type hints for parameters and return value
4. Add a docstring explaining the function
5. Handle errors gracefully with try-except
6. Do NOT use: os, sys, subprocess, file operations, network operations, eval, exec
7. Keep the code simple and readable
8. Test edge cases in your implementation

Return ONLY the Python function code, starting with 'def'."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize tool maker

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.provider = self._initialize_provider()
        self.validator = ToolValidator(config_path)
        self.temperature = self.config.get("tool_maker", {}).get("temperature", 0.7)
        self.max_tokens = self.config.get("tool_maker", {}).get("max_tokens", 2000)

    def _load_config(self, config_path: Optional[Path]) -> dict:
        """Load configuration from YAML file"""
        if config_path and config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)

        # Try default config path
        default_config_path = Path(__file__).parent.parent / "llm_maker_config.yaml"
        if default_config_path.exists():
            with open(default_config_path, "r") as f:
                return yaml.safe_load(f)

        return {}

    def _initialize_provider(self) -> BaseChatProvider:
        """Initialize AI provider for code generation"""
        provider_name = self.config.get("tool_maker", {}).get("provider", "azure")
        provider = detect_provider(provider_name)

        if not provider:
            logger.warning("No AI provider available, using local fallback")
            provider = detect_provider("local")

        logger.info(f"Initialized tool maker with provider: {type(provider).__name__}")
        return provider

    def create_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, str],
        return_type: str = "Any",
        examples: Optional[List[Dict]] = None,
        max_attempts: int = 3,
    ) -> Optional[Tool]:
        """
        Create a tool from description using LLM

        Args:
            name: Function name
            description: What the function should do
            parameters: Dict of parameter_name: type
            return_type: Expected return type
            examples: Optional list of example inputs/outputs
            max_attempts: Maximum attempts to generate valid code

        Returns:
            Tool object or None if generation failed
        """
        logger.info(f"Creating tool '{name}': {description}")

        # Build the prompt
        prompt = self._build_prompt(
            name, description, parameters, return_type, examples
        )

        # Try to generate valid code
        for attempt in range(max_attempts):
            logger.debug(f"Generation attempt {attempt + 1}/{max_attempts}")

            # Generate code using LLM
            code = self._generate_code(prompt)

            if not code:
                logger.error("Failed to generate code")
                continue

            # Validate the generated code
            is_valid, errors = self.validator.validate(code)

            if is_valid:
                # Check function signature
                param_names = list(parameters.keys())
                sig_valid, sig_errors = self.validator.check_function_signature(
                    code, name, param_names
                )

                if sig_valid:
                    logger.info(f"Successfully created tool '{name}'")
                    return Tool(
                        id="",  # Will be set by registry
                        name=name,
                        description=description,
                        code=code,
                        parameters=parameters,
                        return_type=return_type,
                        created_at="",  # Will be set by registry
                        validated=True,
                        examples=examples or [],
                    )
                else:
                    logger.warning(
                        f"Function signature validation failed: {sig_errors}"
                    )
                    # Add feedback to prompt for next attempt
                    prompt += "\n\nPrevious attempt had these issues:\n" + "\n".join(
                        sig_errors
                    )
            else:
                logger.warning(f"Code validation failed: {errors}")
                # Add feedback to prompt for next attempt
                prompt += "\n\nPrevious attempt had these safety issues:\n" + "\n".join(
                    errors
                )

        logger.error(f"Failed to create tool '{name}' after {max_attempts} attempts")
        return None

    def _build_prompt(
        self,
        name: str,
        description: str,
        parameters: Dict[str, str],
        return_type: str,
        examples: Optional[List[Dict]],
    ) -> str:
        """Build prompt for LLM code generation"""
        param_list = [f"{pname}: {ptype}" for pname, ptype in parameters.items()]
        param_str = ", ".join(param_list)

        prompt = f"""Create a Python function with this specification:

Function name: {name}
Parameters: {param_str}
Return type: {return_type}
Description: {description}

"""

        if examples:
            prompt += "Examples:\n"
            for i, example in enumerate(examples, 1):
                prompt += f"\nExample {i}:\n"
                if "input" in example:
                    prompt += f"  Input: {example['input']}\n"
                if "output" in example:
                    prompt += f"  Expected Output: {example['output']}\n"

        prompt += "\nGenerate the complete function implementation."

        return prompt

    def _generate_code(self, prompt: str) -> Optional[str]:
        """Generate code using LLM"""
        try:
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]

            # Get response from provider
            response_text = ""

            if hasattr(self.provider, "complete"):
                # Use streaming if available
                for chunk in self.provider.complete(messages, stream=True):
                    if isinstance(chunk, dict) and "content" in chunk:
                        response_text += chunk["content"]
                    elif isinstance(chunk, str):
                        response_text += chunk
            else:
                # Fallback to non-streaming
                response = self.provider.complete(messages, stream=False)
                if isinstance(response, dict) and "content" in response:
                    response_text = response["content"]
                elif isinstance(response, str):
                    response_text = response

            # Extract code from response (remove markdown code blocks if present)
            code = self._extract_code(response_text)

            return code

        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return None

    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM response"""
        # Remove markdown code blocks
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                code = parts[1].split("```")[0]
                return code.strip()

        if "```" in response:
            parts = response.split("```")
            if len(parts) > 1:
                return parts[1].strip()

        # If no code blocks, assume entire response is code
        return response.strip()

    def validate_tool(self, tool: Tool) -> bool:
        """
        Validate a tool

        Args:
            tool: Tool to validate

        Returns:
            True if valid
        """
        is_valid, errors = self.validator.validate(tool.code)

        if not is_valid:
            logger.error(f"Tool validation failed: {errors}")

        return is_valid

    def refine_tool(
        self, tool: Tool, feedback: str, max_attempts: int = 2
    ) -> Optional[Tool]:
        """
        Refine an existing tool based on feedback

        Args:
            tool: Tool to refine
            feedback: Feedback on what needs improvement
            max_attempts: Maximum refinement attempts

        Returns:
            Refined tool or None
        """
        logger.info(f"Refining tool '{tool.name}' based on feedback")

        prompt = f"""Improve this Python function based on the feedback.

Current implementation:
```python
{tool.code}
```

Feedback: {feedback}

Generate an improved version of the function."""

        for attempt in range(max_attempts):
            code = self._generate_code(prompt)

            if code:
                is_valid, errors = self.validator.validate(code)

                if is_valid:
                    # Create refined tool
                    refined = Tool(
                        id=tool.id,
                        name=tool.name,
                        description=tool.description,
                        code=code,
                        parameters=tool.parameters,
                        return_type=tool.return_type,
                        created_at=tool.created_at,
                        validated=True,
                        examples=tool.examples,
                        tags=tool.tags,
                    )
                    logger.info(f"Successfully refined tool '{tool.name}'")
                    return refined
                else:
                    prompt += "\n\nValidation errors:\n" + "\n".join(errors)

        logger.error(f"Failed to refine tool '{tool.name}'")
        return None
