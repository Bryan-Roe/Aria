"""Enhanced Gradio app for Aria.

Run:
    ./.venv/bin/python scripts/gradio_hello.py

Then open the local URL printed by Gradio.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import gradio as gr

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

CONV_DIR = Path("data_out/gradio_conversations")
LATEST_PATH = CONV_DIR / "latest.json"

CSS = """
:root {
    --bg: #eef4ea;
    --panel: rgba(255, 255, 255, 0.88);
    --panel-strong: #ffffff;
    --ink: #132015;
    --brand: #14532d;
    --brand-2: #4d7c0f;
    --accent: #b45309;
    --muted: #5d6f58;
    --line: rgba(19, 32, 21, 0.10);
    --shadow: 0 18px 50px rgba(19, 32, 21, 0.12);
}
body,
.gradio-container {
    background:
        radial-gradient(1200px 520px at 100% -10%, rgba(128, 211, 95, 0.24), transparent 42%),
        radial-gradient(1000px 460px at -10% -20%, rgba(255, 214, 129, 0.24), transparent 38%),
        linear-gradient(180deg, #f7faf5 0%, #eef4ea 60%, #e7eee1 100%);
    color: var(--ink);
}
.gradio-container,
.gradio-container * {
    transition: background-color 180ms ease, border-color 180ms ease, color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
}
.gradio-container ::selection {
    background: rgba(20, 83, 45, 0.18);
    color: var(--ink);
}
.gradio-container {
    padding: 18px !important;
    border-radius: 20px;
}
#appCard {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 24px;
    padding: 16px;
    width: min(1120px, calc(100vw - 32px));
    margin: 0 auto;
    box-sizing: border-box;
    box-shadow: var(--shadow);
    backdrop-filter: blur(12px);
}
.hero-banner {
    border: 1px solid var(--line);
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(249, 252, 245, 0.84));
    box-shadow: 0 10px 28px rgba(19, 32, 21, 0.08);
    padding: 18px 20px;
    margin-bottom: 16px;
    width: 100%;
    box-sizing: border-box;
}
.hero-title {
    font-size: 1.9rem;
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: -0.04em;
    margin: 0;
    color: var(--ink);
}
.hero-subtitle {
    color: var(--muted);
    margin: 10px 0 0;
    line-height: 1.55;
    max-width: 68ch;
    width: 100%;
}
.pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
}
.pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 700;
    color: var(--brand);
    background: rgba(20, 83, 45, 0.08);
    border: 1px solid rgba(20, 83, 45, 0.14);
}
.section-label {
    margin: 2px 0 8px;
    font-size: 0.76rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 800;
}
.surface-card {
    background: var(--panel-strong);
    border: 1px solid var(--line);
    border-radius: 20px;
    box-shadow: 0 14px 34px rgba(19, 32, 21, 0.08);
    padding: 14px;
    width: 100%;
    box-sizing: border-box;
}
.surface-card .gradio-group,
.surface-card .gradio-row,
.surface-card .gradio-column {
    background: transparent !important;
}
#appCard .form,
#appCard .block,
#appCard .wrap,
#appCard .gradio-group,
#appCard .gradio-row,
#appCard .gradio-column {
    background: transparent !important;
    box-shadow: none !important;
}
#appCard .checkbox-container {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 14px;
    border: 1px solid rgba(19, 32, 21, 0.08);
    background: rgba(255, 255, 255, 0.72);
}
#appCard .checkbox-container:hover {
    background: rgba(20, 83, 45, 0.05);
}
#appCard .checkbox-container input {
    margin: 0;
}
#appCard .checkbox-container label {
    color: var(--ink);
    font-weight: 700;
}
#appCard .gradio-container [data-testid="block-label"],
#appCard .gradio-container label,
#appCard .gradio-container .label-wrap {
    color: var(--ink);
}
#appCard select,
#appCard input,
#appCard textarea {
    background: rgba(255, 255, 255, 0.92) !important;
    border: 1px solid rgba(19, 32, 21, 0.12) !important;
}
#appCard select:hover,
#appCard input:hover,
#appCard textarea:hover {
    border-color: rgba(20, 83, 45, 0.22) !important;
}
#chatPanel {
    background: linear-gradient(180deg, #ffffff 0%, #f8fbf5 100%);
}
.gradio-chatbot {
    min-height: 420px;
    border-radius: 18px;
    overflow: hidden;
}
.gradio-chatbot [data-testid="chatbot"] {
    scrollbar-width: thin;
}
#sidebarPanel {
    background: linear-gradient(180deg, #fbfdf9 0%, #f2f7ed 100%);
}
.simple-note,
.quick-hint {
    color: var(--muted);
    font-size: 0.92rem;
    line-height: 1.45;
}
.simple-note {
    margin-top: 2px;
}
.quick-hint {
    margin-top: 4px;
}
.gradio-container button.primary {
    background: linear-gradient(135deg, var(--brand), var(--brand-2)) !important;
    border: 0 !important;
    color: #f7fff2 !important;
    box-shadow: 0 12px 24px rgba(20, 83, 45, 0.18);
}
.gradio-container button.secondary {
    border-color: rgba(20, 83, 45, 0.16) !important;
    color: #234022 !important;
    background: rgba(255, 255, 255, 0.92) !important;
}
button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 20px rgba(20, 83, 45, 0.12);
}
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    border-radius: 14px !important;
}
.gradio-container input:focus,
.gradio-container textarea:focus,
.gradio-container select:focus {
    outline: 2px solid rgba(77, 124, 15, 0.35) !important;
    outline-offset: 1px;
}
#statusRow textarea {
    font-size: 0.92rem !important;
    line-height: 1.2 !important;
}

@media (max-width: 1100px) {
    .gradio-container {
        padding: 12px !important;
    }
    #appCard {
        padding: 12px;
    }
    .surface-card {
        padding: 12px;
    }
    .gradio-chatbot {
        min-height: 340px;
    }
}

@media (max-width: 760px) {
    .hero-title {
        font-size: 1.48rem;
    }
    .hero-subtitle {
        font-size: 0.92rem;
    }
    #appCard,
    .surface-card {
        border-radius: 14px;
    }
    .gradio-chatbot {
        min-height: 280px;
    }
    button {
        min-height: 42px;
    }
    #statusRow textarea {
        font-size: 0.86rem !important;
    }
}

/* ── Quick-prompt chip row ──────────────────────────── */
.quick-prompts-row {
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 4px;
    margin-bottom: 2px;
}
.quick-prompts-row button {
    border-radius: 999px !important;
    padding: 5px 14px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    border: 1.5px solid rgba(20, 83, 45, 0.18) !important;
    background: rgba(255, 255, 255, 0.82) !important;
    color: var(--brand) !important;
    box-shadow: 0 2px 5px rgba(20, 83, 45, 0.05) !important;
    min-height: 32px !important;
    max-height: 36px !important;
    flex: 1 1 auto !important;
    white-space: nowrap !important;
}
.quick-prompts-row button:hover {
    background: rgba(20, 83, 45, 0.07) !important;
    border-color: rgba(20, 83, 45, 0.28) !important;
    box-shadow: 0 4px 10px rgba(20, 83, 45, 0.10) !important;
}

/* ── Italic timestamps inside chat bubbles ──────────── */
.gradio-chatbot .message em {
    font-size: 0.72rem;
    opacity: 0.38;
    font-style: normal;
    display: block;
    margin-top: 4px;
    letter-spacing: 0.01em;
}

/* ── Thin scrollbar in chatbot ──────────────────────── */
.gradio-chatbot > div {
    scrollbar-width: thin;
    scrollbar-color: rgba(20, 83, 45, 0.20) transparent;
}
.gradio-chatbot > div::-webkit-scrollbar { width: 5px; }
.gradio-chatbot > div::-webkit-scrollbar-thumb {
    background: rgba(20, 83, 45, 0.20);
    border-radius: 999px;
}

/* ── User input box ─────────────────────────────────── */
#userInputBox label { display: none; }
#userInputBox textarea {
    min-height: 54px !important;
    font-size: 1rem !important;
    padding: 14px 16px !important;
    border-radius: 16px !important;
}

/* ── Send row ───────────────────────────────────────── */
#sendRow { gap: 8px; margin-top: 4px; }
#sendRow > * { flex: 1; }
#sendRow > *:first-child { flex: 3 !important; }

/* ── Provider status badge ──────────────────────────── */
#statusRow .wrap { gap: 6px; }
#statusRow textarea {
    font-family: ui-monospace, monospace !important;
    font-size: 0.82rem !important;
    padding: 8px 12px !important;
    border-radius: 10px !important;
    min-height: 36px !important;
}

/* ── Section label ──────────────────────────────────── */
.section-label {
    border-top: 1px solid var(--line);
    padding-top: 8px;
    margin-top: 4px;
}

/* ─────────────────────────────────────────────────────
   DARK MODE
   ───────────────────────────────────────────────────── */
@media (prefers-color-scheme: dark) {
    :root {
        --bg:          #0d1a0c;
        --panel:       rgba(20, 32, 18, 0.94);
        --panel-strong:#182816;
        --ink:         #e0f0da;
        --brand:       #6ee77a;
        --brand-2:     #a3e635;
        --accent:      #fbbf24;
        --muted:       #86a880;
        --line:        rgba(110, 231, 122, 0.10);
        --shadow:      0 18px 50px rgba(0, 0, 0, 0.50);
    }

    body,
    .gradio-container {
        background:
            radial-gradient(1200px 520px at 100% -10%, rgba(30, 75, 25, 0.35), transparent 42%),
            radial-gradient(1000px 460px at -10% -20%, rgba(90, 60, 5, 0.20), transparent 38%),
            linear-gradient(180deg, #101d0e 0%, #0d1a0c 60%, #091308 100%);
        color: var(--ink);
    }

    .gradio-container ::selection {
        background: rgba(110, 231, 122, 0.22);
        color: var(--ink);
    }

    /* Hero banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(24, 40, 22, 0.96), rgba(16, 28, 14, 0.90));
        border-color: rgba(110, 231, 122, 0.10);
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.32);
    }
    .pill {
        color: var(--brand);
        background: rgba(110, 231, 122, 0.10);
        border-color: rgba(110, 231, 122, 0.16);
    }

    /* Cards & panels */
    #appCard {
        background: var(--panel);
        border-color: var(--line);
    }
    .surface-card {
        background: var(--panel-strong);
        border-color: rgba(110, 231, 122, 0.08);
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.38);
    }
    #chatPanel {
        background: linear-gradient(180deg, #1a2c17 0%, #131f11 100%);
    }
    #sidebarPanel {
        background: linear-gradient(180deg, #172514 0%, #111c0f 100%);
    }

    /* Form controls */
    #appCard select,
    #appCard input,
    #appCard textarea {
        background: rgba(20, 32, 18, 0.95) !important;
        border-color: rgba(110, 231, 122, 0.14) !important;
        color: var(--ink) !important;
    }
    #appCard select:hover,
    #appCard input:hover,
    #appCard textarea:hover {
        border-color: rgba(110, 231, 122, 0.28) !important;
    }
    .gradio-container input:focus,
    .gradio-container textarea:focus,
    .gradio-container select:focus {
        outline-color: rgba(163, 230, 53, 0.38) !important;
    }

    /* Checkbox */
    #appCard .checkbox-container {
        background: rgba(24, 40, 22, 0.60);
        border-color: rgba(110, 231, 122, 0.08);
    }
    #appCard .checkbox-container:hover {
        background: rgba(110, 231, 122, 0.06);
    }

    /* Quick-prompt chips */
    .quick-prompts-row button {
        background: rgba(20, 32, 18, 0.88) !important;
        border-color: rgba(110, 231, 122, 0.18) !important;
        color: var(--brand) !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.20) !important;
    }
    .quick-prompts-row button:hover {
        background: rgba(110, 231, 122, 0.08) !important;
        border-color: rgba(110, 231, 122, 0.32) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.28) !important;
    }

    /* Buttons */
    .gradio-container button.primary {
        background: linear-gradient(135deg, #166534, #3a6010) !important;
        box-shadow: 0 10px 22px rgba(0, 0, 0, 0.36) !important;
        color: #d4f5d0 !important;
    }
    .gradio-container button.secondary {
        border-color: rgba(110, 231, 122, 0.18) !important;
        color: var(--brand) !important;
        background: rgba(20, 32, 18, 0.85) !important;
    }
    button:hover {
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.36);
    }

    /* Chatbot scrollbar */
    .gradio-chatbot > div {
        scrollbar-color: rgba(110, 231, 122, 0.22) transparent;
    }
    .gradio-chatbot > div::-webkit-scrollbar-thumb {
        background: rgba(110, 231, 122, 0.22);
    }

    /* Italic timestamps — slightly brighter in dark */
    .gradio-chatbot .message em {
        opacity: 0.48;
    }

    /* Section label border */
    .section-label {
        border-color: rgba(110, 231, 122, 0.10);
    }

    /* Status textarea */
    #statusRow textarea {
        background: rgba(14, 24, 12, 0.80) !important;
        color: var(--muted) !important;
    }
}
"""

THEME = gr.themes.Soft(
    primary_hue="green",
    secondary_hue="amber",
    neutral_hue="stone",
)


def timestamp_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def make_greeting(name: str, style: str, excitement: int, language: str) -> str:
    name = (name or "World").strip()
    greetings = {
        "English": "Hello",
        "Spanish": "Hola",
        "French": "Bonjour",
        "German": "Hallo",
    }
    base = greetings.get(language, "Hello")
    if style == "Formal":
        return f"{base}, {name}."
    if style == "Friendly":
        return f"{base} {name}"
    return f"{base} {name}" + "!" * max(1, int(excitement))


def ensure_conv_dir() -> None:
    CONV_DIR.mkdir(parents=True, exist_ok=True)


def safe_session_name(session_name: str | None) -> str:
    raw = (session_name or "session").strip().replace(" ", "_")
    safe = "".join(ch for ch in raw if ch.isalnum() or ch in ("-", "_"))
    return safe[:64] or "session"


def save_conversation_json(hist_state: list[dict[str, Any]], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = safe_session_name(session_name)
    # Detect path traversal: if the sanitizer was bypassed and safe_name contains
    # directory separators (e.g. "../escape"), reject it explicitly (CWE-73).
    if Path(safe_name).name != safe_name:
        raise ValueError("Invalid session path")
    session_token = hashlib.sha256(safe_name.encode("utf-8")).hexdigest()[:16]
    filename = (CONV_DIR / f"{session_token}_{ts}.json").resolve()
    with filename.open("w", encoding="utf-8") as f:
        json.dump(hist_state, f, ensure_ascii=False, indent=2)
    with LATEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(hist_state, f, ensure_ascii=False, indent=2)
    return str(filename)


def save_conversation_markdown(hist_state: list[dict[str, Any]], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = safe_session_name(session_name)
    filename = CONV_DIR / f"{safe_name}_{ts}.md"
    with filename.open("w", encoding="utf-8") as f:
        for entry in hist_state:
            f.write(f"### User - {entry.get('user_ts', '')}\n")
            f.write(entry.get("user", "") + "\n\n")
            f.write(f"### Assistant - {entry.get('assistant_ts', '')}\n")
            f.write(entry.get("assistant", "") + "\n\n---\n\n")
    return str(filename)


def save_conversation_txt(hist_state: list[dict[str, Any]], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = safe_session_name(session_name)
    filename = CONV_DIR / f"{safe_name}_{ts}.txt"
    with filename.open("w", encoding="utf-8") as f:
        for entry in hist_state:
            f.write(f"User [{entry.get('user_ts', '')}]:\n")
            f.write(entry.get("user", "") + "\n\n")
            f.write(f"Assistant [{entry.get('assistant_ts', '')}]:\n")
            f.write(entry.get("assistant", "") + "\n\n---\n\n")
    return str(filename)


def hist_state_to_display(hist_state: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not hist_state:
        return []
    display: list[dict[str, str]] = []
    for e in hist_state:
        display.append(
            {
                "role": "user",
                "content": f"{e.get('user', '')}\n\n*{e.get('user_ts', '')}*",
            }
        )
        display.append(
            {
                "role": "assistant",
                "content": f"{e.get('assistant', '')}\n\n*{e.get('assistant_ts', '')}*",
            }
        )
    return display


def load_latest_conversation() -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    if not LATEST_PATH.exists():
        return [], []
    try:
        with LATEST_PATH.open("r", encoding="utf-8") as f:
            hist = json.load(f)
    except Exception:
        return [], []
    return hist_state_to_display(hist), hist


def list_json_sessions() -> list[str]:
    ensure_conv_dir()
    return sorted(p.name for p in CONV_DIR.glob("*.json"))


def generate_tts_for_text(text: str) -> str | None:
    if not text or not text.strip():
        return None
    try:
        ensure_conv_dir()
        tts_dir = CONV_DIR / "tts"
        tts_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        wav_path = tts_dir / f"tts_{ts}.wav"
        if pyttsx3:
            try:
                engine = pyttsx3.init()
                engine.save_to_file(text, str(wav_path))
                engine.runAndWait()
                return str(wav_path)
            except Exception:
                pass
        if gTTS:
            try:
                mp3_path = wav_path.with_suffix(".mp3")
                tts = gTTS(text)
                tts.save(str(mp3_path))
                return str(mp3_path)
            except Exception:
                return None
        return None
    except Exception:
        return None


def provider_readiness_note() -> str:
    if os.getenv("LMSTUDIO_BASE_URL"):
        return "LM Studio provider ready."
    if all(
        os.getenv(name)
        for name in (
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_API_VERSION",
        )
    ):
        return "Azure OpenAI provider ready."
    if os.getenv("OPENAI_API_KEY"):
        return "OpenAI provider ready."
    return "No hosted provider configured; local fallback will respond."


def provider_diagnostics_summary() -> str:
    return f"Provider readiness: {provider_readiness_note()}"


def provider_status_snapshot(provider_choice: str) -> tuple[str, str]:
    selected = (provider_choice or "auto").strip().lower()
    readiness = provider_readiness_note()

    if selected == "local":
        return "local (local-echo)", "Using local offline fallback."
    if selected == "lmstudio":
        if os.getenv("LMSTUDIO_BASE_URL"):
            return "lmstudio", "LM Studio provider ready."
        return "lmstudio", "LM Studio selected but not configured in this environment."
    if selected == "azure":
        if all(
            os.getenv(name)
            for name in (
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_DEPLOYMENT",
                "AZURE_OPENAI_API_VERSION",
            )
        ):
            return "azure", "Azure OpenAI provider ready."
        return "azure", "Azure OpenAI selected but required environment variables are missing."
    if selected == "openai":
        if os.getenv("OPENAI_API_KEY"):
            return "openai", "OpenAI provider ready."
        return "openai", "OpenAI selected but OPENAI_API_KEY is missing."
    if selected == "auto":
        if readiness.startswith("No hosted provider configured"):
            return "auto -> local (local-echo)", readiness
        return "auto", readiness
    return selected, readiness


def reset_chat_session(provider_choice: str) -> tuple[list[Any], list[Any], str, str]:
    provider_info, status_info = provider_status_snapshot(provider_choice)
    return [], [], provider_info, status_info


def detect_provider(
    provider_choice: str, model_override_val: str, temperature_val: float, max_output_tokens_val: int
) -> tuple[Any, str]:
    chat_cli_src = Path(__file__).resolve().parents[1] / "ai-projects" / "chat-cli" / "src"
    if str(chat_cli_src) not in sys.path:
        sys.path.insert(0, str(chat_cli_src))

    chat_providers: Any = importlib.import_module("chat_providers")

    detect_provider_fn = getattr(chat_providers, "detect_provider", None)
    if detect_provider_fn is None:
        raise RuntimeError("chat_providers.detect_provider is unavailable")

    provider, info = detect_provider_fn(
        explicit=str(provider_choice) if provider_choice else None,
        model_override=str(model_override_val) if model_override_val else None,
        temperature=float(temperature_val) if temperature_val is not None else None,
        max_output_tokens=int(max_output_tokens_val) if max_output_tokens_val else None,
    )
    return provider, f"{info.name} ({info.model})"


def _looks_like_provider_error(text: str) -> bool:
    lowered = text.lower().strip()
    return lowered.startswith("❌") or any(
        marker in lowered
        for marker in (
            "not found in ollama",
            "cannot connect to ollama",
            "provider unavailable",
            "api key",
            "quota",
            "rate limit",
        )
    )


def respond(
    user_message: str,
    chat_history: list[dict[str, str]],
    hist_state: list[dict[str, Any]],
    use_model: bool,
    provider_choice: str,
    model_override_val: str,
    temperature_val: float,
    max_output_tokens_val: int,
    lang: str,
    persona: str,
    autosave: bool,
    max_history: int,
    session_name: str,
):
    chat_history = chat_history or []
    hist_state = hist_state or []
    if not user_message or not str(user_message).strip():
        yield chat_history, "", hist_state, "", "Waiting for input."
        return

    user_message = str(user_message).strip()
    user_ts = timestamp_now()

    messages: list[dict[str, str]] = []
    for e in hist_state:
        if e.get("user"):
            messages.append({"role": "user", "content": e["user"]})
        if e.get("assistant"):
            messages.append({"role": "assistant", "content": e["assistant"]})
    messages.append({"role": "user", "content": user_message})

    if use_model:
        reply = f"[{persona}-{lang}] " + user_message[::-1]
        assistant_ts = timestamp_now()
        display_user = f"{user_message}\n\n*{user_ts}*"
        display_assistant = f"{reply}\n\n*{assistant_ts}*"
        chat_history = list(chat_history) + [
            {"role": "user", "content": display_user},
            {"role": "assistant", "content": display_assistant},
        ]
        hist_state = list(hist_state) + [
            {
                "user": user_message,
                "assistant": reply,
                "user_ts": user_ts,
                "assistant_ts": assistant_ts,
            }
        ]
        hist_state = hist_state[-int(max_history) :]
        if autosave:
            try:
                save_conversation_json(hist_state, session_name or "session")
            except Exception:
                pass
        yield chat_history[-int(max_history * 2) :], "", hist_state, "simulation", "Replied with simulation mode."
        return

    provider_display = ""
    try:
        provider, provider_display = detect_provider(
            provider_choice,
            model_override_val,
            temperature_val,
            max_output_tokens_val,
        )
    except Exception:
        provider, provider_display = detect_provider(
            "local_echo",
            "",
            temperature_val,
            max_output_tokens_val,
        )
        reply = str(provider.complete(messages, stream=False))
        assistant_ts = timestamp_now()
        display_user = f"{user_message}\n\n*{user_ts}*"
        display_assistant = f"{reply}\n\n*{assistant_ts}*"
        chat_history = list(chat_history) + [
            {"role": "user", "content": display_user},
            {"role": "assistant", "content": display_assistant},
        ]
        hist_state = list(hist_state) + [
            {
                "user": user_message,
                "assistant": reply,
                "user_ts": user_ts,
                "assistant_ts": assistant_ts,
            }
        ]
        hist_state = hist_state[-int(max_history) :]
        if autosave:
            try:
                save_conversation_json(hist_state, session_name or "session")
            except Exception:
                pass
        yield (
            chat_history[-int(max_history * 2) :],
            "",
            hist_state,
            "fallback",
            "Provider unavailable, used local fallback.",
        )
        return

    provider_type = type(provider).__name__.lower()
    if provider_type == "ollamaprovider":
        try:
            full_reply = provider.complete(messages, stream=False)
        except Exception:
            full_reply = ""
        full_reply = str(full_reply)
        if _looks_like_provider_error(full_reply):
            fallback_provider, fallback_display = detect_provider(
                "local_echo",
                "",
                temperature_val,
                max_output_tokens_val,
            )
            fallback_reply = str(fallback_provider.complete(messages, stream=False))
            assistant_ts = timestamp_now()
            display_user = f"{user_message}\n\n*{user_ts}*"
            display_assistant = f"{fallback_reply}\n\n*{assistant_ts}*"
            chat_history = list(chat_history) + [
                {"role": "user", "content": display_user},
                {"role": "assistant", "content": display_assistant},
            ]
            hist_state = list(hist_state) + [
                {
                    "user": user_message,
                    "assistant": fallback_reply,
                    "user_ts": user_ts,
                    "assistant_ts": assistant_ts,
                }
            ]
            hist_state = hist_state[-int(max_history) :]
            if autosave:
                try:
                    save_conversation_json(hist_state, session_name or "session")
                except Exception:
                    pass
            yield (
                chat_history[-int(max_history * 2) :],
                "",
                hist_state,
                fallback_display,
                "Provider fallback used after Ollama error.",
            )
            return
        assistant_ts = timestamp_now()
        display_user = f"{user_message}\n\n*{user_ts}*"
        display_assistant = f"{full_reply}\n\n*{assistant_ts}*"
        chat_history = list(chat_history) + [
            {"role": "user", "content": display_user},
            {"role": "assistant", "content": display_assistant},
        ]
        hist_state = list(hist_state) + [
            {
                "user": user_message,
                "assistant": full_reply,
                "user_ts": user_ts,
                "assistant_ts": assistant_ts,
            }
        ]
        hist_state = hist_state[-int(max_history) :]
        if autosave:
            try:
                save_conversation_json(hist_state, session_name or "session")
            except Exception:
                pass
        yield chat_history[-int(max_history * 2) :], "", hist_state, provider_display, "Complete."
        return

    display_user = f"{user_message}\n\n*{user_ts}*"
    display_assistant = f"...\n\n*{timestamp_now()}*"
    chat_history = list(chat_history) + [
        {"role": "user", "content": display_user},
        {"role": "assistant", "content": display_assistant},
    ]
    yield chat_history[-int(max_history * 2) :], "", hist_state, provider_display, "Streaming response..."

    partial = ""
    try:
        stream_resp = provider.complete(messages, stream=True)
        if hasattr(stream_resp, "__iter__") and not isinstance(stream_resp, str):
            for chunk in stream_resp:
                partial += str(chunk)
                chat_history[-1] = {"role": "assistant", "content": f"{partial}\n\n*{timestamp_now()}*"}
                yield chat_history[-int(max_history * 2) :], "", hist_state, provider_display, "Streaming response..."
        else:
            partial = str(stream_resp)
    except Exception as e:
        err = f"[Provider error: {str(e)}]"
        chat_history[-1] = {"role": "assistant", "content": f"{err}\n\n*{timestamp_now()}*"}
        hist_state = list(hist_state) + [
            {
                "user": user_message,
                "assistant": err,
                "user_ts": user_ts,
                "assistant_ts": timestamp_now(),
            }
        ]
        hist_state = hist_state[-int(max_history) :]
        if autosave:
            try:
                save_conversation_json(hist_state, session_name or "session")
            except Exception:
                pass
        yield (
            chat_history[-int(max_history * 2) :],
            "",
            hist_state,
            provider_display,
            "Provider failed; error captured in chat.",
        )
        return

    assistant_ts = timestamp_now()
    chat_history[-1] = {"role": "assistant", "content": f"{partial}\n\n*{assistant_ts}*"}
    hist_state = list(hist_state) + [
        {
            "user": user_message,
            "assistant": partial,
            "user_ts": user_ts,
            "assistant_ts": assistant_ts,
        }
    ]
    hist_state = hist_state[-int(max_history) :]
    if autosave:
        try:
            save_conversation_json(hist_state, session_name or "session")
        except Exception:
            pass
    yield chat_history[-int(max_history * 2) :], "", hist_state, provider_display, "Complete."


def run_llm_smoke_test(
    chat_history: list[dict[str, str]],
    hist_state: list[dict[str, Any]],
    use_model: bool,
    provider_choice: str,
    model_override_val: str,
    temperature_val: float,
    max_output_tokens_val: int,
    lang: str,
    persona: str,
    autosave: bool,
    max_history: int,
    session_name: str,
):
    smoke_prompt = "LLM smoke test: reply with a short friendly confirmation that the model is working."
    last_result = None
    for result in respond(
        smoke_prompt,
        chat_history,
        hist_state,
        use_model,
        provider_choice,
        model_override_val,
        temperature_val,
        max_output_tokens_val,
        lang,
        persona,
        autosave,
        max_history,
        session_name,
    ):
        last_result = result
    return (
        last_result
        if last_result is not None
        else (
            chat_history,
            "",
            hist_state,
            "",
            "LLM smoke test did not run.",
        )
    )


initial_display, initial_hist_state = load_latest_conversation()
initial_provider_summary = provider_diagnostics_summary()
initial_provider_info, initial_status_info = provider_status_snapshot("auto")

with gr.Blocks() as demo:
    with gr.Column(elem_id="appCard"):
        gr.HTML(
            """
            <div class="hero-banner">
                <div style="display:flex;align-items:center;gap:14px;">
                    <span style="font-size:2.4rem;line-height:1;filter:drop-shadow(0 2px 6px rgba(20,83,45,0.16));">🌿</span>
                    <div>
                        <div class="hero-title">Aria Chat</div>
                        <p class="hero-subtitle" style="margin:4px 0 0;">Conversation-first AI assistant &mdash; provider, export, and history controls stay out of the way until you need them.</p>
                    </div>
                </div>
                <div class="pill-row" style="margin-top:14px;">
                    <span class="pill">🔄&nbsp;Multi-provider</span>
                    <span class="pill">💾&nbsp;Autosave</span>
                    <span class="pill">🔍&nbsp;Search history</span>
                    <span class="pill">🎙️&nbsp;TTS support</span>
                </div>
            </div>
            """
        )

        with gr.Row(equal_height=False):
            with gr.Column(scale=7, elem_id="surfaceBlock", elem_classes=["surface-card"]):
                with gr.Accordion("Optional Greeting Demo", open=False):
                    with gr.Row():
                        name = gr.Textbox(label="Name", placeholder="Your name")
                        language = gr.Dropdown(
                            choices=["English", "Spanish", "French", "German"],
                            value="English",
                            label="Language",
                        )

                    with gr.Row():
                        style = gr.Radio(
                            choices=["Friendly", "Formal", "Enthusiastic"],
                            value="Friendly",
                            label="Style",
                        )
                        excitement = gr.Slider(1, 10, value=1, step=1, label="Exclamation count")

                    with gr.Row():
                        greet_btn = gr.Button("Greet", variant="primary")
                        output = gr.Textbox(label="Greeting", interactive=False, lines=2)

                gr.Markdown("<div class='section-label'>Conversation</div>")
                with gr.Column(elem_id="chatPanel", elem_classes=["surface-card"]):
                    chatbot = gr.Chatbot(label="Chat")

                user_input = gr.Textbox(
                    placeholder="Type a message and press Enter…",
                    label="Your message",
                    elem_id="userInputBox",
                )
                gr.HTML("<div class='section-label' style='margin-top:6px;'>Quick prompts</div>")
                with gr.Row(elem_classes=["quick-prompts-row"]):
                    qp1 = gr.Button("📋 Today's priorities", variant="secondary")
                    qp2 = gr.Button("📝 Project update", variant="secondary")
                    qp3 = gr.Button("💡 App ideas", variant="secondary")

                with gr.Row(elem_id="sendRow"):
                    send_btn = gr.Button("➤ Send", variant="primary")
                    clear_btn = gr.Button("🗑 Clear", variant="secondary")
                    save_btn = gr.Button("💾 Save", variant="secondary")

                with gr.Row():
                    llm_test_btn = gr.Button("🧪 Test LLM", variant="secondary")

                gr.Markdown("<div class='section-label'>Session status</div>")
                with gr.Row(elem_id="statusRow"):
                    provider_info = gr.Textbox(label="Detected provider", interactive=False)
                    status_info = gr.Textbox(label="Status", interactive=False)

            with gr.Column(scale=5, elem_id="sidebarPanel", elem_classes=["surface-card"]):
                gr.Markdown("### Controls")
                simple_mode = gr.Checkbox(label="Simple mode", value=True)
                gr.Markdown("<div class='simple-note'>Simple mode hides advanced settings to keep the UI easy.</div>")

                with gr.Row():
                    use_model = gr.Checkbox(label="Use simulation", value=False)
                    provider_select = gr.Dropdown(
                        choices=["auto", "local", "ollama", "lmstudio", "openai", "azure", "lora", "agi", "quantum"],
                        value="auto",
                        label="Provider",
                    )
                gr.Markdown(f"<div class='simple-note'>{provider_diagnostics_summary()}</div>")

                with gr.Column(visible=False) as advanced_controls:
                    with gr.Accordion("Model", open=False):
                        model_override = gr.Textbox(label="Model override", placeholder="Optional model id")
                        persona = gr.Textbox(label="Assistant name", value="Aria")
                        temperature = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="Temperature")
                        max_output_tokens = gr.Slider(16, 2048, value=512, step=16, label="Max output tokens")

                    with gr.Accordion("History and Sessions", open=False):
                        autosave = gr.Checkbox(label="Autosave conversation", value=True)
                        max_history = gr.Slider(10, 500, step=10, value=200, label="Max history (turns)")
                        session_name = gr.Textbox(label="Session name", placeholder="session-2026-05-29")
                        with gr.Row():
                            export_json_btn = gr.Button("Export JSON", variant="secondary")
                            export_md_btn = gr.Button("Export Markdown", variant="secondary")
                        with gr.Row():
                            export_txt_btn = gr.Button("Export TXT", variant="secondary")
                            load_latest_btn = gr.Button("Load latest", variant="secondary")

                        saved_sessions = gr.Dropdown(choices=list_json_sessions(), label="Saved sessions (.json)")
                        with gr.Row():
                            refresh_sessions_btn = gr.Button("Refresh sessions", variant="secondary")
                            load_session_btn = gr.Button("Load session", variant="secondary")
                            delete_session_btn = gr.Button("Delete session", variant="secondary")

                    with gr.Accordion("Search and Audio", open=False):
                        search_input = gr.Textbox(
                            label="Search conversation", placeholder="Search user or assistant text"
                        )
                        with gr.Row():
                            search_btn = gr.Button("Search", variant="secondary")
                            revert_btn = gr.Button("Show all", variant="secondary")
                        tts_autoplay = gr.Checkbox(label="Autoplay assistant audio", value=False)
                        speak_btn = gr.Button("Speak last reply", variant="secondary")
                        tts_audio = gr.Audio(label="Assistant audio", interactive=False)

                    export_file = gr.File(label="Conversation file", interactive=False)

        greet_btn.click(make_greeting, inputs=[name, style, excitement, language], outputs=output)

        hist_state = gr.State(initial_hist_state)

        demo.load(
            lambda: (
                initial_display,
                initial_hist_state,
                initial_provider_info,
                initial_status_info,
            ),
            outputs=[chatbot, hist_state, provider_info, status_info],
        )

        send_inputs = [
            user_input,
            chatbot,
            hist_state,
            use_model,
            provider_select,
            model_override,
            temperature,
            max_output_tokens,
            language,
            persona,
            autosave,
            max_history,
            session_name,
        ]
        send_outputs = [chatbot, user_input, hist_state, provider_info, status_info]

        send_btn.click(respond, inputs=send_inputs, outputs=send_outputs, queue=True)
        user_input.submit(respond, inputs=send_inputs, outputs=send_outputs, queue=True)

        def toggle_advanced(is_simple: bool):
            return gr.update(visible=not bool(is_simple))

        simple_mode.change(toggle_advanced, inputs=[simple_mode], outputs=[advanced_controls])

        provider_select.change(
            provider_status_snapshot,
            inputs=[provider_select],
            outputs=[provider_info, status_info],
        )

        clear_btn.click(
            reset_chat_session,
            inputs=[provider_select],
            outputs=[chatbot, hist_state, provider_info, status_info],
        )

        llm_test_btn.click(
            run_llm_smoke_test,
            inputs=[
                chatbot,
                hist_state,
                use_model,
                provider_select,
                model_override,
                temperature,
                max_output_tokens,
                language,
                persona,
                autosave,
                max_history,
                session_name,
            ],
            outputs=[chatbot, user_input, hist_state, provider_info, status_info],
            queue=True,
        )

        qp1.click(lambda: "Summarize today's priorities in 5 bullets.", outputs=[user_input])
        qp2.click(lambda: "Help me draft a short project update.", outputs=[user_input])
        qp3.click(lambda: "Give me three creative app ideas.", outputs=[user_input])

        save_btn.click(
            lambda h, s: save_conversation_json(h, s or "session") if h else None,
            inputs=[hist_state, session_name],
            outputs=[export_file],
        )

        export_json_btn.click(
            lambda h, s: save_conversation_json(h, s or "session") if h else None,
            inputs=[hist_state, session_name],
            outputs=[export_file],
        )
        export_md_btn.click(
            lambda h, s: save_conversation_markdown(h, s or "session") if h else None,
            inputs=[hist_state, session_name],
            outputs=[export_file],
        )
        export_txt_btn.click(
            lambda h, s: save_conversation_txt(h, s or "session") if h else None,
            inputs=[hist_state, session_name],
            outputs=[export_file],
        )

        load_latest_btn.click(lambda: load_latest_conversation(), outputs=[chatbot, hist_state])

        def refresh_sessions():
            files = list_json_sessions()
            return gr.Dropdown(choices=files, value=(files[0] if files else None))

        refresh_sessions_btn.click(refresh_sessions, outputs=[saved_sessions])

        def safe_session_path(filename: str) -> Path | None:
            if not filename:
                return None
            candidate = Path(filename)
            if candidate.is_absolute() or candidate.name != filename or candidate.suffix.lower() != ".json":
                return None
            try:
                base = CONV_DIR.resolve()
                full = (base / candidate).resolve()
                full.relative_to(base)
            except Exception:
                return None
            return full

        def load_session(filename: str):
            path = safe_session_path(filename)
            if path is None:
                return [], []
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                return [], []
            return hist_state_to_display(data), data

        load_session_btn.click(load_session, inputs=[saved_sessions], outputs=[chatbot, hist_state])

        def delete_session(filename: str):
            path = safe_session_path(filename)
            if path is not None:
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass
            files = list_json_sessions()
            return gr.Dropdown(choices=files, value=(files[0] if files else None))

        delete_session_btn.click(delete_session, inputs=[saved_sessions], outputs=[saved_sessions])

        def search_chat(query: str, hist: list[dict[str, Any]]):
            if not query or not hist:
                return []
            q = query.lower()
            filtered = [e for e in hist if q in e.get("user", "").lower() or q in e.get("assistant", "").lower()]
            return hist_state_to_display(filtered)

        search_btn.click(search_chat, inputs=[search_input, hist_state], outputs=[chatbot])
        revert_btn.click(lambda h: hist_state_to_display(h), inputs=[hist_state], outputs=[chatbot])

        def speak_last(hist: list[dict[str, Any]], autoplay: bool):
            if not hist:
                return None
            return generate_tts_for_text(hist[-1].get("assistant", ""))

        speak_btn.click(speak_last, inputs=[hist_state, tts_autoplay], outputs=[tts_audio])


if __name__ == "__main__":
    os.environ.setdefault("GRADIO_SERVER_PORT", os.environ.get("GRADIO_PORT", "7861"))
    demo.launch(
        css=CSS,
        theme=THEME,
        server_name="127.0.0.1",
    )
