// Chat Web Client - Version 2025-11-21 - QAI Backend
// Encapsulate chat client in an IIFE to avoid leaking globals when embedded
console.log('chat.js loaded - v2025-11-21-qai - Provider: QAI auto-detect with quantum mode');
(function window_qai_chat_client() {
const AI_BASE = '';
const API_BASE = `/api/chat`;
const STREAM_API = `/api/chat/stream`;
const STATUS_API = `/api/ai/status`;
const QUANTUM_CLASSIFY_API = '/api/quantum/classify';
const QUANTUM_CIRCUIT_API = '/api/quantum/circuit';
const QUANTUM_INFO_API = '/api/quantum/info';
const VISION_INFER_API = '/api/vision/infer';
const IMAGE_GEN_API = '/api/image/generate';

let messages = [];
let isProcessing = false;
let messageCounter = 0;
let currentProvider = 'auto'; // Always use auto-detect for best available
let quantumMode = false; // Quantum enhancement toggle
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
const quantumModeButton = document.getElementById('quantumModeButton');
const quantumPanel = document.getElementById('quantumPanel');
const quantumPanelClose = document.getElementById('quantumPanelClose');
const quantumIndicator = document.getElementById('quantumIndicator');
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
const visionUploadButton = document.getElementById('visionUploadButton');
const visionImageInput = document.getElementById('visionImageInput');
const visionPreview = document.getElementById('visionPreview');
const visionClearButton = document.getElementById('visionClearButton');

// Vision state
let uploadedImage = null;
let uploadedImageBase64 = null;

// Aria avatar state
let ariaAvatarGenerated = false;
let ariaAvatarUrl = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
        // When the Aria interactive page embeds chat, it provides its own
        // send/receive wiring and should avoid double-wiring the controls
        // in this script. A page can opt-in by setting window.ARIA_EMBEDDED=true
        if (window && window.ARIA_EMBEDDED) {
            console.log('chat.js: ARIA_EMBEDDED detected — skipping default UI wiring');
            return;
        }
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
        if (e.key === 'k' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            newChat();
        }
    });

    sendButton.addEventListener('click', sendMessage);

    // Vision upload handlers
    if (visionUploadButton) {
        visionUploadButton.addEventListener('click', () => {
            visionImageInput.click();
        });
    }

    if (visionImageInput) {
        visionImageInput.addEventListener('change', handleImageUpload);
    }

    if (visionClearButton) {
        visionClearButton.addEventListener('click', clearVisionUpload);
    }

    // Aria avatar handlers
    const ariaAvatarContainer = document.getElementById('ariaAvatarContainer');
    const ariaAvatarClose = document.getElementById('ariaAvatarClose');
    const ariaAvatarRegenerate = document.getElementById('ariaAvatarRegenerate');

    if (ariaAvatarClose) {
        ariaAvatarClose.addEventListener('click', hideAriaAvatar);
    }

    if (ariaAvatarRegenerate) {
        ariaAvatarRegenerate.addEventListener('click', () => generateAriaAvatar(true));
    }

    // Auto-generate Aria avatar on page load (after 2 seconds)
    setTimeout(() => {
        if (!ariaAvatarGenerated) {
            generateAriaAvatar(false);
        }
    }, 2000);

    newChatButton.addEventListener('click', () => {
        console.log('New Chat button clicked');
        newChat();
    });
    clearButton.addEventListener('click', () => {
        console.log('Clear button clicked');
        clearChat(false);
    });
    exportButton.addEventListener('click', exportChat);
    importButton.addEventListener('click', importChat);
    toggleThemeButton.addEventListener('click', toggleTheme);
    quantumModeButton.addEventListener('click', toggleQuantumMode);
    if (quantumPanelClose) {
        quantumPanelClose.addEventListener('click', () => {
            quantumPanel.style.display = 'none';
        });
    }
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
        updateStatus('Checking backend...');
        const response = await fetch(STATUS_API);
        if (response.ok) {
            const data = await response.json();
            systemStatus = { status: 'ok', data };
            updateStatusFromSystem();
        }
    } catch (error) {
        console.warn('Backend not available:', error);
        updateStatus('Backend not responding');
    }
}

function updateStatusFromSystem() {
    if (!systemStatus) return;

    // Show success message if everything looks good
    if (systemStatus.status === 'ok') {
        const provider = systemStatus.data?.active_provider || 'local';
        const model = systemStatus.data?.model || 'unknown';
        updateStatus(`Ready - ${provider.toUpperCase()}`);
        providerInfo.textContent = `${provider.toUpperCase()} - ${model}`;
    }
}

async function sendMessage() {
    console.log('sendMessage() called');
    console.log('- messageInput.value:', messageInput.value);
    console.log('- isProcessing:', isProcessing);
    console.log('- sendButton.disabled:', sendButton.disabled);
    console.log('- quantumMode:', quantumMode);

    const text = messageInput.value.trim();
    if (!text || isProcessing) return;

    // Perform quantum analysis if enabled
    if (quantumMode) {
        updateStatus('Performing quantum analysis...');
        await performQuantumAnalysis(text);
    }

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
                ? '❌ Network error. Please ensure QAI backend is running on http://localhost:7071'
                : `❌ Error: ${error.message}`;
            addMessage('system', errorMsg);
            console.error('Full error details:', error);
            updateStatus('Error - check console');
            messageInput.disabled = false;
            sendButton.disabled = false;
            isProcessing = false;
            messageInput.focus();
        }
    }
}

async function oneShotResponse(typingIndicator) {
    // Prepare messages with system prompt if provided
    const apiMessages = systemPrompt ?
        [{ role: 'system', content: systemPrompt }, ...messages] :
        messages;

    console.log('Sending non-streaming request to:', API_BASE);
    console.log('Request body:', { messages: apiMessages, temperature, max_tokens: maxOutputTokens });

    const response = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            messages: apiMessages,
            temperature: temperature,
            max_tokens: maxOutputTokens,
            stream: false
        })
    });

    console.log('Response status:', response.status, response.statusText);

    if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Response data:', data);

    retryCount = 0;
    typingIndicator.remove();
    // Handle QAI backend response format
    const assistantMessage = data.response || data.choices?.[0]?.message?.content || 'No response received.';
    console.log('Assistant message:', assistantMessage);

    addMessage('assistant', assistantMessage, true);
    messages.push({ role: 'assistant', content: assistantMessage });
    updateMessageCount();
    if (data.provider && data.model) {
        providerInfo.textContent = `${data.provider.toUpperCase()} - ${data.model}`;
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

    // Prepare messages with system prompt if provided
    const apiMessages = systemPrompt ?
        [{ role: 'system', content: systemPrompt }, ...messages] :
        messages;

    console.log('Sending streaming request to:', STREAM_API);
    console.log('Request body:', { messages: apiMessages, temperature, max_tokens: maxOutputTokens, stream: true });

    try {
        const response = await fetch(STREAM_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: apiMessages,
                temperature: temperature,
                max_tokens: maxOutputTokens,
                stream: true
            }),
            signal: activeAbortController.signal
        });

        console.log('Stream response status:', response.status, response.statusText);

        if (!response.ok || !response.body) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Remove typing indicator as soon as stream starts
        typingIndicator.remove();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            // QAI backend sends plain text chunks, not SSE
            const chunk = decoder.decode(value, { stream: true });
            if (chunk) {
                console.log('Stream chunk:', chunk);
                fullText += chunk;
                // Update plain text during stream for speed
                contentDiv.textContent = fullText;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }

        // After stream completes, render as markdown
        if (fullText) {
            try {
                const rendered = marked.parse(fullText);
                contentDiv.innerHTML = rendered;
                // Highlight code blocks
                contentDiv.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                    addCopyButton(block.parentElement);
                });
            } catch (e) {
                console.error('Markdown render error:', e);
                contentDiv.textContent = fullText;
            }
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
    console.log('newChat() called');
    if (messages.length > 0 && !confirm('Start a new chat? Current conversation will be cleared.')) {
        console.log('User cancelled new chat');
        return;
    }
    messages = [];
    messageCounter = 0;
    isProcessing = false;
    chatMessages.innerHTML = '';
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.value = '';
    messageInput.focus();
    localStorage.setItem('chatMessages', JSON.stringify([]));
    addMessage('system', 'New conversation started. How can I help you?');
    updateMessageCount();
    updateStatus('Ready');
    saveToStorage();
    console.log('New chat complete');
}

function clearChat(preserveMessages = false) {
    console.log('clearChat() called, preserveMessages:', preserveMessages);
    if (!preserveMessages) {
        messages = [];
        messageCounter = 0;
        isProcessing = false;
        localStorage.setItem('chatMessages', JSON.stringify([]));
    }
    chatMessages.innerHTML = '';
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.value = '';
    messageInput.focus();
    addMessage('system', 'Chat cleared. Type a message to continue.');
    updateMessageCount();
    updateStatus('Ready');
    saveToStorage();
    console.log('Clear chat complete');
}

function exportChat() {
    if (messages.length === 0) {
        if (typeof showToast === 'function') showToast('No messages to export', 3000);
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
                if (typeof showToast === 'function') showToast(`Import failed: ${error.message}`, 4000);
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

// Aria AI Avatar functions
async function generateAriaAvatar(regenerate = false) {
    const ariaAvatarContainer = document.getElementById('ariaAvatarContainer');
    const ariaAvatarImage = document.getElementById('ariaAvatarImage');

    if (!regenerate && ariaAvatarGenerated) {
        ariaAvatarContainer.style.display = 'block';
        return;
    }

    updateStatus('🎨 Generating Aria\'s AI avatar...');

    try {
        // Use a more descriptive prompt for Aria's character
        const prompt = "Portrait of Aria, anime-style AI assistant character, purple gradient hair, cute anime girl, friendly expression, digital art, high quality, detailed, vibrant colors, soft lighting";

        const response = await fetch(IMAGE_GEN_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt,
                size: "512x512",
                style: "anime"
            })
        });

        if (!response.ok) {
            throw new Error(`Image generation failed: ${response.status}`);
        }

        const result = await response.json();

        if (result.image_url || result.image_data) {
            ariaAvatarUrl = result.image_url || `data:image/png;base64,${result.image_data}`;
            ariaAvatarImage.src = ariaAvatarUrl;
            ariaAvatarContainer.style.display = 'block';
            ariaAvatarGenerated = true;
            updateStatus('✅ Aria\'s avatar generated!');

            // Add a chat message from Aria about her new appearance
            if (regenerate) {
                addMessage('assistant', '✨ How do I look? I just got a fresh new appearance from the AI! 💜');
            }
        } else {
            throw new Error('No image data received');
        }
    } catch (error) {
        console.error('Avatar generation error:', error);
        updateStatus(`⚠️ Avatar generation unavailable: ${error.message}`);

        // Fallback: Use a placeholder or emoji-based avatar
        const ariaAvatarImage = document.getElementById('ariaAvatarImage');
        ariaAvatarImage.src = 'data:image/svg+xml,' + encodeURIComponent(`
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="250" viewBox="0 0 200 250">
                <defs>
                    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <rect width="200" height="250" fill="url(#grad)"/>
                <text x="100" y="125" font-size="80" text-anchor="middle" fill="white">👩‍💻</text>
                <text x="100" y="180" font-size="20" text-anchor="middle" fill="white" font-weight="bold">Aria</text>
                <text x="100" y="200" font-size="14" text-anchor="middle" fill="rgba(255,255,255,0.8)">AI Assistant</text>
            </svg>
        `);
        ariaAvatarContainer.style.display = 'block';
        ariaAvatarGenerated = true;
    }
}

function hideAriaAvatar() {
    const ariaAvatarContainer = document.getElementById('ariaAvatarContainer');
    ariaAvatarContainer.style.display = 'none';
    updateStatus('Avatar hidden');
}

// Vision upload handlers
async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        updateStatus('❌ Please select an image file');
        return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = async (e) => {
        uploadedImageBase64 = e.target.result.split(',')[1]; // Remove data:image/...;base64, prefix
        uploadedImage = file.name;

        // Show preview
        visionPreview.innerHTML = `
            <img src="${e.target.result}" alt="Preview">
            <div class="vision-preview-info">
                <span>${file.name}</span>
                <button id="visionClearButton">✕</button>
            </div>
        `;
        visionPreview.style.display = 'block';

        // Re-attach clear button listener
        document.getElementById('visionClearButton').addEventListener('click', clearVisionUpload);

        // Auto-analyze the image
        updateStatus('🔍 Analyzing image...');
        try {
            const response = await fetch(VISION_INFER_API, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: uploadedImageBase64 })
            });

            if (!response.ok) {
                throw new Error(`Vision API error: ${response.status}`);
            }

            const result = await response.json();

            // Add AI message with vision results
            const visionMessage = `🖼️ **Image Analysis**: ${file.name}\n\n` +
                `**Expression**: ${result.label} (${(result.confidence * 100).toFixed(1)}% confidence)\n\n` +
                `**All Scores**:\n${Object.entries(result.scores)
                    .sort((a, b) => b[1] - a[1])
                    .map(([label, score]) => `- ${label}: ${(score * 100).toFixed(1)}%`)
                    .join('\n')}`;

            addMessage('assistant', visionMessage);
            updateStatus('✅ Image analyzed successfully');
        } catch (error) {
            console.error('Vision inference error:', error);
            updateStatus(`❌ Vision error: ${error.message}`);
        }
    };

    reader.readAsDataURL(file);
}

function clearVisionUpload() {
    uploadedImage = null;
    uploadedImageBase64 = null;
    visionImageInput.value = '';
    visionPreview.style.display = 'none';
    visionPreview.innerHTML = '';
    updateStatus('Vision upload cleared');
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

// =============================================================================
// Quantum Mode Functions
// =============================================================================

function toggleQuantumMode() {
    quantumMode = !quantumMode;

    if (quantumMode) {
        quantumModeButton.textContent = '🔬 Quantum ON';
        quantumModeButton.classList.add('active');
        quantumIndicator.style.display = 'flex';
        quantumPanel.style.display = 'block';
        currentProvider = 'quantum';
        updateStatus('Quantum mode enabled');

        // Fetch quantum info
        fetchQuantumInfo();
    } else {
        quantumModeButton.textContent = '🔬 Quantum OFF';
        quantumModeButton.classList.remove('active');
        quantumIndicator.style.display = 'none';
        quantumPanel.style.display = 'none';
        currentProvider = 'auto';
        updateStatus('Quantum mode disabled');
    }

    saveToStorage();
}

async function fetchQuantumInfo() {
    try {
        const response = await fetch(QUANTUM_INFO_API);
        if (response.ok) {
            const data = await response.json();
            if (data.available) {
                updateStatus('Quantum backend ready');
            } else {
                updateStatus('Quantum backend unavailable - using classical fallback');
            }
        }
    } catch (error) {
        console.warn('Could not fetch quantum info:', error);
    }
}

async function performQuantumAnalysis(text) {
    if (!quantumMode) return null;

    try {
        // Convert text to features (simple hash-based approach)
        const features = textToFeatures(text);

        const response = await fetch(QUANTUM_CLASSIFY_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                features: features,
                n_qubits: 4,
                n_layers: 2
            })
        });

        if (!response.ok) {
            throw new Error(`Quantum API error: ${response.status}`);
        }

        const data = await response.json();

        // Update quantum panel
        document.getElementById('quantumClassification').textContent =
            data.classification.toUpperCase();
        document.getElementById('quantumConfidence').textContent =
            (data.confidence * 100).toFixed(1) + '%';
        document.getElementById('quantumQubits').textContent =
            data.quantum_state.n_qubits;
        document.getElementById('quantumLayers').textContent =
            data.quantum_state.n_layers;

        // Get circuit visualization
        await fetchCircuitVisualization(data.quantum_state.n_qubits, data.quantum_state.n_layers);

        return data;
    } catch (error) {
        console.error('Quantum analysis failed:', error);
        document.getElementById('quantumClassification').textContent = 'ERROR';
        return null;
    }
}

async function fetchCircuitVisualization(nQubits, nLayers) {
    try {
        const response = await fetch(QUANTUM_CIRCUIT_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                n_qubits: nQubits,
                n_layers: nLayers,
                entanglement: 'linear'
            })
        });

        if (response.ok) {
            const data = await response.json();
            const vizElement = document.querySelector('.circuit-display');
            if (vizElement) {
                vizElement.textContent = data.visualization;
            }
        }
    } catch (error) {
        console.error('Circuit visualization failed:', error);
    }
}

function textToFeatures(text) {
    // Simple feature extraction: convert text to numeric features
    // Using character codes and length statistics
    const features = [];
    const normalized = text.toLowerCase();

    // Add basic statistics
    features.push(normalized.length / 100.0);  // Normalized length
    features.push(normalized.split(' ').length / 50.0);  // Word count
    features.push(normalized.split('?').length / 10.0);  // Question marks
    features.push(normalized.split('!').length / 10.0);  // Exclamation marks

    // Add character distribution (simple hash)
    let sum = 0;
    for (let i = 0; i < Math.min(normalized.length, 20); i++) {
        sum += normalized.charCodeAt(i);
    }
    features.push((sum % 256) / 256.0);

    // Pad or truncate to 8 features
    while (features.length < 8) {
        features.push(0.0);
    }

    return features.slice(0, 8);
}

})();
