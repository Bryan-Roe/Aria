#!/usr/bin/env bash
set -euo pipefail

# Setup script for the model-specific venv and ML dependencies.
#
# This script creates a venv at AI/microsoft_phi-silica-3.6_v1/venv (by default)
# and installs the light-weight requirements from requirements.txt plus
# an appropriate torch wheel for your platform (CUDA / CPU).
#
# Usage examples:
#  # CPU-only installation (Linux):
#  bash scripts/setup_model_env.sh --cpu
#
#  # CUDA 12.1 installation (choose the CUDA wheel that matches your system):
#  bash scripts/setup_model_env.sh --cuda cu121
#
#  # Use a specific python executable to create the venv:
#  bash scripts/setup_model_env.sh --python /usr/bin/python3.10

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/venv"
REQUIREMENTS_FILE="${ROOT_DIR}/requirements.txt"

PYTHON_EXE="$(which python3 || which python)"
FORCE=false
CUDA_WHEEL=""
CPU_ONLY=false

print_help(){
  cat <<EOF
Usage: $0 [--cpu] [--cuda <cu121|cu118|cu117>] [--python <path>] [--force]

This creates a virtualenv under ${VENV_DIR} and installs model training
dependencies listed in ${REQUIREMENTS_FILE}. You MUST explicitly choose the
torch wheel that matches your machine (CPU or CUDA). The script will not
guess randomly — choose --cpu for CPU-only or --cuda cu121 for CUDA.

Examples:
  $0 --cpu
  $0 --cuda cu121
  $0 --python /usr/bin/python3.10  # use a particular python binary
EOF
}

while (( "$#" )); do
  case "$1" in
    --python)
      PYTHON_EXE="$2"
      shift 2
      ;;
    --cpu)
      CPU_ONLY=true
      shift
      ;;
    --cuda)
      CUDA_WHEEL="$2"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      print_help
      exit 1
      ;;
  esac
done

echo "Using python: ${PYTHON_EXE}"

if [ -d "${VENV_DIR}" ] && [ "${FORCE}" != "true" ]; then
  echo "Virtualenv already exists at ${VENV_DIR}. Use --force to recreate."
else
  echo "Creating venv at ${VENV_DIR}..."
  ${PYTHON_EXE} -m venv "${VENV_DIR}"
fi

# Resolve platform-specific python in venv
VENV_PYTHON="${VENV_DIR}/bin/python"
if [ ! -x "${VENV_PYTHON}" ] && [ -x "${VENV_DIR}/Scripts/python.exe" ]; then
  VENV_PYTHON="${VENV_DIR}/Scripts/python.exe"
fi

if [ ! -x "${VENV_PYTHON}" ]; then
  echo "ERROR: Python not found in created venv: ${VENV_PYTHON}" >&2
  exit 2
fi

echo "Upgrading pip/setuptools/wheel in venv..."
"${VENV_PYTHON}" -m pip install --upgrade pip setuptools wheel

echo "Installing requirements (excluding torch - installed separately)..."
# requirements.txt intentionally does NOT pin torch so we install it explicitly
TMP_REQS=$(mktemp)
grep -v "^#" "${REQUIREMENTS_FILE}" | grep -v "^\s*$" > "${TMP_REQS}"

# Remove any torch line (best-effort)
sed -i '/^torch/Id' "${TMP_REQS}"

"${VENV_PYTHON}" -m pip install -r "${TMP_REQS}"
rm -f "${TMP_REQS}"

if [ "${CPU_ONLY}" = true ]; then
  echo "Installing CPU-only torch wheel (PyTorch)"
  "${VENV_PYTHON}" -m pip install --index-url https://download.pytorch.org/whl/cpu torch
elif [ -n "${CUDA_WHEEL}" ]; then
  echo "Installing CUDA wheel for ${CUDA_WHEEL} (PyTorch)"
  # Use the appropriate stable wheel link; the -f/--find-links ensures the extra index is used
  # Example: --cuda cu121 -> https://download.pytorch.org/whl/cu121
  "${VENV_PYTHON}" -m pip install torch --index-url https://download.pytorch.org/whl/${CUDA_WHEEL}
else
  echo "No torch wheel selection made. Please re-run with either --cpu or --cuda <cuXXX>"
  echo "Example: ${0} --cuda cu121  # for Linux with CUDA 12.1" >&2
  exit 3
fi

echo "Installing optional utility packages recommended for training..."
# Pin huggingface_hub to a version compatible with common transformers/peft
# to avoid accidental upgrades that break imports (transformers<5 expects hf-hub <1.0)
"${VENV_PYTHON}" -m pip install safetensors "huggingface_hub>=0.34.0,<1.0" accelerate --upgrade

# Run a quick pip-check to catch obvious dependency conflicts early and report
echo "Running pip check to detect dependency problems (non-fatal)"
"${VENV_PYTHON}" -m pip check || true

echo "Smoke test: verifying minimal imports and GPU availability (if any)"
"${VENV_PYTHON}" - <<PY
import importlib
for m in ('torch','transformers','datasets','peft','accelerate'):
    try:
        mod = importlib.import_module(m)
        print(m, 'OK', getattr(mod, '__version__', 'no_version'))
    except Exception as e:
        print(m, 'IMPORT FAILED', type(e).__name__, e)
try:
    import torch
    print('torch.cuda.is_available():', torch.cuda.is_available())
except Exception as e:
    print('torch GPU check skipped', type(e).__name__, e)
PY

echo "Model venv setup complete. Activate with: source ${VENV_DIR}/bin/activate"

exit 0
