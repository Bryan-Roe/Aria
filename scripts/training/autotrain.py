#!/usr/bin/env python
r"""
AutoTrain Orchestrator

Lightweight runner to automate model fine-tuning jobs defined in a YAML config.

Goals:
- Zero external services required (works fully offline)
- Sequential job execution with clear logs and machine-readable status
- Supports two runners:
  - hf: calls AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py (full HF stack)
  - local: calls scripts/run_local_lora_training.py (streamlined local runner)

Outputs:
- data_out/autotrain/<job_name>/<timestamp>/stdout.log        (verbatim process output)
- data_out/autotrain/<job_name>/last_run.json                 (last run metadata)
- data_out/autotrain/status.json                              (summary of all jobs)

Usage examples (PowerShell):
    python .\scripts\autotrain.py --dry-run
    python .\scripts\autotrain.py --job phi36_mixed_chat
    python .\scripts\autotrain.py --job phi36_mixed_chat --reinstall  # when using local runner
"""

from __future__ import annotations

import logging

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

# Optional DB logging (safe no-op if not configured)
try:  # noqa: SIM105
    from shared.db_logging import log_lora_run_safe  # type: ignore
except Exception:  # noqa: BLE001

    # type: ignore
    def log_lora_run_safe(*_a: Any, **_kw: Any) -> Dict[str, Any]:
        """Fallback safe no-op logging function used when DB logging isn't configured.

        Typed to satisfy static type checkers.
        """
        return {"success": False, "skipped": True}

try:
    import yaml  # type: ignore
except Exception:  # noqa: BLE001
    # Allow importing this module even if pyyaml is not installed so tests and
    # tooling can import functions without requiring optional deps at module
    # import time. Provide a very small in-file fallback YAML loader for the
    # minimal subset used by unit tests (mappings, lists, simple scalars).
    yaml = None


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "autotrain"
HF_TRAIN_SCRIPT = REPO_ROOT / "AI" / \
    "microsoft_phi-silica-3.6_v1" / "scripts" / "train_lora.py"
LOCAL_RUNNER = REPO_ROOT / "scripts" / "run_local_lora_training.py"


@dataclass
class Job:
    name: str
    runner: str = "hf"  # "hf" | "local"
    category: Optional[str] = None
    dataset: Optional[str] = None
    config: Optional[str] = None
    save_dir: Optional[str] = None
    # Optional overrides
    learning_rate: Optional[float] = None
    lora_dropout: Optional[float] = None
    epochs: Optional[int] = None
    max_train_samples: Optional[int] = None
    max_eval_samples: Optional[int] = None
    seed: Optional[int] = None
    hf_model_id: Optional[str] = None
    no_stream: bool = False  # disable streaming dataset for stability on small GPU runs
    # explicit device preference (auto|cuda|cpu|directml|mps)
    device: Optional[str] = None
    # Local runner specific
    # Forces dependency reinstallation when using the local runner (--reinstall flag)
    reinstall: bool = False
    # Ensure the default factory is typed as List[str] for static checkers
    extra_args: List[str] = field(default_factory=lambda: cast(List[str], []))


def read_yaml(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        # Use PyYAML when available for full-featured parsing
        return yaml.safe_load(text) or {}

    # Very small, permissive YAML subset parser used as a fallback in test
    # environments where PyYAML isn't available. It supports:
    # - top-level mappings (key: value)
    # - simple lists ("- item") and lists of mappings ("- key: value")
    # - null/None values using 'null' / 'None' / '~'
    # - booleans true/false and integers/floats
    def _convert_scalar(val: str):
        if val is None:
            return None
        v = val.strip()
        if v == "" or v in ("null", "Null", "NULL", "~", "None", "none"):
            return None
        if v in ("true", "True", "TRUE"):
            return True
        if v in ("false", "False", "FALSE"):
            return False
        # Try integer then float then fallback to string
        try:
            return int(v)
        except Exception:
            try:
                return float(v)
            except Exception:
                return v

    root: Dict[str, Any] = {}
    stack: List[tuple[int, Any]] = [(-1, root)]

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.lstrip(" ")

        # Pop stack until we find the correct parent context for the current
        # indentation level.
        while stack and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        if content.startswith("- "):
            item_text = content[2:].strip()
            # If parent is a dict, make sure the last key holds a list
            if isinstance(parent, dict):
                if not parent:
                    # No key to attach list to; create a synthetic list key
                    # (unlikely in our tests) and attach it to a numeric key.
                    key = "_list"
                    parent.setdefault(key, [])
                last_key = next(reversed(parent))
                if parent[last_key] is None or not isinstance(parent[last_key], list):
                    parent[last_key] = []
                lst = parent[last_key]
                # Ensure stack knows about this list container
                stack.append((indent, lst))
                parent = lst

            # Now parent should be a list
            if item_text == "":
                # empty list item; create an empty dict placeholder
                new_item: Any = {}
                parent.append(new_item)
                # allow nested children under this new item
                stack.append((indent, new_item))
            elif ":" in item_text:
                key, val = (x.strip() for x in item_text.split(":", 1))
                val_parsed = _convert_scalar(val) if val != "" else None
                new_item = {key: val_parsed}
                parent.append(new_item)
                if val_parsed is None:
                    # value may contain nested children in following lines
                    stack.append((indent, new_item))
            else:
                parent.append(_convert_scalar(item_text))

        elif ":" in content:
            key, val = (x.strip() for x in content.split(":", 1))
            # If parent is a list, attach mappings to the last element
            if isinstance(parent, list):
                if not parent or not isinstance(parent[-1], dict):
                    parent.append({})
                if val == "":
                    parent[-1][key] = None
                    # push the parent dict back so its nested children can be
                    # assigned on subsequent lines
                    stack.append((indent, parent))
                else:
                    parent[-1][key] = _convert_scalar(val)
            else:
                if val == "":
                    parent[key] = None
                    # push current parent so nested children populate this key
                    stack.append((indent, parent))
                else:
                    parent[key] = _convert_scalar(val)

        else:
            # Bare scalars on a line by themselves - append into parent list if
            # present, otherwise skip.
            if isinstance(parent, list):
                parent.append(_convert_scalar(content))

    return root


def load_jobs(config_path: Path) -> List[Job]:
    """Load jobs from a YAML config file and validate required fields.

    The YAML file should contain a top-level `jobs` list where each item must
    include a non-empty string `name`. If a job is missing `name` or its
    `name` is empty/whitespace-only, a ValueError is raised to fail fast.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        List[Job]: The parsed and validated job objects.

    Raises:
        ValueError: If the `jobs` array contains an entry missing a name or
            whose name is empty when stripped.
    """
    raw = read_yaml(config_path)
    jobs: List[Job] = []
    for item in raw.get("jobs", []):
        # Ensure required 'name' is present and coercible to string
        raw_name = item.get("name")
        if raw_name is None:
            raise ValueError("Every job requires a 'name'")

        # Normalize runner with a sensible default
        runner_val = item.get("runner")
        raw_runner = runner_val if runner_val is not None else "hf"

        j = Job(
            name=str(raw_name),
            runner=str(raw_runner),
            category=item.get("category"),
            dataset=item.get("dataset"),
            config=item.get("config"),
            save_dir=item.get("save_dir"),
            learning_rate=item.get("learning_rate"),
            lora_dropout=item.get("lora_dropout"),
            epochs=item.get("epochs"),
            max_train_samples=item.get("max_train_samples"),
            max_eval_samples=item.get("max_eval_samples"),
            seed=item.get("seed"),
            hf_model_id=item.get("hf_model_id"),
            no_stream=bool(item.get("no_stream", False)),
            device=item.get("device"),
            reinstall=bool(item.get("reinstall", False)),
            extra_args=list(item.get("extra_args", [])),
        )
        if not j.name.strip():
            raise ValueError("Every job requires a non-empty 'name'")
        jobs.append(j)
    return jobs


def _venv_python_default() -> Path:
    # Prefer repo root venv if it exists; else system python
    # Try Windows path first, then Linux
    venv_python_win = REPO_ROOT / "venv" / "Scripts" / "python.exe"
    venv_python_linux = REPO_ROOT / "venv" / "bin" / "python"
    if venv_python_win.exists():
        return venv_python_win
    elif venv_python_linux.exists():
        return venv_python_linux
    else:
        return Path(sys.executable)


def _venv_python_ml() -> Path:
    """Return the model-specific virtual environment python if available.

    Falls back to root venv/system python only if the model venv is missing.
    """
    # Try Windows path first, then Linux
    model_py_win = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / \
        "venv" / "Scripts" / "python.exe"
    model_py_linux = REPO_ROOT / "AI" / \
        "microsoft_phi-silica-3.6_v1" / "venv" / "bin" / "python"
    if model_py_win.exists():
        return model_py_win
    elif model_py_linux.exists():
        return model_py_linux
    else:
        return _venv_python_default()


def build_hf_command(job: Job) -> List[str]:
    py = str(_venv_python_ml())  # Use ML venv for HF training
    cmd: List[str] = [py, str(HF_TRAIN_SCRIPT)]
    # Dataset/config
    if job.config:
        cmd += ["--config", str(job.config)]
    if job.dataset:
        cmd += ["--dataset", str(job.dataset)]
    # Overrides
    if job.hf_model_id:
        cmd += ["--hf-model-id", str(job.hf_model_id)]
    if job.learning_rate is not None:
        cmd += ["--learning-rate", str(job.learning_rate)]
    if job.lora_dropout is not None:
        cmd += ["--lora-dropout", str(job.lora_dropout)]
    if job.epochs is not None:
        cmd += ["--epochs", str(job.epochs)]
    if job.max_train_samples is not None:
        cmd += ["--max-train-samples", str(job.max_train_samples)]
    if job.max_eval_samples is not None:
        cmd += ["--max-eval-samples", str(job.max_eval_samples)]
    if job.seed is not None:
        cmd += ["--seed", str(job.seed)]
    if job.save_dir:
        cmd += ["--save-dir", str(job.save_dir)]
    # Streaming control & device preference
    if job.no_stream:
        cmd += ["--no-stream"]
    if job.device:
        cmd += ["--device", str(job.device)]
    else:
        # Default to auto to pick up GPU if available
        cmd += ["--device", "auto"]
    # Pass through any extra args
    cmd += list(job.extra_args)
    return cmd


def build_local_command(job: Job) -> List[str]:
    py = str(_venv_python_default())
    cmd: List[str] = [py, str(LOCAL_RUNNER)]
    # Local runner args are different
    if job.config:
        # local runner expects bare filename under local_train; but allow full path too
        cfg = Path(job.config)
        cfg_name = cfg.name
        cmd += ["--config", cfg_name]
    if job.max_train_samples is not None:
        cmd += ["--max-samples", str(job.max_train_samples)]
    if job.epochs is not None:
        cmd += ["--epochs", str(job.epochs)]
    if job.reinstall:
        cmd += ["--reinstall"]
    # NOTE: dataset path is controlled by the local config file
    cmd += list(job.extra_args)
    return cmd


def ensure_dirs(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def run_job(job: Job, dry_run: bool = False, job_index: int = 0, total_jobs: int = 1) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    job_dir = DATA_OUT / job.name / ts
    ensure_dirs(job_dir)
    log_path = job_dir / "stdout.log"

    # Progress indicator
    progress_pct = int((job_index / max(total_jobs, 1)) * 100)
    print(
        f"\n[autotrain] [{progress_pct}%] Job {job_index + 1}/{total_jobs}: {job.name}")

    env = os.environ.copy()
    if job.hf_model_id:
        env.setdefault("HF_MODEL_ID", str(job.hf_model_id))

    if job.runner == "local":
        cmd = build_local_command(job)
    else:
        cmd = build_hf_command(job)

    result: Dict[str, Any] = {
        "name": job.name,
        "runner": job.runner,
        "category": job.category,
        "cmd": cmd,
        "start_time": ts,
        "status": "planned" if dry_run else "running",
        "return_code": None,
        "log": str(log_path),
        "output_dir": None,
    }

    # Preflight validation (applies to both dry-run and real runs)
    missing: List[str] = []
    if job.runner == "local" and not LOCAL_RUNNER.exists():
        missing.append(str(LOCAL_RUNNER))
    if job.runner == "hf" and not HF_TRAIN_SCRIPT.exists():
        missing.append(str(HF_TRAIN_SCRIPT))
    if job.dataset:
        dp = Path(job.dataset)
        if not dp.exists():
            missing.append(str(dp))

    if dry_run:
        result["status"] = "validated" if not missing else "missing"
        result["validated_type"] = "dry-run"
        if missing:
            result["missing"] = missing
        return result
    else:
        if missing:
            result["status"] = "missing"
            result["validated_type"] = "preflight"
            result["missing"] = missing
            # Create log file even for missing files error
            try:
                with log_path.open("w", encoding="utf-8") as logf:
                    logf.write(
                        f"Preflight validation failed - missing files:\n")
                    for m in missing:
                        logf.write(f"  - {m}\n")
            except Exception:
                pass
            return result
        else:
            result["validated_type"] = "preflight"

    t0 = time.time()
    with log_path.open("w", encoding="utf-8") as logf:
        logf.write(f"$ {' '.join(str(x) for x in cmd)}\n\n")
        logf.flush()
        proc = subprocess.Popen(cmd, cwd=str(
            REPO_ROOT), env=env, stdout=logf, stderr=subprocess.STDOUT, text=True)

        # Write PID file for dashboard cancellation support
        pid_file = DATA_OUT / f"{job.name}.pid"
        try:
            pid_file.write_text(str(proc.pid), encoding="utf-8")
        except Exception:
            pass

        rc = proc.wait()

        # Clean up PID file after completion
        try:
            if pid_file.exists():
                pid_file.unlink()
        except Exception:
            pass

    duration = time.time() - t0
    result["return_code"] = rc
    result["duration_sec"] = round(duration, 2)
    result["duration_human"] = f"{int(duration // 60)}m {int(duration % 60)}s"
    result["status"] = "succeeded" if rc == 0 else "failed"
    print(
        f"[autotrain] Completed in {result['duration_human']} - Status: {result['status']}")

    # Guess output directory if specified on job
    if job.save_dir:
        result["output_dir"] = str(Path(job.save_dir))
        # Attempt metrics extraction for HF jobs
        if job.runner == "hf":
            metrics_path = Path(job.save_dir) / "metrics.jsonl"
            if metrics_path.exists():
                pre_loss = pre_ppl = post_loss = post_ppl = None
                try:
                    with metrics_path.open("r", encoding="utf-8") as mf:
                        from collections import deque
                        # tail subset, memory efficient
                        for line in deque(mf, maxlen=400):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                obj = json.loads(line)
                            except Exception as e:
                                print(
                                    f"[autotrain] Failed to parse metrics line: {e}")
                                continue
                            phase = obj.get("phase")
                            if phase == "pre":
                                pre_loss = obj.get("eval_loss")
                                pre_ppl = obj.get("eval_perplexity")
                            elif phase == "post":
                                post_loss = obj.get("eval_loss")
                                post_ppl = obj.get("eval_perplexity")
                    if any(x is not None for x in (pre_loss, pre_ppl, post_loss, post_ppl)):
                        result["metrics"] = {
                            "pre_eval_loss": pre_loss,
                            "pre_eval_perplexity": pre_ppl,
                            "post_eval_loss": post_loss,
                            "post_eval_perplexity": post_ppl,
                        }
                except Exception as e:
                    print(
                        f"[autotrain] Failed to extract metrics from {metrics_path}: {e}")
                    import traceback
                    traceback.print_exc()

    # Persist last_run.json for job
    write_json(DATA_OUT / job.name / "last_run.json", result)
    return result


def collect_status(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "jobs": all_results,
    }
    write_json(DATA_OUT / "status.json", summary)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="AutoTrain orchestrator")
    ap.add_argument("--config", default=str(REPO_ROOT / "config" /
                    "training" / "autotrain.yaml"), help="Path to autotrain.yaml")
    ap.add_argument("--job", default=None, help="Run only the named job")
    ap.add_argument("--dry-run", action="store_true",
                    help="Validate and print commands; do not execute")
    ap.add_argument("--list", action="store_true",
                    help="List configured jobs and exit")
    ap.add_argument("--resume", action="store_true",
                    help="Skip jobs that recently succeeded (check last_run.json)")
    ap.add_argument("--reinstall", action="store_true",
                    help="Force reinstall for local runner jobs (alias to job.reinstall)")
    args = ap.parse_args()

    # Initialize optional tracing (best-effort)
    try:
        from shared.tracing import init_tracing

        init_tracing(service_name="autotrain")
    except Exception as _e:  # pragma: no cover - non-fatal
        logging.debug(f"[tracing] init skipped in autotrain: {_e}")

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        raise SystemExit(
            f"Config not found: {cfg_path}\n"
            f"Expected location: {REPO_ROOT / 'config' / 'training' / 'autotrain.yaml'}\n"
            "Run with --help to see configuration options or create the config file at the expected location."
        )

    try:
        jobs = load_jobs(cfg_path)
    except ValueError as e:
        print(
            f"[autotrain] ERROR: {e}\nPlease check your YAML config file for missing or empty job names. Each job must have a non-empty 'name' field.")
        raise SystemExit(2)
    if args.list:
        print(json.dumps([j.__dict__ for j in jobs], indent=2))
        return

    # Filter to a specific job if requested
    if args.job:
        jobs = [j for j in jobs if j.name == args.job]
        if not jobs:
            raise SystemExit(f"Job not found in config: {args.job}")

    # Apply global flag
    if args.reinstall:
        for j in jobs:
            if j.runner == "local":
                j.reinstall = True

    ensure_dirs(DATA_OUT)
    results: List[Dict[str, Any]] = []
    start_time = time.time()

    for idx, j in enumerate(jobs):
        # Check if job was recently completed successfully and skip if --resume
        last_run_file = DATA_OUT / j.name / "last_run.json"
        if args.resume and last_run_file.exists():
            try:
                # Only skip if the last run completed successfully
                with last_run_file.open("r", encoding="utf-8") as f:
                    last = json.load(f)
                # Narrow the type and explicitly cast the status to Optional[str].
                # When loading JSON we get Any; cast the container to Dict[str, Any]
                # first so dict.get() is statically known. Then ensure the value
                # is a string before treating it as an Optional[str].
                if isinstance(last, dict):
                    last_dict = cast(Dict[str, Any], last)
                    raw_status = last_dict.get("status")
                    status = cast(Optional[str], raw_status) if isinstance(
                        raw_status, str) else None
                    if status == "succeeded":
                        print(
                            f"[autotrain] Skipping {j.name} (already succeeded recently)")
                        # 'last' was loaded as Any from JSON; cast to the expected
                        # Dict[str, Any] before appending to results to satisfy
                        # static type checkers.
                        results.append(last_dict)
                        collect_status(results)  # incremental update
                        continue
            except Exception:
                # If anything goes wrong reading/parsing, fall through and run the job
                pass

        print(f"[autotrain] Running job: {j.name} (runner={j.runner})")

        # Insert a placeholder 'running' record before launching (for dashboard progress)
        if not args.dry_run:
            running_placeholder: Dict[str, Any] = {
                "name": j.name,
                "runner": j.runner,
                "category": j.category,
                "status": "running",
                "start_time": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                "cmd": None,
                "return_code": None,
                "duration_sec": None,
            }
            results.append(running_placeholder)
            collect_status(results)
            # Now execute the real job; replace placeholder with final result
            res = run_job(j, dry_run=False, job_index=idx,
                          total_jobs=len(jobs))
            results[-1] = res
        else:
            res = run_job(j, dry_run=True, job_index=idx, total_jobs=len(jobs))
            results.append(res)

        # Show estimated time remaining (after including this job's duration)
        if not args.dry_run and res.get("status") in {"succeeded", "failed"}:
            elapsed = time.time() - start_time
            avg_per_job = elapsed / (idx + 1)
            remaining_jobs = len(jobs) - (idx + 1)
            eta_sec = avg_per_job * remaining_jobs
            print(
                f"[autotrain] ETA for remaining jobs: {int(eta_sec // 60)}m {int(eta_sec % 60)}s")

        # Make it easier to view what happens in CI/logs
        print(json.dumps(res, indent=2))

        # === DB Logging (only on successful real runs) ===
        if not args.dry_run and res.get("status") == "succeeded":
            log_info = log_lora_run_safe(j, res)
            if log_info.get("success"):
                print(
                    f"[autotrain] Logged LoRA run to DB (run_id={log_info.get('run_id')})")
            elif log_info.get("skipped"):
                print("[autotrain] DB logging skipped (QAI_DB_CONN not set)")
            else:
                print(
                    f"[autotrain] DB logging failed: {log_info.get('error')}")

        # Incremental status write after each job
        collect_status(results)

    # Final status write (includes any skipped jobs already appended)
    collect_status(results)
    # Non-zero exit if any job failed during non-dry run
    if not args.dry_run:
        # Treat any job that failed or whose preflight validation was missing
        # required files as an overall non-zero exit. This makes CI / callers
        # aware when the orchestrator could not run all jobs successfully.
        problematic = [
            r for r in results if r.get("status") in {"failed", "missing"}
        ]
        if problematic:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
