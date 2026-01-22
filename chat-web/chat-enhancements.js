// Enhanced Chat Interface Features
// Theme toggle, typing indicators, reactions, voice input, export, mobile optimizations

// ============================================
// THEME SYSTEM
// ============================================

let currentTheme = localStorage.getItem('chat-theme') || 'light';

const themes = {
    light: {
        '--bg-primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
        '--bg-chat': 'rgba(255, 255, 255, 0.98)',
        '--bg-message-user': 'linear-gradient(135deg, #667eea, #764ba2)',
        '--bg-message-ai': '#f5f5f5',
        '--text-primary': '#333',
        '--text-secondary': '#666',
        '--text-message-user': '#fff',
        '--text-message-ai': '#333',
        '--border-color': 'rgba(0,0,0,0.1)',
        '--shadow': '0 15px 40px rgba(0, 0, 0, 0.2)',
        '--input-bg': '#fff',
        '--button-bg': '#667eea'
    },
    dark: {
        '--bg-primary': 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        '--bg-chat': 'rgba(30, 30, 46, 0.98)',
        '--bg-message-user': 'linear-gradient(135deg, #667eea, #764ba2)',
        '--bg-message-ai': '#2a2a3e',
        '--text-primary': '#e0e0e0',
        '--text-secondary': '#b0b0b0',
        '--text-message-user': '#fff',
        '--text-message-ai': '#e0e0e0',
        '--border-color': 'rgba(255,255,255,0.1)',
        '--shadow': '0 15px 40px rgba(0, 0, 0, 0.5)',
        '--input-bg': '#2a2a3e',
        '--button-bg': '#667eea'
    },
    ocean: {
        '--bg-primary': 'linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #13547a 100%)',
        '--bg-chat': 'rgba(240, 252, 255, 0.98)',
        '--bg-message-user': 'linear-gradient(135deg, #0093E9, #80D0C7)',
        '--bg-message-ai': '#e0f7fa',
        '--text-primary': '#004d61',
        '--text-secondary': '#006778',
        '--text-message-user': '#fff',
        '--text-message-ai': '#004d61',
        '--border-color': 'rgba(0,147,233,0.2)',
        '--shadow': '0 15px 40px rgba(0, 147, 233, 0.3)',
        '--input-bg': '#e0f7fa',
        '--button-bg': '#0093E9'
    },
    sunset: {
        '--bg-primary': 'linear-gradient(135deg, #fa709a 0%, #fee140 50%, #ff6b6b 100%)',
        '--bg-chat': 'rgba(255, 250, 245, 0.98)',
        '--bg-message-user': 'linear-gradient(135deg, #fa709a, #fee140)',
        '--bg-message-ai': '#fff5e6',
        '--text-primary': '#5a2e1f',
        '--text-secondary': '#8b4513',
        '--text-message-user': '#fff',
        '--text-message-ai': '#5a2e1f',
        '--border-color': 'rgba(250,112,154,0.2)',
        '--shadow': '0 15px 40px rgba(250, 112, 154, 0.3)',
        '--input-bg': '#fff5e6',
        '--button-bg': '#fa709a'
    }
};

function applyTheme(themeName) {
    const theme = themes[themeName];
    if (!theme) return;
    
    Object.entries(theme).forEach(([property, value]) => {
        document.documentElement.style.setProperty(property, value);
    });
    
    currentTheme = themeName;
    localStorage.setItem('chat-theme', themeName);
    
    // Update body background
    document.body.style.background = theme['--bg-primary'];
    document.body.style.backgroundSize = '200% 200%';
    
    addNotification(`🎨 Theme changed to ${themeName}`, 'success');
}

function cycleTheme() {
    const themeKeys = Object.keys(themes);
    const currentIndex = themeKeys.indexOf(currentTheme);
    const nextIndex = (currentIndex + 1) % themeKeys.length;
    applyTheme(themeKeys[nextIndex]);
}

// ============================================
// TYPING INDICATOR
// ============================================

function showTypingIndicator() {
    const existingIndicator = document.getElementById('typing-indicator');
    if (existingIndicator) return;
    
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'message ai-message typing-indicator';
    indicator.innerHTML = `
        <div class="message-content">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
    `;
    
    const messagesDiv = document.getElementById('messages');
    messagesDiv.appendChild(indicator);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// ============================================
// MESSAGE REACTIONS
// ============================================

const reactions = ['👍', '❤️', '😂', '🎉', '🤔', '👏', '🔥', '✨'];

function addReactionButtons(messageElement) {
    const reactionBar = document.createElement('div');
    reactionBar.className = 'reaction-bar';
    reactionBar.style.cssText = `
        display: none;
        gap: 5px;
        margin-top: 5px;
        flex-wrap: wrap;
    `;
    
    reactions.forEach(emoji => {
        const btn = document.createElement('button');
        btn.className = 'reaction-btn';
        btn.textContent = emoji;
        btn.onclick = () => addReaction(messageElement, emoji);
        reactionBar.appendChild(btn);
    });
    
    messageElement.appendChild(reactionBar);
    
    // Show reactions on hover
    messageElement.addEventListener('mouseenter', () => {
        reactionBar.style.display = 'flex';
    });
    messageElement.addEventListener('mouseleave', () => {
        reactionBar.style.display = 'none';
    });
}

function addReaction(messageElement, emoji) {
    let reactionsContainer = messageElement.querySelector('.reactions-display');
    if (!reactionsContainer) {
        reactionsContainer = document.createElement('div');
        reactionsContainer.className = 'reactions-display';
        reactionsContainer.style.cssText = `
            display: flex;
            gap: 5px;
            margin-top: 8px;
            flex-wrap: wrap;
        `;
        messageElement.appendChild(reactionsContainer);
    }
    
    // Check if reaction already exists
    const existing = Array.from(reactionsContainer.children).find(
        r => r.textContent.startsWith(emoji)
    );
    
    if (existing) {
        // Increment count
        const match = existing.textContent.match(/\d+/);
        const count = match ? parseInt(match[0]) + 1 : 2;
        existing.textContent = `${emoji} ${count}`;
    } else {
        // Add new reaction
        const reactionBubble = document.createElement('span');
        reactionBubble.className = 'reaction-bubble';
        reactionBubble.textContent = emoji;
        reactionBubble.style.cssText = `
            background: rgba(102, 126, 234, 0.1);
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        `;
        reactionBubble.onclick = () => reactionBubble.remove();
        reactionsContainer.appendChild(reactionBubble);
    }
}

// ============================================
// VOICE INPUT
// ============================================

let voiceRecognition = null;
let isRecording = false;

function setupVoiceInput() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.log('Voice recognition not supported');
        return false;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    voiceRecognition = new SpeechRecognition();
    voiceRecognition.continuous = false;
    voiceRecognition.interimResults = true;
    voiceRecognition.lang = 'en-US';
    
    voiceRecognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join('');
        
        const input = document.getElementById('messageInput');
        if (input) {
            input.value = transcript;
        }
    };
    
    voiceRecognition.onend = () => {
        isRecording = false;
        updateVoiceButton();
    };
    
    voiceRecognition.onerror = (event) => {
        console.error('Voice recognition error:', event.error);
        isRecording = false;
        updateVoiceButton();
        addNotification('⚠️ Voice recognition error', 'error');
    };
    
    return true;
}

function toggleVoiceInput() {
    if (!voiceRecognition) {
        if (!setupVoiceInput()) {
            addNotification('⚠️ Voice input not supported', 'error');
            return;
        }
    }
    
    if (isRecording) {
        voiceRecognition.stop();
        isRecording = false;
        addNotification('🎤 Stopped recording', 'info');
    } else {
        try {
            voiceRecognition.start();
            isRecording = true;
            addNotification('🎤 Listening...', 'success');
        } catch (e) {
            console.error('Could not start voice recognition:', e);
            addNotification('⚠️ Could not start recording', 'error');
        }
    }
    
    updateVoiceButton();
}

function updateVoiceButton() {
    const btn = document.getElementById('voiceBtn');
    if (btn) {
        btn.textContent = isRecording ? '⏹️' : '🎤';
        btn.style.background = isRecording ? '#e74c3c' : 'var(--button-bg)';
    }
}

// ============================================
// EXPORT CHAT HISTORY
// ============================================

function exportChatHistory(format = 'json') {
    const messages = Array.from(document.querySelectorAll('.message')).map(msg => {
        const isUser = msg.classList.contains('user-message');
        const content = msg.querySelector('.message-content')?.textContent || '';
        const timestamp = msg.querySelector('.message-timestamp')?.textContent || new Date().toLocaleTimeString();
        
        return {
            role: isUser ? 'user' : 'assistant',
            content: content,
            timestamp: timestamp
        };
    });
    
    let data, filename, mimeType;
    
    if (format === 'json') {
        data = JSON.stringify(messages, null, 2);
        filename = `chat-history-${Date.now()}.json`;
        mimeType = 'application/json';
    } else if (format === 'markdown') {
        data = messages.map(msg => 
            `**${msg.role === 'user' ? 'You' : 'AI'}** (${msg.timestamp}):\n${msg.content}\n`
        ).join('\n---\n\n');
        filename = `chat-history-${Date.now()}.md`;
        mimeType = 'text/markdown';
    } else if (format === 'txt') {
        data = messages.map(msg => 
            `[${msg.timestamp}] ${msg.role === 'user' ? 'You' : 'AI'}: ${msg.content}`
        ).join('\n\n');
        filename = `chat-history-${Date.now()}.txt`;
        mimeType = 'text/plain';
    }
    
    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    addNotification(`💾 Chat exported as ${format.toUpperCase()}`, 'success');
}

// ============================================
// NOTIFICATION SYSTEM
// ============================================

function addNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out, fadeOut 0.3s ease-out 2.7s;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// ============================================
// MESSAGE SEARCH
// ============================================

function searchMessages(query) {
    const messages = document.querySelectorAll('.message');
    let count = 0;
    
    messages.forEach(msg => {
        const content = msg.querySelector('.message-content')?.textContent.toLowerCase() || '';
        if (content.includes(query.toLowerCase())) {
            msg.style.background = 'rgba(255, 235, 59, 0.3)';
            msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
            count++;
        } else {
            msg.style.background = '';
        }
    });
    
    addNotification(`Found ${count} message(s) matching "${query}"`, count > 0 ? 'success' : 'info');
}

// ============================================
// KEYBOARD SHORTCUTS
// ============================================

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K: Focus input
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('messageInput')?.focus();
        }
        
        // Ctrl/Cmd + E: Export chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            exportChatHistory('json');
        }
        
        // Ctrl/Cmd + T: Cycle theme
        if ((e.ctrlKey || e.metaKey) && e.key === 't') {
            e.preventDefault();
            cycleTheme();
        }
        
        // Ctrl/Cmd + F: Search messages
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const query = prompt('Search messages:');
            if (query) searchMessages(query);
        }
        
        // Ctrl/Cmd + /: Show shortcuts help
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            showShortcutsHelp();
        }
    });
}

function showShortcutsHelp() {
    const help = `
Keyboard Shortcuts:
• Ctrl/Cmd + K: Focus input
• Ctrl/Cmd + E: Export chat
• Ctrl/Cmd + T: Cycle theme
• Ctrl/Cmd + F: Search messages
• Ctrl/Cmd + /: Show this help
    `.trim();
    
    addNotification(help, 'info');
    setTimeout(() => {
        // Keep visible longer for help text
    }, 5000);
}

// ============================================
// MOBILE OPTIMIZATIONS
// ============================================

function setupMobileOptimizations() {
    // Detect mobile
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        document.body.classList.add('mobile');
        
        // Prevent zoom on input focus
        const metaViewport = document.querySelector('meta[name=viewport]');
        if (metaViewport) {
            metaViewport.content = 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no';
        }
        
        // Add touch-friendly sizing
        document.documentElement.style.setProperty('--touch-target-size', '48px');
        
        // Handle keyboard appearance
        window.addEventListener('resize', () => {
            const chatContainer = document.querySelector('.chat-container');
            if (chatContainer && window.innerHeight < 500) {
                chatContainer.style.maxHeight = `${window.innerHeight - 20}px`;
            }
        });
    }
}

// ============================================
// ENHANCED STYLES
// ============================================

function injectEnhancedStyles() {
    const style = document.createElement('style');
    style.textContent = `
        :root {
            ${Object.entries(themes.light).map(([k, v]) => `${k}: ${v};`).join('\n            ')}
        }
        
        .typing-indicator {
            animation: fadeIn 0.3s ease-out;
        }
        
        .typing-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: var(--text-secondary);
            border-radius: 50%;
            margin: 0 2px;
            animation: typing-bounce 1.4s ease-in-out infinite;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing-bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        
        .reaction-btn {
            background: transparent;
            border: 1px solid var(--border-color);
            border-radius: 50%;
            width: 32px;
            height: 32px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .reaction-btn:hover {
            transform: scale(1.2);
            background: rgba(102, 126, 234, 0.1);
        }
        
        .reaction-bubble:hover {
            transform: scale(1.1);
            background: rgba(102, 126, 234, 0.2) !important;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .chat-container {
                width: 100% !important;
                max-width: 100% !important;
                bottom: 0 !important;
                border-radius: 20px 20px 0 0 !important;
                max-height: 90vh !important;
            }
            
            .message {
                font-size: 14px !important;
            }
            
            button, .reaction-btn {
                min-height: var(--touch-target-size, 44px);
                min-width: var(--touch-target-size, 44px);
            }
        }
    `;
    document.head.appendChild(style);
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    injectEnhancedStyles();
    setupKeyboardShortcuts();
    setupMobileOptimizations();
    applyTheme(currentTheme);
    
    // Add reaction buttons to existing messages
    document.querySelectorAll('.message').forEach(addReactionButtons);
    
    // Observe new messages and add reaction buttons
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.classList && node.classList.contains('message')) {
                    addReactionButtons(node);
                }
            });
        });
    });
    
    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
        observer.observe(messagesContainer, { childList: true });
    }
    
    console.log('✨ Chat enhancements loaded!');
    console.log('💡 Try: Ctrl+T (theme), Ctrl+E (export), Hover messages for reactions');
});

// Export functions for use in main chat script
window.chatEnhancements = {
    showTypingIndicator,
    hideTypingIndicator,
    exportChatHistory,
    cycleTheme,
    toggleVoiceInput,
    searchMessages,
    addNotification
};
