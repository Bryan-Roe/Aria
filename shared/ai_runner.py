"""Shared AI runner module for Azure Functions.

Provides a simple helper to invoke the existing talk-to-ai CLI (`chat_cli.py`) in one-shot
mode so we can reuse the provider auto-detection logic without refactoring.

Environment variables influencing behavior:
  DEFAULT_AI_PROVIDER  -> provider passed when caller does not supply one (default: 'local')
  WRITE_AI_RUN_LOG     -> if '1' (default), write output to ai-projects/chat-cli/logs/auto_run_<ts>.txt
  SYSTEM_PROMPT        -> optional system prompt override forwarded to CLI via --system

The runner returns the raw assistant output as a string plus a metadata dict.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
CHAT_CLI = ROOT_DIR / "ai-projects" / "chat-cli" / "src" / "chat_cli.py"
LOG_DIR = ROOT_DIR / "ai-projects" / "chat-cli" / "logs"

# Cached ANSI escape regex for performance across imports
_ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def run_chat_once(
    prompt: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    system: Optional[str] = None,
    timeout: int = 120,
) -> Tuple[str, Dict[str, str]]:
    """Run the chat CLI in one-shot mode and capture its stdout.

    Parameters
    ----------
    prompt: User prompt to send.
    provider: Provider name ('local', 'openai', 'azure', or 'auto'). Defaults to env DEFAULT_AI_PROVIDER or 'local'.
    model: Optional model override forwarded via --model.
    system: Optional system prompt override forwarded via --system.
    timeout: Seconds before aborting the subprocess.
    """
    if not CHAT_CLI.exists():
        raise FileNotFoundError(f"chat_cli.py not found at {CHAT_CLI}")

    provider = provider or os.getenv("DEFAULT_AI_PROVIDER", "local")
    system = system or os.getenv("SYSTEM_PROMPT")

    cmd = [sys.executable, str(CHAT_CLI), "--provider", provider, "--once", prompt]
    if model:
        cmd.extend(["--model", model])
    if system:
        cmd.extend(["--system", system])

    logging.info("Running chat CLI: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(
            f"chat_cli failed (exit {proc.returncode}): {proc.stderr.strip() or 'no stderr'}"
        )

    raw_output = proc.stdout

    # Strip ANSI color codes for easier consumption (module-level cached regex)
    output = _ANSI_ESCAPE_RE.sub("", raw_output).strip()

    # Try to extract only the assistant content after the 'assistant> ' prompt
    reply = output
    marker = "assistant> "
    idx = output.rfind(marker)
    if idx != -1:
        reply = output[idx + len(marker) :].rstrip()

    metadata = {"provider": provider}
    if model:
        metadata["model"] = model

    # Optional logging of output to file for later review
    if os.getenv("WRITE_AI_RUN_LOG", "1") == "1":
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            log_path = LOG_DIR / f"auto_run_{ts}.txt"
            with log_path.open("w", encoding="utf-8") as f:
                f.write(f"PROMPT: {prompt}\n")
                f.write("OUTPUT (clean):\n")
                f.write(output + "\n\n")
                f.write("REPLY ONLY:\n")
                f.write(reply + "\n")
            logging.info("Wrote AI run log to %s", log_path)
        except Exception as e:  # noqa: BLE001
            logging.warning("Failed to write AI run log: %s", e)

    return reply, metadata
