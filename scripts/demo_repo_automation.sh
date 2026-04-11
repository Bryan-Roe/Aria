#!/bin/bash
# Quick Demo of Repository Automation System

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║           🚀 REPOSITORY AUTOMATION SYSTEM DEMO 🚀                            ║
║               Complete Automation for Aria Repository                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${CYAN}This demo will show you:${NC}"
echo "  1. Test suite validation"
echo "  2. Component overview"
echo "  3. Usage examples"
echo "  4. Status checking"
echo ""
read -p "Press Enter to continue..."

# Step 1: Run tests
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 1: Running Test Suite${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
python3 "$REPO_ROOT/scripts/test_repo_automation.py"

read -p "Press Enter to continue..."

# Step 2: Show components
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 2: Available Components${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}✨ aria${NC}       - Aria character (server + training)"
echo -e "${CYAN}🎓 training${NC}   - LoRA training pipelines"
echo -e "${CYAN}⚛️  quantum${NC}    - Quantum computing workflows"
echo -e "${CYAN}📊 evaluation${NC} - Model evaluation system"
echo -e "${CYAN}📦 datasets${NC}   - Auto dataset discovery"
echo -e "${CYAN}🏥 monitoring${NC} - System health monitoring"
echo -e "${CYAN}💾 backup${NC}     - Automated backups"
echo ""

read -p "Press Enter to continue..."

# Step 3: Usage examples
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 3: Usage Examples${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}🚀 Start everything:${NC}"
echo "   ./scripts/start_repo_automation.sh full"
echo ""
echo -e "${YELLOW}🎭 Start Aria only:${NC}"
echo "   ./scripts/start_repo_automation.sh aria"
echo ""
echo -e "${YELLOW}🎓 Start training pipeline:${NC}"
echo "   ./scripts/start_repo_automation.sh training"
echo ""
echo -e "${YELLOW}🎯 Custom selection:${NC}"
echo "   ./scripts/start_repo_automation.sh components aria,training,quantum"
echo ""
echo -e "${YELLOW}📊 Check status:${NC}"
echo "   ./scripts/start_repo_automation.sh status"
echo ""
echo -e "${YELLOW}🛑 Stop all:${NC}"
echo "   ./scripts/start_repo_automation.sh stop"
echo ""
echo -e "${YELLOW}🌙 Background mode:${NC}"
echo "   ./scripts/start_repo_automation.sh full --background"
echo ""

read -p "Press Enter to continue..."

# Step 4: Check current status
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 4: Current Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
python3 "$REPO_ROOT/scripts/repo_automation.py" --status

echo ""
echo -e "${GREEN}✅ Demo complete!${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "  1. Start automation: ./scripts/start_repo_automation.sh"
echo "  2. Read the guide: cat REPO_AUTOMATION_GUIDE.md"
echo "  3. Monitor status: ./scripts/start_repo_automation.sh status"
echo ""
echo -e "${YELLOW}Happy automating! 🚀${NC}"
