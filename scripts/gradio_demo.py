"""Enhanced Gradio demo for QAI.

Run after installing dependencies:
    ./.venv/bin/python scripts/gradio_demo.py

Then open the local URL printed by Gradio.
"""

import html
import importlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import gradio as gr

# Request-scoped cancellation tokens are stored in a Gradio State (request_tokens) instead of a module-global flag.
# See respond() and cancel_stream() implementations for details.

APP_NAME = "QAI"
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
REPO_AUTOMATION_STATUS_PATH = str(REPO_ROOT / "data_out" / "repo_automation" / "status.json")
REPO_AUTOMATION_LEGACY_STATUS_PATH = str(REPO_ROOT / "automation_status.json")


def default_provider_choice() -> str:
    """Prefer the QAI quantum backend when it is configured, otherwise stay on auto."""
    if os.getenv("QAI_QUANTUM_MODEL_PATH") or os.getenv("QAI_QUANTUM_MODEL"):
        return "qai"
    return "auto"


def provider_readiness_note() -> str:
    """Summarize the currently available QAI provider path for the sidebar."""
    model_path = os.getenv("QAI_QUANTUM_MODEL_PATH") or os.getenv("QAI_QUANTUM_MODEL")
    if model_path:
        return f"QAI quantum backend ready: {model_path}"
    return "QAI quantum backend not configured. Set QAI_QUANTUM_MODEL_PATH or choose auto."


def provider_diagnostics_summary() -> str:
    """Combine the selected provider mode and readiness into a single diagnostic string."""
    provider_mode = default_provider_choice()
    if provider_mode == "qai":
        return f"Provider: QAI quantum alias active · {provider_readiness_note()}"
    return f"Provider: auto · {provider_readiness_note()}"


def _read_json_dict(path: str) -> dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def load_repo_automation_status() -> dict[str, Any] | None:
    """Read the current repo automation status from canonical or legacy paths."""
    for candidate in (REPO_AUTOMATION_STATUS_PATH, REPO_AUTOMATION_LEGACY_STATUS_PATH):
        status = _read_json_dict(candidate)
        if status:
            return status
    return None


def repo_automation_status_summary() -> str:
    """Summarize repo automation health for the QAI sidebar."""
    status = load_repo_automation_status()
    if not status:
        return (
            "Repo automation: no status available. Use `python scripts/repo_automation.py --start`, "
            "`--status`, `--stop`, or `--validate`."
        )

    components = status.get("components_running", {}) or {}
    component_enabled = status.get("component_enabled", {}) or {}
    enabled_components = {name: value for name, value in components.items() if component_enabled.get(name, True)}
    running = sum(1 for value in enabled_components.values() if value)
    total = len(enabled_components)
    active_components = [name for name, value in components.items() if value]
    disabled_components = [name for name, enabled in component_enabled.items() if not enabled]
    active_text = ", ".join(active_components[:4]) if active_components else "none"
    if len(active_components) > 4:
        active_text += f" (+{len(active_components) - 4} more)"
    disabled_text = ", ".join(disabled_components[:3]) if disabled_components else "none"
    if len(disabled_components) > 3:
        disabled_text += f" (+{len(disabled_components) - 3} more)"
    errors = status.get("errors", []) or []
    uptime_seconds = int(float(status.get("uptime_seconds", 0) or 0))
    uptime_text = str(timedelta(seconds=uptime_seconds))
    refreshed_at = status.get("generated_at") or status.get("last_health_check") or "unknown"
    config_paths = status.get("config_paths", {}) or {}
    config_bits = []
    if config_paths.get("quantum"):
        config_bits.append(f"quantum: {config_paths['quantum']}")
    if config_paths.get("evaluation"):
        config_bits.append(f"evaluation: {config_paths['evaluation']}")
    config_text = " · ".join(config_bits) if config_bits else "no optional configs detected"

    return (
        f"Repo automation: {running}/{total} enabled components running · uptime {uptime_text} · "
        f"errors {len(errors)} · active: {active_text} · disabled: {disabled_text} · "
        f"updated: {refreshed_at} · {config_text}"
    )


def repo_automation_next_step() -> str:
    """Return a short action-oriented hint for the repo automation panel."""
    status = load_repo_automation_status()
    if not status:
        return (
            "**Next step:** run `python scripts/repo_automation.py --validate` before starting, "
            "or `--start` to launch the automation stack."
        )

    errors = status.get("errors", []) or []
    components = status.get("components_running", {}) or {}
    component_enabled = status.get("component_enabled", {}) or {}
    enabled_components = {name: value for name, value in components.items() if component_enabled.get(name, True)}
    running = sum(1 for value in enabled_components.values() if value)
    total = len(enabled_components)
    if errors:
        return (
            "**Next step:** run `python scripts/repo_automation.py --validate` to inspect the issues "
            "before restarting automation."
        )
    if total and running < total:
        return (
            "**Next step:** run `python scripts/repo_automation.py --start` to bring the remaining "
            "components online, then check `--status`."
        )
    return (
        "**Next step:** run `python scripts/repo_automation.py --status` to confirm everything is "
        "healthy, or `--stop` when you are done."
    )


def repo_automation_actions_markdown() -> str:
    """Show the supported repo automation actions in the sidebar."""
    return (
        "**Actions**\n\n"
        "- `python scripts/repo_automation.py --start`\n"
        "- `python scripts/repo_automation.py --status`\n"
        "- `python scripts/repo_automation.py --stop`\n"
        "- `python scripts/repo_automation.py --validate`\n"
    )


def _sanitize_cli_output(text: str, limit: int = 4000) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    text = text.replace("```", "`\u200b``")
    if len(text) > limit:
        text = text[:limit] + "\n... (truncated)"
    return text


def run_repo_automation_command(*args: str) -> str:
    """Run a repo automation command and format the captured output for the UI."""
    command = [sys.executable, str(REPO_ROOT / "scripts" / "repo_automation.py"), *args]
    pretty_command = "python scripts/repo_automation.py " + " ".join(args)
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except Exception as exc:
        return (
            "**Repo automation command failed to start.**\n\n"
            f"Command: `{pretty_command}`\n\n"
            f"Error: `{html.escape(str(exc))}`"
        )

    stdout = _sanitize_cli_output(completed.stdout)
    stderr = _sanitize_cli_output(completed.stderr)
    lines = [
        f"**Repo automation command:** `{pretty_command}`",
        f"Exit code: `{completed.returncode}`",
    ]
    if stdout:
        lines.append(f"**Stdout:**\n\n```text\n{stdout}\n```")
    if stderr:
        lines.append(f"**Stderr:**\n\n```text\n{stderr}\n```")
    if completed.returncode == 0:
        return "\n\n".join(lines)
    return "**Repo automation command failed.**\n\n" + "\n\n".join(lines)


# Simple theme CSS snippets (injected into the page)
LIGHT_CSS = """<style>
:root {
    --bg: #f6f7fb;
    --fg: #101828;
    --muted: #667085;
    --card: rgba(255, 255, 255, 0.84);
    --card-border: rgba(15, 23, 42, 0.08);
    --accent: #7c3aed;
    --accent-strong: #5b21b6;
    --accent-soft: rgba(124, 58, 237, 0.12);
    --shadow: 0 20px 60px rgba(15, 23, 42, 0.10);
}
body, .gradio-container {
    background:
        radial-gradient(circle at top left, rgba(124, 58, 237, 0.16), transparent 34%),
        radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 26%),
        linear-gradient(180deg, #fbfcff 0%, #f4f6fb 55%, #eef1f7 100%);
    color: var(--fg);
}
    .gradio-container,
    .gradio-container * {
        transition: background-color 180ms ease, border-color 180ms ease, color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
    }
    .gradio-container ::selection {
        background: rgba(124, 58, 237, 0.22);
        color: var(--fg);
    }
.gradio-container {
    padding: 20px !important;
    border-radius: 20px;
}
.hero-banner {
    border: 1px solid var(--card-border);
    border-radius: 24px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.74));
    box-shadow: var(--shadow);
    padding: 22px 24px;
    margin-bottom: 16px;
    backdrop-filter: blur(10px);
}
.hero-banner:hover {
    transform: translateY(-1px);
}
.hero-title {
    font-size: 1.6rem;
    font-weight: 750;
    letter-spacing: -0.03em;
    margin: 0 0 8px;
}
.hero-subtitle {
    color: var(--muted);
    margin: 0;
    line-height: 1.5;
}
.surface-card {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    box-shadow: var(--shadow);
    padding: 16px;
    backdrop-filter: blur(12px);
}
.surface-card:hover {
    box-shadow: 0 24px 70px rgba(15, 23, 42, 0.14);
}
.surface-card details,
.surface-card summary {
    border-radius: 14px;
}
.surface-card details {
    border: 1px solid var(--card-border);
    background: rgba(255, 255, 255, 0.32);
    padding: 8px 12px;
    margin-bottom: 10px;
}
.surface-card summary {
    cursor: pointer;
    font-weight: 700;
    color: var(--fg);
    outline: none;
}
.surface-card details[open] {
    background: rgba(255, 255, 255, 0.42);
}
.surface-card .gradio-group,
.surface-card .gradio-row,
.surface-card .gradio-column {
    background: transparent !important;
}
.chat-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.sidebar-panel {
    position: sticky;
    top: 16px;
    align-self: flex-start;
    max-height: calc(100vh - 32px);
    overflow: auto;
}
.chatbot {
    max-height: 560px;
    min-height: 460px;
    overflow: auto;
    border-radius: 18px;
}
.primary-chatbot {
    margin-bottom: 10px;
}
.chatbot [data-testid="chatbot"] {
    scrollbar-width: thin;
}
.pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 10px 0 0;
}
.pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 600;
    color: var(--accent-strong);
    background: var(--accent-soft);
    border: 1px solid rgba(124, 58, 237, 0.18);
}
.section-label {
    margin: 4px 0 8px;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 700;
}
.gradio-container button.primary {
    background: linear-gradient(135deg, var(--accent), var(--accent-strong)) !important;
    border: none !important;
    box-shadow: 0 12px 24px rgba(91, 33, 182, 0.22);
}
.gradio-container button.primary:hover {
    filter: brightness(1.04);
    transform: translateY(-1px);
}
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    border-radius: 14px !important;
}
.gradio-container textarea::placeholder,
.gradio-container input::placeholder {
    color: var(--muted);
    opacity: 0.75;
}
.sidebar-note {
    margin: 4px 0 12px;
    color: var(--muted);
    font-size: 0.94rem;
    line-height: 1.45;
}
@media (max-width: 1024px) {
    .sidebar-panel {
        position: static;
        max-height: none;
        overflow: visible;
    }
}
</style>"""

DARK_CSS = """<style>
:root {
    --bg: #070b14;
    --fg: #e5eefc;
    --muted: #94a3b8;
    --card: rgba(11, 16, 28, 0.82);
    --card-border: rgba(148, 163, 184, 0.14);
    --accent: #a855f7;
    --accent-strong: #d8b4fe;
    --accent-soft: rgba(168, 85, 247, 0.16);
    --shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}
body, .gradio-container {
    background:
        radial-gradient(circle at top left, rgba(168, 85, 247, 0.18), transparent 32%),
        radial-gradient(circle at top right, rgba(14, 165, 233, 0.14), transparent 26%),
        linear-gradient(180deg, #0b1020 0%, #080d18 58%, #050811 100%);
    color: var(--fg);
}
    .gradio-container,
    .gradio-container * {
        transition: background-color 180ms ease, border-color 180ms ease, color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
    }
    .gradio-container ::selection {
        background: rgba(168, 85, 247, 0.28);
        color: #f8fafc;
    }
.gradio-container {
    padding: 20px !important;
    border-radius: 20px;
}
.hero-banner {
    border: 1px solid var(--card-border);
    border-radius: 24px;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(17, 24, 39, 0.78));
    box-shadow: var(--shadow);
    padding: 22px 24px;
    margin-bottom: 16px;
    backdrop-filter: blur(12px);
}
.hero-banner:hover {
    transform: translateY(-1px);
}
.hero-title {
    font-size: 1.6rem;
    font-weight: 750;
    letter-spacing: -0.03em;
    margin: 0 0 8px;
}
.hero-subtitle {
    color: var(--muted);
    margin: 0;
    line-height: 1.5;
}
.surface-card {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    box-shadow: var(--shadow);
    padding: 16px;
    backdrop-filter: blur(12px);
}
.surface-card:hover {
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.45);
}
.surface-card details,
.surface-card summary {
    border-radius: 14px;
}
.surface-card details {
    border: 1px solid var(--card-border);
    background: rgba(8, 13, 24, 0.36);
    padding: 8px 12px;
    margin-bottom: 10px;
}
.surface-card summary {
    cursor: pointer;
    font-weight: 700;
    color: var(--fg);
    outline: none;
}
.surface-card details[open] {
    background: rgba(8, 13, 24, 0.5);
}
.surface-card .gradio-group,
.surface-card .gradio-row,
.surface-card .gradio-column {
    background: transparent !important;
}
.chat-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.sidebar-panel {
    position: sticky;
    top: 16px;
    align-self: flex-start;
    max-height: calc(100vh - 32px);
    overflow: auto;
}
.chatbot {
    max-height: 560px;
    min-height: 460px;
    overflow: auto;
    border-radius: 18px;
}
.primary-chatbot {
    margin-bottom: 10px;
}
.chatbot [data-testid="chatbot"] {
    scrollbar-width: thin;
}
.pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 10px 0 0;
}
.pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 600;
    color: var(--accent-strong);
    background: var(--accent-soft);
    border: 1px solid rgba(168, 85, 247, 0.18);
}
.section-label {
    margin: 4px 0 8px;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 700;
}
.gradio-container button.primary {
    background: linear-gradient(135deg, var(--accent), #6d28d9) !important;
    border: none !important;
    box-shadow: 0 12px 24px rgba(88, 28, 135, 0.35);
}
.gradio-container button.primary:hover {
    filter: brightness(1.04);
    transform: translateY(-1px);
}
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    border-radius: 14px !important;
}
.gradio-container textarea::placeholder,
.gradio-container input::placeholder {
    color: var(--muted);
    opacity: 0.82;
}
.sidebar-note {
    margin: 4px 0 12px;
    color: var(--muted);
    font-size: 0.94rem;
    line-height: 1.45;
}
@media (max-width: 1024px) {
    .sidebar-panel {
        position: static;
        max-height: none;
        overflow: visible;
    }
}
.chat-panel { display: flex; flex-direction: column; gap: 12px; }
.sidebar-panel { position: static; max-height: none; overflow: visible; }
</style>"""

COMPACT_CSS = """<style>
.gradio-container { padding: 10px !important; }
.hero-banner { padding: 16px 18px; margin-bottom: 12px; }
.hero-title { font-size: 1.28rem; }
.hero-subtitle { font-size: 0.92rem; }
.surface-card { padding: 12px; border-radius: 18px; }
.chatbot { max-height: 420px; min-height: 360px; }
.gradio-chat { font-size: 12px; line-height: 1.1; }
.sidebar-note { margin: 4px 0 12px; color: var(--muted); font-size: 0.92rem; line-height: 1.4; }
</style>"""


def timestamp_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Conversation persistence helpers
# ---------------------------------------------------------------------------

CONV_DIR = "data_out/gradio_conversations"
LATEST_PATH = os.path.join(CONV_DIR, "latest.json")


def ensure_conv_dir() -> None:
    os.makedirs(CONV_DIR, exist_ok=True)


@contextmanager
def _conv_lock():
    """Simple POSIX advisory lock for conversation directory operations."""
    # Ensure directory exists before creating lockfile
    ensure_conv_dir()
    lock_path = os.path.join(CONV_DIR, ".lock")
    lf = open(lock_path, "w")
    fcntl_module: Any = None
    try:
        try:
            fcntl_module = importlib.import_module("fcntl")
        except Exception:
            fcntl_module = cast(Any, None)
        if fcntl_module:
            fcntl_module.flock(lf, fcntl_module.LOCK_EX)
        yield
    finally:
        try:
            if fcntl_module:
                fcntl_module.flock(lf, fcntl_module.LOCK_UN)
        except Exception:
            pass
        try:
            lf.close()
        except Exception:
            pass


def save_conversation_json(hist_state: list[dict], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = "session"
    conv_root = os.path.realpath(CONV_DIR)
    filename = os.path.realpath(os.path.join(conv_root, f"{safe_name}_{ts}.json"))
    if os.path.commonpath([conv_root, filename]) != conv_root:
        raise ValueError("Invalid session name")
    temp_filename = os.path.realpath(os.path.join(conv_root, f"{safe_name}_{ts}.json.tmp"))
    if os.path.commonpath([conv_root, temp_filename]) != conv_root:
        raise ValueError("Invalid session name")
    latest_temp = LATEST_PATH + ".tmp"
    try:
        with _conv_lock():
            with open(temp_filename, "w", encoding="utf-8") as f:
                json.dump(hist_state, f, ensure_ascii=False, indent=2)
            # atomic replace
            os.replace(temp_filename, filename)
            # update latest atomically
            with open(latest_temp, "w", encoding="utf-8") as f:
                json.dump(hist_state, f, ensure_ascii=False, indent=2)
            os.replace(latest_temp, LATEST_PATH)
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception:
                pass
        if os.path.exists(latest_temp):
            try:
                os.remove(latest_temp)
            except Exception:
                pass
    return filename


def save_conversation_markdown(hist_state: list[dict], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", (session_name or "session").strip()).strip("._-") or "session"
    conv_root = os.path.realpath(CONV_DIR)
    filename = os.path.realpath(os.path.join(conv_root, f"{safe_name}_{ts}.md"))
    if os.path.commonpath([conv_root, filename]) != conv_root:
        raise ValueError("Invalid session name")
    temp_filename = os.path.realpath(os.path.join(conv_root, f".tmp_{uuid.uuid4().hex}.md"))
    if os.path.commonpath([conv_root, temp_filename]) != conv_root:
        raise ValueError("Invalid session name")
    try:
        with _conv_lock():
            with open(temp_filename, "w", encoding="utf-8") as f:
                for entry in hist_state:
                    u = entry.get("user", "")
                    a = entry.get("assistant", "")
                    ut = entry.get("user_ts", "")
                    at = entry.get("assistant_ts", "")
                    f.write(f"### User — {ut}\n")
                    f.write(u + "\n\n")
                    f.write(f"### Assistant — {at}\n")
                    f.write(a + "\n\n---\n\n")
            os.replace(temp_filename, filename)
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception:
                pass
    return filename


def load_latest_conversation() -> tuple[list[tuple[str, str]], list[dict]]:
    if not os.path.exists(LATEST_PATH):
        return [], []
    try:
        with _conv_lock():
            with open(LATEST_PATH, encoding="utf-8") as f:
                hist = json.load(f)
    except Exception:
        return [], []
    display = []
    for e in hist:
        u = e.get("user", "")
        a = e.get("assistant", "")
        ut = e.get("user_ts", "")
        at = e.get("assistant_ts", "")
        display.append((f"{u}\n\n[{ut}]", f"{a}\n\n[{at}]"))
    return display, hist


def hist_state_to_display(hist_state: list[dict]) -> list[tuple[str, str]]:
    if not hist_state:
        return []
    return [
        (
            f"{e.get('user', '')}\n\n[{e.get('user_ts', '')}]",
            f"{e.get('assistant', '')}\n\n[{e.get('assistant_ts', '')}]",
        )
        for e in hist_state
    ]


def hist_state_to_messages(hist_state: list[dict]) -> Any:
    """Convert structured history into Gradio Chatbot messages format."""
    if not hist_state:
        return []
    messages = []
    for e in hist_state:
        u = e.get("user", "")
        a = e.get("assistant", "")
        ut = e.get("user_ts", "")
        at = e.get("assistant_ts", "")
        if u:
            messages.append({"role": "user", "content": f"{u}\n\n[{ut}]"})
        if a:
            messages.append({"role": "assistant", "content": f"{a}\n\n[{at}]"})
    return cast(Any, messages)


# ---------------------------------------------------------------------------
# Helper utilities (export, summarization, auto-improve daemon)
# ---------------------------------------------------------------------------


# Export conversation to HTML for sharing/viewing
def generate_html_export(hist_state: list[dict], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", (session_name or "session").strip()).strip("._-") or "session"
    conv_root = os.path.realpath(CONV_DIR)
    filename = os.path.realpath(os.path.join(conv_root, f"{safe_name}_{ts}.html"))
    if os.path.commonpath([conv_root, filename]) != conv_root:
        raise ValueError("Invalid session name")
    temp_filename = os.path.realpath(os.path.join(conv_root, f"{safe_name}_{ts}.html.tmp"))
    if os.path.commonpath([conv_root, temp_filename]) != conv_root:
        raise ValueError("Invalid session name")
    parts = [
        "<!doctype html>",
        "<html><head><meta charset='utf-8'><title>Conversation</title>",
        "<style>body{font-family:Arial,sans-serif;padding:20px;} .user{background:#eef;padding:8px;margin:6px;border-radius:6px;} .assistant{background:#efe;padding:8px;margin:6px;border-radius:6px;}</style>",
        "</head><body>",
        f"<h1>Conversation — {html.escape(safe_name)}</h1>",
        "<div>",
    ]
    for e in hist_state:
        ut = e.get("user_ts", "")
        at = e.get("assistant_ts", "")
        user = html.escape(e.get("user", ""))
        assistant = html.escape(e.get("assistant", ""))
        parts.append(f"<div class='user'><strong>User [{ut}]</strong><div>{user}</div></div>")
        parts.append(f"<div class='assistant'><strong>Assistant [{at}]</strong><div>{assistant}</div></div>")
    parts.append("</div></body></html>")
    try:
        with _conv_lock():
            with open(temp_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(parts))
            os.replace(temp_filename, filename)
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception:
                pass
    return filename


# Simple summarizer to propose follow-ups or improvements
def summarize_conversation_simple(hist_state: list[dict], top_n: int = 5) -> str:
    if not hist_state:
        return "No conversation yet."
    texts = " ".join((e.get("user", "") or "") + " " + (e.get("assistant", "") or "") for e in hist_state)
    tokens = re.findall(r"\w+", texts.lower())
    stopwords = set(
        [
            "the",
            "and",
            "to",
            "a",
            "is",
            "in",
            "it",
            "of",
            "for",
            "on",
            "that",
            "this",
            "with",
            "as",
            "are",
            "was",
            "i",
            "you",
            "we",
            "they",
            "he",
            "she",
            "be",
        ]
    )  # simple stoplist
    words = [t for t in tokens if t not in stopwords and len(t) > 2]
    common = Counter(words).most_common(top_n)
    top = [w for w, _ in common]
    user_msgs = sum(1 for e in hist_state if e.get("user"))
    assistant_msgs = sum(1 for e in hist_state if e.get("assistant"))
    last_msgs = hist_state[-5:]
    last_lines = []
    for e in last_msgs:
        if e.get("user"):
            user_text = str(e.get("user") or "")
            last_lines.append(f"U: {user_text[:120]}")
        if e.get("assistant"):
            assistant_text = str(e.get("assistant") or "")
            last_lines.append(f"A: {assistant_text[:120]}")
    suggestion = f"Summary: {user_msgs} user messages, {assistant_msgs} assistant messages. Top topics: {', '.join(top)}. Recent: {' | '.join(last_lines)}. Suggested follow-ups: Ask for clarification on {top[0] if top else 'the topic'}."
    return suggestion


SUGGESTIONS_PATH = os.path.join(CONV_DIR, "suggestions.json")
AUTO_IMPROVE_CONFIG_PATH = os.path.join(CONV_DIR, "auto_improve_config.json")


def save_suggestions(suggestions):
    ensure_conv_dir()
    temp = SUGGESTIONS_PATH + ".tmp"
    try:
        with _conv_lock():
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(suggestions, f, ensure_ascii=False, indent=2)
            os.replace(temp, SUGGESTIONS_PATH)
    finally:
        if os.path.exists(temp):
            try:
                os.remove(temp)
            except Exception:
                pass


def load_suggestions():
    if not os.path.exists(SUGGESTIONS_PATH):
        return []
    try:
        with _conv_lock():
            with open(SUGGESTIONS_PATH, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return []


def auto_improve_daemon():
    last_mtime = 0.0
    while True:
        enabled = False
        interval = 60
        try:
            if os.path.exists(AUTO_IMPROVE_CONFIG_PATH):
                with open(AUTO_IMPROVE_CONFIG_PATH, encoding="utf-8") as f:
                    cfg = json.load(f)
                enabled = bool(cfg.get("enabled", False))
                interval = int(cfg.get("interval", interval))
        except Exception:
            enabled = False
        if enabled and os.path.exists(LATEST_PATH):
            try:
                mtime = os.path.getmtime(LATEST_PATH)
                if mtime > last_mtime:
                    _, hist = load_latest_conversation()
                    suggestion = summarize_conversation_simple(hist)
                    existing = load_suggestions()
                    ts = timestamp_now()
                    existing.append({"ts": ts, "suggestion": suggestion})
                    save_suggestions(existing)
                    last_mtime = mtime
            except Exception:
                pass
        time.sleep(interval if enabled else 5)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

with gr.Blocks() as demo:
    # Theme injection element + toggle
    theme_css = gr.HTML(value=LIGHT_CSS)
    hero_banner = gr.HTML(value=f"""
        <div class="hero-banner">
            <div class="hero-title">QAI Gradio Demo</div>
            <p class="hero-subtitle">A polished chat workspace for QAI session management, exports, and lightweight automation experiments.</p>
            <div class="pill-row">
                <span class="pill">{html.escape(provider_diagnostics_summary())}</span>
            </div>
            <div class="pill-row">
                <span class="pill">Streaming chat</span>
                <span class="pill">Session tools</span>
                <span class="pill">Export flows</span>
                <span class="pill">Auto-improve</span>
            </div>
        </div>
        """)
    with gr.Row(elem_classes=["surface-card"]):
        with gr.Column(scale=4):
            gr.Markdown(
                f"# {APP_NAME} — Gradio Demo  \nEnhanced chat demo with persistence, export, search, sessions, streaming, and TTS."
            )
        with gr.Column(scale=1, min_width=220):
            theme_toggle = gr.Checkbox(label="Dark mode", value=False)
            compact_toggle = gr.Checkbox(label="Compact layout", value=False)

    # Chat area
    initial_display, initial_hist_state = load_latest_conversation()
    initial_messages = hist_state_to_messages(initial_hist_state)

    with gr.Row():
        with gr.Column(scale=3, elem_classes=["surface-card", "chat-panel"]):
            gr.Markdown("### Conversation")
            chatbot = gr.Chatbot(
                value=initial_messages, label="Conversation", elem_id="ariaChatbot", elem_classes=["primary-chatbot"]
            )
            user_input = gr.Textbox(
                placeholder="Type a message and press Enter or Send", label="Your message", elem_id="userInput"
            )

            with gr.Row():
                send_btn = gr.Button("Send", variant="primary")
                cancel_btn = gr.Button("Cancel")
                clear_btn = gr.Button("Clear")
                save_btn = gr.Button("Save now")

            provider_info = gr.Textbox(label="Detected provider", interactive=False)
            status = gr.Textbox(label="Status", interactive=False, value="Idle")

        with gr.Column(scale=2, elem_classes=["surface-card", "sidebar-panel"]):
            gr.Markdown("### Sidebar", elem_classes=["section-label"])
            gr.Markdown(
                "Use the sidebar for advanced settings, session history, exports, and automation helpers.",
                elem_classes=["sidebar-note"],
            )

            with gr.Accordion("Model & persona", open=False):
                use_model = gr.Checkbox(label="Use simulation (override provider)", value=False)
                provider_select = gr.Dropdown(
                    choices=["auto", "qai", "quantum", "local", "ollama", "lmstudio", "openai", "azure", "lora", "agi"],
                    value=default_provider_choice(),
                    label="Provider",
                    elem_id="providerSelect",
                )
                model_override = gr.Textbox(
                    label="Model override (optional)",
                    placeholder="e.g., data_out/quantum_llm_training or gpt-4o-mini",
                    elem_id="modelOverride",
                )
                gr.Markdown(provider_readiness_note(), elem_classes=["sidebar-note"])
                gr.Markdown(provider_diagnostics_summary(), elem_classes=["sidebar-note"])
                temperature = gr.Slider(
                    minimum=0.0, maximum=1.0, value=0.7, step=0.05, label="Temperature", elem_id="temperature"
                )
                max_output_tokens = gr.Slider(
                    minimum=16, maximum=2048, step=16, value=512, label="Max output tokens", elem_id="maxTokens"
                )
                persona = gr.Textbox(label="Assistant name", value="QAI")
                persona_presets = gr.Dropdown(
                    choices=["QAI (Friendly)", "Researcher", "Code Assistant"],
                    value="QAI (Friendly)",
                    label="Persona presets",
                )
                autosave = gr.Checkbox(label="Autosave conversation", value=True)
                max_history = gr.Slider(minimum=10, maximum=1000, step=10, value=200, label="Max history (messages)")
                session_name = gr.Textbox(label="Session name (optional)", placeholder="session-2026-05-16")

            with gr.Accordion("Session library", open=False):
                saved_sessions = gr.Dropdown(choices=[], label="Saved sessions", elem_id="savedSessions")
                with gr.Row():
                    refresh_sessions_btn = gr.Button("Refresh sessions")
                    load_session_btn = gr.Button("Load session")
                    delete_session_btn = gr.Button("Delete session")
                with gr.Row():
                    message_index = gr.Number(value=0, label="Conversation index (0-based)")
                    edit_side = gr.Dropdown(choices=["user", "assistant"], value="assistant", label="Edit side")
                edit_message_text = gr.Textbox(label="New message content", placeholder="Replace text")
                with gr.Row():
                    edit_message_btn = gr.Button("Edit message")
                    delete_message_btn = gr.Button("Delete message")
                search_input = gr.Textbox(label="Search conversation", placeholder="Enter text to search")
                with gr.Row():
                    search_btn = gr.Button("Search")
                    revert_btn = gr.Button("Show all")
                load_latest_btn = gr.Button("Load latest")

                with gr.Accordion("Repo automation", open=False):
                    repo_automation_status = gr.Markdown(repo_automation_status_summary())
                    repo_automation_next = gr.Markdown(repo_automation_next_step())
                    repo_automation_actions = gr.Markdown(repo_automation_actions_markdown())
                    with gr.Row():
                        refresh_repo_automation_btn = gr.Button("Refresh repo automation status")
                        run_repo_automation_status_btn = gr.Button("Run repo automation status")
                        run_repo_automation_validate_btn = gr.Button("Run repo automation validate")
                    repo_automation_command_output = gr.Markdown("")

            with gr.Accordion("Exports & webhook", open=False):
                with gr.Row():
                    export_json_btn = gr.Button("Export JSON")
                    export_jsonl_btn = gr.Button("Export JSONL")
                with gr.Row():
                    export_md_btn = gr.Button("Export Markdown")
                    export_txt_btn = gr.Button("Export TXT")
                export_file = gr.File(label="Conversation file", interactive=False)
                webhook_name = gr.Textbox(label="Webhook name", placeholder="webhook-id")
                webhook_dir = gr.Textbox(label="Webhook directory (optional)", placeholder="data_out/webhooks")
                webhook_autocommit = gr.Checkbox(label="Auto-commit (git)", value=False)
                send_to_webhook_btn = gr.Button("Send to Webhook")

            with gr.Accordion("TTS & suggestions", open=False):
                with gr.Row():
                    tts_autoplay = gr.Checkbox(label="Autoplay assistant audio", value=False)
                    tts_backend = gr.Dropdown(choices=["auto", "pyttsx3", "gtts"], value="auto", label="TTS backend")
                speak_btn = gr.Button("Speak last reply")
                tts_audio = gr.Audio(label="Assistant audio", interactive=False)
                auto_improve_enable = gr.Checkbox(label="Auto-improve (background)", value=False)
                auto_improve_interval = gr.Slider(
                    minimum=5, maximum=3600, step=5, value=60, label="Auto-improve interval (sec)"
                )
                suggestions_dropdown = gr.Dropdown(choices=[], label="Auto suggestions", elem_id="suggestionsDropdown")
                with gr.Row():
                    refresh_suggestions_btn = gr.Button("Refresh suggestions")
                    apply_suggestion_btn = gr.Button("Apply suggestion")
                    delete_suggestion_btn = gr.Button("Delete suggestion")

        # Hidden state that stores structured conversation (list of dicts)
        hist_state = gr.State(initial_hist_state)

        suggestions_state = gr.State([])
        request_tokens = gr.State({"latest": None, "tokens": {}})
        default_language = gr.State("English")

        # ------------------------------------------------------------------
        # Actions / Callbacks
        # ------------------------------------------------------------------
        def respond(
            user_message,
            chat_history,
            hist_state,
            use_model,
            provider_choice,
            model_override_val,
            temperature_val,
            max_output_tokens_val,
            lang,
            persona_val,
            autosave,
            max_history,
            session_name,
            request_tokens=None,
        ):
            """Respond and stream updates. Returns (chat_history, cleared_input, hist_state, provider_info, status)."""
            chat_history = chat_history or []
            hist_state = hist_state or []
            if request_tokens is not None and not isinstance(request_tokens, dict):
                request_tokens = None
            # Normalize legacy tuple-pair history into message dicts.
            if chat_history and isinstance(chat_history[0], tuple | list):
                normalized = []
                for pair in chat_history:
                    if not isinstance(pair, tuple | list) or len(pair) != 2:
                        continue
                    normalized.append({"role": "user", "content": str(pair[0])})
                    normalized.append({"role": "assistant", "content": str(pair[1])})
                chat_history = normalized
            if not user_message or not str(user_message).strip():
                if request_tokens:
                    return chat_history, "", hist_state, "", "Idle", request_tokens
                return chat_history, "", hist_state, "", "Idle"

            user_message = str(user_message).strip()
            user_ts = timestamp_now()
            # Create a request-scoped cancellation token only when request_tokens state is provided
            token_event = None
            token_id = None
            if request_tokens is not None:
                token_event = threading.Event()
                token_id = str(time.time())
                # request_tokens is a gr.State dict like {"latest": id, "tokens": {id: Event}}
                try:
                    req_tokens = request_tokens or {"latest": None, "tokens": {}}
                    tokens_map = req_tokens.get("tokens", {})
                    tokens_map[token_id] = token_event
                    req_tokens["tokens"] = tokens_map
                    req_tokens["latest"] = token_id
                    request_tokens = req_tokens
                except Exception:
                    # fallback: no cancel support for this request
                    token_event = None
                    token_id = None

            # Build provider-friendly history
            messages = []
            for e in hist_state:
                u = e.get("user", "")
                a = e.get("assistant", "")
                if u:
                    messages.append({"role": "user", "content": u})
                if a:
                    messages.append({"role": "assistant", "content": a})
            messages.append({"role": "user", "content": user_message})

            provider_display = ""

            # Simulated quick reply
            if use_model:
                reply = f"[{persona_val}-{lang}] " + user_message[::-1]
                provider_display = "simulation"
                assistant_ts = timestamp_now()
                display_user = f"{user_message}\n\n[{user_ts}]"
                display_assistant = f"{reply}\n\n[{assistant_ts}]"
                chat_history = chat_history + [
                    {"role": "user", "content": display_user},
                    {"role": "assistant", "content": display_assistant},
                ]
                hist_state = hist_state + [
                    {"user": user_message, "assistant": reply, "user_ts": user_ts, "assistant_ts": assistant_ts}
                ]
                # enforce max_history
                try:
                    mh = int(max_history) if max_history else None
                except Exception:
                    mh = None
                if mh and len(hist_state) > mh:
                    hist_state = hist_state[-mh:]
                if autosave:
                    try:
                        save_conversation_json(hist_state, session_name or "session")
                    except Exception:
                        pass
                if request_tokens:
                    return chat_history, "", hist_state, provider_display, "Idle", request_tokens
                return chat_history, "", hist_state, provider_display, "Idle"

            # Try using repo providers if available
            try:
                import sys
                from pathlib import Path

                chat_cli_src = Path(__file__).resolve().parents[1] / "ai-projects" / "chat-cli" / "src"
                if str(chat_cli_src) not in sys.path:
                    sys.path.insert(0, str(chat_cli_src))
                from shared.chat_providers import detect_provider  # pyright: ignore[reportAttributeAccessIssue]

                provider, info = detect_provider(
                    explicit=str(provider_choice) if provider_choice else None,
                    model_override=str(model_override_val) if model_override_val else None,
                    temperature=float(temperature_val) if temperature_val is not None else None,
                    max_output_tokens=int(max_output_tokens_val) if max_output_tokens_val else None,
                )
                provider_display = f"{info.name} ({info.model})"
            except Exception:
                # Fallback echo
                provider_display = "fallback"
                reply = f"Echo ({lang}): {user_message}"
                assistant_ts = timestamp_now()
                display_user = f"{user_message}\n\n[{user_ts}]"
                display_assistant = f"{reply}\n\n[{assistant_ts}]"
                chat_history = chat_history + [
                    {"role": "user", "content": display_user},
                    {"role": "assistant", "content": display_assistant},
                ]
                hist_state = hist_state + [
                    {"user": user_message, "assistant": reply, "user_ts": user_ts, "assistant_ts": assistant_ts}
                ]
                # enforce max_history
                try:
                    mh = int(max_history) if max_history else None
                except Exception:
                    mh = None
                if mh and len(hist_state) > mh:
                    hist_state = hist_state[-mh:]
                if autosave:
                    try:
                        save_conversation_json(hist_state, session_name or "session")
                    except Exception:
                        pass
                if request_tokens:
                    return chat_history, "", hist_state, provider_display, "Idle", request_tokens
                return chat_history, "", hist_state, provider_display, "Idle"

            # Initial UI placeholder and streaming status
            display_user = f"{user_message}\n\n[{user_ts}]"
            display_assistant = f"...\n\n[{timestamp_now()}]"
            chat_history = chat_history + [
                {"role": "user", "content": display_user},
                {"role": "assistant", "content": display_assistant},
            ]

            # Yield initial state (client will show 'Streaming...')
            if request_tokens:
                yield chat_history, "", hist_state, provider_display, "Streaming...", request_tokens
            else:
                yield chat_history, "", hist_state, provider_display, "Streaming..."

            partial = ""
            try:
                stream_resp = provider.complete(messages, stream=True)
                if hasattr(stream_resp, "__iter__") and not isinstance(stream_resp, str):
                    for chunk in stream_resp:
                        # allow external cancel
                        if token_event is not None and token_event.is_set():
                            partial += "\n\n[Cancelled]"
                            display_assistant = f"{partial}\n\n[{timestamp_now()}]"
                            chat_history[-1] = {"role": "assistant", "content": display_assistant}
                            # best-effort provider cleanup
                            try:
                                if hasattr(provider, "cancel"):
                                    provider.cancel()
                                elif hasattr(provider, "close"):
                                    provider.close()
                                elif hasattr(provider, "stop"):
                                    provider.stop()
                                elif hasattr(provider, "aclose"):
                                    try:
                                        provider.aclose()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            # cleanup token
                            try:
                                if token_id and isinstance(request_tokens, dict):
                                    request_tokens.get("tokens", {}).pop(token_id, None)
                                    request_tokens["latest"] = None
                            except Exception:
                                pass
                            if request_tokens:
                                yield chat_history, "", hist_state, provider_display, "Cancelled", request_tokens
                            else:
                                yield chat_history, "", hist_state, provider_display, "Cancelled"
                            break
                        chunk_text = str(chunk) if chunk is not None else ""
                        partial += chunk_text
                        display_assistant = f"{partial}\n\n[{timestamp_now()}]"
                        chat_history[-1] = {"role": "assistant", "content": display_assistant}
                        if request_tokens:
                            yield chat_history, "", hist_state, provider_display, "Streaming...", request_tokens
                        else:
                            yield chat_history, "", hist_state, provider_display, "Streaming..."
                else:
                    partial = str(stream_resp)
            except Exception as e:
                err = f"[Provider error: {str(e)}]"
                display_assistant = f"{err}\n\n[{timestamp_now()}]"
                chat_history[-1] = {"role": "assistant", "content": display_assistant}
                hist_state = hist_state + [
                    {"user": user_message, "assistant": err, "user_ts": user_ts, "assistant_ts": timestamp_now()}
                ]
                if autosave:
                    try:
                        save_conversation_json(hist_state, session_name or "session")
                    except Exception:
                        pass
                if request_tokens:
                    yield chat_history, "", hist_state, provider_display, "Idle", request_tokens
                    return
                yield chat_history, "", hist_state, provider_display, "Idle"
                return

            # Finalize
            assistant_ts = timestamp_now()
            reply = partial
            display_assistant = f"{reply}\n\n[{assistant_ts}]"
            chat_history[-1] = {"role": "assistant", "content": display_assistant}
            hist_state = hist_state + [
                {"user": user_message, "assistant": reply, "user_ts": user_ts, "assistant_ts": assistant_ts}
            ]
            # enforce max_history
            try:
                mh = int(max_history) if max_history else None
            except Exception:
                mh = None
            if mh and len(hist_state) > mh:
                hist_state = hist_state[-mh:]
            if autosave:
                try:
                    save_conversation_json(hist_state, session_name or "session")
                except Exception:
                    pass
            if request_tokens:
                yield chat_history, "", hist_state, provider_display, "Idle", request_tokens
                return
            yield chat_history, "", hist_state, provider_display, "Idle"
            return

        # Wire send button and Enter key (submit)
        send_btn.click(
            respond,
            inputs=[
                user_input,
                chatbot,
                hist_state,
                use_model,
                provider_select,
                model_override,
                temperature,
                max_output_tokens,
                default_language,
                persona,
                autosave,
                max_history,
                session_name,
                request_tokens,
            ],
            outputs=[chatbot, user_input, hist_state, provider_info, status, request_tokens],
            queue=True,
        )
        user_input.submit(
            respond,
            inputs=[
                user_input,
                chatbot,
                hist_state,
                use_model,
                provider_select,
                model_override,
                temperature,
                max_output_tokens,
                default_language,
                persona,
                autosave,
                max_history,
                session_name,
                request_tokens,
            ],
            outputs=[chatbot, user_input, hist_state, provider_info, status, request_tokens],
            queue=True,
        )

        def cancel_stream(request_tokens):
            """Cancel the latest active streaming request if present."""
            try:
                if request_tokens and isinstance(request_tokens, dict):
                    lid = request_tokens.get("latest")
                    if lid:
                        tok = request_tokens.get("tokens", {}).get(lid)
                        if tok:
                            try:
                                tok.set()
                            except Exception:
                                pass
                            # cleanup
                            request_tokens.get("tokens", {}).pop(lid, None)
                            request_tokens["latest"] = None
                            return "Cancelled"
            except Exception:
                pass
            return "No active stream"

        cancel_btn.click(cancel_stream, inputs=[request_tokens], outputs=[status, request_tokens])

        def apply_persona(preset, persona_field):
            if not preset:
                return persona_field
            if preset.startswith("QAI"):
                return "QAI"
            if preset == "Researcher":
                return "QAI Research"
            if preset == "Code Assistant":
                return "QAI-Dev"
            return persona_field

        persona_presets.change(apply_persona, inputs=[persona_presets, persona], outputs=[persona])

        def clear_history():
            return [], []

        clear_btn.click(clear_history, outputs=[chatbot, hist_state])

        def save_now(hist_state, session_name):
            if not hist_state:
                return None
            return save_conversation_json(hist_state, session_name or "session")

        save_btn.click(save_now, inputs=[hist_state, session_name], outputs=[export_file])

        def export_json(hist_state, session_name):
            if not hist_state:
                return None
            return save_conversation_json(hist_state, session_name or "session")

        def export_md(hist_state, session_name):
            if not hist_state:
                return None
            return save_conversation_markdown(hist_state, session_name or "session")

        export_json_btn.click(export_json, inputs=[hist_state, session_name], outputs=[export_file])
        export_md_btn.click(export_md, inputs=[hist_state, session_name], outputs=[export_file])

        def _sanitize_session_name(name: Any) -> str:
            raw = str(name or "session").strip()
            sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", raw)
            sanitized = sanitized.strip("._-")
            return sanitized or "session"

        def export_txt(hist_state, session_name):
            if not hist_state:
                return None
            ensure_conv_dir()
            ts = int(time.time())
            conv_root = os.path.realpath(CONV_DIR)
            base_name = f"session_{ts}_{uuid.uuid4().hex}"
            filename = os.path.realpath(os.path.join(conv_root, f"{base_name}.txt"))
            temp = os.path.realpath(os.path.join(conv_root, f"{base_name}.txt.tmp"))
            if os.path.commonpath([conv_root, filename]) != conv_root:
                return None
            if os.path.commonpath([conv_root, temp]) != conv_root:
                return None
            try:
                with _conv_lock():
                    with open(temp, "w", encoding="utf-8") as f:
                        for e in hist_state:
                            ut = e.get("user_ts", "")
                            at = e.get("assistant_ts", "")
                            f.write(f"User [{ut}]:\n")
                            f.write(e.get("user", "") + "\n\n")
                            f.write(f"Assistant [{at}]:\n")
                            f.write(e.get("assistant", "") + "\n\n---\n\n")
                    os.replace(temp, filename)
            finally:
                if os.path.exists(temp):
                    try:
                        os.remove(temp)
                    except Exception:
                        pass
            return filename

        def export_jsonl(hist_state, session_name):
            if not hist_state:
                return None
            ensure_conv_dir()
            ts = int(time.time())
            conv_root = os.path.realpath(CONV_DIR)
            base_name = f"session_{ts}_{uuid.uuid4().hex}"
            filename = os.path.realpath(os.path.join(conv_root, f"{base_name}.jsonl"))
            temp = os.path.realpath(os.path.join(conv_root, f"{base_name}.jsonl.tmp"))
            if os.path.commonpath([conv_root, filename]) != conv_root:
                return None
            if os.path.commonpath([conv_root, temp]) != conv_root:
                return None
            try:
                with _conv_lock():
                    with open(temp, "w", encoding="utf-8") as f:
                        for e in hist_state:
                            f.write(json.dumps(e, ensure_ascii=False) + "\n")
                    os.replace(temp, filename)
            finally:
                if os.path.exists(temp):
                    try:
                        os.remove(temp)
                    except Exception:
                        pass
            return filename

        export_jsonl_btn.click(export_jsonl, inputs=[hist_state, session_name], outputs=[export_file])
        export_txt_btn.click(export_txt, inputs=[hist_state, session_name], outputs=[export_file])

        # Webhook controls
        webhook_name = gr.Textbox(label="Webhook name", placeholder="webhook-id")
        webhook_dir = gr.Textbox(label="Webhook directory (optional)", placeholder="data_out/webhooks")
        webhook_autocommit = gr.Checkbox(label="Auto-commit (git)", value=False)
        send_to_webhook_btn = gr.Button("Send to Webhook")

        def _git_commit_file(path: str) -> bool:
            try:
                import subprocess

                if not path or not os.path.exists(path):
                    return False
                # best-effort commit
                subprocess.run(["git", "add", path], check=False)
                msg = f"Add conversation {os.path.basename(path)}"
                subprocess.run(["git", "commit", "-m", msg, path], check=False)
                return True
            except Exception:
                return False

        def send_to_webhook(hist_state, webhook_name, webhook_dir, autocommit):
            try:
                try:
                    import gradio_webhook
                except ModuleNotFoundError:
                    # attempt to load local scripts/gradio_webhook.py relative to this file
                    import importlib.util
                    from pathlib import Path

                    p = Path(__file__).resolve().parent / "gradio_webhook.py"
                    if not p.exists():
                        raise
                    spec = importlib.util.spec_from_file_location("gradio_webhook", str(p))
                    if spec is None or spec.loader is None:
                        raise RuntimeError("Unable to load gradio_webhook module") from None
                    gradio_webhook = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(gradio_webhook)
                target = webhook_dir if webhook_dir else None
                path = gradio_webhook.post_conversation_to_webhook(
                    hist_state, webhook_name=webhook_name, webhook_dir=target
                )
                if autocommit:
                    try:
                        _git_commit_file(path)
                    except Exception:
                        pass
                return path, "Sent"
            except Exception as e:
                return None, f"Error: {str(e)}"

        send_to_webhook_btn.click(
            send_to_webhook,
            inputs=[hist_state, webhook_name, webhook_dir, webhook_autocommit],
            outputs=[export_file, status],
        )

        def _list_session_files():
            ensure_conv_dir()
            files = []
            for fname in sorted(os.listdir(CONV_DIR)):
                if re.fullmatch(r"[A-Za-z0-9_.-]+\.(json|md|txt)", fname):
                    files.append(fname)
            return files

        def list_sessions():
            files = _list_session_files()
            return gr.update(choices=files, value=files[0] if files else None)

        refresh_sessions_btn.click(list_sessions, outputs=[saved_sessions])

        def _safe_session_path(filename):
            if not filename or not isinstance(filename, str):
                return None
            # Normalize to basename and reject any path components from user input.
            safe_name = Path(filename).name
            if safe_name != filename:
                return None
            # Only allow plain safe filenames with approved extensions.
            if not re.fullmatch(r"[A-Za-z0-9_.-]+\.(json|md|txt)", safe_name):
                return None
            base = Path(CONV_DIR).resolve()
            candidate = (base / safe_name).resolve()
            try:
                candidate.relative_to(base)
            except ValueError:
                return None
            return str(candidate)

        def load_session(filename):
            path = _safe_session_path(filename)
            if not path or not os.path.isfile(path):
                return [], []
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                display = hist_state_to_messages(data)
                return display, data
            except Exception:
                return [], []

        load_session_btn.click(load_session, inputs=[saved_sessions], outputs=[chatbot, hist_state])

        def delete_session(filename):
            files = _list_session_files()
            if filename not in files:
                return gr.update(choices=files, value=files[0] if files else None)

            path = _safe_session_path(filename)
            if not path:
                return gr.update(choices=files, value=files[0] if files else None)

            resolved = Path(path).resolve()
            base = Path(CONV_DIR).resolve()
            if resolved.parent != base or not resolved.is_file():
                return gr.update(choices=files, value=files[0] if files else None)

            try:
                os.remove(str(resolved))
            except Exception:
                pass

            files = _list_session_files()
            return gr.update(choices=files, value=files[0] if files else None)

        delete_session_btn.click(delete_session, inputs=[saved_sessions], outputs=[saved_sessions])

        def edit_message(index, side, new_text, hist_state, autosave, session_name):
            try:
                i = int(index)
            except Exception:
                return hist_state_to_messages(hist_state), hist_state
            if not hist_state or i < 0 or i >= len(hist_state):
                return hist_state_to_messages(hist_state), hist_state
            if side not in ("user", "assistant"):
                side = "assistant"
            hist_state = list(hist_state)
            entry = dict(hist_state[i])
            entry[side] = str(new_text)
            if side == "assistant":
                entry["assistant_ts"] = timestamp_now()
            hist_state[i] = entry
            if autosave:
                try:
                    save_conversation_json(hist_state, session_name or "session")
                except Exception:
                    pass
            return hist_state_to_messages(hist_state), hist_state

        def delete_message_by_index(index, hist_state, autosave, session_name):
            try:
                i = int(index)
            except Exception:
                return hist_state_to_messages(hist_state), hist_state
            if not hist_state or i < 0 or i >= len(hist_state):
                return hist_state_to_messages(hist_state), hist_state
            hist_state = list(hist_state)
            hist_state.pop(i)
            if autosave:
                try:
                    save_conversation_json(hist_state, session_name or "session")
                except Exception:
                    pass
            return hist_state_to_messages(hist_state), hist_state

        edit_message_btn.click(
            edit_message,
            inputs=[message_index, edit_side, edit_message_text, hist_state, autosave, session_name],
            outputs=[chatbot, hist_state],
        )
        delete_message_btn.click(
            delete_message_by_index,
            inputs=[message_index, hist_state, autosave, session_name],
            outputs=[chatbot, hist_state],
        )

        def load_latest_click():
            display, hist = load_latest_conversation()
            return hist_state_to_messages(hist), hist

        load_latest_btn.click(load_latest_click, outputs=[chatbot, hist_state])

        def generate_tts_for_text(text: str, backend: str | None = None) -> str | None:
            """Generate TTS audio file for text. Falls back to a short silent WAV if no TTS backends are available.

            Returns path to audio file or None on unrecoverable errors.
            """
            if not text or not str(text).strip():
                return None
            try:
                ensure_conv_dir()
                tts_dir = os.path.join(CONV_DIR, "tts")
                os.makedirs(tts_dir, exist_ok=True)
                ts = int(time.time())
                wav_path = os.path.join(tts_dir, f"tts_{ts}.wav")

                def try_pyttsx3():
                    try:
                        import pyttsx3

                        engine = pyttsx3.init()
                        engine.save_to_file(text, wav_path)
                        engine.runAndWait()
                        return wav_path
                    except Exception:
                        return None

                def try_gtts():
                    try:
                        from gtts import gTTS

                        mp3_path = wav_path.replace(".wav", ".mp3")
                        tts = gTTS(text)
                        tts.save(mp3_path)
                        return mp3_path
                    except Exception:
                        return None

                def write_silent_wav(path: str, duration: float = 0.1) -> str | None:
                    try:
                        import wave

                        n_channels = 1
                        sampwidth = 2
                        framerate = 22050
                        n_frames = int(framerate * duration)
                        silence = (b"\x00\x00") * n_frames
                        with wave.open(path, "wb") as wf:
                            wf.setnchannels(n_channels)
                            wf.setsampwidth(sampwidth)
                            wf.setframerate(framerate)
                            wf.writeframes(silence)
                        return path
                    except Exception:
                        return None

                # backend selection
                if backend == "pyttsx3":
                    res = try_pyttsx3()
                    if res:
                        return res
                    return write_silent_wav(wav_path)
                if backend == "gtts":
                    res = try_gtts()
                    if res:
                        return res
                    return write_silent_wav(wav_path)

                # auto: prefer pyttsx3 then gTTS, then silent fallback
                res = try_pyttsx3()
                if res:
                    return res
                res = try_gtts()
                if res:
                    return res
                # final fallback: produce a short silent WAV so the UI can play a harmless audio file
                return write_silent_wav(wav_path)
            except Exception:
                return None

        def speak_last(hist_state, autoplay, tts_backend):
            if not hist_state:
                return None
            last = hist_state[-1]
            assistant_text = last.get("assistant", "")
            path = generate_tts_for_text(assistant_text, backend=tts_backend)
            return path

        speak_btn.click(speak_last, inputs=[hist_state, tts_autoplay, tts_backend], outputs=[tts_audio])

        def search_chat(query, hist_state):
            if not query or not hist_state:
                return []
            q = str(query).lower()
            filtered = []
            for e in hist_state:
                u = e.get("user", "")
                a = e.get("assistant", "")
                if q in u.lower() or q in a.lower():
                    ut = e.get("user_ts", "")
                    at = e.get("assistant_ts", "")
                    filtered.append({"role": "user", "content": f"{u}\n\n[{ut}]"})
                    filtered.append({"role": "assistant", "content": f"{a}\n\n[{at}]"})
            return filtered

        search_btn.click(search_chat, inputs=[search_input, hist_state], outputs=[chatbot])

        def revert_search(hist_state):
            return hist_state_to_messages(hist_state)

        revert_btn.click(revert_search, inputs=[hist_state], outputs=[chatbot])

        def refresh_suggestions():
            items = load_suggestions()
            choices = []
            for it in items:
                stext = it.get("suggestion", "").replace("\n", " ")
                choices.append(f"{it.get('ts', '')} - {stext[:140]}")
            return gr.update(choices=choices, value=choices[0] if choices else None)

        def apply_suggestion(choice, hist_state, session_name, autosave):
            if not choice:
                return hist_state_to_messages(hist_state), hist_state
            items = load_suggestions()
            stext = None
            for it in items:
                s_preview = it.get("suggestion", "").replace("\n", " ")[:140]
                label = f"{it.get('ts', '')} - {s_preview}"
                if label == choice or choice in it.get("suggestion", ""):
                    stext = it.get("suggestion")
                    break
            if not stext:
                return hist_state_to_messages(hist_state), hist_state
            assistant_ts = timestamp_now()
            hist_state = hist_state + [{"user": "", "assistant": stext, "user_ts": "", "assistant_ts": assistant_ts}]
            if autosave:
                try:
                    save_conversation_json(hist_state, session_name or "session")
                except Exception:
                    pass
            return hist_state_to_messages(hist_state), hist_state

        def delete_suggestion(choice):
            items = load_suggestions()
            if not choice:
                choices = [
                    "{} - {}".format(it.get("ts", ""), it.get("suggestion", "")[:140].replace("\n", " "))
                    for it in items
                ]
                return gr.update(choices=choices, value=choices[0] if choices else None)
            new_items = []
            for it in items:
                label = "{} - {}".format(it.get("ts", ""), it.get("suggestion", "")[:140].replace("\n", " "))
                if label != choice:
                    new_items.append(it)
            save_suggestions(new_items)
            choices = [
                "{} - {}".format(it.get("ts", ""), it.get("suggestion", "")[:140].replace("\n", " "))
                for it in new_items
            ]
            return gr.update(choices=choices, value=choices[0] if choices else None)

        # Wire suggestion controls
        refresh_suggestions_btn.click(refresh_suggestions, outputs=[suggestions_dropdown])
        apply_suggestion_btn.click(
            apply_suggestion,
            inputs=[suggestions_dropdown, hist_state, session_name, autosave],
            outputs=[chatbot, hist_state],
        )
        delete_suggestion_btn.click(delete_suggestion, inputs=[suggestions_dropdown], outputs=[suggestions_dropdown])

        def refresh_repo_automation_status():
            return repo_automation_status_summary(), repo_automation_next_step()

        refresh_repo_automation_btn.click(
            refresh_repo_automation_status,
            outputs=[repo_automation_status, repo_automation_next],
        )

        def run_repo_automation_status():
            return run_repo_automation_command("--status")

        def run_repo_automation_validate():
            return run_repo_automation_command("--validate")

        run_repo_automation_status_btn.click(
            run_repo_automation_status,
            outputs=[repo_automation_command_output],
        )
        run_repo_automation_validate_btn.click(
            run_repo_automation_validate,
            outputs=[repo_automation_command_output],
        )

        def apply_theme(is_dark: bool, is_compact: bool):
            base = DARK_CSS if is_dark else LIGHT_CSS
            value = base + (COMPACT_CSS if is_compact else "")
            return gr.update(value=value)

        theme_toggle.change(apply_theme, inputs=[theme_toggle, compact_toggle], outputs=[theme_css])
        compact_toggle.change(apply_theme, inputs=[theme_toggle, compact_toggle], outputs=[theme_css])


if __name__ == "__main__":
    # Allow env override for port and public share link
    port_env = os.environ.get("GRADIO_PORT")
    share_env = os.environ.get("GRADIO_SHARE")
    try:
        port = int(port_env) if port_env else None
    except Exception:
        port = None
    share = True if str(share_env).lower() in ("1", "true", "yes") else False
    print(f"Launching Gradio demo (port={port or 'auto'}, share={share})")
    # start background auto-improve daemon (reads config in data_out)
    try:
        threading.Thread(target=auto_improve_daemon, daemon=True).start()
    except Exception:
        pass
    demo.launch(server_name="127.0.0.1", server_port=port, share=share)
