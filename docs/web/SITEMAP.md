# Visual Site Map - Aria Web System

## Overview Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  🏠 WEB HUB (ROOT)                      │
│             (web-hub.html / index.html)                │
│  Unified central navigation for all web interfaces     │
└────────────────┬──────────────────────────────────────┘
                 │
     ┌───────────┼───────────┬────────────────┐
     │           │           │                │
     ▼           ▼           ▼                ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐
│ ARIA    │ │ QUANTUM │ │DASHBARD │ │ API & LOCAL  │
│INTERFACES│ │ WORLDS  │ │& MONITOR│ │ SERVICES     │
└────┬────┘ └────┬────┘ └────┬────┘ └──────────────┘
     │           │           │
     │           │           │
```

---

## Detailed Site Tree

```
HTTP://LOCALHOST/
│
├─── web-hub.html ⭐ MAIN HUB
│    └─ Connects to all pages below
│
├─── aria_web/ (Character & Quantum)
│    ├─── index.html (Aria Visual Command) [🎨 + 🏠]
│    ├─── auto-execute.html (Auto-Executor) [🏠]
│    ├─── quantum-portal.html (Quantum Hub)
│    ├─── quantum-world.html (2D Quantum) [API]
│    ├─── quantum-world-3d.html (3D Quantum)
│    ├─── quantum-world-features.html (Features)
│    └─── test-quantum-world.html (Tests) [API]
│
├─── chat-web/ (Chat Interfaces)
│    ├─── index.html (Main Chat) [🏠]
│    └─── aria.html (Aria Chat)
│
├─── dashboard/ (Monitoring & Analysis)
│    ├─── index.html (Dashboard Index) [🏠]
│    ├─── unified.html (Training Dashboard) [🏠]
│    ├─── hub.html (Command Center) [🏠]
│    ├─── gguf_visualizer.html (Model Analysis) [🏠]
│    ├─── advanced.html (Advanced Tools) [🏠]
│    ├─── analytics.html (Analytics) [🏠]
│    ├─── consolidated.html (Consolidated)
│    └─── enhanced.html (Enhanced View)
│
├─── Documentation
│    ├─ WEB_PAGES_NAVIGATION.md (Detailed guide)
│    ├─ WEB_PAGES_QUICK_REF.md (Quick reference)
│    ├─ WEB_HUB_IMPLEMENTATION.md (Implementation)
│    └─ README.md (Project readme)
│
└─── Backend Services (Not served as files)
     ├─ Port 7071: Azure Functions (/api/*)
     ├─ Port 8080: Aria Server
     └─ Port 8765: Dashboard Server
```

**Legend:**
- ⭐ = Hub page (central navigation)
- 🎨 = Has Aria character interaction
- 🏠 = Has back-to-hub navigation link
- [API] = Requires API backend
- [PORT] = Non-HTTP service

---

## Navigation Flow Diagram

```
                      ┌────────────────┐
                      │  USER VISITS   │
                      │ localhost/     │
                      └────────┬────────┘
                               │
                               ▼
                      ┌────────────────┐
                      │  index.html    │
                      │  (Redirects)   │
                      └────────┬────────┘
                               │
                               ▼
                      ┌────────────────┐
                      │  web-hub.html  │
                      │  (Main Hub)    │
                      └────────┬────────┘
                               │
        ┌──────────────────────┼──────────────────┐
        │                      │                  │
        ▼                      ▼                  ▼
    ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
    │ Aria Pages     │  │ Quantum Pages  │  │ Dashboard Pgs  │
    └────────┬───────┘  └────────┬───────┘  └────────┬───────┘
             │                   │                   │
             ├─ [Back 🏠] ←──────┼──────────→ [Back 🏠]
             │                   │                   │
             └───────────────┬───┴───────────────────┘
                             │
                    [All pages include]
                      [Back-to-Hub Link]
                      (🏠 Web Hub button)
                             │
                             ▼
                    ┌──────────────────┐
                    │  Return to Hub   │
                    │  (web-hub.html)  │
                    └──────────────────┘
```

---

## Hub Card Layout

```
┌─────────────────────────────────────────────────────────────┐
│  ARIA - Web Hub                                             │
│  Quantum AI System - Web Hub                                │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 🎯 ARIA INTERFACES                                           │
├──────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────┐                    │
│ │ 🎨 Aria Visual  │  │ 💬 Chat         │                    │
│ │ Command         │  │ Interface       │                    │
│ │ [Open] [Portal] │  │ [Open] [Aria]   │                    │
│ └─────────────────┘  └─────────────────┘                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ ⚛️  QUANTUM EXPERIENCES                                      │
├──────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────┐                    │
│ │ 🌀 Portal Hub   │  │ 🌍 World 2D     │                    │
│ │ [Enter Portal]  │  │ [Launch] [Test] │                    │
│ ├─────────────────┤  ├─────────────────┤                    │
│ │ 🎭 World 3D     │  │ ✨ Features     │                    │
│ │ [Launch 3D]     │  │ [View Features] │                    │
│ └─────────────────┘  └─────────────────┘                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 📊 DASHBOARDS & MONITORING                                  │
├──────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────┐                    │
│ │ 📈 Training     │  │ 🎛️  Command     │                    │
│ │ Dashboard       │  │ Center          │                    │
│ │ [View Training] │  │ [Open Command]  │                    │
│ ├─────────────────┤  ├─────────────────┤                    │
│ │ 🔍 Model Anal   │  │ 🎯 Advanced     │                    │
│ │ [View Models]   │  │ [Advanced Tools]│                    │
│ └─────────────────┘  └─────────────────┘                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 🔌 API & SERVICES                                            │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ 🚀 API Endpoints     [Check Status] [API Docs]          │ │
│ │ 🔗 Local Services    [8080] [7071] [8765]               │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Page Relationships

```
                    WEB HUB (Central Hub)
                           ↓
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ARIA TIER         QUANTUM TIER      DASHBOARD TIER
        │                  │                  │
    ┌───┴───┐          ┌───┴────┐        ┌──┴──┐
    │   │   │          │    │   │        │  │  │
  [CMD][CHAT][EXEC]  [PORTAL][WORLD][TEST] [HUB][DASH]
    │   │   │          │    │   │        │  │  │
    └───┴───┘          └────┴───┘        └──┴──┘
       ↓                   ↓                 ↓
   [Back 🏠] ←─ → [Back 🏠] ← → [Back 🏠]
```

---

## Access Points

### Primary Entry (Recommended)
```
1. Browser: http://localhost/
2. Auto-redirect to: http://localhost/web-hub.html
3. See all available options
4. Click desired interface
```

### Direct Links (If needed)
```
Aria:       http://localhost/aria_web/
Chat:       http://localhost/chat-web/
Quantum:    http://localhost/aria_web/quantum-portal.html
Dashboards: http://localhost/dashboard/
```

### Quick Navigation
```
From any page, use [🏠 Web Hub] link (top-left)
to return to main hub and see all options
```

---

## Connection Summary

| From Page | Can Navigate To | Via |
|-----------|-----------------|-----|
| Any Aria page | Web Hub | 🏠 Web Hub link |
| Any Chat page | Web Hub | 🏠 Web Hub link |
| Any Dashboard | Web Hub | 🏠 Web Hub link |
| Web Hub | Any page | Card links |
| Root (/) | Web Hub | Auto-redirect |

---

## Service Integration

```
Web Pages (Port 80)
       ↓
    ┌──┴──┐
    │     │
    ▼     ▼
[Hub] ← → [Character Pages]
    │
    └─→ [Call API]
           ↓
    ┌──────┴────────┐
    ▼               ▼
Azure Func      Aria Server
(7071)          (8080)
    │               │
    └─ Services ────┘
       & Data
```

---

**Last Updated**: January 24, 2026  
**Diagram Version**: 1.0  
**Status**: Complete and Connected ✅
