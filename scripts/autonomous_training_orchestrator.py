#!/usr/bin/env python3
"""
Autonomous Training Orchestrator

Production-facing autonomous training loop referenced across docs and automation:
- Writes status to data_out/autonomous_training_status.json
- Writes heartbeat to data_out/autonomous_training_heartbeat.json
- Simulates baseline autonomous cycles (dataset discovery + training metrics)
- Integrates optional Quantum LLM training on a configurable interval

This module is simulator-first and never mutates files in datasets/.
"""

from __future__ import annotations

import argparse
import atexit
import json
import logging
import math
import os
import random
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import yaml

try:
    from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
except ImportError:  # pragma: no cover - optional dependency
    logging.getLogger(__name__).warning("tenacity not available; transient training retries are disabled")

    def retry(*args, **kwargs):  # type: ignore
        def _decorator(func):
            return func

        return _decorator

    def retry_if_exception_type(*args, **kwargs):  # type: ignore
        return Exception

    def stop_after_attempt(*args, **kwargs):  # type: ignore
        return None

    def wait_exponential(*args, **kwargs):  # type: ignore
        return None


# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------

LOG_FILE = Path("data_out") / "autonomous_training.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Paths / constants
# ----------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
# Add shared dir for config_validator import
sys.path.insert(0, str(REPO_ROOT / "shared"))
DATA_OUT_ROOT = REPO_ROOT / "data_out"
STATUS_FILE = DATA_OUT_ROOT / "autonomous_training_status.json"
HEARTBEAT_FILE = DATA_OUT_ROOT / "autonomous_training_heartbeat.json"
PID_FILE = DATA_OUT_ROOT / "autonomous_training.pid"
CONFIG_FILE = REPO_ROOT / "config" / "autonomous_training.yaml"

PLATEAU_PROMOTION_CYCLES = 5
PLATEAU_VARIANCE = 0.005
MAX_HISTORY_CYCLES = 500
_STOP_REQUESTED = False


# ----------------------------------------------------------------------------
# Status / heartbeat helpers
# ----------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now().isoformat()


def _request_stop(signum: int, _frame) -> None:
    global _STOP_REQUESTED
    logger.info("Received signal %s; graceful shutdown requested", signum)
    _STOP_REQUESTED = True


def _acquire_pidfile(*, force: bool = False) -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    if PID_FILE.exists() and not force:
        existing_pid = PID_FILE.read_text(encoding="utf-8").strip()
        if existing_pid and existing_pid.isdigit():
            try:
                os.kill(int(existing_pid), 0)
                raise RuntimeError(
                    f"Another orchestrator instance is running (pid={existing_pid}). " "Use --force-run to take over."
                )
            except ProcessLookupError:
                logger.warning("Stale pidfile detected (pid=%s); replacing", existing_pid)
            except PermissionError:
                raise RuntimeError(
                    f"Unable to verify running process for pid {existing_pid}; "
                    "refusing to continue without --force-run."
                )
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def _release_pidfile() -> None:
    try:
        if PID_FILE.exists() and PID_FILE.read_text(encoding="utf-8").strip() == str(os.getpid()):
            PID_FILE.unlink()
    except OSError:
        logger.debug("Failed to remove pidfile", exc_info=True)


@retry(
    retry=retry_if_exception_type(RuntimeError),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _run_training_cycle_with_retry(cycle_num: int, plateau_cycles: int) -> Dict[str, Any]:
    try:
        return simulate_training_cycle(cycle_num, plateau_cycles=plateau_cycles)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"transient training cycle error: {exc}") from exc


def load_config(config_path: Path = CONFIG_FILE) -> Dict[str, Any]:
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                return data
    return {}


def load_status() -> Dict[str, Any]:
    if STATUS_FILE.exists():
        with open(STATUS_FILE, encoding="utf-8") as f:
            status = json.load(f)
        history = status.get("performance_history", [])
        if len(history) > MAX_HISTORY_CYCLES:
            status["performance_history"] = history[-MAX_HISTORY_CYCLES:]
        status.setdefault("plateau_cycles", 0)
        status.setdefault("promotions", [])
        status.setdefault("dataset_inventory", {})
        status.setdefault("status", "initializing")
        status.setdefault(
            "quantum_llm",
            {
                "enabled": False,
                "status": "not_configured",
                "last_run": None,
                "last_error": None,
                "checkpoint_path": None,
                "inference_ready": False,
                "runs": 0,
            },
        )
        return status

    return {
        "cycles_completed": 0,
        "best_accuracy": 0.0,
        "last_updated": None,
        "performance_history": [],
        "dataset_inventory": {},
        "status": "initializing",
        "plateau_cycles": 0,
        "promotions": [],
        "quantum_llm": {
            "enabled": False,
            "status": "not_configured",
            "last_run": None,
            "last_error": None,
            "checkpoint_path": None,
            "inference_ready": False,
            "runs": 0,
        },
    }


def save_status(status: Dict[str, Any]) -> None:
    status["last_updated"] = _now_iso()
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


def save_heartbeat(
    state: str,
    current_cycle: int | None = None,
    next_cycle_eta: str | None = None,
    error: str | None = None,
) -> None:
    payload: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "state": state,
        "pid": os.getpid(),
    }
    if current_cycle is not None:
        payload["current_cycle"] = current_cycle
    if next_cycle_eta:
        payload["next_cycle_eta"] = next_cycle_eta
    if error:
        payload["error"] = error

    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


# ----------------------------------------------------------------------------
# Baseline autonomous cycle simulation
# ----------------------------------------------------------------------------


def discover_datasets() -> Dict[str, Dict[str, Any]]:
    datasets_dir = REPO_ROOT / "datasets"
    synthetic_dir = DATA_OUT_ROOT / "autonomous_datasets"
    inventory: Dict[str, Dict[str, Any]] = {}

    def _scan_root(root: Path, prefix: str = "") -> None:
        if not root.exists():
            return
        for category_dir in root.iterdir():
            if not category_dir.is_dir():
                continue
            files = list(category_dir.glob("**/train.json")) + list(category_dir.glob("**/train.jsonl"))
            if files:
                key = f"{prefix}{category_dir.name}" if prefix else category_dir.name
                inventory[key] = {
                    "count": len(files),
                    "paths": [str(f.relative_to(REPO_ROOT)) for f in files],
                }

    _scan_root(datasets_dir)
    _scan_root(synthetic_dir, prefix="synthetic:")
    return inventory


def _accuracy_cap(dataset_count: int) -> float:
    base = 0.95
    bonus = 0.005 * math.log1p(max(0, dataset_count - 1))
    return min(base + bonus, 0.995)


def simulate_training_cycle(
    cycle_num: int,
    *,
    accuracy_baseline: float = 0.65,
    plateau_cycles: int = 0,
) -> Dict[str, Any]:
    logger.info("Starting training cycle #%s...", cycle_num)

    datasets = discover_datasets()
    n_cats = len(datasets)
    logger.info("Found %s dataset categories: %s", n_cats, list(datasets.keys()))

    for i in range(3):
        time.sleep(2)
        progress = (i + 1) / 3
        logger.info("  Training progress: %.0f%%", progress * 100)

    cap = _accuracy_cap(n_cats)
    cycle_accuracy = accuracy_baseline + (cycle_num * 0.02) + (0.05 * (1 - (cycle_num * 0.1)))
    cycle_accuracy = min(cycle_accuracy, cap)

    if plateau_cycles > 0:
        noise = random.gauss(0, PLATEAU_VARIANCE)
        cycle_accuracy = min(cap, max(cap - 0.01, cycle_accuracy + noise))

    total_samples = sum(44968 if cat == "chat" else 10000 for cat in datasets)

    return {
        "cycle": cycle_num,
        "accuracy": round(cycle_accuracy, 6),
        "datasets_trained": n_cats,
        "samples_processed": total_samples,
        "training_time_sec": 6,
        "timestamp": _now_iso(),
    }


def promote_model(status: Dict[str, Any]) -> None:
    deployed_root = REPO_ROOT / "deployed_models"
    deployed_root.mkdir(parents=True, exist_ok=True)

    version = len(status.get("promotions", [])) + 1
    payload = {
        "version": version,
        "promoted_at": _now_iso(),
        "cycle": status.get("cycles_completed", 0),
        "accuracy": status.get("best_accuracy", 0.0),
        "dataset_inventory": status.get("dataset_inventory", {}),
    }
    out = deployed_root / f"chat_model_v{version}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info("🚀 Model v%s promoted → %s (accuracy=%.4f)", version, out, payload["accuracy"])


# ----------------------------------------------------------------------------
# Quantum LLM integration
# ----------------------------------------------------------------------------


def _resolve_repo_path(path_value: str | Path | None, default: Path) -> Path:
    if path_value is None:
        return default
    p = Path(path_value)
    return p if p.is_absolute() else (REPO_ROOT / p)


def _select_quantum_dataset() -> Path:
    chat_root = REPO_ROOT / "datasets" / "chat"
    candidates = []
    if chat_root.exists():
        candidates.extend(chat_root.glob("*/train.json"))
        candidates.extend(chat_root.glob("*/train.jsonl"))
        candidates.extend(chat_root.glob("train.json"))
        candidates.extend(chat_root.glob("train.jsonl"))
        candidates.extend(chat_root.glob("*.txt"))

    if candidates:
        return sorted(candidates)[0]
    return chat_root


def _should_run_quantum_cycle(status: Dict[str, Any], config: Dict[str, Any]) -> bool:
    qcfg = config.get("quantum_llm", {}) if isinstance(config.get("quantum_llm"), dict) else {}
    if not qcfg.get("enabled", False):
        return False

    auto_cfg = config.get("autonomous_mode", {}) if isinstance(config.get("autonomous_mode"), dict) else {}
    cycle_minutes = int(auto_cfg.get("cycle_interval_minutes", 30))
    quantum_minutes = int(qcfg.get("training_interval_minutes", 60))
    cycles_between = max(1, int(round(quantum_minutes / max(cycle_minutes, 1))))

    completed = int(status.get("cycles_completed", 0))
    if completed <= 0:
        return False

    qstatus = status.get("quantum_llm", {}) if isinstance(status.get("quantum_llm"), dict) else {}
    last_run = qstatus.get("last_run")
    if last_run:
        try:
            elapsed = (datetime.now() - datetime.fromisoformat(last_run)).total_seconds()
            if elapsed >= quantum_minutes * 60:
                return True
        except Exception:
            pass

    return (completed % cycles_between) == 0


def run_quantum_llm_training(status: Dict[str, Any], config: Dict[str, Any]) -> None:
    qcfg = config.get("quantum_llm", {}) if isinstance(config.get("quantum_llm"), dict) else {}
    quantum_status = status.get("quantum_llm", {}) if isinstance(status.get("quantum_llm"), dict) else {}

    quantum_status.setdefault("runs", 0)
    quantum_status["enabled"] = bool(qcfg.get("enabled", False))
    quantum_status["last_run"] = _now_iso()

    if not quantum_status["enabled"]:
        quantum_status.update(
            {
                "status": "disabled",
                "last_error": None,
            }
        )
        status["quantum_llm"] = quantum_status
        return

    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from quantum_llm_trainer import QuantumEnhancedLLMTrainer, get_quantum_llm_status

        trainer_config: Dict[str, Any] = {
            "quantum_backend": qcfg.get("backend", "local"),
            "n_qubits": qcfg.get("n_qubits", 4),
            "n_quantum_layers": qcfg.get("n_quantum_layers", 2),
            "passive": False,
            "output": {
                "save_dir": "data_out/quantum_llm_training",
            },
            "status_file": "data_out/quantum_llm_training/status.json",
        }

        config_file = _resolve_repo_path(qcfg.get("config_file"), REPO_ROOT / "config" / "quantum_llm_config.yaml")
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                file_cfg = yaml.safe_load(f) or {}
            if isinstance(file_cfg, dict):
                trainer_config.update(file_cfg)

        trainer = QuantumEnhancedLLMTrainer(trainer_config)
        dataset_path = _select_quantum_dataset()
        output_dir = REPO_ROOT / "data_out" / "quantum_llm_training"
        results = trainer.train_with_quantum_enhancement(
            dataset_path=dataset_path,
            output_dir=output_dir,
            epochs=1,
            model=None,
        )

        readiness = get_quantum_llm_status(output_dir=output_dir)
        quantum_status.update(
            {
                "status": "completed",
                "runs": int(quantum_status.get("runs", 0)) + 1,
                "last_error": None,
                "dataset_path": (
                    str(dataset_path.relative_to(REPO_ROOT)) if dataset_path.exists() else str(dataset_path)
                ),
                "epochs_completed": results.get("epochs_completed"),
                "final_loss": results.get("final_loss"),
                "best_loss": results.get("best_loss"),
                "checkpoint_path": readiness.get("checkpoint_path"),
                "inference_ready": bool(readiness.get("inference_ready")),
                "trainer_status": readiness.get("status"),
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Quantum LLM training step failed: %s", exc)
        quantum_status.update(
            {
                "status": "failed",
                "runs": int(quantum_status.get("runs", 0)) + 1,
                "last_error": str(exc),
                "inference_ready": False,
            }
        )

    status["quantum_llm"] = quantum_status


# ----------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------


def run_autonomously(
    *,
    config: Dict[str, Any],
    max_cycles: int | None = None,
    cycle_interval_sec: int | None = None,
    skip_quantum: bool = False,
) -> int:
    global _STOP_REQUESTED
    _STOP_REQUESTED = False
    status = load_status()

    auto_cfg = config.get("autonomous_mode", {}) if isinstance(config.get("autonomous_mode"), dict) else {}
    configured_max_cycles = int(auto_cfg.get("max_cycles", 0))
    configured_interval_sec = int(auto_cfg.get("cycle_interval_minutes", 30)) * 60

    if max_cycles is None:
        max_cycles = configured_max_cycles
    if cycle_interval_sec is None:
        cycle_interval_sec = configured_interval_sec

    start_cycle = int(status.get("cycles_completed", 0))
    infinite_mode = max_cycles <= 0
    end_cycle = start_cycle + max_cycles if not infinite_mode else None

    status.setdefault("started_at", _now_iso())
    status["run_mode"] = "infinite" if infinite_mode else "bounded"
    status["cycle_interval_sec"] = cycle_interval_sec
    status["status"] = "running"
    status["current_cycle"] = start_cycle
    status["next_cycle_eta"] = None
    save_status(status)
    save_heartbeat("running", current_cycle=start_cycle)

    logger.info("=" * 70)
    logger.info("🤖 AUTONOMOUS AI TRAINING ORCHESTRATOR")
    logger.info("=" * 70)
    if infinite_mode:
        logger.info("Starting continuous training mode (infinite cycles)...")
    else:
        logger.info("Starting bounded training mode (max %s cycles)...", max_cycles)
    logger.info("Cycle interval: %ss", cycle_interval_sec)

    status.setdefault("plateau_cycles", 0)
    status.setdefault("promotions", [])

    try:
        cycle_num = start_cycle
        while True:
            if _STOP_REQUESTED:
                logger.info("Stop requested; ending autonomous loop")
                break
            if not infinite_mode and end_cycle is not None and cycle_num >= end_cycle:
                break

            logger.info("\n%s", "=" * 70)
            logger.info("CYCLE %s", cycle_num + 1)
            logger.info("%s", "=" * 70)

            status["status"] = "training"
            status["current_cycle"] = cycle_num + 1
            save_status(status)
            save_heartbeat("training", current_cycle=cycle_num + 1)

            result = _run_training_cycle_with_retry(cycle_num + 1, int(status.get("plateau_cycles", 0)))

            status["cycles_completed"] = cycle_num + 1
            history = status.get("performance_history", [])
            history.append(result)
            if len(history) > MAX_HISTORY_CYCLES:
                history = history[-MAX_HISTORY_CYCLES:]
            status["performance_history"] = history

            if result["accuracy"] > float(status.get("best_accuracy", 0.0)):
                status["best_accuracy"] = result["accuracy"]
                status["plateau_cycles"] = 0
                logger.info("✨ New best accuracy: %.4f", result["accuracy"])
            else:
                status["plateau_cycles"] = int(status.get("plateau_cycles", 0)) + 1
                logger.info(
                    "Current accuracy: %.4f (best: %.4f, plateau: %s cycles)",
                    result["accuracy"],
                    float(status.get("best_accuracy", 0.0)),
                    status["plateau_cycles"],
                )

            if (
                int(status.get("plateau_cycles", 0)) > 0
                and int(status.get("plateau_cycles", 0)) % PLATEAU_PROMOTION_CYCLES == 0
            ):
                logger.info(
                    "📦 Plateau reached %s stable cycles — promoting model...",
                    status["plateau_cycles"],
                )
                promote_model(status)
                status.setdefault("promotions", []).append(
                    {
                        "version": len(status.get("promotions", [])) + 1,
                        "cycle": status["cycles_completed"],
                        "accuracy": status["best_accuracy"],
                        "promoted_at": _now_iso(),
                    }
                )

            status["dataset_inventory"] = discover_datasets()

            if not skip_quantum and _should_run_quantum_cycle(status, config):
                logger.info("🔬 Running scheduled Quantum LLM training step...")
                run_quantum_llm_training(status, config)
            else:
                qstate = status.get("quantum_llm", {}) if isinstance(status.get("quantum_llm"), dict) else {}
                qstate["enabled"] = bool(config.get("quantum_llm", {}).get("enabled", False))
                qstate["status"] = "idle"
                qstate["last_error"] = None
                status["quantum_llm"] = qstate

            cycle_num += 1
            status["status"] = "running"
            if not infinite_mode and end_cycle is not None and cycle_num >= end_cycle:
                status["next_cycle_eta"] = None
            else:
                status["next_cycle_eta"] = (datetime.now() + timedelta(seconds=cycle_interval_sec)).isoformat()

            save_status(status)
            save_heartbeat(
                "running",
                current_cycle=status["cycles_completed"],
                next_cycle_eta=status.get("next_cycle_eta"),
            )

            if not infinite_mode and end_cycle is not None and cycle_num >= end_cycle:
                break

            logger.info("Cycle complete. Next cycle in %ss...", cycle_interval_sec)
            if cycle_interval_sec > 0:
                for _ in range(cycle_interval_sec):
                    if _STOP_REQUESTED:
                        break
                    time.sleep(1)

        if _STOP_REQUESTED:
            status["status"] = "stopped"
            status["next_cycle_eta"] = None
            save_status(status)
            save_heartbeat("stopped", current_cycle=status.get("cycles_completed", 0))
        elif not infinite_mode:
            logger.info("\n%s", "=" * 70)
            logger.info("🎉 TRAINING COMPLETE")
            logger.info("%s", "=" * 70)
            logger.info("Cycles completed: %s", status.get("cycles_completed", 0))
            logger.info("Best accuracy: %.4f", float(status.get("best_accuracy", 0.0)))
            logger.info("Datasets discovered: %s", len(status.get("dataset_inventory", {})))

            status["status"] = "completed"
            status["current_cycle"] = status.get("cycles_completed", 0)
            status["next_cycle_eta"] = None
            save_status(status)
            save_heartbeat("completed", current_cycle=status.get("cycles_completed", 0))

        return 0

    except KeyboardInterrupt:
        logger.info("\n⏸️  Training interrupted")
        status["status"] = "paused"
        status["next_cycle_eta"] = None
        save_status(status)
        save_heartbeat("paused", current_cycle=status.get("cycles_completed", 0))
        return 130
    except Exception as exc:  # noqa: BLE001
        logger.error("❌ Training failed: %s", exc, exc_info=True)
        status["status"] = "error"
        status["error"] = str(exc)
        status["next_cycle_eta"] = None
        save_status(status)
        save_heartbeat("error", current_cycle=status.get("cycles_completed", 0), error=str(exc))
        return 1


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous training orchestrator")
    parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="Number of training cycles (0 = infinite)",
    )
    parser.add_argument("--interval", type=int, default=None, help="Seconds between cycles")
    parser.add_argument("--status", action="store_true", help="Show current status and exit")
    parser.add_argument(
        "--config",
        type=str,
        default=str(CONFIG_FILE),
        help="Path to orchestrator YAML config",
    )
    parser.add_argument(
        "--skip-quantum",
        action="store_true",
        help="Skip Quantum LLM step even if enabled",
    )
    parser.add_argument(
        "--force-run",
        action="store_true",
        help="Allow starting even when pidfile is present",
    )

    args = parser.parse_args()

    if args.status:
        print(json.dumps(load_status(), indent=2))
        return 0

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path

    # Validate configuration before proceeding
    try:
        from shared.config_validator import ConfigValidator
    except ImportError:
        from config_validator import ConfigValidator

    validator = ConfigValidator(REPO_ROOT)
    result = validator.validate_autonomous_training(config_path)
    if not result.valid:
        logger.error("❌ Configuration validation failed:")
        logger.error(result.report(verbose=True))
        return 1

    config = load_config(config_path)
    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)
    _acquire_pidfile(force=args.force_run)
    atexit.register(_release_pidfile)
    try:
        return run_autonomously(
            config=config,
            max_cycles=args.cycles,
            cycle_interval_sec=args.interval,
            skip_quantum=args.skip_quantum,
        )
    finally:
        _release_pidfile()


if __name__ == "__main__":
    sys.exit(main())
