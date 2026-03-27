from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from colorama import Fore, Style, init as colorama_init
except ImportError:  # pragma: no cover - exercised in dependency-light test envs
    class _NoColor:
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ""
        RESET = RESET_ALL = BRIGHT = DIM = NORMAL = ""

    Fore = Style = _NoColor()

    def colorama_init(*args, **kwargs) -> None:
        return None

from chat_providers import detect_provider, RoleMessage


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def provider_readiness_summary() -> str:
    """Return a human-readable provider readiness summary based on env vars."""
    azure_key = bool(os.getenv("AZURE_OPENAI_API_KEY"))
    azure_endpoint = bool(os.getenv("AZURE_OPENAI_ENDPOINT"))
    azure_deployment = bool(os.getenv("AZURE_OPENAI_DEPLOYMENT"))
    azure_version = bool(os.getenv("AZURE_OPENAI_API_VERSION"))
    azure_ready = azure_key and azure_endpoint and azure_deployment and azure_version

    openai_ready = bool(os.getenv("OPENAI_API_KEY"))
    lmstudio_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")

    lines = [
        "Provider readiness:",
        f"  Azure OpenAI : {'ready' if azure_ready else 'not ready'} "
        f"(key={'set' if azure_key else 'missing'}, endpoint={'set' if azure_endpoint else 'missing'}, "
        f"deployment={'set' if azure_deployment else 'missing'}, api_version={'set' if azure_version else 'missing'})",
        f"  OpenAI       : {'ready' if openai_ready else 'not ready'} (OPENAI_API_KEY {'set' if openai_ready else 'missing'})",
        f"  LM Studio    : configured via LMSTUDIO_BASE_URL={lmstudio_url}",
        f"  Ollama       : configured via OLLAMA_BASE_URL={ollama_url}",
        "  Local Echo   : always available",
    ]
    return "\n".join(lines)


def save_conversation(messages: List[RoleMessage], logs_dir: Path) -> Path:
    logs_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"chat_{now_ts()}"
    path = logs_dir / f"{base_name}.jsonl"
    attempt = 1

    while True:
        try:
            with path.open("x", encoding="utf-8") as f:
                for m in messages:
                    f.write(json.dumps(m, ensure_ascii=False) + "\n")
            return path
        except FileExistsError:
            path = logs_dir / f"{base_name}_{attempt}.jsonl"
            attempt += 1


def print_system(msg: str) -> None:
    print(Fore.MAGENTA + msg + Style.RESET_ALL)


def print_user(msg: str) -> None:
    print(Fore.CYAN + msg + Style.RESET_ALL)


def print_assistant_chunk(chunk: str) -> None:
    # Avoid styles on every print for speed
    sys.stdout.write(chunk)
    sys.stdout.flush()


def print_assistant_done() -> None:
    print(Style.RESET_ALL)


def format_provider_error(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    return f"[provider error: {message}]"


def stream_assistant_reply(provider, messages: List[RoleMessage]) -> str:
    print(Fore.GREEN + "assistant> " + Style.RESET_ALL, end="")
    reply_accum = ""
    try:
        result = provider.complete(messages, stream=True)
        if isinstance(result, str):
            reply_accum = result
            print_assistant_chunk(result)
        else:
            for chunk in result:
                reply_accum += chunk
                print_assistant_chunk(chunk)
    except Exception as exc:
        error_text = format_provider_error(exc)
        if reply_accum and not reply_accum.endswith("\n"):
            print_assistant_chunk("\n")
            reply_accum += "\n"
        print_assistant_chunk(error_text)
        reply_accum += error_text
    print_assistant_done()
    return reply_accum


def autonomous_chat(args: argparse.Namespace) -> int:
    colorama_init()

    system_prompt = args.system or os.getenv(
        "SYSTEM_PROMPT",
        "You are a concise, friendly assistant. Be helpful and brief by default.",
    )
    seed_prompt = args.auto_seed or os.getenv(
        "AUTONOMOUS_CHAT_SEED",
        "Start working autonomously on the most useful next step and keep driving the conversation without waiting for user input.",
    )
    followup_prompt = args.auto_followup or os.getenv(
        "AUTONOMOUS_CHAT_FOLLOWUP",
        "Continue autonomously. Build on the conversation so far, choose the next useful step yourself, and keep going without asking for user input.",
    )
    delay_seconds = max(0.0, args.auto_delay)

    provider, info = detect_provider(
        explicit=args.provider, model_override=args.model)

    messages: List[RoleMessage] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    print_system(f"Provider: {info.name} | Model: {info.model}")
    print_system(
        "Autonomous mode active. Press Ctrl+C to stop."
    )

    turn_count = 0
    next_user_message = seed_prompt

    try:
        while args.max_turns is None or turn_count < args.max_turns:
            turn_count += 1
            print_user(f"auto[{turn_count}]> {next_user_message}")
            messages.append({"role": "user", "content": next_user_message})
            reply_accum = stream_assistant_reply(provider, messages)
            messages.append({"role": "assistant", "content": reply_accum})
            next_user_message = followup_prompt
            if delay_seconds > 0:
                time.sleep(delay_seconds)
    except KeyboardInterrupt:
        print()
        return 0

    return 0


def interactive_chat(args: argparse.Namespace) -> int:
    colorama_init()

    system_prompt = args.system or os.getenv(
        "SYSTEM_PROMPT",
        "You are a concise, friendly assistant. Be helpful and brief by default.",
    )
    logs_dir = Path(__file__).resolve().parent.parent / "logs"

    provider, info = detect_provider(
        explicit=args.provider, model_override=args.model)

    messages: List[RoleMessage] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    print_system(f"Provider: {info.name} | Model: {info.model}")
    print_system(
        "Type your message. Commands: /help, /new, /save, /history, /model, /providers, /reasoning, /exit")

    while True:
        try:
            user = input(Fore.CYAN + "you> " + Style.RESET_ALL)
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        cmd = user.strip().lower()
        if cmd == "/exit":
            return 0

        if cmd == "/help":
            print_system(
                "Available commands:\n"
                "  /new        — start a fresh conversation (clears history)\n"
                "  /save       — save conversation to a JSONL file\n"
                "  /history    — show conversation history summary\n"
                "  /model      — show current provider and model info\n"
                "  /providers  — show provider readiness from current env vars\n"
                "  /reasoning  — show AGI reasoning summary (AGI provider only)\n"
                "  /exit       — quit the chat\n"
                "  /help       — show this message"
            )
            continue

        if cmd == "/new":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            print_system("Started a new conversation.")
            continue

        if cmd == "/save":
            path = save_conversation(messages, logs_dir)
            print_system(f"Saved {len(messages)} message(s) to {path}")
            continue

        if cmd == "/history":
            user_msgs = [m for m in messages if m.get("role") == "user"]
            asst_msgs = [m for m in messages if m.get("role") == "assistant"]
            print_system(
                f"Conversation: {len(user_msgs)} user message(s), "
                f"{len(asst_msgs)} assistant reply(ies)."
            )
            if user_msgs:
                last = user_msgs[-1]["content"]
                preview = last[:120] + "..." if len(last) > 120 else last
                print_system(f"Last user message: {preview}")
            continue

        if cmd == "/model":
            print_system(f"Provider : {info.name}")
            print_system(f"Model    : {info.model}")
            continue

        if cmd == "/providers":
            print_system(provider_readiness_summary())
            continue

        if cmd == "/reasoning":
            # Only AGIProvider exposes get_reasoning_summary()
            if hasattr(provider, "get_reasoning_summary"):
                # type: ignore[union-attr]
                summary = provider.get_reasoning_summary()
                last_agent = summary.get("last_agent_used") or "none yet"
                last_score = summary.get("last_agent_score")
                score_str = f"{last_score:.3f}" if last_score is not None else "n/a"
                available = ", ".join(summary.get("available_agents", []))

                # Build learned-pattern lines (top 5 by observation count).
                top_patterns = summary.get("top_learned_patterns", [])
                if top_patterns:
                    pattern_lines = "\n".join(
                        f"    {p.get('domain', '?')}/{p.get('intent', '?')} "
                        f"→ {p.get('agent', '?')} (×{p.get('count', 0)})"
                        for p in top_patterns
                    )
                    pattern_section = f"\n  Top routing patterns    :\n{pattern_lines}"
                else:
                    pattern_section = ""

                print_system(
                    f"AGI Reasoning Summary:\n"
                    f"  Reasoning chains stored : {summary.get('total_reasoning_chains', 0)}\n"
                    f"  Conversation turns      : {summary.get('conversation_length', 0)}\n"
                    f"  Active goals            : {', '.join(summary.get('active_goals', [])) or 'none'}\n"
                    f"  Learned patterns        : {summary.get('learned_patterns_count', 0)}"
                    f"{pattern_section}\n"
                    f"  Last agent routed to    : {last_agent} (score={score_str})\n"
                    f"  Available agents        : {available}"
                )
            else:
                print_system(
                    "Reasoning summary is only available with the AGI provider (--provider agi).")
            continue

        if not user.strip():
            continue

        messages.append({"role": "user", "content": user})

        reply_accum = stream_assistant_reply(provider, messages)
        messages.append({"role": "assistant", "content": reply_accum})


def one_shot(args: argparse.Namespace) -> int:
    colorama_init()
    if not args.once:
        print("--once requires a message string.")
        return 2

    system_prompt = args.system or os.getenv(
        "SYSTEM_PROMPT",
        "You are a concise, friendly assistant.",
    )

    provider, info = detect_provider(
        explicit=args.provider, model_override=args.model)

    messages: List[RoleMessage] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": args.once})

    print_system(f"Provider: {info.name} | Model: {info.model}")
    stream_assistant_reply(provider, messages)

    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Simple terminal chat app with local/OpenAI/Azure providers")
    p.add_argument("--provider", choices=["auto", "openai", "azure", "local", "lora", "agi", "quantum",
                                          "lmstudio", "ollama"], default="auto", help="Which provider to use (default: auto)")
    p.add_argument("--system", type=str, help="Custom system prompt")
    p.add_argument("--model", type=str, help="Model/deployment name override")
    p.add_argument("--once", type=str, help="Send a single message then exit")
    p.add_argument("--interactive", action="store_true",
                   help="Use stdin-driven interactive chat instead of autonomous mode")
    p.add_argument("--autonomous", action="store_true",
                   help="Run unattended continuous chat without prompting for stdin")
    p.add_argument("--auto-seed", type=str,
                   help="Initial autonomous user message")
    p.add_argument("--auto-followup", type=str,
                   help="Autonomous follow-up message reused after each assistant turn")
    p.add_argument("--auto-delay", type=float, default=0.0,
                   help="Delay between autonomous turns in seconds (default: 0)")
    p.add_argument("--max-turns", type=int,
                   help="Maximum autonomous turns before exiting (default: run forever)")
    return p


def should_run_autonomous(args: argparse.Namespace) -> bool:
    if args.interactive:
        return False
    if args.autonomous:
        return True
    return not args.once


def main(argv: List[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.once:
        return one_shot(args)
    if should_run_autonomous(args):
        return autonomous_chat(args)
    return interactive_chat(args)


if __name__ == "__main__":
    raise SystemExit(main())
