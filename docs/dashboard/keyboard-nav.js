/**
 * Keyboard Navigation System
 * Comprehensive keyboard shortcuts with hints panel
 *
 * Features:
 * - Global shortcuts (Ctrl+K, Ctrl+S, etc.)
 * - Modal/dialog shortcuts (Escape, Enter)
 * - Form navigation (Tab, Shift+Tab, arrows)
 * - Persistent hints panel (? to toggle)
 * - ARIA labels for accessibility
 */

class KeyboardNavigationManager {
    constructor(options = {}) {
        this.shortcuts = new Map();
        this.config = {
            showHintsOnLoad: options.showHintsOnLoad || false,
            hintsKey: options.hintsKey || '?',
            enableFormNav: options.enableFormNav !== false,
            enableModalNav: options.enableModalNav !== false,
            ...options
        };
        this.hintsVisible = false;
        this.init();
    }

    init() {
        // Register default shortcuts
        this.registerDefaultShortcuts();

        // Setup keyboard listener
        document.addEventListener('keydown', this.handleKeyDown.bind(this));

        // Create hints panel
        this.createHintsPanel();

        // Show hints on load if configured
        if (this.config.showHintsOnLoad) {
            setTimeout(() => this.showHints(), 1000);
        }
    }

    /**
     * Register a keyboard shortcut
     */
    register(key, callback, description, category = 'General') {
        const shortcutId = this.normalizeKey(key);
        this.shortcuts.set(shortcutId, {
            key,
            callback,
            description,
            category
        });
    }

    /**
     * Normalize key combination for consistent lookup
     */
    normalizeKey(key) {
        return key.toLowerCase()
            .replace('ctrl+', 'control+')
            .replace('cmd+', 'control+');
    }

    /**
     * Register default shortcuts
     */
    registerDefaultShortcuts() {
        // Navigation shortcuts
        this.register('Control+h', () => {
            window.location.href = '/hub.html';
        }, 'Go to Hub', 'Navigation');

        this.register('Control+u', () => {
            window.location.href = '/unified.html';
        }, 'Go to Training Dashboard', 'Navigation');

        this.register('Control+a', () => {
            window.location.href = '/analytics.html';
        }, 'Go to Analytics', 'Navigation');

        // Action shortcuts
        this.register('Control+s', (e) => {
            e.preventDefault();
            const saveBtn = document.querySelector('[onclick*="saveConfig"]');
            if (saveBtn) saveBtn.click();
        }, 'Save Configuration', 'Actions');

        this.register('Control+r', (e) => {
            e.preventDefault();
            const refreshBtn = document.querySelector('[onclick*="refresh"]');
            if (refreshBtn) refreshBtn.click();
        }, 'Refresh Data', 'Actions');

        this.register('Control+/', () => {
            this.toggleHints();
        }, 'Toggle Keyboard Shortcuts', 'Help');

        this.register('?', () => {
            this.toggleHints();
        }, 'Toggle Keyboard Shortcuts', 'Help');

        // Modal shortcuts
        if (this.config.enableModalNav) {
            this.register('Escape', () => {
                const modal = document.querySelector('.modal-overlay, [role="dialog"]');
                if (modal) {
                    const closeBtn = modal.querySelector('.modal-close, [onclick*="remove"], button:last-child');
                    if (closeBtn) closeBtn.click();
                }
            }, 'Close Modal/Dialog', 'Modals');
        }

        // Form shortcuts
        if (this.config.enableFormNav) {
            this.register('Control+Enter', () => {
                const submitBtn = document.querySelector('button[type="submit"], .btn-primary:not([disabled])');
                if (submitBtn && !submitBtn.disabled) submitBtn.click();
            }, 'Submit Form', 'Forms');
        }
    }

    /**
     * Handle keydown events
     */
    handleKeyDown(e) {
        // Build key combination string
        const parts = [];
        if (e.ctrlKey || e.metaKey) parts.push('control');
        if (e.shiftKey) parts.push('shift');
        if (e.altKey) parts.push('alt');

        const key = e.key.toLowerCase();
        if (!['control', 'shift', 'alt', 'meta'].includes(key)) {
            parts.push(key);
        }

        const combination = parts.join('+');
        const shortcut = this.shortcuts.get(combination);

        if (shortcut) {
            // Don't trigger if typing in input
            if (['input', 'textarea', 'select'].includes(e.target.tagName.toLowerCase())) {
                // Allow ? to work in inputs for help
                if (key !== '?') return;
            }

            e.preventDefault();
            shortcut.callback(e);
        }

        // Form navigation enhancements
        if (this.config.enableFormNav) {
            this.handleFormNavigation(e);
        }
    }

    /**
     * Enhanced form navigation
     */
    handleFormNavigation(e) {
        const activeElement = document.activeElement;
        const isFormElement = ['input', 'textarea', 'select', 'button'].includes(
            activeElement.tagName.toLowerCase()
        );

        if (!isFormElement) return;

        // Arrow keys for select/radio navigation
        if (activeElement.tagName.toLowerCase() === 'select') {
            // Let default behavior work for select
            return;
        }

        // Tab navigation (already handled by browser, but we can enhance)
        if (e.key === 'Tab') {
            // Add visual focus indicator
            setTimeout(() => {
                const newFocus = document.activeElement;
                if (newFocus && newFocus !== activeElement) {
                    newFocus.style.outline = '2px solid #0f9d89';
                    setTimeout(() => {
                        newFocus.style.outline = '';
                    }, 500);
                }
            }, 10);
        }
    }

    /**
     * Create hints panel
     */
    createHintsPanel() {
        const panel = document.createElement('div');
        panel.id = 'keyboard-hints-panel';
        panel.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(26, 26, 46, 0.98);
            border: 2px solid #0f9d89;
            border-radius: 12px;
            padding: 20px;
            max-width: 400px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 10000;
            display: none;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
        `;

        panel.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0; color: #0f9d89; font-size: 1.2em;">⌨️ Keyboard Shortcuts</h3>
                <button id="close-hints-btn" style="background: none; border: none; color: #aaa; font-size: 1.5em; cursor: pointer; padding: 0; width: 30px; height: 30px;">&times;</button>
            </div>
            <div id="shortcuts-content"></div>
        `;

        document.body.appendChild(panel);

        document.getElementById('close-hints-btn').onclick = () => this.hideHints();

        // Close on click outside
        panel.addEventListener('click', (e) => e.stopPropagation());
        document.addEventListener('click', () => {
            if (this.hintsVisible) this.hideHints();
        });

        this.updateHintsContent();
    }

    /**
     * Update hints panel content
     */
    updateHintsContent() {
        const content = document.getElementById('shortcuts-content');
        if (!content) return;

        // Group shortcuts by category
        const categories = {};
        this.shortcuts.forEach(shortcut => {
            if (!categories[shortcut.category]) {
                categories[shortcut.category] = [];
            }
            categories[shortcut.category].push(shortcut);
        });

        let html = '';
        Object.keys(categories).sort().forEach(category => {
            html += `<div style="margin-bottom: 20px;">
                <h4 style="color: #888; font-size: 0.9em; text-transform: uppercase; margin-bottom: 10px;">${category}</h4>
                <div style="display: flex; flex-direction: column; gap: 8px;">`;

            categories[category].forEach(shortcut => {
                const keys = shortcut.key.split('+').map(k =>
                    `<kbd style="background: #0f9d89; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-family: monospace;">${k}</kbd>`
                ).join(' + ');

                html += `<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(102, 126, 234, 0.1); border-radius: 6px;">
                    <span style="color: #eaeaea; font-size: 0.9em;">${shortcut.description}</span>
                    <span>${keys}</span>
                </div>`;
            });

            html += `</div></div>`;
        });

        content.innerHTML = html;
    }

    /**
     * Show hints panel
     */
    showHints() {
        const panel = document.getElementById('keyboard-hints-panel');
        if (panel) {
            panel.style.display = 'block';
            this.hintsVisible = true;
        }
    }

    /**
     * Hide hints panel
     */
    hideHints() {
        const panel = document.getElementById('keyboard-hints-panel');
        if (panel) {
            panel.style.display = 'none';
            this.hintsVisible = false;
        }
    }

    /**
     * Toggle hints panel
     */
    toggleHints() {
        if (this.hintsVisible) {
            this.hideHints();
        } else {
            this.showHints();
        }
    }

    /**
     * Add ARIA labels to elements
     */
    addAriaLabels() {
        // Add labels to buttons
        document.querySelectorAll('button:not([aria-label])').forEach(btn => {
            const text = btn.textContent.trim() || btn.title || 'Button';
            btn.setAttribute('aria-label', text);
        });

        // Add labels to inputs
        document.querySelectorAll('input:not([aria-label])').forEach(input => {
            const label = input.previousElementSibling;
            if (label && label.tagName === 'LABEL') {
                input.setAttribute('aria-label', label.textContent.trim());
            } else {
                input.setAttribute('aria-label', input.placeholder || input.name || 'Input field');
            }
        });

        // Add role to modals
        document.querySelectorAll('.modal, .modal-overlay').forEach(modal => {
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
        });
    }

    /**
     * Destroy navigation manager
     */
    destroy() {
        document.removeEventListener('keydown', this.handleKeyDown.bind(this));
        const panel = document.getElementById('keyboard-hints-panel');
        if (panel) panel.remove();
    }
}

// Auto-initialize if window exists
if (typeof window !== 'undefined') {
    window.KeyboardNavigationManager = KeyboardNavigationManager;

    // Auto-create instance
    window.addEventListener('DOMContentLoaded', () => {
        if (!window.keyboardNav) {
            window.keyboardNav = new KeyboardNavigationManager();

            // Add ARIA labels after a short delay to let page render
            setTimeout(() => {
                window.keyboardNav.addAriaLabels();
            }, 500);
        }
    });
}
