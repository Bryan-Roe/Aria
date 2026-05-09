"""Minimal Gradio hello-world demo.

Run after installing dependencies:
    ./.venv/bin/python scripts/gradio_hello.py

Then open the local URL printed by Gradio.
"""

import gradio as gr


def greet(name: str) -> str:
    return "Hello " + name + "!!"


demo = gr.Interface(fn=greet, inputs="text", outputs="text")


if __name__ == "__main__":
    demo.launch()
