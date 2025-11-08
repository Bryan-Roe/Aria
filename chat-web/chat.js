// Chat Web Client
const API_BASE = '/api/chat';

let messages = [];
let isProcessing = false;
let messageCounter = 0;
let currentProvider = 'auto';

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const newChatButton = document.getElementById('newChatButton');
const clearButton = document.getElementById('clearButton');
const exportButton = document.getElementById('exportButton');
const toggleThemeButton = document.getElementById('toggleThemeButton');
const providerInfo = document.getElementById('providerInfo');
const providerSelect = document.getElementById('providerSelect');
const messageCount = document.getElementById('messageCount');
const statusText = document.getElementById('statusText');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Configure marked.js for markdown rendering
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (err) {}
                }
                return hljs.highlightAuto(code).value;
            }
        });
    }

    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
    });

    // Keyboard shortcuts
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
        if (e.key === 'k' && e.ctrlKey) {
            e.preventDefault();
            newChat();
        }
    });

    sendButton.addEventListener('click', sendMessage);
    newChatButton.addEventListener('click', newChat);
    clearButton.addEventListener('click', clearChat);
    exportButton.addEventListener('click', exportChat);
    toggleThemeButton.addEventListener('click', toggleTheme);
    
    providerSelect.addEventListener('change', (e) => {
        currentProvider = e.target.value;
        updateStatus(`Provider changed to ${currentProvider}`);
    });

    // Load saved conversations
    loadFromStorage();
    
    // Focus input
    messageInput.focus();
});

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || isProcessing) return;

    // Add user message to UI
    addMessage('user', text);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    messageInput.disabled = true;
    sendButton.disabled = true;
    isProcessing = true;
    updateStatus('Sending...');

    // Add to messages array
    messages.push({ role: 'user', content: text });
    updateMessageCount();

    // Show typing indicator
    const typingIndicator = showTypingIndicator();

    try {
        // Call API
        const response = await fetch(API_BASE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: messages,
                provider: currentProvider,
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Remove typing indicator
        typingIndicator.remove();

        // Add assistant response with markdown rendering
        const assistantMessage = data.response || 'No response received.';
        addMessage('assistant', assistantMessage, true);
        messages.push({ role: 'assistant', content: assistantMessage });
        updateMessageCount();

        // Update provider info if available
        if (data.provider) {
            providerInfo.textContent = `${data.provider} - ${data.model || 'default'}`;
        }

        updateStatus('Ready');
        saveToStorage();

    } catch (error) {
        console.error('Error:', error);
        typingIndicator.remove();
        addMessage('system', `Error: ${error.message}. The chat service may be unavailable.`);
        updateStatus('Error');
    } finally {
        messageInput.disabled = false;
        sendButton.disabled = false;
        isProcessing = false;
        messageInput.focus();
    }
}

function addMessage(role, content, useMarkdown = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (useMarkdown && typeof marked !== 'undefined' && role === 'assistant') {
        // Render markdown
        contentDiv.innerHTML = marked.parse(content);
        
        // Add copy buttons to code blocks
        const codeBlocks = contentDiv.querySelectorAll('pre');
        codeBlocks.forEach(block => {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-button';
            copyBtn.textContent = 'Copy';
            copyBtn.onclick = () => {
                const code = block.querySelector('code')?.textContent || block.textContent;
                navigator.clipboard.writeText(code).then(() => {
                    copyBtn.textContent = 'Copied!';
                    setTimeout(() => copyBtn.textContent = 'Copy', 2000);
                });
            };
            block.style.position = 'relative';
            block.appendChild(copyBtn);
        });
    } else {
        contentDiv.textContent = content;
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    messageCounter++;
    return messageDiv;
}

function showTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message assistant';
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator active';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    
    indicatorDiv.appendChild(typingDiv);
    chatMessages.appendChild(indicatorDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return indicatorDiv;
}

function newChat() {
    if (messages.length > 0 && !confirm('Start a new conversation? Current chat will be lost.')) {
        return;
    }
    messages = [];
    messageCounter = 0;
    clearChat();
    addMessage('system', 'New conversation started. How can I help you?');
    updateMessageCount();
    saveToStorage();
}

function clearChat() {
    // Keep only system messages
    const systemMessages = Array.from(chatMessages.querySelectorAll('.message.system'));
    chatMessages.innerHTML = '';
    
    // Add back first system message or create new one
    if (systemMessages.length === 0) {
        addMessage('system', 'Chat cleared. Type a message to continue.');
    } else {
        chatMessages.appendChild(systemMessages[0]);
    }
    messageCounter = systemMessages.length;
    updateMessageCount();
}

function exportChat() {
    if (messages.length === 0) {
        alert('No messages to export');
        return;
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `chat-export-${timestamp}.json`;
    
    const exportData = {
        timestamp: new Date().toISOString(),
        provider: currentProvider,
        messageCount: messages.length,
        messages: messages
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    
    updateStatus(`Exported ${messages.length} messages`);
}

function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    toggleThemeButton.textContent = isDark ? '☀️ Light' : '🌓 Dark';
}

function updateMessageCount() {
    const userMessages = messages.filter(m => m.role === 'user').length;
    messageCount.textContent = userMessages;
}

function updateStatus(text) {
    statusText.textContent = text;
    setTimeout(() => {
        if (statusText.textContent === text) {
            statusText.textContent = 'Ready';
        }
    }, 3000);
}

function saveToStorage() {
    try {
        localStorage.setItem('chatMessages', JSON.stringify(messages));
        localStorage.setItem('chatProvider', currentProvider);
    } catch (e) {
        console.error('Failed to save to storage:', e);
    }
}

function loadFromStorage() {
    try {
        const saved = localStorage.getItem('chatMessages');
        const savedProvider = localStorage.getItem('chatProvider');
        const savedTheme = localStorage.getItem('theme');
        
        if (savedProvider) {
            currentProvider = savedProvider;
            providerSelect.value = savedProvider;
        }
        
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            toggleThemeButton.textContent = '☀️ Light';
        }
        
        if (saved) {
            messages = JSON.parse(saved);
            // Restore messages to UI
            messages.forEach(msg => {
                if (msg.role !== 'system') {
                    addMessage(msg.role, msg.content, msg.role === 'assistant');
                }
            });
            updateMessageCount();
        }
    } catch (e) {
        console.error('Failed to load from storage:', e);
    }
}
