from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
import json as _json
import subprocess
from pathlib import Path
from typing import Dict, Generator, Iterable, List, Optional

try:
    # openai>=1.0
    from openai import OpenAI, AzureOpenAI  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    OpenAI = None  # type: ignore
    AzureOpenAI = None  # type: ignore


RoleMessage = Dict[str, str]  # {"role": "system|user|assistant", "content": "..."}


@dataclass
class ProviderChoice:
    name: str  # 'azure' | 'openai' | 'local'
    model: str



class BaseChatProvider:
    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        raise NotImplementedError


class LoraLocalProvider(BaseChatProvider):
    """Provider for local inference with LoRA adapters.

    If ML dependencies are unavailable in the current process (e.g.,
    Azure Functions worker without torch/transformers/peft), this provider
    falls back to a subprocess bridge that uses the workspace venv
    (./venv/Scripts/python.exe) to perform inference.
    """
    def __init__(self, adapter_dir: str, device: str = None, temperature: float = 0.7, max_new_tokens: int = 256):
        self.adapter_dir = Path(adapter_dir)
        self.use_subprocess = False
        self.bridge_python: Optional[str] = None
        self.temperature = float(temperature)
        self.max_new_tokens = int(max_new_tokens)
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
        with open(adapter_config_path, "r", encoding="utf-8") as f:
            adapter_cfg = _json.load(f)
        base_model_id = adapter_cfg.get("base_model_name_or_path", "microsoft/Phi-3.5-mini-instruct")
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
                pad_token_id=self.tokenizer.eos_token_id,
            )
        response = self.tokenizer.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        if not stream:
            return response
        def gen():
            for ch in response:
                yield ch
                time.sleep(0.002)
        return gen()

    def _complete_via_subprocess(self, messages: List[RoleMessage]) -> str:
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
            # Truncate very long errors
            if len(msg) > 1000:
                msg = msg[:1000] + "..."
            raise RuntimeError(f"LoRA bridge failed: {msg}")
        text = proc.stdout.decode("utf-8", errors="ignore").strip()
        return text

    def _build_prompt(self, messages: List[RoleMessage]) -> str:
        # Simple concatenation; can be improved for chat templates
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"[SYSTEM] {content}\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        prompt += "Assistant: "
        return prompt

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
        last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
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
            raise RuntimeError("openai package not installed. Install 'openai' to use this provider.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        if stream:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=True,
            )

            def gen() -> Generator[str, None, None]:
                for chunk in resp:
                    try:
                        delta = chunk.choices[0].delta
                        if delta and delta.content:
                            yield delta.content
                    except Exception:
                        # Be resilient to SDK shape changes
                        pass
            return gen()
        else:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=False,
            )
            try:
                return resp.choices[0].message.content or ""
            except Exception:
                return ""


class AzureOpenAIProvider(BaseChatProvider):
    def __init__(self, deployment: str, endpoint: str, api_key: str, api_version: str = "2024-08-01-preview", temperature: float = 0.7, max_output_tokens: Optional[int] = None):
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

    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        if stream:
            resp = self.client.chat.completions.create(
                model=self.deployment,  # In Azure, 'model' is your deployment name
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=True,
            )

            def gen() -> Generator[str, None, None]:
                for chunk in resp:
                    try:
                        delta = chunk.choices[0].delta
                        if delta and delta.content:
                            yield delta.content
                    except Exception:
                        pass
            return gen()
        else:
            resp = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=False,
            )
            try:
                return resp.choices[0].message.content or ""
            except Exception:
                return ""


def detect_provider(explicit: Optional[str] = None, model_override: Optional[str] = None, temperature: Optional[float] = None, max_output_tokens: Optional[int] = None) -> tuple[BaseChatProvider, ProviderChoice]:
    """Detect the best provider based on environment variables.

    Priority:
      1) explicit selection if provided
      2) Azure if all required vars present
      3) OpenAI if OPENAI_API_KEY is present
      4) Local fallback
            5) LoRA if provider is 'lora' and model_override is set
    """
    choice = (explicit or "auto").lower()

    # LoRA config
    if choice == "lora":
        if not model_override:
            raise RuntimeError("LoRA provider selected but model path not provided.")
        temp_val = float(temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.7"))
        max_new = int(max_output_tokens) if max_output_tokens is not None else 256
        provider = LoraLocalProvider(adapter_dir=model_override, temperature=temp_val, max_new_tokens=max_new)
        return provider, ProviderChoice(name="lora", model=str(model_override))


    # Azure config
    az_key = os.getenv("AZURE_OPENAI_API_KEY")
    az_ep = os.getenv("AZURE_OPENAI_ENDPOINT")
    az_dep = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    az_ver = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    # OpenAI config
    oi_key = os.getenv("OPENAI_API_KEY")
    oi_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    temp = float(temperature if temperature is not None else os.getenv("CHAT_TEMPERATURE", "0.7"))

    # Resolve based on explicit choice first
    if choice == "azure":
        if not (az_key and az_ep and (model_override or az_dep)):
            raise RuntimeError("Azure OpenAI selected but required env vars are missing. Set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT.")
        model = model_override or az_dep  # deployment name
        provider = AzureOpenAIProvider(deployment=model, endpoint=az_ep, api_key=az_key, api_version=az_ver, temperature=temp, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="azure", model=model)

    if choice == "openai":
        if not oi_key:
            raise RuntimeError("OpenAI selected but OPENAI_API_KEY is not set.")
        model = model_override or oi_model
        provider = OpenAIProvider(model=model, api_key=oi_key, temperature=temp, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="openai", model=model)

    if choice == "local":
        model = model_override or "local-echo"
        provider = LocalEchoProvider()
        return provider, ProviderChoice(name="local", model=model)

    # Auto mode
    if az_key and az_ep and (model_override or az_dep):
        model = model_override or az_dep
        provider = AzureOpenAIProvider(deployment=model, endpoint=az_ep, api_key=az_key, api_version=az_ver, temperature=temp, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="azure", model=model)

    if oi_key:
        model = model_override or oi_model
        provider = OpenAIProvider(model=model, api_key=oi_key, temperature=temp, max_output_tokens=max_output_tokens)
        return provider, ProviderChoice(name="openai", model=model)

    # Fallback
    model = model_override or "local-echo"
    provider = LocalEchoProvider()
    return provider, ProviderChoice(name="local", model=model)
