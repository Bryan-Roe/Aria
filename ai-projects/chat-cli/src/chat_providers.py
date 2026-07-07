from __future__ import annotations

import json as _json
import logging
import os
import random
import subprocess
import sys
import threading
import time
from collections.abc import Generator, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from shared.local_calc import evaluate_arithmetic, normalize_expression
    from shared.local_summary import is_summary_request, summarize_text
except ModuleNotFoundError:
    # Support direct CLI execution from ai-projects/chat-cli/src where repo root
    # is not automatically on sys.path (e.g., `python chat_cli.py --once ...`).
    _THIS_FILE = Path(__file__).resolve()
    for _parent in _THIS_FILE.parents:
        if (_parent / "shared").is_dir():
            _parent_str = str(_parent)
            if _parent_str not in sys.path:
                sys.path.insert(0, _parent_str)
            break
    from shared.local_calc import evaluate_arithmetic, normalize_expression
    from shared.local_summary import is_summary_request, summarize_text

try:
    from shared.local_settings import apply_local_settings

    apply_local_settings()
except Exception:
    pass

# Helpers for Azure quota/rate-limit detection
try:  # shared package may not be importable in all contexts (tests add paths)
    from shared.azure_utils import format_quota_message, is_quota_error, is_transient_rate_error
except Exception:  # pragma: no cover - best-effort import
    # Provide fallbacks if the shared module is unavailable in the
    # runtime/test harness.
    def is_quota_error(e: Any) -> bool:
        txt = str(e).lower() if e is not None else ""
        return any(
            k in txt
            for k in (
                "quota",
                "premium",
                "exceed",
                "allowance",
                "insufficient",
                "billing",
            )
        )

    def is_transient_rate_error(e: Any) -> bool:
        txt = str(e).lower() if e is not None else ""
        return any(k in txt for k in ("rate limit", "429", "too many requests", "rate_limit"))

    def format_quota_message(exc: Any, service_name: str = "Azure OpenAI") -> str:
        return (
            f"{service_name} quota/premium limit reached. Check billing/limits or use another provider."
            f" Details: {str(exc)}"
        )


_LOGGER = logging.getLogger(__name__)

try:
    # openai>=1.0
    from openai import AzureOpenAI, OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    OpenAI = None  # type: ignore
    AzureOpenAI = None  # type: ignore


# Thread-safe cache for LM Studio availability checks
_lm_studio_availability_cache: dict[str, Any] = {
    "available": None,
    "checked_at": 0.0,
    "url": None,
}
_lm_studio_cache_lock = threading.RLock()
# Backward-compatible alias for tests expecting _lmstudio_cache_lock
_lmstudio_cache_lock = _lm_studio_cache_lock
_LM_STUDIO_CACHE_TTL_SECONDS = 30
# Backward-compatible aliases for tests
_lmstudio_cache = _lm_studio_availability_cache
_LMSTUDIO_CACHE_TTL = _LM_STUDIO_CACHE_TTL_SECONDS

# Thread-safe cache for Ollama availability checks
_ollama_availability_cache: dict[str, Any] = {
    "available": None,
    "checked_at": 0.0,
    "url": None,
}
_ollama_cache_lock = threading.RLock()
_OLLAMA_CACHE_TTL_SECONDS = 30

# Thread-safe cache for Groq availability checks
_groq_availability_cache: dict[str, Any] = {
    "available": None,
    "checked_at": 0.0,
    "url": None,
}
_groq_cache_lock = threading.RLock()
_GROQ_CACHE_TTL_SECONDS = 30


# Thread-safe cache for detect_provider results to reduce repeated provider
# probing and client instantiation on hot API paths (e.g., /api/ai/status,
# chat endpoint setup). Cache entries are keyed by explicit parameters and
# relevant environment values so config changes invalidate naturally.
_provider_detection_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
_provider_detection_cache_lock = threading.RLock()
_PROVIDER_DETECT_CACHE_TTL_SECONDS = 5.0


# {"role": "system|user|assistant", "content": "..."}
RoleMessage = dict[str, str]


# Backward-compatible provider aliases used by tests and scripts.
# Keys should be lowercase and normalized with `-`/`_` variants where useful.
_PROVIDER_ALIASES: dict[str, str] = {
    "azure_openai": "azure",
    "azure-openai": "azure",
    "open_ai": "openai",
    "lm_studio": "lmstudio",
    "lm-studio": "lmstudio",
    "local_echo": "local",
    "local-echo": "local",
    "qai": "quantum",
    "qai_quantum": "quantum",
    "qai-quantum": "quantum",
    "quantum_llm": "quantum",
    "quantum-llm": "quantum",
    "groq_api": "groq",
    "groq-api": "groq",
}

_KNOWN_PROVIDER_CHOICES: set[str] = {
    "auto",
    "lmstudio",
    "ollama",
    "azure",
    "openai",
    "local",
    "lora",
    "agi",
    "qai",
    "quantum",
    "groq",
}


def _get_lmstudio_api_key() -> str | None:
    """Resolve LM Studio API token from supported env var names."""
    return (
        os.getenv("LM_API_TOKEN")
        or os.getenv("LMSTUDIO_API_KEY")
        or os.getenv("LMSTUDIO_TOKEN")
        or os.getenv("LMSTUDIO_API_TOKEN")
    )


def _get_bounded_timeout_env(name: str, default: float, *, minimum: float = 0.1, maximum: float = 300.0) -> float:
    """Read a timeout value from env with bounds and fallback.

    Returns ``default`` when missing/invalid, and clamps to ``[minimum, maximum]``.
    """
    raw = os.getenv(name)
    if raw is None:
        return float(default)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return float(default)
    if value < minimum:
        return float(minimum)
    if value > maximum:
        return float(maximum)
    return float(value)


def _is_text_like_content_block_type(block_type: Any) -> bool:
    """Return True for OpenAI-compatible text block type variants."""
    if not isinstance(block_type, str):
        return False
    normalized = block_type.strip().lower()
    return normalized == "text" or normalized.endswith("_text")


def _normalize_message_content_for_openai_api(content: Any) -> Any:
    """Normalize message content before sending it to OpenAI-compatible APIs.

    This trims plain-text messages and removes whitespace-only text blocks from
    block-based content, while preserving non-text blocks such as image_url.
    Returns None when no meaningful content remains.
    """
    if isinstance(content, str):
        normalized = content.strip()
        return normalized or None

    if isinstance(content, list):
        normalized_blocks: list[dict[str, Any]] = []
        for block in content:
            if not isinstance(block, dict):
                continue

            if not _is_text_like_content_block_type(block.get("type")):
                normalized_blocks.append(block)
                continue

            text_value = block.get("text")
            if not isinstance(text_value, str):
                continue

            normalized_text = text_value.strip()
            if not normalized_text:
                continue

            normalized_block = dict(block)
            normalized_block["text"] = normalized_text
            normalized_blocks.append(normalized_block)

        return normalized_blocks or None

    if content is None:
        return None

    normalized = str(content).strip()
    return normalized or None


def _normalize_messages_for_openai_api(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop empty messages and sanitize content for OpenAI-compatible APIs."""
    normalized_messages: list[dict[str, Any]] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue

        normalized_content = _normalize_message_content_for_openai_api(msg.get("content"))
        if normalized_content is None:
            continue

        normalized_message = dict(msg)
        normalized_message["content"] = normalized_content
        normalized_messages.append(normalized_message)

    if not normalized_messages:
        raise ValueError("No non-empty message content provided")

    return normalized_messages


def _check_lmstudio_available(url: str) -> bool:
    """Backward-compatible alias for the newer `_check_lm_studio_available` function.

    Older parts of the codebase call `_check_lmstudio_available` (no underscore
    between `lm` and `studio`) so keep a tiny wrapper here that delegates to the
    canonical implementation defined later in this module. This avoids import
    time IndentationError and keeps the two names consistent.
    """
    # Delegate to the canonical implementation which is defined below.
    try:
        return _check_lm_studio_available(url)
    except NameError:
        # If the canonical implementation isn't available for some reason,
        # perform a conservative HTTP ping.
        try:
            import urllib.error
            import urllib.request

            base_url = url.removesuffix("/v1")
            models_endpoint_url = base_url + "/v1/models"
            request = urllib.request.Request(models_endpoint_url, headers={"User-Agent": "QAI"})  # noqa: S310
            urllib.request.urlopen(request, timeout=1)  # noqa: S310 - configurable local endpoint
            return True
        except Exception:
            return False


@dataclass
class ProviderChoice:
    """Lightweight descriptor returned alongside a provider instance by ``detect_provider``.

    Attributes:
        name:  Canonical provider name (e.g. ``"azure"``, ``"openai"``,
               ``"lmstudio"``, ``"ollama"``, ``"local"``, ``"agi"``,
               ``"quantum"``, ``"lora"``).
        model: The model identifier or path that the provider will use.
    """

    name: str  # 'azure' | 'openai' | 'local'
    model: str


class BaseChatProvider:
    """Abstract base for all chat providers.

    Subclasses must implement ``complete()``.  Helper static methods for
    parsing OpenAI-style streaming and non-streaming responses are provided
    so concrete providers don't duplicate that logic.
    """

    def complete(self, messages: list[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        """Send *messages* to the backend and return the response.

        Args:
            messages: Conversation history as a list of ``{"role": …, "content": …}`` dicts.
            stream:   When ``True`` return a generator that yields string chunks;
                      when ``False`` return the full response as a single string.

        Raises:
            NotImplementedError: Subclasses must override this method.
        """
        raise NotImplementedError

    @staticmethod
    def _normalize_messages_for_api(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sanitize messages before forwarding them to external providers."""
        return _normalize_messages_for_openai_api(messages)

    @staticmethod
    def _handle_openai_streaming_response(response) -> Generator[str, None, None]:
        """Extract content from OpenAI-style streaming response.

        Common helper for OpenAI, LMStudio, and other OpenAI-compatible providers.
        Handles the standard streaming chunk format with resilient error handling.
        """
        for chunk in response:
            try:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
            except Exception:
                # Be resilient to SDK shape changes
                pass

    @staticmethod
    def _handle_openai_non_streaming_response(response) -> str:
        """Extract content from OpenAI-style non-streaming response.

        Common helper for OpenAI, LMStudio, and other OpenAI-compatible providers.
        Handles the standard completion format with resilient error handling.
        """
        try:
            return response.choices[0].message.content or ""
        except Exception:
            return ""


class LoraLocalProvider(BaseChatProvider):
    """Provider for local inference with LoRA adapters.

    If ML dependencies are unavailable in the current process (e.g.,
    Azure Functions worker without torch/transformers/peft), this provider
    falls back to a subprocess bridge that uses the workspace venv
    (./venv/Scripts/python.exe) to perform inference.
    """

    def __init__(
        self,
        adapter_dir: str,
        device: str = None,
        temperature: float = 0.7,
        max_new_tokens: int = 256,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
    ):
        """Initialize LoRA provider with enhanced generation parameters.

        Args:
            adapter_dir: Path to LoRA adapter
            device: Device for inference (cuda/cpu)
            temperature: Sampling temperature (higher = more random)
            max_new_tokens: Maximum tokens to generate
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            repetition_penalty: Penalty for repeating tokens
        """
        self.adapter_dir = Path(adapter_dir)
        self.use_subprocess = False
        self.bridge_python: str | None = None
        self.temperature = float(temperature)
        self.max_new_tokens = int(max_new_tokens)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.repetition_penalty = float(repetition_penalty)
        # Lazy import heavy deps on demand
        self._lazy_setup()
        if not self.use_subprocess:
            self.device = device or ("cuda" if self.torch.cuda.is_available() else "cpu")
            self.model, self.tokenizer = self._load_model_and_tokenizer()
        else:
            # In subprocess mode we keep state minimal here
            self.device = "cpu"

    def _load_model_and_tokenizer(self):
        # Detect adapter config
        import json as _json

        adapter_config_path = self.adapter_dir / "adapter_config.json"
        if not adapter_config_path.exists():
            raise RuntimeError(f"adapter_config.json not found in {self.adapter_dir}")
        with open(adapter_config_path, encoding="utf-8") as f:
            adapter_cfg = _json.load(f)
        base_model_id = adapter_cfg.get("base_model_name_or_path", "microsoft/Phi-3.5-mini-instruct")
        # Fallback mapping for Phi-3.6
        if base_model_id == "Phi-3.6-mini-instruct":
            base_model_id = "microsoft/Phi-3.5-mini-instruct"
        base_model = self.AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=(self.torch.float16 if self.device == "cuda" else self.torch.float32),
            device_map="auto" if self.device == "cuda" else None,
        )
        tokenizer_source = self.adapter_dir.parent / "tokenizer"
        if tokenizer_source.exists():
            tokenizer = self.AutoTokenizer.from_pretrained(tokenizer_source)
        else:
            tokenizer = self.AutoTokenizer.from_pretrained(base_model_id)
        model = self.PeftModel.from_pretrained(base_model, self.adapter_dir)
        model.eval()
        return model, tokenizer

    def complete(self, messages: list[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        if self.use_subprocess:
            response = self._complete_via_subprocess(messages)
            if not stream:
                return response

            def gen():
                for ch in response:
                    yield ch
                    time.sleep(0.002)

            return gen()
        # In-process inference path
        prompt = self._build_prompt(messages)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=True,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                repetition_penalty=self.repetition_penalty,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        response = self.tokenizer.decode(output[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True)
        if not stream:
            return response

        def gen():
            for ch in response:
                yield ch
                time.sleep(0.002)

        return gen()

    def _complete_via_subprocess(self, messages: list[RoleMessage]) -> str:
        if not self.bridge_python:
            raise RuntimeError("Subprocess bridge not configured for LoRA provider.")
        bridge_script = Path(__file__).resolve().parent / "lora_infer_bridge.py"
        if not bridge_script.exists():
            raise RuntimeError(f"Bridge script not found at {bridge_script}")
        payload = {
            "adapter_dir": str(self.adapter_dir),
            "messages": messages,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
        }
        try:
            proc = subprocess.run(
                [self.bridge_python, "-u", str(bridge_script)],
                input=_json.dumps(payload).encode("utf-8"),
                capture_output=True,
                check=False,
                timeout=300,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to launch LoRA bridge: {e}") from e
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="ignore")
            stdout = proc.stdout.decode("utf-8", errors="ignore")
            msg = stderr.strip() or stdout.strip() or f"exit code {proc.returncode}"
            # Truncate very long errors but keep start and end
            if len(msg) > 1000:
                msg = msg[:500] + "\n...\n" + msg[-500:]
            raise RuntimeError(f"LoRA bridge failed: {msg}")
        text = proc.stdout.decode("utf-8", errors="ignore").strip()
        return text

    def _build_prompt(self, messages: list[RoleMessage]) -> str:
        """Build prompt string from messages.

        Uses list join instead of string += for O(n) instead of O(n²) complexity.
        """
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"[SYSTEM] {content}")
            elif role == "user":
                parts.append(f"User: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")

        # Build final prompt: messages joined by newlines, ending with "Assistant: "
        if parts:
            return "\n".join(parts) + "\nAssistant: "
        return "Assistant: "

    def _lazy_setup(self) -> None:
        """Import heavy dependencies lazily so that non-LoRA providers don't require them.

        If imports fail (common under Azure Functions without ML deps),
        configure a subprocess bridge to a venv Python.
        """
        try:
            import torch as _torch  # type: ignore
            from transformers import AutoModelForCausalLM as _AM  # type: ignore
            from transformers import AutoTokenizer as _AT

            try:
                from peft import PeftModel as _PM  # type: ignore
            except Exception:
                # peft missing -> subprocess
                self._configure_subprocess_bridge()
                return
        except Exception:
            # Any import failure -> subprocess
            self._configure_subprocess_bridge()
            return
        # Store on self for in-process inference
        self.torch = _torch
        self.AutoModelForCausalLM = _AM
        self.AutoTokenizer = _AT
        self.PeftModel = _PM

    def _configure_subprocess_bridge(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        venv_python = repo_root / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            self.bridge_python = str(venv_python)
            self.use_subprocess = True
        else:
            raise RuntimeError(
                "Missing dependencies for LoRA provider and no venv found. "
                "Create ./venv and install 'torch', 'transformers', 'peft'."
            )


class LocalEchoProvider(BaseChatProvider):
    """A simple offline provider that mimics a helpful assistant.
    Useful for smoke tests and environments without keys.

    This provider generates contextually aware responses without requiring
    external API calls, making it ideal for testing, development, and
    offline scenarios.
    """

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self._response_templates = self._initialize_templates()

    def _initialize_templates(self) -> dict[str, list[str]]:
        """Initialize response templates categorized by intent."""
        return {
            "greeting": [
                "Hello! I'm here to help. What would you like to know?",
                "Hi there! How can I assist you today?",
                "Greetings! I'm ready to help with your questions.",
            ],
            "question": [
                "That's an interesting question. Here's my take:",
                "Let me help you with that:",
                "Good question! Here's what I think:",
                "Based on your question, here's my understanding:",
            ],
            "code": [
                "For coding tasks, I'd suggest:",
                "Here's a technical approach:",
                "From a development perspective:",
                "For this programming challenge:",
            ],
            "explanation": [
                "Let me break this down:",
                "Here's a clear explanation:",
                "To explain this simply:",
                "In other words:",
            ],
            "generic": [
                "Here's a concise take:",
                "Quick thoughts:",
                "A few ideas:",
                "My perspective:",
                "Summary:",
            ],
        }

    def _detect_intent(self, text: str) -> str:
        """Detect the intent of the user message."""
        lower_text = text.lower()

        # Check for greetings
        if any(word in lower_text for word in ["hello", "hi", "hey", "greetings"]) and len(text) < 50:
            return "greeting"

        # Check for coding-related queries
        if any(
            word in lower_text
            for word in [
                "code",
                "function",
                "class",
                "debug",
                "program",
                "script",
                "algorithm",
            ]
        ):
            return "code"

        # Check for explanation requests
        if any(
            word in lower_text
            for word in [
                "explain",
                "what is",
                "what are",
                "how does",
                "describe",
                "tell me about",
            ]
        ):
            return "explanation"

        # Check for questions
        if any(word in lower_text for word in ["?", "how", "why", "when", "where", "who", "can you"]):
            return "question"

        return "generic"

    def _craft_autonomous_reply(self, messages: list[RoleMessage], last_user: str, turn_count: int) -> str:
        """Generate more useful offline output for autonomous CLI loops."""
        assistant_messages = [m["content"] for m in messages if m.get("role") == "assistant"]
        last_assistant = assistant_messages[-1] if assistant_messages else ""
        user_topics = [
            m["content"].strip() for m in messages if m.get("role") == "user" and m.get("content", "").strip()
        ]
        topic = user_topics[0][:120].rstrip(".,?!") if user_topics else "the current task"

        if "message count exceeded limit" in last_assistant.lower():
            return (
                "Autonomous checkpoint:\n"
                "1. The conversation is getting long, so summarize the objective in one sentence.\n"
                "2. Keep only the latest constraints and the best next action.\n"
                "3. Continue with one concrete step instead of repeating the same prompt."
            )

        sequence = [
            (
                f"Autonomous plan for '{topic}':\n\n"
                "1. Define the concrete objective and success condition.\n"
                "2. Inspect the current inputs, dependencies, or repo context.\n"
                "3. Pick the smallest next action that creates evidence of progress."
            ),
            (
                f"Autonomous next step for '{topic}':\n\n"
                "- Gather one missing fact before changing direction.\n"
                "- Write down the current assumption you are relying on.\n"
                "- Execute a single focused action, then reassess."
            ),
            (
                f"Autonomous review for '{topic}':\n\n"
                "- What changed since the previous turn?\n"
                "- What is still blocked or uncertain?\n"
                "- What is the highest-value follow-up action right now?"
            ),
            (
                f"Autonomous refinement for '{topic}':\n\n"
                "1. Remove repetition.\n"
                "2. Convert vague goals into one measurable outcome.\n"
                "3. Continue with a concrete command, edit, or validation step."
            ),
        ]
        return sequence[(turn_count - 1) % len(sequence)]

    def _craft_reply(self, messages: list[RoleMessage]) -> str:
        """Generate a contextually appropriate response.

        The local echo provider has no real model, so responses are
        rule-based — but they should at least be informative and
        actionable rather than meaninglessly rephrasing the user's input.
        """
        last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "").strip()

        if not last_user:
            return (
                "Hi! I'm running in offline mode (no API keys configured). "
                "I can still help with Aria commands, answer simple questions, "
                "or assist with code structure. What would you like to do?"
            )

        intent = self._detect_intent(last_user)
        lower = last_user.lower()
        turn_count = sum(1 for m in messages if m.get("role") == "user")

        if (
            "start working autonomously" in lower
            or "continue autonomously" in lower
            or "without waiting for user input" in lower
            or "choose the next useful step yourself" in lower
        ):
            return self._craft_autonomous_reply(messages, last_user, turn_count)

        # --- Arithmetic (real, deterministic answers even offline) ---
        calc_result = evaluate_arithmetic(last_user)
        if calc_result is not None:
            expression = normalize_expression(last_user) or last_user.strip().rstrip("?.! ")
            return f"{expression} = {calc_result}"

        if is_summary_request(last_user):
            summary = summarize_text(last_user, max_sentences=3, max_chars=420)
            return (
                "Local summary:\n"
                f"{summary}\n\n"
                "Offline extractive mode is active. Configure a live provider for abstractive summaries."
            )

        # --- Greetings ---
        if intent == "greeting":
            greetings = [
                "Hello! I'm running in local offline mode — no external model is active. "
                "Try `--provider azure`, `--provider openai`, or `--provider lmstudio` for a full AI response.",
                "Hi there! Offline mode is active. Set AZURE_OPENAI_API_KEY or OPENAI_API_KEY to enable a real AI provider.",
                "Hey! Running without a live model right now. I can still help with Aria commands and simple tasks.",
            ]
            return self.rng.choice(greetings)

        # --- Aria movement commands ---
        aria_keywords = {
            "left": "Moving Aria to the left. [aria:walk:left]",
            "right": "Moving Aria to the right. [aria:walk:right]",
            "jump": "Aria jumps! [aria:jump]",
            "wave": "Aria waves hello! [aria:wave]",
            "dance": "Aria starts dancing! [aria:dance]",
            "idle": "Aria returns to idle. [aria:idle]",
        }
        for keyword, response in aria_keywords.items():
            if keyword in lower:
                return response

        # --- Coding requests ---
        if intent == "code":
            topic = last_user[:80].rstrip(".,?!")
            suggestions = [
                f"For '{topic}', here's one approach:\n\n"
                "1. Identify inputs, outputs, and edge cases first.\n"
                "2. Write a minimal working version before optimising.\n"
                "3. Add error handling for external calls (I/O, network, parsing).\n\n"
                "Enable a real provider (e.g. `--provider openai`) for generated code.",
                f"Coding tip for '{topic}':\n\n"
                "- Keep functions small and focused on one task.\n"
                "- Use type hints for clarity and static analysis.\n"
                "- Write a unit test for each edge case you can think of.\n\n"
                "Connect a live model for actual code generation.",
            ]
            return self.rng.choice(suggestions)

        # --- Explanation requests ---
        if intent == "explanation":
            topic = last_user[:80].rstrip(".,?!")
            return (
                f"I'm in offline mode, so I can't give a full explanation of '{topic}'. "
                "Here's what I'd suggest:\n\n"
                "1. Check the official docs or a trusted reference.\n"
                "2. Ask again with `--provider azure` or `--provider openai` for a detailed answer.\n"
                "3. Or try `--provider agi` for structured chain-of-thought reasoning."
            )

        # --- Questions ---
        if intent == "question":
            closers = [
                "Switch to a live provider for a detailed answer.",
                "Try `--provider openai` or `--provider azure` for a real response.",
                "Use `--provider agi` for structured reasoning on complex questions.",
            ]
            return (
                f"Good question! Unfortunately I'm in local echo mode and can't look things up. "
                f"{self.rng.choice(closers)}"
            )

        # --- Multi-turn acknowledgement ---
        if turn_count > 3:
            follow_ups = [
                "I'm still in offline mode — I can only give canned responses. "
                "Configure a provider to continue this conversation meaningfully.",
                "Thanks for staying in the conversation! A live provider would give you much better answers here.",
            ]
            return self.rng.choice(follow_ups)

        # --- Generic fallback ---
        generic = [
            "I'm running in local fallback mode. "
            "Set AZURE_OPENAI_API_KEY, OPENAI_API_KEY, or start LM Studio / Ollama to enable full AI responses.",
            "Offline mode active. I can process Aria commands but can't generate AI responses without a configured provider.",
            "No live model detected. Run with `--provider lmstudio` (LM Studio running locally), "
            "`--provider ollama`, `--provider openai`, or `--provider azure`.",
        ]
        return self.rng.choice(generic)

    def complete(self, messages: list[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        text = self._craft_reply(messages)
        if not stream:
            return text

        def gen() -> Generator[str, None, None]:
            for ch in text:
                yield ch
                # Tiny delay to simulate streaming; keep very small
                time.sleep(0.002)

        return gen()


class OpenAIProvider(BaseChatProvider):
    """Provider for the OpenAI public API (chat completions).

    Requires the ``openai`` package and a valid ``OPENAI_API_KEY`` environment
    variable (or an explicit *api_key* argument).  Supports both streaming and
    non-streaming completions, and retries transient 429 rate-limit errors with
    exponential back-off.
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int | None = None,
    ):
        """Initialize the OpenAI provider.

        Args:
            model: Model ID (e.g. ``"gpt-4o-mini"``).
            api_key: OpenAI API key.  Falls back to the ``OPENAI_API_KEY``
                environment variable when ``None``.
            temperature: Sampling temperature in ``[0, 2]``.  Higher values
                produce more varied output.
            max_output_tokens: Maximum tokens the model may generate.
                ``None`` uses the model's own default.
        """
        if OpenAI is None:
            raise RuntimeError("openai package not installed. Install 'openai' to use this provider.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def complete(self, messages: list[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        """Complete with OpenAI and handle quota/rate-limit errors gracefully.

        Behaviour mirrors AzureOpenAIProvider:
          - Quota/billing errors → friendly string or single-chunk generator.
          - Transient 429 errors → small retry with back-off.
          - Mid-stream errors → yielded friendly/error token instead of raising.
        """

        normalized_messages = self._normalize_messages_for_api(messages)

        def _attempt_create(**kwargs):
            max_retries = 3
            base_backoff = 0.4
            attempt = 0
            while True:
                try:
                    return self.client.chat.completions.create(**kwargs)
                except Exception as e:
                    if is_quota_error(e):
                        raise
                    if is_transient_rate_error(e) and attempt < max_retries:
                        sleep_time = base_backoff * (2**attempt)
                        _LOGGER.info(
                            "OpenAI rate-limit, retrying in %.2fs (attempt %d)",
                            sleep_time,
                            attempt + 1,
                        )
                        time.sleep(sleep_time)
                        attempt += 1
                        continue
                    raise

        try:
            resp = _attempt_create(
                model=self.model,
                messages=normalized_messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=stream,
            )
        except Exception as e:
            if is_quota_error(e):
                friendly = format_quota_message(e, service_name="OpenAI")
                if stream:

                    def _gen_quota_err() -> Generator[str, None, None]:
                        yield friendly

                    return _gen_quota_err()
                return friendly
            raise

        if stream:

            def _gen() -> Generator[str, None, None]:
                try:
                    for chunk in resp:
                        try:
                            delta = chunk.choices[0].delta
                            if delta and delta.content:
                                yield delta.content
                        except Exception:
                            continue
                except Exception as exc:
                    if is_quota_error(exc):
                        yield format_quota_message(exc, service_name="OpenAI")
                    else:
                        yield f"[OpenAI error: {str(exc)}]"

            return _gen()
        else:
            try:
                return resp.choices[0].message.content or ""
            except Exception:
                return ""


class LMStudioProvider(BaseChatProvider):
    """Provider for LM Studio local server (compatible with OpenAI API)."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234/v1",
        model: str = "local-model",
        temperature: float = 0.7,
        max_output_tokens: int | None = None,
    ):
        """Initialize the LM Studio provider.

        Args:
            base_url: Base URL of the LM Studio local server.  Defaults to
                the standard LM Studio port.  Override with ``LMSTUDIO_BASE_URL``.
            model: Model name as reported by the LM Studio server.  Override
                with ``LMSTUDIO_MODEL``.
            temperature: Sampling temperature in ``[0, 2]``.
            max_output_tokens: Maximum tokens to generate.

        The provider uses the official ``openai`` SDK when available and falls
        back to a pure-HTTP implementation (``urllib.request``) in environments
        where the SDK is not installed.  An API token is read from
        ``LM_API_TOKEN`` / ``LMSTUDIO_API_KEY`` / ``LMSTUDIO_TOKEN`` /
        ``LMSTUDIO_API_TOKEN`` when the LM Studio server requires authentication.
        """
        # Prefer official OpenAI SDK when available, but support a pure-HTTP
        # fallback so LM Studio remains usable in minimal environments.
        self.client = None
        if OpenAI is not None:
            # Newer LM Studio server configurations can require API token auth.
            # Keep backward compatibility by using the legacy placeholder key when
            # no token env var is provided.
            lmstudio_api_key = _get_lmstudio_api_key() or "lm-studio"
            self.client = OpenAI(
                base_url=base_url,
                api_key=lmstudio_api_key,
            )
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.base_url = base_url

    def _chat_completions_url(self) -> str:
        return self.base_url.rstrip("/") + "/chat/completions"

    def _complete_via_http(self, messages: list[RoleMessage], stream: bool) -> Iterable[str] | str:
        import json
        import urllib.request

        timeout_seconds = _get_bounded_timeout_env("LMSTUDIO_HTTP_TIMEOUT", 60.0, minimum=1.0, maximum=600.0)

        normalized_messages = self._normalize_messages_for_api(messages)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": normalized_messages,
            "temperature": self.temperature,
            "stream": stream,
        }
        if self.max_output_tokens is not None:
            payload["max_tokens"] = self.max_output_tokens

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "QAI",
        }
        lmstudio_api_key = _get_lmstudio_api_key()
        if lmstudio_api_key:
            headers["Authorization"] = f"Bearer {lmstudio_api_key}"

        req = urllib.request.Request(  # noqa: S310 - URL from configurable local endpoint
            self._chat_completions_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        if stream:

            def _gen() -> Generator[str, None, None]:
                with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:  # noqa: S310 - local configurable endpoint
                    for raw_line in resp:
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = _json.loads(data)
                            delta = obj.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                        except Exception:
                            continue

            return _gen()

        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:  # noqa: S310 - local configurable endpoint
            body = resp.read().decode("utf-8", errors="replace")
        obj = _json.loads(body)
        return obj.get("choices", [{}])[0].get("message", {}).get("content", "") or ""

    def complete(self, messages: list[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        try:
            if self.client is None:
                return self._complete_via_http(messages, stream)

            normalized_messages = self._normalize_messages_for_api(messages)
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=normalized_messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=stream,
            )

            if stream:
                return self._handle_openai_streaming_response(resp)
            else:
                return self._handle_openai_non_streaming_response(resp)
        except Exception as e:
            # Provide helpful error messages for common issues
            error_msg = str(e).lower()

            if (
                "connection" in error_msg
                or "refused" in error_msg
                or "timeout" in error_msg
                or "timed out" in error_msg
            ):
                suggestion = (
                    f"❌ Cannot connect to LM Studio at {self.base_url}\n\n"
                    f"Troubleshooting steps:\n"
                    f"1. Make sure LM Studio is running\n"
                    f"2. Check that the local server is started in LM Studio\n"
                    f"3. Verify the server is running on {self.base_url}\n"
                    f"4. Check your firewall settings\n\n"
                    f"The request may have timed out or the server may be unreachable.\n\n"
                    f"Set LMSTUDIO_BASE_URL environment variable if using a different address."
                )
                if stream:

                    def gen_err() -> Generator[str, None, None]:
                        yield suggestion

                    return gen_err()
                return suggestion

            if "model" in error_msg and ("not found" in error_msg or "does not exist" in error_msg):
                suggestion = (
                    f"❌ Model '{self.model}' not found in LM Studio.\n\n"
                    f"Troubleshooting steps:\n"
                    f"1. Check that a model is loaded in LM Studio\n"
                    f"2. Use --model flag to specify the correct model name\n"
                    f"3. Set LMSTUDIO_MODEL environment variable\n\n"
                    f"The model name should match what's shown in LM Studio's server panel."
                )
                if stream:

                    def gen_err() -> Generator[str, None, None]:
                        yield suggestion

                    return gen_err()
                return suggestion

            if "no models loaded" in error_msg or "please load a model" in error_msg:
                suggestion = (
                    f"❌ LM Studio is reachable but no model is currently loaded.\n\n"
                    f"Troubleshooting steps:\n"
                    f"1. Open LM Studio and load a model in the Developer/Server page\n"
                    f"2. Confirm the model matches LMSTUDIO_MODEL (currently '{self.model}')\n"
                    f"3. Re-run after the model shows as loaded in the server panel\n\n"
                    f"If you changed models recently, restart the local server to refresh the load."
                )
                if stream:

                    def gen_err() -> Generator[str, None, None]:
                        yield suggestion

                    return gen_err()
                return suggestion

            if "invalid_api_key" in error_msg or "api token is required" in error_msg:
                suggestion = (
                    f"❌ LM Studio at {self.base_url} requires API token authentication.\n\n"
                    f"Troubleshooting steps:\n"
                    f"1. Export one of: LM_API_TOKEN, LMSTUDIO_API_KEY, LMSTUDIO_TOKEN, LMSTUDIO_API_TOKEN\n"
                    f"2. Ensure token matches LM Studio server configuration\n"
                    f"3. Re-run with --provider lmstudio\n\n"
                    f"Example:\n"
                    f"export LM_API_TOKEN='<your-token>'"
                )
                if stream:

                    def gen_err() -> Generator[str, None, None]:
                        yield suggestion

                    return gen_err()
                return suggestion

            # Re-raise unexpected errors
            raise


class OllamaProvider(BaseChatProvider):
    """Provider for Ollama local server (compatible with OpenAI API).

    Ollama is a popular local LLM server that supports models like Llama, Mistral,
    CodeLlama, and many others. It provides an OpenAI-compatible API.

    Default endpoint: http://127.0.0.1:11434/v1
    Configure via OLLAMA_BASE_URL environment variable.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434/v1",
        model: str = "llama3.2",
        temperature: float = 0.7,
        max_output_tokens: int | None = None,
    ):
        """Initialize the Ollama provider.

        Args:
            base_url: Base URL of the Ollama OpenAI-compatible endpoint.
                Defaults to the standard Ollama port.  Override with
                ``OLLAMA_BASE_URL``.
            model: Model tag as known to Ollama (e.g. ``"llama3.2"``,
                ``"codellama:latest"``).  Override with ``OLLAMA_MODEL``.
            temperature: Sampling temperature in ``[0, 2]``.
            max_output_tokens: Maximum tokens to generate.

        Raises:
            RuntimeError: If the ``openai`` package is not installed.
        """
        if OpenAI is None:
            raise RuntimeError("openai package not installed. Install 'openai' to use this provider.")
        # Ollama doesn't require real key
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.base_url = base_url

    def complete(self, messages: list[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        try:
            normalized_messages = self._normalize_messages_for_api(messages)
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=normalized_messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=stream,
            )

            if stream:
                return self._handle_openai_streaming_response(resp)
            else:
                return self._handle_openai_non_streaming_response(resp)
        except Exception as e:
            # Provide helpful error messages for common Ollama issues
            error_msg = str(e).lower()

            if "connection" in error_msg or "refused" in error_msg or "timeout" in error_msg:
                suggestion = (
                    f"❌ Cannot connect to Ollama at {self.base_url}\n\n"
                    f"Troubleshooting steps:\n"
                    f"1. Make sure Ollama is installed and running\n"
                    f"   - Install: https://ollama.ai/download\n"
                    f"   - Start: 'ollama serve' (or it may start automatically)\n"
                    f"2. Verify Ollama is listening on {self.base_url}\n"
                    f"3. Check your firewall settings\n\n"
                    f"Set OLLAMA_BASE_URL environment variable if using a different address."
                )
                if stream:

                    def gen_err() -> Generator[str, None, None]:
                        yield suggestion

                    return gen_err()
                return suggestion

            if "model" in error_msg and (
                "not found" in error_msg or "does not exist" in error_msg or "not available" in error_msg
            ):
                suggestion = (
                    f"❌ Model '{self.model}' not found in Ollama.\n\n"
                    f"Troubleshooting steps:\n"
                    f"1. Pull the model first:\n"
                    f"   ollama pull {self.model}\n\n"
                    f"2. List available models:\n"
                    f"   ollama list\n\n"
                    f"3. Popular models to try:\n"
                    f"   - llama2:latest (7B general purpose)\n"
                    f"   - codellama:latest (7B for coding)\n"
                    f"   - mistral:latest (7B high quality)\n"
                    f"   - llama3.2:latest (3B latest from Meta)\n\n"
                    f"Use --model flag or set OLLAMA_MODEL environment variable."
                )
                if stream:

                    def gen_err() -> Generator[str, None, None]:
                        yield suggestion

                    return gen_err()
                return suggestion

            # Re-raise unexpected errors
            raise


class GroqProvider(BaseChatProvider):
    """Provider for the Groq cloud API (OpenAI-compatible endpoint).

    Groq provides fast inference for open models (Llama, Mixtral, Gemma, etc.)
    via an OpenAI-compatible REST API.  Requires the ``openai`` package and a
    valid ``GROQ_API_KEY`` environment variable (or explicit *api_key* argument).

    Default endpoint: https://api.groq.com/openai/v1
    Configure via GROQ_BASE_URL environment variable.
    """

    def __init__(
        self,
        model: str = "llama-3.1-8b-instant",
        api_key: str | None = None,
        base_url: str = "https://api.groq.com/openai/v1",
        temperature: float = 0.7,
        max_output_tokens: int | None = None,
    ):
        """Initialize the Groq provider.

        Args:
            model: Groq model ID (e.g. ``"llama-3.1-8b-instant"``,
                ``"mixtral-8x7b-32768"``).  Override with ``GROQ_MODEL``.
            api_key: Groq API key.  Falls back to the ``GROQ_API_KEY``
                environment variable when ``None``.
            base_url: Groq OpenAI-compatible endpoint.  Defaults to the
                standard Groq endpoint.  Override with ``GROQ_BASE_URL``.
            temperature: Sampling temperature in ``[0, 2]``.
            max_output_tokens: Maximum tokens to generate.

        Raises:
            RuntimeError: If the ``openai`` package is not installed.
        """
        if OpenAI is None:
            raise RuntimeError("openai package not installed. Install 'openai' to use this provider.")
        resolved_key = api_key or os.getenv("GROQ_API_KEY")
        if not resolved_key:
            raise RuntimeError("Groq provider requires GROQ_API_KEY to be set.")
        self.client = OpenAI(base_url=base_url, api_key=resolved_key)
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.base_url = base_url

    def complete(self, messages: list[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        """Complete using Groq and surface friendly error messages for common failures."""
        try:
            normalized_messages = self._normalize_messages_for_api(messages)
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=normalized_messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=stream,
            )

            if stream:
                return self._handle_openai_streaming_response(resp)
            else:
                return self._handle_openai_non_streaming_response(resp)
        except Exception as e:
            error_msg = str(e).lower()

            if "connection" in error_msg or "refused" in error_msg or "timeout" in error_msg:
                suggestion = (
                    f"❌ Cannot connect to Groq at {self.base_url}\n\n"
                    f"Troubleshooting steps:\n"
                    f"1. Check your internet connection\n"
                    f"2. Verify GROQ_BASE_URL is correct (default: https://api.groq.com/openai/v1)\n"
                    f"3. Check https://status.groq.com for service status\n\n"
                    f"Set GROQ_BASE_URL environment variable if using a custom endpoint."
                )
                if stream:

                    def gen_conn_err() -> Generator[str, None, None]:
                        yield suggestion

                    return gen_conn_err()
                return suggestion

            if "invalid_api_key" in error_msg or "authentication" in error_msg or "401" in error_msg:
                suggestion = (
                    "❌ Groq authentication failed.\n\n"
                    "Troubleshooting steps:\n"
                    "1. Check that GROQ_API_KEY is set and valid\n"
                    "2. Get a key at https://console.groq.com/keys\n"
                    "3. Re-run with --provider groq\n\n"
                    "Example:\n"
                    "export GROQ_API_KEY='<your-key>'"
                )
                if stream:

                    def gen_auth_err() -> Generator[str, None, None]:
                        yield suggestion

                    return gen_auth_err()
                return suggestion

            if "model" in error_msg and ("not found" in error_msg or "does not exist" in error_msg):
                suggestion = (
                    f"❌ Model '{self.model}' not found on Groq.\n\n"
                    f"Troubleshooting steps:\n"
                    f"1. Check available models at https://console.groq.com/docs/models\n"
                    f"2. Use --model flag to specify a valid model name\n"
                    f"3. Set GROQ_MODEL environment variable\n\n"
                    f"Popular models: llama-3.1-8b-instant, llama-3.3-70b-versatile, mixtral-8x7b-32768"
                )
                if stream:

                    def gen_model_err() -> Generator[str, None, None]:
                        yield suggestion

                    return gen_model_err()
                return suggestion

            # Re-raise unexpected errors
            raise


class AzureOpenAIProvider(BaseChatProvider):
    """Provider for Azure-hosted OpenAI deployments.

    Requires the ``openai`` package.  Authentication is via an API key; the
    endpoint and deployment name must be supplied explicitly (or read from
    ``AZURE_OPENAI_ENDPOINT`` / ``AZURE_OPENAI_DEPLOYMENT`` env vars by
    :func:`detect_provider`).  Retries transient 429 errors with jittered
    exponential back-off, and converts quota/billing errors into friendly
    string messages rather than raising exceptions.
    """

    def __init__(
        self,
        deployment: str,
        endpoint: str,
        api_key: str,
        api_version: str = "2024-08-01-preview",
        temperature: float = 0.7,
        max_output_tokens: int | None = None,
    ):
        """Initialize the Azure OpenAI provider.

        Args:
            deployment: Azure deployment name (used as the ``model`` parameter
                in API calls).
            endpoint: Azure OpenAI resource endpoint URL (e.g.
                ``"https://<resource>.openai.azure.com"``).
            api_key: Azure OpenAI API key.
            api_version: REST API version string.  Defaults to the latest
                stable preview.
            temperature: Sampling temperature in ``[0, 2]``.
            max_output_tokens: Maximum tokens the model may generate.
        """
        if AzureOpenAI is None:
            raise RuntimeError("openai package not installed. Install 'openai' to use this provider.")
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint,
        )
        self.deployment = deployment
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def complete(self, messages: list[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        """Complete with Azure OpenAI and handle quota/rate-limit errors gracefully.

        Behavior:
          - If a quota/premium allowance error is detected, return a friendly
            message instead of raising an exception.
          - Retry transient rate-limit style errors a small number of times with
            exponential backoff.

        Returns either a string (non-stream) or a generator yielding string chunks.
        """

        normalized_messages = self._normalize_messages_for_api(messages)

        # Internal helper: attempt the SDK call with small retry/backoff for
        # transient rate-limit style errors. If we detect a quota/premium error
        # we return the exception directly for caller to handle.
        def _attempt_create(**kwargs):
            max_retries = 3
            base_backoff = 0.4
            attempt = 0
            while True:
                try:
                    return self.client.chat.completions.create(**kwargs)
                except Exception as e:  # pragma: no cover - depends on runtime
                    # If this looks like a quota/premium allowance error, bail out
                    if is_quota_error(e):
                        raise
                    # Retry transient rate-limit errors a few times
                    if is_transient_rate_error(e) and attempt < max_retries:
                        sleep_time = base_backoff * (2**attempt)
                        jitter = min(sleep_time * 0.1, 0.5)
                        import time

                        _LOGGER.info(
                            "Azure rate-limit detected, retrying in %.2fs (attempt %d)",
                            sleep_time + jitter,
                            attempt + 1,
                        )
                        time.sleep(sleep_time + jitter)
                        attempt += 1
                        continue
                    # Propagate other exceptions
                    raise

        try:
            resp = _attempt_create(
                model=self.deployment,  # In Azure, 'model' is your deployment name
                messages=normalized_messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=stream,
            )
        except Exception as e:
            # If quota/premium, return a friendly message instead of bubbling an
            # exception to callers (better UX for local & CLI users)
            if is_quota_error(e):
                friendly = format_quota_message(e, service_name="Azure OpenAI")
                if stream:

                    def gen_err() -> Generator[str, None, None]:
                        yield friendly

                    return gen_err()
                return friendly
            # Not a quota error -> re-raise so upstream can observe generic failures
            raise

        if stream:

            def gen() -> Generator[str, None, None]:
                # resp can be an iterator/generator from the SDK. We iterate and
                # guard against runtime errors that may occur during streaming.
                try:
                    for chunk in resp:
                        try:
                            delta = chunk.choices[0].delta
                            if delta and delta.content:
                                yield delta.content
                        except Exception:
                            # Resilient: skip unexpected chunk shapes
                            continue
                except Exception as e:
                    # Catch runtime errors during iteration and turn them into
                    # a short user-friendly message (quota or otherwise).
                    if is_quota_error(e):
                        yield format_quota_message(e, service_name="Azure OpenAI")
                    else:
                        yield f"[AzureOpenAI error: {str(e)}]"

            return gen()

        else:
            try:
                return resp.choices[0].message.content or ""
            except Exception:
                return ""


def _check_lm_studio_available(server_url: str) -> bool:
    """Check if LM Studio server is available at the given URL.

    Uses a thread-safe cache to avoid repeated HTTP requests within the TTL period.
    The HTTP request is performed outside the lock to avoid blocking other threads.

    Args:
        server_url: Base URL for LM Studio API (e.g., "http://127.0.0.1:1234/v1")

    Returns:
        True if LM Studio is available, False otherwise.
    """
    # Check cache under lock
    with _lm_studio_cache_lock:
        current_time = time.time()
        if (
            _lm_studio_availability_cache["available"] is not None
            and _lm_studio_availability_cache["url"] == server_url
            and (current_time - _lm_studio_availability_cache["checked_at"]) < _LM_STUDIO_CACHE_TTL_SECONDS
        ):
            return _lm_studio_availability_cache["available"]

    # Perform HTTP check outside lock to avoid blocking other threads
    is_available = False
    lmstudio_api_key = _get_lmstudio_api_key()
    healthcheck_timeout = _get_bounded_timeout_env("LMSTUDIO_HEALTHCHECK_TIMEOUT", 1.0, minimum=0.1, maximum=30.0)
    try:
        import urllib.error
        import urllib.request

        # Remove trailing /v1 if present, then append /v1/models
        base_url = server_url.removesuffix("/v1")
        models_endpoint_url = base_url + "/v1/models"
        headers = {"User-Agent": "QAI"}
        if lmstudio_api_key:
            headers["Authorization"] = f"Bearer {lmstudio_api_key}"
        request = urllib.request.Request(models_endpoint_url, headers=headers)  # noqa: S310
        urllib.request.urlopen(request, timeout=healthcheck_timeout)  # noqa: S310 - configurable local endpoint
        is_available = True
    except urllib.error.HTTPError as exc:
        # Endpoint is reachable but auth failed: count as available only when
        # caller configured a token (possibly wrong/expired).
        if exc.code in (401, 403) and bool(lmstudio_api_key):
            is_available = True
        else:
            is_available = False
    except Exception:
        is_available = False

    # Update cache under lock
    with _lm_studio_cache_lock:
        _lm_studio_availability_cache["available"] = is_available
        _lm_studio_availability_cache["checked_at"] = time.time()
        _lm_studio_availability_cache["url"] = server_url

    return is_available


def _check_ollama_available(server_url: str) -> bool:
    """Check if Ollama server is available at the given URL.

    Uses a thread-safe cache to avoid repeated HTTP requests within the TTL period.
    The HTTP request is performed outside the lock to avoid blocking other threads.

    Args:
        server_url: Base URL for Ollama API (e.g., "http://127.0.0.1:11434/v1")

    Returns:
        True if Ollama is available, False otherwise.
    """
    # Check cache under lock
    with _ollama_cache_lock:
        current_time = time.time()
        if (
            _ollama_availability_cache["available"] is not None
            and _ollama_availability_cache["url"] == server_url
            and (current_time - _ollama_availability_cache["checked_at"]) < _OLLAMA_CACHE_TTL_SECONDS
        ):
            return _ollama_availability_cache["available"]

    # Perform HTTP check outside lock to avoid blocking other threads
    is_available = False
    try:
        import urllib.error
        import urllib.request

        # Remove trailing /v1 if present, then try /api/tags endpoint (Ollama-specific)
        base_url = server_url.removesuffix("/v1")
        # Ollama uses /api/tags to list models
        tags_endpoint_url = base_url + "/api/tags"
        request = urllib.request.Request(tags_endpoint_url, headers={"User-Agent": "QAI"})  # noqa: S310
        urllib.request.urlopen(request, timeout=1)  # noqa: S310 - configurable local endpoint
        is_available = True
    except Exception:
        # Fallback: try OpenAI-compatible /v1/models endpoint
        try:
            import urllib.error
            import urllib.request

            base_url = server_url.removesuffix("/v1")
            models_endpoint_url = base_url + "/v1/models"
            request = urllib.request.Request(models_endpoint_url, headers={"User-Agent": "QAI"})  # noqa: S310
            urllib.request.urlopen(request, timeout=1)  # noqa: S310 - configurable local endpoint
            is_available = True
        except Exception:
            is_available = False

    # Update cache under lock
    with _ollama_cache_lock:
        _ollama_availability_cache["available"] = is_available
        _ollama_availability_cache["checked_at"] = time.time()
        _ollama_availability_cache["url"] = server_url

    return is_available


def _check_groq_available(server_url: str) -> bool:
    """Check if the Groq API is reachable with the configured API key.

    Uses a thread-safe cache to avoid repeated HTTP requests within the TTL period.

    Args:
        server_url: Base URL for Groq OpenAI-compatible API (e.g.,
            ``"https://api.groq.com/openai/v1"``).

    Returns:
        True if Groq is reachable and the API key is accepted, False otherwise.
    """
    # Check cache under lock
    with _groq_cache_lock:
        current_time = time.time()
        if (
            _groq_availability_cache["available"] is not None
            and _groq_availability_cache["url"] == server_url
            and (current_time - _groq_availability_cache["checked_at"]) < _GROQ_CACHE_TTL_SECONDS
        ):
            return _groq_availability_cache["available"]

    # Perform HTTP check outside lock to avoid blocking other threads
    is_available = False
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        # No key configured — Groq cannot be available without authentication
        with _groq_cache_lock:
            _groq_availability_cache["available"] = False
            _groq_availability_cache["checked_at"] = time.time()
            _groq_availability_cache["url"] = server_url
        return False

    try:
        import urllib.error
        import urllib.request

        models_url = server_url.rstrip("/") + "/models"
        headers = {"User-Agent": "QAI", "Authorization": "Bearer " + groq_api_key}
        request = urllib.request.Request(models_url, headers=headers)
        urllib.request.urlopen(request, timeout=3)
        is_available = True
    except Exception:
        # Any error (connection refused, 401/403 invalid key, timeout) means
        # Groq is not available for auto-detection purposes.
        is_available = False

    # Update cache under lock
    with _groq_cache_lock:
        _groq_availability_cache["available"] = is_available
        _groq_availability_cache["checked_at"] = time.time()
        _groq_availability_cache["url"] = server_url

    return is_available


def _get_provider_detect_cache_ttl_seconds() -> float:
    """Resolve provider-detection cache TTL from env with safe bounds."""
    return _get_bounded_timeout_env(
        "QAI_PROVIDER_DETECT_CACHE_TTL",
        _PROVIDER_DETECT_CACHE_TTL_SECONDS,
        minimum=0.0,
        maximum=300.0,
    )


def _build_provider_detect_cache_key(
    provider_choice: str,
    model_override: str | None,
    temperature: float | None,
    max_output_tokens: int | None,
) -> tuple[Any, ...]:
    """Build a cache key for detect_provider with env-aware invalidation."""
    lmstudio_api_key = _get_lmstudio_api_key()
    return (
        provider_choice,
        model_override,
        temperature,
        max_output_tokens,
        os.getenv("CHAT_TEMPERATURE"),
        os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1"),
        os.getenv("LMSTUDIO_MODEL", "local-model"),
        bool(lmstudio_api_key),
        os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
        os.getenv("OLLAMA_MODEL", "llama3.2"),
        bool(os.getenv("AZURE_OPENAI_API_KEY")),
        os.getenv("AZURE_OPENAI_ENDPOINT"),
        os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        bool(os.getenv("OPENAI_API_KEY")),
        os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        bool(os.getenv("GROQ_API_KEY")),
        os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
    )


def _get_cached_provider_detection(cache_key: tuple[Any, ...]) -> tuple[BaseChatProvider, ProviderChoice] | None:
    """Return a cached detect_provider result when still fresh."""
    ttl_seconds = _get_provider_detect_cache_ttl_seconds()
    if ttl_seconds <= 0:
        return None

    with _provider_detection_cache_lock:
        entry = _provider_detection_cache.get(cache_key)
        if not entry:
            return None

        if (time.time() - float(entry.get("cached_at", 0.0))) >= ttl_seconds:
            _provider_detection_cache.pop(cache_key, None)
            return None

        provider = entry.get("provider")
        choice = entry.get("choice")
        if provider is None or choice is None:
            _provider_detection_cache.pop(cache_key, None)
            return None
        return provider, choice


def _set_cached_provider_detection(
    cache_key: tuple[Any, ...],
    provider: BaseChatProvider,
    choice: ProviderChoice,
) -> None:
    """Store detect_provider result in cache."""
    ttl_seconds = _get_provider_detect_cache_ttl_seconds()
    if ttl_seconds <= 0:
        return

    with _provider_detection_cache_lock:
        _provider_detection_cache[cache_key] = {
            "provider": provider,
            "choice": choice,
            "cached_at": time.time(),
        }


def _cache_provider_result(
    cache_key: tuple[Any, ...] | None,
    provider: BaseChatProvider,
    choice: ProviderChoice,
) -> tuple[BaseChatProvider, ProviderChoice]:
    """Cache helper for early-return branches in detect_provider."""
    if cache_key is not None:
        _set_cached_provider_detection(cache_key, provider, choice)
    return provider, choice


def detect_provider(
    explicit: str | None = None,
    model_override: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
) -> tuple[BaseChatProvider, ProviderChoice]:
    """Detect and instantiate the best available chat provider.

    Provider selection rules
    ------------------------
    1. **Explicit mode** — when *explicit* is set and not ``"auto"``:

       * ``"lmstudio"`` → :class:`LMStudioProvider` (requires server running).
       * ``"ollama"``   → :class:`OllamaProvider` (requires server running).
       * ``"azure"``    → :class:`AzureOpenAIProvider` (needs ``AZURE_OPENAI_API_KEY``,
         ``AZURE_OPENAI_ENDPOINT``, ``AZURE_OPENAI_DEPLOYMENT``).
       * ``"openai"``   → :class:`OpenAIProvider` (needs ``OPENAI_API_KEY``).
       * ``"groq"``     → :class:`GroqProvider` (needs ``GROQ_API_KEY``).
       * ``"local"``    → probes LM Studio then Ollama; falls back to
         :class:`LocalEchoProvider`.
       * ``"local_echo"`` / ``"local-echo"`` → :class:`LocalEchoProvider` directly.
       * ``"agi"``      → full AGI provider from ``agi_provider`` module; falls
         back to ``local_agi_provider.LocalAGIProvider`` when unavailable.
       * ``"quantum"``  → ``quantum_provider.create_quantum_llm_provider``; needs
         ``QAI_QUANTUM_MODEL_PATH`` or ``--model``.
       * ``"lora"``     → :class:`LoraLocalProvider`; requires *model_override* path.

    2. **Auto mode** (``explicit=None`` or ``"auto"``) — probes in order:
       LM Studio → Ollama → Azure OpenAI → OpenAI → Groq → :class:`LocalEchoProvider`.

    Results for the ``auto``, ``local``, ``lmstudio``, ``ollama``, ``azure``,
    ``openai``, and ``groq`` choices are cached for
    :data:`_PROVIDER_DETECT_CACHE_TTL_SECONDS` seconds (default 5 s) to avoid
    repeated availability probes on hot paths.
    Cache TTL can be tuned with ``QAI_PROVIDER_DETECT_CACHE_TTL``.

    Args:
        explicit: Provider name or ``None``/``"auto"`` for automatic detection.
            See :data:`_KNOWN_PROVIDER_CHOICES` for valid values.
        model_override: Override the model name/path selected by env vars.
        temperature: Sampling temperature.  ``None`` reads ``CHAT_TEMPERATURE``
            (default ``0.7``).
        max_output_tokens: Maximum tokens to generate.

    Returns:
        A ``(provider, choice)`` tuple where *choice* records the resolved
        provider name and model.

    Raises:
        ValueError: When *explicit* names an unknown provider.
        RuntimeError: When required configuration (API keys, server) is absent.
    """
    explicit_normalized = (explicit or "").strip().lower()
    force_local_echo = explicit_normalized in {"local_echo", "local-echo"}
    provider_choice = explicit_normalized or "auto"
    provider_choice = _PROVIDER_ALIASES.get(provider_choice, provider_choice)

    explicit_requested = bool(explicit and str(explicit).strip())
    if explicit_requested and provider_choice not in _KNOWN_PROVIDER_CHOICES:
        valid = ", ".join(sorted(_KNOWN_PROVIDER_CHOICES))
        raise ValueError(f"Unknown provider '{explicit}'. Valid providers: {valid}")

    # Cache only non-special providers. AGI/Quantum/LoRA can be stateful or
    # model-path specific and are intentionally resolved fresh.
    cache_key: tuple[Any, ...] | None = None
    if provider_choice in {"auto", "local", "lmstudio", "ollama", "azure", "openai", "groq"}:
        cache_key = _build_provider_detect_cache_key(provider_choice, model_override, temperature, max_output_tokens)
        cached = _get_cached_provider_detection(cache_key)
        if cached is not None:
            return cached

    # LM Studio config
    lm_studio_base_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    lm_studio_model_name = os.getenv("LMSTUDIO_MODEL", "local-model")

    # Ollama config
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
    ollama_model_name = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Groq config
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    groq_base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # AGI config - advanced reasoning capabilities
    if provider_choice == "agi":
        try:
            from agi_provider import create_agi_provider

            temperature_value = float(temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.7"))
            max_tokens_limit = int(max_output_tokens) if max_output_tokens is not None else 2048
            verbose = os.getenv("AGI_VERBOSE", "false").lower() == "true"
            provider, info = create_agi_provider(
                model=model_override,
                temperature=temperature_value,
                max_output_tokens=max_tokens_limit,
                verbose=verbose,
            )
            return provider, ProviderChoice(name=info.name, model=info.model)
        except Exception as import_error:
            # If agi_provider isn't available or fails to import for any reason,
            # fall back to a lightweight local AGI implementation that uses the
            # core deterministic LLM simulator. This keeps `--provider agi`
            # functional in minimal environments (CI, dev machines without
            # heavy deps).
            _LOGGER.warning(
                "AGI provider import failed (%s); falling back to LocalAGIProvider",
                import_error,
            )
            # Recompute settings (import may have failed before they were set).
            temperature_value = float(temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.7"))
            max_tokens_limit = int(max_output_tokens) if max_output_tokens is not None else 2048
            try:
                from local_agi_provider import LocalAGIProvider

                provider = LocalAGIProvider(
                    model=model_override or "local-llm",
                    temperature=temperature_value,
                    max_output_tokens=max_tokens_limit,
                )
                return provider, ProviderChoice(name="agi", model=getattr(provider, "model", "local-llm"))
            except Exception as e:
                raise RuntimeError(
                    f"AGI provider selected but agi_provider module not available and local fallback failed: {import_error} / {e}"
                ) from import_error

    if provider_choice == "quantum":
        try:
            from quantum_provider import create_quantum_llm_provider

            selected_model_path = (
                model_override or os.getenv("QAI_QUANTUM_MODEL_PATH") or os.getenv("QAI_QUANTUM_MODEL")
            )
            if not selected_model_path:
                raise RuntimeError(
                    "Quantum LLM provider requires a model path. Provide --model or set "
                    "QAI_QUANTUM_MODEL_PATH (or QAI_QUANTUM_MODEL).\n"
                    "Example: --provider quantum --model data_out/quantum_llm_training"
                )

            temperature_value = float(temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.8"))
            max_tokens_limit = int(max_output_tokens) if max_output_tokens is not None else 200

            provider, info = create_quantum_llm_provider(
                model_path=selected_model_path,
                temperature=temperature_value,
                max_output_tokens=max_tokens_limit,
            )
            return provider, ProviderChoice(name=info.name, model=info.model)
        except ImportError as import_error:
            raise RuntimeError(
                f"Quantum provider selected but quantum_provider module not available: {import_error}"
            ) from import_error

    if provider_choice == "lora":
        if not model_override:
            raise RuntimeError("LoRA provider selected but model path not provided.")
        temperature_value = float(temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.7"))
        max_new_tokens = int(max_output_tokens) if max_output_tokens is not None else 256
        provider = LoraLocalProvider(
            adapter_dir=model_override,
            temperature=temperature_value,
            max_new_tokens=max_new_tokens,
        )
        return provider, ProviderChoice(name="lora", model=str(model_override))

    # Azure OpenAI config
    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    # OpenAI config
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    temperature_setting = float(temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.7"))

    # Resolve based on explicit choice first
    if provider_choice == "lmstudio":
        selected_model = model_override or lm_studio_model_name
        provider = LMStudioProvider(
            base_url=lm_studio_base_url,
            model=selected_model,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="lmstudio", model=selected_model))

    if provider_choice == "ollama":
        selected_model = model_override or ollama_model_name
        provider = OllamaProvider(
            base_url=ollama_base_url,
            model=selected_model,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="ollama", model=selected_model))

    if provider_choice == "azure":
        if not (azure_openai_api_key and azure_openai_endpoint and (model_override or azure_openai_deployment)):
            raise RuntimeError(
                "Azure OpenAI selected but required env vars are missing. Set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT."
            )
        selected_model = model_override or azure_openai_deployment  # deployment name
        provider = AzureOpenAIProvider(
            deployment=selected_model,
            endpoint=azure_openai_endpoint,
            api_key=azure_openai_api_key,
            api_version=azure_openai_api_version,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="azure", model=selected_model))

    if provider_choice == "openai":
        if not openai_api_key:
            raise RuntimeError("OpenAI selected but OPENAI_API_KEY is not set.")
        selected_model = model_override or openai_model_name
        provider = OpenAIProvider(
            model=selected_model,
            api_key=openai_api_key,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="openai", model=selected_model))

    if provider_choice == "groq":
        if not groq_api_key:
            raise RuntimeError("Groq selected but GROQ_API_KEY is not set.")
        selected_model = model_override or groq_model_name
        provider = GroqProvider(
            model=selected_model,
            api_key=groq_api_key,
            base_url=groq_base_url,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="groq", model=selected_model))

    if provider_choice == "local":
        if force_local_echo:
            selected_model = model_override or "local-echo"
            provider = LocalEchoProvider()
            return _cache_provider_result(cache_key, provider, ProviderChoice(name="local", model=selected_model))

        # "local" should prefer actual local-LLM runtimes first, then degrade
        # to the deterministic local echo provider when no runtime is available.
        if _check_lm_studio_available(lm_studio_base_url):
            selected_model = model_override or lm_studio_model_name
            provider = LMStudioProvider(
                base_url=lm_studio_base_url,
                model=selected_model,
                temperature=temperature_setting,
                max_output_tokens=max_output_tokens,
            )
            return _cache_provider_result(cache_key, provider, ProviderChoice(name="lmstudio", model=selected_model))

        if _check_ollama_available(ollama_base_url):
            selected_model = model_override or ollama_model_name
            provider = OllamaProvider(
                base_url=ollama_base_url,
                model=selected_model,
                temperature=temperature_setting,
                max_output_tokens=max_output_tokens,
            )
            return _cache_provider_result(cache_key, provider, ProviderChoice(name="ollama", model=selected_model))

        selected_model = model_override or "local-echo"
        provider = LocalEchoProvider()
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="local", model=selected_model))

    # Auto mode - check for LM Studio first using thread-safe cached check
    if _check_lm_studio_available(lm_studio_base_url):
        selected_model = model_override or lm_studio_model_name
        provider = LMStudioProvider(
            base_url=lm_studio_base_url,
            model=selected_model,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="lmstudio", model=selected_model))

    # Check for Ollama next
    if _check_ollama_available(ollama_base_url):
        selected_model = model_override or ollama_model_name
        provider = OllamaProvider(
            base_url=ollama_base_url,
            model=selected_model,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="ollama", model=selected_model))

    if azure_openai_api_key and azure_openai_endpoint and (model_override or azure_openai_deployment):
        selected_model = model_override or azure_openai_deployment
        provider = AzureOpenAIProvider(
            deployment=selected_model,
            endpoint=azure_openai_endpoint,
            api_key=azure_openai_api_key,
            api_version=azure_openai_api_version,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="azure", model=selected_model))

    if openai_api_key:
        selected_model = model_override or openai_model_name
        provider = OpenAIProvider(
            model=selected_model,
            api_key=openai_api_key,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="openai", model=selected_model))

    # Check Groq after OpenAI in auto mode
    if groq_api_key and _check_groq_available(groq_base_url):
        selected_model = model_override or groq_model_name
        provider = GroqProvider(
            model=selected_model,
            api_key=groq_api_key,
            base_url=groq_base_url,
            temperature=temperature_setting,
            max_output_tokens=max_output_tokens,
        )
        return _cache_provider_result(cache_key, provider, ProviderChoice(name="groq", model=selected_model))

    # Fallback to local echo provider
    selected_model = model_override or "local-echo"
    provider = LocalEchoProvider()
    return _cache_provider_result(cache_key, provider, ProviderChoice(name="local", model=selected_model))
