#!/bin/bash
# LM Studio MCP Server startup script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default configuration
LMSTUDIO_BASE_URL="${LMSTUDIO_BASE_URL:-http://127.0.0.1:1234/v1}"
LMSTUDIO_MODEL="${LMSTUDIO_MODEL:-local-model}"
LMSTUDIO_TEMPERATURE="${LMSTUDIO_TEMPERATURE:-0.7}"
LMSTUDIO_MAX_TOKENS="${LMSTUDIO_MAX_TOKENS:-2048}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --help                Show this help message
  --test                Run tests before starting
  --base-url URL        Set LM Studio base URL (default: $LMSTUDIO_BASE_URL)
  --model MODEL         Set model name (default: $LMSTUDIO_MODEL)
  --temperature TEMP    Set temperature (default: $LMSTUDIO_TEMPERATURE)
  --max-tokens TOKENS   Set max tokens (default: $LMSTUDIO_MAX_TOKENS)

Environment Variables:
  LMSTUDIO_BASE_URL     LM Studio server endpoint
  LMSTUDIO_MODEL        Default model to use
  LMSTUDIO_TEMPERATURE  Sampling temperature
  LMSTUDIO_MAX_TOKENS   Max tokens in response

Examples:
  $(basename "$0")
  $(basename "$0") --model mistral-7b
  $(basename "$0") --base-url http://192.168.1.100:1234/v1 --test
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_usage
            exit 0
            ;;
        --test)
            RUN_TEST=true
            shift
            ;;
        --base-url)
            LMSTUDIO_BASE_URL="$2"
            shift 2
            ;;
        --model)
            LMSTUDIO_MODEL="$2"
            shift 2
            ;;
        --temperature)
            LMSTUDIO_TEMPERATURE="$2"
            shift 2
            ;;
        --max-tokens)
            LMSTUDIO_MAX_TOKENS="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Export configuration
export LMSTUDIO_BASE_URL
export LMSTUDIO_MODEL
export LMSTUDIO_TEMPERATURE
export LMSTUDIO_MAX_TOKENS

# Print configuration
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          LM Studio MCP Server                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
print_info "Configuration:"
echo "  Base URL:       $LMSTUDIO_BASE_URL"
echo "  Model:          $LMSTUDIO_MODEL"
echo "  Temperature:    $LMSTUDIO_TEMPERATURE"
echo "  Max Tokens:     $LMSTUDIO_MAX_TOKENS"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

print_info "Python: $(python3 --version)"

# Check if virtual environment exists and activate it
if [[ -d "$SCRIPT_DIR/venv" ]]; then
    print_info "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate" || true
elif [[ -d ".venv" ]]; then
    print_info "Activating virtual environment..."
    source ".venv/bin/activate" || true
else
    print_warn "No virtual environment found. Consider creating one:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r mcp-requirements.txt"
fi

# Check if MCP is installed
if ! python3 -c "import mcp" 2>/dev/null; then
    print_warn "MCP package not found. Installing dependencies..."
    if pip install -r "$SCRIPT_DIR/mcp-requirements.txt"; then
        print_info "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
fi

# Optionally run tests
if [[ "$RUN_TEST" == true ]]; then
    print_info "Running tests before starting server..."
    echo ""

    if python3 "$SCRIPT_DIR/test_lmstudio_mcp.py"; then
        print_info "Tests passed! Starting server..."
        echo ""
    else
        print_error "Tests failed! Not starting server."
        exit 1
    fi
fi

# Start the server
print_info "Starting LM Studio MCP Server..."
echo ""

python3 "$SCRIPT_DIR/lmstudio_mcp_server.py"
