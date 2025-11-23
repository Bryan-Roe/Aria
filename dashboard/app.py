from flask import Flask, render_template, jsonify
import json
from pathlib import Path

app = Flask(__name__)

DATA_OUT = Path(__file__).resolve().parents[1] / "data_out"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    # Load orchestrator status
    status_files = ["autotrain/status.json", "quantum_autorun/status.json", "evaluation_autorun/status.json"]
    results = {}
    for fname in status_files:
        fpath = DATA_OUT / fname
        if fpath.exists():
            with fpath.open() as f:
                results[fname] = json.load(f)
    return jsonify(results)

@app.route("/resources")
def resources():
    # Load latest resource snapshot
    snap_path = DATA_OUT / "resource_monitor_snapshot.json"
    if snap_path.exists():
        with snap_path.open() as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No snapshot found"})

@app.route("/results")
def results():
    # Load latest exported results
    res_path = Path(__file__).resolve().parents[1] / "exports" / "all_orchestrators.json"
    if res_path.exists():
        with res_path.open() as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No results found"})

if __name__ == "__main__":
    app.run(debug=True)
