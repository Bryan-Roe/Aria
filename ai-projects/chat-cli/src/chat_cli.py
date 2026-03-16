from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from colorama import Fore, Style, init as colorama_init

from chat_providers import detect_provider, RoleMessage


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_conversation(messages: List[RoleMessage], logs_dir: Path) -> Path:
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / f"chat_{now_ts()}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for m in messages:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    return path


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


def interactive_chat(args: argparse.Namespace) -> int:
    colorama_init()

    system_prompt = args.system or os.getenv(
        "SYSTEM_PROMPT",
        "You are a concise, friendly assistant. Be helpful and brief by default.",
    )
    logs_dir = Path(__file__).resolve().parent.parent / "logs"

    provider, info = detect_provider(explicit=args.provider, model_override=args.model)

    messages: List[RoleMessage] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    print_system(f"Provider: {info.name} | Model: {info.model}")
    print_system("Type your message. Commands: /new, /save, /exit")

    while True:
        try:
            user = input(Fore.CYAN + "you> " + Style.RESET_ALL)
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        cmd = user.strip().lower()
        if cmd == "/exit":
            return 0
        if cmd == "/new":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            print_system("Started a new conversation.")
            continue
        if cmd == "/save":
            path = save_conversation(messages, logs_dir)
            print_system(f"Saved to {path}")
            continue
        if not user.strip():
            continue

        messages.append({"role": "user", "content": user})

        # Stream assistant reply
        print(Fore.GREEN + "assistant> " + Style.RESET_ALL, end="")
        reply_accum = ""
        result = provider.complete(messages, stream=True)
        if isinstance(result, str):
            reply_accum = result
            print_assistant_chunk(result)
        else:
            for chunk in result:
                reply_accum += chunk
                print_assistant_chunk(chunk)
        print_assistant_done()

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

    provider, info = detect_provider(explicit=args.provider, model_override=args.model)

    messages: List[RoleMessage] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": args.once})

    print_system(f"Provider: {info.name} | Model: {info.model}")
    print(Fore.GREEN + "assistant> " + Style.RESET_ALL, end="")

    reply_accum = ""
    result = provider.complete(messages, stream=True)
    if isinstance(result, str):
        reply_accum = result
        print_assistant_chunk(result)
    else:
        for chunk in result:
            reply_accum += chunk
            print_assistant_chunk(chunk)
    print_assistant_done()

    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Simple terminal chat app with local/OpenAI/Azure providers")
    p.add_argument("--provider", choices=["auto", "openai", "azure", "local", "lora", "agi", "quantum", "lmstudio", "ollama"], default="auto", help="Which provider to use (default: auto)")
    p.add_argument("--system", type=str, help="Custom system prompt")
    p.add_argument("--model", type=str, help="Model/deployment name override")
    p.add_argument("--once", type=str, help="Send a single message then exit")
    return p


def main(argv: List[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.once:
        return one_shot(args)
    return interactive_chat(args)


if __name__ == "__main__":
    raise SystemExit(main())
