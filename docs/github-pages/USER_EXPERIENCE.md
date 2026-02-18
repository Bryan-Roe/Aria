# GitHub Pages User Experience Guide

## What Users See When They Visit Your Site

### 🖥️ On GitHub Pages (https://username.github.io/repo-name/)

#### Main Page Load
```
┌─────────────────────────────────────────────────────────┐
│                         Aria                             │
│              Quantum AI System - Web Hub                 │
│                                                          │
│  🎯 Aria Interfaces    ⚛️ Quantum    📊 Dashboards       │
│  🔌 API & Services                                       │
└─────────────────────────────────────────────────────────┘
```

#### When They Click "Check Local Status"
```
[Alert Box]
┌────────────────────────────────────────────────────────┐
│ "API status checking is only available in your local  │
│  development environment.                             │
│                                                       │
│  To check API status locally:                        │
│  curl http://localhost:7071/api/ai/status | jq"     │
│                                                       │
│                                    [OK]              │
└────────────────────────────────────────────────────────┘
```

#### When They Click "Aria Server (8080)"
```
[Alert Box]
┌────────────────────────────────────────────────────────┐
│ "Aria Server" is only available in your local         │
│ development environment.                              │
│                                                       │
│ To run this locally:                                 │
│ cd aria_web && python server.py                      │
│                                                       │
│                                    [OK]              │
└────────────────────────────────────────────────────────┘
```

#### Footer Display
```
┌─────────────────────────────────────────────────────────┐
│ [Documentation] [Quick Start] [Features] [README]       │
│                                                         │
│ © 2026 Aria Quantum AI System. All rights reserved.    │
│ Last updated: January 24, 2026                         │
│ Environment: GitHub Pages (Deployment)                │
└─────────────────────────────────────────────────────────┘
```

### 💻 On Local Development (http://localhost:8000/)

#### When They Click "Check Local Status"
```
[Alert Box with API Status]
┌────────────────────────────────────────────────────────┐
│ ✅ API is running!                                     │
│                                                       │
│ Active Provider: azure                              │
│                                                       │
│ Check full status at:                               │
│ http://localhost:7071/api/ai/status                 │
│                                        [OK]         │
└────────────────────────────────────────────────────────┘

🔗 Opens: http://localhost:7071/api/ai/status
   Shows: Full JSON status with provider, env vars, etc.
```

#### When They Click "Aria Server (8080)"
```
🔗 Opens: http://localhost:8080
   Shows: Live Aria server with interactive 3D character
```

#### Footer Display
```
┌─────────────────────────────────────────────────────────┐
│ [Documentation] [Quick Start] [Features] [README]       │
│                                                         │
│ © 2026 Aria Quantum AI System. All rights reserved.    │
│ Last updated: January 24, 2026                         │
│ Environment: Local Development                        │
└─────────────────────────────────────────────────────────┘
```

## User Scenarios

### Scenario 1: Business User on GitHub Pages

**Goal:** See what the Aria system can do

**Experience:**
1. ✅ Arrives at GitHub Pages site
2. ✅ Sees beautiful web hub with all interface options
3. ✅ Clicks "Open Aria" → Sees Aria interface (works!)
4. ✅ Clicks "Open Chat" → Sees chat interface (works!)
5. ✅ Clicks "Check Local Status" → Gets clear instructions
6. ✅ Reads "to see full features, set up local environment"

**Outcome:** User understands the system and knows how to get started

### Scenario 2: Developer on Local Machine

**Goal:** Test the system locally

**Experience:**
1. ✅ Clones repository
2. ✅ Runs: `python -m http.server`
3. ✅ Visits: `http://localhost:8000/web-hub.html`
4. ✅ Clicks "Check Local Status" → API is checked and status shown
5. ✅ Clicks "Aria Server" → Opens live Aria server
6. ✅ All features work perfectly

**Outcome:** Developer can test all functionality

### Scenario 3: CI/CD Pipeline

**Goal:** Deploy to production

**Experience:**
1. ✅ GitHub Actions automatically builds and deploys
2. ✅ Site goes live on GitHub Pages
3. ✅ All navigation links work
4. ✅ No manual configuration needed
5. ✅ Users can access from any device

**Outcome:** Zero-config deployment to production

## Component Behavior Matrix

| Component | GitHub Pages | Local Dev | Web Server |
|-----------|--------------|-----------|-----------|
| Web Hub | ✅ Works | ✅ Works | ✅ Works |
| Navigation Links | ✅ Works | ✅ Works | ✅ Works |
| Aria Interface | ✅ Works | ✅ Works | ✅ Works |
| Chat Interface | ✅ Works | ✅ Works | ✅ Works |
| Quantum Pages | ✅ Works | ✅ Works | ✅ Works |
| Dashboard | ✅ Works | ✅ Works | ✅ Works |
| API Status Check | ⚠️ Info | ✅ Works | ⚠️ Depends |
| Aria Server Link | ⚠️ Info | ✅ Works | ⚠️ Depends |
| Functions Link | ⚠️ Info | ✅ Works | ⚠️ Depends |
| Dashboard Server Link | ⚠️ Info | ✅ Works | ⚠️ Depends |
| Docs Links | ⚠️ Info | ✅ Works | ⚠️ Depends |

## Message Examples

### API Status Check Response

**GitHub Pages:**
```
"API status checking is only available in your local 
development environment.

To check API status locally:
curl http://localhost:7071/api/ai/status | jq"
```

**Local Development (API Running):**
```
"✅ API is running!

Active Provider: azure

Check full status at:
http://localhost:7071/api/ai/status"
```

**Local Development (API Not Running):**
```
"⚠️ API is not running at http://localhost:7071/api/ai/status

Start it with: func host start"
```

## Navigation Flow Diagrams

### User on GitHub Pages

```
GitHub Pages
    ↓
Web Hub (works) ←── CSS & JS load ✅
    ├─→ Aria Interface (works) ✅
    ├─→ Chat Interface (works) ✅
    ├─→ Quantum Pages (work) ✅
    ├─→ Dashboards (work) ✅
    ├─→ Check API (shows instructions) ℹ️
    ├─→ Services (show instructions) ℹ️
    └─→ Docs (show locations) ℹ️
```

### User on Local Development

```
Localhost with Services Running
    ↓
Web Hub (works) ←── CSS & JS load ✅
    ├─→ Aria Interface (works) ✅
    ├─→ Chat Interface (works) ✅
    ├─→ Quantum Pages (work) ✅
    ├─→ Dashboards (work) ✅
    ├─→ Check API (connects & shows status) ✅
    ├─→ Aria Server (opens http://localhost:8080) ✅
    ├─→ Functions (opens http://localhost:7071) ✅
    ├─→ Dashboard Server (opens http://localhost:8765) ✅
    └─→ Docs (opens markdown files) ✅
```

## Response Time Expectations

| Action | GitHub Pages | Local Dev |
|--------|--------------|-----------|
| Page Load | <2 seconds | <1 second |
| Navigation Click | <1 second | <500ms |
| API Check | <500ms | <500ms |
| Service Detection | <1 second | <1 second |
| Environment Detection | <50ms | <50ms |

## Accessibility Notes

### Screen Reader Experience
```
[Logo] "Aria"
[Heading] "Quantum AI System - Web Hub"

[Section] "Aria Interfaces"
  [Card] "Aria Visual Command"
  [Description] "Interactive visual command system..."
  [Button] "Open Aria"
  [Button] "Auto-Execute Planner"

[Section] "Quantum Experiences"
  [Card] "Quantum Portal Hub"
  ...

[Section] "Dashboards & Monitoring"
  ...

[Section] "API & Services"
  [Card] "API Endpoints"
  [Button] "Check Local Status"
  [Button] "API Documentation"
```

### Keyboard Navigation
```
Tab → Navigate through all buttons
Enter → Activate button
Space → Activate button
Escape → Close alerts

All interactive elements are keyboard accessible.
All links have clear focus states.
```

## Mobile Experience

### Portrait Mode (Mobile)
```
┌──────────────────┐
│      Aria        │ 100vw
│ Quantum AI Hub   │
├──────────────────┤
│ 🎯 Aria          │
│    Interfaces    │ Single column
│ [Button] [Button]│ Cards stack
├──────────────────┤
│ ⚛️ Quantum       │
│    Experiences   │
│ [Button] [Button]│
└──────────────────┘
```

### Landscape Mode
```
┌────────────────────────────────────────────┐
│ Aria | Quantum AI Hub                      │
├────────────────────────────────────────────┤
│ 🎯 Aria         │ ⚛️ Quantum              │ Two columns
│ [Btn] [Btn]     │ [Btn] [Btn]             │ Responsive grid
├────────────────────────────────────────────┤
│ 📊 Dashboards   │ 🔌 API & Services      │
│ [Btn] [Btn]     │ [Btn] [Btn]             │
└────────────────────────────────────────────┘
```

## Error Handling

### Network Timeout (GitHub Pages)
```
User clicks "Check Local Status"
    ↓
Page detects GitHub Pages
    ↓
Shows helpful message (no error, just info)
    ↓
User can copy command and run locally
```

### Service Unavailable (Local Dev)
```
User clicks "Aria Server"
    ↓
Page detects localhost
    ↓
Tries to connect to port 8080
    ↓
Connection fails
    ↓
Shows: "Aria Server is not running at http://localhost:8080
Start it with: cd aria_web && python server.py"
```

## Success Indicators

Users will know everything is working when they see:

✅ **Web Hub** — Loads and displays all cards
✅ **Navigation** — All interface links lead to correct pages
✅ **Design** — Glassmorphism effects visible, smooth animations
✅ **Environment** — Footer shows correct environment label
✅ **Responsiveness** — Layout adapts to their screen size
✅ **Accessibility** — Can navigate with keyboard
✅ **Messages** — Helpful guidance when clicking service links

---

**For detailed technical information, see:** `GITHUB_PAGES_TECHNICAL_DETAILS.md`
