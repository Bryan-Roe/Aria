"""Aria CLI — minimal OpenAI Responses API client.

Reads a prompt from CLI args or stdin, calls the OpenAI Responses API,
and prints the model's reply. Designed to fail gracefully and to be
trivially testable.

Usage:
    OPENAI_API_KEY=sk-... python app.py "Explain quantum entanglement"
    echo "Hello" | python app.py
    python app.py --model gpt-4o-mini --temperature 0.0 "Refactor this code"

Environment variables:
    OPENAI_API_KEY            Required for --provider openai; optional when using local fallback.
    OPENAI_MODEL              Optional. Overrides default model.
    OPENAI_BASE_URL           Optional. Custom API base (e.g. Azure-compatible proxy).
    OPENAI_ORG                Optional. Organization ID.
    OPENAI_TIMEOUT            Optional. Request timeout in seconds (default: 60).
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import sys
import typing

# Ensure the shared module can be imported from the project root
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OpenAIAPIConnectionError = Exception
OpenAIAPIError = Exception
OpenAIAuthenticationError = Exception
OpenAIRateLimitError = Exception
_OpenAIClass = None

try:
    import openai

    # Bug fix: avoid AttributeError on legacy openai packages
    # that do not expose `OpenAI`.
    _OpenAIClass = getattr(openai, "OpenAI", None)

    try:
        OpenAIAPIConnectionError = openai.APIConnectionError
        OpenAIAPIError = openai.APIError
        OpenAIAuthenticationError = openai.AuthenticationError
        OpenAIRateLimitError = openai.RateLimitError
    except AttributeError:
        try:
            # Lazy import of importlib for dynamic openai.error module loading
            import importlib
            openai_error = importlib.import_module("openai.error")
            OpenAIAPIConnectionError = openai_error.APIConnectionError
            OpenAIAPIError = openai_error.APIError
            OpenAIAuthenticationError = openai_error.AuthenticationError
            OpenAIRateLimitError = openai_error.RateLimitError
        except (ImportError, AttributeError):
            pass
except ImportError:  # pragma: no cover - optional dependency when using local fallback
    # When the `openai` package isn't installed, allow the CLI to still run
    # in a local fallback mode. Define lightweight placeholders for exception
    # types so the except handlers below continue to work.
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
    OpenAI = _OpenAIClass  # type: ignore[assignment, misc]


# Optional: import summarizer helpers directly so the code can call them
# without referencing `shared.local_summary` each time. Provide safe fallbacks
# when the shared.local_summary module is not available.
try:
    from shared.local_summary import is_summary_request, summarize_text
except Exception:
    def is_summary_request(text: str) -> bool:  # pragma: no cover - fallback
        return False

    def summarize_text(text: str, *, max_sentences: int = 3, max_chars: int = 420) -> str:  # pragma: no cover - fallback
        return ""


# --------------------------------------------------------------------------- #
# Constants & configuration
# --------------------------------------------------------------------------- #

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_ENV = os.getenv("OPENAI_TIMEOUT", "60")
SYSTEM_PROMPT = (
    "You are a concise AI coding assistant. "
    "Return practical, code-focused responses."
)

# Exit codes
EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_USAGE = 2
EXIT_AUTH = 3
EXIT_RATE_LIMIT = 4
EXIT_NETWORK = 5
EXIT_API = 6

logger = logging.getLogger("aria.app")


# --------------------------------------------------------------------------- #
# Validation & parsing helpers
# --------------------------------------------------------------------------- #

def _parse_timeout(value: str) -> float:
    """Parse and validate a timeout value from the environment."""
    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("OPENAI_TIMEOUT must be a valid number.") from exc

    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("OPENAI_TIMEOUT must be a positive finite number.")

    return timeout


def _validate_temperature(value: float) -> float:
    """Validate a sampling temperature."""
    if not math.isfinite(value):
        raise ValueError("Temperature must be a finite number.")
    if not 0.0 <= value <= 2.0:
        raise ValueError("Temperature must be between 0.0 and 2.0.")
    return value


def _extract_text(resp: typing.Any) -> str:
    """Extract plain text from an OpenAI Responses API result.

    Prefers the convenience ``output_text`` attribute when available, and
    falls back to walking the structured ``output`` list. Always returns
    a stripped string (possibly empty).
    """
    output_text = getattr(resp, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts: list[str] = []
    output: typing.Iterable[typing.Any] = getattr(
        resp, "output", None) or []
    for item in output:
        contents: typing.Iterable[typing.Any] = getattr(
            item, "content", None) or []
        for content in contents:
            content_type = getattr(content, "type", "")
            if content_type not in {"output_text", "text"}:
                continue

            text = getattr(content, "text", None)
            if text is not None and hasattr(text, "value"):
                text = text.value

            if isinstance(text, str):
                stripped = text.strip()
                if stripped:
                    parts.append(stripped)

    return "\n".join(parts)


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
    prompt = prompt.strip()
    system_prompt = system_prompt.strip()
    model = model.strip()
    temperature = _validate_temperature(temperature)

    if not prompt:
        raise ValueError("Prompt cannot be empty.")
    if not model:
        raise ValueError("Model cannot be empty.")
    if not system_prompt:
        raise ValueError("System prompt cannot be empty.")

    logger.debug("Requesting completion: model=%s temperature=%s",
                 model, temperature)
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
    """Deterministic local fallback responder.

    This provides a helpful message when OpenAI is unavailable or when the
    user explicitly requests local mode. It deliberately keeps behavior
    deterministic and safe for local use.
    """
    prompt = (prompt or "").strip()
    system_prompt = (system_prompt or "").strip()
    if not prompt:
        raise ValueError("Prompt cannot be empty.")
    if not system_prompt:
        raise ValueError("System prompt cannot be empty.")

    ptext = prompt.strip()
    lower = ptext.lower()

    if is_summary_request(lower) or len(ptext) > 300:
        summary = summarize_text(ptext, max_sentences=3, max_chars=420)
        return (
            "[Local fallback summary]\n\n"
            f"Summary:\n{summary}\n\n"
            "Note: this is an offline extractive summary. For richer abstractive summaries, set OPENAI_API_KEY and install the 'openai' package."
        )

    if "explain" in lower or "what is" in lower:
        # Build sentences lazily — only needed in this branch.
        sentences = [s.strip()
                     for s in ptext.replace("\n", " ").split(".") if s.strip()]
        expl = sentences[0] if sentences else ptext
        return (
            "[Local fallback explanation]\n\n"
            f"Brief explanation:\n{expl}\n\n"
            "Suggestions:\n- Ask for examples\n- Ask for step-by-step instructions\n\n"
            "Note: enable cloud provider for fuller explanations."
        )

    # Generic helpful fallback: echo plus tips.
    tips = (
        "[Local fallback mode] OpenAI unavailable — local responder.\n\n"
        f"Prompt:\n{ptext}\n\n"
        "Helpful next steps:\n- Try a shorter prompt for local fallback.\n- Set OPENAI_API_KEY to use the cloud provider.\n- Re-run with --provider local to force local mode.\n"
    )
    return tips


# --------------------------------------------------------------------------- #
# CLI plumbing
# --------------------------------------------------------------------------- #

def _read_prompt(args_prompt: list[str]) -> str:
    """Read prompt from CLI args, piped stdin, or interactive input."""
    if args_prompt:
        return " ".join(args_prompt).strip()

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

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
        help=f"Sampling temperature from 0.0 to 2.0 (default: {DEFAULT_TEMPERATURE}).",
    )
    parser.add_argument(
        "--system",
        default=SYSTEM_PROMPT,
        help="Override the system prompt.",
    )
    parser.add_argument(
        "--provider",
        choices=("auto", "openai", "local"),
        default="auto",
        help="Provider selection: auto (default), openai, or local.",
    )
    parser.add_argument(
        "--no-local-fallback",
        dest="local_fallback",
        action="store_false",
        help="Disable automatic fallback to local mode on OpenAI failures.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def _handle_openai_error(
    exc: Exception,
    err_msg: str,
    exit_code: int,
    *,
    local_fallback: bool,
    prompt: str,
    system: str,
) -> int:
    """Shared handler for OpenAI API errors: fall back locally or exit with code."""
    if local_fallback:
        print(f"{type(exc).__name__} ({exc}); using local fallback.",
              file=sys.stderr)
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

    prompt = _read_prompt(args.prompt)
    if not prompt:
        print("Error: prompt cannot be empty.", file=sys.stderr)
        return EXIT_USAGE

    # Local mode is fully offline and should not require cloud credentials.
    if args.provider == "local":
        try:
            print(ask_local(prompt, system_prompt=args.system))
            return EXIT_OK
        except ValueError as exc:
            print(f"Invalid input: {exc}", file=sys.stderr)
            return EXIT_USAGE

    try:
        timeout = _parse_timeout(DEFAULT_TIMEOUT_ENV)
        temperature = _validate_temperature(args.temperature)
    except ValueError as exc:
        print(f"Invalid configuration: {exc}", file=sys.stderr)
        return EXIT_USAGE

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        if args.provider == "openai":
            print("Error: missing OPENAI_API_KEY environment variable.",
                  file=sys.stderr)
            return EXIT_AUTH
        # auto mode: transparently degrade to local when allowed
        if args.local_fallback:
            print(
                "Warning: missing OPENAI_API_KEY; falling back to local mode.", file=sys.stderr)
            print(ask_local(prompt, system_prompt=args.system))
            return EXIT_OK
        print("Error: missing OPENAI_API_KEY environment variable.", file=sys.stderr)
        return EXIT_AUTH

    client_kwargs: dict[str, typing.Any] = {
        "api_key": api_key,
        "timeout": timeout,
    }
    if base_url := os.getenv("OPENAI_BASE_URL"):
        client_kwargs["base_url"] = base_url.strip()
    if org := os.getenv("OPENAI_ORG"):
        client_kwargs["organization"] = org
    # If the openai package isn't installed, handle according to fallback
    # preference before attempting to construct the client.
    if OpenAI is None:
        if args.local_fallback:
            print(
                "Warning: 'openai' package not installed; falling back to local mode.", file=sys.stderr)
            print(ask_local(prompt, system_prompt=args.system))
            return EXIT_OK
        print("Error: the 'openai' package is not installed. Install it with: pip install openai", file=sys.stderr)
        return EXIT_USAGE

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
        return _handle_openai_error(
            exc, "Authentication failed", EXIT_AUTH,
            local_fallback=args.local_fallback, prompt=prompt, system=args.system,
        )
    except OpenAIRateLimitError as exc:
        return _handle_openai_error(
            exc, "Rate limit exceeded", EXIT_RATE_LIMIT,
            local_fallback=args.local_fallback, prompt=prompt, system=args.system,
        )
    except OpenAIAPIConnectionError as exc:
        return _handle_openai_error(
            exc, "Network error reaching OpenAI", EXIT_NETWORK,
            local_fallback=args.local_fallback, prompt=prompt, system=args.system,
        )
    except OpenAIAPIError as exc:
        return _handle_openai_error(
            exc, "OpenAI API error", EXIT_API,
            local_fallback=args.local_fallback, prompt=prompt, system=args.system,
        )
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
