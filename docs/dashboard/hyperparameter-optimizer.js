/**
 * Automated Hyperparameter Optimization
 * Smart tuning with Bayesian optimization, grid search, and early stopping
 */

class HyperparameterOptimizer {
    constructor() {
        this.searchSpace = {};
        this.trials = [];
        this.bestConfig = null;
        this.bestScore = -Infinity;
        this.currentTrial = 0;
        this.maxTrials = 10;
        this.strategy = 'bayesian'; // bayesian, grid, random
        this.earlyStopping = {
            enabled: true,
            patience: 3,
            minDelta: 0.01
        };
    }

    /**
     * Define search space
     */
    defineSearchSpace(space) {
        this.searchSpace = space;
        console.log('[HyperOptim] Search space defined:', space);
    }

    /**
     * Start optimization
     */
    async startOptimization(config) {
        this.maxTrials = config.maxTrials || 10;
        this.strategy = config.strategy || 'bayesian';
        this.currentTrial = 0;
        this.trials = [];
        this.bestConfig = null;
        this.bestScore = -Infinity;

        console.log(`[HyperOptim] Starting ${this.strategy} optimization with ${this.maxTrials} trials`);

        // Show optimization UI
        this.showOptimizationUI();

        // Generate trial configurations based on strategy
        const trialConfigs = this.generateTrialConfigs();

        // Run trials
        for (let i = 0; i < trialConfigs.length; i++) {
            if (this.shouldStopEarly()) {
                console.log('[HyperOptim] Early stopping triggered');
                break;
            }

            await this.runTrial(trialConfigs[i], i + 1);
        }

        // Show final results
        this.showOptimizationResults();
    }

    /**
     * Generate trial configurations based on strategy
     */
    generateTrialConfigs() {
        switch (this.strategy) {
            case 'grid':
                return this.generateGridSearch();
            case 'random':
                return this.generateRandomSearch();
            case 'bayesian':
                return this.generateBayesianSearch();
            default:
                return this.generateRandomSearch();
        }
    }

    /**
     * Grid search: Exhaustive search over all combinations
     */
    generateGridSearch() {
        const configs = [];
        const params = Object.keys(this.searchSpace);
        
        // Generate all combinations (limited to maxTrials)
        const combinations = this.cartesianProduct(
            params.map(p => this.searchSpace[p].values || this.searchSpace[p].range)
        );

        return combinations.slice(0, this.maxTrials).map(combo => {
            const config = {};
            params.forEach((p, idx) => {
                config[p] = combo[idx];
            });
            return config;
        });
    }

    /**
     * Random search: Random sampling from search space
     */
    generateRandomSearch() {
        const configs = [];
        
        for (let i = 0; i < this.maxTrials; i++) {
            const config = {};
            Object.keys(this.searchSpace).forEach(param => {
                const space = this.searchSpace[param];
                
                if (space.values) {
                    // Categorical: random choice
                    config[param] = space.values[Math.floor(Math.random() * space.values.length)];
                } else if (space.range) {
                    // Continuous: random value in range
                    const [min, max] = space.range;
                    const scale = space.scale || 'linear';
                    
                    if (scale === 'log') {
                        const logMin = Math.log(min);
                        const logMax = Math.log(max);
                        config[param] = Math.exp(logMin + Math.random() * (logMax - logMin));
                    } else {
                        config[param] = min + Math.random() * (max - min);
                    }
                    
                    // Round if integer type
                    if (space.type === 'int') {
                        config[param] = Math.round(config[param]);
                    }
                }
            });
            configs.push(config);
        }

        return configs;
    }

    /**
     * Bayesian optimization: Intelligent search using Gaussian Process
     */
    generateBayesianSearch() {
        // Start with random samples
        const initialSamples = 3;
        const configs = this.generateRandomSearch().slice(0, initialSamples);

        // For remaining trials, use acquisition function
        // (Simplified version - real Bayesian optimization is more complex)
        for (let i = initialSamples; i < this.maxTrials; i++) {
            const config = this.selectNextBayesianConfig();
            configs.push(config);
        }

        return configs;
    }

    /**
     * Select next configuration using Expected Improvement (simplified)
     */
    selectNextBayesianConfig() {
        // Generate candidate configs
        const candidates = this.generateRandomSearch().slice(0, 20);
        
        // Score each candidate based on distance from previous trials
        let bestCandidate = candidates[0];
        let bestEI = -Infinity;

        candidates.forEach(candidate => {
            const ei = this.calculateExpectedImprovement(candidate);
            if (ei > bestEI) {
                bestEI = ei;
                bestCandidate = candidate;
            }
        });

        return bestCandidate;
    }

    /**
     * Calculate Expected Improvement (simplified)
     */
    calculateExpectedImprovement(config) {
        if (this.trials.length === 0) return Math.random();

        // Calculate distance to existing trials
        let minDistance = Infinity;
        this.trials.forEach(trial => {
            const distance = this.configDistance(config, trial.config);
            minDistance = Math.min(minDistance, distance);
        });

        // Exploration bonus: prefer configs far from existing trials
        const exploration = minDistance;
        
        // Exploitation: prefer regions with good scores
        const exploitation = this.predictScore(config);

        return exploration * 0.3 + exploitation * 0.7;
    }

    /**
     * Calculate distance between two configurations
     */
    configDistance(config1, config2) {
        let distance = 0;
        Object.keys(config1).forEach(param => {
            const v1 = config1[param];
            const v2 = config2[param];
            
            if (typeof v1 === 'number' && typeof v2 === 'number') {
                const space = this.searchSpace[param];
                const range = space.range ? space.range[1] - space.range[0] : 1;
                distance += Math.pow((v1 - v2) / range, 2);
            } else if (v1 !== v2) {
                distance += 1;
            }
        });
        return Math.sqrt(distance);
    }

    /**
     * Predict score for a configuration (simplified)
     */
    predictScore(config) {
        if (this.trials.length === 0) return 0.5;

        // Weighted average of nearby trials
        let weightedSum = 0;
        let totalWeight = 0;

        this.trials.forEach(trial => {
            const distance = this.configDistance(config, trial.config);
            const weight = Math.exp(-distance);
            weightedSum += weight * trial.score;
            totalWeight += weight;
        });

        return totalWeight > 0 ? weightedSum / totalWeight : 0.5;
    }

    /**
     * Run a single trial
     */
    async runTrial(config, trialNum) {
        console.log(`[HyperOptim] Running trial ${trialNum}/${this.maxTrials}`, config);

        this.updateTrialUI(trialNum, 'running', config);

        try {
            // Submit training job with this configuration
            const response = await fetch('/api/start-training', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...config,
                    job_name: `hyperparam_trial_${trialNum}`,
                    _hyperopt: true
                })
            });

            if (!response.ok) {
                throw new Error('Training submission failed');
            }

            // Wait for completion (poll status)
            const result = await this.waitForCompletion(`hyperparam_trial_${trialNum}`);

            // Calculate score (lower loss = higher score)
            const score = result.post_loss ? (1 / result.post_loss) * 100 : 0;

            // Record trial
            const trial = {
                trialNum,
                config,
                score,
                loss: result.post_loss,
                duration: result.duration,
                timestamp: Date.now()
            };

            this.trials.push(trial);

            // Update best config
            if (score > this.bestScore) {
                this.bestScore = score;
                this.bestConfig = config;
                this.saveBestConfig();
            }

            this.updateTrialUI(trialNum, 'completed', config, score);

            console.log(`[HyperOptim] Trial ${trialNum} completed. Score: ${score.toFixed(2)}`);

        } catch (err) {
            console.error(`[HyperOptim] Trial ${trialNum} failed:`, err);
            this.updateTrialUI(trialNum, 'failed', config);
        }
    }

    /**
     * Wait for training completion
     */
    async waitForCompletion(jobName, timeout = 3600000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            await new Promise(resolve => setTimeout(resolve, 5000)); // Poll every 5 seconds

            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                const job = data.jobs?.find(j => j.name === jobName);
                if (job && job.status === 'completed') {
                    return job;
                }
                if (job && job.status === 'failed') {
                    throw new Error('Training failed');
                }
            } catch (err) {
                console.error('[HyperOptim] Status poll error:', err);
            }
        }

        throw new Error('Training timeout');
    }

    /**
     * Check if early stopping should trigger
     */
    shouldStopEarly() {
        if (!this.earlyStopping.enabled) return false;
        if (this.trials.length < this.earlyStopping.patience + 1) return false;

        // Check if no improvement in last N trials
        const recentTrials = this.trials.slice(-this.earlyStopping.patience);
        const recentBest = Math.max(...recentTrials.map(t => t.score));
        
        const improvement = recentBest - this.bestScore;
        return improvement < this.earlyStopping.minDelta;
    }

    /**
     * Show optimization UI
     */
    showOptimizationUI() {
        const container = document.getElementById('hyperoptContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">🎯 Hyperparameter Optimization</h3>
                    <button class="btn btn-danger btn-sm" onclick="hyperOptimizer.stopOptimization()">⏹️ Stop</button>
                </div>
                <div style="padding:20px">
                    <div class="alert alert-info">
                        Running ${this.strategy} optimization with ${this.maxTrials} trials...
                    </div>
                    <div id="trialsProgress"></div>
                    <div id="currentBest" style="margin-top:20px"></div>
                </div>
            </div>
        `;

        container.style.display = 'block';
    }

    /**
     * Update trial UI
     */
    updateTrialUI(trialNum, status, config, score = null) {
        const container = document.getElementById('trialsProgress');
        if (!container) return;

        const trialId = `trial-${trialNum}`;
        let trialEl = document.getElementById(trialId);

        if (!trialEl) {
            trialEl = document.createElement('div');
            trialEl.id = trialId;
            trialEl.className = 'alert alert-info';
            container.appendChild(trialEl);
        }

        const statusEmoji = {
            running: '⏳',
            completed: '✅',
            failed: '❌'
        };

        const configStr = Object.entries(config)
            .map(([k, v]) => `${k}: ${typeof v === 'number' ? v.toFixed(4) : v}`)
            .join(', ');

        trialEl.innerHTML = `
            ${statusEmoji[status]} <strong>Trial ${trialNum}/${this.maxTrials}</strong> - ${status}<br>
            <small>${configStr}</small>
            ${score !== null ? `<br><strong>Score: ${score.toFixed(2)}</strong>` : ''}
        `;

        trialEl.className = `alert alert-${status === 'completed' ? 'success' : status === 'failed' ? 'error' : 'info'}`;

        // Update current best
        if (this.bestConfig) {
            const bestEl = document.getElementById('currentBest');
            if (bestEl) {
                const bestStr = Object.entries(this.bestConfig)
                    .map(([k, v]) => `${k}: ${typeof v === 'number' ? v.toFixed(4) : v}`)
                    .join(', ');
                
                bestEl.innerHTML = `
                    <div class="card">
                        <div class="card-header"><h4>🏆 Current Best Configuration</h4></div>
                        <div style="padding:15px">
                            <p><strong>Score:</strong> ${this.bestScore.toFixed(2)}</p>
                            <p>${bestStr}</p>
                        </div>
                    </div>
                `;
            }
        }
    }

    /**
     * Show final optimization results
     */
    showOptimizationResults() {
        const container = document.getElementById('hyperoptContainer');
        if (!container) return;

        const bestStr = Object.entries(this.bestConfig)
            .map(([k, v]) => `<li><strong>${k}:</strong> ${typeof v === 'number' ? v.toFixed(4) : v}</li>`)
            .join('');

        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">✅ Optimization Complete</h3>
                </div>
                <div style="padding:20px">
                    <div class="alert alert-success">
                        <h4>🏆 Best Configuration Found</h4>
                        <p><strong>Score:</strong> ${this.bestScore.toFixed(2)}</p>
                        <ul>${bestStr}</ul>
                    </div>

                    <h4>Trial Summary</h4>
                    <p>Completed ${this.trials.length} trials</p>
                    
                    <div style="margin-top:20px;display:flex;gap:10px">
                        <button class="btn btn-primary" onclick="hyperOptimizer.applyBestConfig()">✨ Apply Best Config</button>
                        <button class="btn btn-secondary" onclick="hyperOptimizer.exportResults()">📥 Export Results</button>
                        <button class="btn btn-secondary" onclick="hyperOptimizer.visualizeResults()">📊 Visualize</button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Save best configuration
     */
    saveBestConfig() {
        if (!this.bestConfig) return;

        localStorage.setItem('hyperopt-best-config', JSON.stringify({
            config: this.bestConfig,
            score: this.bestScore,
            timestamp: Date.now()
        }));

        console.log('[HyperOptim] Best config saved:', this.bestConfig);
    }

    /**
     * Apply best configuration to training form
     */
    applyBestConfig() {
        if (!this.bestConfig) return;

        Object.keys(this.bestConfig).forEach(key => {
            const el = document.getElementById(key);
            if (el) {
                el.value = this.bestConfig[key];
            }
        });

        alert('Best configuration applied to training form!');
        
        // Switch to training tab
        if (typeof switchTab === 'function') {
            switchTab('training');
        }
    }

    /**
     * Export optimization results
     */
    exportResults() {
        const results = {
            strategy: this.strategy,
            maxTrials: this.maxTrials,
            trialsCompleted: this.trials.length,
            bestConfig: this.bestConfig,
            bestScore: this.bestScore,
            allTrials: this.trials,
            timestamp: Date.now()
        };

        const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `hyperopt-results-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Visualize optimization results
     */
    visualizeResults() {
        // Create visualization chart
        const canvas = document.createElement('canvas');
        canvas.id = 'hyperoptChart';
        canvas.style.height = '400px';
        
        const container = document.getElementById('hyperoptContainer');
        if (container) {
            container.appendChild(canvas);
        }

        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.trials.map(t => `Trial ${t.trialNum}`),
                datasets: [{
                    label: 'Trial Score',
                    data: this.trials.map(t => t.score),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Best Score So Far',
                    data: this.trials.map((t, idx) => 
                        Math.max(...this.trials.slice(0, idx + 1).map(tr => tr.score))
                    ),
                    borderColor: '#2dce89',
                    backgroundColor: 'rgba(45, 206, 137, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Optimization Progress'
                    }
                }
            }
        });
    }

    /**
     * Stop optimization
     */
    stopOptimization() {
        if (!confirm('Are you sure you want to stop optimization?')) return;
        
        this.maxTrials = this.currentTrial;
        alert('Optimization will stop after current trial completes');
    }

    /**
     * Helper: Cartesian product
     */
    cartesianProduct(arrays) {
        return arrays.reduce((acc, array) => 
            acc.flatMap(x => array.map(y => [...x, y])), [[]]
        );
    }
}

// Export for use in dashboard
if (typeof window !== 'undefined') {
    window.HyperparameterOptimizer = HyperparameterOptimizer;
}
