/**
 * Training Anomaly Detection System
 * Monitors training metrics for anomalies and triggers alerts
 *
 * Features:
 * - Loss spike detection (>20% increase between epochs)
 * - Divergence detection (loss > threshold)
 * - Stagnation detection (no improvement for N epochs)
 * - Desktop notifications
 * - Optional auto-pause
 */

class TrainingAnomalyDetector {
    constructor(options = {}) {
        this.lossHistory = [];
        this.config = {
            spikeThreshold: options.spikeThreshold || 0.20, // 20% increase
            divergenceThreshold: options.divergenceThreshold || 10.0,
            stagnationEpochs: options.stagnationEpochs || 5,
            enableNotifications: options.enableNotifications !== false,
            enableAutoPause: options.enableAutoPause || false,
            checkInterval: options.checkInterval || 5000, // 5 seconds
            ...options
        };
        this.anomalies = [];
        this.isMonitoring = false;
        this.intervalId = null;
    }

    /**
     * Add a new loss value to history
     */
    addLossValue(epoch, loss, jobName = 'current') {
        this.lossHistory.push({
            epoch,
            loss,
            jobName,
            timestamp: Date.now()
        });

        // Keep only recent history (last 100 epochs)
        if (this.lossHistory.length > 100) {
            this.lossHistory.shift();
        }

        // Check for anomalies
        this.detectAnomalies();
    }

    /**
     * Detect anomalies in loss progression
     */
    detectAnomalies() {
        if (this.lossHistory.length < 2) return;

        const recent = this.lossHistory.slice(-10); // Last 10 epochs
        const current = recent[recent.length - 1];
        const previous = recent[recent.length - 2];

        // 1. SPIKE DETECTION: >20% increase from previous epoch
        if (previous && current.loss > previous.loss * (1 + this.config.spikeThreshold)) {
            const increase = ((current.loss - previous.loss) / previous.loss * 100).toFixed(1);
            this.reportAnomaly('spike', {
                type: 'Loss Spike',
                severity: 'warning',
                message: `Loss increased by ${increase}% (${previous.loss.toFixed(4)} → ${current.loss.toFixed(4)})`,
                epoch: current.epoch,
                jobName: current.jobName,
                recommendation: 'Check for data quality issues or reduce learning rate'
            });
        }

        // 2. DIVERGENCE DETECTION: Loss > threshold
        if (current.loss > this.config.divergenceThreshold) {
            this.reportAnomaly('divergence', {
                type: 'Training Divergence',
                severity: 'error',
                message: `Loss diverged to ${current.loss.toFixed(4)} (threshold: ${this.config.divergenceThreshold})`,
                epoch: current.epoch,
                jobName: current.jobName,
                recommendation: 'Training likely unstable. Reduce learning rate significantly or restart with different hyperparameters'
            });
        }

        // 3. STAGNATION DETECTION: No improvement for N epochs
        if (recent.length >= this.config.stagnationEpochs) {
            const lastN = recent.slice(-this.config.stagnationEpochs);
            const minLoss = Math.min(...lastN.map(h => h.loss));
            const maxLoss = Math.max(...lastN.map(h => h.loss));
            const variation = maxLoss - minLoss;

            // If variation is very small (< 0.001), consider it stagnant
            if (variation < 0.001) {
                this.reportAnomaly('stagnation', {
                    type: 'Training Stagnation',
                    severity: 'info',
                    message: `No improvement for ${this.config.stagnationEpochs} epochs (loss: ${current.loss.toFixed(4)})`,
                    epoch: current.epoch,
                    jobName: current.jobName,
                    recommendation: 'Consider early stopping or increasing learning rate'
                });
            }
        }
    }

    /**
     * Report an anomaly
     */
    reportAnomaly(id, anomaly) {
        // Check if this anomaly was already reported recently (debounce)
        const recentDuplicate = this.anomalies.find(a =>
            a.type === anomaly.type &&
            a.jobName === anomaly.jobName &&
            (Date.now() - a.timestamp < 30000) // Within 30 seconds
        );

        if (recentDuplicate) return;

        // Add timestamp
        anomaly.timestamp = Date.now();
        anomaly.id = `${id}-${anomaly.timestamp}`;

        // Store anomaly
        this.anomalies.push(anomaly);

        // Trigger notification
        if (this.config.enableNotifications) {
            this.sendNotification(anomaly);
        }

        // Trigger callback if provided
        if (this.config.onAnomaly) {
            this.config.onAnomaly(anomaly);
        }

        // Auto-pause if enabled and severity is error
        if (this.config.enableAutoPause && anomaly.severity === 'error') {
            this.pauseTraining(anomaly);
        }
    }

    /**
     * Send desktop notification
     */
    sendNotification(anomaly) {
        if (!('Notification' in window)) return;

        if (Notification.permission === 'granted') {
            new Notification(`⚠️ ${anomaly.type}`, {
                body: anomaly.message,
                icon: '/favicon.ico',
                badge: '/favicon.ico',
                tag: anomaly.id,
                requireInteraction: anomaly.severity === 'error'
            });
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    this.sendNotification(anomaly);
                }
            });
        }
    }

    /**
     * Pause training (if supported)
     */
    pauseTraining(anomaly) {
        console.warn('Auto-pause triggered:', anomaly);
        // This would need backend support to actually pause training
        // For now, just log and notify
        if (this.config.onPause) {
            this.config.onPause(anomaly);
        }
    }

    /**
     * Start monitoring training data from API
     */
    startMonitoring(statusUrl = '/status') {
        if (this.isMonitoring) return;

        this.isMonitoring = true;
        this.intervalId = setInterval(async () => {
            try {
                const response = await fetch(statusUrl);
                const data = await response.json();

                // Extract loss from latest job
                if (data.jobs && data.jobs.length > 0) {
                    const latestJob = data.jobs[data.jobs.length - 1];
                    if (latestJob.status === 'running' && latestJob.current_epoch && latestJob.current_loss) {
                        this.addLossValue(
                            latestJob.current_epoch,
                            latestJob.current_loss,
                            latestJob.name
                        );
                    }
                }
            } catch (err) {
                console.error('Anomaly detector monitoring error:', err);
            }
        }, this.config.checkInterval);
    }

    /**
     * Stop monitoring
     */
    stopMonitoring() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isMonitoring = false;
    }

    /**
     * Get recent anomalies
     */
    getRecentAnomalies(count = 10) {
        return this.anomalies.slice(-count);
    }

    /**
     * Clear anomaly history
     */
    clearAnomalies() {
        this.anomalies = [];
    }

    /**
     * Get anomaly statistics
     */
    getStatistics() {
        return {
            total: this.anomalies.length,
            spikes: this.anomalies.filter(a => a.type === 'Loss Spike').length,
            divergences: this.anomalies.filter(a => a.type === 'Training Divergence').length,
            stagnations: this.anomalies.filter(a => a.type === 'Training Stagnation').length,
            byJob: this.anomalies.reduce((acc, a) => {
                acc[a.jobName] = (acc[a.jobName] || 0) + 1;
                return acc;
            }, {})
        };
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.TrainingAnomalyDetector = TrainingAnomalyDetector;
}
