# QAI Notification System Guide

## Overview

The QAI platform now includes a comprehensive desktop notification system that alerts users about training events, milestones, and system status - even when the browser window is minimized or in the background.

**Version**: 1.0
**Date**: November 2024
**Status**: Production Ready ✅

---

## Features

### 1. **Browser-Based Notifications** 🔔
- Native desktop notifications using Web Notifications API
- Cross-platform support (Windows, macOS, Linux)
- No external dependencies required
- Works in Chrome, Firefox, Edge, Safari

### 2. **Training Event Alerts**
- Job started notifications
- Job completed with duration and final loss
- Job failure alerts with error details
- Training milestone notifications (loss thresholds, epoch intervals)

### 3. **System Monitoring**
- GPU utilization alerts (>95% usage)
- Resource warnings
- Backup completion notifications
- Evaluation completion alerts

### 4. **User Control**
- Toggle button in QAI Hub header
- Persistent state across sessions
- Permission request on first use
- Visual feedback (🔔 on / 🔕 off)

---

## Installation & Setup

### Browser Integration (Production)

**No installation required!** The notification system is built into:
- `dashboard/unified.html` - Training dashboard
- `dashboard/analytics.html` - Analytics dashboard
- `dashboard/hub.html` - QAI Hub with toggle button

**First-time setup:**
1. Open http://localhost:8000/hub.html
2. Click the notification toggle button (🔕 icon in header)
3. Allow notifications when browser prompts
4. Toggle turns to 🔔 - you're all set!

### Python CLI Tool (Optional)

For system-level notifications or integration with external scripts:

```powershell
# Install dependencies (Windows only)
pip install win10toast

# Test notification
python scripts/notification_system.py --test

# Monitor training job
python scripts/notification_system.py --monitor data_out/autotrain/status.json --job-name phi35_test
```

**Platform-specific requirements:**
- **Windows**: `pip install win10toast`
- **macOS**: No dependencies (uses `osascript`)
- **Linux**: No dependencies (uses `notify-send`)

---

## Usage Guide

### Browser Notifications (Recommended)

#### Enable/Disable Notifications

1. **Via Hub Toggle**:
   - Navigate to http://localhost:8000/hub.html
   - Click notification button in header (top right)
   - Allow browser permission when prompted
   - Toggle anytime to enable/disable

2. **Automatic Integration**:
   - Unified dashboard checks status every 5 seconds
   - Auto-notifies on job state changes
   - No manual polling required

#### Notification Events

**Training Events:**
- 🚀 **Job Started**: "Training Started - Job 'phi35_mixed_chat' has begun training"
- ✅ **Job Complete**: "Training Complete - Job 'phi35_mixed_chat' finished in 45min with loss 0.2341"
- ❌ **Job Failed**: "Training Failed - Job 'phi35_mixed_chat' failed: CUDA out of memory"

**Milestones:**
- 🎯 **Loss Threshold**: "Milestone Reached - Job 'test': Loss below 0.5 = 0.4523"
- 🎯 **Epoch Milestone**: "Milestone Reached - Job 'test': Epoch 5 complete = 0.3245"

**System Alerts:**
- ⚠️ **GPU Warning**: "GPU Alert - GPU utilization at 97% (Memory: 10240MB)"
- 💾 **Backup Complete**: "Backup Complete - Created backup 'pre_prod_v1' (342.56 MB)"
- 📊 **Evaluation Done**: "Evaluation Complete - Model 'phi35_lora_v3' - Perplexity: 12.34"

### Python CLI Tool

#### Test Notifications

```powershell
# Send test notification
python scripts/notification_system.py --test
```

Output:
```
Sending test notifications...
✅ Test notification sent
```

You should see a desktop notification appear.

#### Monitor Training Jobs

```powershell
# Monitor single job
python scripts/notification_system.py \
  --monitor data_out/autotrain/status.json \
  --job-name phi35_mixed_chat
```

**Monitoring behavior:**
- Checks status file every 10 seconds
- Sends notification on job start
- Milestone alerts every 5 epochs
- Final notification on completion/failure
- Exits when job finishes

#### Integration in Scripts

```python
from scripts.notification_system import NotificationManager

notifier = NotificationManager()

# Job events
notifier.notify_job_started("phi35_test")
notifier.notify_job_completed("phi35_test", duration_min=45, final_loss=0.2341)
notifier.notify_job_failed("phi35_test", error="CUDA out of memory")

# Milestones
notifier.notify_milestone("phi35_test", "Loss below 0.5", 0.4523)

# System alerts
notifier.notify_gpu_alert(gpu_util=97, memory_used=10240)
notifier.notify_backup_complete("pre_prod_v1", size_mb=342.56)
notifier.notify_evaluation_complete("phi35_lora_v3", perplexity=12.34)
```

---

## Implementation Details

### Browser JavaScript (Unified Dashboard)

Located in `dashboard/unified.html` (lines 2334-2414):

```javascript
// Initialize notifications
let notificationsEnabled = false;

function initNotifications() {
    if ("Notification" in window) {
        if (Notification.permission === "granted") {
            notificationsEnabled = true;
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                notificationsEnabled = (permission === "granted");
            });
        }
    }
}

// Send notification
function sendDesktopNotification(title, message, icon = '🔔') {
    if (!notificationsEnabled) return;

    const notification = new Notification(title, {
        body: message,
        icon: 'data:image/svg+xml,<svg>...</svg>',
        requireInteraction: false,
        tag: 'qai-training'
    });

    notification.onclick = () => {
        window.focus();
        notification.close();
    };
}

// Training event helpers
function notifyJobStarted(jobName) { ... }
function notifyJobCompleted(jobName, durationMin, finalLoss) { ... }
function notifyJobFailed(jobName, error) { ... }
function notifyMilestone(jobName, milestone, value) { ... }
function notifyGPUAlert(gpuUtil, memoryUsed) { ... }
```

**Integration points:**
- Auto-refresh loop (every 5 seconds)
- Job status comparisons
- GPU monitoring thresholds
- Manual triggers from UI buttons

### Python CLI Tool

Located in `scripts/notification_system.py` (415 lines):

**Core classes:**
1. **NotificationManager**: Cross-platform notification sender
   - `send_notification(title, message, icon, duration)`
   - `notify_job_started/completed/failed()`
   - `notify_milestone()`, `notify_gpu_alert()`
   - Platform-specific methods: `_send_windows()`, `_send_macos()`, `_send_linux()`

2. **TrainingNotifier**: Training-specific monitoring wrapper
   - `monitor_training(job_name, status_file)` - Polls status JSON
   - Milestone tracking (loss thresholds, epoch intervals)
   - Automatic start/complete/fail detection

**Platform implementations:**
- **Windows**: `win10toast.ToastNotifier` (optional dependency)
- **macOS**: `osascript` shell command (built-in)
- **Linux**: `notify-send` command (built-in)

---

## Configuration

### Browser Notification Settings

**Permission levels:**
- `granted`: Notifications enabled
- `denied`: User blocked notifications (requires browser settings change)
- `default`: Not yet requested (will prompt on first toggle)

**Toggle state persistence:**
- Stored in browser localStorage (future enhancement)
- Currently resets on page reload
- Planned: Remember user preference across sessions

### Python CLI Milestones

Edit in `scripts/notification_system.py`:

```python
class TrainingNotifier:
    def __init__(self):
        self.milestones = {
            'loss_threshold': 0.5,  # Notify when loss drops below this
            'epoch_interval': 5      # Notify every N epochs
        }
```

**Customization examples:**
```python
# More frequent updates
self.milestones = {
    'loss_threshold': 0.3,  # Lower threshold
    'epoch_interval': 1     # Every epoch
}

# Less frequent (production)
self.milestones = {
    'loss_threshold': 0.1,  # Very low threshold
    'epoch_interval': 10    # Every 10 epochs
}
```

---

## Troubleshooting

### Browser Notifications Not Working

**Issue**: Toggle button doesn't show 🔔

**Solutions:**
1. Check browser support:
   ```javascript
   console.log("Notification" in window); // Should be true
   console.log(Notification.permission);  // Check permission state
   ```

2. Clear denied permissions:
   - Chrome: Settings → Privacy → Site Settings → Notifications
   - Firefox: Page Info → Permissions → Show Notifications
   - Edge: Settings → Cookies and site permissions → Notifications

3. Test manually:
   ```javascript
   new Notification("Test", { body: "This is a test" });
   ```

**Issue**: Notifications disappear too quickly

**Solution**: Increase duration in code:
```javascript
const notification = new Notification(title, {
    body: message,
    requireInteraction: true  // Stays until user dismisses
});
```

### Python CLI Issues

**Issue**: `ImportError: No module named 'win10toast'` (Windows)

**Solution**:
```powershell
pip install win10toast
```

**Issue**: Notifications fall back to console prints

**Cause**: Library not installed or platform not detected

**Check**:
```python
from scripts.notification_system import NotificationManager
notifier = NotificationManager()
print(f"System: {notifier.system}")
print(f"Enabled: {notifier.enabled}")
```

**Issue**: Monitor doesn't detect job changes

**Solutions:**
1. Verify status file exists:
   ```powershell
   Test-Path data_out/autotrain/status.json
   ```

2. Check JSON format:
   ```powershell
   Get-Content data_out/autotrain/status.json | ConvertFrom-Json
   ```

3. Run with verbose output:
   ```python
   # Add debug prints in monitor_training() loop
   print(f"Current status: {status}")
   ```

---

## Best Practices

### Development
- Test notifications before long training runs
- Use `--test` flag to verify system works
- Keep milestone intervals reasonable (every 5-10 epochs)
- Don't spam notifications (can be intrusive)

### Production
- Enable notifications for critical jobs only
- Set higher loss thresholds (e.g., 0.3 instead of 0.5)
- Use GPU alerts for resource monitoring
- Pair with backup notifications for safety

### User Experience
- Respect browser permission denials
- Provide clear toggle UI (🔔 vs 🔕)
- Include actionable information in messages
- Use appropriate icons for event types

### Integration
- Call `initNotifications()` on dashboard load
- Check `notificationsEnabled` before sending
- Gracefully handle permission denials
- Combine with WebSocket for real-time updates

---

## API Reference

### Browser JavaScript Functions

```javascript
// Initialization
initNotifications()  // Request permission if needed

// Toggle control
toggleNotifications()  // Enable/disable notifications

// Send notification
sendDesktopNotification(title, message, icon)
// title: string - Notification title
// message: string - Body text
// icon: string - Emoji or SVG data URI

// Training events
notifyJobStarted(jobName)
notifyJobCompleted(jobName, durationMin, finalLoss)
notifyJobFailed(jobName, error)
notifyMilestone(jobName, milestone, value)

// System alerts
notifyGPUAlert(gpuUtil, memoryUsed)
```

### Python CLI

```python
from scripts.notification_system import NotificationManager, TrainingNotifier

# Basic usage
notifier = NotificationManager()
notifier.send_notification("Title", "Message", icon="info", duration=10)

# Training-specific
notifier.notify_job_started("job_name")
notifier.notify_job_completed("job_name", duration_min=45, final_loss=0.234)
notifier.notify_job_failed("job_name", error="Error message")
notifier.notify_milestone("job_name", "Milestone description", value=0.456)

# System alerts
notifier.notify_gpu_alert(gpu_util=97, memory_used=10240)
notifier.notify_backup_complete("backup_name", size_mb=342.56)
notifier.notify_evaluation_complete("model_name", perplexity=12.34)

# Monitoring (blocking)
monitor = TrainingNotifier()
monitor.monitor_training("job_name", Path("status.json"))
```

---

## Future Enhancements

### Planned Features
- [ ] Persistent toggle state (localStorage)
- [ ] Notification history panel
- [ ] Customizable notification sounds
- [ ] Email/Slack integration
- [ ] Notification filtering (by job type, severity)
- [ ] Grouped notifications (batch updates)
- [ ] Rich notifications with action buttons
- [ ] Mobile push notifications (via PWA)

### Integration Roadmap
- [ ] WebSocket real-time event streaming
- [ ] Database logging of notification events
- [ ] Admin panel for notification settings
- [ ] Per-user notification preferences
- [ ] Notification analytics (sent/clicked/dismissed)

---

## Related Documentation

- **QAI Hub Guide**: `QAI_HUB_ENHANCEMENTS_V2.md` - Overview of all hub features
- **Backup System**: `scripts/backup_manager.py` - Triggers backup notifications
- **WebSocket Server**: `dashboard/websocket_server.py` - Real-time job updates
- **Analytics Dashboard**: `dashboard/analytics.html` - Notification integration

---

## Support

**Issues**: Report notification bugs in project issues
**Feature Requests**: Submit enhancement proposals
**Questions**: Check FAQ section or consult project README

---

## Changelog

### Version 1.0 (November 2024)
- ✅ Initial browser notification system
- ✅ Python CLI tool for cross-platform notifications
- ✅ Training event notifications (start/complete/fail)
- ✅ Milestone tracking (loss thresholds, epoch intervals)
- ✅ System alerts (GPU, backup, evaluation)
- ✅ Hub integration with toggle button
- ✅ Unified dashboard integration
- ✅ Analytics dashboard integration
- ✅ Documentation and examples

---

**Last Updated**: November 2024
**Status**: Production Ready ✅
**Maintainer**: QAI Development Team
