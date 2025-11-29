# Dashboard Enhancements Summary

## New Features Implemented (2025-11-23)

### 1. Cancel Job Mechanism

**Backend (`dashboard/app.py`):**
- Added `/api/cancel_job/<job_name>` POST endpoint
- Reads PID from file-based tracking (`data_out/autotrain/<job_name>.pid`)
- Terminates process tree using OS-appropriate commands:
  - Windows: `taskkill /F /T /PID <pid>`
  - Unix/Linux: `os.killpg(os.getpgid(pid), signal.SIGTERM)`
- Updates job status to `cancelled` with timestamp
- Calculates elapsed duration for cancelled jobs

**Frontend (`dashboard/templates/index.html`):**
- Cancel button appears for `running` and `retry_running` jobs
- Confirmation dialog before cancellation
- Visual feedback: "Cancelling..." → "Cancelled"
- Available in both desktop table and mobile card views

**Training Script (`scripts/autotrain.py`):**
- Writes PID to file after subprocess spawns
- Cleans up PID file automatically on job completion
- PID file location: `data_out/autotrain/<job_name>.pid`

### 2. Validated Type Display

**Data Model:**
- `validated_type` field distinguishes validation phases:
  - `"dry-run"`: Job validated during `--dry-run` mode
  - `"preflight"`: Job validated before actual execution

**UI Display:**
- New "Type" column in job tables (desktop and category sections)
- Displayed as small text in validated jobs
- Shows in mobile card view meta info
- Badge styling: Purple badge for `validated` status

**Use Cases:**
- Distinguish dry-run checks from runtime preflight validation
- Track which jobs passed validation without execution
- Debug configuration issues by validation phase

### 3. Per-Job ETA Estimates

**Algorithm:**
- Calculates runner-specific average durations:
  - Groups completed jobs by `runner` type ("hf" vs "local")
  - Computes mean duration for each runner category
- For running jobs:
  - Parses `start_time` to calculate elapsed seconds
  - Subtracts elapsed from runner-specific average
  - Returns remaining time estimate (rounded to 1 decimal)

**UI Display:**
- New "ETA (s)" column in desktop tables
- Shows estimated remaining seconds for running jobs
- Displayed in mobile card meta info: "ETA: X.Xs"
- Empty for completed/pending jobs

**Benefits:**
- More accurate than global average (accounts for runner differences)
- Real-time progress visibility
- Helps users estimate overall pipeline completion

## Visual Improvements

### Status Badges
- `succeeded` → Green gradient
- `failed` → Red
- `running` → Blue
- `pending` → Gray
- `validated` → Purple (new)
- `cancelled` → Orange (new)

### Button Styling
- **Retry**: Gray border, hover brightness
- **Cancel**: Red border/text, hover fills red background

### Theme System
- Dark/light mode toggle (moon/sun icon in header)
- Persisted via `localStorage`
- CSS variable system for consistent theming
- Responsive design for narrow screens (<640px)

## API Endpoints

| Endpoint | Method | Purpose | Returns |
|----------|--------|---------|---------|
| `/api/training_progress` | GET | Current progress snapshot | Full job status with ETA, validated_type, category |
| `/api/retry_job/<name>` | POST | Retry failed/succeeded job | `{accepted: true, retry_count: N}` |
| `/api/cancel_job/<name>` | POST | Cancel running job | `{cancelled: true, pid: N}` |
| `/api/training_progress_history` | GET | Historical snapshots | Array of progress states |
| `/api/training_progress_history_csv` | GET | Export history as CSV | CSV file download |

## Testing

### Dry-Run Verification
```powershell
python .\scripts\autotrain.py --dry-run
```
- Confirms `validated_type: "dry-run"` in output
- All jobs should show `validated` status

### Dashboard Smoke Test
```powershell
.\venv\Scripts\python.exe -c "from dashboard.app import app; print('OK')"
```
- Verifies imports and no syntax errors

### Live Testing
1. Start dashboard: `python dashboard/app.py` or use SocketIO runner
2. Navigate to http://localhost:5000
3. Click theme toggle (moon icon) to test dark mode
4. Start a training job to see:
   - Per-job ETA in running job row
   - Cancel button availability
   - Validated type display

### Cancel Testing
1. Start a long-running job: `python .\scripts\autotrain.py --job <name>`
2. Click "Cancel" button in dashboard
3. Confirm PID file cleanup: `Test-Path data_out/autotrain/<name>.pid` (should be False)
4. Verify status changes to `cancelled`

## Configuration Example

All job categories propagate from `autotrain.yaml`:
```yaml
jobs:
  - name: phi35_comprehensive_full
    runner: hf
    category: comprehensive  # Shows in collapsible "comprehensive" section
    dataset: datasets/chat/comprehensive
    ...
```

## Backward Compatibility

- Existing status.json files work without modification
- Jobs without `validated_type` display empty cell (no errors)
- Jobs without `category` grouped under "uncategorized"
- PID files are optional (cancel only works when file present)

## Future Enhancements (Potential)

- [ ] Real-time log streaming for running jobs
- [ ] Pause/resume functionality
- [ ] Job queue reordering
- [ ] Email/webhook notifications on completion
- [ ] GPU utilization metrics in dashboard
- [ ] Multi-user authentication and job ownership
- [ ] Historical trend charts (success rate over time)
