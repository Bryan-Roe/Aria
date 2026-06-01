import json
import logging
import sys
from pathlib import Path

import azure.functions as func

from chat_providers import detect_provider
from shared.http_utils import create_cors_headers, validate_messages

# Add chat-cli to path so we can import chat_providers
talk_to_ai_path = Path(__file__).resolve().parent.parent / "ai-projects" / "chat-cli" / "src"
sys.path.insert(0, str(talk_to_ai_path))

# Add repo root to path so we can import shared utilities as a package
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))


app = func.FunctionApp()


@app.route(route="chat", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def chat(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint for chat interactions.

    POST /api/chat
    Body: {
        "messages": [{"role": "user|assistant|system", "content": "..."}],
        "provider": "auto|openai|azure|local" (optional),
        "model": "model-name" (optional),
        "stream": false (optional, streaming not implemented in HTTP yet)
    }

    Response: {
        "response": "assistant's reply",
        "provider": "azure|openai|local",
        "model": "model-name"
    }
    """
    logging.info("Chat function invoked")

    try:
        # Parse request
        req_body = req.get_json()
        messages = req_body.get("messages", [])
        provider_choice = req_body.get("provider", "auto")
        model_override = req_body.get("model")

        # If LoRA provider selected without a model path, try default path
        if (provider_choice or "").lower() == "lora" and not model_override:
            default_adapter = Path(__file__).resolve().parent.parent / "data_out" / "lora_training" / "lora_adapter"
            if default_adapter.exists():
                model_override = str(default_adapter)
            else:
                return func.HttpResponse(
                    json.dumps(
                        {
                            "error": "LoRA provider selected but no adapter path provided and default path not found.",
                            "hint": "Provide 'model' in request body (e.g., data_out/lora_training/lora_adapter) or create the default adapter directory.",
                            "defaultTried": str(default_adapter),
                        }
                    ),
                    status_code=400,
                    mimetype="application/json",
                )

        if not messages:
            return func.HttpResponse(
                json.dumps({"error": "No messages provided"}),
                status_code=400,
                mimetype="application/json",
            )

        # Validate messages format
        is_valid, error_msg = validate_messages(messages)
        if not is_valid:
            return func.HttpResponse(
                json.dumps({"error": error_msg}),
                status_code=400,
                mimetype="application/json",
            )

        # Get provider
        provider, info = detect_provider(explicit=provider_choice, model_override=model_override)

        logging.info(f"Using provider: {info.name}, model: {info.model}")

        # Get completion (non-streaming for HTTP simplicity)
        result = provider.complete(messages, stream=False)

        # If result is still a generator, consume it
        if hasattr(result, "__iter__") and not isinstance(result, str):
            result = "".join(result)

        response_data = {"response": result, "provider": info.name, "model": info.model}

        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json",
            headers=create_cors_headers(),
        )

    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        return func.HttpResponse(
            json.dumps({"error": f"Validation error: {str(ve)}"}),
            status_code=400,
            mimetype="application/json",
        )
    except RuntimeError as re:
        logging.error(f"Runtime error: {str(re)}")
        return func.HttpResponse(
            json.dumps({"error": f"Configuration error: {str(re)}"}),
            status_code=500,
            mimetype="application/json",
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="chat", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def chat_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests"""
    return func.HttpResponse("", status_code=200, headers=create_cors_headers())
