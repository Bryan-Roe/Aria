"""Programmable AI safety middleware for request/response/tool controls.

This module provides policy-based controls that can be embedded in chat, agent,
or workflow paths to enforce practical AI safety rules:

- Input validation and sanitization
- Prompt risk classification
- Output scanning for secrets and dangerous code patterns
- Tool allow/review/deny gating
- Simple approval requirements based on risk
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable


@dataclass(frozen=True)
class SafetyDecision:
    """Decision produced by a safety gate."""

    allowed: bool
    risk_level: str
    reason: str
    flags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ToolPolicy:
    """Policy for a tool name."""

    mode: str  # allow | review_required | deny
    allowed_args: tuple[str, ...] = field(default_factory=tuple)


DEFAULT_TOOL_POLICY: dict[str, ToolPolicy] = {
    "read_file": ToolPolicy(mode="allow"),
    "grep_search": ToolPolicy(mode="allow"),
    "list_dir": ToolPolicy(mode="allow"),
    "run_in_terminal": ToolPolicy(mode="review_required"),
    "apply_patch": ToolPolicy(mode="review_required"),
    "delete_file": ToolPolicy(mode="deny"),
}

VALID_TOOL_POLICY_MODES = {"allow", "review_required", "deny"}


class AISafetyMiddleware:
    """Policy-based AI safety middleware.

    Notes:
    - Keep this module dependency-light and synchronous so it can be reused
      from functions, scripts, and tests.
    - It intentionally returns structured decisions instead of raising directly.
    """

    def __init__(
        self,
        *,
        max_prompt_chars: int = 10_000,
        banned_phrases: Iterable[str] | None = None,
        tool_policy: dict[str, ToolPolicy] | None = None,
    ) -> None:
        self.max_prompt_chars = max_prompt_chars
        self.banned_phrases = tuple(
            p.lower()
            for p in (
                banned_phrases
                if banned_phrases is not None
                else (
                    "ignore previous instructions",
                    "reveal system prompt",
                    "exfiltrate secrets",
                    "bypass safety",
                    "rm -rf",
                )
            )
        )
        self.tool_policy = dict(DEFAULT_TOOL_POLICY)
        if tool_policy:
            self.tool_policy.update(tool_policy)

        invalid_modes = {
            tool_name: policy.mode
            for tool_name, policy in self.tool_policy.items()
            if policy.mode not in VALID_TOOL_POLICY_MODES
        }
        self._invalid_policy_modes = invalid_modes

        self._secret_patterns: tuple[re.Pattern[str], ...] = (
            re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key pattern
            re.compile(r"-----BEGIN (?:RSA |EC |)PRIVATE KEY-----"),
            re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}"),
        )
        self._dangerous_code_markers = (
            "os.system(",
            "subprocess.popen(",
            "subprocess.run(",
            "eval(",
            "exec(",
        )

    def validate_input(self, prompt: str) -> SafetyDecision:
        """Validate and sanitize user input text."""
        if not isinstance(prompt, str):
            return SafetyDecision(
                allowed=False,
                risk_level="high",
                reason="input must be a string",
                flags=("invalid_type",),
            )

        text = prompt.strip()
        if not text:
            return SafetyDecision(
                allowed=False,
                risk_level="low",
                reason="empty prompt",
                flags=("empty_prompt",),
            )

        if len(text) > self.max_prompt_chars:
            return SafetyDecision(
                allowed=False,
                risk_level="medium",
                reason="prompt exceeds max length",
                flags=("max_length_exceeded",),
            )

        lowered = text.lower()
        matched = tuple(p for p in self.banned_phrases if p in lowered)
        if matched:
            return SafetyDecision(
                allowed=False,
                risk_level="high",
                reason="prompt contains banned instruction patterns",
                flags=("banned_phrase",) + matched,
            )

        return SafetyDecision(
            allowed=True,
            risk_level=self.classify_prompt_risk(text),
            reason="input accepted",
        )

    def classify_prompt_risk(self, prompt: str) -> str:
        """Classify prompt as low/medium/high risk based on intent markers."""
        lowered = prompt.lower()
        high_markers = (
            "credential",
            "token",
            "secret",
            "exploit",
            "ransomware",
            "jailbreak",
        )
        medium_markers = (
            "deploy",
            "production",
            "delete",
            "migration",
            "sudo",
        )

        if any(marker in lowered for marker in high_markers):
            return "high"
        if any(marker in lowered for marker in medium_markers):
            return "medium"
        return "low"

    def validate_output(self, output_text: str) -> SafetyDecision:
        """Scan model output for obvious secrets and dangerous snippets."""
        if not isinstance(output_text, str):
            return SafetyDecision(
                allowed=False,
                risk_level="high",
                reason="output must be a string",
                flags=("invalid_output_type",),
            )

        flags: list[str] = []
        for pattern in self._secret_patterns:
            if pattern.search(output_text):
                flags.append("secret_pattern_detected")
                break

        lowered = output_text.lower()
        for marker in self._dangerous_code_markers:
            if marker in lowered:
                flags.append("dangerous_code_marker")
                break

        if flags:
            return SafetyDecision(
                allowed=False,
                risk_level="high",
                reason="output failed safety scan",
                flags=tuple(flags),
            )

        return SafetyDecision(
            allowed=True,
            risk_level="low",
            reason="output accepted",
        )

    def check_tool_call(
        self, tool_name: str, args: dict[str, Any] | None
    ) -> SafetyDecision:
        """Evaluate a proposed tool invocation against policy."""
        if args is None:
            args_map: dict[str, Any] = {}
        elif not isinstance(args, dict):
            return SafetyDecision(
                allowed=False,
                risk_level="high",
                reason="tool args must be an object/dict",
                flags=("invalid_tool_args_type", type(args).__name__),
            )
        else:
            args_map = args

        if self._invalid_policy_modes:
            offending = sorted(self._invalid_policy_modes.keys())[0]
            mode = self._invalid_policy_modes[offending]
            return SafetyDecision(
                allowed=False,
                risk_level="high",
                reason="invalid tool policy mode configured",
                flags=("invalid_tool_policy_mode", offending, str(mode)),
            )

        policy = self.tool_policy.get(tool_name, ToolPolicy(mode="review_required"))

        if policy.mode == "deny":
            return SafetyDecision(
                allowed=False,
                risk_level="high",
                reason=f"tool '{tool_name}' is denied by policy",
                flags=("tool_denied",),
            )

        if policy.allowed_args:
            unknown = sorted(set(args_map).difference(policy.allowed_args))
            if unknown:
                return SafetyDecision(
                    allowed=False,
                    risk_level="medium",
                    reason="tool arguments violate allowlist",
                    flags=("tool_arg_violation",) + tuple(unknown),
                )

        if policy.mode == "review_required":
            return SafetyDecision(
                allowed=False,
                risk_level="medium",
                reason=f"tool '{tool_name}' requires human approval",
                flags=("review_required",),
            )

        return SafetyDecision(
            allowed=True,
            risk_level="low",
            reason=f"tool '{tool_name}' allowed",
        )

    @staticmethod
    def requires_human_approval(decision: SafetyDecision) -> bool:
        """Whether a decision should be routed to human approval."""
        return (not decision.allowed) and decision.risk_level in {"medium", "high"}

    @staticmethod
    def audit_record(
        *,
        event_type: str,
        actor: str,
        decision: SafetyDecision,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a structured audit event for logging/telemetry pipelines."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor": actor,
            "allowed": decision.allowed,
            "risk_level": decision.risk_level,
            "reason": decision.reason,
            "flags": list(decision.flags),
            "metadata": metadata or {},
        }
