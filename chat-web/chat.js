// Chat Web Client - Version 2024-11-15 18:31
console.log('chat.js loaded - v2024-11-15-18:31 - Provider: auto-detect only');
const API_BASE = '/api/chat';
const STREAM_API = '/api/chat/stream';
const STATUS_API = '/api/ai/status';

let messages = [];
let isProcessing = false;
let messageCounter = 0;
let currentProvider = 'auto'; // Always use auto-detect for best available
let systemStatus = null;
let retryCount = 0;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;
let streamEnabled = true;
let temperature = 0.7;
let maxOutputTokens = 1024;
let systemPrompt = '';
let activeAbortController = null;

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const cancelStreamBtn = document.getElementById('cancelStreamBtn');
const newChatButton = document.getElementById('newChatButton');
const clearButton = document.getElementById('clearButton');
const exportButton = document.getElementById('exportButton');
const importButton = document.getElementById('importButton');
const toggleThemeButton = document.getElementById('toggleThemeButton');
const providerInfo = document.getElementById('providerInfo');
const messageCount = document.getElementById('messageCount');
const statusText = document.getElementById('statusText');
const streamToggle = document.getElementById('streamToggle');
const tempSlider = document.getElementById('tempSlider');
const tempValue = document.getElementById('tempValue');
const maxTokensInput = document.getElementById('maxTokensInput');
const toggleSystemButton = document.getElementById('toggleSystemButton');
const systemPromptBox = document.getElementById('systemPromptBox');
const systemPromptInput = document.getElementById('systemPromptInput');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
        if (cancelStreamBtn) {
            cancelStreamBtn.addEventListener('click', function() {
                if (activeAbortController) {
                    activeAbortController.abort();
                    updateStatus('Streaming cancelled');
                }
                cancelStreamBtn.style.display = 'none';
            });
        }
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
    clearButton.addEventListener('click', () => clearChat(false));
    exportButton.addEventListener('click', exportChat);
    importButton.addEventListener('click', importChat);
    toggleThemeButton.addEventListener('click', toggleTheme);
    streamToggle.addEventListener('change', (e) => {
        streamEnabled = !!e.target.checked;
        saveToStorage();
    });
    tempSlider.addEventListener('input', (e) => {
        temperature = parseFloat(e.target.value);
        tempValue.textContent = temperature.toFixed(2);
    });
    tempSlider.addEventListener('change', () => saveToStorage());
    maxTokensInput.addEventListener('change', (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
            maxOutputTokens = Math.max(64, Math.min(40960, val));
            e.target.value = String(maxOutputTokens);
            saveToStorage();
        }
    });
    toggleSystemButton.addEventListener('click', () => {
        const show = systemPromptBox.style.display !== 'block';
        systemPromptBox.style.display = show ? 'block' : 'none';
    });
    systemPromptInput.addEventListener('input', (e) => {
        systemPrompt = e.target.value;
        saveToStorage();
    });

    // Load saved conversations and settings
    loadFromStorage();
    
    // Focus input
    messageInput.focus();

    // Fetch system status on load
    fetchSystemStatus();
});

async function fetchSystemStatus() {
    try {
        updateStatus('Checking system status...');
        const response = await fetch(STATUS_API);
        if (response.ok) {
            systemStatus = await response.json();
            updateStatusFromSystem();
        }
    } catch (error) {
        console.warn('Status check failed:', error);
        updateStatus('Status check unavailable');
    }
}

function updateStatusFromSystem() {
    if (!systemStatus) return;

    // Update provider info with actual detected provider
    const provider = systemStatus.active_provider || 'local';
    const model = systemStatus.model || 'default';

    // Show success message if everything looks good
    if (systemStatus.status === 'ok') {
        updateStatus(`Ready - ${provider} (${model})`);
        providerInfo.textContent = `${provider} - ${model}`;
    }
}

async function sendMessage() {
    console.log('sendMessage() called');
    console.log('- messageInput.value:', messageInput.value);
    console.log('- isProcessing:', isProcessing);
    console.log('- sendButton.disabled:', sendButton.disabled);
    
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
        // Choose streaming or one-shot
        if (streamEnabled) {
            if (cancelStreamBtn) cancelStreamBtn.style.display = 'inline-block';
            await streamResponse(typingIndicator);
        } else {
            await oneShotResponse(typingIndicator);
        }
    } catch (error) {
        console.error('Error:', error);
        typingIndicator.remove();
        
        // Attempt retry if within limits
        if (retryCount < MAX_RETRIES && error.message.includes('HTTP')) {
            retryCount++;
            const delay = RETRY_DELAY * Math.pow(2, retryCount - 1);
            addMessage('system', `⚠️ Request failed. Retrying in ${delay/1000}s... (${retryCount}/${MAX_RETRIES})`);
            updateStatus(`Retrying ${retryCount}/${MAX_RETRIES}...`);
            
            setTimeout(() => {
                // Re-send by simulating button click
                messages.pop(); // Remove the failed user message
                messageInput.value = text; // Restore input
                messageInput.disabled = false;
                sendButton.disabled = false;
                isProcessing = false;
                sendMessage();
            }, delay);
        } else {
            // Max retries exceeded or non-retryable error
            retryCount = 0;
            const errorMsg = error.message.includes('NetworkError') || error.message.includes('Failed to fetch')
                ? '❌ Network error. Please check your connection and ensure the Functions host is running.'
                : `❌ Error: ${error.message}`;
            addMessage('system', errorMsg);
            updateStatus('Error - check console');
            messageInput.disabled = false;
            sendButton.disabled = false;
            isProcessing = false;
            messageInput.focus();
        }
    }
}

async function oneShotResponse(typingIndicator) {
    const response = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            messages: messages,
            provider: 'auto',
            temperature: temperature,
            max_output_tokens: maxOutputTokens,
            system_prompt: systemPrompt,
        })
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    retryCount = 0;
    typingIndicator.remove();
    const assistantMessage = data.response || 'No response received.';
    addMessage('assistant', assistantMessage, true);
    messages.push({ role: 'assistant', content: assistantMessage });
    updateMessageCount();
    if (data.provider) {
        providerInfo.textContent = `${data.provider} - ${data.model || 'default'}`;
    }
    updateStatus('Ready');
    saveToStorage();
    messageInput.disabled = false;
    sendButton.disabled = false;
    isProcessing = false;
    messageInput.focus();
}

async function streamResponse(typingIndicator) {
    let streamAborted = false;
    // Prepare assistant message container to update incrementally
    const assistantDiv = document.createElement('div');
    assistantDiv.className = 'message assistant';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = '';
    assistantDiv.appendChild(contentDiv);
    chatMessages.appendChild(assistantDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    activeAbortController = new AbortController();
    
    try {
        const response = await fetch(STREAM_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: messages,
                provider: 'auto',
                temperature: temperature,
                max_output_tokens: maxOutputTokens,
                system_prompt: systemPrompt,
            }),
            signal: activeAbortController.signal
        });
        
        if (!response.ok || !response.body) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Remove typing indicator as soon as stream starts
        typingIndicator.remove();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullText = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            // Parse SSE chunks split by double newlines
            let idx;
            while ((idx = buffer.indexOf('\n\n')) !== -1) {
                const chunk = buffer.slice(0, idx);
                buffer = buffer.slice(idx + 2);
                if (chunk.startsWith('data:')) {
                    const dataJson = chunk.slice(5).trim();
                    if (!dataJson) continue;
                    try {
                        const obj = JSON.parse(dataJson);
                        const delta = obj.delta || '';
                        if (delta) {
                            fullText += delta;
                            // Update plain text during stream for speed
                            contentDiv.textContent = fullText;
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }
                    } catch {}
                }
            }
        }

        // Render final markdown for the whole message
        if (typeof marked !== 'undefined') {
            contentDiv.innerHTML = marked.parse(fullText || '');
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
        }

        // Push to messages history
        messages.push({ role: 'assistant', content: fullText });
        updateMessageCount();
        retryCount = 0;
        updateStatus('Ready');
        saveToStorage();
    } catch (error) {
        typingIndicator.remove();
        assistantDiv.remove();
        
        if (error.name === 'AbortError') {
            streamAborted = true;
            addMessage('system', '❌ Streaming cancelled by user.');
            updateStatus('Cancelled');
        } else {
            throw error; // Re-throw to be handled by sendMessage
        }
    } finally {
        if (cancelStreamBtn) cancelStreamBtn.style.display = 'none';
        activeAbortController = null;
        messageInput.disabled = false;
        sendButton.disabled = false;
        isProcessing = false;
        messageInput.focus();
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
    if (messages.length > 0 && !confirm('Start a new chat? Current conversation will be cleared.')) {
        return;
    }
    messages = [];
    messageCounter = 0;
    clearChat();
    addMessage('system', 'New conversation started. How can I help you?');
    updateMessageCount();
    saveToStorage();
}

function clearChat(preserveMessages = false) {
    if (!preserveMessages) {
        messages = [];
        messageCounter = 0;
    }
    chatMessages.innerHTML = '';
    addMessage('system', 'Chat cleared. Type a message to continue.');
    messageCounter = 1;
    updateMessageCount();
    saveToStorage();
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

function importChat() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                if (data.messages && Array.isArray(data.messages)) {
                    const imported = data.messages;
                    clearChat(true); // reset UI but preserve current messages until reassigned
                    messages = imported;
                    // Restore messages to UI
                    messages.forEach(msg => {
                        if (msg.role !== 'system') {
                            addMessage(msg.role, msg.content, msg.role === 'assistant');
                        }
                    });
                    updateMessageCount();
                    saveToStorage();
                    updateStatus(`Imported ${messages.length} messages`);
                } else {
                    throw new Error('Invalid chat export format');
                }
            } catch (error) {
                alert(`Failed to import: ${error.message}`);
            }
        };
        reader.readAsText(file);
    };
    input.click();
}

function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    toggleThemeButton.textContent = isDark ? '☀️ Light' : '🌙 Dark';
}

function updateMessageCount() {
    const userMessages = messages.filter(m => m.role === 'user').length;
    messageCount.textContent = userMessages;
}

function updateStatus(text) {
    statusText.textContent = text;
    if (text.includes('Ready') || text.includes('ok')) {
        statusText.style.color = '#28a745';
    } else if (text.includes('Error') || text.includes('❌')) {
        statusText.style.color = '#dc3545';
    } else if (text.includes('⚠️')) {
        statusText.style.color = '#ffc107';
    } else {
        statusText.style.color = '';
    }
    
    setTimeout(() => {
        if (statusText.textContent === text) {
            statusText.textContent = 'Ready';
            statusText.style.color = '';
        }
    }, 3000);
}

function saveToStorage() {
    try {
        localStorage.setItem('chatMessages', JSON.stringify(messages));
        localStorage.setItem('chatStream', streamEnabled ? '1' : '0');
        localStorage.setItem('chatTemp', String(temperature));
        localStorage.setItem('chatMaxTokens', String(maxOutputTokens));
        localStorage.setItem('chatSystemPrompt', systemPrompt || '');
    } catch (e) {
        console.error('Failed to save to storage:', e);
    }
}

function loadFromStorage() {
    try {
        const saved = localStorage.getItem('chatMessages');
        const savedTheme = localStorage.getItem('theme');
        const savedStream = localStorage.getItem('chatStream');
        const savedTemp = localStorage.getItem('chatTemp');
        const savedMax = localStorage.getItem('chatMaxTokens');
        const savedSys = localStorage.getItem('chatSystemPrompt');
        
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            toggleThemeButton.textContent = '☀️ Light';
                } else {
                    toggleThemeButton.textContent = '🌙 Dark';
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

        // Restore settings
        streamEnabled = savedStream === '1';
        streamToggle.checked = streamEnabled;
        if (savedTemp) {
            temperature = parseFloat(savedTemp);
            if (!isNaN(temperature)) {
                tempSlider.value = String(temperature);
                tempValue.textContent = temperature.toFixed(2);
            }
        }
        if (savedMax) {
            const v = parseInt(savedMax, 10);
            if (!isNaN(v)) {
                maxOutputTokens = v;
                maxTokensInput.value = String(v);
            }
        }
        if (savedSys) {
            systemPrompt = savedSys;
            systemPromptInput.value = systemPrompt;
        }
    } catch (e) {
        console.error('Failed to load from storage:', e);
    }
}
