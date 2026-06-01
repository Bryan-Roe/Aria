"""Enhanced Gradio app for Aria.

Run:
    ./.venv/bin/python scripts/gradio_hello.py

Then open the local URL printed by Gradio.
"""

from __future__ import annotations

from datetime import datetime
import importlib
from pathlib import Path
from typing import Any
import json
import sys
import time

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
    --bg: #f3f7f2;
    --panel: #fdfefc;
    --ink: #1f2d1f;
    --brand: #14532d;
    --brand-2: #4d7c0f;
    --accent: #b45309;
    --muted: #e8efdf;
}
.gradio-container {
    background: radial-gradient(1300px 540px at 100% -20%, #d9f2cc, transparent),
                            radial-gradient(1000px 480px at -10% -20%, #fef2d3, transparent),
              var(--bg);
}
#appCard {
  background: var(--panel);
    border: 1px solid #d9e4cf;
    border-radius: 18px;
    padding: 14px;
    box-shadow: 0 14px 45px rgba(31, 45, 31, 0.1);
}
#brandTitle h1 {
  color: var(--ink);
    letter-spacing: 0.3px;
    font-weight: 750;
}
#helperText p {
    color: #445a34;
}
.simple-note {
    color: #4b663f;
    font-size: 0.9rem;
    margin-top: 2px;
}
#surfaceBlock {
    border: 1px solid #dde8d1;
    border-radius: 14px;
    background: linear-gradient(180deg, #ffffff, #f7fbf3);
    padding: 10px;
}
#surfaceBlock h2 {
    margin-top: 6px;
}
#chatPanel {
    border: 1px solid #e3ecd8;
    border-radius: 12px;
    background: #fbfdf8;
    padding: 8px;
}
#sidebarPanel {
    border: 1px solid #e2e9d8;
    border-radius: 12px;
    background: linear-gradient(180deg, #fcfefb, #f3f8ed);
    padding: 10px;
}
.quick-hint {
    color: #496238;
    font-size: 0.92rem;
    margin-top: 2px;
}
button.primary {
  background: linear-gradient(135deg, var(--brand), var(--brand-2)) !important;
    border: 0 !important;
    color: #f5fff0 !important;
}
button.secondary {
    border-color: #ceddbf !important;
    color: #244025 !important;
}
button:hover {
    transform: translateY(-1px);
    transition: transform 120ms ease, box-shadow 120ms ease;
    box-shadow: 0 8px 18px rgba(20, 83, 45, 0.12);
}
.gradio-container input:focus,
.gradio-container textarea:focus {
    outline: 2px solid #7ea761 !important;
    outline-offset: 1px;
}
.gradio-chatbot {
    min-height: 360px;
}
#statusRow textarea {
    font-size: 0.92rem !important;
    line-height: 1.2 !important;
}

@media (max-width: 1100px) {
    #appCard {
        padding: 10px;
    }
    #surfaceBlock,
    #sidebarPanel {
        padding: 8px;
    }
    .gradio-chatbot {
        min-height: 300px;
    }
}

@media (max-width: 760px) {
    #brandTitle h1 {
        font-size: 1.45rem;
    }
    #surfaceBlock,
    #sidebarPanel {
        border-radius: 10px;
    }
    .gradio-chatbot {
        min-height: 250px;
    }
    button {
        min-height: 42px;
    }
    #statusRow textarea {
        font-size: 0.86rem !important;
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
    filename = CONV_DIR / f"{safe_name}_{ts}.json"
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
                "content": f"{e.get('user', '')}\n\n[{e.get('user_ts', '')}]",
            }
        )
        display.append(
            {
                "role": "assistant",
                "content": f"{e.get('assistant', '')}\n\n[{e.get('assistant_ts', '')}]",
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
        display_user = f"{user_message}\n\n[{user_ts}]"
        display_assistant = f"{reply}\n\n[{assistant_ts}]"
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
        reply = f"Echo ({lang}): {user_message}"
        assistant_ts = timestamp_now()
        display_user = f"{user_message}\n\n[{user_ts}]"
        display_assistant = f"{reply}\n\n[{assistant_ts}]"
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
        yield chat_history[
            -int(max_history * 2) :
        ], "", hist_state, "fallback", "Provider unavailable, used local echo fallback."
        return

    display_user = f"{user_message}\n\n[{user_ts}]"
    display_assistant = f"...\n\n[{timestamp_now()}]"
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
                chat_history[-1] = {"role": "assistant", "content": f"{partial}\n\n[{timestamp_now()}]"}
                yield chat_history[-int(max_history * 2) :], "", hist_state, provider_display, "Streaming response..."
        else:
            partial = str(stream_resp)
    except Exception as e:
        err = f"[Provider error: {str(e)}]"
        chat_history[-1] = {"role": "assistant", "content": f"{err}\n\n[{timestamp_now()}]"}
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
        yield chat_history[
            -int(max_history * 2) :
        ], "", hist_state, provider_display, "Provider failed; error captured in chat."
        return

    assistant_ts = timestamp_now()
    chat_history[-1] = {"role": "assistant", "content": f"{partial}\n\n[{assistant_ts}]"}
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


initial_display, initial_hist_state = load_latest_conversation()

with gr.Blocks() as demo:
    with gr.Column(elem_id="appCard"):
        gr.Markdown(
            "# Aria - Gradio Chat",
            elem_id="brandTitle",
        )
        gr.Markdown(
            "Simple chat first. Advanced controls are available when needed.",
            elem_id="helperText",
        )

        with gr.Row(equal_height=False):
            with gr.Column(scale=7, elem_id="surfaceBlock"):
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

                gr.Markdown("## Conversation")
                with gr.Column(elem_id="chatPanel"):
                    chatbot = gr.Chatbot(label="Chat")

                user_input = gr.Textbox(placeholder="Type a message and press Enter", label="Your message")
                gr.Markdown("<div class='quick-hint'>Quick prompts: tap one below, then press Enter or Send.</div>")
                gr.Examples(
                    examples=[
                        ["Summarize today's priorities in 5 bullets."],
                        ["Help me draft a short project update."],
                        ["Give me three creative app ideas."],
                    ],
                    inputs=[user_input],
                )

                with gr.Row():
                    send_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear", variant="secondary")
                    save_btn = gr.Button("Save", variant="secondary")

                with gr.Row(elem_id="statusRow"):
                    provider_info = gr.Textbox(label="Detected provider", interactive=False)
                    status_info = gr.Textbox(label="Status", interactive=False)

            with gr.Column(scale=5, elem_id="sidebarPanel"):
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

        demo.load(lambda: (initial_display, initial_hist_state), outputs=[chatbot, hist_state])

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

        clear_btn.click(lambda: ([], [], "Ready."), outputs=[chatbot, hist_state, status_info])

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

        def load_session(filename: str):
            if not filename:
                return [], []
            path = CONV_DIR / filename
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                return [], []
            return hist_state_to_display(data), data

        load_session_btn.click(load_session, inputs=[saved_sessions], outputs=[chatbot, hist_state])

        def delete_session(filename: str):
            if filename:
                try:
                    (CONV_DIR / filename).unlink(missing_ok=True)
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
    demo.launch(css=CSS, theme=THEME)
