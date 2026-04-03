#!/usr/bin/env bash
set -u
cd /workspaces/Aria || exit 1
mkdir -p data_out/repo_health_automation

PID_FILE="data_out/aria_forever_watchdog.pid"
HEARTBEAT_FILE="data_out/aria_forever_watchdog_heartbeat.json"
STATE_FILE="data_out/aria_forever_watchdog_state.json"
LOCK_DIR="data_out/aria_forever_watchdog.lockdir"

# Optional supervised components (opt-in)
ENABLE_AUTONOMOUS_TRAINING="${ENABLE_AUTONOMOUS_TRAINING:-0}"

# Prefer project virtualenv Python when available to avoid interpreter drift.
PYTHON_BIN="python"
if [[ -x "/workspaces/Aria/.venv/bin/python" ]]; then
  PYTHON_BIN="/workspaces/Aria/.venv/bin/python"
fi

# Strong single-instance guard: atomic mkdir with one stale-lock retry.
acquire_lock() {
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    return 0
  fi

  # If lock exists but PID is not alive, attempt one recovery.
  local existing_pid=""
  if [[ -f "$PID_FILE" ]]; then
    existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  fi
  if [[ -n "$existing_pid" ]] && ! kill -0 "$existing_pid" 2>/dev/null; then
    rmdir "$LOCK_DIR" 2>/dev/null || true
    mkdir "$LOCK_DIR" 2>/dev/null && return 0
  fi

  return 1
}

if ! acquire_lock; then
  exit 0
fi

# Single-instance guard: if another live watchdog exists, exit cleanly.
if [[ -f "$PID_FILE" ]]; then
  existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
    exit 0
  fi
fi

echo "$$" > "$PID_FILE"
cleanup() {
  local stop_utc
  stop_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  cat > "$HEARTBEAT_FILE" <<EOF
{"watchdog_pid":$$,"timestamp_utc":"$stop_utc","status":"stopped"}
EOF
  cat > "$STATE_FILE" <<EOF
{"watchdog_pid":$$,"timestamp_utc":"$stop_utc","status":"stopped","enable_autonomous_training":"$ENABLE_AUTONOMOUS_TRAINING"}
EOF
  rm -f "$PID_FILE"
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

start_if_missing() {
  local pattern="$1"
  local cmd="$2"
  local log_file="$3"

  if ! pgrep -f "$pattern" >/dev/null; then
    nohup bash -lc "$cmd" >> "$log_file" 2>&1 &
  fi
}

enforce_single_instance() {
  local pattern="$1"
  local pids
  pids="$(pgrep -f "$pattern" || true)"
  if [[ -z "$pids" ]]; then
    return
  fi

  # Keep newest (highest PID), terminate older duplicates.
  local keep_pid
  keep_pid="$(echo "$pids" | sort -n | tail -n 1)"
  local pid
  while IFS= read -r pid; do
    [[ -z "$pid" ]] && continue
    if [[ "$pid" != "$keep_pid" ]]; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done <<< "$pids"
}

trim_log_if_large() {
  local log_file="$1"
  local max_bytes="$2"
  local keep_lines="$3"

  if [[ -f "$log_file" ]]; then
    local size_bytes
    size_bytes=$(wc -c < "$log_file" 2>/dev/null || echo 0)
    if [[ "$size_bytes" -gt "$max_bytes" ]]; then
      tail -n "$keep_lines" "$log_file" > "${log_file}.tmp" 2>/dev/null || true
      mv "${log_file}.tmp" "$log_file" 2>/dev/null || true
    fi
  fi
}

http_status() {
  local url="$1"
  curl -m 5 -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000"
}

aria_active_port() {
  # Return first healthy Aria port, or empty string if none are healthy.
  local ports=()
  if [[ -n "${ARIA_PORT:-}" ]]; then
    ports+=("${ARIA_PORT}")
  fi
  ports+=("8080" "8081" "8082" "8090")

  local seen=" "
  local p status
  for p in "${ports[@]}"; do
    # Skip duplicates while preserving order.
    if [[ "$seen" == *" $p "* ]]; then
      continue
    fi
    seen+="$p "
    status="$(http_status "http://localhost:${p}/api/aria/state")"
    if [[ "$status" == "200" ]]; then
      echo "$p"
      return 0
    fi
  done
  echo ""
  return 0
}

restart_aria_now() {
  local aria_pattern="apps/aria/server.py"
  if pgrep -f "$aria_pattern" >/dev/null; then
    pkill -f "$aria_pattern" || true
    sleep 1
  fi
  nohup bash -lc "$PYTHON_BIN apps/aria/server.py" >> "data_out/aria_server.log" 2>&1 &
}

restart_functions_now() {
  local func_pattern="func host start"
  if pgrep -f "$func_pattern" >/dev/null; then
    pkill -f "$func_pattern" || true
    sleep 1
  fi
  nohup bash -lc "func host start" >> "data_out/functions_host.log" 2>&1 &
}

while true; do
  # Debounce restart decisions to avoid thrashing on transient health blips.
  aria_failures=0
  functions_failures=0
  last_aria_restart_epoch=0
  last_functions_restart_epoch=0
  if [[ -f "$STATE_FILE" ]]; then
    aria_failures="$(grep -o '"aria_failures":[0-9]*' "$STATE_FILE" 2>/dev/null | cut -d: -f2)"
    functions_failures="$(grep -o '"functions_failures":[0-9]*' "$STATE_FILE" 2>/dev/null | cut -d: -f2)"
    last_aria_restart_epoch="$(grep -o '"last_aria_restart_epoch":[0-9]*' "$STATE_FILE" 2>/dev/null | cut -d: -f2)"
    last_functions_restart_epoch="$(grep -o '"last_functions_restart_epoch":[0-9]*' "$STATE_FILE" 2>/dev/null | cut -d: -f2)"
    aria_failures="${aria_failures:-0}"
    functions_failures="${functions_failures:-0}"
    last_aria_restart_epoch="${last_aria_restart_epoch:-0}"
    last_functions_restart_epoch="${last_functions_restart_epoch:-0}"
  fi

  now_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  now_epoch="$(date +%s)"

  # Log maintenance for indefinite runtime (50 MiB cap, retain recent tail).
  trim_log_if_large "data_out/aria_forever_watchdog.log" 52428800 5000
  trim_log_if_large "data_out/repo_automation.log" 52428800 10000
  trim_log_if_large "data_out/repo_health_automation/automation.log" 52428800 10000
  trim_log_if_large "data_out/aria_server.log" 52428800 10000
  trim_log_if_large "data_out/functions_host.log" 52428800 10000
  trim_log_if_large "data_out/autonomous_training.log" 52428800 10000

  # Core automations
  enforce_single_instance "scripts/repo_automation.py --start"
  start_if_missing "scripts/repo_automation.py --start" \
    "$PYTHON_BIN scripts/repo_automation.py --start" \
    "data_out/repo_automation.log"

  enforce_single_instance "repo_health_automation.py --watch --interval 300 --strict-endpoints --continue-on-fail"
  start_if_missing "repo_health_automation.py --watch --interval 300 --strict-endpoints --continue-on-fail" \
    "$PYTHON_BIN scripts/repo_health_automation.py --watch --interval 300 --strict-endpoints --continue-on-fail" \
    "data_out/repo_health_automation/automation.log"

  # Aria web server
  enforce_single_instance "apps/aria/server.py"
  start_if_missing "apps/aria/server.py" \
    "$PYTHON_BIN apps/aria/server.py" \
    "data_out/aria_server.log"
  active_aria_port="$(aria_active_port)"
  if [[ -n "$active_aria_port" ]]; then
    aria_failures=0
  else
    aria_failures=$((aria_failures + 1))
    # Cooldown: at least 120s between forced restarts.
    if [[ "$aria_failures" -ge 3 ]] && (( now_epoch - last_aria_restart_epoch >= 120 )); then
      restart_aria_now
      aria_failures=0
      last_aria_restart_epoch="$now_epoch"
      active_aria_port="$(aria_active_port)"
    fi
  fi

  # Azure Functions host (optional; only if func CLI exists)
  if command -v func >/dev/null 2>&1; then
    enforce_single_instance "func host start"
    start_if_missing "func host start" \
      "func host start" \
      "data_out/functions_host.log"
    if [[ "$(http_status "http://localhost:7071/api/ai/status")" == "200" ]]; then
      functions_failures=0
    else
      functions_failures=$((functions_failures + 1))
      # Cooldown: at least 120s between forced restarts.
      if [[ "$functions_failures" -ge 3 ]] && (( now_epoch - last_functions_restart_epoch >= 120 )); then
        restart_functions_now
        functions_failures=0
        last_functions_restart_epoch="$now_epoch"
      fi
    fi
  fi

  # Optional autonomous training orchestrator
  if [[ "$ENABLE_AUTONOMOUS_TRAINING" == "1" ]]; then
    enforce_single_instance "scripts/autonomous_training_orchestrator.py"
    start_if_missing "scripts/autonomous_training_orchestrator.py" \
      "$PYTHON_BIN scripts/autonomous_training_orchestrator.py" \
      "data_out/autonomous_training.log"
  fi

  cat > "$HEARTBEAT_FILE" <<EOF
{"watchdog_pid":$$,"timestamp_utc":"$now_utc","status":"running","active_aria_port":"${active_aria_port:-}"}
EOF

  cat > "$STATE_FILE" <<EOF
{"watchdog_pid":$$,"timestamp_utc":"$now_utc","active_aria_port":"${active_aria_port:-}","aria_failures":$aria_failures,"functions_failures":$functions_failures,"last_aria_restart_epoch":$last_aria_restart_epoch,"last_functions_restart_epoch":$last_functions_restart_epoch,"enable_autonomous_training":"$ENABLE_AUTONOMOUS_TRAINING"}
EOF

  sleep 30
done
