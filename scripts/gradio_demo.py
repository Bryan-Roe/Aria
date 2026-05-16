"""Enhanced Gradio demo for Aria.

Run after installing dependencies:
    ./.venv/bin/python scripts/gradio_demo.py

Then open the local URL printed by Gradio.
"""

import gradio as gr
import os
import json
import time
import tempfile
import threading
import re
import html
from collections import Counter
from datetime import datetime
from typing import List, Tuple, Optional
from contextlib import contextmanager
try:
    import fcntl
except Exception:
    fcntl = None

# Module-level flag to cancel streaming responses
CANCEL_STREAM = False


# Simple theme CSS snippets (injected into the page)
LIGHT_CSS = """<style>
:root { --bg: #ffffff; --fg: #0a0a0a; --card: #f3f4f6; }
body, .gradio-container { background: var(--bg); color: var(--fg); }
.gradio-container { padding: 12px; border-radius: 8px; }
.chatbot { max-height: 420px; overflow: auto; }
</style>"""

DARK_CSS = """<style>
:root { --bg: #0b0f19; --fg: #e6eef8; --card: #0f1720; }
body, .gradio-container { background: var(--bg); color: var(--fg); }
.gradio-container { padding: 12px; border-radius: 8px; }
.chatbot { max-height: 420px; overflow: auto; }
</style>"""

COMPACT_CSS = """<style>
.gradio-container { padding: 6px; }
.gradio-chat { font-size: 12px; line-height: 1.1; }
.gradio-container .gradio-chatbot { max-height: 300px; }
</style>"""


def timestamp_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def make_greeting(name: str, style: str, excitement: int, language: str) -> str:
    """Construct a greeting based on selected style and language."""
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
    # Enthusiastic
    return f"{base} {name}" + "!" * max(1, int(excitement))


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
    try:
        if fcntl:
            fcntl.flock(lf, fcntl.LOCK_EX)
        yield
    finally:
        try:
            if fcntl:
                fcntl.flock(lf, fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            lf.close()
        except Exception:
            pass


def save_conversation_json(hist_state: List[dict], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = (session_name or "session").strip().replace(" ", "_")
    filename = os.path.join(CONV_DIR, f"{safe_name}_{ts}.json")
    temp_filename = filename + ".tmp"
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


def save_conversation_markdown(hist_state: List[dict], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = (session_name or "session").strip().replace(" ", "_")
    filename = os.path.join(CONV_DIR, f"{safe_name}_{ts}.md")
    temp_filename = filename + ".tmp"
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


def load_latest_conversation() -> Tuple[List[Tuple[str, str]], List[dict]]:
    if not os.path.exists(LATEST_PATH):
        return [], []
    try:
        with _conv_lock():
            with open(LATEST_PATH, "r", encoding="utf-8") as f:
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


def hist_state_to_display(hist_state: List[dict]) -> List[Tuple[str, str]]:
    if not hist_state:
        return []
    return [
        (f"{e.get('user','')}\n\n[{e.get('user_ts','')}]", f"{e.get('assistant','')}\n\n[{e.get('assistant_ts','')}]")
        for e in hist_state
    ]


# ---------------------------------------------------------------------------
# Helper utilities (export, summarization, auto-improve daemon)
# ---------------------------------------------------------------------------

# Export conversation to HTML for sharing/viewing
def generate_html_export(hist_state: List[dict], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = (session_name or "session").strip().replace(" ", "_")
    filename = os.path.join(CONV_DIR, f"{safe_name}_{ts}.html")
    temp_filename = filename + ".tmp"
    parts = [
        "<!doctype html>",
        "<html><head><meta charset='utf-8'><title>Conversation</title>",
        "<style>body{font-family:Arial,sans-serif;padding:20px;} .user{background:#eef;padding:8px;margin:6px;border-radius:6px;} .assistant{background:#efe;padding:8px;margin:6px;border-radius:6px;}</style>",
        "</head><body>",
        f"<h1>Conversation — {html.escape(safe_name)}</h1>",
        "<div>",
    ]
    for e in hist_state:
        ut = e.get('user_ts', '')
        at = e.get('assistant_ts', '')
        user = html.escape(e.get('user', ''))
        assistant = html.escape(e.get('assistant', ''))
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
def summarize_conversation_simple(hist_state: List[dict], top_n: int = 5) -> str:
    if not hist_state:
        return "No conversation yet."
    texts = " ".join(((e.get('user','') or '') + " " + (e.get('assistant','') or '') for e in hist_state))
    tokens = re.findall(r"\w+", texts.lower())
    stopwords = set(["the","and","to","a","is","in","it","of","for","on","that","this","with","as","are","was","i","you","we","they","he","she","be"])  # simple stoplist
    words = [t for t in tokens if t not in stopwords and len(t) > 2]
    common = Counter(words).most_common(top_n)
    top = [w for w,_ in common]
    user_msgs = sum(1 for e in hist_state if e.get('user'))
    assistant_msgs = sum(1 for e in hist_state if e.get('assistant'))
    last_msgs = hist_state[-5:]
    last_lines = []
    for e in last_msgs:
        if e.get('user'):
            last_lines.append(f"U: {e.get('user')[:120]}")
        if e.get('assistant'):
            last_lines.append(f"A: {e.get('assistant')[:120]}")
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
            with open(SUGGESTIONS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return []


def auto_improve_daemon():
    last_mtime = 0
    while True:
        enabled = False
        interval = 60
        try:
            if os.path.exists(AUTO_IMPROVE_CONFIG_PATH):
                with open(AUTO_IMPROVE_CONFIG_PATH, "r", encoding="utf-8") as f:
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
    with gr.Row():
        gr.Markdown("# Aria — Gradio Demo  \nEnhanced greeting and chat demo with persistence, export, search, sessions, streaming, and TTS.")
        theme_toggle = gr.Checkbox(label="Dark mode", value=False)
        compact_toggle = gr.Checkbox(label="Compact layout", value=False)

    # Greeting controls
    with gr.Row():
        name = gr.Textbox(label="Name", placeholder="Your name here", elem_id="nameInput")
        language = gr.Dropdown(
            choices=["English", "Spanish", "French", "German"],
            value="English",
            label="Language",
            elem_id="languageSelect",
        )

    with gr.Row():
        style = gr.Radio(
            choices=["Friendly", "Formal", "Enthusiastic"],
            value="Friendly",
            label="Style",
            elem_id="styleSelect",
        )
        excitement = gr.Slider(minimum=1, maximum=10, value=1, step=1, label="Exclamation count", elem_id="excitementSlider")

    greet_btn = gr.Button("Greet", variant="primary")
    output = gr.Textbox(label="Greeting", interactive=False, lines=2, elem_id="greetingOutput")
    examples = gr.Examples(
        examples=[["Alice", "English", "Friendly", 1], ["Carlos", "Spanish", "Friendly", 2], ["Marie", "French", "Enthusiastic", 4]],
        inputs=[name, language, style, excitement],
    )
    greet_btn.click(lambda n, s, e, l: make_greeting(n, s, e, l), inputs=[name, style, excitement, language], outputs=output)

    # Chat area
    initial_display, initial_hist_state = load_latest_conversation()

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(value=initial_display, label="Conversation", elem_id="ariaChatbot")
            user_input = gr.Textbox(placeholder="Type a message and press Enter or Send", label="Your message", elem_id="userInput")

            # Controls
            use_model = gr.Checkbox(label="Use simulation (override provider)", value=False)
            provider_select = gr.Dropdown(choices=["auto", "local", "ollama", "lmstudio", "openai", "azure", "lora", "agi", "quantum"], value="auto", label="Provider", elem_id="providerSelect")
            model_override = gr.Textbox(label="Model override (optional)", placeholder="e.g., llama3.2 or gpt-4o-mini", elem_id="modelOverride")
            temperature = gr.Slider(minimum=0.0, maximum=1.0, value=0.7, step=0.05, label="Temperature", elem_id="temperature")
            max_output_tokens = gr.Slider(minimum=16, maximum=2048, step=16, value=512, label="Max output tokens", elem_id="maxTokens")
            persona = gr.Textbox(label="Assistant name", value="Aria")
            persona_presets = gr.Dropdown(choices=["Aria (Friendly)", "Researcher", "Code Assistant"], value="Aria (Friendly)", label="Persona presets")
            autosave = gr.Checkbox(label="Autosave conversation", value=True)
            max_history = gr.Slider(minimum=10, maximum=1000, step=10, value=200, label="Max history (messages)")
            session_name = gr.Textbox(label="Session name (optional)", placeholder="session-2026-05-16")

            # Status / provider info
            provider_info = gr.Textbox(label="Detected provider", interactive=False)
            status = gr.Textbox(label="Status", interactive=False, value="Idle")

            with gr.Row():
                send_btn = gr.Button("Send")
                cancel_btn = gr.Button("Cancel")
                clear_btn = gr.Button("Clear")
                save_btn = gr.Button("Save now")

            with gr.Row():
                export_json_btn = gr.Button("Export JSON")
                export_jsonl_btn = gr.Button("Export JSONL")
                export_md_btn = gr.Button("Export Markdown")
                export_txt_btn = gr.Button("Export TXT")
                load_latest_btn = gr.Button("Load latest")

            export_file = gr.File(label="Conversation file", interactive=False)

            # Saved sessions manager
            saved_sessions = gr.Dropdown(choices=[], label="Saved sessions", elem_id="savedSessions")
            with gr.Row():
                refresh_sessions_btn = gr.Button("Refresh sessions")
                load_session_btn = gr.Button("Load session")
                delete_session_btn = gr.Button("Delete session")
            # Message edit/delete UI
            with gr.Row():
                message_index = gr.Number(value=0, label="Conversation index (0-based)")
                edit_side = gr.Dropdown(choices=["user", "assistant"], value="assistant", label="Edit side")
                edit_message_text = gr.Textbox(label="New message content", placeholder="Replace text")
            with gr.Row():
                edit_message_btn = gr.Button("Edit message")
                delete_message_btn = gr.Button("Delete message")
            # End message edit/delete UI
            with gr.Row():
                refresh_sessions_btn = gr.Button("Refresh sessions")
                load_session_btn = gr.Button("Load session")
                delete_session_btn = gr.Button("Delete session")

            search_input = gr.Textbox(label="Search conversation", placeholder="Enter text to search")
            with gr.Row():
                search_btn = gr.Button("Search")
                revert_btn = gr.Button("Show all")

            # TTS
            with gr.Row():
                tts_autoplay = gr.Checkbox(label="Autoplay assistant audio", value=False)
                tts_backend = gr.Dropdown(choices=["auto", "pyttsx3", "gtts"], value="auto", label="TTS backend")
                speak_btn = gr.Button("Speak last reply")
            tts_audio = gr.Audio(label="Assistant audio", interactive=False)

            with gr.Row():
                auto_improve_enable = gr.Checkbox(label="Auto-improve (background)", value=False)
                auto_improve_interval = gr.Slider(minimum=5, maximum=3600, step=5, value=60, label="Auto-improve interval (sec)")
                suggestions_dropdown = gr.Dropdown(choices=[], label="Auto suggestions", elem_id="suggestionsDropdown")
                refresh_suggestions_btn = gr.Button("Refresh suggestions")
                apply_suggestion_btn = gr.Button("Apply suggestion")
                delete_suggestion_btn = gr.Button("Delete suggestion")

        # Hidden state that stores structured conversation (list of dicts)
        hist_state = gr.State(initial_hist_state)

        suggestions_state = gr.State([])

        # ------------------------------------------------------------------
        # Actions / Callbacks
        # ------------------------------------------------------------------
        def respond(user_message, chat_history, hist_state, use_model, provider_choice, model_override_val, temperature_val, max_output_tokens_val, lang, persona_val, autosave, max_history, session_name):
            """Respond and stream updates. Returns (chat_history, cleared_input, hist_state, provider_info, status)."""
            chat_history = chat_history or []
            hist_state = hist_state or []
            if not user_message or not str(user_message).strip():
                return chat_history, "", hist_state, "", "Idle"

            user_message = str(user_message).strip()
            user_ts = timestamp_now()
            # reset cancel flag for this request
            global CANCEL_STREAM
            CANCEL_STREAM = False

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
                chat_history = chat_history + [(display_user, display_assistant)]
                hist_state = hist_state + [{"user": user_message, "assistant": reply, "user_ts": user_ts, "assistant_ts": assistant_ts}]
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
                return chat_history, "", hist_state, provider_display, "Idle"

            # Try using repo providers if available
            try:
                import sys
                from pathlib import Path
                chat_cli_src = Path(__file__).resolve().parents[1] / "ai-projects" / "chat-cli" / "src"
                if str(chat_cli_src) not in sys.path:
                    sys.path.insert(0, str(chat_cli_src))
                import chat_providers

                provider, info = chat_providers.detect_provider(
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
                chat_history = chat_history + [(display_user, display_assistant)]
                hist_state = hist_state + [{"user": user_message, "assistant": reply, "user_ts": user_ts, "assistant_ts": assistant_ts}]
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
                return chat_history, "", hist_state, provider_display, "Idle"

            # Initial UI placeholder and streaming status
            display_user = f"{user_message}\n\n[{user_ts}]"
            display_assistant = f"...\n\n[{timestamp_now()}]"
            chat_history = chat_history + [(display_user, display_assistant)]

            # Yield initial state (client will show 'Streaming...')
            yield chat_history, "", hist_state, provider_display, "Streaming..."

            partial = ""
            try:
                stream_resp = provider.complete(messages, stream=True)
                if hasattr(stream_resp, "__iter__") and not isinstance(stream_resp, str):
                    for chunk in stream_resp:
                        # allow external cancel
                        if CANCEL_STREAM:
                            partial += "\n\n[Cancelled]"
                            display_assistant = f"{partial}\n\n[{timestamp_now()}]"
                            chat_history[-1] = (display_user, display_assistant)
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
                            yield chat_history, "", hist_state, provider_display, "Cancelled"
                            break
                        chunk_text = str(chunk) if chunk is not None else ""
                        partial += chunk_text
                        display_assistant = f"{partial}\n\n[{timestamp_now()}]"
                        chat_history[-1] = (display_user, display_assistant)
                        yield chat_history, "", hist_state, provider_display, "Streaming..."
                else:
                    partial = str(stream_resp)
            except Exception as e:
                err = f"[Provider error: {str(e)}]"
                display_assistant = f"{err}\n\n[{timestamp_now()}]"
                chat_history[-1] = (display_user, display_assistant)
                hist_state = hist_state + [{"user": user_message, "assistant": err, "user_ts": user_ts, "assistant_ts": timestamp_now()}]
                if autosave:
                    try:
                        save_conversation_json(hist_state, session_name or "session")
                    except Exception:
                        pass
                yield chat_history, "", hist_state, provider_display, "Idle"
                return

            # Finalize
            assistant_ts = timestamp_now()
            reply = partial
            display_assistant = f"{reply}\n\n[{assistant_ts}]"
            chat_history[-1] = (display_user, display_assistant)
            hist_state = hist_state + [{"user": user_message, "assistant": reply, "user_ts": user_ts, "assistant_ts": assistant_ts}]
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
            yield chat_history, "", hist_state, provider_display, "Idle"
            return

        # Wire send button and Enter key (submit)
        send_btn.click(
            respond,
            inputs=[user_input, chatbot, hist_state, use_model, provider_select, model_override, temperature, max_output_tokens, language, persona, autosave, max_history, session_name],
            outputs=[chatbot, user_input, hist_state, provider_info, status],
            queue=True,
        )
        user_input.submit(
            respond,
            inputs=[user_input, chatbot, hist_state, use_model, provider_select, model_override, temperature, max_output_tokens, language, persona, autosave, max_history, session_name],
            outputs=[chatbot, user_input, hist_state, provider_info, status],
            queue=True,
        )

        def cancel_stream():
            global CANCEL_STREAM
            CANCEL_STREAM = True
            return "Cancelled"

        cancel_btn.click(cancel_stream, outputs=[status])

        def apply_persona(preset, persona_field):
            if not preset:
                return persona_field
            if preset.startswith("Aria"):
                return "Aria"
            if preset == "Researcher":
                return "Dr. Aria"
            if preset == "Code Assistant":
                return "Aria-Dev"
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

        def export_txt(hist_state, session_name):
            if not hist_state:
                return None
            ensure_conv_dir()
            ts = int(time.time())
            safe_name = (session_name or "session").strip().replace(" ", "_")
            filename = os.path.join(CONV_DIR, f"{safe_name}_{ts}.txt")
            temp = filename + ".tmp"
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
            safe_name = (session_name or "session").strip().replace(" ", "_")
            filename = os.path.join(CONV_DIR, f"{safe_name}_{ts}.jsonl")
            temp = filename + ".tmp"
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
                    from pathlib import Path
                    import importlib.util
                    p = Path(__file__).resolve().parent / "gradio_webhook.py"
                    if not p.exists():
                        raise
                    spec = importlib.util.spec_from_file_location("gradio_webhook", str(p))
                    gradio_webhook = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(gradio_webhook)
                target = webhook_dir if webhook_dir else None
                path = gradio_webhook.post_conversation_to_webhook(hist_state, webhook_name=webhook_name, webhook_dir=target)
                if autocommit:
                    try:
                        _git_commit_file(path)
                    except Exception:
                        pass
                return path, "Sent"
            except Exception as e:
                return None, f"Error: {str(e)}"

        send_to_webhook_btn.click(send_to_webhook, inputs=[hist_state, webhook_name, webhook_dir, webhook_autocommit], outputs=[export_file, status])

        def list_sessions():
            ensure_conv_dir()
            files = []
            for fname in sorted(os.listdir(CONV_DIR)):
                if fname.endswith((".json", ".md", ".txt")):
                    files.append(fname)
            return gr.Dropdown.update(choices=files, value=files[0] if files else None)

        refresh_sessions_btn.click(list_sessions, outputs=[saved_sessions])

        def load_session(filename):
            if not filename:
                return [], []
            path = os.path.join(CONV_DIR, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                display = hist_state_to_display(data)
                return display, data
            except Exception:
                return [], []

        load_session_btn.click(load_session, inputs=[saved_sessions], outputs=[chatbot, hist_state])

        def delete_session(filename):
            if not filename:
                return gr.Dropdown.update()
            path = os.path.join(CONV_DIR, filename)
            try:
                os.remove(path)
            except Exception:
                pass
            files = []
            for fname in sorted(os.listdir(CONV_DIR)):
                if fname.endswith((".json", ".md", ".txt")):
                    files.append(fname)
            return gr.Dropdown.update(choices=files, value=files[0] if files else None)

        delete_session_btn.click(delete_session, inputs=[saved_sessions], outputs=[saved_sessions])

        def edit_message(index, side, new_text, hist_state, autosave, session_name):
            try:
                i = int(index)
            except Exception:
                return hist_state_to_display(hist_state), hist_state
            if not hist_state or i < 0 or i >= len(hist_state):
                return hist_state_to_display(hist_state), hist_state
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
            return hist_state_to_display(hist_state), hist_state

        def delete_message_by_index(index, hist_state, autosave, session_name):
            try:
                i = int(index)
            except Exception:
                return hist_state_to_display(hist_state), hist_state
            if not hist_state or i < 0 or i >= len(hist_state):
                return hist_state_to_display(hist_state), hist_state
            hist_state = list(hist_state)
            hist_state.pop(i)
            if autosave:
                try:
                    save_conversation_json(hist_state, session_name or "session")
                except Exception:
                    pass
            return hist_state_to_display(hist_state), hist_state

        edit_message_btn.click(edit_message, inputs=[message_index, edit_side, edit_message_text, hist_state, autosave, session_name], outputs=[chatbot, hist_state])
        delete_message_btn.click(delete_message_by_index, inputs=[message_index, hist_state, autosave, session_name], outputs=[chatbot, hist_state])

        def load_latest_click():
            display, hist = load_latest_conversation()
            return display, hist

        load_latest_btn.click(load_latest_click, outputs=[chatbot, hist_state])

        def generate_tts_for_text(text: str, backend: Optional[str] = None) -> Optional[str]:
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
                        mp3_path = wav_path.replace('.wav', '.mp3')
                        tts = gTTS(text)
                        tts.save(mp3_path)
                        return mp3_path
                    except Exception:
                        return None
                # backend selection
                if backend == "pyttsx3":
                    return try_pyttsx3()
                if backend == "gtts":
                    return try_gtts()
                # auto: prefer pyttsx3 then gTTS
                res = try_pyttsx3()
                if res:
                    return res
                return try_gtts()
            except Exception:
                return None

        def speak_last(hist_state, autoplay, tts_backend):
            if not hist_state:
                return None
            last = hist_state[-1]
            assistant_text = last.get('assistant', '')
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
                    filtered.append((f"{u}\n\n[{ut}]", f"{a}\n\n[{at}]"))
            return filtered

        search_btn.click(search_chat, inputs=[search_input, hist_state], outputs=[chatbot])

        def revert_search(hist_state):
            return hist_state_to_display(hist_state)

        revert_btn.click(revert_search, inputs=[hist_state], outputs=[chatbot])

        def refresh_suggestions():
            items = load_suggestions()
            choices = []
            for it in items:
                stext = it.get('suggestion', '').replace('\n', ' ')
                choices.append(f"{it.get('ts','')} - {stext[:140]}")
            return gr.Dropdown.update(choices=choices, value=choices[0] if choices else None)

        def apply_suggestion(choice, hist_state, session_name, autosave):
            if not choice:
                return hist_state_to_display(hist_state), hist_state
            items = load_suggestions()
            stext = None
            for it in items:
                s_preview = it.get('suggestion', '').replace('\n',' ')[:140]
                label = f"{it.get('ts','')} - {s_preview}"
                if label == choice or choice in it.get('suggestion', ''):
                    stext = it.get('suggestion')
                    break
            if not stext:
                return hist_state_to_display(hist_state), hist_state
            assistant_ts = timestamp_now()
            hist_state = hist_state + [{"user": "", "assistant": stext, "user_ts": "", "assistant_ts": assistant_ts}]
            if autosave:
                try:
                    save_conversation_json(hist_state, session_name or "session")
                except Exception:
                    pass
            return hist_state_to_display(hist_state), hist_state

        def delete_suggestion(choice):
            items = load_suggestions()
            if not choice:
                choices = [f"{it.get('ts','')} - {it.get('suggestion','')[:140].replace('\n',' ')}" for it in items]
                return gr.Dropdown.update(choices=choices, value=choices[0] if choices else None)
            new_items = []
            for it in items:
                label = f"{it.get('ts','')} - {it.get('suggestion','')[:140].replace('\n',' ')}"
                if label != choice:
                    new_items.append(it)
            save_suggestions(new_items)
            choices = [f"{it.get('ts','')} - {it.get('suggestion','')[:140].replace('\n',' ')}" for it in new_items]
            return gr.Dropdown.update(choices=choices, value=choices[0] if choices else None)

        # Wire suggestion controls
        refresh_suggestions_btn.click(refresh_suggestions, outputs=[suggestions_dropdown])
        apply_suggestion_btn.click(apply_suggestion, inputs=[suggestions_dropdown, hist_state, session_name, autosave], outputs=[chatbot, hist_state])
        delete_suggestion_btn.click(delete_suggestion, inputs=[suggestions_dropdown], outputs=[suggestions_dropdown])

        def apply_theme(is_dark: bool, is_compact: bool):
            base = DARK_CSS if is_dark else LIGHT_CSS
            value = base + (COMPACT_CSS if is_compact else "")
            return gr.HTML.update(value=value)

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
