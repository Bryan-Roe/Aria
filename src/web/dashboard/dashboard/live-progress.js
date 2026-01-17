/**
 * Live Training Progress Tracker
 * Real-time monitoring with streaming updates, live charts, and job controls
 */

class LiveProgressTracker {
    constructor(options = {}) {
        this.pollingInterval = options.pollingInterval || 2000; // 2 seconds
        this.chartUpdateInterval = options.chartUpdateInterval || 5000; // 5 seconds
        this.activeJobId = null;
        this.pollTimer = null;
        this.chartTimer = null;
        this.liveChart = null;
        this.startTime = null;
        this.currentEpoch = 0;
        this.totalEpochs = 0;
        this.callbacks = {
            onUpdate: options.onUpdate || (() => {}),
            onComplete: options.onComplete || (() => {}),
            onError: options.onError || (() => {})
        };
    }

    /**
     * Start tracking a training job
     */
    startTracking(jobId, totalEpochs) {
        this.activeJobId = jobId;
        this.totalEpochs = totalEpochs;
        this.startTime = Date.now();
        this.currentEpoch = 0;

        // Initialize UI
        this.showProgressUI();
        this.initializeLiveChart();

        // Start polling
        this.pollTimer = setInterval(() => this.pollProgress(), this.pollingInterval);
        this.chartTimer = setInterval(() => this.updateLiveChart(), this.chartUpdateInterval);

        console.log(`[LiveProgress] Started tracking job: ${jobId}`);
    }

    /**
     * Stop tracking
     */
    stopTracking() {
        if (this.pollTimer) clearInterval(this.pollTimer);
        if (this.chartTimer) clearInterval(this.chartTimer);
        this.pollTimer = null;
        this.chartTimer = null;
        this.activeJobId = null;
        console.log('[LiveProgress] Stopped tracking');
    }

    /**
     * Poll for progress updates
     */
    async pollProgress() {
        if (!this.activeJobId) return;

        try {
            const response = await fetch(`/api/job-progress/${this.activeJobId}`);
            if (!response.ok) {
                // Fallback to status endpoint
                const statusResponse = await fetch('/status');
                const statusData = await statusResponse.json();
                this.handleStatusUpdate(statusData);
                return;
            }

            const data = await response.json();
            this.handleProgressUpdate(data);
        } catch (err) {
            console.error('[LiveProgress] Poll error:', err);
            this.callbacks.onError(err);
        }
    }

    /**
     * Handle progress update from server
     */
    handleProgressUpdate(data) {
        if (data.status === 'completed') {
            this.stopTracking();
            this.callbacks.onComplete(data);
            this.showCompletionMessage(data);
            return;
        }

        if (data.status === 'failed') {
            this.stopTracking();
            this.callbacks.onError(new Error(data.error || 'Training failed'));
            this.showErrorMessage(data);
            return;
        }

        // Update UI elements
        this.updateProgressBars(data);
        this.updateMetrics(data);
        this.updateETA(data);
        
        this.callbacks.onUpdate(data);
    }

    /**
     * Handle status update (fallback)
     */
    handleStatusUpdate(statusData) {
        if (!statusData.jobs) return;

        const job = statusData.jobs.find(j => j.id === this.activeJobId || j.name === this.activeJobId);
        if (!job) return;

        const progress = {
            current_epoch: job.current_epoch || 0,
            total_epochs: job.total_epochs || this.totalEpochs,
            current_loss: job.current_loss || job.post_loss || 0,
            train_loss: job.train_loss || [],
            eval_loss: job.eval_loss || [],
            status: job.status || 'running',
            progress_percent: job.progress_percent || 0
        };

        this.handleProgressUpdate(progress);
    }

    /**
     * Update progress bars
     */
    updateProgressBars(data) {
        const epochBar = document.getElementById('liveEpochProgress');
        const overallBar = document.getElementById('liveOverallProgress');

        if (epochBar) {
            const epochPercent = ((data.current_step || 0) / (data.total_steps_per_epoch || 100)) * 100;
            epochBar.style.width = `${Math.min(epochPercent, 100)}%`;
            epochBar.textContent = `Epoch ${data.current_epoch || 0}/${data.total_epochs || this.totalEpochs}`;
        }

        if (overallBar) {
            const overallPercent = data.progress_percent || 0;
            overallBar.style.width = `${Math.min(overallPercent, 100)}%`;
            overallBar.textContent = `${Math.round(overallPercent)}%`;
        }

        this.currentEpoch = data.current_epoch || 0;
    }

    /**
     * Update metrics display
     */
    updateMetrics(data) {
        const lossEl = document.getElementById('liveCurrentLoss');
        const lrEl = document.getElementById('liveLearningRate');
        const stepsEl = document.getElementById('liveStepsPerSec');

        if (lossEl && data.current_loss !== undefined) {
            lossEl.textContent = data.current_loss.toFixed(4);
            lossEl.className = 'metric-value ' + this.getLossClass(data.current_loss);
        }

        if (lrEl && data.learning_rate !== undefined) {
            lrEl.textContent = data.learning_rate.toExponential(2);
        }

        if (stepsEl && data.steps_per_sec !== undefined) {
            stepsEl.textContent = data.steps_per_sec.toFixed(2);
        }
    }

    /**
     * Calculate and update ETA
     */
    updateETA(data) {
        const etaEl = document.getElementById('liveETA');
        if (!etaEl) return;

        const elapsed = (Date.now() - this.startTime) / 1000; // seconds
        const progress = data.progress_percent || 0;

        if (progress > 0 && progress < 100) {
            const totalEstimated = elapsed / (progress / 100);
            const remaining = totalEstimated - elapsed;
            
            etaEl.textContent = this.formatTime(remaining);
        } else {
            etaEl.textContent = 'Calculating...';
        }
    }

    /**
     * Initialize live chart
     */
    initializeLiveChart() {
        const canvas = document.getElementById('liveProgressChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.liveChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Training Loss',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        pointRadius: 3
                    },
                    {
                        label: 'Validation Loss',
                        data: [],
                        borderColor: '#f093fb',
                        backgroundColor: 'rgba(240, 147, 251, 0.1)',
                        tension: 0.4,
                        pointRadius: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 500 },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: { display: true, text: 'Loss' }
                    },
                    x: {
                        title: { display: true, text: 'Step' }
                    }
                },
                plugins: {
                    legend: { display: true, position: 'top' },
                    tooltip: { mode: 'index', intersect: false }
                }
            }
        });
    }

    /**
     * Update live chart with new data
     */
    async updateLiveChart() {
        if (!this.liveChart || !this.activeJobId) return;

        try {
            const response = await fetch(`/api/job-metrics/${this.activeJobId}`);
            if (!response.ok) return;

            const data = await response.json();
            
            // Update chart data
            this.liveChart.data.labels = data.steps || [];
            this.liveChart.data.datasets[0].data = data.train_loss || [];
            this.liveChart.data.datasets[1].data = data.eval_loss || [];
            
            this.liveChart.update('none'); // Update without animation for smoothness
        } catch (err) {
            console.error('[LiveProgress] Chart update error:', err);
        }
    }

    /**
     * Show progress UI
     */
    showProgressUI() {
        const container = document.getElementById('liveProgressContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">🎯 Live Training Progress</h3>
                    <div style="display:flex;gap:10px">
                        <button class="btn btn-warning btn-sm" onclick="liveTracker.pauseTraining()">⏸️ Pause</button>
                        <button class="btn btn-danger btn-sm" onclick="liveTracker.stopTraining()">⏹️ Stop</button>
                    </div>
                </div>

                <div style="padding:20px">
                    <!-- Progress Bars -->
                    <div class="form-group">
                        <label>Epoch Progress</label>
                        <div class="progress-bar">
                            <div class="progress-fill" id="liveEpochProgress" style="width:0%">Epoch 0/0</div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Overall Progress</label>
                        <div class="progress-bar">
                            <div class="progress-fill" id="liveOverallProgress" style="width:0%">0%</div>
                        </div>
                    </div>

                    <!-- Metrics Grid -->
                    <div class="grid-4" style="margin-top:20px">
                        <div class="metric-card">
                            <div class="metric-label">Current Loss</div>
                            <div class="metric-value metric-info" id="liveCurrentLoss">0.0000</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Learning Rate</div>
                            <div class="metric-value" id="liveLearningRate">0.0e+0</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Steps/Sec</div>
                            <div class="metric-value" id="liveStepsPerSec">0.00</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">ETA</div>
                            <div class="metric-value" id="liveETA">Calculating...</div>
                        </div>
                    </div>

                    <!-- Live Chart -->
                    <div style="margin-top:20px;height:300px">
                        <canvas id="liveProgressChart"></canvas>
                    </div>
                </div>
            </div>
        `;

        container.style.display = 'block';
    }

    /**
     * Hide progress UI
     */
    hideProgressUI() {
        const container = document.getElementById('liveProgressContainer');
        if (container) container.style.display = 'none';
    }

    /**
     * Show completion message
     */
    showCompletionMessage(data) {
        const container = document.getElementById('liveProgressContainer');
        if (!container) return;

        const finalLoss = data.final_loss || data.current_loss || 0;
        const duration = ((Date.now() - this.startTime) / 1000 / 60).toFixed(1);

        container.innerHTML = `
            <div class="alert alert-success">
                <h3>✅ Training Complete!</h3>
                <p><strong>Final Loss:</strong> ${finalLoss.toFixed(4)}</p>
                <p><strong>Duration:</strong> ${duration} minutes</p>
                <p><strong>Epochs:</strong> ${this.currentEpoch}/${this.totalEpochs}</p>
                <button class="btn btn-primary" onclick="liveTracker.hideProgressUI()">Close</button>
            </div>
        `;
    }

    /**
     * Show error message
     */
    showErrorMessage(data) {
        const container = document.getElementById('liveProgressContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="alert alert-error">
                <h3>❌ Training Failed</h3>
                <p>${data.error || 'Unknown error occurred'}</p>
                <button class="btn btn-secondary" onclick="liveTracker.hideProgressUI()">Close</button>
            </div>
        `;
    }

    /**
     * Job control: Pause training
     */
    async pauseTraining() {
        if (!this.activeJobId) return;

        try {
            const response = await fetch(`/api/job-control/${this.activeJobId}/pause`, {
                method: 'POST'
            });
            
            if (response.ok) {
                alert('Training paused successfully');
            }
        } catch (err) {
            console.error('[LiveProgress] Pause error:', err);
            alert('Failed to pause training');
        }
    }

    /**
     * Job control: Stop training
     */
    async stopTraining() {
        if (!this.activeJobId) return;
        if (!confirm('Are you sure you want to stop this training job?')) return;

        try {
            const response = await fetch(`/api/job-control/${this.activeJobId}/stop`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.stopTracking();
                alert('Training stopped successfully');
                this.hideProgressUI();
            }
        } catch (err) {
            console.error('[LiveProgress] Stop error:', err);
            alert('Failed to stop training');
        }
    }

    /**
     * Helper: Get loss color class
     */
    getLossClass(loss) {
        if (loss < 0.5) return 'metric-good';
        if (loss < 1.0) return 'metric-warning';
        return 'metric-bad';
    }

    /**
     * Helper: Format time (seconds to human readable)
     */
    formatTime(seconds) {
        if (seconds < 60) return `${Math.round(seconds)}s`;
        if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
        const hours = Math.floor(seconds / 3600);
        const mins = Math.round((seconds % 3600) / 60);
        return `${hours}h ${mins}m`;
    }

    /**
     * Get tracking status
     */
    isTracking() {
        return this.activeJobId !== null;
    }

    /**
     * Get current job ID
     */
    getActiveJobId() {
        return this.activeJobId;
    }
}

// Export for use in dashboard
if (typeof window !== 'undefined') {
    window.LiveProgressTracker = LiveProgressTracker;
}
