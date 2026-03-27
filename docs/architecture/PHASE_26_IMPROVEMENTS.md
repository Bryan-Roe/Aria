# Phase 26: Intelligent Optimization Enhancements

**Status**: In Progress (6 of 6 features underway)  
**Started**: 2025-11-25  
**Focus**: AI-driven intelligence, data profiling, VRAM awareness, anomaly detection, UX enhancements, history tracking

## Overview

Phase 26 transitions from UI polish to **intelligent, data-driven optimization**. The platform now analyzes datasets to recommend optimal hyperparameters, monitors GPU resources to prevent OOM errors, and detects training anomalies in real-time.

---

## ✅ Feature 1: Dataset Profiling System (COMPLETE)

### Implementation

**Backend**: `scripts/dataset_profiler.py` (250+ lines)

- **Tokenization Analysis**: Counts tokens per message using simple whitespace splitting
- **Statistical Metrics**: mean, median, min, max, stdev of token counts
- **Vocabulary Profiling**: Unique token count, role distribution (user/assistant)
- **Turn Analysis**: Average turns per conversation
- **Intelligent Recommendations**: Heuristic engine based on:
  - **Sample count**: <500 (small), <2k (medium), >2k (large)
  - **Token length**: >500 reduces batch size to prevent memory issues
  - **Vocabulary size**: >10k increases LoRA rank for better coverage

**Dashboard Integration**: `dashboard/unified.html`

- **Profile Dataset Button**: Added to tuning wizard modal (blue button between Close and Apply Best)
- **AI Recommendation Row**: Shows `🎯 AI Recommended` profile at top of wizard table when profiling completes
- **Async Profiling**: Calls `/api/profile-dataset` endpoint, stores recommendations in `window.__profilerRecommendations`
- **Fallback to Heuristics**: If profiler unavailable or fails, wizard continues with size-based tiers

**Backend Endpoint**: `dashboard/serve.py`

- **Route**: `GET /api/profile-dataset?dataset=<name>`
- **Process**: Shells out to `dataset_profiler.py --recommend --quiet`, parses JSON output
- **Timeout**: 30-second limit with graceful error handling
- **Response Format**:

  ```json
  {
    "total_samples": 290,
    "valid_samples": 290,
    "tokens": {
      "total": 23883,
      "mean": 41.2,
      "median": 34,
      "min": 1,
      "max": 1323,
      "stdev": 82.8
    },
    "vocabulary": { "size": 6851 },
    "roles": { "user": 290, "assistant": 290 },
    "turns_per_sample": { "mean": 2.0 },
    "recommendations": {
      "batch_size": 4,
      "learning_rate": "2e-4",
      "lora_rank": 8,
      "epochs": 5,
      "reasoning": ["Small dataset (<500): lower batch, higher LR, more epochs"]
    }
  }
  ```

**Profiler CLI**:

```powershell
# Analyze dataset with recommendations
python .\scripts\dataset_profiler.py .\datasets\chat\mixed_chat --recommend

# Save profile to file
python .\scripts\dataset_profiler.py .\datasets\chat\mixed_chat --recommend --output profile.json

# JSON-only output (for scripting)
python .\scripts\dataset_profiler.py .\datasets\chat\mixed_chat --recommend --quiet
```

**Format Support**:

- **JSON Array**: Standard `[{...}, {...}]` format
- **JSONL**: One JSON object per line (fallback for large datasets)

**Example Recommendations** (mixed_chat dataset):

- **Dataset**: 290 samples, 23,883 tokens, 6,851 vocab
- **Batch Size**: 4 (small dataset)
- **Learning Rate**: 2e-4 (higher for fewer samples)
- **LoRA Rank**: 8 (small vocab)
- **Epochs**: 5 (more iterations for small data)
- **Reasoning**: "Small dataset (<500): lower batch, higher LR, more epochs"

### User Workflow

1. **Select Dataset**: Choose dataset from dropdown in unified.html
2. **Open Wizard**: Click `🧪 Tuning Wizard` button or press `Ctrl+Y`
3. **Profile Dataset**: Click `📊 Profile Dataset` button in modal
4. **View Recommendations**: Wizard reloads with `🎯 AI Recommended` row at top
5. **Apply Settings**: Click `Apply` button to populate form fields
6. **Start Training**: Submit form with optimized hyperparameters

### Technical Details

**Profiler Architecture**:

- **Input**: Path to dataset directory or train.json
- **Processing**:
  1. Load JSON/JSONL file
  2. Tokenize all messages (simple whitespace split)
  3. Calculate statistics using `statistics` module
  4. Count vocabulary with `Counter`
  5. Apply heuristic rules based on thresholds
- **Output**: JSON profile with recommendations

**Recommendation Engine** (heuristic rules):

```python
# Small dataset (<500 samples)
batch_size = 4
learning_rate = "2e-4"
lora_rank = 8
epochs = 5

# Medium dataset (500-2000 samples)
batch_size = 8
learning_rate = "1e-4"
lora_rank = 16
epochs = 3

# Large dataset (>2000 samples)
batch_size = 16
learning_rate = "5e-5"
lora_rank = 32
epochs = 3

# Adjust for long messages
if avg_tokens > 500:
    batch_size = max(2, batch_size // 2)

# Adjust for large vocab
if vocab_size > 10000:
    lora_rank *= 2
```

**Frontend Integration**:

- `buildSuggestions(samples)`: Checks for profiler recommendations first, falls back to heuristics
- `buildHeuristicSuggestions(samples)`: Generates size-based tiers (Quick, Balanced, High Quality)
- `profileDatasetForWizard()`: Async function to call API, show loading state, reload wizard
- `window.__profilerRecommendations`: Global storage for recommendations

**Error Handling**:

- **Dataset not found**: Returns error, wizard continues with heuristics
- **Profiler timeout**: 30s limit prevents hanging
- **Parse errors**: Graceful fallback to heuristics
- **Missing script**: Error message in wizard, no crash

### Benefits

1. **Data-Driven Decisions**: Recommendations based on actual dataset characteristics, not guesswork
2. **Reduced Trial-and-Error**: Optimal hyperparameters on first try
3. **Prevent Common Mistakes**: Automatically adjusts batch size for long messages, epochs for small datasets
4. **Transparency**: Reasoning field explains why each recommendation was made
5. **Flexibility**: Users can still override recommendations or use heuristic tiers

### Testing

```powershell
# Test profiler standalone
python .\scripts\dataset_profiler.py .\datasets\chat\mixed_chat --recommend

# Test with multiple datasets
python .\scripts\dataset_profiler.py .\datasets\chat\dolly_general --recommend
python .\scripts\dataset_profiler.py .\datasets\chat\orca_math --recommend

# Test API endpoint (requires dashboard server)
curl "http://localhost:8080/api/profile-dataset?dataset=mixed_chat"
```

---

## 🔄 Feature 2: GPU-Aware Batch Size Calculator (IN PROGRESS)

**Goal**: Prevent out-of-memory (OOM) errors by probing GPU VRAM and recommending safe batch sizes.

**Plan**:

1. **VRAM Probing**:
   - Try `torch.cuda.get_device_properties()` if CUDA available
   - Fallback to `nvidia-smi --query-gpu=memory.free --format=csv`
   - Store total and available VRAM
2. **Memory Estimation**:
   - Calculate model size (parameters × 4 bytes per float32)
   - Add LoRA adapter overhead (rank × 2 × hidden_size × 4)
   - Estimate activation memory (batch_size × seq_len × hidden_size × layers × 4)
3. **Safe Batch Calculation**:
   - Reserve 20% headroom for OS/driver
   - Recommend max batch size that fits in remaining VRAM
4. **Dashboard Integration**:
   - Add "🖥️ Calculate Safe Batch" button to unified.html
   - Show VRAM usage bar and recommended batch size
   - Auto-populate batch_size field

**Expected Output**:

```text
GPU: NVIDIA RTX 4090 (24GB)
Available VRAM: 20.5GB (85% free)
Model: microsoft/Phi-3.5-mini-instruct (3.8B params)
Estimated model memory: 15.2GB (fp32) / 7.6GB (fp16)
LoRA overhead (rank=16): 0.4GB
Safe batch size: 8 (with 20% headroom)
```

---

## 🔄 Feature 3: Training Anomaly Detection (IN PROGRESS)

**Goal**: Monitor training metrics in real-time and alert on issues (spikes, divergence, stagnation).

**Plan**:

1. **Metric Monitoring**:
   - Track loss progression across epochs
   - Detect **spikes** (>20% increase between epochs)
   - Detect **divergence** (loss >10.0 or NaN)
   - Detect **stagnation** (no improvement for 5+ epochs)
2. **Alert System**:
   - Desktop notification on anomaly
   - Visual indicator in analytics.html (red badge, exclamation icon)
   - Optional auto-pause (configurable in settings)
3. **Dashboard Integration**:
   - Add "Anomaly Detection" toggle to analytics.html
   - Show anomaly timeline on chart (markers for spikes/stagnation)
   - Export anomaly report to JSON

**Anomaly Rules**:

- **Spike**: `loss[epoch] > loss[epoch-1] * 1.2`
- **Divergence**: `loss[epoch] > 10.0 or isNaN(loss[epoch])`
- **Stagnation**: `min(loss[epoch-5:epoch]) >= min(loss[epoch-6:epoch-1])`

---

## 🔄 Feature 4: Shared Theme Stylesheet (IN PROGRESS)

**Goal**: Reduce CSS duplication across unified.html, analytics.html, hub.html by extracting common styles.

**Plan**:

1. **Extract Common Styles**:
   - Dark mode variables (colors, backgrounds)
   - Card styles (border, shadow, padding)
   - Button styles (primary, secondary, info, danger)
   - Badge styles (success, warning, error)
   - Modal styles (overlay, container, animations)
2. **Create Shared CSS**:
   - File: `dashboard/shared-theme.css` (~300 lines)
   - Link from all 3 pages: `<link rel="stylesheet" href="shared-theme.css">`
3. **Reduce Duplication**:
   - Before: ~300 lines per page (900 total)
   - After: ~50 lines per page (450 total)
   - Savings: 450 lines (50% reduction)

---

## 🔄 Feature 5: Enhanced Keyboard Navigation (IN PROGRESS)

**Goal**: Add comprehensive keyboard shortcuts and accessibility improvements.

**Plan**:

1. **Shortcuts**:
   - `Tab`: Cycle through form fields
   - `Enter`: Submit form
   - `Escape`: Close modal
   - `Arrow keys`: Navigate preset profiles
   - `Space`: Toggle checkboxes
   - `?`: Show keyboard hints panel
2. **Keyboard Hints Panel**:
   - Persistent panel (bottom-right corner)
   - Toggle with `?` key
   - Shows all available shortcuts with descriptions
   - Responsive (hide on mobile)
3. **Accessibility**:
   - ARIA labels for all form fields
   - Role attributes for custom widgets
   - Focus indicators (blue outline)
   - Screen reader announcements for status changes

---

## 🔄 Feature 6: Training Session History Tracker (IN PROGRESS)

**Goal**: Persist training sessions for comparison and replay.

**Plan**:

1. **Session Storage**:
   - Use localStorage or IndexedDB
   - Store: config, start_time, end_time, final_loss, status
   - Max 100 sessions (LRU eviction)
2. **History Tab**:
   - Add to unified.html (between Training and Analytics tabs)
   - Table with columns: Date, Model, Dataset, Epochs, Final Loss, Status
   - Filters: Date range, Status (completed/failed), Model
   - Sort: Date (desc), Loss (asc), Duration
3. **Session Replay**:
   - "Load Config" button to populate form from history
   - Compare button to diff two sessions
   - Export to CSV/JSON
4. **Comparison View**:
   - Side-by-side config diff
   - Loss progression chart overlay
   - Delta metrics (loss improvement, duration)

---

## Progress Summary

| Feature                    | Status         | Completion |
| -------------------------- | -------------- | ---------- |
| Dataset Profiling          | ✅ Complete    | 100%       |
| GPU-Aware Batch Calculator | 🔄 In Progress | 50%        |
| Anomaly Detection          | 🔄 In Progress | 40%        |
| Shared CSS                 | 🔄 In Progress | 70%        |
| Keyboard Navigation        | 🔄 In Progress | 40%        |
| Training Session History   | 🔄 In Progress | 60%        |

**Overall**: 45% complete (6/6 features touched)

---

## Testing Strategy

### Dataset Profiling (Completed)

- [x] Profiler script runs standalone
- [x] Handles JSON array format
- [x] Handles JSONL format
- [x] Generates recommendations
- [x] Dashboard button added
- [x] API endpoint implemented
- [ ] End-to-end test (dashboard → profile → apply)

### Remaining Features

- [ ] Unit tests for VRAM calculator
- [ ] Anomaly detection with sample data
- [ ] CSS extraction script
- [ ] Keyboard navigation E2E test
- [ ] Session storage persistence test

---

## Dependencies

**Phase 26 Additions**:

- None (uses built-in Python `statistics`, `json`, `subprocess`)

**Existing Stack**:

- Python 3.11
- PyTorch (for VRAM probing in Feature 2)
- Chart.js (for anomaly visualization in Feature 3)
- Browser Notification API (for anomaly alerts)
- localStorage/IndexedDB (for session history)

---

## Key Files Modified

### Phase 26 Feature 1 (Dataset Profiling)

- `../../scripts/dataset_profiler.py` (NEW): 250+ line profiler with CLI
- `../../apps/dashboard/unified.html`: Tuning wizard integration
  - Added `📊 Profile Dataset` button
  - Added `buildSuggestions()` refactor to prioritize AI recommendations
  - Added `buildHeuristicSuggestions()` with existing tier logic
  - Added `profileDatasetForWizard()` async function
- `../../apps/dashboard/serve.py`:
  - Added `/api/profile-dataset` endpoint
  - Shells out to profiler script with subprocess

---

## Next Steps (Priority Order)

1. **Complete GPU-Aware Batch Calculator** (High Priority)
   - Prevents costly OOM crashes
   - Adds immediate value for users with limited VRAM
2. **Implement Anomaly Detection** (High Priority)
   - Prevents wasted training time on diverging runs
   - Early warning system for issues
3. **Extract Shared CSS** (Medium Priority)
   - Code quality improvement
   - Easier theme maintenance
4. **Add Keyboard Navigation** (Medium Priority)
   - Power user feature
   - Accessibility compliance
5. **Build Session History Tracker** (Low Priority)
   - Nice-to-have for advanced users
   - Lower ROI than other features

---

## Lessons Learned

1. **Heuristic Recommendations Work Well**: Simple thresholds (sample count, token length, vocab size) provide surprisingly good hyperparameter suggestions without ML.
2. **JSONL Support Essential**: Many large datasets use one-object-per-line format to avoid loading entire file into memory.
3. **Graceful Degradation**: Wizard falls back to heuristics if profiler fails—no hard dependency on external tools.
4. **User Transparency**: Showing "reasoning" field builds trust in AI recommendations.
5. **Async Profiling**: 30s timeout prevents UI blocking, but may need adjustment for very large datasets (>10k samples).

---

## Documentation

- Dataset Profiler CLI (`scripts/dataset_profiler.py`) - Standalone profiler with `--help` docs
- [Tuning Wizard](../../apps/dashboard/unified.html) - See `showTuningWizard()` function
- [API Endpoints](../../apps/dashboard/serve.py) - `/api/profile-dataset` route
- [Phase 25 Improvements](PHASE_25_IMPROVEMENTS.md) - Previous phase for context

---

**Last Updated**: 2025-11-25  
**Next Review**: After Feature 2 completion
