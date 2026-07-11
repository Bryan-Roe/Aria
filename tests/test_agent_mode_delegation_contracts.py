"""Contract tests for agent mode delegation and switch-and-return behavior.

These tests validate markdown-level contracts in `.github/agents/*.agent.md`
to prevent silent drift in the primary agent's routing protocol and
specialist return-to-agent requirements.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / ".github" / "agents"
PRIMARY_AGENT_FILE = AGENTS_DIR / "ai.agent.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_agent_name(path: Path) -> str | None:
    """Extract `name:` from frontmatter."""
    text = _read(path)
    if not text.startswith("---\n"):
        return None
    split = text.split("\n---\n", 1)
    if len(split) != 2:
        return None
    frontmatter = split[0]
    for line in frontmatter.splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def _extract_bullets_between(text: str, start_header: str, end_header: str) -> list[str]:
    """Extract bullet lines in a markdown section bounded by headers."""
    try:
        start = text.index(start_header)
    except ValueError:
        return []
    try:
        end = text.index(end_header, start)
    except ValueError:
        end = len(text)

    block = text[start:end]
    return [ln.strip() for ln in block.splitlines() if ln.strip().startswith("-")]


def _extract_backtick_targets(lines: list[str]) -> list[str]:
    targets: list[str] = []
    for line in lines:
        matches = re.findall(r"`([^`]+)`", line)
        if matches:
            # routing and alias lines consistently use rightmost backtick token as target
            targets.append(matches[-1])
    return targets


@pytest.mark.unit
def test_primary_agent_declares_automatic_mode_switching_section() -> None:
    text = _read(PRIMARY_AGENT_FILE)
    assert "## Automatic Mode Switching" in text
    assert "temporary modes" in text
    assert "resume `agent` mode" in text


@pytest.mark.unit
def test_primary_agent_routing_rules_cover_canonical_specialists() -> None:
    text = _read(PRIMARY_AGENT_FILE)
    assert "### Routing Rules" in text

    expected_targets = [
        "`agi-reasoning`",
        "`aria-character`",
        "`autonomous-trainer`",
        "`full-stack-debugger`",
        "`ai-architect`",
        "`chat-provider`",
        "`platform-ops`",
        "`vision-ai`",
        "`data-pipeline`",
        "`llm-maker`",
        "`qai-specialist`",
    ]
    for target in expected_targets:
        assert target in text


@pytest.mark.unit
def test_routing_rule_targets_resolve_to_existing_agent_names() -> None:
    text = _read(PRIMARY_AGENT_FILE)
    bullets = _extract_bullets_between(
        text,
        "### Routing Rules",
        "### Mode Name Resolution (Aliases)",
    )
    targets = _extract_backtick_targets(bullets)
    assert targets, "Expected routing rule bullets with explicit targets"

    available = {n for n in (_extract_agent_name(p) for p in AGENTS_DIR.glob("*.agent.md")) if n}
    missing = sorted({t for t in targets if t not in available})
    assert not missing, f"Routing targets not found in agent names: {missing}"


@pytest.mark.unit
def test_primary_agent_declares_alias_mapping_lines() -> None:
    text = _read(PRIMARY_AGENT_FILE)
    assert "### Mode Name Resolution (Aliases)" in text
    assert "`Full_stack_debugging` → `full-stack-debugger`" in text
    assert "`AI_model_training` → `autonomous-trainer`" in text
    assert "`Aria_character_development` → `aria-character`" in text
    assert "`AI_chat_development` → `chat-provider`" in text
    assert "`Quantum_ML_development` → `qai-specialist`" in text


@pytest.mark.unit
def test_alias_targets_resolve_to_existing_agent_names() -> None:
    available = {n for n in (_extract_agent_name(p) for p in AGENTS_DIR.glob("*.agent.md")) if n}

    # Canonical alias targets
    for target in {
        "full-stack-debugger",
        "autonomous-trainer",
        "aria-character",
        "chat-provider",
        "qai-specialist",
    }:
        assert target in available

    # Explicitly allowed alternate-mode direct name in primary instructions
    assert "AI_model_training" in available


@pytest.mark.unit
def test_alias_sources_exist_as_alternate_mode_agent_names() -> None:
    text = _read(PRIMARY_AGENT_FILE)
    bullets = _extract_bullets_between(
        text,
        "### Mode Name Resolution (Aliases)",
        "### Switch-and-Return Protocol",
    )
    sources = []
    for line in bullets:
        matches = re.findall(r"`([^`]+)`", line)
        if len(matches) >= 2:
            sources.append(matches[0])

    assert sources, "Expected alias source entries in alias section"
    available = {n for n in (_extract_agent_name(p) for p in AGENTS_DIR.glob("*.agent.md")) if n}
    missing_sources = sorted({s for s in sources if s not in available})
    assert not missing_sources, (
        f"Alias source names should map to existing alternate-mode agent names: {missing_sources}"
    )


@pytest.mark.unit
def test_primary_agent_switch_and_return_protocol_handoff_fields() -> None:
    text = _read(PRIMARY_AGENT_FILE)
    assert "### Switch-and-Return Protocol" in text

    required_fields = [
        "what it did",
        "what it found",
        "files/systems touched",
        "blockers or risks",
        "recommended next step",
    ]
    for field in required_fields:
        assert field in text

    assert "Immediately resume as the primary `agent`." in text


@pytest.mark.unit
def test_primary_task_execution_pattern_orders_delegate_before_return() -> None:
    text = _read(PRIMARY_AGENT_FILE)
    marker_delegate = "3. **Delegate**"
    marker_return = "4. **Return**"
    assert marker_delegate in text
    assert marker_return in text
    assert text.index(marker_delegate) < text.index(marker_return)


@pytest.mark.unit
def test_all_specialists_define_return_to_agent_contract() -> None:
    specialist_files = [p for p in AGENTS_DIR.glob("*.agent.md") if p.name != "ai.agent.md"]
    assert specialist_files, "Expected specialist agent files to exist"

    missing = []
    for path in specialist_files:
        text = _read(path)
        if "## Return-to-Agent Contract" not in text:
            missing.append(path.name)

    assert not missing, f"Missing Return-to-Agent Contract section: {missing}"


@pytest.mark.unit
def test_specialist_contracts_mark_temporary_and_return_to_primary() -> None:
    specialist_files = [p for p in AGENTS_DIR.glob("*.agent.md") if p.name != "ai.agent.md"]

    bad = []
    for path in specialist_files:
        text = _read(path)
        has_temporary = "temporary" in text.lower()
        has_handoff = "hand back to `agent`" in text.lower() or "primary `agent`" in text
        if not (has_temporary and has_handoff):
            bad.append(path.name)

    assert not bad, f"Specialist return contract wording incomplete: {bad}"


@pytest.mark.unit
def test_legacy_chatmode_directory_is_not_present() -> None:
    """Chat modes were migrated to .github/agents; keep legacy dir removed."""
    legacy_dir = REPO_ROOT / ".github" / "chatmodes"
    assert not legacy_dir.exists(), "Legacy .github/chatmodes directory should remain removed after migration."


@pytest.mark.unit
def test_no_legacy_chatmode_markdown_files_exist() -> None:
    """Prevent reintroduction of *.chatmode.md files after migration."""
    legacy_files = list((REPO_ROOT / ".github").glob("**/*.chatmode.md"))
    assert not legacy_files, f"Unexpected legacy chatmode files found: {legacy_files}"
