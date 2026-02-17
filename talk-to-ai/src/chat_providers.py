from __future__ import annotations

import os
import random
import threading
import time
from dataclasses import dataclass
import json as _json
import subprocess
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional
import logging

# Helpers for Azure quota/rate-limit detection
try:  # shared package may not be importable in all contexts (tests add paths)
    from shared.azure_utils import (
        is_quota_error,
        is_transient_rate_error,
        format_quota_message,
    )
except Exception:  # pragma: no cover - best-effort import
    # Provide fallbacks if shared module isn't available in runtime/test harness
    def is_quota_error(e: Any) -> bool:
        txt = str(e).lower() if e is not None else ""
        return any(k in txt for k in ("quota", "premium", "exceed", "allowance", "insufficient", "billing"))

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
    from openai import OpenAI, AzureOpenAI  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    OpenAI = None  # type: ignore
    AzureOpenAI = None  # type: ignore


# Thread-safe cache for LM Studio availability checks
_lm_studio_availability_cache: Dict[str, Any] = {
    "available": None, "checked_at": 0.0, "url": None}
_lm_studio_cache_lock = threading.RLock()
# Backward-compatible alias for tests expecting _lmstudio_cache_lock
_lmstudio_cache_lock = _lm_studio_cache_lock
_LM_STUDIO_CACHE_TTL_SECONDS = 30


# {"role": "system|user|assistant", "content": "..."}
RoleMessage = Dict[str, str]


# -------------------------------------------------------------------------
# LM Studio availability cache to avoid repeated HTTP health checks
# -------------------------------------------------------------------------

_lmstudio_cache: Dict[str, Any] = {
    "available": None, "checked_at": 0.0, "url": None}
_LMSTUDIO_CACHE_TTL = 30  # seconds


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
            import urllib.request
            import urllib.error
            base_url = url.removesuffix("/v1")
            models_endpoint_url = base_url + "/v1/models"
            request = urllib.request.Request(
                models_endpoint_url, headers={"User-Agent": "QAI"})
            urllib.request.urlopen(request, timeout=1)
            return True
        except Exception:
            return False


@dataclass
class ProviderChoice:
    name: str  # 'azure' | 'openai' | 'local'
    model: str


class BaseChatProvider:
    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        raise NotImplementedError

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
        repetition_penalty: float = 1.1
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
        self.bridge_python: Optional[str] = None
        self.temperature = float(temperature)
        self.max_new_tokens = int(max_new_tokens)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.repetition_penalty = float(repetition_penalty)
        # Lazy import heavy deps on demand
        self._lazy_setup()
        if not self.use_subprocess:
            self.device = device or (
                "cuda" if self.torch.cuda.is_available() else "cpu")
            self.model, self.tokenizer = self._load_model_and_tokenizer()
        else:
            # In subprocess mode we keep state minimal here
            self.device = "cpu"

    def _load_model_and_tokenizer(self):
        # Detect adapter config
        import json as _json
        adapter_config_path = self.adapter_dir / "adapter_config.json"
        if not adapter_config_path.exists():
            raise RuntimeError(
                f"adapter_config.json not found in {self.adapter_dir}")
        with open(adapter_config_path, "r", encoding="utf-8") as f:
            adapter_cfg = _json.load(f)
        base_model_id = adapter_cfg.get(
            "base_model_name_or_path", "microsoft/Phi-3.5-mini-instruct")
        # Fallback mapping for Phi-3.6
        if base_model_id == "Phi-3.6-mini-instruct":
            base_model_id = "microsoft/Phi-3.5-mini-instruct"
        base_model = self.AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=self.torch.float16 if self.device == "cuda" else self.torch.float32,
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

    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
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
        response = self.tokenizer.decode(
            output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        if not stream:
            return response

        def gen():
            for ch in response:
                yield ch
                time.sleep(0.002)
        return gen()

    def _complete_via_subprocess(self, messages: List[RoleMessage]) -> str:
        if not self.bridge_python:
            raise RuntimeError(
                "Subprocess bridge not configured for LoRA provider.")
        bridge_script = Path(__file__).resolve().parent / \
            "lora_infer_bridge.py"
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
            msg = stderr.strip() or stdout.strip(
            ) or f"exit code {proc.returncode}"
            # Truncate very long errors but keep start and end
            if len(msg) > 1000:
                msg = msg[:500] + "\n...\n" + msg[-500:]
            raise RuntimeError(f"LoRA bridge failed: {msg}")
        text = proc.stdout.decode("utf-8", errors="ignore").strip()
        return text

    def _build_prompt(self, messages: List[RoleMessage]) -> str:
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
            from transformers import AutoModelForCausalLM as _AM, AutoTokenizer as _AT  # type: ignore
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
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def _craft_reply(self, messages: List[RoleMessage]) -> str:
        last_user = next((m["content"] for m in reversed(
            messages) if m.get("role") == "user"), "")
        lead_ins = [
            "Here's a concise take:",
            "Quick thoughts:",
            "A few ideas:",
            "My perspective:",
            "Summary:",
        ]
        closers = [
            "Does that help?",
            "Let me know if you want examples.",
            "We can refine this together.",
            "Happy to go deeper.",
        ]
        if not last_user.strip():
            return "Hi! Ask me anything. I can brainstorm, summarize, or explain topics."
        hint = last_user.strip()
        if len(hint) > 300:
            hint = hint[:300] + "..."
        reply = f"{self.rng.choice(lead_ins)} {self._rephrase(hint)} {self.rng.choice(closers)}"
        return reply

    def _rephrase(self, text: str) -> str:
        # Extremely lightweight rephrasing to feel less echo-y
        swaps = {
            "I need": "You're looking for",
            "I want": "You want",
            "How to": "Ways to",
            "help": "support",
            "problem": "challenge",
            "issue": "question",
        }
        for a, b in swaps.items():
            text = text.replace(a, b)
        return text

    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
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
    def __init__(self, model: str, api_key: Optional[str] = None, temperature: float = 0.7, max_output_tokens: Optional[int] = None):
        if OpenAI is None:
            raise RuntimeError(
                "openai package not installed. Install 'openai' to use this provider.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
            stream=stream,
        )
        
        if stream:
            return self._handle_openai_streaming_response(resp)
        else:
            return self._handle_openai_non_streaming_response(resp)


class LMStudioProvider(BaseChatProvider):
    """Provider for LM Studio local server (compatible with OpenAI API)."""

    def __init__(self, base_url: str = "http://127.0.0.1:1234/v1", model: str = "local-model", temperature: float = 0.7, max_output_tokens: Optional[int] = None):
        if OpenAI is None:
            raise RuntimeError(
                "openai package not installed. Install 'openai' to use this provider.")
        self.client = OpenAI(
            base_url=base_url,
            api_key="lm-studio"  # LM Studio doesn't require real key
        )
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
            stream=stream,
        )
        
        if stream:
            return self._handle_openai_streaming_response(resp)
        else:
            return self._handle_openai_non_streaming_response(resp)


class AzureOpenAIProvider(BaseChatProvider):
    def __init__(self, deployment: str, endpoint: str, api_key: str, api_version: str = "2024-08-01-preview", temperature: float = 0.7, max_output_tokens: Optional[int] = None):
        if AzureOpenAI is None:
            raise RuntimeError(
                "openai package not installed. Install 'openai' to use this provider.")
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint,
        )
        self.deployment = deployment
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        """Complete with Azure OpenAI and handle quota/rate-limit errors gracefully.

        Behavior:
          - If a quota/premium allowance error is detected, return a friendly
            message instead of raising an exception.
          - Retry transient rate-limit style errors a small number of times with
            exponential backoff.

        Returns either a string (non-stream) or a generator yielding string chunks.
        """
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
                        sleep_time = base_backoff * (2 ** attempt)
                        jitter = min(sleep_time * 0.1, 0.5)
                        import time

                        _LOGGER.info(
                            "Azure rate-limit detected, retrying in %.2fs (attempt %d)", sleep_time + jitter, attempt + 1)
                        time.sleep(sleep_time + jitter)
                        attempt += 1
                        continue
                    # Propagate other exceptions
                    raise

        try:
            resp = _attempt_create(
                model=self.deployment,  # In Azure, 'model' is your deployment name
                messages=messages,
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
    try:
        import urllib.request
        import urllib.error
        # Remove trailing /v1 if present, then append /v1/models
        base_url = server_url.removesuffix("/v1")
        models_endpoint_url = base_url + "/v1/models"
        request = urllib.request.Request(
            models_endpoint_url, headers={"User-Agent": "QAI"})
        urllib.request.urlopen(request, timeout=1)
        is_available = True
    except Exception:
        is_available = False

    # Update cache under lock
    with _lm_studio_cache_lock:
        _lm_studio_availability_cache["available"] = is_available
        _lm_studio_availability_cache["checked_at"] = time.time()
        _lm_studio_availability_cache["url"] = server_url

    return is_available


def detect_provider(explicit: Optional[str] = None, model_override: Optional[str] = None, temperature: Optional[float] = None, max_output_tokens: Optional[int] = None) -> tuple[BaseChatProvider, ProviderChoice]:
    """Detect the best provider based on environment variables.

    Priority:
      1) explicit selection if provided
      2) LM Studio if LMSTUDIO_BASE_URL is set
      3) AGI if selected (advanced reasoning capabilities)
      4) Quantum if selected
      5) Azure if all required vars present
      6) OpenAI if OPENAI_API_KEY is present
      7) Local fallback
      8) LoRA if provider is 'lora' and model_override is set
    """
    provider_choice = (explicit or "auto").lower()

    # LM Studio config
    lm_studio_base_url = os.getenv(
        "LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    lm_studio_model_name = os.getenv("LMSTUDIO_MODEL", "local-model")

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
                verbose=verbose
            )
            return provider, ProviderChoice(name=info.name, model=info.model)
        except ImportError as import_error:
            raise RuntimeError(f"AGI provider selected but agi_provider module not available: {import_error}")

    # Quantum config
    if provider_choice == "quantum":
        try:
            from quantum_provider import create_quantum_provider
            temperature_value = float(
                temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.7"))
            max_tokens_limit = int(
                max_output_tokens) if max_output_tokens is not None else 1024
            provider, info = create_quantum_provider(
                model=model_override,
                temperature=temperature_value,
                max_output_tokens=max_tokens_limit
            )
            return provider, ProviderChoice(name=info.name, model=info.model)
        except ImportError as import_error:
            raise RuntimeError(
                f"Quantum provider selected but quantum_provider module not available: {import_error}")

    # LoRA config
    if provider_choice == "lora":
        if not model_override:
            raise RuntimeError(
                "LoRA provider selected but model path not provided.")
        temperature_value = float(
            temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.7"))
        max_new_tokens = int(
            max_output_tokens) if max_output_tokens is not None else 256
        provider = LoraLocalProvider(
            adapter_dir=model_override, temperature=temperature_value, max_new_tokens=max_new_tokens)
        return provider, ProviderChoice(name="lora", model=str(model_override))

    # Azure OpenAI config
    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version = os.getenv(
        "AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    # OpenAI config
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    temperature_setting = float(
        temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.7"))

    # Resolve based on explicit choice first
    if provider_choice == "lmstudio":
        selected_model = model_override or lm_studio_model_name
        provider = LMStudioProvider(base_url=lm_studio_base_url, model=selected_model,
                                    temperature=temperature_setting, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="lmstudio", model=selected_model)

    if provider_choice == "azure":
        if not (azure_openai_api_key and azure_openai_endpoint and (model_override or azure_openai_deployment)):
            raise RuntimeError(
                "Azure OpenAI selected but required env vars are missing. Set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT.")
        selected_model = model_override or azure_openai_deployment  # deployment name
        provider = AzureOpenAIProvider(deployment=selected_model, endpoint=azure_openai_endpoint, api_key=azure_openai_api_key,
                                       api_version=azure_openai_api_version, temperature=temperature_setting, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="azure", model=selected_model)

    if provider_choice == "openai":
        if not openai_api_key:
            raise RuntimeError(
                "OpenAI selected but OPENAI_API_KEY is not set.")
        selected_model = model_override or openai_model_name
        provider = OpenAIProvider(model=selected_model, api_key=openai_api_key,
                                  temperature=temperature_setting, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="openai", model=selected_model)

    if provider_choice == "local":
        selected_model = model_override or "local-echo"
        provider = LocalEchoProvider()
        return provider, ProviderChoice(name="local", model=selected_model)

    # Auto mode - check for LM Studio first using thread-safe cached check
    if _check_lm_studio_available(lm_studio_base_url):
        selected_model = model_override or lm_studio_model_name
        provider = LMStudioProvider(base_url=lm_studio_base_url, model=selected_model,
                                    temperature=temperature_setting, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="lmstudio", model=selected_model)

    if azure_openai_api_key and azure_openai_endpoint and (model_override or azure_openai_deployment):
        selected_model = model_override or azure_openai_deployment
        provider = AzureOpenAIProvider(deployment=selected_model, endpoint=azure_openai_endpoint, api_key=azure_openai_api_key,
                                       api_version=azure_openai_api_version, temperature=temperature_setting, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="azure", model=selected_model)

    if openai_api_key:
        selected_model = model_override or openai_model_name
        provider = OpenAIProvider(model=selected_model, api_key=openai_api_key,
                                  temperature=temperature_setting, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="openai", model=selected_model)

    # Fallback to local echo provider
    selected_model = model_override or "local-echo"
    provider = LocalEchoProvider()
    return provider, ProviderChoice(name="local", model=selected_model)
