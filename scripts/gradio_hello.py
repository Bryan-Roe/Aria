"""Enhanced Gradio demo for Aria.

Run after installing dependencies:
    ./.venv/bin/python scripts/gradio_hello.py

Then open the local URL printed by Gradio.
"""

import gradio as gr


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
    gr.Markdown("# Aria — Gradio Demo\nEnhanced greeting demo with styles, languages, and examples.")

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
        excitement = gr.Slider(
            minimum=1,
            maximum=10,
            value=1,
            step=1,
            label="Exclamation count",
            elem_id="excitementSlider",
        )

    greet_btn = gr.Button("Greet", variant="primary")
    output = gr.Textbox(label="Greeting", interactive=False, lines=2, elem_id="greetingOutput")

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

    greet_btn.click(on_greet, inputs=[name, language, style, excitement], outputs=output)


if __name__ == "__main__":
    demo.launch()
