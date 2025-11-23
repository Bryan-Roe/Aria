# QAI Automation Dashboard

A simple Flask web dashboard for monitoring orchestrator status, resource usage, and results export.

## Features
- Orchestrator status (autotrain, quantum_autorun, evaluation_autorun)
- Resource monitor snapshot
- Results export (all orchestrators)

## Usage
1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
2. Run the dashboard:
   ```powershell
   python app.py
   ```
3. Open [http://localhost:5000](http://localhost:5000) in your browser.

## Endpoints
- `/` : Main dashboard
- `/status` : Orchestrator status JSON
- `/resources` : Resource monitor snapshot JSON
- `/results` : Results export JSON

## Customization
- Add more endpoints or UI sections as needed.
- Integrate with authentication or advanced visualization if desired.
