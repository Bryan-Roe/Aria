#!/bin/bash
# Autonomous Code Agent Launcher
# Simplifies running the agent with proper environment setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
LLM_TYPE=${LLM_TYPE:-"ollama"}
DRY_RUN=""
MODEL=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Help function
show_help() {
    cat <<EOF
Autonomous Code Agent - Local LLM Agent for Repository Tasks

Usage:
  ./scripts/agent.sh [OPTIONS] --task "YOUR TASK DESCRIPTION"

Options:
  --task TEXT               Task description (required)
  --llm-type TYPE          LLM type: ollama, lmstudio (default: $LLM_TYPE)
  --model NAME             Specific model to use
  --dry-run                Analyze only, don't modify files
  --check-llm              Check if LLM is available and exit
  --setup-ollama           Download and setup Ollama
  --setup-lmstudio         Show LM Studio setup instructions
  --help                   Show this help message

Examples:
  # Analyze a task without making changes
  ./scripts/agent.sh --task "fix failing tests" --dry-run

  # Full autonomous agent run
  ./scripts/agent.sh --task "add docstrings to chat_providers.py"

  # Use LM Studio instead of Ollama
  ./scripts/agent.sh --task "refactor quantum_mcp_server.py" --llm-type lmstudio

  # Check if Ollama is running
  ./scripts/agent.sh --check-llm

  # Setup instructions
  ./scripts/agent.sh --setup-ollama

EOF
}

# Setup Ollama
setup_ollama() {
    echo -e "${YELLOW}Setting up Ollama...${NC}"

    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}✓ Ollama is installed${NC}"
        echo ""
        echo "Start Ollama with:"
        echo "  ollama serve"
        echo ""
        echo "In another terminal, pull a model:"
        echo "  ollama pull mistral"
        echo "  # or: ollama pull llama2"
        echo ""
    else
        echo -e "${RED}✗ Ollama not found${NC}"
        echo ""
        echo "Install Ollama from: https://ollama.ai"
        echo ""
        echo "Or on macOS/Linux with Homebrew:"
        echo "  brew install ollama"
        echo ""
    fi

    exit 0
}

# Setup LM Studio
setup_lmstudio() {
    echo -e "${YELLOW}LM Studio Setup Instructions${NC}"
    echo ""
    echo "1. Download LM Studio from: https://lmstudio.ai"
    echo "2. Install and launch the application"
    echo "3. Download a model (Mistral recommended)"
    echo "4. Go to 'Developer' tab"
    echo "5. Select your model and click 'Start Server'"
    echo ""
    echo "Then set environment variables:"
    echo "  export LMSTUDIO_BASE_URL='http://127.0.0.1:1234/v1'"
    echo "  export LMSTUDIO_MODEL='local-model'"
    echo ""
    echo "Verify with:"
    echo "  curl http://127.0.0.1:1234/v1/models"
    echo ""
    exit 0
}

# Check LLM availability
check_llm() {
    echo -e "${YELLOW}Checking $LLM_TYPE availability...${NC}"

    if [ "$LLM_TYPE" = "ollama" ]; then
        URL="http://127.0.0.1:11434/api/tags"
    else
        URL="http://127.0.0.1:1234/v1/models"
    fi

    if curl -s "$URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $LLM_TYPE is available${NC}"
        curl -s "$URL" | head -20
        exit 0
    else
        echo -e "${RED}✗ Cannot reach $LLM_TYPE at $URL${NC}"
        echo ""
        echo "Make sure $LLM_TYPE is running:"
        if [ "$LLM_TYPE" = "ollama" ]; then
            echo "  ollama serve"
        else
            echo "  Start LM Studio and go to Developer → Local Server"
        fi
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --task)
            TASK="$2"
            shift 2
            ;;
        --llm-type)
            LLM_TYPE="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --check-llm)
            check_llm
            ;;
        --setup-ollama)
            setup_ollama
            ;;
        --setup-lmstudio)
            setup_lmstudio
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$TASK" ]; then
    echo -e "${RED}Error: --task is required${NC}"
    echo ""
    show_help
    exit 1
fi

# Build command
CMD="python3 '$SCRIPT_DIR/autonomous_code_agent.py'"
CMD="$CMD --task '$TASK'"
CMD="$CMD --llm-type '$LLM_TYPE'"

if [ -n "$MODEL" ]; then
    CMD="$CMD --model '$MODEL'"
fi

if [ -n "$DRY_RUN" ]; then
    CMD="$CMD $DRY_RUN"
fi

# Set environment based on LLM type
if [ "$LLM_TYPE" = "ollama" ]; then
    export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
    export OLLAMA_MODEL="${OLLAMA_MODEL:-mistral}"
    echo -e "${GREEN}Using Ollama${NC}"
    echo "  Base URL: $OLLAMA_BASE_URL"
    echo "  Model: $OLLAMA_MODEL"
elif [ "$LLM_TYPE" = "lmstudio" ]; then
    export LMSTUDIO_BASE_URL="${LMSTUDIO_BASE_URL:-http://127.0.0.1:1234/v1}"
    export LMSTUDIO_MODEL="${LMSTUDIO_MODEL:-local-model}"
    echo -e "${GREEN}Using LM Studio${NC}"
    echo "  Base URL: $LMSTUDIO_BASE_URL"
    echo "  Model: $LMSTUDIO_MODEL"
fi

echo ""
echo -e "${YELLOW}Task:${NC} $TASK"
if [ -n "$DRY_RUN" ]; then
    echo -e "${YELLOW}Mode:${NC} Dry-run (analysis only)"
fi
echo ""

# Run the agent
cd "$REPO_ROOT"
eval "$CMD"
