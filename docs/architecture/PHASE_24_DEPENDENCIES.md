# Phase 24 Dependencies & Installation

## Required for WebSocket Server (Phase 23)

```powershell
pip install websockets watchdog
```

**Purpose:**
- `websockets`: WebSocket server for real-time dashboard updates
- `watchdog`: File system monitoring for job status changes

**Usage:**
```powershell
# Start WebSocket server
python dashboard/websocket_server.py

# WebSocket endpoint
ws://localhost:8765
```

---

## Optional for Windows Notifications (Phase 24)

```powershell
pip install win10toast
```

**Purpose:**
- Windows 10/11 native toast notifications
- Only needed for Python CLI notification tool
- Browser notifications require NO dependencies

**Platforms:**
- **Windows**: `pip install win10toast` (recommended)
- **macOS**: No dependencies (uses built-in `osascript`)
- **Linux**: No dependencies (uses built-in `notify-send`)

**Usage:**
```powershell
# Test notification
python scripts/notification_system.py --test

# Monitor training job
python scripts/notification_system.py --monitor data_out/autotrain/status.json --job-name test
```

---

## No Dependencies Required

The following Phase 24 features require **NO additional installations**:

✅ **Export Functionality** (PNG/CSV/TXT)
- Browser-based export
- Uses native canvas API and blob downloads
- Works in all modern browsers

✅ **Backup Manager**
- Pure Python implementation
- Uses stdlib: `os`, `shutil`, `json`, `tarfile`, `hashlib`
- Cross-platform compatible

✅ **Browser Notifications**
- Uses Web Notifications API (built into browsers)
- No npm packages or libraries needed
- Supported in Chrome, Firefox, Edge, Safari

---

## Installation Commands Summary

```powershell
# WebSocket server (Phase 23 - REQUIRED for real-time updates)
pip install websockets watchdog

# Windows notifications (Phase 24 - OPTIONAL for Python CLI)
pip install win10toast

# That's it! All other features are dependency-free.
```

---

## Verification

```powershell
# Check installed packages
pip list | Select-String "websockets|watchdog|win10toast"

# Expected output:
# watchdog      x.x.x
# websockets    x.x.x
# win10toast    x.x.x (if installed)
```

---

## Feature Dependency Matrix

| Feature | Dependencies | Status |
| --------- | -------------- | -------- |
| WebSocket Server | websockets, watchdog | Required for Phase 23 |
| Export (PNG/CSV/TXT) | None | Phase 24 ✅ |
| Backup Manager | None | Phase 24 ✅ |
| Browser Notifications | None | Phase 24 ✅ |
| Python CLI Notifications | win10toast (Windows only) | Phase 24 ✅ Optional |
| Analytics Dashboard | Chart.js (CDN) | Phase 23 ✅ |
| Job Queue | None | Phase 23 ✅ |
| Model Comparison | None | Phase 23 ✅ |
| Config Templates | None | Phase 23 ✅ |

---

## Troubleshooting

### WebSocket Issues

**Error**: `ModuleNotFoundError: No module named 'websockets'`

**Fix**:
```powershell
pip install websockets watchdog
```

### Windows Notification Issues

**Error**: `ModuleNotFoundError: No module named 'win10toast'`

**Fix** (optional):
```powershell
pip install win10toast
```

**Fallback**: Python CLI will print to console if library not installed

### Browser Notification Issues

**Error**: "Notification API not supported"

**Fix**: Use a modern browser (Chrome 22+, Firefox 22+, Edge 14+, Safari 7+)

---

Last Updated: November 2024
