// QAI Control Center JavaScript

// Same-origin: the FastAPI service serves this UI, so use relative URLs.
// This works regardless of host/port (localhost, 0.0.0.0, remote, proxy).
const API_BASE = '';

// Global state
let currentProvider = 'auto';

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

/** Escape text for safe insertion into HTML (prevents XSS via innerHTML). */
function esc(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/** Fetch JSON with error handling; throws on non-2xx responses. */
async function fetchJSON(path, options) {
    const response = await fetch(`${API_BASE}${path}`, options);
    if (!response.ok) {
        let detail = response.statusText;
        try {
            const body = await response.json();
            detail = body.detail || body.error || detail;
        } catch (_) { /* ignore parse errors */ }
        throw new Error(`${response.status}: ${detail}`);
    }
    return response.json();
}

/** Toggle a button into/out of a loading state. */
function setLoading(btn, loading) {
    if (!btn) return;
    if (loading) {
        btn.classList.add('is-loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('is-loading');
        btn.disabled = false;
    }
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeTabs();
    initializeForms();
    restoreProvider();
    checkServiceStatus();
    loadDashboard();

    setInterval(checkServiceStatus, 30000);
});

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

function initializeTheme() {
    const stored = localStorage.getItem('qai-theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = stored || (prefersDark ? 'dark' : 'light');
    applyTheme(theme);

    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('qai-theme', next);
        });
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const toggle = document.getElementById('themeToggle');
    if (toggle) toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------

function initializeTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    const lastTab = localStorage.getItem('qai-tab');
    if (lastTab && document.getElementById(lastTab)) switchTab(lastTab);
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        const active = btn.dataset.tab === tabName;
        btn.classList.toggle('active', active);
        btn.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tabName);
    });
    localStorage.setItem('qai-tab', tabName);
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch (tabName) {
        case 'dashboard': loadDashboard(); break;
        case 'quantum': loadQuantumData(); break;
        case 'chat': loadChatData(); break;
        case 'training': loadTrainingData(); break;
    }
}

// ---------------------------------------------------------------------------
// Service Status
// ---------------------------------------------------------------------------

async function checkServiceStatus() {
    const indicator = document.getElementById('serviceStatus');
    const dot = indicator.querySelector('.status-dot');
    const text = indicator.querySelector('.status-text');
    try {
        const data = await fetchJSON('/health');
        const healthy = data.status === 'healthy';
        dot.classList.toggle('online', healthy);
        dot.classList.toggle('offline', !healthy);
        text.textContent = healthy ? 'Online' : 'Error';
    } catch (error) {
        dot.classList.remove('online');
        dot.classList.add('offline');
        text.textContent = 'Offline';
    }
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

async function loadDashboard() {
    try {
        const data = await fetchJSON('/status');

        document.getElementById('systemStatus').innerHTML = `
            <div class="status-item">
                <span class="status-label">Service</span>
                <span class="status-value success">${esc(data.service)}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Version</span>
                <span class="status-value">${esc(data.version)}</span>
            </div>
            ${statusRow('Quantum Enabled', data.quantum?.enabled)}
            ${statusRow('Chat Enabled', data.chat?.enabled)}
            ${statusRow('Training Enabled', data.training?.enabled)}
        `;

        const results = data.quantum?.recent_results || [];
        document.getElementById('recentActivity').innerHTML = results.length
            ? results.map(r => `
                <div class="result-item">
                    <strong>Quantum:</strong> ${esc(r.dataset)} —
                    <span class="accuracy">${formatPct(r.accuracy)}</span> accuracy
                    <br><small>${esc(r.backend)} · ${esc(r.timestamp)}</small>
                </div>`).join('')
            : emptyRow('No recent activity');

        addLog('Dashboard loaded successfully', 'success');
    } catch (error) {
        document.getElementById('systemStatus').innerHTML = emptyRow('Unable to load status');
        addLog(`Dashboard load error: ${error.message}`, 'error');
        toast(`Dashboard unavailable: ${error.message}`, 'error');
    }
}

// ---------------------------------------------------------------------------
// Quantum AI
// ---------------------------------------------------------------------------

async function loadQuantumData() {
    try {
        const datasets = await fetchJSON('/quantum/datasets');
        fillSelect('quantumDataset', (datasets || []).map(d => ({ value: d.name, label: d.name })));

        const status = await fetchJSON('/quantum/status');
        document.getElementById('quantumStatus').innerHTML = `
            <div class="status-item">
                <span class="status-label">Backend</span>
                <span class="status-value">${esc(status.backend)}</span>
            </div>
            ${statusRow('Azure Connected', status.azure_connected)}
            <div class="status-item">
                <span class="status-label">Available Backends</span>
                <span class="status-value">${esc((status.available_backends || []).length)}</span>
            </div>
        `;

        const results = status.recent_results || [];
        document.getElementById('quantumResults').innerHTML = results.length
            ? results.map(r => `
                <div class="result-item">
                    <strong>${esc(r.dataset)}</strong><br>
                    Accuracy: <span class="accuracy">${formatPct(r.accuracy)}</span><br>
                    <small>${esc(r.backend)} · ${esc(r.timestamp)}</small>
                </div>`).join('')
            : emptyRow('No results yet');

        document.getElementById('quantumAutorunJobs').innerHTML =
            emptyRow('Available jobs will appear here');

        addLog('Quantum data loaded', 'info');
    } catch (error) {
        addLog(`Quantum load error: ${error.message}`, 'error');
        toast(`Quantum data error: ${error.message}`, 'error');
    }
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

async function loadChatData() {
    try {
        const data = await fetchJSON('/chat/status');

        document.getElementById('chatProviders').innerHTML =
            Object.entries(data.providers || {}).map(([name, info]) => `
                <div class="status-item">
                    <span class="status-label">${esc(name.toUpperCase())}</span>
                    <span class="status-value ${info.available ? 'success' : 'error'}">
                        ${info.available ? '✓ Available' : '✗ Unavailable'}${info.cost ? ` (${esc(info.cost)})` : ''}
                    </span>
                </div>`).join('') || emptyRow('No providers');

        document.getElementById('chatStatus').innerHTML = `
            <div class="status-item">
                <span class="status-label">Default Provider</span>
                <span class="status-value">${esc(data.default_provider)}</span>
            </div>`;

        const convos = data.recent_conversations || [];
        document.getElementById('chatHistory').innerHTML = convos.length
            ? convos.map(c => `
                <div class="result-item">
                    <strong>${esc(c.file)}</strong><br>
                    ${esc(c.message_count)} messages<br>
                    <small>${esc(c.preview)}</small>
                </div>`).join('')
            : emptyRow('No conversations yet');

        addLog('Chat data loaded', 'info');
    } catch (error) {
        addLog(`Chat load error: ${error.message}`, 'error');
        toast(`Chat data error: ${error.message}`, 'error');
    }
}

// ---------------------------------------------------------------------------
// Training
// ---------------------------------------------------------------------------

async function loadTrainingData() {
    try {
        const datasets = await fetchJSON('/training/datasets');

        const chatOptions = (datasets.chat || []).map(ds => ({
            value: `../../datasets/chat/${ds}`, label: ds,
        }));
        fillSelect('loraDataset', chatOptions);

        const status = await fetchJSON('/training/status');

        document.getElementById('trainingStatus').innerHTML = `
            <div class="status-item">
                <span class="status-label">System</span>
                <span class="status-value success">Ready</span>
            </div>`;

        const adapter = status.lora_adapter || {};
        document.getElementById('loraAdapterStatus').innerHTML = adapter.available
            ? `
                <div class="status-item">
                    <span class="status-label">Status</span>
                    <span class="status-value success">✓ Available</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Model</span>
                    <span class="status-value">${esc(adapter.model || 'N/A')}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Rank</span>
                    <span class="status-value">${esc(adapter.rank || 'N/A')}</span>
                </div>`
            : emptyRow('No adapter trained yet');

        const jobs = await fetchJSON('/training/autotrain/jobs');
        fillSelect('autotrainJob', (jobs.jobs || []).map(j => ({ value: j, label: j })), 'Select job…');

        const autotrainJobs = status.orchestrators?.autotrain?.jobs || {};
        document.getElementById('autotrainStatus').innerHTML = Object.keys(autotrainJobs).length
            ? Object.entries(autotrainJobs).map(([name, job]) => `
                <div class="job-item">
                    <span><strong>${esc(name)}</strong> — ${esc(job.status || 'unknown')}</span>
                </div>`).join('')
            : emptyRow('No jobs run yet');

        document.getElementById('datasetList').innerHTML = `
            <h4>Quantum (${(datasets.quantum || []).length})</h4>
            <div class="dataset-grid">${(datasets.quantum || []).map(d => `<div class="dataset-item quantum">${esc(d)}</div>`).join('')}</div>
            <h4>Chat (${(datasets.chat || []).length})</h4>
            <div class="dataset-grid">${(datasets.chat || []).map(d => `<div class="dataset-item chat">${esc(d)}</div>`).join('')}</div>
            <h4>Vision (${(datasets.vision || []).length})</h4>
            <div class="dataset-grid">${(datasets.vision || []).map(d => `<div class="dataset-item vision">${esc(d)}</div>`).join('')}</div>
        `;

        addLog('Training data loaded', 'info');
    } catch (error) {
        addLog(`Training load error: ${error.message}`, 'error');
        toast(`Training data error: ${error.message}`, 'error');
    }
}

// ---------------------------------------------------------------------------
// Forms & Actions
// ---------------------------------------------------------------------------

function initializeForms() {
    document.getElementById('quantumTrainForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await trainQuantumClassifier(e.submitter || e.target.querySelector('[type="submit"]'));
    });
    document.getElementById('loraTrainForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await trainLoRA(e.submitter || e.target.querySelector('[type="submit"]'));
    });
    document.getElementById('chatForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await sendChatMessage();
    });
    document.getElementById('chatProvider').addEventListener('change', (e) => {
        currentProvider = e.target.value;
        localStorage.setItem('qai-provider', currentProvider);
    });
}

function restoreProvider() {
    const stored = localStorage.getItem('qai-provider');
    if (stored) {
        currentProvider = stored;
        const select = document.getElementById('chatProvider');
        if (select) select.value = stored;
    }
}

async function trainQuantumClassifier(btn) {
    const dataset = document.getElementById('quantumDataset').value;
    if (!dataset) { toast('Please select a dataset', 'warning'); return; }

    const payload = {
        dataset,
        n_qubits: parseInt(document.getElementById('quantumQubits').value, 10),
        n_layers: parseInt(document.getElementById('quantumLayers').value, 10),
        epochs: parseInt(document.getElementById('quantumEpochs').value, 10),
        backend: document.getElementById('quantumBackend').value,
    };

    setLoading(btn, true);
    addLog(`Starting quantum training: ${dataset}`, 'info');
    try {
        const result = await fetchJSON('/quantum/train', jsonPost(payload));
        if (result.success) {
            toast('Quantum training started!', 'success');
            addLog('Quantum training started successfully!', 'success');
            setTimeout(loadQuantumData, 2000);
        } else {
            const msg = result.stderr || result.error || 'Unknown error';
            toast(`Training error: ${msg}`, 'error');
            addLog(`Training error: ${msg}`, 'error');
        }
    } catch (error) {
        toast(`Request failed: ${error.message}`, 'error');
        addLog(`Request failed: ${error.message}`, 'error');
    } finally {
        setLoading(btn, false);
    }
}

async function trainLoRA(btn) {
    const dataset = document.getElementById('loraDataset').value;
    if (!dataset) { toast('Please select a dataset', 'warning'); return; }

    const payload = {
        dataset,
        max_train_samples: parseInt(document.getElementById('loraTrainSamples').value, 10),
        max_eval_samples: parseInt(document.getElementById('loraEvalSamples').value, 10),
        epochs: parseInt(document.getElementById('loraEpochs').value, 10),
    };

    setLoading(btn, true);
    addLog(`Starting LoRA training on ${dataset}`, 'info');
    try {
        const result = await fetchJSON('/training/lora', jsonPost(payload));
        if (result.success) {
            toast('LoRA training started!', 'success');
            addLog('LoRA training started successfully!', 'success');
            setTimeout(loadTrainingData, 2000);
        } else {
            const msg = result.stderr || result.error || 'Unknown error';
            toast(`Training error: ${msg}`, 'error');
            addLog(`Training error: ${msg}`, 'error');
        }
    } catch (error) {
        toast(`Request failed: ${error.message}`, 'error');
        addLog(`Request failed: ${error.message}`, 'error');
    } finally {
        setLoading(btn, false);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSendBtn');
    const message = input.value.trim();
    if (!message) return;

    addChatMessage(message, 'user');
    input.value = '';
    setLoading(sendBtn, true);
    const typing = showTyping();

    try {
        const provider = currentProvider === 'auto' ? null : currentProvider;
        const result = await fetchJSON('/chat/message', jsonPost({ message, provider }));
        removeTyping(typing);
        if (result.success) {
            addChatMessage(result.response, 'assistant');
            addLog(`Chat response from ${result.provider}`, 'info');
        } else {
            const msg = result.error || 'Unknown error';
            addChatMessage('Error: ' + msg, 'system');
            addLog(`Chat error: ${msg}`, 'error');
        }
    } catch (error) {
        removeTyping(typing);
        addChatMessage('Error: ' + error.message, 'system');
        addLog(`Chat request failed: ${error.message}`, 'error');
    } finally {
        setLoading(sendBtn, false);
        input.focus();
    }
}

function addChatMessage(content, role) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    messageDiv.textContent = content;  // textContent => XSS-safe
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showTyping() {
    const messagesDiv = document.getElementById('chatMessages');
    const el = document.createElement('div');
    el.className = 'chat-message assistant';
    el.innerHTML = '<span class="typing-dots"><span></span><span></span><span></span></span>';
    messagesDiv.appendChild(el);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return el;
}

function removeTyping(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
}

async function runAutoTrain(dryRun, btn) {
    const job = document.getElementById('autotrainJob').value;
    if (!job) { toast('Please select a job', 'warning'); return; }

    setLoading(btn, true);
    addLog(`Running AutoTrain job: ${job} ${dryRun ? '(dry run)' : ''}`, 'info');
    try {
        const result = await fetchJSON('/training/autotrain', jsonPost({ job_name: job, dry_run: dryRun }));
        if (result.success) {
            toast('AutoTrain job completed!', 'success');
            addLog('AutoTrain job completed successfully!', 'success');
            setTimeout(loadTrainingData, 2000);
        } else {
            const msg = result.stderr || result.error || 'Unknown error';
            toast(`AutoTrain error: ${msg}`, 'error');
            addLog(`AutoTrain error: ${msg}`, 'error');
        }
    } catch (error) {
        toast(`Request failed: ${error.message}`, 'error');
        addLog(`Request failed: ${error.message}`, 'error');
    } finally {
        setLoading(btn, false);
    }
}

function quickAction(action) {
    if (['quantum', 'chat', 'training'].includes(action)) switchTab(action);
}

function refreshStatus(btn) {
    addLog('Refreshing status…', 'info');
    setLoading(btn, true);
    Promise.all([checkServiceStatus(), loadDashboard()]).finally(() => setLoading(btn, false));
}

// ---------------------------------------------------------------------------
// Logging & Toasts
// ---------------------------------------------------------------------------

function addLog(message, type = 'info') {
    const logOutput = document.getElementById('logOutput');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logOutput.appendChild(entry);
    logOutput.scrollTop = logOutput.scrollHeight;
}

function clearLogs() {
    document.getElementById('logOutput').innerHTML = '';
    addLog('Logs cleared', 'info');
}

function refreshLogs() {
    addLog('Logs refreshed', 'info');
}

function toast(message, type = 'info', timeout = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => {
        el.classList.add('hide');
        setTimeout(() => el.remove(), 250);
    }, timeout);
}

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

function jsonPost(body) {
    return {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    };
}

function statusRow(label, value) {
    return `
        <div class="status-item">
            <span class="status-label">${esc(label)}</span>
            <span class="status-value ${value ? 'success' : 'error'}">${value ? '✓ Yes' : '✗ No'}</span>
        </div>`;
}

function emptyRow(text) {
    return `<div class="status-item"><span class="status-label">${esc(text)}</span></div>`;
}

function formatPct(value) {
    const n = Number(value);
    return Number.isFinite(n) ? `${(n * 100).toFixed(1)}%` : 'N/A';
}

function fillSelect(id, options, placeholder = 'Select dataset…') {
    const select = document.getElementById(id);
    if (!select) return;
    const previous = select.value;
    select.innerHTML = `<option value="">${esc(placeholder)}</option>` +
        options.map(o => `<option value="${esc(o.value)}">${esc(o.label)}</option>`).join('');
    if (previous && options.some(o => o.value === previous)) select.value = previous;
}
