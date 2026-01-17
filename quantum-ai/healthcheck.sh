#!/bin/bash
# Health check for Quantum AI API
# Exit 0 if healthy, 1 if unhealthy

PORT="${PORT:-5050}"
HOST="${HOST:-localhost}"
TIMEOUT="${TIMEOUT:-5}"

curl -sf --max-time "$TIMEOUT" "http://${HOST}:${PORT}/health" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ API healthy on ${HOST}:${PORT}"
    exit 0
else
    echo "❌ API unhealthy or not responding on ${HOST}:${PORT}"
    exit 1
fi
