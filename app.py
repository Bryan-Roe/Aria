"""Aria CLI — minimal multi-provider AI client.

Reads a prompt from CLI args or stdin, calls a provider, and prints the reply.
Supports:
- Quantum AI via /api/quantum-llm/chat
- OpenAI Responses API
- Local deterministic fallback
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import math
import os
import re
import sys
import typing
from collections.abc import Iterable
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlparse as _urlparse

logger = logging.getLogger("aria.app")

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_ENV = os.getenv("OPENAI_TIMEOUT", "60")
MAX_PROMPT_CHARS = 10_000
MAX_SYSTEM_PROMPT_CHARS = 4_000
MAX_MODEL_NAME_CHARS = 128
SYSTEM_PROMPT = (
    "You are a concise AI coding assistant. Return practical, "
    "code-focused responses."
)
QUANTUM_CHAT_PATH = "/api/quantum-llm/chat"

EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_USAGE = 2
EXIT_AUTH = 3
EXIT_RATE_LIMIT = 4
EXIT_NETWORK = 5
EXIT_API = 6

OpenAIAPIConnectionError: type[Exception] = Exception
OpenAIAPIError: type[Exception] = Exception
OpenAIAuthenticationError: type[Exception] = Exception
OpenAIRateLimitError: type[Exception] = Exception
_OpenAIClass: typing.Any | None = None

try:
    import openai

    _OpenAIClass = getattr(openai, "OpenAI", None)

    try:
        OpenAIAPIConnectionError = openai.APIConnectionError
        OpenAIAPIError = openai.APIError
        OpenAIAuthenticationError = openai.AuthenticationError
        OpenAIRateLimitError = openai.RateLimitError
    except AttributeError:
        try:
            openai_error = importlib.import_module("openai.error")
            OpenAIAPIConnectionError = openai_error.APIConnectionError
            OpenAIAPIError = openai_error.APIError
            OpenAIAuthenticationError = openai_error.AuthenticationError
            OpenAIRateLimitError = openai_error.RateLimitError
        except (ImportError, AttributeError):
            pass
except ImportError:  # pragma: no cover - optional dependency

    class _OpenAIPackageMissing(Exception):
        pass

    OpenAIAPIConnectionError = _OpenAIPackageMissing
    OpenAIAPIError = _OpenAIPackageMissing
    OpenAIAuthenticationError = _OpenAIPackageMissing
    OpenAIRateLimitError = _OpenAIPackageMissing
    _OpenAIClass = None

if typing.TYPE_CHECKING:
    from openai import OpenAI
else:
    OpenAI = _OpenAIClass

try:
    from shared.local_summary import is_summary_request, summarize_text
except Exception:  # pragma: no cover - fallback

    def is_summary_request(text: str) -> bool:
        _ = text
        return False

    def summarize_text(text: str, *, max_sentences: int = 3, max_chars: int = 420) -> str:
        _ = (text, max_sentences, max_chars)
        return ""


def _parse_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("OPENAI_TIMEOUT must be a valid number.") from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("OPENAI_TIMEOUT must be a positive finite number.")
    return timeout


def _validate_temperature(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Temperature must be a finite number.")
    if not 0.0 <= value <= 2.0:
        raise ValueError("Temperature must be between 0.0 and 2.0.")
    return value


def _validate_prompt(prompt: str, *, max_chars: int = MAX_PROMPT_CHARS) -> str:
    normalized = (prompt or "").strip()
    if not normalized:
        raise ValueError("Prompt cannot be empty.")
    if len(normalized) > max_chars:
        raise ValueError(
            f"Prompt is too long ({len(normalized)} chars). "
            f"Maximum supported length is {max_chars} chars."
        )
    return normalized


def _validate_system_prompt(system_prompt: str) -> str:
    normalized = (system_prompt or "").strip()
    if not normalized:
        raise ValueError("System prompt cannot be empty.")
    if len(normalized) > MAX_SYSTEM_PROMPT_CHARS:
        raise ValueError(
            f"System prompt is too long ({len(normalized)} chars). "
            f"Maximum supported length is {MAX_SYSTEM_PROMPT_CHARS} chars."
        )
    return normalized


def _validate_model_name(model: str) -> str:
    normalized = (model or "").strip()
    if not normalized:
        raise ValueError("Model cannot be empty.")
    if len(normalized) > MAX_MODEL_NAME_CHARS:
        raise ValueError(
            f"Model name is too long ({len(normalized)} chars). "
            f"Maximum supported length is {MAX_MODEL_NAME_CHARS} chars."
        )
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", normalized):
        raise ValueError(
            "Model contains unsupported characters. Allowed: letters, "
            "digits, '.', '_', ':', '-'."
        )
    return normalized


def _read_stdin_limited(max_chars: int) -> str:
    return sys.stdin.read(max_chars + 1)


def _env_str(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _extract_text(resp: typing.Any) -> str:
    output_text = getattr(resp, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts: list[str] = []
    output: Iterable[typing.Any] = getattr(resp, "output", None) or []
    for item in output:
        contents: Iterable[typing.Any] = getattr(item, "content", None) or []
        for content in contents:
            content_type = getattr(content, "type", "")
            if content_type not in {"output_text", "text"}:
                continue

            text = getattr(content, "text", None)
            if text is not None and hasattr(text, "value"):
                text = text.value
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())

    return "\n".join(parts).strip()


def _extract_quantum_text(payload: typing.Any) -> str:
    if isinstance(payload, str):
        return payload.strip()

    if isinstance(payload, dict):
        payload_dict = typing.cast(dict[str, typing.Any], payload)
        for key in (
            "output_text",
            "text",
            "response",
            "completion",
            "message",
        ):
            value = payload_dict.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        choices = payload_dict.get("choices")
        if isinstance(choices, list) and choices:
            choices_list = typing.cast(list[typing.Any], choices)
            first = choices_list[0]
            if isinstance(first, dict):
                first_dict = typing.cast(dict[str, typing.Any], first)
                message = first_dict.get("message")
                if isinstance(message, dict):
                    message_dict = typing.cast(dict[str, typing.Any], message)
                    content = message_dict.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                text = first_dict.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()

        data = payload_dict.get("data")
        if isinstance(data, dict):
            nested = _extract_quantum_text(data)
            if nested:
                return nested

    return ""


def ask_quantum(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    system_prompt: str = SYSTEM_PROMPT,
    base_url: str = "http://localhost:7071",
    timeout: float = 60.0,
) -> str:
    prompt = _validate_prompt(prompt)
    system_prompt = _validate_system_prompt(system_prompt)
    model = _validate_model_name(model)
    temperature = _validate_temperature(temperature)

    base_url = (base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("Quantum base URL cannot be empty.")
    from urllib.parse import urlparse as _urlparse

    _parsed = _urlparse(base_url)
    if _parsed.scheme not in {"http", "https"}:
        raise ValueError(
            f"Quantum base URL scheme '{_parsed.scheme}' is not allowed; "
            "use http or https."
        )

    payload = {
        "prompt": prompt,
        "system_prompt": system_prompt,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "model": model,
        "temperature": temperature,
    }

    req = urllib_request.Request(
        # noqa: S310 - URL from configurable local endpoint
        f"{base_url}{QUANTUM_CHAT_PATH}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib_request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        raw = resp.read().decode("utf-8", errors="replace").strip()
        if not raw:
            return ""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        return _extract_quantum_text(parsed) or raw


def ask_ai(
    client: OpenAI,
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    prompt = _validate_prompt(prompt)
    system_prompt = _validate_system_prompt(system_prompt)
    model = _validate_model_name(model)
    temperature = _validate_temperature(temperature)

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return _extract_text(resp)


def ask_local(prompt: str, *, system_prompt: str = SYSTEM_PROMPT) -> str:
    prompt = _validate_prompt(prompt)
    _validate_system_prompt(system_prompt)

    ptext = prompt.strip()
    lower = ptext.lower()

    if is_summary_request(lower) or len(ptext) > 300:
        summary = summarize_text(ptext, max_sentences=3, max_chars=420)
        return (
            "[Local fallback summary]\n\n"
            f"Summary:\n{summary}\n\n"
            "Note: this is an offline extractive summary. "
            "For richer results, set QUANTUM_LLM_BASE_URL or OPENAI_API_KEY."
        )

    if "explain" in lower or "what is" in lower:
        sentences = [
            s.strip()
            for s in ptext.replace("\n", " ").split(".")
            if s.strip()
        ]
        expl = sentences[0] if sentences else ptext
        return (
            "[Local fallback explanation]\n\n"
            f"Brief explanation:\n{expl}\n\n"
            "Suggestions:\n"
            "- Ask for examples\n"
            "- Ask for step-by-step instructions"
        )

    return (
        "[Local fallback mode]\n\n"
        f"Prompt:\n{ptext}\n\n"
        "Helpful next steps:\n"
        "- Set QUANTUM_LLM_BASE_URL to use Quantum AI.\n"
        "- Set OPENAI_API_KEY to use OpenAI.\n"
    )


def _read_prompt(args_prompt: list[str]) -> str:
    if args_prompt:
        return " ".join(args_prompt).strip()
    if not sys.stdin.isatty():
        return _read_stdin_limited(MAX_PROMPT_CHARS).strip()
    try:
        return input("Prompt: ").strip()
    except EOFError:
        return ""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aria-app",
        description="Minimal multi-provider AI CLI for Aria.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Prompt text. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model name (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=(
            f"Sampling temperature from 0.0 to 2.0 "
            f"(default: {DEFAULT_TEMPERATURE})."
        ),
    )
    parser.add_argument(
        "--system",
        default=SYSTEM_PROMPT,
        help="Override the system prompt.",
    )
    parser.add_argument(
        "--provider",
        choices=("auto", "openai", "quantum", "local"),
        default="auto",
        help="Provider selection: auto (default), openai, quantum, or local.",
    )
    parser.add_argument(
        "--no-local-fallback",
        dest="local_fallback",
        action="store_false",
        help="Disable automatic fallback to local mode on provider failures.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    parser.set_defaults(local_fallback=True)
    return parser


def _handle_provider_error(
    exc: Exception,
    err_msg: str,
    exit_code: int,
    *,
    local_fallback: bool,
    prompt: str,
    system: str,
) -> int:
    if local_fallback:
        print(
            f"{type(exc).__name__} ({exc}); using local fallback.",
            file=sys.stderr,
        )
        print(ask_local(prompt, system_prompt=system))
        return EXIT_OK
    print(f"{err_msg}: {exc}", file=sys.stderr)
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        prompt = _validate_prompt(_read_prompt(args.prompt))
    except ValueError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return EXIT_USAGE

    try:
        timeout = _parse_timeout(DEFAULT_TIMEOUT_ENV)
        temperature = _validate_temperature(args.temperature)
    except ValueError as exc:
        print(f"Invalid configuration: {exc}", file=sys.stderr)
        return EXIT_USAGE

    quantum_base_url = _env_str("QUANTUM_LLM_BASE_URL") or _env_str("FUNCTIONS_BASE_URL")
    quantum_enabled = bool(quantum_base_url)

    if args.provider == "local":
        try:
            print(ask_local(prompt, system_prompt=args.system))
            return EXIT_OK
        except ValueError as exc:
            print(f"Invalid input: {exc}", file=sys.stderr)
            return EXIT_USAGE

    if args.provider in {"auto", "quantum"} and quantum_enabled:
        try:
            print(
                ask_quantum(
                    prompt,
                    model=args.model,
                    temperature=temperature,
                    system_prompt=args.system,
                    base_url=quantum_base_url,
                    timeout=timeout,
                )
            )
            return EXIT_OK
        except urllib_error.HTTPError as exc:
            if args.provider == "quantum":
                return _handle_provider_error(
                    exc,
                    "Quantum API error",
                    EXIT_API,
                    local_fallback=args.local_fallback,
                    prompt=prompt,
                    system=args.system,
                )
        except (urllib_error.URLError, TimeoutError) as exc:
            if args.provider == "quantum":
                return _handle_provider_error(
                    exc,
                    "Network error reaching Quantum AI",
                    EXIT_NETWORK,
                    local_fallback=args.local_fallback,
                    prompt=prompt,
                    system=args.system,
                )
        except ValueError as exc:
            print(f"Invalid input: {exc}", file=sys.stderr)
            return EXIT_USAGE

    api_key = _env_str("OPENAI_API_KEY")
    if not api_key:
        if args.provider == "openai":
            if args.local_fallback:
                print(ask_local(prompt, system_prompt=args.system))
                return EXIT_OK
            print(
                "Error: missing OPENAI_API_KEY environment variable.",
                file=sys.stderr,
            )
            return EXIT_AUTH
        if args.local_fallback:
            print(ask_local(prompt, system_prompt=args.system))
            return EXIT_OK
        print(
            "Error: missing OPENAI_API_KEY environment variable.",
            file=sys.stderr,
        )
        return EXIT_AUTH

    if _OpenAIClass is None:
        if args.local_fallback:
            print(ask_local(prompt, system_prompt=args.system))
            return EXIT_OK
        print(
            "Error: the 'openai' package is not installed. "
            "Install it with: pip install openai",
            file=sys.stderr,
        )
        return EXIT_USAGE

    client_kwargs: dict[str, typing.Any] = {
        "api_key": api_key,
        "timeout": timeout,
    }
    base_url = _env_str("OPENAI_BASE_URL")
    if base_url:
        client_kwargs["base_url"] = base_url
    org = _env_str("OPENAI_ORG")
    if org:
        client_kwargs["organization"] = org

    try:
        client = OpenAI(**client_kwargs)
        output = ask_ai(
            client,
            prompt,
            model=args.model,
            temperature=temperature,
            system_prompt=args.system,
        )
    except OpenAIAuthenticationError as exc:
        return _handle_provider_error(
            exc,
            "Authentication failed",
            EXIT_AUTH,
            local_fallback=args.local_fallback,
            prompt=prompt,
            system=args.system,
        )
    except OpenAIRateLimitError as exc:
        return _handle_provider_error(
            exc,
            "Rate limit exceeded",
            EXIT_RATE_LIMIT,
            local_fallback=args.local_fallback,
            prompt=prompt,
            system=args.system,
        )
    except OpenAIAPIConnectionError as exc:
        return _handle_provider_error(
            exc,
            "Network error reaching OpenAI",
            EXIT_NETWORK,
            local_fallback=args.local_fallback,
            prompt=prompt,
            system=args.system,
        )
    except OpenAIAPIError as exc:
        return _handle_provider_error(
            exc,
            "OpenAI API error",
            EXIT_API,
            local_fallback=args.local_fallback,
            prompt=prompt,
            system=args.system,
        )
    except ValueError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected failure")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED

    print(output or "(No text returned.)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
