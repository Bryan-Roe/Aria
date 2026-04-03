#!/bin/bash
# Complete Repository Automation Startup Script
# One-command automation for the entire Aria repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

function print_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║              🚀 ARIA REPOSITORY AUTOMATION SYSTEM 🚀                         ║
║                  Complete Automation for the Entire Repo                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

function show_components() {
    echo -e "${CYAN}Available Components:${NC}"
    echo ""
    echo "  1. ${GREEN}aria${NC}       - Aria character (server + training)"
    echo "  2. ${GREEN}training${NC}   - LoRA training pipelines"
    echo "  3. ${GREEN}quantum${NC}    - Quantum computing workflows"
    echo "  4. ${GREEN}evaluation${NC} - Model evaluation system"
    echo "  5. ${GREEN}datasets${NC}   - Auto dataset discovery"
    echo "  6. ${GREEN}monitoring${NC} - System health monitoring"
    echo "  7. ${GREEN}backup${NC}     - Automated backups"
    echo ""
    echo "  ${YELLOW}ALL${NC}        - Start all components"
    echo ""
}

function show_menu() {
    echo -e "${BLUE}Select automation mode:${NC}"
    echo ""
    echo "  ${GREEN}1)${NC} Full Automation    - Start ALL components (production)"
    echo "  ${GREEN}2)${NC} Aria Only          - Just Aria character automation"
    echo "  ${GREEN}3)${NC} Training Pipeline  - Training + evaluation only"
    echo "  ${GREEN}4)${NC} Custom Selection   - Choose specific components"
    echo "  ${GREEN}5)${NC} Status             - Check current automation status"
    echo "  ${GREEN}6)${NC} Stop All           - Stop all automation"
    echo "  ${GREEN}0)${NC} Exit"
    echo ""
    read -p "Enter choice [0-6]: " choice
}

function check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python 3: $(python3 --version)${NC}"

    if ! python3 -c "import psutil" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  psutil not installed, installing...${NC}"
        pip3 install psutil
    fi
    echo -e "${GREEN}✅ psutil installed${NC}"
}

function start_full_automation() {
    echo -e "${GREEN}🚀 Starting Full Repository Automation...${NC}"
    echo ""
    python3 "$REPO_ROOT/scripts/repo_automation.py" --start --daemon
}

function start_aria_only() {
    echo -e "${GREEN}🚀 Starting Aria Automation Only...${NC}"
    echo ""
    python3 "$REPO_ROOT/scripts/repo_automation.py" --start --components aria --daemon
}

function start_training_pipeline() {
    echo -e "${GREEN}🚀 Starting Training Pipeline...${NC}"
    echo ""
    python3 "$REPO_ROOT/scripts/repo_automation.py" --start --components training,evaluation --daemon
}

function start_custom() {
    echo ""
    show_components
    read -p "Enter components (comma-separated, e.g., aria,training,quantum): " components

    if [ -z "$components" ]; then
        echo -e "${RED}❌ No components specified${NC}"
        return
    fi

    echo -e "${GREEN}🚀 Starting selected components...${NC}"
    echo ""
    python3 "$REPO_ROOT/scripts/repo_automation.py" --start --components "$components" --daemon
}

function show_status() {
    python3 "$REPO_ROOT/scripts/repo_automation.py" --status
}

function stop_all() {
    echo -e "${YELLOW}🛑 Stopping all automation...${NC}"
    python3 "$REPO_ROOT/scripts/repo_automation.py" --stop
    echo -e "${GREEN}✅ All automation stopped${NC}"
}

function run_background() {
    local mode=$1
    echo -e "${GREEN}🚀 Starting in background mode...${NC}"

    case "$mode" in
        full)
            nohup python3 "$REPO_ROOT/scripts/repo_automation.py" --start --daemon \
                > "$REPO_ROOT/data_out/repo_automation/automation.log" 2>&1 &
            ;;
        aria)
            nohup python3 "$REPO_ROOT/scripts/repo_automation.py" --start --components aria --daemon \
                > "$REPO_ROOT/data_out/repo_automation/automation.log" 2>&1 &
            ;;
        training)
            nohup python3 "$REPO_ROOT/scripts/repo_automation.py" --start --components training,evaluation --daemon \
                > "$REPO_ROOT/data_out/repo_automation/automation.log" 2>&1 &
            ;;
        *)
            nohup python3 "$REPO_ROOT/scripts/repo_automation.py" --start --components "$mode" --daemon \
                > "$REPO_ROOT/data_out/repo_automation/automation.log" 2>&1 &
            ;;
    esac

    local pid=$!
    echo -e "${GREEN}✅ Started with PID $pid${NC}"
    echo -e "${BLUE}ℹ️  View logs: tail -f $REPO_ROOT/data_out/repo_automation/automation.log${NC}"
    echo -e "${BLUE}ℹ️  Check status: $0 status${NC}"
}

# Main script
print_banner
check_dependencies

# Check for command line arguments
if [ $# -gt 0 ]; then
    case "$1" in
        full|all)
            if [ "$2" == "--background" ] || [ "$2" == "-b" ]; then
                run_background "full"
            else
                start_full_automation
            fi
            exit 0
            ;;
        aria)
            if [ "$2" == "--background" ] || [ "$2" == "-b" ]; then
                run_background "aria"
            else
                start_aria_only
            fi
            exit 0
            ;;
        training)
            if [ "$2" == "--background" ] || [ "$2" == "-b" ]; then
                run_background "training"
            else
                start_training_pipeline
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
        components)
            if [ -z "$2" ]; then
                show_components
                exit 0
            else
                if [ "$3" == "--background" ] || [ "$3" == "-b" ]; then
                    run_background "$2"
                else
                    python3 "$REPO_ROOT/scripts/repo_automation.py" --start --components "$2" --daemon
                fi
                exit 0
            fi
            ;;
        --help|-h)
            echo "Usage: $0 [mode] [options]"
            echo ""
            echo "Modes:"
            echo "  full, all      Full automation (all components)"
            echo "  aria           Aria character only"
            echo "  training       Training pipeline only"
            echo "  components     List available components"
            echo "  status         Check automation status"
            echo "  stop           Stop all automation"
            echo ""
            echo "Options:"
            echo "  --background, -b    Run in background"
            echo ""
            echo "Examples:"
            echo "  $0 full              # Start everything"
            echo "  $0 aria -b           # Start Aria in background"
            echo "  $0 components aria,training  # Custom selection"
            echo "  $0 status            # Check status"
            echo "  $0 stop              # Stop all"
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
            start_full_automation
            break
            ;;
        2)
            start_aria_only
            break
            ;;
        3)
            start_training_pipeline
            break
            ;;
        4)
            start_custom
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

    echo ""
    read -p "Press Enter to continue..."
    echo ""
done
