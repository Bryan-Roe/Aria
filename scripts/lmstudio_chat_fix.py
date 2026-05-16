#!/usr/bin/env python3
"""LM Studio chat + code-fix helper.

Uses an OpenAI-compatible local endpoint (default: http://127.0.0.1:1234/v1)
for:
  1) General chat prompts
  2) Code-fix prompts for a target file (optional in-place write)

Examples:
  python scripts/lmstudio_chat_fix.py --list-models
  python scripts/lmstudio_chat_fix.py --prompt "Explain this repository's likely architecture."
  python scripts/lmstudio_chat_fix.py --fix-file scripts/fast_validate.py --instruction "Fix lint issues only"
  python scripts/lmstudio_chat_fix.py --fix-file scripts/fast_validate.py --instruction "Fix lint issues only" --write
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
DEFAULT_MODEL = os.getenv("LMSTUDIO_MODEL", "openai/gpt-oss-120b")


def _validate_base_url(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Invalid --base-url: only http/https are allowed")
    if not parsed.hostname:
        raise ValueError("Invalid --base-url: hostname is required")
    if parsed.username or parsed.password:
        raise ValueError("Invalid --base-url: userinfo is not allowed")
    if parsed.query or parsed.fragment:
        raise ValueError("Invalid --base-url: query/fragment are not allowed")

    allowed_hosts = {"127.0.0.1", "localhost", "::1"}
    if parsed.hostname not in allowed_hosts:
        raise ValueError("Invalid --base-url: only local LM Studio endpoints are allowed")

    return base_url.rstrip("/")


def _post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} calling {url}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Connection error calling {url}: {exc}") from exc


def _get_json(url: str, timeout: int = 30) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} calling {url}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Connection error calling {url}: {exc}") from exc


def list_models(base_url: str) -> list[str]:
    payload = _get_json(base_url.rstrip("/") + "/models")
    return [m.get("id", "") for m in payload.get("data", []) if m.get("id")]


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).rstrip() + "\n"
    return text


def chat(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 1200,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    response = _post_json(base_url.rstrip("/") + "/chat/completions", payload)

    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError(f"No choices in response: {response}")

    message = choices[0].get("message", {})
    content = message.get("content", "") or ""

    # Some local models surface only reasoning under certain settings.
    if not content:
        reasoning = message.get("reasoning", "")
        if reasoning:
            content = reasoning

    return content


def _resolve_and_validate_fix_path(raw_path: str) -> pathlib.Path:
    base_dir = pathlib.Path.cwd().resolve()
    candidate = pathlib.Path(raw_path)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    candidate = candidate.resolve()

    try:
        candidate.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError(f"--fix-file must be within the current working directory: {base_dir}") from exc

    return candidate


def fix_file(
    file_path: pathlib.Path,
    instruction: str,
    base_url: str,
    model: str,
    write: bool,
) -> str:
    safe_root = pathlib.Path.cwd().resolve()
    resolved_path = file_path.expanduser().resolve()
    try:
        resolved_path.relative_to(safe_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes allowed root '{safe_root}': {file_path}") from exc

    file_path = resolved_path
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    original = file_path.read_text(encoding="utf-8")
    prompt = (
        f"You are fixing source code.\n"
        f"Target file: {file_path}\n"
        f"Instruction: {instruction}\n\n"
        "Return ONLY the full corrected file content. "
        "Do not include markdown fences, commentary, or explanations.\n\n"
        "Current file content:\n"
        "-----BEGIN FILE-----\n"
        f"{original}\n"
        "-----END FILE-----\n"
    )

    fixed = chat(
        base_url=base_url,
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise coding assistant. "
                    "Output only the final file text."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=4000,
    )

    fixed = _strip_markdown_fence(fixed)

    if write:
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = file_path.with_suffix(file_path.suffix + f".{stamp}.bak")
        backup.write_text(original, encoding="utf-8")
        file_path.write_text(fixed, encoding="utf-8")
        print(f"Wrote updated file: {file_path}")
        print(f"Backup created: {backup}")

    return fixed


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Chat and fix code via local LM Studio endpoint")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL, help="LM Studio base URL (OpenAI compatible)")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Model id to use")
    p.add_argument("--list-models", action="store_true", help="List models from /models and exit")
    p.add_argument("--prompt", help="One-shot chat prompt")
    p.add_argument("--fix-file", help="Path of file to repair")
    p.add_argument("--instruction", help="Fix instruction for --fix-file")
    p.add_argument("--write", action="store_true", help="Write fixed content back to --fix-file")
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.base_url = _validate_base_url(args.base_url)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.list_models:
        models = list_models(args.base_url)
        if not models:
            print("No models found.")
            return 1
        print("Available models:")
        for m in models:
            print(f"- {m}")
        return 0

    if args.fix_file:
        if not args.instruction:
            print("--instruction is required when using --fix-file", file=sys.stderr)
            return 2
        try:
            safe_fix_path = _resolve_and_validate_fix_path(args.fix_file)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        output = fix_file(
            file_path=safe_fix_path,
            instruction=args.instruction,
            base_url=args.base_url,
            model=args.model,
            write=args.write,
        )
        if not args.write:
            print(output)
        return 0

    if args.prompt:
        answer = chat(
            base_url=args.base_url,
            model=args.model,
            messages=[{"role": "user", "content": args.prompt}],
        )
        print(answer)
        return 0

    print("Nothing to do. Use --prompt or --fix-file (or --list-models).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
