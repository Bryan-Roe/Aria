#!/bin/bash
# Quantum AI Training Dashboard - Startup Script

echo "=============================================================="
echo "  🚀 Starting Quantum AI Training Dashboard"
echo "=============================================================="
echo ""

# Check if venv exists
if [ ! -d "./venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate venv
source ./venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q flask flask-cors pennylane numpy pandas scikit-learn

echo ""
echo "✅ Starting web server..."
echo ""
echo "📡 Dashboard will be available at: http://localhost:5000"
echo ""
echo "💡 Features:"
echo "   • Real-time training visualization"
echo "   • Interactive parameter tuning"
echo "   • Live loss/accuracy charts"
echo "   • Training history browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================================="
echo ""

# Start the app
python web_app.py
