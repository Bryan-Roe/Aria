// QAI Control Center JavaScript

const API_BASE = 'http://localhost:8000';

// Global state
let currentProvider = 'auto';
let chatHistory = [];

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeForms();
    checkServiceStatus();
    loadDashboard();

    // Refresh status every 30 seconds
    setInterval(checkServiceStatus, 30000);
});

// Tab Management
function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    // Load tab-specific data
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'quantum':
            loadQuantumData();
            break;
        case 'chat':
            loadChatData();
            break;
        case 'training':
            loadTrainingData();
            break;
    }
}

// Service Status
async function checkServiceStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        const indicator = document.getElementById('serviceStatus');
        const dot = indicator.querySelector('.status-dot');
        const text = indicator.querySelector('.status-text');

        if (data.status === 'healthy') {
            dot.classList.add('online');
            dot.classList.remove('offline');
            text.textContent = 'Online';
        } else {
            dot.classList.remove('online');
            dot.classList.add('offline');
            text.textContent = 'Error';
        }
    } catch (error) {
        const indicator = document.getElementById('serviceStatus');
        const dot = indicator.querySelector('.status-dot');
        const text = indicator.querySelector('.status-text');
        dot.classList.remove('online');
        dot.classList.add('offline');
        text.textContent = 'Offline';
    }
}

// Dashboard
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();

        // Update system status
        const statusHtml = `
            <div class="status-item">
                <span class="status-label">Service</span>
                <span class="status-value success">${data.service}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Version</span>
                <span class="status-value">${data.version}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Quantum Enabled</span>
                <span class="status-value ${data.quantum.enabled ? 'success' : 'error'}">
                    ${data.quantum.enabled ? '✓ Yes' : '✗ No'}
                </span>
            </div>
            <div class="status-item">
                <span class="status-label">Chat Enabled</span>
                <span class="status-value ${data.chat.enabled ? 'success' : 'error'}">
                    ${data.chat.enabled ? '✓ Yes' : '✗ No'}
                </span>
            </div>
            <div class="status-item">
                <span class="status-label">Training Enabled</span>
                <span class="status-value ${data.training.enabled ? 'success' : 'error'}">
                    ${data.training.enabled ? '✓ Yes' : '✗ No'}
                </span>
            </div>
        `;
        document.getElementById('systemStatus').innerHTML = statusHtml;

        // Update recent activity
        let activityHtml = '<div class="status-item"><span class="status-label">No recent activity</span></div>';

        if (data.quantum.recent_results && data.quantum.recent_results.length > 0) {
            activityHtml = data.quantum.recent_results.map(result => `
                <div class="result-item">
                    <strong>Quantum:</strong> ${result.dataset} -
                    <span class="accuracy">${(result.accuracy * 100).toFixed(1)}%</span> accuracy
                    <br><small>${result.backend} - ${result.timestamp}</small>
                </div>
            `).join('');
        }

        document.getElementById('recentActivity').innerHTML = activityHtml;

        addLog('Dashboard loaded successfully', 'success');
    } catch (error) {
        addLog(`Dashboard load error: ${error.message}`, 'error');
    }
}

// Quantum AI
async function loadQuantumData() {
    try {
        // Load datasets
        const datasetsResponse = await fetch(`${API_BASE}/quantum/datasets`);
        const datasets = await datasetsResponse.json();

        const datasetSelect = document.getElementById('quantumDataset');
        datasetSelect.innerHTML = '<option value="">Select dataset...</option>' +
            datasets.map(d => `<option value="${d.name}">${d.name}</option>`).join('');

        // Load status
        const statusResponse = await fetch(`${API_BASE}/quantum/status`);
        const status = await statusResponse.json();

        const statusHtml = `
            <div class="status-item">
                <span class="status-label">Backend</span>
                <span class="status-value">${status.backend}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Azure Connected</span>
                <span class="status-value ${status.azure_connected ? 'success' : 'error'}">
                    ${status.azure_connected ? '✓ Yes' : '✗ No'}
                </span>
            </div>
            <div class="status-item">
                <span class="status-label">Available Backends</span>
                <span class="status-value">${status.available_backends.length}</span>
            </div>
        `;
        document.getElementById('quantumStatus').innerHTML = statusHtml;

        // Load recent results
        const resultsHtml = status.recent_results && status.recent_results.length > 0
            ? status.recent_results.map(r => `
                <div class="result-item">
                    <strong>${r.dataset}</strong><br>
                    Accuracy: <span class="accuracy">${(r.accuracy * 100).toFixed(1)}%</span><br>
                    <small>${r.backend} - ${r.timestamp}</small>
                </div>
            `).join('')
            : '<div class="status-item"><span class="status-label">No results yet</span></div>';

        document.getElementById('quantumResults').innerHTML = resultsHtml;

        // Load AutoRun jobs (placeholder)
        document.getElementById('quantumAutorunJobs').innerHTML = `
            <div class="status-item">
                <span class="status-label">Available jobs will appear here</span>
            </div>
        `;

        addLog('Quantum data loaded', 'info');
    } catch (error) {
        addLog(`Quantum load error: ${error.message}`, 'error');
    }
}

// Chat
async function loadChatData() {
    try {
        const response = await fetch(`${API_BASE}/chat/status`);
        const data = await response.json();

        // Update provider status
        const providersHtml = Object.entries(data.providers).map(([name, info]) => `
            <div class="status-item">
                <span class="status-label">${name.toUpperCase()}</span>
                <span class="status-value ${info.available ? 'success' : 'error'}">
                    ${info.available ? '✓ Available' : '✗ Unavailable'}
                    ${info.cost ? ` (${info.cost})` : ''}
                </span>
            </div>
        `).join('');

        document.getElementById('chatProviders').innerHTML = providersHtml;

        // Update chat status
        const statusHtml = `
            <div class="status-item">
                <span class="status-label">Default Provider</span>
                <span class="status-value">${data.default_provider}</span>
            </div>
        `;
        document.getElementById('chatStatus').innerHTML = statusHtml;

        // Load conversation history
        if (data.recent_conversations && data.recent_conversations.length > 0) {
            const historyHtml = data.recent_conversations.map(conv => `
                <div class="result-item">
                    <strong>${conv.file}</strong><br>
                    ${conv.message_count} messages<br>
                    <small>${conv.preview}</small>
                </div>
            `).join('');
            document.getElementById('chatHistory').innerHTML = historyHtml;
        } else {
            document.getElementById('chatHistory').innerHTML =
                '<div class="status-item"><span class="status-label">No conversations yet</span></div>';
        }

        addLog('Chat data loaded', 'info');
    } catch (error) {
        addLog(`Chat load error: ${error.message}`, 'error');
    }
}

// Training
async function loadTrainingData() {
    try {
        // Load datasets
        const datasetsResponse = await fetch(`${API_BASE}/training/datasets`);
        const datasets = await datasetsResponse.json();

        // Populate LoRA dataset select
        const loraSelect = document.getElementById('loraDataset');
        loraSelect.innerHTML = '<option value="">Select dataset...</option>';

        if (datasets.chat && datasets.chat.length > 0) {
            datasets.chat.forEach(ds => {
                loraSelect.innerHTML += `<option value="../../datasets/chat/${ds}">${ds}</option>`;
            });
        }

        // Load training status
        const statusResponse = await fetch(`${API_BASE}/training/status`);
        const status = await statusResponse.json();

        const statusHtml = `
            <div class="status-item">
                <span class="status-label">System</span>
                <span class="status-value success">Ready</span>
            </div>
        `;
        document.getElementById('trainingStatus').innerHTML = statusHtml;

        // LoRA adapter status
        const adapterHtml = status.lora_adapter.available
            ? `
                <div class="status-item">
                    <span class="status-label">Status</span>
                    <span class="status-value success">✓ Available</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Model</span>
                    <span class="status-value">${status.lora_adapter.model || 'N/A'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Rank</span>
                    <span class="status-value">${status.lora_adapter.rank || 'N/A'}</span>
                </div>
            `
            : '<div class="status-item"><span class="status-label">No adapter trained yet</span></div>';

        document.getElementById('loraAdapterStatus').innerHTML = adapterHtml;

        // Load AutoTrain jobs
        const jobsResponse = await fetch(`${API_BASE}/training/autotrain/jobs`);
        const jobs = await jobsResponse.json();

        const jobSelect = document.getElementById('autotrainJob');
        jobSelect.innerHTML = '<option value="">Select job...</option>' +
            (jobs.jobs || []).map(job => `<option value="${job}">${job}</option>`).join('');

        // AutoTrain status
        const autotrainHtml = status.orchestrators.autotrain.jobs &&
            Object.keys(status.orchestrators.autotrain.jobs).length > 0
            ? Object.entries(status.orchestrators.autotrain.jobs).map(([name, job]) => `
                <div class="job-item">
                    <span><strong>${name}</strong> - ${job.status || 'unknown'}</span>
                </div>
            `).join('')
            : '<div class="status-item"><span class="status-label">No jobs run yet</span></div>';

        document.getElementById('autotrainStatus').innerHTML = autotrainHtml;

        // Dataset list
        const datasetHtml = `
            <h4>Quantum (${datasets.quantum ? datasets.quantum.length : 0})</h4>
            <div class="dataset-grid">
                ${(datasets.quantum || []).map(d => `<div class="dataset-item quantum">${d}</div>`).join('')}
            </div>
            <h4>Chat (${datasets.chat ? datasets.chat.length : 0})</h4>
            <div class="dataset-grid">
                ${(datasets.chat || []).map(d => `<div class="dataset-item chat">${d}</div>`).join('')}
            </div>
            <h4>Vision (${datasets.vision ? datasets.vision.length : 0})</h4>
            <div class="dataset-grid">
                ${(datasets.vision || []).map(d => `<div class="dataset-item vision">${d}</div>`).join('')}
            </div>
        `;
        document.getElementById('datasetList').innerHTML = datasetHtml;

        addLog('Training data loaded', 'info');
    } catch (error) {
        addLog(`Training load error: ${error.message}`, 'error');
    }
}

// Form Handlers
function initializeForms() {
    // Quantum training form
    document.getElementById('quantumTrainForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await trainQuantumClassifier();
    });

    // LoRA training form
    document.getElementById('loraTrainForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await trainLoRA();
    });

    // Chat form
    document.getElementById('chatForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await sendChatMessage();
    });

    // Chat provider change
    document.getElementById('chatProvider').addEventListener('change', (e) => {
        currentProvider = e.target.value;
    });
}

async function trainQuantumClassifier() {
    const dataset = document.getElementById('quantumDataset').value;
    const n_qubits = parseInt(document.getElementById('quantumQubits').value);
    const n_layers = parseInt(document.getElementById('quantumLayers').value);
    const epochs = parseInt(document.getElementById('quantumEpochs').value);
    const backend = document.getElementById('quantumBackend').value;

    if (!dataset) {
        addLog('Please select a dataset', 'error');
        return;
    }

    addLog(`Starting quantum training: ${dataset}`, 'info');

    try {
        const response = await fetch(`${API_BASE}/quantum/train`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset, n_qubits, n_layers, epochs, backend })
        });

        const result = await response.json();

        if (result.success) {
            addLog('Quantum training started successfully!', 'success');
            setTimeout(() => loadQuantumData(), 2000);
        } else {
            addLog(`Training error: ${result.stderr || result.error}`, 'error');
        }
    } catch (error) {
        addLog(`Request failed: ${error.message}`, 'error');
    }
}

async function trainLoRA() {
    const dataset = document.getElementById('loraDataset').value;
    const max_train_samples = parseInt(document.getElementById('loraTrainSamples').value);
    const max_eval_samples = parseInt(document.getElementById('loraEvalSamples').value);
    const epochs = parseInt(document.getElementById('loraEpochs').value);

    if (!dataset) {
        addLog('Please select a dataset', 'error');
        return;
    }

    addLog(`Starting LoRA training on ${dataset}`, 'info');

    try {
        const response = await fetch(`${API_BASE}/training/lora`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset, max_train_samples, max_eval_samples, epochs })
        });

        const result = await response.json();

        if (result.success) {
            addLog('LoRA training started successfully!', 'success');
            setTimeout(() => loadTrainingData(), 2000);
        } else {
            addLog(`Training error: ${result.stderr || result.error}`, 'error');
        }
    } catch (error) {
        addLog(`Request failed: ${error.message}`, 'error');
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';

    try {
        const provider = currentProvider === 'auto' ? null : currentProvider;

        const response = await fetch(`${API_BASE}/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, provider })
        });

        const result = await response.json();

        if (result.success) {
            addChatMessage(result.response, 'assistant');
            addLog(`Chat response from ${result.provider}`, 'info');
        } else {
            addChatMessage('Error: ' + (result.error || 'Unknown error'), 'system');
            addLog(`Chat error: ${result.error}`, 'error');
        }
    } catch (error) {
        addChatMessage('Error: ' + error.message, 'system');
        addLog(`Chat request failed: ${error.message}`, 'error');
    }
}

function addChatMessage(content, role) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    messageDiv.textContent = content;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function runAutoTrain(dryRun) {
    const job = document.getElementById('autotrainJob').value;

    if (!job) {
        addLog('Please select a job', 'error');
        return;
    }

    addLog(`Running AutoTrain job: ${job} ${dryRun ? '(dry run)' : ''}`, 'info');

    try {
        const response = await fetch(`${API_BASE}/training/autotrain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_name: job, dry_run: dryRun })
        });

        const result = await response.json();

        if (result.success) {
            addLog('AutoTrain job completed successfully!', 'success');
            setTimeout(() => loadTrainingData(), 2000);
        } else {
            addLog(`AutoTrain error: ${result.stderr || result.error}`, 'error');
        }
    } catch (error) {
        addLog(`Request failed: ${error.message}`, 'error');
    }
}

// Quick Actions
function quickAction(action) {
    switch(action) {
        case 'quantum':
            switchTab('quantum');
            break;
        case 'chat':
            switchTab('chat');
            break;
        case 'training':
            switchTab('training');
            break;
    }
}

function refreshStatus() {
    addLog('Refreshing status...', 'info');
    loadDashboard();
}

// Logging
function addLog(message, type = 'info') {
    const logOutput = document.getElementById('logOutput');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
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
