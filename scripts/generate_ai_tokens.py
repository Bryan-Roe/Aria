#!/usr/bin/env python3
"""Automated AI provider token generation, validation, and rotaton.

Discovers, probes, and optionally auto-generates authentication tokens for all
configured AI providers in this repo (Ollama, LM Studio, Azure OpenAI, OpenAI).

Usage
-----
    # Probe all providers and print a status table (no writes)
    python3 scripts/generate_ai_tokens.py

    # Probe a specific provider
    python3 scripts/generate_ai_tokens.py --provider lmstudio

    # Probe + write validated tokens back to local.settings.json
    python3 scripts/generate_ai_tokens.py --write

    # Interactive: prompt for missing values and write
    python3 scripts/generate_ai_tokens.py --write --interactive

    # Generate a fresh LM Studio local token and write it
    python3 scripts/generate_ai_tokens.py --provider lmstudio --rotate --write

    # Attempt Azure CLI token exchange (requires `az login`)
    python3 scripts/generate_ai_tokens.py --provider azure --use-az-cli --write

    # Output machine-readable JSON
    python3 scripts/generate_ai_tokens.py --json

    # Pull an Ollama model if none are available
    python3 scripts/generate_ai_tokens.py --provider ollama --pull-model llama3.2

Env vars used
-------------
    AZURE_OPENAI_API_KEY      — Azure OpenAI static key
    AZURE_OPENAI_ENDPOINT     — Azure OpenAI endpoint URL
    AZURE_OPENAI_DEPLOYMENT   — Azure OpenAI deployment name
    AZURE_OPENAI_API_VERSION  — Azure OpenAI API version
    OPENAI_API_KEY            — OpenAI direct key
    LM_API_TOKEN              — LM Studio auth token (alias LMSTUDIO_API_KEY)
    LMSTUDIO_BASE_URL         — LM Studio server URL (default: http://localhost:1234)
    LMSTUDIO_MODEL            — LM Studio model name
    OLLAMA_BASE_URL           — Ollama server URL (default: http://127.0.0.1:11434)
    OLLAMA_MODEL              — Ollama model name

Exit codes
----------
    0 — at least one provider is healthy
    1 — no providers available
    2 — configuration error (bad args, unreadable settings)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Path constants ────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_SETTINGS = REPO_ROOT / "local.settings.json"
STATUS_OUT = REPO_ROOT / "data_out" / "ai_token_status.json"

# ── Colour helpers ────────────────────────────────────────────────────────────

_COLOR = sys.stdout.isatty()
_GREEN = "\033[92m" if _COLOR else ""
_RED = "\033[91m" if _COLOR else ""
_YELLOW = "\033[93m" if _COLOR else ""
_BLUE = "\033[94m" if _COLOR else ""
_BOLD = "\033[1m" if _COLOR else ""
_RESET = "\033[0m" if _COLOR else ""


def _ok(msg: str) -> None:
    print(f"{_GREEN}✅  {msg}{_RESET}")


def _fail(msg: str) -> None:
    print(f"{_RED}❌  {msg}{_RESET}")


def _warn(msg: str) -> None:
    print(f"{_YELLOW}⚠️   {msg}{_RESET}")


def _info(msg: str) -> None:
    print(f"{_BLUE}ℹ️   {msg}{_RESET}")


def _head(msg: str) -> None:
    print(f"\n{_BOLD}{_BLUE}{'─' * 56}\n  {msg}\n{'─' * 56}{_RESET}")


logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
_log = logging.getLogger(__name__)


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class ProviderResult:
    name: str
    status: str  # "ok" | "warn" | "fail" | "skipped"
    token_present: bool = False
    token_generated: bool = False
    token_rotated: bool = False
    endpoint: str = ""
    model: str = ""
    latency_ms: float = 0.0
    error: str = ""
    env_written: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


# ── local.settings.json helpers ───────────────────────────────────────────────


def _load_settings() -> dict[str, Any]:
    if LOCAL_SETTINGS.exists():
        try:
            return json.loads(LOCAL_SETTINGS.read_text())
        except json.JSONDecodeError as exc:
            _warn(f"Could not parse local.settings.json: {exc}")
    return {"IsEncrypted": False, "Values": {}}


def _save_settings(settings: dict[str, Any]) -> None:
    LOCAL_SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
    _ok(f"Wrote {LOCAL_SETTINGS}")


def _get_setting(settings: dict[str, Any], key: str, fallback: str = "") -> str:
    """Return value from settings 'Values' dict, then env, then fallback."""
    vals = settings.get("Values", {})
    val = vals.get(key, "") or os.environ.get(key, fallback)
    # Skip comment-only entries (values starting with #)
    if str(val).strip().startswith("#"):
        return fallback
    return val or fallback


def _effective_env(settings: dict[str, Any]) -> dict[str, str]:
    """Merge local.settings.json Values into current env (settings wins)."""
    merged: dict[str, str] = {}
    for k, v in (settings.get("Values") or {}).items():
        if v and not str(v).strip().startswith("#"):
            merged[k] = str(v)
    for k, v in os.environ.items():
        if k not in merged and v:
            merged[k] = v
    return merged


# ── HTTP probe helper ─────────────────────────────────────────────────────────


def _probe_url(url: str, headers: dict[str, str] | None = None, timeout: int = 5) -> tuple[int, Any]:
    """Return (status_code, parsed_json_or_None). Returns (-1, None) on connection error."""
    req = urllib.request.Request(url, headers=headers or {})  # noqa: S310
    try:
        t0 = time.monotonic()
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
            elapsed_ms = (time.monotonic() - t0) * 1000
            try:
                return resp.status, json.loads(raw), elapsed_ms
            except json.JSONDecodeError:
                return resp.status, raw, elapsed_ms
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return exc.code, body, 0.0
    except Exception:
        return -1, None, 0.0


def _endpoint_candidates(primary_url: str) -> list[str]:
    """Return probe candidate URLs with container-friendly localhost fallbacks.

    Keeps primary URL first, then adds common substitutions used across dev
    containers where host.docker.internal may be unavailable.
    """
    candidates: list[str] = []

    def _add(url: str) -> None:
        if url and url not in candidates:
            candidates.append(url)

    normalized = primary_url.rstrip("/")
    _add(normalized)

    def _swap_hostname(url: str, current: str, target: str) -> str | None:
        parts = urllib.parse.urlsplit(url)
        if parts.hostname != current:
            return None

        auth = ""
        if parts.username:
            auth = parts.username
            if parts.password:
                auth += f":{parts.password}"
            auth += "@"

        host = target
        if ":" in target and not target.startswith("["):
            host = f"[{target}]"

        port = ""
        if parts.port is not None:
            port = f":{parts.port}"

        netloc = f"{auth}{host}{port}"
        return urllib.parse.urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

    variants = [
        "host.docker.internal",
        "gateway.docker.internal",
        "127.0.0.1",
        "localhost",
    ]

    # Prefer parsed URL hostname matching to avoid accidental path/query
    # replacements when a host-like token appears outside netloc.
    parsed_host = urllib.parse.urlsplit(normalized).hostname
    current_variant = parsed_host if parsed_host in variants else None

    # Fallback for non-URL strings: keep existing substring-based behavior.
    if current_variant is None and "://" not in normalized:
        for candidate in variants:
            if candidate in normalized:
                current_variant = candidate
                break

    if current_variant is not None:
        for target in variants:
            if target == current_variant:
                continue
            swapped = _swap_hostname(normalized, current_variant, target)
            if swapped is None and "://" not in normalized:
                swapped = normalized.replace(current_variant, target)
            if swapped is not None:
                _add(swapped)

    return candidates


# ── Token generation helpers ──────────────────────────────────────────────────


def _generate_local_token(prefix: str = "lm") -> str:
    """Generate a cryptographically-random local bearer token."""
    rand = secrets.token_urlsafe(32)
    return f"{prefix}-{rand}"


def _az_cli_get_token(resource: str = "https://cognitiveservices.azure.com") -> str | None:
    """Try to get an AAD access token via the Azure CLI."""
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", resource, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("accessToken")
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def _az_cli_get_account() -> dict[str, str] | None:
    """Return Azure account info dict, or None if not logged in."""
    try:
        result = subprocess.run(
            ["az", "account", "show", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


# ── Provider: Ollama ──────────────────────────────────────────────────────────


def probe_ollama(
    env: dict[str, str],
    *,
    rotate: bool = False,
    pull_model: str = "",
    write: bool = False,
    interactive: bool = False,
) -> ProviderResult:
    result = ProviderResult(name="ollama", status="fail")

    base_url = (env.get("OLLAMA_BASE_URL") or "http://127.0.0.1:11434").rstrip("/")
    # Ollama's management API is always at /api/tags (not under /v1)
    api_base = re.sub(r"/v1$", "", base_url, flags=re.IGNORECASE)
    result.endpoint = api_base

    # Ollama does not use API tokens — probe the /api/tags endpoint
    status = -1
    data: Any = None
    latency = 0.0
    endpoint_used = api_base
    attempted = []
    for candidate in _endpoint_candidates(api_base):
        attempted.append(candidate)
        status, data, latency = _probe_url(f"{candidate}/api/tags")
        if status != -1:
            endpoint_used = candidate
            break

    result.endpoint = endpoint_used
    result.latency_ms = latency
    result.token_present = True  # no token required

    if status == 200 and isinstance(data, dict):
        models = [m.get("name", "") for m in data.get("models", [])]
        if models:
            result.model = models[0]
            _ok(f"Ollama   — {endpoint_used} ({len(models)} models: {', '.join(models[:3])})")
            result.status = "ok"
        else:
            _warn(f"Ollama   — server reachable but no models installed at {endpoint_used}")
            result.status = "warn"
            result.notes.append("No models installed. Run: ollama pull llama3.2")
    elif status == -1:
        _fail(f"Ollama   — server not reachable (tried: {', '.join(attempted)}) (is `ollama serve` running?)")
        result.status = "fail"
        result.error = "connection refused"
        result.notes.append("Start Ollama: ollama serve")
        return result
    else:
        _fail(f"Ollama   — unexpected response {status} from {endpoint_used}")
        result.status = "fail"
        result.error = f"HTTP {status}"
        return result

    # Auto-pull model if requested and none installed
    if pull_model and not [m for m in (data.get("models") or []) if pull_model in m.get("name", "")]:
        _info(f"Pulling Ollama model: {pull_model} …")
        try:
            pr = subprocess.run(
                ["ollama", "pull", pull_model],
                timeout=300,
                capture_output=True,
                text=True,
            )
            if pr.returncode == 0:
                _ok(f"Pulled model: {pull_model}")
                result.model = pull_model
                result.notes.append(f"Pulled model: {pull_model}")
            else:
                _warn(f"Could not pull {pull_model}: {pr.stderr.strip()[:120]}")
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            _warn(f"ollama pull failed: {exc}")

    # Write nothing for Ollama (no token required). Update OLLAMA_MODEL if discovered.
    if write and result.model and not env.get("OLLAMA_MODEL"):
        result.env_written["OLLAMA_MODEL"] = result.model

    return result


# ── Provider: LM Studio ───────────────────────────────────────────────────────


def probe_lmstudio(
    env: dict[str, str],
    *,
    rotate: bool = False,
    write: bool = False,
    interactive: bool = False,
) -> ProviderResult:
    result = ProviderResult(name="lmstudio", status="fail")

    base_url = (env.get("LMSTUDIO_BASE_URL") or "http://localhost:1234").rstrip("/")
    v1_url = base_url if base_url.endswith("/v1") else f"{base_url}/v1"
    result.endpoint = v1_url

    token = env.get("LM_API_TOKEN") or env.get("LMSTUDIO_API_KEY") or env.get("LMSTUDIO_TOKEN") or ""

    # Try probing /v1/models
    headers: dict[str, str] = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        result.token_present = True

    status = -1
    data: Any = None
    latency = 0.0
    endpoint_used = v1_url
    attempted = []
    for candidate in _endpoint_candidates(v1_url):
        attempted.append(candidate)
        status, data, latency = _probe_url(f"{candidate}/models", headers=headers)
        if status != -1:
            endpoint_used = candidate
            break

    result.endpoint = endpoint_used
    result.latency_ms = latency

    if status == 401:
        # Server is up but auth failed
        _warn(f"LM Studio — server at {endpoint_used} requires a token (401 Unauthorized)")
        if rotate or not token:
            # Generate a fresh token
            new_token = _generate_local_token("lmstudio")
            result.token_generated = True
            result.token_rotated = rotate and bool(token)
            token = new_token
            result.token_present = True
            _info(f"Generated LM Studio token: {new_token[:16]}… (copy to LM Studio server settings)")
            result.notes.append("Generated a new token. Paste it into LM Studio → Server → API Keys.")
            if write:
                result.env_written["LM_API_TOKEN"] = token
        elif interactive:
            token = input("  Enter LM Studio API token: ").strip()
            result.token_present = bool(token)
            if write and token:
                result.env_written["LM_API_TOKEN"] = token
        else:
            result.status = "warn"
            result.error = "401 — token required; run with --rotate or --interactive"
            _fail("LM Studio — token required but none provided")
        # Re-probe with new token
        headers["Authorization"] = f"Bearer {token}"
        status, data, latency = _probe_url(f"{endpoint_used}/models", headers=headers)
        result.latency_ms = latency

    if status == 200 and isinstance(data, dict):
        models = [m.get("id", "") for m in data.get("data", [])]
        active = models[0] if models else env.get("LMSTUDIO_MODEL", "unknown")
        result.model = active
        _ok(f"LM Studio — {endpoint_used}  model: {active}  ({latency:.0f}ms)")
        result.status = "ok"
        result.token_present = True
        if write and models and not env.get("LMSTUDIO_MODEL"):
            result.env_written["LMSTUDIO_MODEL"] = active
        if write and not env.get("LMSTUDIO_BASE_URL"):
            result.env_written["LMSTUDIO_BASE_URL"] = base_url
    elif status == -1:
        _fail(f"LM Studio — not reachable (tried: {', '.join(attempted)}) (enable local server in LM Studio app)")
        result.status = "fail"
        result.error = "connection refused"
        result.notes.append("Enable LM Studio local server: LM Studio → Local Server tab → Start")
    elif status != 401:
        _fail(f"LM Studio — unexpected response {status} from {endpoint_used}")
        result.status = "fail"
        result.error = f"HTTP {status}"

    return result


# ── Provider: Azure OpenAI ────────────────────────────────────────────────────


def probe_azure_openai(
    env: dict[str, str],
    *,
    use_az_cli: bool = False,
    rotate: bool = False,
    write: bool = False,
    interactive: bool = False,
) -> ProviderResult:
    result = ProviderResult(name="azure_openai", status="fail")

    api_key = env.get("AZURE_OPENAI_API_KEY", "")
    endpoint = env.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    deployment = env.get("AZURE_OPENAI_DEPLOYMENT", "")
    api_ver = env.get("AZURE_OPENAI_API_VERSION", "2024-02-01")

    # ── Step 1: resolve API key ───────────────────────────────────────────────
    if not api_key and use_az_cli:
        _info("Trying Azure CLI token exchange …")
        account = _az_cli_get_account()
        if account:
            _ok(f"Azure CLI — logged in as: {account.get('user', {}).get('name', '?')} ({account.get('name', '?')})")
            aad_token = _az_cli_get_token()
            if aad_token:
                api_key = aad_token
                result.token_generated = True
                result.notes.append(
                    "Used Azure CLI AAD token (expires ~1h). Set AZURE_OPENAI_API_KEY for long-lived auth."
                )
                _ok(f"Got AAD access token via az CLI ({aad_token[:12]}…)")
                if write:
                    result.env_written["AZURE_OPENAI_API_KEY"] = aad_token
            else:
                _warn("Azure CLI available but token exchange failed")
        else:
            _fail("Azure CLI not logged in — run: az login")
            result.status = "fail"
            result.error = "az account show failed"
            return result

    if not api_key and interactive:
        api_key = input("  Enter AZURE_OPENAI_API_KEY (or leave blank to skip): ").strip()
        if api_key and write:
            result.env_written["AZURE_OPENAI_API_KEY"] = api_key

    if not api_key:
        _warn("Azure OpenAI — AZURE_OPENAI_API_KEY not set (use --use-az-cli or --interactive)")
        result.status = "skipped"
        result.error = "no api key"
        return result

    result.token_present = True

    # ── Step 2: resolve endpoint ──────────────────────────────────────────────
    if not endpoint and interactive:
        endpoint = input("  Enter AZURE_OPENAI_ENDPOINT: ").strip().rstrip("/")
        if endpoint and write:
            result.env_written["AZURE_OPENAI_ENDPOINT"] = endpoint

    if not endpoint:
        _warn("Azure OpenAI — AZURE_OPENAI_ENDPOINT not set")
        result.status = "skipped"
        result.error = "no endpoint"
        return result

    if not deployment and interactive:
        deployment = input("  Enter AZURE_OPENAI_DEPLOYMENT (model deployment name): ").strip()
        if deployment and write:
            result.env_written["AZURE_OPENAI_DEPLOYMENT"] = deployment

    result.endpoint = endpoint

    # ── Step 3: probe /deployments endpoint ──────────────────────────────────
    probe_url = f"{endpoint}/openai/deployments?api-version={api_ver}"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }
    status, data, latency = _probe_url(probe_url, headers=headers)
    result.latency_ms = latency

    if status == 200 and isinstance(data, dict):
        deployments = [d.get("id", "") for d in data.get("value", [])]
        chosen = deployment or (deployments[0] if deployments else "")
        result.model = chosen
        _ok(f"Azure OpenAI — {endpoint}  deployment: {chosen or '?'}  ({latency:.0f}ms)")
        if not deployment and deployments:
            _info(f"  Auto-detected deployments: {', '.join(deployments[:5])}")
            if write and not env.get("AZURE_OPENAI_DEPLOYMENT"):
                result.env_written["AZURE_OPENAI_DEPLOYMENT"] = deployments[0]
        result.status = "ok"
    elif status == 401:
        _fail("Azure OpenAI — 401 Unauthorized. API key is invalid or expired.")
        result.status = "fail"
        result.error = "401 — invalid api key"
        if use_az_cli:
            result.notes.append("AAD token may have expired. Re-run with --use-az-cli to refresh.")
    elif status == 403:
        _fail("Azure OpenAI — 403 Forbidden. Check endpoint/deployment access.")
        result.status = "fail"
        result.error = "403"
    elif status == -1:
        _fail(f"Azure OpenAI — endpoint not reachable: {endpoint}")
        result.status = "fail"
        result.error = "connection failed"
    else:
        _warn(f"Azure OpenAI — unexpected response {status} from {probe_url}")
        result.status = "warn"
        result.error = f"HTTP {status}"

    return result


# ── Provider: OpenAI ──────────────────────────────────────────────────────────


def probe_openai(
    env: dict[str, str],
    *,
    rotate: bool = False,
    write: bool = False,
    interactive: bool = False,
) -> ProviderResult:
    result = ProviderResult(name="openai", status="fail")

    api_key = env.get("OPENAI_API_KEY", "")
    result.endpoint = "https://api.openai.com/v1"

    if not api_key and interactive:
        api_key = input("  Enter OPENAI_API_KEY (or leave blank to skip): ").strip()
        if api_key and write:
            result.env_written["OPENAI_API_KEY"] = api_key

    if not api_key:
        _warn("OpenAI   — OPENAI_API_KEY not set (use --interactive to enter)")
        result.status = "skipped"
        result.error = "no api key"
        return result

    result.token_present = True

    # Validate key format (sk-... or sk-proj-...)
    if not re.match(r"^sk-", api_key):
        _warn("OpenAI   — key doesn't start with `sk-` (may be invalid)")
        result.notes.append("API key format looks unexpected (should start with sk-)")

    # Probe /v1/models
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    status, data, latency = _probe_url("https://api.openai.com/v1/models", headers=headers, timeout=8)
    result.latency_ms = latency

    if status == 200 and isinstance(data, dict):
        model_ids = [m.get("id", "") for m in (data.get("data") or []) if "gpt" in m.get("id", "")]
        result.model = model_ids[0] if model_ids else "unknown"
        _ok(f"OpenAI   — valid key ✓  ({latency:.0f}ms)  example model: {result.model}")
        result.status = "ok"
    elif status == 401:
        _fail("OpenAI   — 401 Unauthorized. Key is invalid or revoked.")
        result.status = "fail"
        result.error = "401 — invalid api key"
        result.notes.append("Generate a new key at: https://platform.openai.com/api-keys")
    elif status == 429:
        _warn("OpenAI   — 429 rate limited but key is likely valid")
        result.status = "warn"
        result.error = "429 rate limit"
    elif status == -1:
        _warn("OpenAI   — could not reach api.openai.com (network issue?)")
        # Key may still be fine; treat as warn not fail
        result.status = "warn"
        result.error = "connection failed"
    else:
        _warn(f"OpenAI   — unexpected response {status}")
        result.status = "warn"
        result.error = f"HTTP {status}"

    return result


# ── Aggregate runner ──────────────────────────────────────────────────────────


def run(
    providers: list[str],
    settings: dict[str, Any],
    *,
    rotate: bool = False,
    write: bool = False,
    interactive: bool = False,
    use_az_cli: bool = False,
    pull_model: str = "",
) -> list[ProviderResult]:
    env = _effective_env(settings)
    results: list[ProviderResult] = []
    pending_writes: dict[str, str] = {}

    for prov in providers:
        if prov in ("ollama",):
            r = probe_ollama(env, rotate=rotate, pull_model=pull_model, write=write, interactive=interactive)
        elif prov in ("lmstudio", "lm_studio", "lm-studio"):
            r = probe_lmstudio(env, rotate=rotate, write=write, interactive=interactive)
        elif prov in ("azure", "azure_openai", "azure-openai"):
            r = probe_azure_openai(env, use_az_cli=use_az_cli, rotate=rotate, write=write, interactive=interactive)
        elif prov in ("openai",):
            r = probe_openai(env, rotate=rotate, write=write, interactive=interactive)
        else:
            _warn(f"Unknown provider '{prov}' — skipping")
            continue

        results.append(r)
        pending_writes.update(r.env_written)

    if write and pending_writes:
        values = settings.setdefault("Values", {})
        for k, v in pending_writes.items():
            values[k] = v
        _save_settings(settings)
        _info(f"Updated {len(pending_writes)} key(s): {', '.join(pending_writes)}")

    return results


# ── Summary rendering ─────────────────────────────────────────────────────────


def _render_summary(results: list[ProviderResult]) -> None:
    _head("Provider Token Status")
    width = 60
    print(f"  {'Provider':<18}{'Status':<10}{'Token':<8}{'Endpoint / Notes'}")
    print(f"  {'─' * 16}  {'─' * 8}  {'─' * 6}  {'─' * (width - 36)}")
    for r in results:
        icon = {
            "ok": _GREEN + "✅ ok" + _RESET,
            "warn": _YELLOW + "⚠  warn" + _RESET,
            "fail": _RED + "❌ fail" + _RESET,
            "skipped": "── skip",
        }.get(r.status, r.status)
        token_s = ("🔑 yes" if r.token_present else "🚫 no ") if r.name != "ollama" else "none  "
        ep = r.endpoint[:40] if r.endpoint else ""
        print(f"  {r.name:<18}{icon:<22}{token_s:<14}{ep}")
        for note in r.notes:
            print(f"    {'':18}{_YELLOW}↳ {note}{_RESET}")

    healthy = sum(1 for r in results if r.status == "ok")
    print(f"\n  {_BOLD}Healthy providers: {healthy}/{len(results)}{_RESET}")


def _write_json_status(results: list[ProviderResult]) -> None:
    """Write machine-readable status to data_out/ai_token_status.json."""
    STATUS_OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "healthy": sum(1 for r in results if r.status == "ok"),
        "total": len(results),
        "providers": {
            r.name: {
                "status": r.status,
                "token_present": r.token_present,
                "token_generated": r.token_generated,
                "token_rotated": r.token_rotated,
                "endpoint": r.endpoint,
                "model": r.model,
                "latency_ms": round(r.latency_ms, 1),
                "error": r.error,
                "notes": r.notes,
            }
            for r in results
        },
    }
    STATUS_OUT.write_text(json.dumps(payload, indent=2))


# ── CLI ───────────────────────────────────────────────────────────────────────

_ALL_PROVIDERS = ["ollama", "lmstudio", "azure", "openai"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate, validate, and rotate AI provider tokens.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--provider",
        "-p",
        default="all",
        help="Provider to probe: ollama|lmstudio|azure|openai|all (default: all)",
    )
    parser.add_argument(
        "--write",
        "-w",
        action="store_true",
        help="Write validated/generated tokens back to local.settings.json",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Prompt for missing values interactively",
    )
    parser.add_argument(
        "--rotate",
        "-r",
        action="store_true",
        help="Generate fresh tokens even if existing ones are valid (LM Studio)",
    )
    parser.add_argument(
        "--use-az-cli",
        action="store_true",
        help="Get Azure OpenAI token via `az account get-access-token` (requires az login)",
    )
    parser.add_argument(
        "--pull-model",
        metavar="MODEL",
        default="",
        help="Pull this Ollama model if not already installed (e.g. llama3.2)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON to stdout (and still write status file)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Resolve provider list
    if args.provider.lower() == "all":
        providers = list(_ALL_PROVIDERS)
    else:
        providers = [p.strip().lower() for p in args.provider.split(",") if p.strip()]

    _head("AI Token Generator")
    _info(f"Providers: {', '.join(providers)}")
    if args.write:
        _info(f"Will write validated tokens → {LOCAL_SETTINGS.name}")
    if args.rotate:
        _info("Token rotation enabled")
    if args.use_az_cli:
        _info("Azure CLI token exchange enabled")
    print()

    settings = _load_settings()

    results = run(
        providers=providers,
        settings=settings,
        rotate=args.rotate,
        write=args.write,
        interactive=args.interactive,
        use_az_cli=args.use_az_cli,
        pull_model=args.pull_model,
    )

    if not results:
        _fail("No providers checked.")
        return 2

    if args.json:
        # JSON to stdout
        payload = {
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "healthy": sum(1 for r in results if r.status == "ok"),
            "total": len(results),
            "providers": {
                r.name: {
                    "status": r.status,
                    "token_present": r.token_present,
                    "model": r.model,
                    "latency_ms": round(r.latency_ms, 1),
                    "error": r.error,
                }
                for r in results
            },
        }
        print(json.dumps(payload, indent=2))
    else:
        _render_summary(results)

    # Always write status file
    _write_json_status(results)
    try:
        _info(f"Status written → {STATUS_OUT.relative_to(REPO_ROOT)}")
    except ValueError:
        _info(f"Status written → {STATUS_OUT}")

    # Exit 0 if at least one OK provider
    healthy = sum(1 for r in results if r.status == "ok")
    return 0 if healthy > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
