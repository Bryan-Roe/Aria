# QAI Dashboard Suite - Complete Feature Guide

## 🎯 Overview

Three progressive dashboard interfaces for monitoring and managing AI training:

1. **index.html** - Basic real-time monitoring
2. **enhanced.html** - Full-featured with job controls
3. **advanced.html** - ⭐ Professional-grade with GPU monitoring & charts

## 🚀 Quick Access

```
Basic:    http://localhost:8000/index.html
Enhanced: http://localhost:8000/enhanced.html
Advanced: http://localhost:8000/advanced.html  ⭐ RECOMMENDED
```

---

## 🎮 Advanced Dashboard Features

### **Real-Time GPU Monitoring**
✅ **Live Metrics** (updates every 5 seconds):
- GPU utilization percentage with visual progress bar
- VRAM usage (current / total) 
- Core temperature with color-coded warnings:
  - 🟢 Green < 70°C (optimal)
  - 🟡 Yellow 70-80°C (warm)
  - 🔴 Red > 80°C (hot - warning shown)
- Power draw vs power limit
- GPU model name (e.g., RTX 4050 Laptop GPU)

✅ **Temperature Alerts**: Automatic warning when GPU > 85°C

✅ **Multiple GPU Support**: Displays all available GPUs

### **System Resource Monitoring**
✅ **CPU Metrics**:
- Real-time usage percentage
- Core count display
- Clock frequency

✅ **Memory Metrics**:
- RAM usage (GB used / total GB)
- Usage percentage with progress bar
- Automatic color coding for high usage

✅ **Disk Metrics**:
- Total storage capacity
- Used space tracking

### **Interactive Charts** (Chart.js)

#### 📈 **Perplexity Progress Chart**
- Side-by-side comparison: Pre-training vs Post-training
- Bar chart showing improvement for each model
- Color-coded: Gray (before) → Purple (after)
- Hover tooltips with exact values

#### ⏱️ **Training Duration Chart**
- Line chart showing time per job
- Smooth curve with gradient fill
- Identifies bottlenecks and optimization opportunities

### **Smart Notifications**
✅ **Browser Notifications**: Alerts when jobs complete (with permission)
✅ **In-App Toasts**: Success/error messages slide in from top-right
✅ **Sound Alerts**: (Optional) Audio cues for completion
✅ **Visual Indicators**: Pulsing green dot = dashboard live

### **Export & Reporting**
✅ **One-Click Export**: Download complete training history as JSON
✅ **Report Contents**:
- All job metrics (pre/post loss & perplexity)
- Duration data
- Training timeline
- Model configurations
✅ **Filename**: Auto-dated `training-report-2025-11-25.json`

### **Job List Views**

#### 🏃 **Running Jobs Panel**
- Live status with pulsing animation
- Current job name
- Real-time metrics

#### ✅ **Completed Jobs Panel**
- Last 10 successful jobs
- Final perplexity scores
- Click for full details

#### ⏳ **Queued Jobs Panel**
- Pending jobs in order
- Estimated start time
- Job configuration preview

### **Quick Stats Dashboard**
Six key metrics at a glance:
1. ✅ Completed jobs count
2. 🏃 Currently running jobs
3. ⏳ Queued jobs waiting
4. ❌ Failed jobs count
5. ⚡ Average training time
6. 🎯 Best perplexity score achieved

---

## 📡 API Endpoints Reference

### Core Endpoints
```
GET  /status                    → Training status JSON
GET  /api/datasets              → List all datasets with sample counts
GET  /api/models                → List trained model adapters
GET  /api/configs               → List training YAML configurations
```

### Job Management
```
GET  /api/job/<name>            → Detailed job info + output files
GET  /api/logs/<name>           → Last 500 lines of training logs
POST /api/start-training        → Launch new training job
```

### System Monitoring
```
GET  /api/gpu                   → Real-time GPU stats (nvidia-smi)
GET  /api/gpu-processes         → List processes using GPU
GET  /api/system                → CPU, RAM, disk usage
GET  /api/history               → Training history for charts
```

### Example API Calls
```powershell
# Get GPU status
curl http://localhost:8000/api/gpu | jq

# View job logs
curl http://localhost:8000/api/logs/phi35_mega_synthetic_full

# Export training history
Invoke-WebRequest -Uri http://localhost:8000/api/history -OutFile history.json
```

---

## 🎨 Dashboard Comparison

| Feature | Basic | Enhanced | Advanced |
|---------|-------|----------|----------|
| Real-time status | ✅ | ✅ | ✅ |
| Job metrics | ✅ | ✅ | ✅ |
| GPU monitoring | ❌ | ❌ | ✅ |
| System resources | ❌ | ❌ | ✅ |
| Interactive charts | ❌ | ❌ | ✅ |
| Job controls | ❌ | ✅ | ✅ |
| Model comparison | ❌ | ✅ | ✅ |
| Log viewer | ❌ | ✅ | ✅ |
| Dataset browser | ❌ | ✅ | ✅ |
| Notifications | ❌ | ❌ | ✅ |
| Export reports | ❌ | ❌ | ✅ |
| Auto-refresh | 10s | 10s | 5s |

---

## 🔧 Usage Scenarios

### Monitoring Long Training Sessions
1. Open **advanced.html**
2. Enable **Auto-refresh (5s)** checkbox
3. Leave browser tab open
4. Dashboard will:
   - Update metrics every 5 seconds
   - Show browser notification when jobs complete
   - Alert if GPU temperature gets too high
   - Track progress with live charts

### Comparing Model Performance
1. Navigate to **Enhanced** dashboard
2. Go to **🤖 Models** tab
3. See leaderboard ranked by perplexity
4. Best model has **👑** crown badge
5. Click **Deploy** for production use

### Starting New Training
1. Go to **Enhanced** → **⚡ New Training** tab
2. Select:
   - Config: `autotrain_extended_marathon.yaml`
   - Dataset: `mega_synthetic` (1,260 samples)
   - Model: `Phi-3.5-mini-instruct`
3. Set epochs (3) and learning rate (0.0002)
4. Click **🚀 Start Training**
5. Job appears in **Running Jobs** immediately

### Troubleshooting Failed Jobs
1. Open **Enhanced** → **🏃 Jobs** tab
2. Find failed job (red border)
3. Click to expand details
4. Click **📜 View Logs**
5. Last 500 lines show error details
6. Fix issue and relaunch

---

## 🎯 Performance Tips

### Optimal Settings
- **Auto-refresh**: 5-10 seconds (balance between freshness & load)
- **Browser**: Chrome/Edge for best Chart.js performance
- **Multiple tabs**: OK, but increases server load

### GPU Temperature Management
- **Normal**: < 70°C
- **Acceptable**: 70-80°C
- **Warning**: 80-85°C (dashboard shows yellow)
- **Critical**: > 85°C (dashboard shows red alert)
- **Action**: If consistently > 85°C:
  - Check laptop cooling
  - Reduce batch size
  - Lower max concurrent jobs

### Memory Optimization
- Running jobs use ~6GB VRAM
- Keep system RAM usage < 80%
- Close unnecessary applications during training
- Dashboard itself uses ~50MB RAM

---

## 📊 Live Data Examples

### GPU Status (from your system)
```json
{
  "name": "NVIDIA GeForce RTX 4050 Laptop GPU",
  "temperature": 48°C,
  "utilization": 0%,
  "memory_used": 0MB / 6141MB,
  "power_draw": 2W
}
```

### Completed Job Metrics
```json
{
  "name": "phi35_mega_synthetic_full",
  "duration": "4m 5s",
  "pre_perplexity": 16.59,
  "post_perplexity": 16.16,
  "improvement": "2.6%",
  "status": "succeeded"
}
```

---

## 🔮 Keyboard Shortcuts

- **R** - Refresh all data
- **E** - Export report
- **Space** - Toggle auto-refresh
- **Esc** - Close notifications

---

## 🐛 Troubleshooting

### Dashboard won't load
```powershell
# Check if server is running
Get-Process python | Where-Object {$_.CommandLine -like '*serve.py*'}

# Restart server
python .\dashboard\serve.py
```

### GPU not showing
- **Issue**: nvidia-smi not found
- **Fix**: Ensure NVIDIA drivers installed
- **Test**: `nvidia-smi` in PowerShell

### Charts not rendering
- **Issue**: Chart.js CDN blocked
- **Fix**: Check internet connection or download Chart.js locally
- **Fallback**: Use Enhanced dashboard (no charts required)

### Stale data
- **Issue**: status.json not updating
- **Fix**: Check if training process is running
- **Verify**: `cat data_out\autotrain\status.json`

---

## 🎉 Success Metrics

Your current training status:
- ✅ **2 jobs completed** successfully
- 🏃 **1 job running** (phi35_comprehensive_marathon)
- ⏳ **10 jobs queued** (3-4 hours remaining)
- 🎯 **Best perplexity**: 16.16 (phi35_mega_synthetic_full)
- 💪 **Improvement**: Up to 46.7% (qwen25_mega_synthetic_full)

**Dashboard is monitoring all of this in real-time!** 🚀

---

## 📝 Next Steps

1. ✅ Open advanced dashboard: http://localhost:8000/advanced.html
2. ✅ Enable auto-refresh for hands-free monitoring
3. ✅ Watch GPU utilization during training
4. ✅ Get notified when marathon completes
5. ✅ Compare models and deploy the winner
6. ✅ Export final report for documentation

Enjoy your professional AI training dashboard! 🎊
