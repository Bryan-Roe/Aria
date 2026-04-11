#!/usr/bin/env bash
# Start repo health automation (one-shot or continuous)
# Wraps: scripts/repo_health_automation.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="${PYTHON_BIN:-python3}"

print_usage() {
  cat <<EOF
Usage: $0 [mode] [options]

Modes:
  once         Run one health cycle (default)
  watch        Run continuous health cycles
  status       Show last status JSON summary

Options:
  --strict                 Use strict endpoint integration gate
  --full-pytest            Include full pytest smoke in each cycle
  --auto-fix-ruff          Auto-fix changed Python files via Ruff before checks
  --continue-on-fail       Continue remaining steps even after a failed step
  --interval <seconds>     Watch interval (default: 300)
  --background, -b         Run watch mode in background (nohup)

Examples:
  $0 once --strict
  $0 once --strict --full-pytest
  $0 watch --strict --interval 300
  $0 watch --strict -b
  $0 status
EOF
}

MODE="once"
STRICT=0
FULL_PYTEST=0
AUTO_FIX_RUFF=0
CONTINUE_ON_FAIL=0
INTERVAL=300
BACKGROUND=0

if [[ $# -gt 0 ]]; then
  case "$1" in
    once|watch|status)
      MODE="$1"
      shift
      ;;
    --help|-h)
      print_usage
      exit 0
      ;;
  esac
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict)
      STRICT=1
      ;;
    --full-pytest)
      FULL_PYTEST=1
      ;;
    --auto-fix-ruff)
      AUTO_FIX_RUFF=1
      ;;
    --continue-on-fail)
      CONTINUE_ON_FAIL=1
      ;;
    --interval)
      shift
      INTERVAL="${1:-300}"
      ;;
    --background|-b)
      BACKGROUND=1
      ;;
    --help|-h)
      print_usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      print_usage
      exit 2
      ;;
  esac
  shift
done

STATUS_PATH="$REPO_ROOT/data_out/repo_health_automation/status.json"
LOG_PATH="$REPO_ROOT/data_out/repo_health_automation/automation.log"

if [[ "$MODE" == "status" ]]; then
  if [[ ! -f "$STATUS_PATH" ]]; then
    echo "No status file found at: $STATUS_PATH"
    exit 1
  fi
  echo "Status file: $STATUS_PATH"
  "$PYTHON_BIN" - <<PY
import json
from pathlib import Path
p=Path(r"$STATUS_PATH")
obj=json.loads(p.read_text())
print(json.dumps({
    "updated_at": obj.get("updated_at"),
    "total_cycles": obj.get("total_cycles"),
    "successful_cycles": obj.get("successful_cycles"),
    "failed_cycles": obj.get("failed_cycles"),
    "last_cycle_succeeded": (obj.get("last_cycle") or {}).get("succeeded"),
}, indent=2))
PY
  exit 0
fi

args=()
if [[ "$MODE" == "watch" ]]; then
  args+=("--watch" "--interval" "$INTERVAL")
else
  args+=("--once")
fi
if [[ "$STRICT" -eq 1 ]]; then
  args+=("--strict-endpoints")
fi
if [[ "$FULL_PYTEST" -eq 1 ]]; then
  args+=("--full-pytest")
fi
if [[ "$AUTO_FIX_RUFF" -eq 1 ]]; then
  args+=("--auto-fix-ruff")
fi
if [[ "$CONTINUE_ON_FAIL" -eq 1 ]]; then
  args+=("--continue-on-fail")
fi

mkdir -p "$REPO_ROOT/data_out/repo_health_automation"

if [[ "$BACKGROUND" -eq 1 ]]; then
  if [[ "$MODE" != "watch" ]]; then
    echo "--background is only valid with watch mode" >&2
    exit 2
  fi
  echo "Starting repo health automation in background..."
  nohup "$PYTHON_BIN" "$REPO_ROOT/scripts/repo_health_automation.py" "${args[@]}" > "$LOG_PATH" 2>&1 &
  pid=$!
  echo "Started PID: $pid"
  echo "Log: $LOG_PATH"
  echo "Status: $STATUS_PATH"
  exit 0
fi

exec "$PYTHON_BIN" "$REPO_ROOT/scripts/repo_health_automation.py" "${args[@]}"
