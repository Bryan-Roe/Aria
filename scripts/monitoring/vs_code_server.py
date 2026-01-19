#!/usr/bin/env python
"""Auto Ops VS Code Integration Server

Provides a real-time web dashboard for VS Code to display auto operations status.
Serves on localhost:8765 for VS Code's Simple Browser.

Usage:
  python scripts/monitoring/vs_code_server.py
  
Then access: http://localhost:8765 in VS Code Simple Browser
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Import dashboard aggregation
from scripts.monitoring.auto_ops_dashboard import (
    get_all_statuses,
    parse_autonomous_training,
    parse_autotrain,
    parse_evaluation,
    parse_quantum,
    parse_gguf_training,
    parse_train_and_promote,
    parse_master_orchestrator,
    parse_training_scheduler,
    parse_auto_scheduler,
    parse_ci_pipeline,
)

app = Flask(__name__)
CORS(app)

# HTML Template for VS Code dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto Ops Dashboard - VS Code</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            padding: 16px;
            font-size: 13px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--vscode-sideBar-border);
        }
        
        .header h1 {
            font-size: 18px;
            font-weight: 600;
        }
        
        .header-controls {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .refresh-badge {
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
            padding: 4px 8px;
            background: var(--vscode-input-background);
            border-radius: 3px;
        }
        
        .control-btn {
            padding: 6px 12px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.2s;
        }
        
        .control-btn:hover {
            background: var(--vscode-button-hoverBackground);
        }
        
        .control-btn.secondary {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        
        .category {
            margin-bottom: 24px;
        }
        
        .category-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--vscode-descriptionForeground);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--vscode-sideBar-border);
        }
        
        .operation {
            display: flex;
            gap: 12px;
            padding: 12px;
            margin-bottom: 8px;
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s, border-color 0.2s;
        }
        
        .operation:hover {
            background: var(--vscode-editor-lineHighlightBackground);
            border-color: var(--vscode-focusBorder);
        }
        
        .op-status {
            font-size: 18px;
            min-width: 24px;
            text-align: center;
        }
        
        .op-content {
            flex: 1;
        }
        
        .op-header {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 4px;
        }
        
        .op-name {
            font-weight: 500;
            color: var(--vscode-editor-foreground);
        }
        
        .op-status-text {
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 2px;
            background: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
        }
        
        .op-status-text.running {
            background: #4ec9b0;
            color: white;
        }
        
        .op-status-text.idle {
            background: #808080;
            color: white;
        }
        
        .op-status-text.success {
            background: #4ec9b0;
            color: white;
        }
        
        .op-status-text.error {
            background: #f48771;
            color: white;
        }
        
        .op-metrics {
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
            line-height: 1.4;
        }
        
        .op-metric {
            display: inline-block;
            margin-right: 16px;
        }
        
        .op-alert {
            margin-top: 6px;
            padding: 6px 8px;
            background: #3d3d00;
            border-left: 3px solid #ffd700;
            border-radius: 2px;
            font-size: 11px;
            color: #ffee99;
        }
        
        .op-alert.error {
            background: #3d0000;
            border-left-color: #ff6b6b;
            color: #ff9999;
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: var(--vscode-input-border);
            border-radius: 2px;
            overflow: hidden;
            margin: 6px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: #4ec9b0;
            transition: width 0.3s;
        }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
            padding: 12px;
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
        }
        
        .summary-item {
            text-align: center;
        }
        
        .summary-value {
            font-size: 24px;
            font-weight: 600;
            color: var(--vscode-editor-foreground);
        }
        
        .summary-label {
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
            text-transform: uppercase;
            margin-top: 4px;
        }
        
        .no-data {
            color: var(--vscode-descriptionForeground);
            text-align: center;
            padding: 32px 16px;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Auto Operations Dashboard</h1>
            <div class="header-controls">
                <span class="refresh-badge" id="refresh-badge">Auto-refresh: 5s</span>
                <button class="control-btn secondary" onclick="toggleAutoRefresh()">Pause</button>
                <button class="control-btn" onclick="refreshNow()">Refresh</button>
            </div>
        </div>
        
        <div class="summary" id="summary">
            <div class="summary-item">
                <div class="summary-value" id="total-running">0</div>
                <div class="summary-label">Running</div>
            </div>
            <div class="summary-item">
                <div class="summary-value" id="total-success">0</div>
                <div class="summary-label">Success</div>
            </div>
            <div class="summary-item">
                <div class="summary-value" id="total-failed">0</div>
                <div class="summary-label">Failed</div>
            </div>
            <div class="summary-item">
                <div class="summary-value" id="total-alerts">0</div>
                <div class="summary-label">Alerts</div>
            </div>
        </div>
        
        <div id="dashboard">Loading...</div>
    </div>
    
    <script>
        let autoRefreshEnabled = true;
        let refreshInterval = null;
        
        async function loadDashboard() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                renderDashboard(data);
            } catch (error) {
                console.error('Failed to load dashboard:', error);
                document.getElementById('dashboard').innerHTML = '<div class="no-data">Connection error. Retrying...</div>';
            }
        }
        
        function renderDashboard(data) {
            const categories = {
                learning: [],
                evaluation: [],
                scheduling: [],
                deployment: [],
                ci: []
            };
            
            let totals = { running: 0, success: 0, failed: 0, alerts: 0 };
            
            data.operations.forEach(op => {
                if (categories[op.category]) {
                    categories[op.category].push(op);
                }
                
                if (op.status === 'running') totals.running++;
                if (op.status === 'success') totals.success++;
                if (op.status === 'error') totals.failed++;
                if (op.alerts.length > 0) totals.alerts++;
            });
            
            // Update summary
            document.getElementById('total-running').textContent = totals.running;
            document.getElementById('total-success').textContent = totals.success;
            document.getElementById('total-failed').textContent = totals.failed;
            document.getElementById('total-alerts').textContent = totals.alerts;
            
            // Render categories
            const categoryTitles = {
                learning: '🤖 Learning & Training',
                evaluation: '📊 Evaluation & Analysis',
                scheduling: '⏰ Scheduling & Orchestration',
                deployment: '🚀 Deployment',
                ci: '🔄 CI/CD'
            };
            
            let html = '';
            Object.entries(categories).forEach(([key, ops]) => {
                if (ops.length === 0) return;
                
                html += `<div class="category">
                    <div class="category-title">${categoryTitles[key]}</div>
                    ${ops.map(op => renderOperation(op)).join('')}
                </div>`;
            });
            
            document.getElementById('dashboard').innerHTML = html;
        }
        
        function renderOperation(op) {
            const statusEmoji = {
                running: '🟢',
                idle: '⚪',
                success: '✅',
                error: '❌',
                scheduled: '📅',
                disabled: '🔒',
                unknown: '❓',
                active: '🟢'
            }[op.status] || '❓';
            
            let metricsHtml = '';
            Object.entries(op.metrics || {}).forEach(([key, val]) => {
                if (typeof val === 'object') return;
                metricsHtml += `<span class="op-metric"><strong>${key}:</strong> ${val}</span>`;
            });
            
            let alertsHtml = '';
            op.alerts.forEach(alert => {
                const isError = alert.includes('❌') || alert.includes('failed');
                alertsHtml += `<div class="op-alert ${isError ? 'error' : ''}">${alert}</div>`;
            });
            
            let progressHtml = '';
            if (op.progress > 0) {
                progressHtml = `<div class="progress-bar"><div class="progress-fill" style="width: ${op.progress}%"></div></div>`;
            }
            
            return `
                <div class="operation">
                    <div class="op-status">${statusEmoji}</div>
                    <div class="op-content">
                        <div class="op-header">
                            <div class="op-name">${op.name}</div>
                            <span class="op-status-text ${op.status}">${op.status}</span>
                        </div>
                        ${progressHtml}
                        <div class="op-metrics">${metricsHtml}</div>
                        ${alertsHtml}
                    </div>
                </div>
            `;
        }
        
        function toggleAutoRefresh() {
            autoRefreshEnabled = !autoRefreshEnabled;
            if (autoRefreshEnabled) {
                refreshInterval = setInterval(loadDashboard, 5000);
                document.querySelector('.refresh-badge').textContent = 'Auto-refresh: 5s';
                event.target.textContent = 'Pause';
            } else {
                clearInterval(refreshInterval);
                document.querySelector('.refresh-badge').textContent = 'Auto-refresh: Off';
                event.target.textContent = 'Resume';
            }
        }
        
        function refreshNow() {
            loadDashboard();
        }
        
        // Initial load and setup
        loadDashboard();
        refreshInterval = setInterval(loadDashboard, 5000);
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Serve dashboard HTML"""
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/status")
def api_status():
    """Get current status of all operations"""
    try:
        statuses = get_all_statuses()
        
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "operations": [
                {
                    "name": s.name,
                    "category": s.category,
                    "status": s.status,
                    "cycles_completed": s.cycles_completed,
                    "current_task": s.current_task,
                    "progress": s.progress,
                    "alerts": s.alerts,
                    "metrics": s.metrics,
                    "last_update": s.last_update,
                }
                for s in statuses
            ]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Manually trigger a refresh"""
    return jsonify({"status": "refreshed"})


def main():
    """Start the VS Code integration server"""
    port = 8765
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║           Auto Operations Dashboard - VS Code Server          ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

🚀 Server starting on http://localhost:{port}

📝 Usage:
   1. Keep this terminal open
   2. In VS Code: Ctrl+Shift+P → "Simple Browser: Open"
   3. Enter: http://localhost:{port}
   4. Dashboard will auto-refresh every 5 seconds

✅ Features:
   • Real-time status of all 10 auto operations
   • Auto-refresh every 5 seconds
   • Summary metrics (running, success, failed, alerts)
   • Organized by category
   • Alert indicators
   • Progress tracking

🔗 API Endpoints:
   GET  http://localhost:{port}/          - Dashboard HTML
   GET  http://localhost:{port}/api/status - JSON status

Ctrl+C to stop
════════════════════════════════════════════════════════════════
""")
    
    app.run(host="localhost", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
