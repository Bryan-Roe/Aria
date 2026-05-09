# QAI Web UI - Quick Start Guide

Beautiful web interface to control all your QAI operations!

## 🚀 Super Quick Start

```powershell
cd mount
.\start.ps1
```

Then open your browser to: **http://localhost:8000**

## 📱 Features

### 📊 Dashboard
- Real-time system status
- Quick action buttons
- Recent activity feed
- Health monitoring

### ⚛️ Quantum AI Tab
- Train quantum classifiers with custom parameters
- View available backends (Qiskit Aer, Lightning, Azure)
- Monitor training results
- Run AutoRun orchestrator jobs

### 💬 Chat Tab
- Interactive chat interface
- Multiple provider support:
  - 🆓 Local (Free, offline)
  - ☁️ Azure OpenAI
  - 🤖 OpenAI
  - 🎯 LoRA Adapter (if trained)
- Auto-detect best available provider
- Conversation history

### 🎓 Training Tab
- Train LoRA adapters on custom datasets
- Run AutoTrain orchestrator jobs
- Monitor training status
- View all available datasets (quantum/chat/vision)
- Check LoRA adapter status

### 📝 Logs Tab
- Real-time system logs
- Color-coded by severity (info/warning/error/success)
- Clear and refresh controls

## 🎨 UI Features

- **Modern Design**: Beautiful gradient interface with smooth animations
- **Responsive**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Auto-refresh status every 30 seconds
- **Easy Navigation**: Tab-based interface
- **Visual Feedback**: Color-coded status indicators

## 🔧 How to Use

### Starting the Service

**Option 1: PowerShell Script**
```powershell
cd mount
.\start.ps1
```

**Option 2: Manual Start**
```powershell
cd mount
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

**Option 3: Production Mode**
```powershell
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Training a Quantum Classifier

1. Go to **⚛️ Quantum AI** tab
2. Select a dataset (heart, ionosphere, sonar, etc.)
3. Configure parameters:
   - Number of qubits (2-20)
   - Number of layers (1-10)
   - Training epochs
   - Backend (Qiskit Aer recommended for local)
4. Click **🚀 Start Training**
5. Monitor progress in the logs

### Using Chat

1. Go to **💬 Chat** tab
2. Select provider (or use auto-detect)
3. Type your message
4. Press **Send** or hit Enter
5. See response instantly

Provider recommendations:
- **Local**: Always available, free, offline
- **Azure/OpenAI**: Best quality, requires API keys
- **LoRA**: Use your trained model

### Training a LoRA Adapter

1. Go to **🎓 Training** tab
2. Select a chat dataset
3. Configure:
   - Max training samples (64 for quick test)
   - Max eval samples (16 for quick test)
   - Epochs (1 for testing)
4. Click **🚀 Start Training**
5. Monitor in logs tab

### Running Orchestrator Jobs

**Quantum AutoRun:**
1. Go to **⚛️ Quantum AI** tab
2. Scroll to "Quantum AutoRun Jobs" section
3. Select a predefined job
4. Run directly or do a dry-run first

**AutoTrain:**
1. Go to **🎓 Training** tab
2. Select an AutoTrain job
3. Click **Dry Run** to validate
4. Click **Run Job** to execute

## 🎯 Quick Examples

### Example 1: Quick Quantum Test
1. Dashboard → Click "⚛️ Train Quantum Model"
2. Select "heart" dataset
3. Keep default parameters
4. Start training
5. Check results in Dashboard after completion

### Example 2: Free Local Chat
1. Dashboard → Click "💬 Start Chat"
2. Provider is already on "Local" (free!)
3. Ask: "What is quantum computing?"
4. Get instant response

### Example 3: Train a Quick LoRA
1. Dashboard → Click "🎓 Train LoRA"
2. Select "dolly" dataset
3. Set samples to 64 (fast test)
4. Start training
5. Use trained adapter in Chat tab

## 🔍 Monitoring

### Dashboard Indicators

**Status Dot Colors:**
- 🟢 Green = Online and healthy
- 🟡 Yellow = Checking...
- 🔴 Red = Offline or error

**System Status:**
- ✓ Green checkmark = Enabled and working
- ✗ Red X = Disabled or error

### Logs Tab

Watch real-time activity:
- 🟢 **Info**: Normal operations
- 🟡 **Warning**: Attention needed
- 🔴 **Error**: Something failed
- 🔵 **Success**: Operation completed

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
service:
  host: 0.0.0.0  # Change to 127.0.0.1 for localhost only
  port: 8000      # Change port if needed
  debug: true     # Set false for production

api:
  cors_enabled: true
  cors_origins:
    - http://localhost:3000
    - http://localhost:7071
```

## 🐛 Troubleshooting

### "Service Offline" Status
**Solution:** Check if the backend is running
```powershell
cd mount
python app.py
```

### CORS Errors
**Solution:** Add your URL to `config.yaml` under `cors_origins`

### Can't Load Data
**Solution:** Make sure all paths in `config.yaml` point to correct locations

### Training Errors
**Solution:** Check the Logs tab for detailed error messages

### Chat Not Working
**Solution:**
- Local provider always works (no setup needed)
- For Azure/OpenAI: Set environment variables
- For LoRA: Train an adapter first

## 🚀 Advanced Usage

### Custom API Base URL

If running the backend on a different host/port, edit `app.js`:

```javascript
const API_BASE = 'http://your-server:8000';
```

### Running on Network

To access from other devices:

```powershell
# In config.yaml, set:
service:
  host: 0.0.0.0  # Listen on all interfaces

# Then access from other devices:
# http://YOUR-IP:8000
```

### Production Deployment

```powershell
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn app:app --workers 4 --bind 0.0.0.0:8000
```

## 📊 Performance Tips

1. **Quantum Training**: Start with small epochs (10) for testing
2. **LoRA Training**: Use 64 samples for quick validation
3. **Chat**: Local provider is instant, cloud providers have latency
4. **Refresh Rate**: Increase interval in app.js if using on slow connection

## 🎨 Customization

### Changing Colors

Edit `static/styles.css` variables:

```css
:root {
    --primary: #667eea;      /* Main brand color */
    --secondary: #48bb78;    /* Secondary color */
    --success: #48bb78;      /* Success green */
    --danger: #f56565;       /* Error red */
}
```

### Adding Custom Sections

1. Add HTML section in `static/index.html`
2. Add styles in `static/styles.css`
3. Add JavaScript logic in `static/app.js`
4. Connect to backend API endpoints

## 🔐 Security Notes

**Development Mode:**
- CORS is wide open
- Debug mode enabled
- No authentication

**Production Recommendations:**
- Set `debug: false` in config
- Restrict CORS origins
- Add authentication middleware
- Use HTTPS
- Set secure cookie flags

## 📖 API Documentation

While the UI is running, you can also access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide full API documentation for programmatic access.

## 💡 Tips & Tricks

1. **Use Keyboard Shortcuts**: Enter to send chat messages
2. **Quick Navigation**: Click dashboard quick actions to jump to tabs
3. **Monitor Everything**: Keep Logs tab open in another window
4. **Save Conversations**: Chat history auto-saves to JSONL files
5. **Dry Run First**: Always test orchestrator jobs with dry-run

## 🤝 Need Help?

Check the main README.md for:
- Detailed system architecture
- Backend API documentation
- Integration module details
- Configuration options
- Troubleshooting guides

## 🎉 You're Ready!

Open http://localhost:8000 and start exploring your AI control center!

---

**Made with ❤️ for the QAI Workspace**
