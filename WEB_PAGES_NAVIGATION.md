# Aria Web Hub - Complete Website Navigation

## Hub Overview

The **Web Hub** (`web-hub.html`) is the central gateway connecting all web pages and features across the Aria Quantum AI System.

### Access the Hub

- **Root URL**: `http://localhost/` (or `http://localhost/web-hub.html`)
- **Direct**: Points to `index.html` which redirects to `web-hub.html`

---

## Connected Pages

### 🎯 Aria Interfaces

| Page | URL | Description |
|------|-----|-------------|
| **Aria Visual Command** | `aria_web/index.html` | Interactive visual command system with real-time character control |
| **Chat Interface** | `chat-web/index.html` | Multi-provider AI chat with streaming and code highlighting |
| **Auto-Execute Planner** | `aria_web/auto-execute.html` | Command planning and automated execution UI |
| **Aria Chat** | `chat-web/aria.html` | Dedicated chat interface for Aria interactions |

### ⚛️ Quantum Experiences

| Page | URL | Description |
|------|-----|-------------|
| **Quantum Portal Hub** | `aria_web/quantum-portal.html` | Central gateway to all quantum worlds |
| **Quantum World 2D** | `aria_web/quantum-world.html` | Interactive 2D quantum simulation (API-backed) |
| **Quantum World 3D** | `aria_web/quantum-world-3d.html` | 3D canvas quantum visualization |
| **Quantum Features** | `aria_web/quantum-world-features.html` | Feature showcase and guide |
| **Quantum Test Suite** | `aria_web/test-quantum-world.html` | Automated testing (API-backed) |

### 📊 Dashboards & Monitoring

| Page | URL | Description |
|------|-----|-------------|
| **Training Dashboard** | `dashboard/unified.html` | Real-time training metrics and analytics |
| **Command Center** | `dashboard/hub.html` | System control hub with status and orchestration |
| **Model Analysis** | `dashboard/gguf_visualizer.html` | GGUF model visualization and inspection |
| **Advanced Dashboard** | `dashboard/advanced.html` | Hyperparameter optimization tools |
| **Analytics** | `dashboard/analytics.html` | Performance analytics |
| **Consolidated View** | `dashboard/consolidated.html` | Integrated system monitoring |
| **Enhanced Dashboard** | `dashboard/enhanced.html` | Enhanced analytics view |
| **Dashboard Index** | `dashboard/index.html` | Main dashboard landing page |

### 🔌 API & Services

| Endpoint | Port | Description |
|----------|------|-------------|
| **Azure Functions** | 7071 | REST API endpoints (`/api/chat`, `/api/ai/status`, etc.) |
| **Aria Server** | 8080 | Aria web UI and character server |
| **Dashboard Server** | 8765 | VS Code integrated dashboard |

---

## Navigation Features

### Back-to-Hub Links

All main pages include a **"🏠 Web Hub"** button in the top-left corner for easy return to the hub:

- **Aria Interfaces**: `nav-hub` link to `../../web-hub.html`
- **Chat Interface**: `nav-hub` link to `../web-hub.html`
- **Dashboard Pages**: `nav-hub` link to `../web-hub.html`

### Hub Card Organization

The Web Hub groups pages into clear categories with:

- **Icon indicators** for each section
- **Status badges** (API-Connected, Live Feed, Control Panel, etc.)
- **Quick access buttons** for primary and secondary interfaces
- **Feature descriptions** for each page

---

## Connection Map

```
                        web-hub.html (Root)
                              |
        ______________|_______|_______|______________
        |              |              |              |
    Aria UI      Chat Interface   Quantum Worlds  Dashboards
        |              |              |              |
    index.html    chat/index.html  quantum-portal  dashboard/*
    aria.html     aria.html        quantum-*html    hub.html
    auto-exec.html                 test-quantum    unified.html
                                                   advanced.html
                                                   gguf_visual
```

---

## URL Patterns

| Pattern | Usage |
|---------|-------|
| `/` | Redirects to `/web-hub.html` |
| `/web-hub.html` | Main hub page (NEW) |
| `/aria_web/*` | Aria character and quantum experiences |
| `/chat-web/*` | Chat interfaces |
| `/dashboard/*` | Training dashboards and monitoring |

---

## Local Service URLs

Quick reference for locally-hosted services:

- **Web Hub**: `http://localhost/web-hub.html`
- **Aria Server**: `http://localhost:8080`
- **Azure Functions API**: `http://localhost:7071`
- **Dashboard Server**: `http://localhost:8765`
- **API Status Check**: `http://localhost:7071/api/ai/status`

---

## Features of the Hub

### 🎨 Design
- Responsive grid layout with 320px minimum card width
- Glassmorphism styling with backdrop blur effects
- Smooth hover animations and transitions
- Dark theme support ready
- Mobile-friendly navigation

### 🎯 Organization
- 6 main categories (Aria, Quantum, Dashboards, API, Local Services)
- Clear status indicators for each page
- Organized link groups within each card
- Category section titles with visual separators

### ♿ Accessibility
- Semantic HTML structure
- ARIA labels and descriptions
- Keyboard navigation support
- Color-independent status indicators
- Focus-visible styles for all interactive elements

---

## Integration Points

### API Connectivity
All pages connecting to backend services will show:
- Provider information (Azure OpenAI, LMStudio, etc.)
- Connection status indicators
- Real-time feedback messages

### Chat System
Connected pages share:
- Multi-provider chat detection
- Token streaming support
- Lip-sync animations for Aria
- Conversation history across interfaces

### Quantum Simulations
Unified quantum experience with:
- 2D and 3D visualization options
- API-backed interactive simulations
- Real-time circuit execution
- Testing and validation suites

---

## Maintenance Notes

### Adding New Pages
1. Create the HTML file in appropriate directory
2. Add navigation link to Web Hub card
3. Include back-to-hub link in new page header
4. Update this documentation

### Updating Links
All hub links are relative paths (`../`, `../../`) for deployment flexibility.

### Testing Navigation
- Verify all links work from hub
- Test back-to-hub links from each page
- Check responsive design at 320px+ widths
- Validate dark theme support

---

Last Updated: January 24, 2026
Created: January 24, 2026
