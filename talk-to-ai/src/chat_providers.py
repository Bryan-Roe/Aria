from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from typing import Dict, Generator, Iterable, List, Optional

try:
    # openai>=1.0
    from openai import OpenAI, AzureOpenAI
    from openai.types.chat import ChatCompletion
except Exception:  # pragma: no cover - optional at runtime
    OpenAI = None  # type: ignore
    AzureOpenAI = None  # type: ignore
    ChatCompletion = None  # type: ignore


RoleMessage = Dict[str, str]  # {"role": "system|user|assistant", "content": "..."}


@dataclass
class ProviderChoice:
    name: str  # 'azure' | 'openai' | 'local'
    model: str


class BaseChatProvider:
    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        raise NotImplementedError


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
    def __init__(self, model: str, api_key: Optional[str] = None, temperature: float = 0.7):
        if OpenAI is None:
            raise RuntimeError("openai package not installed. Install 'openai' to use this provider.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        if stream:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
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
                stream=False,
            )
            try:
                return resp.choices[0].message.content or ""
            except Exception:
                return ""


class AzureOpenAIProvider(BaseChatProvider):
    def __init__(self, deployment: str, endpoint: str, api_key: str, api_version: str = "2024-08-01-preview", temperature: float = 0.7):
        if AzureOpenAI is None:
            raise RuntimeError("openai package not installed. Install 'openai' to use this provider.")
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint,
        )
        self.deployment = deployment
        self.temperature = temperature

    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        if stream:
            resp = self.client.chat.completions.create(
                model=self.deployment,  # In Azure, 'model' is your deployment name
                messages=messages,
                temperature=self.temperature,
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
                stream=False,
            )
            try:
                return resp.choices[0].message.content or ""
            except Exception:
                return ""


def detect_provider(explicit: Optional[str] = None, model_override: Optional[str] = None) -> tuple[BaseChatProvider, ProviderChoice]:
    """Detect the best provider based on environment variables.

    Priority:
      1) explicit selection if provided
      2) Azure if all required vars present
      3) OpenAI if OPENAI_API_KEY is present
      4) Local fallback
    """
    choice = (explicit or "auto").lower()

    # Azure config
    az_key = os.getenv("AZURE_OPENAI_API_KEY")
    az_ep = os.getenv("AZURE_OPENAI_ENDPOINT")
    az_dep = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    az_ver = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    # OpenAI config
    oi_key = os.getenv("OPENAI_API_KEY")
    oi_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    temp = float(os.getenv("CHAT_TEMPERATURE", "0.7"))

    # Resolve based on explicit choice first
    if choice == "azure":
        if not (az_key and az_ep and (model_override or az_dep)):
            raise RuntimeError("Azure OpenAI selected but required env vars are missing. Set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT.")
        model = model_override or az_dep  # deployment name
        provider = AzureOpenAIProvider(deployment=model, endpoint=az_ep, api_key=az_key, api_version=az_ver, temperature=temp)
        return provider, ProviderChoice(name="azure", model=model)

    if choice == "openai":
        if not oi_key:
            raise RuntimeError("OpenAI selected but OPENAI_API_KEY is not set.")
        model = model_override or oi_model
        provider = OpenAIProvider(model=model, api_key=oi_key, temperature=temp)
        return provider, ProviderChoice(name="openai", model=model)

    if choice == "local":
        model = model_override or "local-echo"
        provider = LocalEchoProvider()
        return provider, ProviderChoice(name="local", model=model)

    # Auto mode
    if az_key and az_ep and (model_override or az_dep):
        model = model_override or az_dep
        provider = AzureOpenAIProvider(deployment=model, endpoint=az_ep, api_key=az_key, api_version=az_ver, temperature=temp)
        return provider, ProviderChoice(name="azure", model=model)

    if oi_key:
        model = model_override or oi_model
        provider = OpenAIProvider(model=model, api_key=oi_key, temperature=temp)
        return provider, ProviderChoice(name="openai", model=model)

    # Fallback
    model = model_override or "local-echo"
    provider = LocalEchoProvider()
    return provider, ProviderChoice(name="local", model=model)
