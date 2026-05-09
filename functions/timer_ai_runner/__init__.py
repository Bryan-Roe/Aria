import datetime
import logging
import os
import sys
from datetime import timezone
from pathlib import Path

import azure.functions as func

# Add shared folder to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from chat_providers import detect_provider  # noqa: E402


def main(myTimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.now(timezone.utc).isoformat()
    if myTimer.past_due:
        logging.warning("The timer is past due!")

    provider_choice = os.getenv("DEFAULT_AI_PROVIDER", "local")
    prompt = os.getenv("AI_DEFAULT_PROMPT", f"Automated check-in at {utc_timestamp}")
    model = os.getenv("AI_MODEL")

    try:
        provider, info = detect_provider(explicit=provider_choice, model_override=model)
        messages = [{"role": "user", "content": prompt}]
        reply = provider.complete(messages, stream=False)
        logging.info(
            "AI timer run succeeded. Provider=%s, Model=%s, Reply=%s",
            info.name,
            info.model,
            reply,
        )
    except Exception as e:  # noqa: BLE001
        logging.exception("AI timer run failed: %s", e)

    logging.info("Python timer trigger function ran at %s", utc_timestamp)
