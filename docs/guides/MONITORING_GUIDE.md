# Autonomous Training Monitoring Guide

Complete guide to monitoring and analyzing your autonomous AI training system.

## Quick Start

### 1. Real-Time Dashboard (Recommended)
```powershell
# Live monitoring with auto-refresh every 5 seconds
python .\scripts\monitor_autonomous_training.py
```

### 2. Quick Status Check
```powershell
# One-time status display
python .\scripts\monitor_autonomous_training.py --once

# Or compact summary
python .\scripts\monitor_autonomous_training.py --summary
```

### 3. Analytics Report
```powershell
# Generate detailed analytics
python .\scripts\training_analytics.py --report

# View performance chart
python .\scripts\training_analytics.py --chart

# Export HTML report
python .\scripts\training_analytics.py --html data_out/report.html
```

## Monitoring Tools

### Real-Time Dashboard (`monitor_autonomous_training.py`)

**Features:**
- 🎯 Live status updates (refreshes every 5 seconds)
- 📊 Performance metrics and trends
- 📝 Recent log activity
- ⚠️ Automatic alerts and warnings
- 🎨 Color-coded output for easy reading

**Usage:**

```powershell
# Continuous monitoring (press Ctrl+C to exit)
python .\scripts\monitor_autonomous_training.py

# One-time display
python .\scripts\monitor_autonomous_training.py --once

# Compact summary
python .\scripts\monitor_autonomous_training.py --summary

# Custom refresh interval (10 seconds)
python .\scripts\monitor_autonomous_training.py --refresh 10

# Export metrics to CSV
python .\scripts\monitor_autonomous_training.py --export metrics.csv
```

**Dashboard Sections:**

1. **System Overview**
   - Current phase (training, optimization, etc.)
   - Cycles completed
   - Best accuracy achieved
   - Last cycle duration

2. **Dataset Inventory**
   - Datasets by category
   - Total available datasets
   - Distribution breakdown

3. **Performance Metrics**
   - Last 5 cycles summary
   - Accuracy trends
   - Model counts
   - Improvement/decline indicators

4. **Task Queue**
   - Active tasks
   - Completed tasks
   - Task history

5. **Recent Activity**
   - Last 10 log entries
   - Color-coded by severity
   - Error/warning highlighting

6. **Alerts**
   - Performance degradation warnings
   - Low dataset count alerts
   - Error notifications
   - System status issues

### Analytics Tool (`training_analytics.py`)

**Features:**
- 📈 Performance trend analysis
- 🔮 Accuracy predictions
- 💡 Optimization insights
- 📊 ASCII charts
- 📄 HTML report generation

**Usage:**

```powershell
# Text report with recommendations
python .\scripts\training_analytics.py --report

# ASCII chart of performance
python .\scripts\training_analytics.py --chart

# Chart specific metric
python .\scripts\training_analytics.py --chart --metric max_accuracy

# Generate HTML report
python .\scripts\training_analytics.py --html report.html
```

**Insights Provided:**

1. **Performance Trend**
   - Initial vs current accuracy
   - Total improvement
   - Improvement rate per cycle

2. **Predictions**
   - Cycles needed to reach 80%, 85%, 90%, 95%
   - Based on current improvement rate
   - Helps plan training duration

3. **Optimization Insights**
   - Optimal epoch count
   - Plateau detection
   - Convergence status

4. **Model Quality Breakdown**
   - Exceptional models (≥95%)
   - Excellent models (85-95%)
   - Distribution analysis

5. **Recommendations**
   - Action items based on performance
   - Training strategy suggestions
   - Deployment readiness

## Monitoring Workflows

### 1. Active Development Monitoring

Run dashboard in one terminal while orchestrator runs in another:

```powershell
# Terminal 1: Start orchestrator
python .\scripts\autonomous_training_orchestrator.py

# Terminal 2: Monitor in real-time
python .\scripts\monitor_autonomous_training.py
```

### 2. Scheduled Status Checks

Check status periodically without continuous monitoring:

```powershell
# Check every 10 minutes (Windows Task Scheduler or loop)
while ($true) {
    python .\scripts\monitor_autonomous_training.py --summary
    Start-Sleep -Seconds 600
}
```

### 3. Performance Analysis Workflow

After several training cycles:

```powershell
# 1. Generate text report
python .\scripts\training_analytics.py --report > analysis.txt

# 2. View performance chart
python .\scripts\training_analytics.py --chart

# 3. Export detailed HTML report
python .\scripts\training_analytics.py --html report.html

# 4. Open report in browser
start report.html
```

### 4. Data Export for External Analysis

```powershell
# Export metrics to CSV
python .\scripts\monitor_autonomous_training.py --export metrics.csv

# Import in Excel, pandas, or other tools
# File includes: timestamp, cycle, epochs, accuracies, model counts
```

## Understanding the Dashboard

### Status Indicators

**Phase Colors:**
- 🔵 Blue: Data discovery, collection
- 🟡 Yellow: Training in progress
- 🟢 Green: Deployment, success
- 🔴 Red: Error, stopped

**Accuracy Color Coding:**
- 🟢 Green: ≥90% (Excellent)
- 🔵 Cyan: 75-90% (Good)
- 🟡 Yellow: 60-75% (Fair)
- 🔴 Red: <60% (Needs work)

**Trend Indicators:**
- ↑ Green: Improving (>1% gain)
- → Yellow: Stable/plateau
- ↓ Red: Declining (>1% loss)

### Key Metrics Explained

**Cycles Completed:**
- Number of full training cycles run
- Each cycle = discovery → collection → training → analysis

**Best Accuracy:**
- Highest mean accuracy achieved across all cycles
- Target: 85-95% for production

**Mean Accuracy:**
- Average accuracy across all trained datasets
- More realistic than max accuracy

**Max Accuracy:**
- Best single dataset performance
- Shows model potential

**Exceptional Models:**
- Models achieving ≥95% accuracy
- Ready for production deployment

**Successful Count:**
- Number of datasets successfully trained
- Out of total available

**Improvement Rate:**
- Average accuracy gain per cycle
- Helps predict future performance

## Alerts & Warnings

### Performance Degradation
**Trigger:** >5% accuracy drop between cycles

**Possible Causes:**
- Dataset quality issues
- Overfitting from too many epochs
- Random initialization variance
- System resource constraints

**Actions:**
1. Check recent logs for errors
2. Verify dataset integrity
3. Consider reducing epochs temporarily
4. Review hyperparameter settings

### Low Dataset Count
**Trigger:** <100 datasets available

**Possible Causes:**
- Initial setup incomplete
- Download failures
- Disk space issues

**Actions:**
1. Check `datasets/` directories
2. Run data collection manually
3. Verify network connectivity
4. Check disk space

### Plateau Detected
**Trigger:** <0.01% variance in last 3 cycles

**Possible Causes:**
- Model has converged
- Need more epochs
- Learning rate too low
- Architecture limitations

**Actions:**
1. Increase epoch count in config
2. Enable hyperparameter tuning
3. Try architecture evolution
4. Consider ensemble methods

### Training Errors
**Trigger:** Failed training jobs

**Possible Causes:**
- Categorical data not encoded
- Out of memory
- Corrupt datasets
- Software bugs

**Actions:**
1. Review error logs
2. Check failed dataset names
3. Preprocess problematic datasets
4. Reduce batch size or workers

## Advanced Monitoring

### Custom Metrics Export

```powershell
# Export and analyze with Python
python .\scripts\monitor_autonomous_training.py --export metrics.csv

# Load in Python/pandas
import pandas as pd
df = pd.read_csv('metrics.csv')
print(df.describe())

# Plot with matplotlib
df.plot(x='cycle', y='mean_accuracy')
```

### Log Analysis

```powershell
# View full logs
Get-Content data_out\autonomous_training.log

# Filter for errors
Get-Content data_out\autonomous_training.log | Select-String "ERROR"

# Count warnings
(Get-Content data_out\autonomous_training.log | Select-String "WARNING").Count

# Tail logs in real-time
Get-Content data_out\autonomous_training.log -Wait -Tail 20
```

### Status File Inspection

```powershell
# View raw status JSON
Get-Content data_out\autonomous_training_status.json | ConvertFrom-Json

# Extract specific field
(Get-Content data_out\autonomous_training_status.json | ConvertFrom-Json).best_accuracy

# Performance history
(Get-Content data_out\autonomous_training_status.json | ConvertFrom-Json).performance_history | ConvertTo-Json
```

### Integration with Azure Monitor

```powershell
# Send metrics to Azure Log Analytics (example)
$status = Get-Content data_out\autonomous_training_status.json | ConvertFrom-Json
$metrics = @{
    Timestamp = Get-Date
    BestAccuracy = $status.best_accuracy
    CyclesCompleted = $status.cycles_completed
    Phase = $status.current_phase
}

# Post to Azure Monitor REST API
# (Configure workspace ID and shared key)
# Invoke-RestMethod -Uri $uri -Method Post -Body ($metrics | ConvertTo-Json)
```

## Monitoring Best Practices

### 1. Always Monitor During Initial Cycles
- Watch first 3-5 cycles closely
- Verify data collection works
- Confirm training completes successfully
- Check accuracy improvements

### 2. Set Up Alerting
- Configure email/Slack notifications in config
- Monitor disk space usage
- Watch for repeated errors
- Track memory usage

### 3. Regular Analysis
- Generate analytics report weekly
- Export metrics for trend analysis
- Review optimization recommendations
- Adjust configuration based on insights

### 4. Performance Baselines
- Record initial accuracy
- Set target accuracy goals
- Track improvement rate
- Compare against baselines

### 5. Resource Monitoring
- Monitor CPU usage (should be 80-100% with 20 workers)
- Check memory usage (2-4 GB typical)
- Watch disk I/O
- Ensure adequate disk space (>50 GB free)

## Troubleshooting

### Dashboard Shows "Status file not found"
```powershell
# Check if orchestrator is running
Get-Process python | Where-Object {$_.CommandLine -like "*autonomous_training*"}

# Start orchestrator if not running
python .\scripts\autonomous_training_orchestrator.py --once
```

### No Performance Data
```powershell
# Verify status file exists
Test-Path data_out\autonomous_training_status.json

# Check if orchestrator has completed a cycle
python .\scripts\autonomous_training_orchestrator.py --status
```

### Charts Not Displaying Properly
- Ensure terminal supports ANSI colors
- Use Windows Terminal or PowerShell 7+
- Try `--once` mode for static display

### Metrics Export Fails
```powershell
# Check data_out directory exists
New-Item -ItemType Directory -Force -Path data_out

# Verify write permissions
Test-Path data_out -PathType Container
```

## Example Monitoring Session

```powershell
# 1. Start orchestrator
python .\scripts\autonomous_training_orchestrator.py

# Wait for first cycle to complete (~5-10 minutes)

# 2. In new terminal, monitor in real-time
python .\scripts\monitor_autonomous_training.py

# 3. After 3-5 cycles, generate analytics
python .\scripts\training_analytics.py --report

# 4. Export data for further analysis
python .\scripts\monitor_autonomous_training.py --export metrics.csv
python .\scripts\training_analytics.py --html report.html

# 5. Open HTML report
start data_out\report.html
```

## Integration Examples

### PowerShell Dashboard Script
```powershell
# monitor.ps1 - Custom monitoring script
while ($true) {
    Clear-Host
    Write-Host "=== AUTONOMOUS TRAINING MONITOR ===" -ForegroundColor Cyan
    Write-Host ""
    
    python .\scripts\monitor_autonomous_training.py --summary
    
    Write-Host "`nPress Ctrl+C to exit"
    Start-Sleep -Seconds 30
}
```

### Scheduled Report Generation
```powershell
# Create scheduled task to generate reports daily
$action = New-ScheduledTaskAction -Execute "python" -Argument ".\scripts\training_analytics.py --html daily_report.html"
$trigger = New-ScheduledTaskTrigger -Daily -At 6am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "AutoTrainingReport"
```

### Slack Notification (Future Enhancement)
```python
# In autonomous_training_orchestrator.py
# Add webhook notification on cycle completion
import requests

def send_slack_notification(status):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    message = {
        "text": f"Training Cycle Complete: {status['best_accuracy']:.2%} accuracy"
    }
    requests.post(webhook_url, json=message)
```

## FAQ

**Q: How often should I check the monitor?**
A: During initial setup, check every cycle. Once stable, periodic checks (hourly/daily) are sufficient.

**Q: What's a good target accuracy?**
A: 85-90% is excellent for most datasets. 90%+ is production-ready.

**Q: How long until I see results?**
A: First cycle completes in 5-10 minutes. Significant improvements appear after 3-5 cycles.

**Q: Can I run monitoring on a different machine?**
A: Yes, if you share the `data_out/` directory or copy status files.

**Q: How much history is kept?**
A: All history is preserved in status file. Export regularly for long-term analysis.

## Next Steps

1. **Set up monitoring**: Start with real-time dashboard
2. **Establish baselines**: Record initial performance
3. **Set goals**: Define target accuracy and timeline
4. **Regular reviews**: Generate analytics reports weekly
5. **Optimize**: Adjust configuration based on insights
6. **Automate**: Set up scheduled exports and reports

For more information, see:
- `AUTONOMOUS_TRAINING_README.md` - Full orchestrator guide
- `autonomous_training.yaml` - Configuration options
- Logs: `data_out/autonomous_training.log`
