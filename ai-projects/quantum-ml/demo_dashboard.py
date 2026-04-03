#!/usr/bin/env python3
"""
Quick demo of the Quantum AI Web Dashboard
Tests that everything is working correctly
"""
import time

import requests

BASE_URL = "http://localhost:5000"

print("=" * 70)
print("  🧪 Quantum AI Dashboard - Quick Demo")
print("=" * 70)
print()

# Test 1: Check if server is running
print("1. Testing server connection...")
try:
    response = requests.get(f"{BASE_URL}/api/datasets", timeout=2)
    if response.status_code == 200:
        datasets = response.json()
        print(f"   ✅ Server is running! Found {len(datasets)} datasets.")
    else:
        print(f"   ❌ Server returned error: {response.status_code}")
        exit(1)
except requests.exceptions.ConnectionError:
    print("   ❌ Server not running! Start with: ./start_dashboard.sh")
    exit(1)

# Test 2: List datasets
print("\n2. Available datasets:")
for ds in datasets:
    print(f"   • {ds['name']} ({ds['features']} features)")

# Test 3: Start a quick training session
print("\n3. Starting 1-minute training demo...")
config = {
    "dataset": "heart",
    "n_qubits": 3,
    "n_layers": 1,
    "learning_rate": 0.02,
    "duration_minutes": 1,
    "batch_size": 16,
}

# Use timeout for all requests to prevent hanging
REQUEST_TIMEOUT = 30  # seconds

response = requests.post(
    f"{BASE_URL}/api/train/start", json=config, timeout=REQUEST_TIMEOUT
)
if response.status_code != 200:
    print(f"   ❌ Failed to start training: {response.text}")
    exit(1)

session = response.json()
session_id = session["session_id"]
print(f"   ✅ Training started: {session_id}")

# Test 4: Monitor training
print("\n4. Monitoring training progress...")
print("   (Press Ctrl+C to stop)\n")

try:
    for i in range(60):  # Monitor for up to 60 seconds
        response = requests.get(
            f"{BASE_URL}/api/train/status/{session_id}", timeout=REQUEST_TIMEOUT
        )
        status = response.json()

        epoch = status["current_epoch"]
        loss = status["current_loss"]
        acc = status["best_val_acc"] * 100

        print(
            f"   Epoch {epoch:3d} | Loss: {loss:.4f} | Best Acc: {acc:5.2f}%", end="\r"
        )

        if status["status"] in ["completed", "error", "stopped"]:
            print()  # New line
            if status["status"] == "completed":
                print("\n   ✅ Training completed!")
                print(f"   Final accuracy: {acc:.2f}%")
                print(f"   Total epochs: {status['total_epochs']}")
            else:
                print(f"\n   ⚠️  Training {status['status']}")
            break

        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n   ⏹️  Stopping training...")
    requests.post(f"{BASE_URL}/api/train/stop/{session_id}", timeout=REQUEST_TIMEOUT)
    print("   ✅ Training stopped")

# Test 5: List results
print("\n5. Checking training history...")
response = requests.get(f"{BASE_URL}/api/results", timeout=REQUEST_TIMEOUT)
results = response.json()
print(f"   ✅ Found {len(results)} training sessions in history")

print("\n" + "=" * 70)
print("  ✅ Demo Complete!")
print("=" * 70)
print("\n💡 Open your browser to http://localhost:5000 for the full UI!\n")
