#!/bin/bash
# Start LLM Maker Web UI

echo "================================================"
echo "Starting LLM Maker Web UI..."
echo "================================================"
echo ""

cd "$(dirname "$0")"

echo "Checking dependencies..."
python3 -c "import sys; sys.path.insert(0, 'src'); from tool_maker import ToolMaker" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: LLM Maker components not found"
    echo "Please ensure you're in the llm-maker directory"
    exit 1
fi

echo "✓ Dependencies OK"
echo ""
echo "Starting web server on http://localhost:8090"
echo "Press Ctrl+C to stop"
echo ""

python3 web_server.py
