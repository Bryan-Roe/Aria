#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

STRICT_ENDPOINTS=0
if [[ "${1:-}" == "--strict-endpoints" ]]; then
  STRICT_ENDPOINTS=1
  shift
fi

if [[ "$#" -gt 0 ]]; then
  echo "Usage: scripts/integration_contract_gate.sh [--strict-endpoints]" >&2
  exit 2
fi

pushd "$REPO_ROOT" >/dev/null

if [[ "$STRICT_ENDPOINTS" -eq 1 ]]; then
  python scripts/integration_smoke.py --strict-endpoints --json
else
  python scripts/integration_smoke.py --json
fi

python scripts/ci_orchestrator.py --integration-contract-tests
python scripts/ci_orchestrator.py --validate-all

popd >/dev/null

echo "[integration_contract_gate] passed"
