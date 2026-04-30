/**
 * Model Comparison & Benchmarking System
 * Side-by-side comparison, performance benchmarking, and leaderboards
 */

class ModelComparator {
    constructor() {
        this.selectedModels = [];
        this.benchmarkResults = new Map();
        this.comparisonChart = null;
    }

    /**
     * Add model to comparison
     */
    addModel(modelId) {
        if (this.selectedModels.includes(modelId)) return;
        if (this.selectedModels.length >= 4) {
            if (typeof showToast === 'function') showToast('Maximum 4 models can be compared at once', 'warn', 4000);
            return;
        }

        this.selectedModels.push(modelId);
        this.updateComparisonView();
    }

    /**
     * Remove model from comparison
     */
    removeModel(modelId) {
        this.selectedModels = this.selectedModels.filter(id => id !== modelId);
        this.updateComparisonView();
    }

    /**
     * Clear all selections
     */
    clearSelection() {
        this.selectedModels = [];
        this.updateComparisonView();
    }

    /**
     * Update comparison view
     */
    async updateComparisonView() {
        const container = document.getElementById('modelComparisonContainer');
        if (!container) return;

        if (this.selectedModels.length === 0) {
            container.innerHTML = '<p style="text-align:center;color:#888;padding:40px">Select models to compare</p>';
            return;
        }

        // Fetch model details
        const models = await this.fetchModelDetails(this.selectedModels);

        // Render comparison table
        container.innerHTML = this.renderComparisonTable(models);

        // Update comparison chart
        this.updateComparisonChart(models);
    }

    /**
     * Fetch model details
     */
    async fetchModelDetails(modelIds) {
        try {
            const response = await fetch('/status');
            const data = await response.json();

            if (!data.jobs) return [];

            return modelIds.map(id => {
                const job = data.jobs.find(j => j.id === id || j.name === id);
                return job || { id, name: 'Unknown', error: 'Not found' };
            });
        } catch (err) {
            console.error('[ModelComparator] Fetch error:', err);
            return [];
        }
    }

    /**
     * Render comparison table
     */
    renderComparisonTable(models) {
        const rows = [
            { label: 'Model Name', key: 'name' },
            { label: 'Final Loss', key: 'post_loss', format: (v) => v?.toFixed(4) || 'N/A' },
            { label: 'Initial Loss', key: 'pre_loss', format: (v) => v?.toFixed(4) || 'N/A' },
            { label: 'Improvement', key: null, format: (_, m) => {
                if (m.pre_loss && m.post_loss) {
                    const improvement = ((m.pre_loss - m.post_loss) / m.pre_loss * 100).toFixed(2);
                    return `${improvement}%`;
                }
                return 'N/A';
            }},
            { label: 'Duration', key: 'duration', format: (v) => v ? `${Math.round(v/60)}m` : 'N/A' },
            { label: 'Epochs', key: 'epochs' },
            { label: 'Batch Size', key: 'batch_size' },
            { label: 'Learning Rate', key: 'learning_rate', format: (v) => v?.toExponential(2) || 'N/A' },
            { label: 'LoRA Rank', key: 'lora_rank' },
            { label: 'LoRA Alpha', key: 'lora_alpha' },
            { label: 'Dataset', key: 'dataset' },
            { label: 'Status', key: 'status', format: (v) => `<span class="badge badge-${v === 'completed' ? 'success' : 'warning'}">${v || 'unknown'}</span>` }
        ];

        let html = '<table class="comparison-table"><thead><tr><th>Metric</th>';
        models.forEach(m => {
            html += `<th>${m.name || m.id}<button class="btn btn-danger btn-sm" onclick="modelComparator.removeModel('${m.id}')" style="margin-left:10px">✕</button></th>`;
        });
        html += '</tr></thead><tbody>';

        rows.forEach(row => {
            html += `<tr><td><strong>${row.label}</strong></td>`;
            models.forEach(model => {
                const value = row.key ? model[row.key] : null;
                const formatted = row.format ? row.format(value, model) : (value || 'N/A');
                html += `<td>${formatted}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';

        html += '<div style="margin-top:20px;display:flex;gap:10px">';
        html += '<button class="btn btn-primary" onclick="modelComparator.exportComparison()">📥 Export Comparison</button>';
        html += '<button class="btn btn-secondary" onclick="modelComparator.benchmarkSelected()">⚡ Run Benchmark</button>';
        html += '<button class="btn btn-secondary" onclick="modelComparator.clearSelection()">🗑️ Clear</button>';
        html += '</div>';

        return html;
    }

    /**
     * Update comparison chart
     */
    updateComparisonChart(models) {
        const canvas = document.getElementById('comparisonChart');
        if (!canvas) return;

        if (this.comparisonChart) {
            this.comparisonChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        this.comparisonChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Loss (inv)', 'Speed', 'Improvement', 'Efficiency', 'Stability'],
                datasets: models.map((model, idx) => ({
                    label: model.name || model.id,
                    data: this.calculateModelScores(model),
                    borderColor: this.getChartColor(idx),
                    backgroundColor: this.getChartColor(idx, 0.2),
                    pointBackgroundColor: this.getChartColor(idx)
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    /**
     * Calculate model scores for radar chart
     */
    calculateModelScores(model) {
        const lossScore = model.post_loss ? Math.min((1 / model.post_loss) * 10, 100) : 0;
        const speedScore = model.duration ? Math.min((3600 / model.duration) * 100, 100) : 0;
        const improvementScore = model.pre_loss && model.post_loss
            ? Math.min(((model.pre_loss - model.post_loss) / model.pre_loss) * 100, 100)
            : 0;
        const efficiencyScore = model.batch_size && model.duration
            ? Math.min((model.batch_size / model.duration) * 1000, 100)
            : 0;
        const stabilityScore = 75; // Placeholder - could calculate from loss variance

        return [lossScore, speedScore, improvementScore, efficiencyScore, stabilityScore];
    }

    /**
     * Get chart color by index
     */
    getChartColor(index, alpha = 1) {
        const colors = [
            `rgba(102, 126, 234, ${alpha})`,
            `rgba(240, 147, 251, ${alpha})`,
            `rgba(45, 206, 137, ${alpha})`,
            `rgba(255, 159, 64, ${alpha})`
        ];
        return colors[index % colors.length];
    }

    /**
     * Export comparison to CSV/JSON
     */
    async exportComparison() {
        const models = await this.fetchModelDetails(this.selectedModels);

        const format = prompt('Export format: json or csv?', 'json');
        if (!format || !['json', 'csv'].includes(format.toLowerCase())) return;

        let content, filename, type;

        if (format === 'json') {
            content = JSON.stringify(models, null, 2);
            filename = `comparison-${Date.now()}.json`;
            type = 'application/json';
        } else {
            // CSV format
            const headers = ['Name', 'Final Loss', 'Improvement %', 'Duration (min)', 'Epochs', 'Batch Size', 'Learning Rate', 'LoRA Rank'];
            const rows = models.map(m => [
                m.name || m.id,
                m.post_loss?.toFixed(4) || '',
                m.pre_loss && m.post_loss ? ((m.pre_loss - m.post_loss) / m.pre_loss * 100).toFixed(2) : '',
                m.duration ? Math.round(m.duration / 60) : '',
                m.epochs || '',
                m.batch_size || '',
                m.learning_rate || '',
                m.lora_rank || ''
            ]);

            content = [headers, ...rows].map(row => row.join(',')).join('\n');
            filename = `comparison-${Date.now()}.csv`;
            type = 'text/csv';
        }

        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Run performance benchmark on selected models
     */
    async benchmarkSelected() {
        if (this.selectedModels.length === 0) {
            if (typeof showToast === 'function') showToast('Please select models to benchmark', 'warn', 4000);
            return;
        }

        const container = document.getElementById('benchmarkResults');
        if (container) {
            container.innerHTML = '<div class="alert alert-info">Running benchmark... This may take a few minutes.</div>';
        }

        try {
            const response = await fetch('/api/benchmark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_ids: this.selectedModels })
            });

            const results = await response.json();
            this.benchmarkResults = new Map(results.map(r => [r.model_id, r]));
            this.displayBenchmarkResults(results);
        } catch (err) {
            console.error('[ModelComparator] Benchmark error:', err);
            if (container) {
                container.innerHTML = `<div class="alert alert-error">Benchmark failed: ${err.message}</div>`;
            }
        }
    }

    /**
     * Display benchmark results
     */
    displayBenchmarkResults(results) {
        const container = document.getElementById('benchmarkResults');
        if (!container) return;

        let html = '<div class="card"><div class="card-header"><h3>⚡ Benchmark Results</h3></div><table>';
        html += '<thead><tr><th>Model</th><th>Inference Time (ms)</th><th>Memory (MB)</th><th>Throughput (tok/s)</th><th>Score</th></tr></thead>';
        html += '<tbody>';

        results.forEach(result => {
            const score = this.calculateBenchmarkScore(result);
            html += `<tr>
                <td>${result.model_name}</td>
                <td>${result.inference_time?.toFixed(2) || 'N/A'}</td>
                <td>${result.memory_mb?.toFixed(0) || 'N/A'}</td>
                <td>${result.throughput?.toFixed(2) || 'N/A'}</td>
                <td class="metric-value metric-${score > 80 ? 'good' : score > 50 ? 'warning' : 'bad'}">${score}</td>
            </tr>`;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
    }

    /**
     * Calculate benchmark score
     */
    calculateBenchmarkScore(result) {
        const speedScore = result.inference_time ? Math.min(100, (100 / result.inference_time) * 100) : 0;
        const memoryScore = result.memory_mb ? Math.min(100, (2000 / result.memory_mb) * 100) : 0;
        const throughputScore = result.throughput ? Math.min(100, result.throughput) : 0;

        return Math.round((speedScore + memoryScore + throughputScore) / 3);
    }

    /**
     * Generate leaderboard
     */
    async generateLeaderboard() {
        try {
            const response = await fetch('/status');
            const data = await response.json();

            if (!data.jobs || data.jobs.length === 0) {
                return '<p style="text-align:center;color:#888">No jobs available for leaderboard</p>';
            }

            // Sort by performance score
            const ranked = data.jobs
                .filter(j => j.post_loss && j.status === 'completed')
                .map(j => ({
                    ...j,
                    score: this.calculateOverallScore(j)
                }))
                .sort((a, b) => b.score - a.score)
                .slice(0, 10);

            let html = '<table class="leaderboard-table">';
            html += '<thead><tr><th>Rank</th><th>Model</th><th>Loss</th><th>Duration</th><th>Score</th></tr></thead>';
            html += '<tbody>';

            ranked.forEach((job, idx) => {
                const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '';
                html += `<tr>
                    <td>${medal} #${idx + 1}</td>
                    <td>${job.name || 'Unknown'}</td>
                    <td>${job.post_loss.toFixed(4)}</td>
                    <td>${Math.round(job.duration / 60)}m</td>
                    <td class="metric-value metric-good">${job.score}</td>
                </tr>`;
            });

            html += '</tbody></table>';
            return html;
        } catch (err) {
            console.error('[ModelComparator] Leaderboard error:', err);
            return '<p style="color:#f44">Failed to generate leaderboard</p>';
        }
    }

    /**
     * Calculate overall score
     */
    calculateOverallScore(job) {
        const lossScore = job.post_loss ? (1 / job.post_loss) * 20 : 0;
        const improvementScore = job.pre_loss && job.post_loss
            ? ((job.pre_loss - job.post_loss) / job.pre_loss) * 30
            : 0;
        const efficiencyScore = job.duration && job.epochs
            ? Math.min((job.epochs / (job.duration / 3600)) * 25, 25)
            : 0;
        const qualityScore = 25; // Placeholder

        return Math.round(lossScore + improvementScore + efficiencyScore + qualityScore);
    }
}

// Export for use in dashboard
if (typeof window !== 'undefined') {
    window.ModelComparator = ModelComparator;
}
