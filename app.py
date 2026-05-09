"""Aria CLI — minimal OpenAI Responses API client.

Reads a prompt from CLI args or stdin, calls the OpenAI Responses API,
and prints the model's reply. Designed to fail gracefully and to be
trivially testable.

Usage:
    OPENAI_API_KEY=sk-... python app.py "Explain quantum entanglement"
    echo "Hello" | python app.py
    python app.py --model gpt-4o-mini --temperature 0.0 "Refactor this code"

Environment variables:
    OPENAI_API_KEY            Required. OpenAI API key.
    OPENAI_MODEL              Optional. Overrides default model.
    OPENAI_BASE_URL           Optional. Custom API base (e.g. Azure-compatible proxy).
    OPENAI_ORG                Optional. Organization ID.
    OPENAI_TIMEOUT            Optional. Request timeout in seconds (default: 60).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any, Iterable

try:
    from openai import (
        APIConnectionError,
        APIError,
        AuthenticationError,
        OpenAI,
        RateLimitError,
    )
except ImportError as exc:  # pragma: no cover - import-time guard
    sys.stderr.write(
        "Error: the 'openai' package is not installed.\n"
        "Install it with: pip install openai\n"
    )
    raise SystemExit(1) from exc


# --------------------------------------------------------------------------- #
# Constants & configuration
# --------------------------------------------------------------------------- #

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "60"))
SYSTEM_PROMPT = (
    "You are a concise AI coding assistant. "
    "Return practical, code-focused responses."
)

# Exit codes
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_AUTH = 3
EXIT_RATE_LIMIT = 4
EXIT_NETWORK = 5
EXIT_API = 6
EXIT_UNEXPECTED = 1

logger = logging.getLogger("aria.app")


# --------------------------------------------------------------------------- #
# Response parsing
# --------------------------------------------------------------------------- #

def _extract_text(resp: Any) -> str:
    """Extract plain text from an OpenAI Responses API result.

    Prefers the convenience ``output_text`` attribute when available, and
    falls back to walking the structured ``output`` list. Always returns
    a stripped string (possibly empty).
    """
    # Fast path: SDK convenience attribute.
    output_text = getattr(resp, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    # Fallback: walk the structured output.
    parts: list[str] = []
    output: Iterable[Any] = getattr(resp, "output", None) or []
    for item in output:
        contents: Iterable[Any] = getattr(item, "content", None) or []
        for content in contents:
            if getattr(content, "type", "") != "output_text":
                continue
            text = getattr(content, "text", "")
            # Some SDK versions wrap text in an object with a `.value` attr.
            if hasattr(text, "value"):
                text = text.value
            if isinstance(text, str) and text:
                parts.append(text)

    return "\n".join(parts).strip()


# --------------------------------------------------------------------------- #
# Core request
# --------------------------------------------------------------------------- #

def ask_ai(
    client: OpenAI,
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    """Send ``prompt`` to the Responses API and return the extracted text."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    logger.debug("Requesting completion: model=%s temperature=%s", model, temperature)
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return _extract_text(resp)


# --------------------------------------------------------------------------- #
# CLI plumbing
# --------------------------------------------------------------------------- #

def _read_prompt(args_prompt: list[str]) -> str:
    """Read prompt from CLI args, piped stdin, or interactive input."""
    if args_prompt:
        return " ".join(args_prompt).strip()

    # Piped stdin (non-TTY) — read the whole buffer.
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    # Interactive fallback.
    try:
        return input("Prompt: ").strip()
    except EOFError:
        return ""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aria-app",
        description="Minimal OpenAI Responses API CLI for Aria.",
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
        help=f"Sampling temperature (default: {DEFAULT_TEMPERATURE}).",
    )
    parser.add_argument(
        "--system",
        default=SYSTEM_PROMPT,
        help="Override the system prompt.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: missing OPENAI_API_KEY environment variable.",
            file=sys.stderr,
        )
        return EXIT_AUTH

    prompt = _read_prompt(args.prompt)
    if not prompt:
        print("Error: prompt cannot be empty.", file=sys.stderr)
        return EXIT_USAGE

    client_kwargs: dict[str, Any] = {"api_key": api_key, "timeout": DEFAULT_TIMEOUT}
    if base_url := os.getenv("OPENAI_BASE_URL"):
        client_kwargs["base_url"] = base_url
    if org := os.getenv("OPENAI_ORG"):
        client_kwargs["organization"] = org

    try:
        client = OpenAI(**client_kwargs)
        output = ask_ai(
            client,
            prompt,
            model=args.model,
            temperature=args.temperature,
            system_prompt=args.system,
        )
    except AuthenticationError as exc:
        print(f"Authentication failed: {exc}", file=sys.stderr)
        return EXIT_AUTH
    except RateLimitError as exc:
        print(f"Rate limit exceeded: {exc}", file=sys.stderr)
        return EXIT_RATE_LIMIT
    except APIConnectionError as exc:
        print(f"Network error reaching OpenAI: {exc}", file=sys.stderr)
        return EXIT_NETWORK
    except APIError as exc:
        print(f"OpenAI API error: {exc}", file=sys.stderr)
        return EXIT_API
    except ValueError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001 - last-resort safety net
        logger.exception("Unexpected failure")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED

    print(output or "(No text returned.)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
