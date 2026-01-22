// Unified Navigation Component for QAI Web Interfaces
// Links Aria, Chat, and Dashboard together with smooth navigation

const navigationConfig = {
    apps: [
        {
            id: 'aria',
            name: 'Aria Character',
            icon: '🎭',
            url: '/aria_web/index.html',
            description: 'Interactive AI character with animations and commands'
        },
        {
            id: 'chat',
            name: 'QAI Chat',
            icon: '💬',
            url: '/chat-web/index.html',
            description: 'Quantum AI chat interface with streaming'
        },
        {
            id: 'dashboard',
            name: 'Dashboard',
            icon: '📊',
            url: '/dashboard/index.html',
            description: 'Training monitoring and analytics'
        },
        {
            id: 'auto-execute',
            name: 'Auto-Execute',
            icon: '🤖',
            url: '/aria_web/auto-execute.html',
            description: 'Advanced command automation system'
        }
    ],
    quickActions: [
        { icon: '🏠', label: 'Home', action: () => window.location.href = '/' },
        { icon: '🔄', label: 'Refresh', action: () => window.location.reload() },
        { icon: '📱', label: 'Install App', action: () => promptInstallPWA() }
    ]
};

class UnifiedNavigation {
    constructor(currentApp = null) {
        this.currentApp = currentApp;
        this.isExpanded = localStorage.getItem('nav-expanded') === 'true';
        this.theme = localStorage.getItem('global-theme') || 'auto';
        this.init();
    }
    
    init() {
        this.injectStyles();
        this.createNavBar();
        this.setupEventListeners();
        this.detectCurrentApp();
    }
    
    injectStyles() {
        const style = document.createElement('style');
        style.id = 'unified-nav-styles';
        style.textContent = `
            :root {
                --nav-height: 60px;
                --nav-bg: rgba(255, 255, 255, 0.95);
                --nav-text: #333;
                --nav-accent: #667eea;
                --nav-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            [data-theme="dark"] {
                --nav-bg: rgba(30, 30, 46, 0.95);
                --nav-text: #e0e0e0;
                --nav-accent: #8a95f0;
                --nav-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            
            .unified-nav {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: var(--nav-height);
                background: var(--nav-bg);
                backdrop-filter: blur(10px);
                box-shadow: var(--nav-shadow);
                z-index: 10000;
                display: flex;
                align-items: center;
                padding: 0 20px;
                transition: all 0.3s ease;
            }
            
            .unified-nav.collapsed {
                height: 40px;
            }
            
            .nav-logo {
                font-size: 24px;
                font-weight: bold;
                color: var(--nav-accent);
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 10px;
                margin-right: auto;
                transition: all 0.3s;
            }
            
            .nav-logo:hover {
                transform: scale(1.05);
            }
            
            .nav-apps {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            
            .nav-app-btn {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 10px 16px;
                background: transparent;
                border: 2px solid transparent;
                border-radius: 12px;
                color: var(--nav-text);
                text-decoration: none;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s;
                white-space: nowrap;
            }
            
            .nav-app-btn:hover {
                background: rgba(102, 126, 234, 0.1);
                border-color: var(--nav-accent);
                transform: translateY(-2px);
            }
            
            .nav-app-btn.active {
                background: var(--nav-accent);
                color: white;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }
            
            .nav-app-icon {
                font-size: 20px;
            }
            
            .nav-actions {
                display: flex;
                gap: 8px;
                margin-left: 20px;
                padding-left: 20px;
                border-left: 1px solid rgba(0,0,0,0.1);
            }
            
            .nav-action-btn {
                padding: 8px 12px;
                background: transparent;
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 8px;
                cursor: pointer;
                font-size: 18px;
                transition: all 0.3s;
                color: var(--nav-text);
            }
            
            .nav-action-btn:hover {
                background: rgba(102, 126, 234, 0.1);
                transform: scale(1.1);
            }
            
            .nav-toggle {
                position: absolute;
                bottom: -15px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--nav-bg);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 0 0 12px 12px;
                padding: 4px 12px;
                cursor: pointer;
                font-size: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: all 0.3s;
            }
            
            .nav-toggle:hover {
                padding: 6px 16px;
            }
            
            .nav-breadcrumb {
                position: absolute;
                bottom: 5px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 12px;
                color: var(--nav-text);
                opacity: 0.7;
            }
            
            /* Mobile responsiveness */
            @media (max-width: 768px) {
                .unified-nav {
                    padding: 0 10px;
                }
                
                .nav-app-btn {
                    padding: 8px 10px;
                    font-size: 12px;
                }
                
                .nav-app-name {
                    display: none;
                }
                
                .nav-actions {
                    margin-left: 10px;
                    padding-left: 10px;
                }
            }
            
            /* Notification badge */
            .nav-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                background: #e74c3c;
                color: white;
                border-radius: 50%;
                width: 18px;
                height: 18px;
                font-size: 11px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            
            /* Dropdown menu */
            .nav-dropdown {
                position: relative;
            }
            
            .nav-dropdown-menu {
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 10px;
                background: var(--nav-bg);
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.2);
                padding: 10px;
                min-width: 200px;
                display: none;
                animation: slideDown 0.3s ease-out;
            }
            
            .nav-dropdown:hover .nav-dropdown-menu {
                display: block;
            }
            
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .nav-dropdown-item {
                padding: 10px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 10px;
                color: var(--nav-text);
            }
            
            .nav-dropdown-item:hover {
                background: rgba(102, 126, 234, 0.1);
            }
        `;
        document.head.appendChild(style);
    }
    
    createNavBar() {
        const nav = document.createElement('nav');
        nav.className = 'unified-nav';
        nav.innerHTML = `
            <a href="/" class="nav-logo">
                <span>⚛️</span>
                <span>QAI Platform</span>
            </a>
            
            <div class="nav-apps">
                ${navigationConfig.apps.map(app => `
                    <a href="${app.url}" 
                       class="nav-app-btn ${this.currentApp === app.id ? 'active' : ''}"
                       data-app="${app.id}"
                       title="${app.description}">
                        <span class="nav-app-icon">${app.icon}</span>
                        <span class="nav-app-name">${app.name}</span>
                    </a>
                `).join('')}
            </div>
            
            <div class="nav-actions">
                <button class="nav-action-btn" id="nav-theme-btn" title="Toggle theme">
                    🌓
                </button>
                <button class="nav-action-btn" id="nav-fullscreen-btn" title="Toggle fullscreen">
                    ⛶
                </button>
                <div class="nav-dropdown">
                    <button class="nav-action-btn" title="More actions">
                        ⚙️
                    </button>
                    <div class="nav-dropdown-menu">
                        <div class="nav-dropdown-item" id="nav-install">
                            📱 Install App
                        </div>
                        <div class="nav-dropdown-item" id="nav-shortcuts">
                            ⌨️ Keyboard Shortcuts
                        </div>
                        <div class="nav-dropdown-item" id="nav-about">
                            ℹ️ About
                        </div>
                    </div>
                </div>
            </div>
            
            <button class="nav-toggle">
                ${this.isExpanded ? '▲' : '▼'}
            </button>
        `;
        
        document.body.insertBefore(nav, document.body.firstChild);
        
        // Add padding to body to account for nav
        document.body.style.paddingTop = 'var(--nav-height)';
    }
    
    setupEventListeners() {
        // Theme toggle
        document.getElementById('nav-theme-btn')?.addEventListener('click', () => {
            this.toggleTheme();
        });
        
        // Fullscreen toggle
        document.getElementById('nav-fullscreen-btn')?.addEventListener('click', () => {
            this.toggleFullscreen();
        });
        
        // Nav collapse/expand
        document.querySelector('.nav-toggle')?.addEventListener('click', () => {
            this.toggleExpanded();
        });
        
        // Install PWA
        document.getElementById('nav-install')?.addEventListener('click', () => {
            this.promptInstall();
        });
        
        // Show shortcuts
        document.getElementById('nav-shortcuts')?.addEventListener('click', () => {
            this.showKeyboardShortcuts();
        });
        
        // About
        document.getElementById('nav-about')?.addEventListener('click', () => {
            this.showAbout();
        });
        
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey) {
                const key = e.key.toLowerCase();
                const apps = navigationConfig.apps;
                
                // Ctrl/Cmd + Shift + 1-4: Switch apps
                if (key >= '1' && key <= '4') {
                    e.preventDefault();
                    const index = parseInt(key) - 1;
                    if (apps[index]) {
                        window.location.href = apps[index].url;
                    }
                }
                
                // Ctrl/Cmd + Shift + T: Toggle theme
                if (key === 't') {
                    e.preventDefault();
                    this.toggleTheme();
                }
                
                // Ctrl/Cmd + Shift + F: Toggle fullscreen
                if (key === 'f') {
                    e.preventDefault();
                    this.toggleFullscreen();
                }
            }
        });
    }
    
    detectCurrentApp() {
        const path = window.location.pathname;
        if (path.includes('aria_web')) {
            this.currentApp = 'aria';
        } else if (path.includes('chat-web')) {
            this.currentApp = 'chat';
        } else if (path.includes('dashboard')) {
            this.currentApp = 'dashboard';
        }
    }
    
    toggleTheme() {
        const themes = ['light', 'dark', 'auto'];
        const currentIndex = themes.indexOf(this.theme);
        this.theme = themes[(currentIndex + 1) % themes.length];
        localStorage.setItem('global-theme', this.theme);
        
        if (this.theme === 'auto') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', this.theme);
        }
        
        this.showNotification(`🎨 Theme: ${this.theme}`);
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error('Fullscreen error:', err);
            });
            this.showNotification('⛶ Fullscreen enabled');
        } else {
            document.exitFullscreen();
            this.showNotification('⛶ Fullscreen disabled');
        }
    }
    
    toggleExpanded() {
        this.isExpanded = !this.isExpanded;
        localStorage.setItem('nav-expanded', this.isExpanded);
        
        const nav = document.querySelector('.unified-nav');
        const toggle = document.querySelector('.nav-toggle');
        
        if (this.isExpanded) {
            nav.classList.remove('collapsed');
            toggle.textContent = '▲';
        } else {
            nav.classList.add('collapsed');
            toggle.textContent = '▼';
        }
    }
    
    promptInstall() {
        // This will be handled by the PWA install prompt
        if (window.deferredPrompt) {
            window.deferredPrompt.prompt();
            window.deferredPrompt.userChoice.then(choice => {
                this.showNotification(
                    choice.outcome === 'accepted' ? '✅ App installed!' : 'ℹ️ Install cancelled'
                );
                window.deferredPrompt = null;
            });
        } else {
            this.showNotification('ℹ️ Install not available or already installed');
        }
    }
    
    showKeyboardShortcuts() {
        const shortcuts = `
Keyboard Shortcuts:
• Ctrl/Cmd + Shift + 1-4: Switch apps
• Ctrl/Cmd + Shift + T: Toggle theme
• Ctrl/Cmd + Shift + F: Toggle fullscreen
• Ctrl/Cmd + K: Focus search/input
• Ctrl/Cmd + /: Show shortcuts
        `.trim();
        
        alert(shortcuts);
    }
    
    showAbout() {
        const about = `
QAI Platform - Quantum AI System
Version: 2.0.0
Build: ${new Date().toLocaleDateString()}

Components:
• Aria Character - Interactive AI avatar
• QAI Chat - Streaming chat interface
• Dashboard - Training monitoring

© 2026 QAI Platform
        `.trim();
        
        alert(about);
    }
    
    showNotification(message) {
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: rgba(102, 126, 234, 0.95);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 10001;
            animation: slideInRight 0.3s ease-out, fadeOut 0.3s ease-out 2.7s;
        `;
        
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.unifiedNav = new UnifiedNavigation();
    });
} else {
    window.unifiedNav = new UnifiedNavigation();
}

// Export for manual initialization
window.UnifiedNavigation = UnifiedNavigation;
