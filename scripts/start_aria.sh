#!/bin/bash
# Aria Automation Quick Start Script
# Simplifies starting Aria automation with common configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARIA_ROOT="$(dirname "$SCRIPT_DIR")"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════╗"
    echo "║   🤖 Aria Automation Quick Start 🤖   ║"
    echo "╔═══════════════════════════════════════╝"
    echo -e "${NC}"
}

function check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python 3: $(python3 --version)${NC}"
    
    # Check psutil
    if ! python3 -c "import psutil" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  psutil not installed, installing...${NC}"
        pip3 install psutil
    fi
    echo -e "${GREEN}✅ psutil installed${NC}"
    
    # Check func (optional)
    if command -v func &> /dev/null; then
        echo -e "${GREEN}✅ Azure Functions Core Tools: $(func --version)${NC}"
    else
        echo -e "${YELLOW}⚠️  Azure Functions Core Tools not found (backend won't start)${NC}"
        echo -e "${YELLOW}   Install from: https://docs.microsoft.com/azure/azure-functions/functions-run-local${NC}"
    fi
}

function show_menu() {
    echo ""
    echo -e "${BLUE}Select automation mode:${NC}"
    echo "  1) Full Stack     - Server + Backend + Training + Monitoring (recommended)"
    echo "  2) Server Only    - Aria web interface only"
    echo "  3) Training Only  - Continuous training (no server)"
    echo "  4) Single Train   - One training cycle and exit"
    echo "  5) Status         - Check current automation status"
    echo "  6) Stop All       - Stop all Aria processes"
    echo "  0) Exit"
    echo ""
    read -p "Enter choice [0-6]: " choice
}

function start_full_stack() {
    echo -e "${GREEN}🚀 Starting Aria Full Stack...${NC}"
    python3 "$ARIA_ROOT/scripts/aria_automation.py" --mode full
}

function start_server_only() {
    echo -e "${GREEN}🚀 Starting Aria Server Only...${NC}"
    python3 "$ARIA_ROOT/scripts/aria_automation.py" --mode server
}

function start_training_continuous() {
    echo -e "${GREEN}🚀 Starting Continuous Training...${NC}"
    python3 "$ARIA_ROOT/scripts/aria_automation.py" --mode training
}

function start_training_once() {
    echo -e "${GREEN}🚀 Running Single Training Cycle...${NC}"
    python3 "$ARIA_ROOT/scripts/aria_automation.py" --mode training --once
}

function show_status() {
    python3 "$ARIA_ROOT/scripts/aria_automation.py" --status
}

function stop_all() {
    echo -e "${YELLOW}🛑 Stopping all Aria processes...${NC}"
    python3 "$ARIA_ROOT/scripts/aria_automation.py" --stop
    echo -e "${GREEN}✅ All processes stopped${NC}"
}

function run_background() {
    local mode=$1
    echo -e "${GREEN}🚀 Starting Aria in background (mode: $mode)...${NC}"
    
    nohup python3 "$ARIA_ROOT/scripts/aria_automation.py" --mode "$mode" \
        > "$ARIA_ROOT/data_out/aria_automation/aria_automation.log" 2>&1 &
    
    local pid=$!
    echo -e "${GREEN}✅ Started with PID $pid${NC}"
    echo -e "${BLUE}ℹ️  View logs: tail -f $ARIA_ROOT/data_out/aria_automation/aria_automation.log${NC}"
    echo -e "${BLUE}ℹ️  Check status: $0 status${NC}"
}

# Main script
print_banner
check_dependencies

# Check for command line arguments
if [ $# -gt 0 ]; then
    case "$1" in
        full|server|training)
            if [ "$2" == "--background" ] || [ "$2" == "-b" ]; then
                run_background "$1"
            elif [ "$2" == "--once" ] && [ "$1" == "training" ]; then
                start_training_once
            else
                python3 "$ARIA_ROOT/scripts/aria_automation.py" --mode "$1"
            fi
            exit 0
            ;;
        status)
            show_status
            exit 0
            ;;
        stop)
            stop_all
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [mode] [options]"
            echo ""
            echo "Modes:"
            echo "  full        Full stack (server + backend + training)"
            echo "  server      Server only"
            echo "  training    Continuous training"
            echo "  status      Check status"
            echo "  stop        Stop all"
            echo ""
            echo "Options:"
            echo "  --background, -b    Run in background"
            echo "  --once              Single training cycle (training mode only)"
            echo ""
            echo "Examples:"
            echo "  $0 full             # Start full stack (foreground)"
            echo "  $0 full -b          # Start full stack (background)"
            echo "  $0 training --once  # Single training cycle"
            echo "  $0 status           # Check status"
            echo "  $0 stop             # Stop all"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid mode: $1${NC}"
            echo "Run '$0 --help' for usage"
            exit 1
            ;;
    esac
fi

# Interactive menu
while true; do
    show_menu
    
    case $choice in
        1)
            start_full_stack
            break
            ;;
        2)
            start_server_only
            break
            ;;
        3)
            start_training_continuous
            break
            ;;
        4)
            start_training_once
            break
            ;;
        5)
            show_status
            ;;
        6)
            stop_all
            ;;
        0)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid choice${NC}"
            ;;
    esac
done
