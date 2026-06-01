#!/usr/bin/env python3
"""Fast integration smoke checks for the Aria repository.

This script validates critical integration wiring without running full test suites.
It is safe for local development and CI gates.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    from .config_paths import canonical_config_path, get_config_candidates, resolve_existing_config_path
except ImportError:
    from config_paths import canonical_config_path, get_config_candidates, resolve_existing_config_path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "integration_smoke"
# Adapter startup can be slow in cold/containerized environments because
# importing `function_app` initializes multiple subsystems. Keep this timeout
# comfortably above typical observed startup (~13s) to avoid false negatives.
LOCAL_DEV_ADAPTER_PROBE_TIMEOUT_SEC = 25.0
LOCAL_DEV_ADAPTER_REQUEST_TIMEOUT_SEC = 10.0

_REQUIRED_AI_STATUS_KEYS = {"active_provider", "settings", "endpoints", "status"}
_REQUIRED_AI_STATUS_ENDPOINTS = {
    "/api/ai/status",
    "/api/chat",
    "/api/chat-web",
    "/api/tts",
    "/api/quantum/run",
}
_REQUIRED_AI_ROUTE_NAMES = {
    "ai/status",
    "chat",
    "chat-web",
    "agi/stream",
}


@dataclass
class StepResult:
    name: str
    status: str
    critical: bool
    duration_sec: float
    detail: str = ""


def _run_command(
    name: str,
    cmd: List[str],
    *,
    critical: bool = True,
    timeout: int = 180,
) -> StepResult:
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        duration = round(time.perf_counter() - start, 2)
        status = "succeeded" if proc.returncode == 0 else "failed"

        tail_stdout = (proc.stdout or "").strip()[-400:]
        tail_stderr = (proc.stderr or "").strip()[-400:]
        detail_parts = [f"rc={proc.returncode}"]
        if tail_stdout:
            detail_parts.append(f"stdout={tail_stdout}")
        if tail_stderr:
            detail_parts.append(f"stderr={tail_stderr}")

        return StepResult(
            name=name,
            status=status,
            critical=critical,
            duration_sec=duration,
            detail=" | ".join(detail_parts),
        )
    except subprocess.TimeoutExpired:
        duration = round(time.perf_counter() - start, 2)
        return StepResult(
            name=name,
            status="timeout",
            critical=critical,
            duration_sec=duration,
            detail=f"timeout={timeout}s",
        )
    except Exception as exc:  # noqa: BLE001
        duration = round(time.perf_counter() - start, 2)
        return StepResult(
            name=name,
            status="error",
            critical=critical,
            duration_sec=duration,
            detail=str(exc),
        )


def _check_config_paths() -> List[StepResult]:
    checks = {
        "master_orchestrator_config": "master_orchestrator",
        "quantum_autorun_config": "quantum_autorun",
        "evaluation_autorun_config": "evaluation_autorun",
    }

    results: List[StepResult] = []
    for name, config_key in checks.items():
        candidates = get_config_candidates(REPO_ROOT, config_key)
        canonical = canonical_config_path(REPO_ROOT, config_key)
        start = time.perf_counter()
        found: Optional[Path] = next((p for p in candidates if p.exists()), None)
        duration = round(time.perf_counter() - start, 2)

        if found is None:
            results.append(
                StepResult(
                    name=name,
                    status="failed",
                    critical=True,
                    duration_sec=duration,
                    detail="missing canonical and legacy config",
                )
            )
            continue

        if found == canonical:
            results.append(
                StepResult(
                    name=name,
                    status="succeeded",
                    critical=True,
                    duration_sec=duration,
                    detail=f"resolved={found.relative_to(REPO_ROOT)}",
                )
            )
        else:
            results.append(
                StepResult(
                    name=name,
                    status="warning",
                    critical=False,
                    duration_sec=duration,
                    detail=("using legacy path; prefer " f"{canonical.relative_to(REPO_ROOT)}"),
                )
            )

    return results


def _fetch_local_functions_payload(url: str, timeout: int = 2) -> Dict[str, Any]:
    """Fetch and parse the local Functions status payload."""
    with urlopen(url, timeout=timeout) as resp:  # noqa: S310 - local probe
        return json.loads(resp.read().decode("utf-8"))


def _fetch_local_functions_json(
    url: str,
    *,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 5,
) -> Dict[str, Any]:
    """Fetch and parse a JSON response from local Functions endpoints."""
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url=url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 - local probe
        return json.loads(resp.read().decode("utf-8"))


def _fetch_local_functions_sse(
    url: str,
    *,
    payload: Dict[str, Any],
    timeout: int = 8,
) -> str:
    """Fetch raw SSE body text from local Functions endpoints."""
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 - local probe
        return resp.read().decode("utf-8", errors="replace")


def _local_dev_adapter_command(url: str) -> List[str]:
    """Build the adapter command for the target local Functions URL."""

    parsed = urlparse(url)
    port = parsed.port or 7071
    return [sys.executable, "local_dev_adapter.py", "--port", str(port)]


def _probe_with_local_dev_adapter(url: str) -> Optional[Dict[str, Any]]:
    """Best-effort fallback: start local adapter and retry endpoint probe."""
    proc: Optional[subprocess.Popen[str]] = None
    deadline = time.time() + LOCAL_DEV_ADAPTER_PROBE_TIMEOUT_SEC

    try:
        proc = subprocess.Popen(
            _local_dev_adapter_command(url),
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        while time.time() < deadline:
            try:
                remaining = max(1.0, deadline - time.time())
                request_timeout = min(
                    LOCAL_DEV_ADAPTER_REQUEST_TIMEOUT_SEC,
                    remaining,
                )
                return _fetch_local_functions_payload(url, timeout=request_timeout)
            except (URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
                time.sleep(0.25)

        return None
    except OSError:
        return None
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()


def _probe_with_local_dev_adapter_request(
    *,
    url: str,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    sse: bool = False,
) -> Optional[Any]:
    """Best-effort adapter probe for arbitrary local Functions endpoints."""
    proc: Optional[subprocess.Popen[str]] = None
    deadline = time.time() + LOCAL_DEV_ADAPTER_PROBE_TIMEOUT_SEC

    try:
        proc = subprocess.Popen(
            _local_dev_adapter_command(url),
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        while time.time() < deadline:
            try:
                remaining = max(1.0, deadline - time.time())
                request_timeout = min(
                    LOCAL_DEV_ADAPTER_REQUEST_TIMEOUT_SEC,
                    remaining,
                )
                if sse:
                    return _fetch_local_functions_sse(
                        url,
                        payload=payload or {},
                        timeout=int(request_timeout),
                    )
                return _fetch_local_functions_json(
                    url,
                    method=method,
                    payload=payload,
                    timeout=int(request_timeout),
                )
            except (URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
                time.sleep(0.25)

        return None
    except OSError:
        return None
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()


def _probe_agi_endpoints(strict: bool) -> List[StepResult]:
    """Probe AGI HTTP routes with minimal contract checks."""
    results: List[StepResult] = []

    endpoints = [
        {
            "name": "functions_agi_status_endpoint",
            "url": "http://localhost:7071/api/agi/status",
            "method": "GET",
            "payload": None,
            "required_key": "available",
            "sse": False,
        },
        {
            "name": "functions_agi_analyze_endpoint",
            "url": "http://localhost:7071/api/agi/analyze",
            "method": "POST",
            "payload": {"query": "integration smoke analyze"},
            "required_key": "analysis",
            "sse": False,
        },
        {
            "name": "functions_agi_stream_endpoint",
            "url": "http://localhost:7071/api/agi/stream",
            "method": "POST",
            "payload": {"query": "integration smoke stream"},
            "required_key": "data: [DONE]",
            "sse": True,
        },
    ]

    for ep in endpoints:
        start = time.perf_counter()
        try:
            if ep["sse"]:
                body = _fetch_local_functions_sse(
                    ep["url"],
                    payload=ep["payload"] or {},
                    timeout=LOCAL_DEV_ADAPTER_REQUEST_TIMEOUT_SEC,
                )
                ok = ep["required_key"] in body and '"delta"' in body
                if not ok:
                    raise ValueError("stream_missing_expected_sse_markers")
                detail = "sse=[DONE]+delta"
            else:
                payload = _fetch_local_functions_json(
                    ep["url"],
                    method=ep["method"],
                    payload=ep["payload"],
                    timeout=LOCAL_DEV_ADAPTER_REQUEST_TIMEOUT_SEC,
                )
                if ep["required_key"] not in payload:
                    raise ValueError(f"missing_key={ep['required_key']}")
                detail = f"has_key={ep['required_key']}"

            duration = round(time.perf_counter() - start, 2)
            results.append(
                StepResult(
                    name=ep["name"],
                    status="succeeded",
                    critical=strict,
                    duration_sec=duration,
                    detail=detail,
                )
            )
        except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
            duration = round(time.perf_counter() - start, 2)
            if strict:
                fallback = _probe_with_local_dev_adapter_request(
                    url=ep["url"],
                    method=ep["method"],
                    payload=ep["payload"],
                    sse=bool(ep["sse"]),
                )
                if fallback is not None:
                    if ep["sse"]:
                        if ep["required_key"] in fallback and '"delta"' in fallback:
                            results.append(
                                StepResult(
                                    name=ep["name"],
                                    status="succeeded",
                                    critical=True,
                                    duration_sec=duration,
                                    detail="sse=[DONE]+delta | via=local_dev_adapter",
                                )
                            )
                            continue
                    elif isinstance(fallback, dict) and ep["required_key"] in fallback:
                        results.append(
                            StepResult(
                                name=ep["name"],
                                status="succeeded",
                                critical=True,
                                duration_sec=duration,
                                detail=f"has_key={ep['required_key']} | via=local_dev_adapter",
                            )
                        )
                        continue

                results.append(
                    StepResult(
                        name=ep["name"],
                        status="failed",
                        critical=True,
                        duration_sec=duration,
                        detail=f"endpoint_unreachable={ep['url']}",
                    )
                )
            else:
                results.append(
                    StepResult(
                        name=ep["name"],
                        status="skipped",
                        critical=False,
                        duration_sec=duration,
                        detail="functions host not running (non-strict mode)",
                    )
                )

    return results


def _probe_functions_endpoint(strict: bool) -> StepResult:
    name = "functions_ai_status_endpoint"
    start = time.perf_counter()
    url = "http://localhost:7071/api/ai/status"

    def _build_success_detail(payload: Dict[str, Any], source: str = "") -> Optional[str]:
        valid, detail = _validate_ai_status_payload(payload)
        if not valid:
            return None
        return f"{detail}{source}"

    try:
        payload = _fetch_local_functions_payload(url)
        detail = _build_success_detail(payload)
        duration = round(time.perf_counter() - start, 2)
        if detail is not None:
            return StepResult(
                name=name,
                status="succeeded",
                critical=strict,
                duration_sec=duration,
                detail=detail,
            )
        return StepResult(
            name=name,
            status="failed",
            critical=strict,
            duration_sec=duration,
            detail="invalid_ai_status_payload",
        )
    except (URLError, TimeoutError, OSError):
        duration = round(time.perf_counter() - start, 2)
        if strict:
            # First retry directly to absorb transient startup races.
            for _ in range(2):
                time.sleep(0.25)
                try:
                    payload = _fetch_local_functions_payload(url)
                    detail = _build_success_detail(payload, " | via=direct_retry")
                    duration = round(time.perf_counter() - start, 2)
                    if detail is not None:
                        return StepResult(
                            name=name,
                            status="succeeded",
                            critical=True,
                            duration_sec=duration,
                            detail=detail,
                        )
                except (URLError, TimeoutError, OSError):
                    continue

            fallback_payload = _probe_with_local_dev_adapter(url)
            if fallback_payload is not None:
                detail = _build_success_detail(fallback_payload, " | via=local_dev_adapter")
                if detail is not None:
                    duration = round(time.perf_counter() - start, 2)
                    return StepResult(
                        name=name,
                        status="succeeded",
                        critical=True,
                        duration_sec=duration,
                        detail=detail,
                    )

            # Final direct retry covers the case where adapter startup fails
            # because another process is already bound to :7071.
            try:
                payload = _fetch_local_functions_payload(url)
                detail = _build_success_detail(payload, " | via=final_direct_retry")
                duration = round(time.perf_counter() - start, 2)
                if detail is not None:
                    return StepResult(
                        name=name,
                        status="succeeded",
                        critical=True,
                        duration_sec=duration,
                        detail=detail,
                    )
            except (URLError, TimeoutError, OSError):
                return StepResult(
                    name=name,
                    status="failed",
                    critical=True,
                    duration_sec=duration,
                    detail=f"endpoint_unreachable={url}",
                )
        return StepResult(
            name=name,
            status="skipped",
            critical=False,
            duration_sec=duration,
            detail="functions host not running (non-strict mode)",
        )
    except Exception as exc:  # noqa: BLE001
        duration = round(time.perf_counter() - start, 2)
        return StepResult(
            name=name,
            status="error",
            critical=strict,
            duration_sec=duration,
            detail=str(exc),
        )


def _validate_ai_status_payload(payload: Dict[str, Any]) -> tuple[bool, str]:
    missing_keys = sorted(k for k in _REQUIRED_AI_STATUS_KEYS if k not in payload)
    if missing_keys:
        return False, f"missing_keys={','.join(missing_keys)}"

    if payload.get("status") != "ok":
        return False, f"status={payload.get('status')}"

    settings = payload.get("settings")
    if not isinstance(settings, dict):
        return False, "settings_not_dict"

    provider_chain = settings.get("provider_chain")
    if not isinstance(provider_chain, list) or not provider_chain:
        return False, "provider_chain_missing_or_empty"

    if not settings.get("active_provider"):
        return False, "settings_active_provider_missing"

    endpoints = payload.get("endpoints")
    if not isinstance(endpoints, list):
        return False, "endpoints_not_list"

    missing_endpoints = sorted(_REQUIRED_AI_STATUS_ENDPOINTS - set(endpoints))
    if missing_endpoints:
        return False, f"missing_endpoints={','.join(missing_endpoints)}"

    provider = payload.get("active_provider", "unknown")
    return True, f"provider={provider} | provider_chain_len={len(provider_chain)}"


def _probe_ai_routes_endpoint(strict: bool) -> StepResult:
    name = "functions_ai_routes_endpoint"
    start = time.perf_counter()
    url = "http://localhost:7071/api/ai/routes"
    try:
        payload = _fetch_local_functions_json(url, method="GET", timeout=LOCAL_DEV_ADAPTER_REQUEST_TIMEOUT_SEC)
        detail = _validate_ai_routes_payload(payload)
        duration = round(time.perf_counter() - start, 2)
        if detail is not None:
            return StepResult(
                name=name,
                status="succeeded",
                critical=strict,
                duration_sec=duration,
                detail=detail,
            )
        return StepResult(
            name=name,
            status="failed",
            critical=strict,
            duration_sec=duration,
            detail="invalid_ai_routes_payload",
        )
    except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        duration = round(time.perf_counter() - start, 2)
        if strict:
            fallback = _probe_with_local_dev_adapter_request(
                url=url,
                method="GET",
                payload=None,
                sse=False,
            )
            if isinstance(fallback, dict):
                detail = _validate_ai_routes_payload(fallback)
                if detail is not None:
                    return StepResult(
                        name=name,
                        status="succeeded",
                        critical=True,
                        duration_sec=duration,
                        detail=f"{detail} | via=local_dev_adapter",
                    )
            return StepResult(
                name=name,
                status="failed",
                critical=True,
                duration_sec=duration,
                detail=f"endpoint_unreachable={url}",
            )
        return StepResult(
            name=name,
            status="skipped",
            critical=False,
            duration_sec=duration,
            detail="functions host not running (non-strict mode)",
        )


def _validate_ai_routes_payload(payload: Dict[str, Any]) -> Optional[str]:
    functions = payload.get("functions")
    if not isinstance(functions, list):
        return None
    route_names = {
        item.get("route") for item in functions if isinstance(item, dict) and isinstance(item.get("route"), str)
    }
    missing = sorted(_REQUIRED_AI_ROUTE_NAMES - route_names)
    if missing:
        return None
    return f"routes={len(functions)}"


def _resolved_config_paths() -> Dict[str, Optional[str]]:
    """Resolve key config paths for summary metadata."""
    config_keys = [
        "master_orchestrator",
        "quantum_autorun",
        "evaluation_autorun",
    ]
    resolved: Dict[str, Optional[str]] = {}
    for key in config_keys:
        selected = resolve_existing_config_path(REPO_ROOT, key)
        resolved[key] = str(selected.relative_to(REPO_ROOT)) if selected else None
    return resolved


def run_smoke(strict_endpoints: bool) -> Dict[str, Any]:
    steps: List[StepResult] = []

    steps.extend(_check_config_paths())

    steps.append(
        _run_command(
            "master_orchestrator_status",
            [sys.executable, "scripts/master_orchestrator.py", "--status"],
            critical=True,
        )
    )
    steps.append(
        _run_command(
            "quantum_autorun_dry_run",
            [sys.executable, "scripts/quantum_autorun.py", "--dry-run"],
            critical=True,
        )
    )
    steps.append(
        _run_command(
            "repo_automation_status",
            [sys.executable, "scripts/repo_automation.py", "--status"],
            critical=True,
        )
    )
    steps.append(
        _run_command(
            "chat_cli_local_once",
            [
                sys.executable,
                "ai-projects/chat-cli/src/chat_cli.py",
                "--provider",
                "local",
                "--once",
                "integration smoke ping",
            ],
            critical=True,
        )
    )

    steps.append(_probe_functions_endpoint(strict_endpoints))
    steps.append(_probe_ai_routes_endpoint(strict_endpoints))
    steps.extend(_probe_agi_endpoints(strict_endpoints))

    total = len(steps)
    succeeded = sum(1 for s in steps if s.status == "succeeded")
    failed_critical = [s for s in steps if s.critical and s.status not in {"succeeded", "warning"}]
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

    summary = {
        "generated_at": generated_at,
        "run_id": run_id,
        "config_path": None,
        "config_paths": _resolved_config_paths(),
        "strict_endpoints": strict_endpoints,
        "total_steps": total,
        "succeeded": succeeded,
        "warnings": sum(1 for s in steps if s.status == "warning"),
        "failed": sum(1 for s in steps if s.status == "failed"),
        "skipped": sum(1 for s in steps if s.status == "skipped"),
        "errors": sum(1 for s in steps if s.status == "error"),
        "passed": len(failed_critical) == 0,
        "results": [asdict(s) for s in steps],
    }
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Aria integration smoke checks")
    ap.add_argument(
        "--strict-endpoints",
        action="store_true",
        help="Fail if local Functions endpoint is unavailable",
    )
    ap.add_argument(
        "--output",
        default=str(DATA_OUT / "status.json"),
        help="Path to write JSON summary",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Print JSON summary to stdout",
    )
    args = ap.parse_args()

    summary = run_smoke(strict_endpoints=args.strict_endpoints)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("[integration_smoke] Summary")
        print(
            f"passed={summary['passed']} | succeeded={summary['succeeded']}/{summary['total_steps']} "
            f"| warnings={summary['warnings']} | failed={summary['failed']} | errors={summary['errors']}"
        )
        print(f"output={output_path}")

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
