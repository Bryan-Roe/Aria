"""Gradio AI chat app for Hugging Face Spaces and local development.

This lightweight UI reuses the repository's existing multi-provider chat
backend (`chat_providers.detect_provider`) so the same provider selection and
fallback logic used by the CLI/API can power a simple web chat experience.
"""

from __future__ import annotations

from typing import Any

import gradio as gr

from chat_providers import detect_provider


SUPPORTED_PROVIDER_CHOICES = [
    "auto",
    "local",
    "openai",
    "azure",
    "lmstudio",
    "ollama",
    "agi",
]


def _history_to_messages(history: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    """Convert Gradio chat history to provider-compatible message dicts."""
    messages: list[dict[str, str]] = []
    for item in history or []:
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant", "system"}:
            continue
        if isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content.strip()})
    return messages


def chat_response(
    message: str,
    history: list[dict[str, Any]] | None,
    provider_name: str,
    model_override: str,
    system_prompt: str,
) -> str:
    """Return a chat response using the repository's provider abstraction."""
    clean_message = (message or "").strip()
    if not clean_message:
        return "Please enter a message."

    explicit_provider = (provider_name or "auto").strip().lower()
    explicit_provider = explicit_provider if explicit_provider in SUPPORTED_PROVIDER_CHOICES else "auto"
    model_name = (model_override or "").strip() or None
    system_text = (system_prompt or "").strip()

    messages: list[dict[str, str]] = []
    if system_text:
        messages.append({"role": "system", "content": system_text})
    messages.extend(_history_to_messages(history))
    messages.append({"role": "user", "content": clean_message})

    try:
        provider, choice = detect_provider(
            explicit=explicit_provider,
            model_override=model_name,
        )
        result = provider.complete(messages, stream=False)
        if isinstance(result, str):
            reply = result.strip() or "[Empty response]"
        else:
            reply = "".join(str(chunk) for chunk in result).strip() or "[Empty response]"

        provider_banner = f"[{choice.name}:{choice.model}] "
        return provider_banner + reply
    except Exception as exc:  # pragma: no cover - runtime/provider dependent
        return f"[chat error] {exc}"


with gr.Blocks(title="Aria AI Chat") as demo:
    gr.Markdown(
        """
        # 🤖 Aria AI Chat

        Chat with Aria using the repository's built-in provider layer.
        Choose `auto` to let the app select among LM Studio, Ollama, Azure OpenAI,
        OpenAI, or the local fallback based on what is configured.
        """
    )

    with gr.Accordion("Chat settings", open=False):
        provider_input = gr.Dropdown(
            choices=SUPPORTED_PROVIDER_CHOICES,
            value="auto",
            label="Provider",
            info="auto uses the repo's normal provider detection and fallback behavior.",
        )
        model_input = gr.Textbox(
            label="Model override",
            placeholder="Optional: e.g. llama3.2, gpt-4o-mini, local-model",
        )
        system_input = gr.Textbox(
            label="System prompt",
            placeholder="Optional instruction for Aria's behavior",
            lines=3,
        )

    chat_component = gr.Chatbot(label="Aria")

    gr.ChatInterface(
        fn=chat_response,
        chatbot=chat_component,
        additional_inputs=[provider_input, model_input, system_input],
        examples=[
            ["Hello Aria!", "auto", "", "You are friendly and concise."],
            ["Explain what this repository does.", "local", "", "Be clear and brief."],
            ["Give me three ideas for improving the app.", "auto", "", "Be practical."],
        ],
        cache_examples=False,
    )


if __name__ == "__main__":
    demo.launch()
