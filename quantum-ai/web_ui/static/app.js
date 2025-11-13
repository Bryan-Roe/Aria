// Quantum AI Training Dashboard - Frontend Logic

let currentSessionId = null;
let statusUpdateInterval = null;
let lossChart = null;
let accuracyChart = null;
let circuitCanvas = null;
let circuitCtx = null;
let particleInterval = null;

// API Base URL
const API_BASE = window.location.origin;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Quantum AI Dashboard initializing...');
    initializeCircuitCanvas();
    initializeCharts();
    loadDatasets();
    loadResults();
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    document.getElementById('start-training-btn').addEventListener('click', startTraining);
    document.getElementById('stop-training-btn').addEventListener('click', stopTraining);
    document.getElementById('dataset-select').addEventListener('change', updateDatasetInfo);
}

// Initialize Circuit Canvas
function initializeCircuitCanvas() {
    circuitCanvas = document.getElementById('circuit-canvas');
    circuitCtx = circuitCanvas.getContext('2d');
    
    // Set canvas size
    const rect = circuitCanvas.getBoundingClientRect();
    circuitCanvas.width = rect.width;
    circuitCanvas.height = 300;
    
    drawIdleCircuit();
}

// Draw idle circuit state
function drawIdleCircuit() {
    if (!circuitCtx) return;
    
    const ctx = circuitCtx;
    const width = circuitCanvas.width;
    const height = circuitCanvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    // Draw gradient background
    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.1)');
    gradient.addColorStop(1, 'rgba(139, 92, 246, 0.1)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    // Draw placeholder text
    ctx.font = 'bold 18px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto';
    ctx.fillStyle = '#6366f1';
    ctx.textAlign = 'center';
    ctx.fillText('⚛️ Quantum Circuit Visualization', width / 2, height / 2 - 15);
    
    ctx.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText('Start training to see live circuit diagram', width / 2, height / 2 + 15);
    
    // Update stats
    document.getElementById('gate-count').textContent = '0';
    document.getElementById('circuit-depth').textContent = '0';
}

// Draw active quantum circuit
function drawQuantumCircuit(nQubits, nLayers, epoch) {
    if (!circuitCtx) return;
    
    const ctx = circuitCtx;
    const width = circuitCanvas.width;
    const height = circuitCanvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    // Background
    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.05)');
    gradient.addColorStop(1, 'rgba(139, 92, 246, 0.05)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    const padding = 60;
    const qubitSpacing = (height - 2 * padding) / (nQubits - 1 || 1);
    const layerWidth = (width - 2 * padding) / (nLayers + 2);
    
    // Draw qubit lines
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 2;
    for (let i = 0; i < nQubits; i++) {
        const y = padding + i * qubitSpacing;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
        
        // Qubit label
        ctx.fillStyle = '#cbd5e1';
        ctx.font = '14px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`|q${i}⟩`, padding - 10, y + 5);
    }
    
    // Animate based on epoch
    const pulsePhase = (epoch % 10) / 10;
    
    // Draw gates with animation
    for (let layer = 0; layer < nLayers; layer++) {
        const x = padding + (layer + 1) * layerWidth;
        
        for (let i = 0; i < nQubits; i++) {
            const y = padding + i * qubitSpacing;
            
            // Rotation gate (pulsing)
            const gateSize = 25 + Math.sin(pulsePhase * Math.PI * 2) * 3;
            ctx.fillStyle = `rgba(239, 68, 68, ${0.7 + Math.sin(pulsePhase * Math.PI * 2) * 0.3})`;
            ctx.beginPath();
            ctx.arc(x, y, gateSize / 2, 0, Math.PI * 2);
            ctx.fill();
            
            // Gate label
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 11px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('Ry', x, y + 4);
        }
        
        // CNOT gates (entanglement)
        if (nQubits > 1) {
            const cnotX = x + layerWidth / 2;
            ctx.strokeStyle = `rgba(16, 185, 129, ${0.7 + Math.sin(pulsePhase * Math.PI * 2 + Math.PI) * 0.3})`;
            ctx.lineWidth = 3;
            
            for (let i = 0; i < nQubits - 1; i++) {
                const y1 = padding + i * qubitSpacing;
                const y2 = padding + (i + 1) * qubitSpacing;
                
                // Vertical line
                ctx.beginPath();
                ctx.moveTo(cnotX, y1);
                ctx.lineTo(cnotX, y2);
                ctx.stroke();
                
                // Control dot
                ctx.fillStyle = '#10b981';
                ctx.beginPath();
                ctx.arc(cnotX, y1, 5, 0, Math.PI * 2);
                ctx.fill();
                
                // Target circle
                ctx.strokeStyle = '#10b981';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(cnotX, y2, 12, 0, Math.PI * 2);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(cnotX - 8, y2);
                ctx.lineTo(cnotX + 8, y2);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(cnotX, y2 - 8);
                ctx.lineTo(cnotX, y2 + 8);
                ctx.stroke();
            }
        }
    }
    
    // Measurement symbols
    const measX = width - padding - 20;
    for (let i = 0; i < nQubits; i++) {
        const y = padding + i * qubitSpacing;
        
        // Measurement box
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 2;
        ctx.strokeRect(measX - 15, y - 15, 30, 30);
        
        // Meter symbol
        ctx.beginPath();
        ctx.arc(measX, y + 5, 10, Math.PI, 0);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(measX, y + 5);
        ctx.lineTo(measX + 7, y - 2);
        ctx.stroke();
    }
    
    // Epoch indicator with glow
    ctx.save();
    ctx.shadowColor = '#6366f1';
    ctx.shadowBlur = 10;
    ctx.fillStyle = '#6366f1';
    ctx.font = 'bold 16px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`EPOCH ${epoch}`, 15, 25);
    ctx.restore();
    
    // Update circuit stats
    const gateCount = nQubits * nLayers + (nQubits - 1) * nLayers;
    const circuitDepth = nLayers * 2;
    document.getElementById('gate-count').textContent = gateCount;
    document.getElementById('circuit-depth').textContent = circuitDepth;
}

// Create particle effect
function createParticle(x, y) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = x + 'px';
    particle.style.top = y + 'px';
    particle.style.background = `hsl(${Math.random() * 60 + 200}, 70%, 60%)`;
    document.body.appendChild(particle);
    
    setTimeout(() => particle.remove(), 2000);
}

// Start particle animation
function startParticleAnimation() {
    if (particleInterval) return;
    
    particleInterval = setInterval(() => {
        const canvas = document.getElementById('circuit-canvas');
        if (!canvas) return;
        
        const rect = canvas.getBoundingClientRect();
        const x = rect.left + Math.random() * rect.width;
        const y = rect.top + Math.random() * rect.height;
        createParticle(x, y);
    }, 300);
}

// Stop particle animation
function stopParticleAnimation() {
    if (particleInterval) {
        clearInterval(particleInterval);
        particleInterval = null;
    }
}

// Initialize Charts
function initializeCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#cbd5e1'
                }
            }
        },
        scales: {
            x: {
                ticks: { color: '#94a3b8' },
                grid: { color: '#334155' }
            },
            y: {
                ticks: { color: '#94a3b8' },
                grid: { color: '#334155' }
            }
        }
    };

    // Loss Chart
    const lossCtx = document.getElementById('loss-chart').getContext('2d');
    lossChart = new Chart(lossCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Training Loss',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Validation Loss',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                title: {
                    display: true,
                    text: 'Training & Validation Loss',
                    color: '#cbd5e1'
                }
            }
        }
    });

    // Accuracy Chart
    const accCtx = document.getElementById('accuracy-chart').getContext('2d');
    accuracyChart = new Chart(accCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Validation Accuracy',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                title: {
                    display: true,
                    text: 'Validation Accuracy',
                    color: '#cbd5e1'
                }
            },
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    min: 0,
                    max: 1,
                    ticks: {
                        ...chartOptions.scales.y.ticks,
                        callback: function(value) {
                            return (value * 100).toFixed(0) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Load Available Datasets
async function loadDatasets() {
    try {
        const response = await fetch(`${API_BASE}/api/datasets`);
        const datasets = await response.json();
        
        const select = document.getElementById('dataset-select');
        select.innerHTML = '<option value="">Select a dataset...</option>';
        
        datasets.forEach(dataset => {
            const option = document.createElement('option');
            option.value = dataset.name;
            option.textContent = `${dataset.name} (${dataset.features} features)`;
            select.appendChild(option);
        });
        
        console.log(`✅ Loaded ${datasets.length} datasets`);
    } catch (error) {
        console.error('Error loading datasets:', error);
        showError('Failed to load datasets');
    }
}

// Update Dataset Info
function updateDatasetInfo() {
    const select = document.getElementById('dataset-select');
    const infoDiv = document.getElementById('dataset-info');
    
    if (select.value) {
        infoDiv.textContent = `Selected: ${select.value}`;
    } else {
        infoDiv.textContent = '';
    }
}

// Start Training
async function startTraining() {
    const dataset = document.getElementById('dataset-select').value;
    
    if (!dataset) {
        alert('Please select a dataset');
        return;
    }
    
    const config = {
        dataset: dataset,
        n_qubits: parseInt(document.getElementById('n-qubits').value),
        n_layers: parseInt(document.getElementById('n-layers').value),
        learning_rate: parseFloat(document.getElementById('learning-rate').value),
        duration_minutes: parseInt(document.getElementById('duration').value),
        batch_size: parseInt(document.getElementById('batch-size').value)
    };
    
    console.log('🚀 Starting training with config:', config);
    
    try {
        const response = await fetch(`${API_BASE}/api/train/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        currentSessionId = result.session_id;
        
        // Update UI
        document.getElementById('start-training-btn').disabled = true;
        document.getElementById('stop-training-btn').disabled = false;
        document.getElementById('status-idle').style.display = 'none';
        document.getElementById('status-training').style.display = 'block';
        document.getElementById('progress-container').style.display = 'block';
        
        // Start visual effects
        const nQubits = parseInt(document.getElementById('n-qubits').value);
        const nLayers = parseInt(document.getElementById('n-layers').value);
        drawQuantumCircuit(nQubits, nLayers, 0);
        startParticleAnimation();
        
        // Start polling for updates
        startStatusPolling();
        
        console.log(`✅ Training started: ${currentSessionId}`);
    } catch (error) {
        console.error('Error starting training:', error);
        showError('Failed to start training');
    }
}

// Stop Training
async function stopTraining() {
    if (!currentSessionId) return;
    
    try {
        await fetch(`${API_BASE}/api/train/stop/${currentSessionId}`, {
            method: 'POST'
        });
        
        stopStatusPolling();
        console.log('⏹️ Training stopped');
    } catch (error) {
        console.error('Error stopping training:', error);
    }
}

// Start Status Polling
function startStatusPolling() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
    
    statusUpdateInterval = setInterval(updateTrainingStatus, 1000);
}

// Stop Status Polling
function stopStatusPolling() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
        statusUpdateInterval = null;
    }
    
    // Stop visual effects
    stopParticleAnimation();
    drawIdleCircuit();
    
    // Reset UI
    document.getElementById('start-training-btn').disabled = false;
    document.getElementById('stop-training-btn').disabled = true;
    document.getElementById('status-idle').style.display = 'block';
    document.getElementById('status-training').style.display = 'none';
    document.getElementById('progress-container').style.display = 'none';
    
    currentSessionId = null;
    loadResults(); // Refresh results list
}

// Update Training Status
async function updateTrainingStatus() {
    if (!currentSessionId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/train/status/${currentSessionId}`);
        const status = await response.json();
        
        // Update status text
        document.getElementById('status-text').textContent = status.status;
        document.getElementById('current-epoch').textContent = status.current_epoch;
        document.getElementById('current-loss').textContent = status.current_loss.toFixed(4);
        document.getElementById('best-val-acc').textContent = (status.best_val_acc * 100).toFixed(2) + '%';
        
        // Update elapsed time
        if (status.elapsed_time) {
            const minutes = Math.floor(status.elapsed_time / 60);
            const seconds = Math.floor(status.elapsed_time % 60);
            document.getElementById('elapsed-time').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            // Update progress bar
            const configDuration = parseInt(document.getElementById('duration').value) * 60;
            const progress = Math.min((status.elapsed_time / configDuration) * 100, 100);
            document.getElementById('progress-fill').style.width = progress + '%';
            document.getElementById('progress-text').textContent = progress.toFixed(0) + '% complete';
        }
        
        // Update visual accuracy bar
        const accuracy = status.best_val_acc * 100;
        document.getElementById('accuracy-bar').style.width = accuracy + '%';
        document.getElementById('accuracy-percent').textContent = accuracy.toFixed(1) + '%';
        
        // Update circuit visualization
        const nQubits = parseInt(document.getElementById('n-qubits').value);
        const nLayers = parseInt(document.getElementById('n-layers').value);
        drawQuantumCircuit(nQubits, nLayers, status.current_epoch);
        
        // Update charts
        if (status.metrics && status.metrics.epochs.length > 0) {
            updateCharts(status.metrics);
        }
        
        // Check if completed
        if (status.status === 'completed' || status.status === 'error' || status.status === 'stopped') {
            stopStatusPolling();
            
            if (status.status === 'completed') {
                showSuccess('Training completed successfully!');
            } else if (status.status === 'error') {
                showError('Training failed: ' + (status.metrics.error || 'Unknown error'));
            }
        }
        
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// Update Charts with New Data
function updateCharts(metrics) {
    // Loss Chart
    lossChart.data.labels = metrics.epochs;
    lossChart.data.datasets[0].data = metrics.train_loss;
    lossChart.data.datasets[1].data = metrics.val_loss;
    lossChart.update('none'); // Update without animation for smoothness
    
    // Accuracy Chart
    accuracyChart.data.labels = metrics.epochs;
    accuracyChart.data.datasets[0].data = metrics.val_accuracy;
    accuracyChart.update('none');
}

// Load Training Results
async function loadResults() {
    try {
        const response = await fetch(`${API_BASE}/api/results`);
        const results = await response.json();
        
        const resultsDiv = document.getElementById('results-list');
        
        if (results.length === 0) {
            resultsDiv.innerHTML = '<p class="info-text">No training sessions yet. Start training to see results here.</p>';
            return;
        }
        
        resultsDiv.innerHTML = '';
        
        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'result-item';
            item.onclick = () => viewResultDetails(result.filename);
            
            item.innerHTML = `
                <div class="result-header">
                    <div class="result-title">${result.dataset}</div>
                    <div class="result-badge success">${(result.best_acc * 100).toFixed(2)}% acc</div>
                </div>
                <div class="result-meta">
                    <span>📅 ${result.timestamp.join('_')}</span>
                    <span>🔄 ${result.epochs} epochs</span>
                </div>
            `;
            
            resultsDiv.appendChild(item);
        });
        
        console.log(`✅ Loaded ${results.length} training results`);
    } catch (error) {
        console.error('Error loading results:', error);
    }
}

// View Result Details
async function viewResultDetails(filename) {
    try {
        const response = await fetch(`${API_BASE}/api/results/${filename}`);
        const data = await response.json();
        
        console.log('📊 Result details:', data);
        
        // Update charts with historical data
        if (data.metrics) {
            updateCharts(data.metrics);
        }
        
        // Show details (could open a modal or expand in place)
        alert(`Training Session Details:\n\nDataset: ${data.config.dataset}\nQubits: ${data.config.n_qubits}\nLayers: ${data.config.n_layers}\nEpochs: ${data.total_epochs}\nBest Accuracy: ${(data.best_val_acc * 100).toFixed(2)}%`);
        
    } catch (error) {
        console.error('Error loading result details:', error);
    }
}

// Show Success Message
function showSuccess(message) {
    console.log('✅', message);
    // Could add a toast notification here
}

// Show Error Message
function showError(message) {
    console.error('❌', message);
    alert('Error: ' + message);
}
