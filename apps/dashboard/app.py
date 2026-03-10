from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
from pathlib import Path
from datetime import datetime, timedelta
import yaml
import threading
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import traceback
import subprocess
import signal
import os
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))  # Ensure scripts module is importable

from scripts.autotrain import load_jobs, Job, run_job  # reuse orchestrator logic for retry

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DATA_OUT = REPO_ROOT / "data_out"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    # Load orchestrator status
    status_files = ["autotrain/status.json", "quantum_autorun/status.json", "evaluation_autorun/status.json"]
    results = {}
    for fname in status_files:
        fpath = DATA_OUT / fname
        if fpath.exists():
            with fpath.open() as f:
                results[fname] = json.load(f)
    return jsonify(results)

@app.route("/resources")
def resources():
    # Load latest resource snapshot
    snap_path = DATA_OUT / "resource_monitor_snapshot.json"
    if snap_path.exists():
        with snap_path.open() as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No snapshot found"})

@app.route("/results")
def results():
    # Load latest exported results
    res_path = Path(__file__).resolve().parents[1] / "exports" / "all_orchestrators.json"
    if res_path.exists():
        with res_path.open() as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No results found"})

def _compute_training_progress():
    """Compute incremental AutoTrain progress with ETA and success-only percentage.

    Returns dict with:
      percent_complete: succeeded/total * 100 (failed excluded)
      percent_success_alias: same value (alias for clarity)
      eta_seconds / eta_iso: estimated remaining time until all jobs finish (based on avg succeeded duration)
      average_job_duration_seconds: mean duration of succeeded jobs
    """
    cfg_path = REPO_ROOT / "autotrain.yaml"
    try:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
        configured_jobs = [j.get("name") for j in cfg.get("jobs", []) if j.get("name")]
    except Exception:
        configured_jobs = []

    status_path = DATA_OUT / "autotrain" / "status.json"
    jobs_status = []
    if status_path.exists():
        try:
            status_obj = json.loads(status_path.read_text(encoding="utf-8"))
            jobs_status = status_obj.get("jobs", [])
        except Exception:
            jobs_status = []

    status_map = {j.get("name"): j for j in jobs_status}
    # Include extra jobs from status not present in config (e.g., local_job)
    # Performance optimization: Direct iteration instead of .keys()
    extra_jobs = [name for name in status_map if name not in configured_jobs]
    all_job_names = configured_jobs + extra_jobs
    enriched = []
    succeeded = failed = running = pending = validated = 0
    succeeded_durations = []
    running_job_name = None
    running_log_path = None
    total_epochs_running = None
    # Compute runner-specific average durations for per-job ETA
    runner_durations = {}
    for rec in jobs_status:
        if rec.get("status") == "succeeded" and rec.get("duration_sec"):
            runner = rec.get("runner", "unknown")
            runner_durations.setdefault(runner, []).append(rec["duration_sec"])
    runner_avg = {r: (sum(durs)/len(durs)) for r, durs in runner_durations.items()}

    for name in all_job_names:
        rec = status_map.get(name)
        if rec is None:
            enriched.append({"name": name, "status": "pending"})
            pending += 1
            continue
        st = rec.get("status")
        if st == "succeeded":
            succeeded += 1
            dur = rec.get("duration_sec")
            if isinstance(dur, (int, float)):
                succeeded_durations.append(dur)
        elif st == "failed":
            failed += 1
        elif st == "validated":
            validated += 1
        elif st == "running" or st == "retry_running":
            running += 1
            running_job_name = name
            running_log_path = rec.get("log")
        else:
            pending += 1
        
        # Compute per-job ETA if running
        job_eta_sec = None
        if st in {"running", "retry_running"} and rec.get("start_time"):
            runner_type = rec.get("runner", "unknown")
            avg_dur = runner_avg.get(runner_type)
            if avg_dur:
                try:
                    start_dt = datetime.strptime(rec["start_time"], "%Y%m%dT%H%M%SZ")
                    elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
                    remaining = max(0, avg_dur - elapsed)
                    job_eta_sec = round(remaining, 1)
                except Exception:
                    pass
        
        enriched.append({
            "name": name,
            "status": st,
            "start_time": rec.get("start_time"),
            "return_code": rec.get("return_code"),
            "duration_sec": rec.get("duration_sec"),
            "validated_type": rec.get("validated_type"),
            "category": rec.get("category"),
            "runner": rec.get("runner"),
            "eta_sec": job_eta_sec,
        })

    total_jobs = len(all_job_names)
    if total_jobs:
        percent_complete = round((succeeded / total_jobs) * 100, 2)
    else:
        percent_complete = 0.0

    if succeeded and succeeded_durations and total_jobs > succeeded:
        avg = sum(succeeded_durations) / len(succeeded_durations)
        remaining_jobs = total_jobs - succeeded
        eta_seconds = avg * remaining_jobs
        eta_iso = (datetime.now(timezone.utc) + timedelta(seconds=eta_seconds)).isoformat() + "Z"
    else:
        avg = None
        eta_seconds = None
        eta_iso = None

    # Intra-job progress parsing for current running job
    current_job_percent = None
    current_epoch = None
    total_epochs = None
    current_step = None
    total_steps = None
    if running_job_name and running_log_path:
        try:
            log_file = Path(running_log_path)
            if log_file.exists():
                # Tail last ~400 lines for patterns
                lines = _tail_lines(log_file, 400)
                # Patterns: Epoch X/Y, global_step = Z, total_flos
                # Compile regex patterns ONCE outside loop for performance
                import re
                epoch_pat = re.compile(r"Epoch\s+(\d+)/(\d+)")
                step_pat = re.compile(r"global_step\s*=\s*(\d+)")
                last_epoch = None
                last_total_epochs = None
                last_step = None
                for ln in lines:
                    e_m = epoch_pat.search(ln)
                    if e_m:
                        last_epoch = int(e_m.group(1))
                        last_total_epochs = int(e_m.group(2))
                    s_m = step_pat.search(ln)
                    if s_m:
                        last_step = int(s_m.group(1))
                if last_epoch and last_total_epochs:
                    current_epoch = last_epoch
                    total_epochs = last_total_epochs
                    # Compute epoch-based percent if no steps
                    current_job_percent = round(((last_epoch - 1) / max(1, last_total_epochs)) * 100, 2)
                # If we have steps and epochs, approximate total steps
                if last_step is not None and total_epochs is not None:
                    # Heuristic: use max observed step as current_step; total steps unknown until training end.
                    current_step = last_step
                    # Try to infer total steps from training args saved in output dir (trainer_state.json)
                    trainer_state = log_file.parent / "trainer_state.json"
                    if trainer_state.exists():
                        try:
                            st_obj = json.loads(trainer_state.read_text(encoding="utf-8"))
                            opt = st_obj.get("trainer_state", st_obj)
                            max_steps = opt.get("max_steps")
                            if isinstance(max_steps, int) and max_steps > 0:
                                total_steps = max_steps
                        except Exception:
                            pass
                    if total_steps:
                        step_percent = round((current_step / max(1, total_steps)) * 100, 2)
                        # Prefer finer-grained step percent when available
                        current_job_percent = step_percent
        except Exception:
            pass

    # Add metrics for succeeded jobs
    for job_rec in enriched:
        if job_rec.get("status") == "succeeded":
            metrics = _extract_job_metrics(job_rec)
            if metrics:
                job_rec["metrics"] = metrics

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "total_jobs": total_jobs,
        "succeeded": succeeded,
        "validated": validated,
        "failed": failed,
        "running": running,
        "pending": pending,
        "percent_complete": percent_complete,  # success-only percent
        "percent_success_alias": percent_complete,
        "average_job_duration_seconds": avg,
        "eta_seconds": eta_seconds,
        "eta_iso": eta_iso,
        "current_job_name": running_job_name,
        "current_job_percent": current_job_percent,
        "current_epoch": current_epoch,
        "total_epochs": total_epochs,
        "current_step": current_step,
        "total_steps": total_steps,
        "jobs": enriched,
    }
    _append_progress_history(payload)
    return payload

# ========================= RETRY SUPPORT =========================

RETRY_LOCK = threading.Lock()
ACTIVE_RETRY: Optional[str] = None
STATUS_PATH = DATA_OUT / "autotrain" / "status.json"

def _read_status() -> Dict[str, Any]:
    if STATUS_PATH.exists():
        try:
            return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"jobs": []}
    return {"jobs": []}

def _write_status(obj: Dict[str, Any]) -> None:
    try:
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    except Exception:
        pass

def _find_job_entry(status_obj: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    for j in status_obj.get("jobs", []):
        if j.get("name") == name:
            return j
    return None

@app.route("/api/retry_job/<job_name>", methods=["POST"])
def retry_job(job_name: str):
    """Retry a single AutoTrain job safely.

    Concurrency rules:
      - Only one retry active at a time (ACTIVE_RETRY guarded by RETRY_LOCK)
      - No retry allowed while any job is currently running.
    """
    global ACTIVE_RETRY
    with RETRY_LOCK:
        status_obj = _read_status()
        jobs_list = status_obj.get("jobs", [])
        if ACTIVE_RETRY is not None:
            return jsonify({"error": "retry_in_progress", "active_retry": ACTIVE_RETRY}), 409
        # Disallow if any job currently running (avoid log collision / resource contention)
        if any(j.get("status") in {"running", "retry_running"} for j in jobs_list):
            return jsonify({"error": "job_currently_running"}), 409

        target_entry = _find_job_entry(status_obj, job_name)
        if target_entry is None:
            return jsonify({"error": "job_not_found"}), 404

        # Load job from config so we have full definition (dataset, save_dir, etc.)
        cfg_path = REPO_ROOT / "autotrain.yaml"
        try:
            config_jobs = {j.name: j for j in load_jobs(cfg_path)}
        except Exception:
            return jsonify({"error": "config_load_failed"}), 500
        if job_name not in config_jobs:
            return jsonify({"error": "job_not_in_config"}), 400
        job_obj: Job = config_jobs[job_name]

        # Prepare placeholder update
        retry_count = int(target_entry.get("retry_count", 0)) + 1
        target_entry.update({
            "status": "retry_running",
            "retry_count": retry_count,
            "retry_start_time": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        })
        status_obj["generated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
        _write_status(status_obj)
        ACTIVE_RETRY = job_name

        def _do_retry(job: Job, retry_num: int):
            try:
                result = run_job(job, dry_run=False, job_index=0, total_jobs=1)
            except Exception as e:  # capture unexpected exception
                result = {
                    "name": job.name,
                    "runner": job.runner,
                    "status": "failed",
                    "error": str(e),
                    "trace": traceback.format_exc().splitlines()[-5:],
                    "retry_count": retry_num,
                }
            # Merge result back into status
            with RETRY_LOCK:
                current_status = _read_status()
                entry = _find_job_entry(current_status, job.name)
                if entry is not None:
                    # Preserve retry_count from placeholder
                    preserved_retry = entry.get("retry_count", retry_num)
                    result["retry_count"] = preserved_retry
                    result["status"] = result.get("status")
                    result["retry_completed_time"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    # Mark as succeeded/failed (no special retry_running state anymore)
                    for k in ["status","return_code","duration_sec","duration_human","log","metrics","output_dir","cmd","start_time","retry_count","retry_completed_time"]:
                        v = result.get(k)
                        if v is not None:
                            entry[k] = v
                    current_status["generated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
                    _write_status(current_status)
                ACTIVE_RETRY = None
        threading.Thread(target=_do_retry, args=(job_obj, retry_count), daemon=True).start()

        return jsonify({"accepted": True, "job": job_name, "retry_count": retry_count})

@app.route("/api/cancel_job/<job_name>", methods=["POST"])
def cancel_job(job_name: str):
    """Cancel a running or retry_running job by terminating its process.
    
    Concurrency rules:
      - Only jobs with status running or retry_running can be cancelled
      - Requires active PID tracking
    """
    global ACTIVE_JOB_PIDS
    with RETRY_LOCK:
        status_obj = _read_status()
        target_entry = _find_job_entry(status_obj, job_name)
        if target_entry is None:
            return jsonify({"error": "job_not_found"}), 404
        
        st = target_entry.get("status")
        if st not in {"running", "retry_running"}:
            return jsonify({"error": "job_not_running", "status": st}), 400
        
        pid = ACTIVE_JOB_PIDS.get(job_name)
        if pid is None:
            return jsonify({"error": "pid_not_tracked"}), 400
        
        # Attempt to terminate process
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], check=False)
            else:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            
            # Update status to cancelled
            target_entry["status"] = "cancelled"
            target_entry["cancelled_time"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            if "start_time" in target_entry:
                try:
                    start = datetime.strptime(target_entry["start_time"], "%Y%m%dT%H%M%SZ")
                    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                    target_entry["duration_sec"] = round(elapsed, 2)
                except Exception:
                    pass
            
            status_obj["generated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
            _write_status(status_obj)
            
            # Remove from active tracking
            del ACTIVE_JOB_PIDS[job_name]
            if ACTIVE_RETRY == job_name:
                ACTIVE_RETRY = None
            
            return jsonify({"cancelled": True, "job": job_name, "pid": pid})
        except Exception as e:
            return jsonify({"error": "termination_failed", "detail": str(e)}), 500

@app.route("/api/training_progress")
def training_progress():
    return jsonify(_compute_training_progress())

def _extract_job_metrics(job_rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out_dir = job_rec.get("output_dir")
    if not out_dir:
        return None
    p = Path(out_dir) / "metrics.jsonl"
    if not p.exists():
        return None
    pre_loss = pre_ppl = post_loss = post_ppl = last_step = None
    try:
        # Read last ~200 lines to capture metrics
        lines = _tail_lines(p, 200)
        import json as _json
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = _json.loads(ln)
            except Exception:
                continue
            phase = obj.get("phase")
            if phase == "pre":
                pre_loss = obj.get("eval_loss")
                pre_ppl = obj.get("eval_perplexity")
            elif phase == "post":
                post_loss = obj.get("eval_loss")
                post_ppl = obj.get("eval_perplexity")
            step = obj.get("step") or obj.get("global_step")
            if isinstance(step, int):
                last_step = step
        if any(x is not None for x in (pre_loss, pre_ppl, post_loss, post_ppl)):
            return {
                "pre_eval_loss": pre_loss,
                "pre_eval_perplexity": pre_ppl,
                "post_eval_loss": post_loss,
                "post_eval_perplexity": post_ppl,
                "last_step": last_step,
            }
    except Exception:
        return None
    return None

def _tail_lines(path: Path, max_lines: int) -> List[str]:
    """Efficiently read the last max_lines from a potentially large file."""
    try:
        size = path.stat().st_size
        if size <= 65536:  # small file heuristic - stream instead of readlines()
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                lines = []
                for line in f:
                    lines.append(line)
                    if len(lines) > max_lines:
                        lines.pop(0)  # Keep only last max_lines
                return lines
        # Large file: read backwards in blocks
        block_size = 8192
        lines: List[str] = []
        with path.open("rb") as f:
            pos = max(0, size - block_size)
            f.seek(pos)
            chunk = f.read(block_size)
            buf = chunk
            # Expand backwards until enough lines or start of file
            while True:
                decoded = buf.decode("utf-8", errors="ignore")
                lines = decoded.splitlines()
                if len(lines) >= max_lines or pos == 0:
                    break
                # Move further back
                new_pos = max(0, pos - block_size)
                read_size = pos - new_pos
                f.seek(new_pos)
                more = f.read(read_size)
                buf = more + buf
                pos = new_pos
            return lines[-max_lines:]
    except Exception:
        return []

HISTORY_PATH = DATA_OUT / "autotrain" / "progress_history.json"
_history_lock = threading.Lock()

def _append_progress_history(snapshot: dict, limit: int = 500):
    try:
        with _history_lock:
            if HISTORY_PATH.exists():
                try:
                    hist = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
                    if not isinstance(hist, list):
                        hist = []
                except Exception:
                    hist = []
            else:
                hist = []
            new_entry = {
                "generated_at": snapshot.get("generated_at"),
                "percent_complete": snapshot.get("percent_complete"),
                "current_job_name": snapshot.get("current_job_name"),
                "current_job_percent": snapshot.get("current_job_percent"),
                "current_epoch": snapshot.get("current_epoch"),
            }
            if not hist or any(new_entry.get(k) != hist[-1].get(k) for k in ("percent_complete","current_job_name","current_job_percent","current_epoch")):
                hist.append(new_entry)
            if len(hist) > limit:
                hist = hist[-limit:]
            HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            HISTORY_PATH.write_text(json.dumps(hist), encoding="utf-8")
    except Exception:
        pass

@app.route("/api/training_progress_history")
def training_progress_history():
    try:
        if HISTORY_PATH.exists():
            hist = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
            return jsonify({"history": hist, "count": len(hist)})
        return jsonify({"history": [], "count": 0})
    except Exception:
        return jsonify({"history": [], "count": 0, "error": "history_read_failed"})

@app.route("/api/training_progress_history_csv")
def training_progress_history_csv():
    # Provide CSV export of progress history snapshots
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["generated_at","percent_complete","current_job_name","current_job_percent","current_epoch"])
    try:
        hist = []
        if HISTORY_PATH.exists():
            hist = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
            if not isinstance(hist, list):
                hist = []
        for row in hist:
            writer.writerow([
                row.get("generated_at"),
                row.get("percent_complete"),
                row.get("current_job_name"),
                row.get("current_job_percent"),
                row.get("current_epoch"),
            ])
    except Exception:
        pass
    return output.getvalue(), 200, {"Content-Type": "text/csv"}

def _start_progress_emitter(interval_sec: int = 5):
    """Background thread emitting training_progress via SocketIO when data changes."""
    last_json = None
    def loop():
        nonlocal last_json
        while True:
            payload = _compute_training_progress()
            current_json = json.dumps(payload, sort_keys=True)
            if current_json != last_json:
                socketio.emit("training_progress", payload)
                last_json = current_json
            time.sleep(interval_sec)
    threading.Thread(target=loop, daemon=True).start()

_start_progress_emitter()

if __name__ == "__main__":
    import os
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    socketio.run(app, debug=debug_mode)
