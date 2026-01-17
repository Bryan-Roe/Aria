/**
 * Training Session History Tracker
 * Persist training sessions and enable replay/comparison
 * 
 * Features:
 * - Session persistence (localStorage/IndexedDB)
 * - Session comparison
 * - Config replay (load previous settings)
 * - Export to CSV/JSON
 * - Filtering by date/status/model
 */

class TrainingSessionHistory {
    constructor(options = {}) {
        this.config = {
            storage: options.storage || 'localStorage', // or 'indexedDB'
            maxSessions: options.maxSessions || 100,
            autoSave: options.autoSave !== false,
            ...options
        };
        this.sessions = [];
        this.currentSession = null;
        this.init();
    }
    
    async init() {
        // Load existing sessions
        await this.loadSessions();
        
        // Setup auto-save if enabled
        if (this.config.autoSave) {
            this.setupAutoSave();
        }
    }
    
    /**
     * Load sessions from storage
     */
    async loadSessions() {
        if (this.config.storage === 'localStorage') {
            const stored = localStorage.getItem('qai_training_sessions');
            if (stored) {
                try {
                    this.sessions = JSON.parse(stored);
                } catch (err) {
                    console.error('Failed to load sessions:', err);
                    this.sessions = [];
                }
            }
        } else if (this.config.storage === 'indexedDB') {
            // IndexedDB implementation (future enhancement)
            console.warn('IndexedDB storage not yet implemented, falling back to localStorage');
            this.config.storage = 'localStorage';
            await this.loadSessions();
        }
    }
    
    /**
     * Save sessions to storage
     */
    async saveSessions() {
        // Keep only max sessions
        if (this.sessions.length > this.config.maxSessions) {
            this.sessions = this.sessions.slice(-this.config.maxSessions);
        }
        
        if (this.config.storage === 'localStorage') {
            try {
                localStorage.setItem('qai_training_sessions', JSON.stringify(this.sessions));
            } catch (err) {
                console.error('Failed to save sessions:', err);
            }
        }
    }
    
    /**
     * Start a new training session
     */
    startSession(config) {
        this.currentSession = {
            id: `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            startTime: Date.now(),
            endTime: null,
            status: 'running',
            config: JSON.parse(JSON.stringify(config)), // Deep clone
            metrics: {
                initialLoss: null,
                finalLoss: null,
                bestLoss: null,
                epochs: [],
                avgLossPerEpoch: []
            },
            anomalies: [],
            notes: ''
        };
        
        return this.currentSession.id;
    }
    
    /**
     * Update current session metrics
     */
    updateSession(updates) {
        if (!this.currentSession) return;
        
        Object.assign(this.currentSession, updates);
        
        if (this.config.autoSave) {
            this.saveSessions();
        }
    }
    
    /**
     * End current session
     */
    endSession(status = 'completed', finalMetrics = {}) {
        if (!this.currentSession) return;
        
        this.currentSession.endTime = Date.now();
        this.currentSession.status = status;
        this.currentSession.duration = this.currentSession.endTime - this.currentSession.startTime;
        Object.assign(this.currentSession.metrics, finalMetrics);
        
        // Add to history
        this.sessions.push(this.currentSession);
        this.currentSession = null;
        
        this.saveSessions();
    }
    
    /**
     * Get all sessions
     */
    getAllSessions() {
        return this.sessions;
    }
    
    /**
     * Get session by ID
     */
    getSessionById(id) {
        return this.sessions.find(s => s.id === id);
    }
    
    /**
     * Filter sessions
     */
    filterSessions(filters = {}) {
        let filtered = [...this.sessions];
        
        // Filter by status
        if (filters.status) {
            filtered = filtered.filter(s => s.status === filters.status);
        }
        
        // Filter by model
        if (filters.model) {
            filtered = filtered.filter(s => 
                s.config.model && s.config.model.includes(filters.model)
            );
        }
        
        // Filter by dataset
        if (filters.dataset) {
            filtered = filtered.filter(s => 
                s.config.dataset && s.config.dataset.includes(filters.dataset)
            );
        }
        
        // Filter by date range
        if (filters.startDate) {
            const start = new Date(filters.startDate).getTime();
            filtered = filtered.filter(s => s.startTime >= start);
        }
        
        if (filters.endDate) {
            const end = new Date(filters.endDate).getTime();
            filtered = filtered.filter(s => s.startTime <= end);
        }
        
        // Filter by min loss
        if (filters.minLoss !== undefined) {
            filtered = filtered.filter(s => 
                s.metrics.finalLoss !== null && s.metrics.finalLoss >= filters.minLoss
            );
        }
        
        // Filter by max loss
        if (filters.maxLoss !== undefined) {
            filtered = filtered.filter(s => 
                s.metrics.finalLoss !== null && s.metrics.finalLoss <= filters.maxLoss
            );
        }
        
        return filtered;
    }
    
    /**
     * Compare sessions
     */
    compareSessions(sessionIds) {
        const sessions = sessionIds.map(id => this.getSessionById(id)).filter(Boolean);
        
        if (sessions.length === 0) return null;
        
        return {
            sessions,
            comparison: {
                bestLoss: Math.min(...sessions.map(s => s.metrics.finalLoss || Infinity)),
                worstLoss: Math.max(...sessions.map(s => s.metrics.finalLoss || 0)),
                avgLoss: sessions.reduce((sum, s) => sum + (s.metrics.finalLoss || 0), 0) / sessions.length,
                totalDuration: sessions.reduce((sum, s) => sum + (s.duration || 0), 0),
                avgDuration: sessions.reduce((sum, s) => sum + (s.duration || 0), 0) / sessions.length,
                statusBreakdown: sessions.reduce((acc, s) => {
                    acc[s.status] = (acc[s.status] || 0) + 1;
                    return acc;
                }, {})
            }
        };
    }
    
    /**
     * Replay session config
     */
    replaySession(sessionId) {
        const session = this.getSessionById(sessionId);
        if (!session) return null;
        
        return JSON.parse(JSON.stringify(session.config)); // Deep clone
    }
    
    /**
     * Export sessions to JSON
     */
    exportToJSON(sessionIds = null) {
        const sessions = sessionIds 
            ? sessionIds.map(id => this.getSessionById(id)).filter(Boolean)
            : this.sessions;
        
        return JSON.stringify(sessions, null, 2);
    }
    
    /**
     * Export sessions to CSV
     */
    exportToCSV(sessionIds = null) {
        const sessions = sessionIds 
            ? sessionIds.map(id => this.getSessionById(id)).filter(Boolean)
            : this.sessions;
        
        if (sessions.length === 0) return '';
        
        // CSV headers
        const headers = [
            'ID', 'Start Time', 'Duration (min)', 'Status',
            'Model', 'Dataset', 'Epochs', 'Batch Size', 'Learning Rate',
            'LoRA Rank', 'Initial Loss', 'Final Loss', 'Best Loss',
            'Anomalies', 'Notes'
        ];
        
        // CSV rows
        const rows = sessions.map(s => [
            s.id,
            new Date(s.startTime).toISOString(),
            s.duration ? Math.round(s.duration / 60000) : 'N/A',
            s.status,
            s.config.model || 'N/A',
            s.config.dataset || 'N/A',
            s.config.epochs || 'N/A',
            s.config.batch_size || s.config.batchSize || 'N/A',
            s.config.learning_rate || s.config.learningRate || 'N/A',
            s.config.lora_rank || s.config.loraRank || 'N/A',
            s.metrics.initialLoss || 'N/A',
            s.metrics.finalLoss || 'N/A',
            s.metrics.bestLoss || 'N/A',
            s.anomalies.length,
            s.notes ? `"${s.notes.replace(/"/g, '""')}"` : ''
        ]);
        
        return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    }
    
    /**
     * Delete session
     */
    deleteSession(sessionId) {
        this.sessions = this.sessions.filter(s => s.id !== sessionId);
        this.saveSessions();
    }
    
    /**
     * Clear all sessions
     */
    clearAllSessions() {
        this.sessions = [];
        this.saveSessions();
    }
    
    /**
     * Setup auto-save
     */
    setupAutoSave() {
        // Save every 30 seconds if there's a current session
        setInterval(() => {
            if (this.currentSession) {
                // Find and update in sessions array
                const index = this.sessions.findIndex(s => s.id === this.currentSession.id);
                if (index >= 0) {
                    this.sessions[index] = this.currentSession;
                }
                this.saveSessions();
            }
        }, 30000);
    }
    
    /**
     * Get statistics
     */
    getStatistics() {
        const completed = this.sessions.filter(s => s.status === 'completed');
        
        return {
            total: this.sessions.length,
            completed: completed.length,
            failed: this.sessions.filter(s => s.status === 'failed').length,
            running: this.sessions.filter(s => s.status === 'running').length,
            avgDuration: completed.length > 0
                ? completed.reduce((sum, s) => sum + (s.duration || 0), 0) / completed.length
                : 0,
            avgFinalLoss: completed.length > 0
                ? completed.reduce((sum, s) => sum + (s.metrics.finalLoss || 0), 0) / completed.length
                : 0,
            bestSession: completed.length > 0
                ? completed.reduce((best, s) => 
                    (s.metrics.finalLoss || Infinity) < (best.metrics.finalLoss || Infinity) ? s : best
                  )
                : null
        };
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.TrainingSessionHistory = TrainingSessionHistory;
}
