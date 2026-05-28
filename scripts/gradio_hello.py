"""Enhanced Gradio demo for Aria.

Run after installing dependencies:
    ./.venv/bin/python scripts/gradio_hello.py

Then open the local URL printed by Gradio.
"""

from typing import List, Tuple, Dict, Any
from datetime import datetime
import time
import json
import os
import gradio as gr  # type: ignore[import-not-found]

try:
    import pyttsx3  # type: ignore[import-not-found]
except ImportError:
    pyttsx3 = None  # type: ignore[assignment]

try:
    from gtts import gTTS  # type: ignore[import-not-found]
except ImportError:
    gTTS = None  # type: ignore[assignment]


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


with gr.Blocks() as demo:
    gr.Markdown(
        "# Aria — Gradio Demo\nEnhanced greeting demo with styles, languages, and examples.")

    with gr.Row():
        name = gr.Textbox(
            label="Name", placeholder="Your name here", elem_id="nameInput")
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
        excitement = gr.Slider(
            minimum=1,
            maximum=10,
            value=1,
            step=1,
            label="Exclamation count",
            elem_id="excitementSlider",
        )

    greet_btn = gr.Button("Greet", variant="primary")
    output = gr.Textbox(label="Greeting", interactive=False,
                        lines=2, elem_id="greetingOutput")

    examples = gr.Examples(
        examples=[
            ["Alice", "English", "Friendly", 1],
            ["Carlos", "Spanish", "Friendly", 2],
            ["Marie", "French", "Enthusiastic", 4],
        ],
        inputs=[name, language, style, excitement],
    )

    def on_greet(n: str, lang: str, s: str, e: int) -> str:
        return make_greeting(n, s, e, lang)

"""Enhanced Gradio demo for Aria.

Run after installing dependencies:
    ./.venv/bin/python scripts/gradio_hello.py

Then open the local URL printed by Gradio.
"""


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


def save_conversation_json(hist_state: List[dict], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = (session_name or "session").strip().replace(" ", "_")
    filename = os.path.join(CONV_DIR, f"{safe_name}_{ts}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(hist_state, f, ensure_ascii=False, indent=2)
    # update latest
    with open(LATEST_PATH, "w", encoding="utf-8") as f:
        json.dump(hist_state, f, ensure_ascii=False, indent=2)
    return filename


def save_conversation_markdown(hist_state: List[dict], session_name: str = "session") -> str:
    ensure_conv_dir()
    ts = int(time.time())
    safe_name = (session_name or "session").strip().replace(" ", "_")
    filename = os.path.join(CONV_DIR, f"{safe_name}_{ts}.md")
    with open(filename, "w", encoding="utf-8") as f:
        for entry in hist_state:
            u = entry.get("user", "")
            a = entry.get("assistant", "")
            ut = entry.get("user_ts", "")
            at = entry.get("assistant_ts", "")
            f.write(f"### User — {ut}\n")
            f.write(u + "\n\n")
            f.write(f"### Assistant — {at}\n")
            f.write(a + "\n\n---\n\n")
    return filename


def load_latest_conversation() -> Tuple[List[Tuple[str, str]], List[dict]]:
    if not os.path.exists(LATEST_PATH):
        return [], []
    try:
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
        (f"{e.get('user', '')}\n\n[{e.get('user_ts', '')}]",
         f"{e.get('assistant', '')}\n\n[{e.get('assistant_ts', '')}]")
        for e in hist_state
    ]


with gr.Blocks() as demo:
    gr.Markdown(
        "# Aria — Gradio Demo\nEnhanced greeting and chat demo with persistence, export, search, and session controls.")

    # Greeting controls (kept simple)
    with gr.Row():
        name = gr.Textbox(
            label="Name", placeholder="Your name here", elem_id="nameInput")
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
        excitement = gr.Slider(
            minimum=1,
            maximum=10,
            value=1,
            step=1,
            label="Exclamation count",
            elem_id="excitementSlider",
        )

    greet_btn = gr.Button("Greet", variant="primary")
    output = gr.Textbox(label="Greeting", interactive=False,
                        lines=2, elem_id="greetingOutput")

    examples = gr.Examples(
        examples=[
            ["Alice", "English", "Friendly", 1],
            ["Carlos", "Spanish", "Friendly", 2],
            ["Marie", "French", "Enthusiastic", 4],
        ],
        inputs=[name, language, style, excitement],
    )

    def on_greet(n: str, lang: str, s: str, e: int) -> str:
        return make_greeting(n, s, e, lang)

    greet_btn.click(on_greet, inputs=[
                    name, language, style, excitement], outputs=output)

    # ------------------------------------------------------------------
    # Chat-style demo with persistence and utilities
    # ------------------------------------------------------------------
    gr.Markdown("## Chat-style demo")

    # Load latest conversation (if any) as initial state
    initial_display, initial_hist_state = load_latest_conversation()

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(value=initial_display,
                                 label="Conversation", elem_id="ariaChatbot")

            user_input = gr.Textbox(
                placeholder="Type a message", label="Your message", elem_id="userInput")

            # Controls
            use_model = gr.Checkbox(
                label="Use simulation (override provider)", value=False)
            provider_select = gr.Dropdown(
                choices=["auto", "local", "ollama", "lmstudio",
                         "openai", "azure", "lora", "agi", "quantum"],
                value="auto",
                label="Provider",
                elem_id="providerSelect",
            )
            model_override = gr.Textbox(label="Model override (optional)",
                                        placeholder="e.g., llama3.2 or gpt-4o-mini", elem_id="modelOverride")
            temperature = gr.Slider(minimum=0.0, maximum=1.0, value=0.7,
                                    step=0.05, label="Temperature", elem_id="temperature")
            max_output_tokens = gr.Slider(
                minimum=16, maximum=2048, step=16, value=512, label="Max output tokens", elem_id="maxTokens")
            persona = gr.Textbox(label="Assistant name", value="Aria")
            persona_presets = gr.Dropdown(choices=[
                                          "Aria (Friendly)", "Researcher", "Code Assistant"], value="Aria (Friendly)", label="Persona presets")
            autosave = gr.Checkbox(label="Autosave conversation", value=True)
            max_history = gr.Slider(
                minimum=10, maximum=500, step=10, value=200, label="Max history (messages)")
            session_name = gr.Textbox(
                label="Session name (optional)", placeholder="session-2026-05-16")
            provider_info = gr.Textbox(
                label="Detected provider", interactive=False)

            with gr.Row():
                send_btn = gr.Button("Send")
                clear_btn = gr.Button("Clear")
                save_btn = gr.Button("Save now")

            with gr.Row():
                export_json_btn = gr.Button("Export JSON")
                export_md_btn = gr.Button("Export Markdown")
                export_txt_btn = gr.Button("Export TXT")
                load_latest_btn = gr.Button("Load latest")

            export_file = gr.File(label="Conversation file", interactive=False)

            # Saved sessions manager
            saved_sessions = gr.Dropdown(
                choices=[], label="Saved sessions", elem_id="savedSessions")
            with gr.Row():
                refresh_sessions_btn = gr.Button("Refresh sessions")
                load_session_btn = gr.Button("Load session")
                delete_session_btn = gr.Button("Delete session")

            search_input = gr.Textbox(
                label="Search conversation", placeholder="Enter text to search")
            with gr.Row():
                search_btn = gr.Button("Search")
                revert_btn = gr.Button("Show all")

            # Text-to-Speech
            with gr.Row():
                tts_autoplay = gr.Checkbox(
                    label="Autoplay assistant audio", value=False)
                speak_btn = gr.Button("Speak last reply")
            tts_audio = gr.Audio(label="Assistant audio", interactive=False)

        # Hidden state that stores structured conversation (list of dicts)
        hist_state = gr.State(initial_hist_state)

        # ------------------------------------------------------------------
        # Actions / Callbacks
        # ------------------------------------------------------------------
        def respond(user_message, chat_history, hist_state, use_model, provider_choice, model_override_val, temperature_val, max_output_tokens_val, lang, persona, autosave, max_history, session_name):
            """Generator-style responder: streams tokens when the provider supports streaming.

            Yields tuples mapping to outputs: (chatbot, user_input, hist_state, provider_info)
            """
            chat_history = chat_history or []
            hist_state = hist_state or []
            if not user_message or not str(user_message).strip():
                return chat_history, "", hist_state, ""

            user_message = str(user_message).strip()
            user_ts = timestamp_now()

            # Build messages for provider
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

            if use_model:
                # Quick simulated response
                reply = f"[{persona}-{lang}] " + user_message[::-1]
                provider_display = "simulation"

                assistant_ts = timestamp_now()
                display_user = f"{user_message}\n\n[{user_ts}]"
                display_assistant = f"{reply}\n\n[{assistant_ts}]"

                chat_history = list(chat_history) + \
                    [(display_user, display_assistant)]
                hist_state = list(hist_state) + [
                    {"user": user_message, "assistant": reply,
                        "user_ts": user_ts, "assistant_ts": assistant_ts}
                ]

                if autosave:
                    try:
                        save_conversation_json(
                            hist_state, session_name or "session")
                    except Exception:
                        pass

                yield chat_history, "", hist_state, provider_display
                return

            # Attempt to create provider
            try:
                import sys
                from pathlib import Path
                chat_cli_src = Path(__file__).resolve(
                ).parents[1] / "ai-projects" / "chat-cli" / "src"
                if str(chat_cli_src) not in sys.path:
                    sys.path.insert(0, str(chat_cli_src))
                import chat_providers

                provider, info = chat_providers.detect_provider(
                    explicit=str(provider_choice) if provider_choice else None,
                    model_override=str(
                        model_override_val) if model_override_val else None,
                    temperature=float(
                        temperature_val) if temperature_val is not None else None,
                    max_output_tokens=int(
                        max_output_tokens_val) if max_output_tokens_val else None,
                )
                provider_display = f"{info.name} ({info.model})"
            except Exception as e:
                # Fallback to echo if provider detection/import failed
                provider_display = f"fallback (error)"
                reply = f"Echo ({lang}): {user_message}"

                assistant_ts = timestamp_now()
                display_user = f"{user_message}\n\n[{user_ts}]"
                display_assistant = f"{reply}\n\n[{assistant_ts}]"
                chat_history = list(chat_history) + \
                    [(display_user, display_assistant)]
                hist_state = list(hist_state) + [
                    {"user": user_message, "assistant": reply,
                        "user_ts": user_ts, "assistant_ts": assistant_ts}
                ]
                if autosave:
                    try:
                        save_conversation_json(
                            hist_state, session_name or "session")
                    except Exception:
                        pass

                yield chat_history, "", hist_state, provider_display
                return

            # Prepare initial placeholder in UI
            display_user = f"{user_message}\n\n[{user_ts}]"
            display_assistant = f"...\n\n[{timestamp_now()}]"
            chat_history = list(chat_history) + \
                [(display_user, display_assistant)]

            # Yield initial UI state with placeholder
            yield chat_history, "", hist_state, provider_display

            # Stream tokens if provider supports it
            partial = ""
            try:
                stream_resp = provider.complete(messages, stream=True)
                if hasattr(stream_resp, "__iter__") and not isinstance(stream_resp, str):
                    for chunk in stream_resp:
                        try:
                            chunk_text = str(chunk)
                        except Exception:
                            chunk_text = ""
                        partial += chunk_text
                        # Update assistant display with partial text
                        display_assistant = f"{partial}\n\n[{timestamp_now()}]"
                        chat_history[-1] = (display_user, display_assistant)
                        yield chat_history, "", hist_state, provider_display
                else:
                    # Provider returned non-iterable despite stream=True; treat as final text
                    partial = str(stream_resp)
            except Exception as e:
                # Provider streaming failed; show error in UI
                err = f"[Provider error: {str(e)}]"
                display_assistant = f"{err}\n\n[{timestamp_now()}]"
                chat_history[-1] = (display_user, display_assistant)
                yield chat_history, "", hist_state, provider_display

                # Append final entry to hist_state and return
                hist_state = list(hist_state) + [
                    {"user": user_message, "assistant": err,
                        "user_ts": user_ts, "assistant_ts": timestamp_now()}
                ]
                if autosave:
                    try:
                        save_conversation_json(
                            hist_state, session_name or "session")
                    except Exception:
                        pass
                yield chat_history, "", hist_state, provider_display
                return

            # Finalize response
            assistant_ts = timestamp_now()
            reply = partial
            display_assistant = f"{reply}\n\n[{assistant_ts}]"
            chat_history[-1] = (display_user, display_assistant)
            hist_state = list(hist_state) + [
                {"user": user_message, "assistant": reply,
                    "user_ts": user_ts, "assistant_ts": assistant_ts}
            ]
            if autosave:
                try:
                    save_conversation_json(
                        hist_state, session_name or "session")
                except Exception:
                    pass

            yield chat_history, "", hist_state, provider_display
            return

        send_btn.click(
            respond,
            inputs=[user_input, chatbot, hist_state, use_model, provider_select, model_override,
                    temperature, max_output_tokens, language, persona, autosave, max_history, session_name],
            outputs=[chatbot, user_input, hist_state, provider_info],
            queue=True,
        )

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

        persona_presets.change(apply_persona, inputs=[
                               persona_presets, persona], outputs=[persona])

        def clear_history():
            return [], []

        clear_btn.click(clear_history, outputs=[chatbot, hist_state])

        def save_now(hist_state, session_name):
            if not hist_state:
                return None
            path = save_conversation_json(
                hist_state, session_name or "session")
            return path

        save_btn.click(save_now, inputs=[
                       hist_state, session_name], outputs=[export_file])

        def export_json(hist_state, session_name):
            if not hist_state:
                return None
            return save_conversation_json(hist_state, session_name or "session")

        def export_md(hist_state, session_name):
            if not hist_state:
                return None
            return save_conversation_markdown(hist_state, session_name or "session")

        export_json_btn.click(export_json, inputs=[
                              hist_state, session_name], outputs=[export_file])
        export_md_btn.click(export_md, inputs=[
                            hist_state, session_name], outputs=[export_file])

        def export_txt(hist_state, session_name):
            if not hist_state:
                return None
            # Write simple plain-text transcript
            ensure_conv_dir()
            ts = int(time.time())
            safe_name = (session_name or "session").strip().replace(" ", "_")
            filename = os.path.join(CONV_DIR, f"{safe_name}_{ts}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                for e in hist_state:
                    ut = e.get("user_ts", "")
                    at = e.get("assistant_ts", "")
                    f.write(f"User [{ut}]:\n")
                    f.write(e.get("user", "") + "\n\n")
                    f.write(f"Assistant [{at}]:\n")
                    f.write(e.get("assistant", "") + "\n\n---\n\n")
            return filename

        export_txt_btn.click(export_txt, inputs=[
                             hist_state, session_name], outputs=[export_file])

        def list_sessions():
            ensure_conv_dir()
            files = []
            for fname in sorted(os.listdir(CONV_DIR)):
                if fname.endswith(('.json', '.md', '.txt')):
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

        load_session_btn.click(load_session, inputs=[
                               saved_sessions], outputs=[chatbot, hist_state])

        def delete_session(filename):
            if not filename:
                return gr.Dropdown.update()
            path = os.path.join(CONV_DIR, filename)
            try:
                os.remove(path)
            except Exception:
                pass
            # Return updated dropdown choices
            files = []
            for fname in sorted(os.listdir(CONV_DIR)):
                if fname.endswith(('.json', '.md', '.txt')):
                    files.append(fname)
            return gr.Dropdown.update(choices=files, value=files[0] if files else None)

        delete_session_btn.click(delete_session, inputs=[
                                 saved_sessions], outputs=[saved_sessions])

        def load_latest_click():
            display, hist = load_latest_conversation()
            return display, hist

        load_latest_btn.click(load_latest_click, outputs=[chatbot, hist_state])

        def generate_tts_for_text(text: str) -> str | None:
            """Generate TTS audio file for given text. Returns path or None on failure."""
            if not text or not str(text).strip():
                return None
            try:
                ensure_conv_dir()
                tts_dir = os.path.join(CONV_DIR, "tts")
                os.makedirs(tts_dir, exist_ok=True)
                ts = int(time.time())
                wav_path = os.path.join(tts_dir, f"tts_{ts}.wav")
                # Try pyttsx3 first
                if pyttsx3:
                    try:
                        engine = pyttsx3.init()
                        engine.save_to_file(text, wav_path)
                        engine.runAndWait()
                        return wav_path
                    except Exception:
                        pass
                # Fallback to gTTS (may require network)
                if gTTS:
                    try:
                        mp3_path = wav_path.replace('.wav', '.mp3')
                        tts = gTTS(text)
                        tts.save(mp3_path)
                        return mp3_path
                    except Exception:
                        return None
                return None
            except Exception:
                return None

        def speak_last(hist_state, autoplay):
            # Pick last assistant entry
            if not hist_state:
                return None
            last = hist_state[-1]
            assistant_text = last.get('assistant', '')
            path = generate_tts_for_text(assistant_text)
            # If autoplay is requested, returning audio file will make Gradio render audio player
            return path

        speak_btn.click(speak_last, inputs=[
                        hist_state, tts_autoplay], outputs=[tts_audio])

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

        search_btn.click(search_chat, inputs=[
                         search_input, hist_state], outputs=[chatbot])

        def revert_search(hist_state):
            return hist_state_to_display(hist_state)

        revert_btn.click(revert_search, inputs=[hist_state], outputs=[chatbot])


if __name__ == "__main__":
    demo.launch()
