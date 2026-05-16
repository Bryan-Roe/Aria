#!/usr/bin/env bash
set -euo pipefail

# scripts/integration_contract_gate.sh
# Purpose: Small, deterministic gate wrapper used by the Integration Contract Gate
# workflow. Provides a reliable health check for the AI functions status endpoint and
# optional helpers for CI environments.
#
# Behavior:
#  - Always runs:
#      python scripts/integration_smoke.py
#      python scripts/ci_orchestrator.py --integration-contract-tests
#      python scripts/ci_orchestrator.py --validate-all
#  - In --strict-endpoints mode, also verifies /api/ai/status reachability.
#  - Exits 0 on success, non-zero on failure (exit code 2 for unreachable endpoint).

strict_endpoints=false
for arg in "$@"; do
  case "${arg}" in
    --strict-endpoints) strict_endpoints=true ;;
  esac
done

endpoint="${INTEGRATION_AI_STATUS_ENDPOINT:-http://localhost:7071/api/ai/status}"
retry_count="${RETRY_COUNT:-30}"
retry_interval="${RETRY_INTERVAL:-1}"
start_cmd="${START_FUNC_CMD:-}" # optional command to start a local function host

log() {
  echo "[integration_contract_gate] $*"
}

run_step() {
  local name="$1"
  shift
  log "Running ${name}: $*"
  set +e
  "$@"
  local rc=$?
  set -e
  if [[ ${rc} -ne 0 ]]; then
    exit "${rc}"
  fi
}

run_step integration_smoke python scripts/integration_smoke.py
run_step integration_contract_tests python scripts/ci_orchestrator.py --integration-contract-tests
run_step validate_all python scripts/ci_orchestrator.py --validate-all

if [[ "${strict_endpoints}" != "true" ]]; then
  log "Standard mode complete."
  exit 0
fi

if [[ -n "${start_cmd}" ]]; then
  log "START_FUNC_CMD is provided; attempting to start process in background."
  # shellcheck disable=SC2086
  ${start_cmd} &>/tmp/integration_contract_gate.start.log &
  start_pid=$!
  log "Started background process (PID=${start_pid}). Logs: /tmp/integration_contract_gate.start.log"
fi

log "Strict mode: checking AI status endpoint: ${endpoint}"

i=0
while (( i < retry_count )); do
  if curl --silent --fail --max-time 5 --show-error "${endpoint}" -o /dev/null; then
    log "AI status endpoint reachable: ${endpoint}"
    # If we started a background process and it's still running, leave it alone; the
    # CI job should manage lifecycle. Exit success so workflow can continue.
    exit 0
  fi
  ((i++))
  log "Attempt ${i}/${retry_count} — endpoint not ready yet; sleeping ${retry_interval}s"
  sleep "${retry_interval}"
done

log "AI status endpoint not reachable after ${retry_count} attempts: ${endpoint}" >&2
log "Last lines of start log (if any):"
if [[ -f /tmp/integration_contract_gate.start.log ]]; then
  tail -n +1 /tmp/integration_contract_gate.start.log | sed -n '1,200p' || true
else
  log "(no start log present)"
fi

# Provide helpful diagnostics to the Actions log
log "--- Diagnostics ---"
log "Netstat (listening ports):"
if command -v ss >/dev/null 2>&1; then
  ss -ltnp || true
elif command -v netstat >/dev/null 2>&1; then
  netstat -ltnp || true
else
  log "(ss/netstat not available)"
fi

log "Curl debug attempt:" 
curl --verbose --max-time 10 "${endpoint}" || true

exit 2
