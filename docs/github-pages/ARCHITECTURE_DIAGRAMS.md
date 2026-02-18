# GitHub Pages Architecture & Flow Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Web Hub (web-hub.html)                       │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ JavaScript Environment Detection (Lines 460-557)           │ │
│  │                                                            │ │
│  │ if (hostname.includes('github.io'))  → GitHub Pages      │ │
│  │ if (hostname === 'localhost')        → Local Dev         │ │
│  │ else                                  → Web Server        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Smart Handler Functions                                   │ │
│  │                                                            │ │
│  │ ├─ tryLocalService()       → Check port connectivity     │ │
│  │ ├─ checkLocalAPI()         → Test API status             │ │
│  │ ├─ showAPIGuide()          → Show documentation          │ │
│  │ ├─ openDocs/README/etc()   → Context-aware file access  │ │
│  │ └─ displayEnvironmentInfo() → Show environment label      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ User Interaction Handlers                                 │ │
│  │                                                            │ │
│  │ Navigation Links           → Relative paths (work all)   │ │
│  │ API Checks                 → Smart functions             │ │
│  │ Service Links              → Conditional behavior        │ │
│  │ Doc Links                  → Environment-aware           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Flow

```
Developer
    ↓
Git Push
    ↓
┌─────────────────────┐
│  GitHub Repository  │
├─────────────────────┤
│ ✓ web-hub.html      │
│ ✓ .nojekyll         │
│ ✓ CSS/JS files      │
│ ✓ Markdown docs     │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ Settings → Pages    │
│ Source: main branch │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ GitHub Actions      │
│ Build & Deploy      │
│ (1-2 minutes)       │
└─────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ GitHub Pages Live                   │
│ https://user.github.io/repo/        │
├─────────────────────────────────────┤
│ ✅ Web hub loads                    │
│ ✅ Navigation works                 │
│ ✅ Smart handlers active            │
│ ✅ API checks show instructions     │
│ ✅ Service links show guidance      │
└─────────────────────────────────────┘
    ↓
Public can access & browse!
```

## Request Routing

### Navigation Links (Always Work)
```
User clicks: aria_web/index.html
    ↓
Browser: window.location.href = 'aria_web/index.html'
    ↓
┌─────────────────────────────────────┐
│ GitHub Pages | Local Dev | Web Srv  │
├─────────────────────────────────────┤
│ ✅ Resolves correctly               │
│ ✅ Loads resource                   │
│ ✅ Displays interface               │
└─────────────────────────────────────┘
```

### API Check (Environment-Aware)
```
User clicks: "Check Local Status"
    ↓
JavaScript calls: checkLocalAPI()
    ↓
Detect environment:
┌─────────────────────────────────────┐
│ GitHub Pages?                       │
│ YES → Show message with setup       │
│ NO  → Check localhost:7071 API      │
│       → API running? Show status    │
│       → API down? Show restart info │
└─────────────────────────────────────┘
```

### Service Link (Conditional)
```
User clicks: "Aria Server (8080)"
    ↓
JavaScript calls: tryLocalService(url, name)
    ↓
┌────────────────────────────────────────┐
│ Detect Environment                     │
├────────────────────────────────────────┤
│ GitHub Pages                           │
│ ↓                                      │
│ alert("Only available locally")        │
│ show: "cd aria_web && python ..." │
│                                        │
│ Local Development                      │
│ ↓                                      │
│ Try fetch to http://localhost:8080     │
│ ↓                                      │
│ Success? → window.open(url)            │
│ Fail?    → alert("Not running...")     │
│           show: "cd aria_web && ..."   │
│                                        │
│ Other Web Server                       │
│ ↓                                      │
│ Similar to local (attempt connect)     │
└────────────────────────────────────────┘
```

## File Relationships

```
Root Directory
    ├── index.html
    │   └─→ Redirects to web-hub.html
    │
    ├── web-hub.html ⭐ MAIN FILE (UPDATED)
    │   ├─→ Imports no external resources
    │   ├─→ Contains all CSS inline
    │   ├─→ Contains all JS inline
    │   ├─→ Links to aria_web/
    │   ├─→ Links to chat-web/
    │   ├─→ Links to dashboard/
    │   └─→ Smart environment detection
    │
    ├── .nojekyll ⭐ NEW FILE
    │   └─→ Disables Jekyll processing
    │
    ├── aria_web/
    │   ├── index.html (Has back-nav)
    │   ├── quantum-portal.html
    │   ├── quantum-world.html
    │   └── ... other files
    │
    ├── chat-web/
    │   ├── index.html (Has back-nav)
    │   └── ... other files
    │
    ├── dashboard/
    │   ├── index.html (Has back-nav)
    │   └── ... other files
    │
    └── Documentation/ ⭐ NEW FILES
        ├── GITHUB_PAGES_DEPLOYMENT.md
        ├── GITHUB_PAGES_QUICK_START.md
        ├── GITHUB_PAGES_TECHNICAL_DETAILS.md
        ├── GITHUB_PAGES_USER_EXPERIENCE.md
        ├── GITHUB_PAGES_UPDATE_SUMMARY.md
        ├── GITHUB_PAGES_DEPLOYMENT_CHECKLIST.md
        ├── GITHUB_PAGES_COMPLETE_SUMMARY.md
        ├── WEB_PAGES_NAVIGATION.md
        ├── WEB_PAGES_QUICK_REF.md
        └── WEB_HUB_IMPLEMENTATION.md
```

## Environment Detection Decision Tree

```
Page Loads
    ↓
┌─────────────────────────────────────────┐
│ Check window.location.hostname          │
└─────────────────────────────────────────┘
    ↓
    ├─ Contains 'github.io'?
    │  │
    │  └─→ YES
    │      │
    │      ├─ Set isGitHubPages = true
    │      └─ Configure: Show instructions for services
    │
    ├─ Equals 'localhost'?
    │  │
    │  └─→ YES
    │      │
    │      ├─ Set isLocalhost = true
    │      └─ Configure: Try to connect to services
    │
    └─ Other
       │
       └─→ YES
           │
           ├─ Set isWebServer = true
           └─ Configure: Attempt connections (like localhost)

    ↓
Application runs with appropriate behavior
```

## User Journey Maps

### Journey A: GitHub Pages Visitor
```
┌─────────────────┐
│ Visit GitHub    │
│ Pages Link      │
└────────┬────────┘
         ↓
    ┌─────────────────────────────┐
    │ Page Loads                  │
    │ (Environment: GitHub Pages) │
    └────────┬────────────────────┘
             ↓
    ┌────────────────────────────────────┐
    │ See Web Hub                        │
    │ ✓ All interface cards visible     │
    │ ✓ CSS/Design loads correctly      │
    │ ✓ Footer shows "GitHub Pages"     │
    └────────┬───────────────────────────┘
             ├─ Click "Open Aria"
             │  ↓
             │  ┌──────────────────────┐
             │  │ Aria Interface Loads │
             │  │ ✓ Works on GH Pages  │
             │  └──────────────────────┘
             │
             ├─ Click "Check Status"
             │  ↓
             │  ┌────────────────────────────────────┐
             │  │ Alert: "Not available online"      │
             │  │ Shows: "func host start"           │
             │  │ User learns about local setup      │
             │  └────────────────────────────────────┘
             │
             └─ Click "Aria Server"
                ↓
                ┌────────────────────────────────────┐
                │ Alert: "Only available locally"    │
                │ Shows: "cd aria_web && python..."  │
                │ User knows how to run locally      │
                └────────────────────────────────────┘

Result: User sees system, understands limitations,
        learns how to set up locally for full features
```

### Journey B: Local Developer
```
┌──────────────────┐
│ Start Services:  │
│ - func host      │
│ - aria server    │
│ - dashboard      │
└────────┬─────────┘
         ↓
    ┌──────────────────────────────┐
    │ Visit localhost:8000         │
    │ (Environment: Local Development)
    └────────┬─────────────────────┘
             ↓
    ┌────────────────────────────────────┐
    │ See Web Hub                        │
    │ ✓ All features available          │
    │ ✓ Footer shows "Local Development"│
    └────────┬───────────────────────────┘
             ├─ Click "Open Aria"
             │  ↓
             │  ┌──────────────────────┐
             │  │ Live Aria Loads      │
             │  │ ✓ API Connected      │
             │  │ ✓ Full Features      │
             │  └──────────────────────┘
             │
             ├─ Click "Check Status"
             │  ↓
             │  ┌────────────────────────────┐
             │  │ ✅ API is running!         │
             │  │ Provider: azure            │
             │  │ Opens: /api/ai/status      │
             │  │ Shows: Full JSON response  │
             │  └────────────────────────────┘
             │
             └─ Click "Aria Server"
                ↓
                ┌────────────────────────────┐
                │ Opens: http://localhost:8080
                │ ✓ Live Server Loads       │
                │ ✓ Full Interactivity     │
                └────────────────────────────┘

Result: Developer has full local environment,
        all features working, ready for development
```

## Code Execution Flow

```
HTML Page Loads (web-hub.html)
    ↓
┌────────────────────────────────────────────┐
│ 1. Parse HTML Structure                   │
│    - Header with title                    │
│    - Grid of cards                        │
│    - Navigation buttons                   │
│    - CSS (inline in <style>)              │
└────────┬─────────────────────────────────┘
         ↓
┌────────────────────────────────────────────┐
│ 2. Apply Styles                           │
│    - CSS Grid layout                      │
│    - Glassmorphism effects                │
│    - Responsive breakpoints               │
│    - Color variables                      │
└────────┬─────────────────────────────────┘
         ↓
┌────────────────────────────────────────────┐
│ 3. Execute JavaScript (Lines 460-557)     │
│    - Detect environment                   │
│    - Define handler functions             │
│    - Register event listeners             │
│    - Display environment info             │
└────────┬─────────────────────────────────┘
         ↓
┌────────────────────────────────────────────┐
│ 4. Page Ready for Interaction             │
│    - User can click buttons                │
│    - Environment detection active         │
│    - Smart handlers ready                 │
└────────┬─────────────────────────────────┘
         ↓
┌────────────────────────────────────────────┐
│ 5. User Action (e.g., click button)       │
│    - Calls handler function               │
│    - Checks environment                   │
│    - Executes appropriate code path       │
│    - Shows result or alert                │
└────────────────────────────────────────────┘
```

## Error Handling Flow

```
User Interaction
    ↓
Try/Catch Block
    ├─ Try: Fetch API or open link
    │  ↓
    │  ├─ Success → Execute action ✅
    │  └─ Fail → Catch exception
    │
    └─ Catch: Handle error
       ↓
       ├─ Check environment
       │  ├─ GitHub Pages → Show helpful message ℹ️
       │  ├─ Local Dev → Show service not running
       │  └─ Other → Show generic guidance
       │
       └─ Display message to user
          (No silent failures)
```

---

**Diagrams Version:** 1.0
**Last Updated:** January 24, 2026
