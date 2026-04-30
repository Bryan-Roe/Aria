#!/bin/bash
# Quick demo of Aria automation capabilities
# Shows all major features in action

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 Aria Automation Demo 🤖                                ║
║              Demonstrating Full Automation Capabilities                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${YELLOW}This demo will showcase:${NC}"
echo "  1. Automation test suite"
echo "  2. Status checking"
echo "  3. Available commands"
echo "  4. Configuration validation"
echo ""
read -p "Press Enter to continue..."

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}STEP 1: Running Automation Test Suite${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
python3 scripts/test_aria_automation.py

echo ""
read -p "Press Enter to continue..."

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}STEP 2: Checking Current Status${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
python3 scripts/aria_automation.py --status || echo "No automation currently running (this is normal)"

echo ""
read -p "Press Enter to continue..."

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}STEP 3: Available Automation Commands${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Start Commands:${NC}"
echo "  ./scripts/start_aria.sh                    # Interactive menu"
echo "  ./scripts/start_aria.sh full               # Full stack"
echo "  ./scripts/start_aria.sh full --background  # Background mode"
echo "  ./scripts/start_aria.sh server             # Server only"
echo "  ./scripts/start_aria.sh training --once    # Single training"
echo ""
echo -e "${YELLOW}Management Commands:${NC}"
echo "  ./scripts/start_aria.sh status             # Check status"
echo "  ./scripts/start_aria.sh stop               # Stop all"
echo ""
echo -e "${YELLOW}Direct Python Commands:${NC}"
echo "  python3 scripts/aria_automation.py --mode full      # Full automation"
echo "  python3 scripts/aria_automation.py --mode server    # Server only"
echo "  python3 scripts/aria_automation.py --mode training  # Training only"
echo "  python3 scripts/aria_automation.py --status         # Status check"
echo "  python3 scripts/aria_automation.py --stop           # Stop all"
echo ""

read -p "Press Enter to continue..."

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}STEP 4: Configuration Files${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Automation Scripts:${NC}"
ls -lh scripts/aria_automation.py scripts/start_aria.sh scripts/test_aria_automation.py 2>/dev/null || echo "Scripts directory not accessible"
echo ""
echo -e "${YELLOW}Configuration Files:${NC}"
ls -lh config/aria_automation.service config/master_orchestrator.yaml 2>/dev/null || echo "Config directory not accessible"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
ls -lh ARIA_AUTOMATION_GUIDE.md ARIA_AUTOMATION_SUMMARY.md ARIA_QUICKREF.txt 2>/dev/null || echo "Documentation not accessible"
echo ""

read -p "Press Enter to continue..."

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}STEP 5: Quick Reference${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
cat ARIA_QUICKREF.txt
echo ""

read -p "Press Enter to continue..."

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}STEP 6: Integration Options${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Background Service Options:${NC}"
echo ""
echo "1. Systemd (Linux - Recommended for Production)"
echo "   sudo cp config/aria_automation.service /etc/systemd/system/"
echo "   sudo systemctl enable aria_automation"
echo "   sudo systemctl start aria_automation"
echo ""
echo "2. Screen (SSH Sessions)"
echo "   screen -S aria"
echo "   python3 scripts/aria_automation.py --mode full"
echo "   # Detach: Ctrl+A, then D"
echo ""
echo "3. Nohup (Simple Background)"
echo "   nohup python3 scripts/aria_automation.py --mode full > aria.log 2>&1 &"
echo ""
echo "4. Cron (Scheduled Training)"
echo "   crontab -e"
echo "   # Add: */30 * * * * cd /workspaces/Aria && python3 scripts/aria_automation.py --mode training --once"
echo ""
echo "5. Master Orchestrator (Advanced)"
echo "   python3 scripts/master_orchestrator.py --workflow aria_full_stack"
echo ""

read -p "Press Enter to finish..."

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                         🎉 Demo Complete! 🎉                                  ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Aria automation is fully configured and ready to use!                        ║${NC}"
echo -e "${GREEN}║                                                                               ║${NC}"
echo -e "${GREEN}║  Quick Start:                                                                 ║${NC}"
echo -e "${GREEN}║    ./scripts/start_aria.sh                    # Interactive menu              ║${NC}"
echo -e "${GREEN}║    ./scripts/start_aria.sh full               # Start full automation         ║${NC}"
echo -e "${GREEN}║                                                                               ║${NC}"
echo -e "${GREEN}║  Documentation:                                                               ║${NC}"
echo -e "${GREEN}║    ARIA_AUTOMATION_GUIDE.md     - Complete guide                              ║${NC}"
echo -e "${GREEN}║    ARIA_AUTOMATION_SUMMARY.md   - Quick summary                               ║${NC}"
echo -e "${GREEN}║    ARIA_QUICKREF.txt            - Command reference                           ║${NC}"
echo -e "${GREEN}║                                                                               ║${NC}"
echo -e "${GREEN}║  Access Points:                                                               ║${NC}"
echo -e "${GREEN}║    http://localhost:8080              - Aria web interface                    ║${NC}"
echo -e "${GREEN}║    http://localhost:8080/auto-execute.html - Auto-execute page                ║${NC}"
echo -e "${GREEN}║    http://localhost:7071/api/ai/status - Backend API                          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Would you like to start Aria automation now?${NC}"
read -p "Start automation? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${GREEN}Starting Aria automation...${NC}"
    ./scripts/start_aria.sh
else
    echo ""
    echo -e "${YELLOW}To start later, run: ./scripts/start_aria.sh${NC}"
fi
