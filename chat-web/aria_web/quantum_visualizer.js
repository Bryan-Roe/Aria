// Quantum State 3D Visualizer for Aria
// Renders quantum states, Bloch spheres, and quantum effects in the 3D world

class QuantumVisualizer {
    constructor(stage, aria) {
        this.stage = stage;
        this.aria = aria;
        this.visualizationActive = false;
        this.blochSpheres = [];
        this.quantumParticles = [];
        this.entanglementLines = [];
        this.updateInterval = null;
        
        this.initQuantumUI();
        console.log('✓ Quantum Visualizer initialized');
    }
    
    initQuantumUI() {
        // Create quantum control panel
        const panel = document.createElement('div');
        panel.id = 'quantum-panel';
        panel.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(20, 20, 50, 0.9);
            border: 2px solid #00ffff;
            border-radius: 8px;
            padding: 15px;
            color: #00ffff;
            font-family: 'Courier New', monospace;
            min-width: 250px;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
            z-index: 1000;
        `;
        
        panel.innerHTML = `
            <h3 style="margin: 0 0 10px 0; font-size: 16px;">⚛️ Quantum Control</h3>
            <button id="toggle-quantum-viz" class="quantum-btn">Enable Visualization</button>
            <button id="quantum-predict-behavior" class="quantum-btn">Predict Behavior</button>
            <button id="quantum-generate-world" class="quantum-btn">Generate World</button>
            <div id="quantum-status" style="margin-top: 10px; font-size: 12px;"></div>
            <div id="quantum-metrics" style="margin-top: 10px; font-size: 11px;"></div>
        `;
        
        document.body.appendChild(panel);
        
        // Add CSS for quantum buttons
        const style = document.createElement('style');
        style.textContent = `
            .quantum-btn {
                display: block;
                width: 100%;
                margin: 5px 0;
                padding: 8px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: 1px solid #00ffff;
                border-radius: 4px;
                color: white;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
            }
            .quantum-btn:hover {
                background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
                box-shadow: 0 0 15px rgba(0, 255, 255, 0.7);
                transform: translateY(-2px);
            }
            .quantum-btn:active {
                transform: translateY(0);
            }
            .quantum-btn.active {
                background: linear-gradient(135deg, #00ff88 0%, #00ccff 100%);
                border-color: #00ff88;
            }
            .bloch-sphere {
                position: absolute;
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 2px solid rgba(0, 255, 255, 0.6);
                background: radial-gradient(circle, rgba(100, 100, 255, 0.3), rgba(0, 0, 100, 0.2));
                box-shadow: 0 0 20px rgba(0, 255, 255, 0.5), inset 0 0 20px rgba(0, 255, 255, 0.3);
                transition: all 0.5s ease;
                pointer-events: none;
            }
            .quantum-particle {
                position: absolute;
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: radial-gradient(circle, #00ffff, #0088ff);
                box-shadow: 0 0 10px #00ffff;
                pointer-events: none;
                animation: quantumFloat 3s infinite ease-in-out;
            }
            .entanglement-line {
                position: absolute;
                height: 2px;
                background: linear-gradient(90deg, rgba(0, 255, 255, 0.8), rgba(255, 0, 255, 0.8));
                box-shadow: 0 0 5px rgba(0, 255, 255, 0.8);
                pointer-events: none;
                animation: quantumPulse 2s infinite;
            }
            @keyframes quantumFloat {
                0%, 100% { transform: translateY(0) scale(1); opacity: 1; }
                50% { transform: translateY(-20px) scale(1.2); opacity: 0.7; }
            }
            @keyframes quantumPulse {
                0%, 100% { opacity: 0.8; }
                50% { opacity: 0.3; }
            }
            @keyframes blochRotate {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        // Event listeners
        document.getElementById('toggle-quantum-viz').addEventListener('click', () => {
            this.toggleVisualization();
        });
        
        document.getElementById('quantum-predict-behavior').addEventListener('click', () => {
            this.predictBehavior();
        });
        
        document.getElementById('quantum-generate-world').addEventListener('click', () => {
            this.generateQuantumWorld();
        });
    }
    
    async toggleVisualization() {
        this.visualizationActive = !this.visualizationActive;
        const btn = document.getElementById('toggle-quantum-viz');
        
        if (this.visualizationActive) {
            btn.textContent = 'Disable Visualization';
            btn.classList.add('active');
            await this.startVisualization();
        } else {
            btn.textContent = 'Enable Visualization';
            btn.classList.remove('active');
            this.stopVisualization();
        }
    }
    
    async startVisualization() {
        log('🌀 Quantum visualization enabled');
        this.updateStatus('Fetching quantum state...');
        
        try {
            const response = await fetch('/api/aria/quantum/state');
            const data = await response.json();
            
            if (data.enabled) {
                this.renderBlochSpheres(data.bloch_vectors || []);
                this.updateMetrics(data);
                this.createQuantumParticles(20);
                
                // Start continuous updates
                this.updateInterval = setInterval(() => {
                    this.updateQuantumVisualization();
                }, 2000);
                
                this.updateStatus('✓ Quantum visualization active');
            } else {
                this.updateStatus('⚠ Quantum unavailable: ' + (data.message || data.error));
            }
        } catch (error) {
            console.error('Quantum visualization error:', error);
            this.updateStatus('❌ Connection failed');
        }
    }
    
    stopVisualization() {
        log('Quantum visualization disabled');
        this.updateStatus('Visualization stopped');
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        // Clear all visual elements
        this.blochSpheres.forEach(sphere => sphere.remove());
        this.quantumParticles.forEach(particle => particle.remove());
        this.entanglementLines.forEach(line => line.remove());
        
        this.blochSpheres = [];
        this.quantumParticles = [];
        this.entanglementLines = [];
    }
    
    renderBlochSpheres(blochVectors) {
        // Clear existing spheres
        this.blochSpheres.forEach(sphere => sphere.remove());
        this.blochSpheres = [];
        
        blochVectors.forEach((vec, index) => {
            const sphere = document.createElement('div');
            sphere.className = 'bloch-sphere';
            sphere.id = `bloch-${vec.qubit}`;
            
            // Position near the character
            const baseX = 20 + (index * 100);
            const baseY = 10;
            
            sphere.style.left = baseX + '%';
            sphere.style.top = baseY + '%';
            
            // Create state vector indicator
            const indicator = document.createElement('div');
            indicator.style.cssText = `
                position: absolute;
                width: 4px;
                height: 40px;
                background: linear-gradient(180deg, #ff00ff, #00ffff);
                left: 50%;
                top: 50%;
                transform-origin: bottom center;
                transform: translate(-50%, -100%) 
                    rotateX(${vec.theta * 180 / Math.PI}deg) 
                    rotateZ(${vec.phi * 180 / Math.PI}deg);
                box-shadow: 0 0 10px #00ffff;
            `;
            sphere.appendChild(indicator);
            
            // Add qubit label
            const label = document.createElement('div');
            label.textContent = `Q${vec.qubit}`;
            label.style.cssText = `
                position: absolute;
                bottom: -20px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 10px;
                color: #00ffff;
                font-weight: bold;
            `;
            sphere.appendChild(label);
            
            this.stage.appendChild(sphere);
            this.blochSpheres.push(sphere);
            
            // Animate rotation
            sphere.style.animation = 'blochRotate 10s linear infinite';
        });
    }
    
    createQuantumParticles(count) {
        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.className = 'quantum-particle';
            
            // Random position around character
            const angle = (Math.PI * 2 * i) / count;
            const radius = 15 + Math.random() * 20;
            const x = 50 + Math.cos(angle) * radius;
            const y = 50 + Math.sin(angle) * radius;
            
            particle.style.left = x + '%';
            particle.style.top = y + '%';
            particle.style.animationDelay = (i * 0.1) + 's';
            
            this.stage.appendChild(particle);
            this.quantumParticles.push(particle);
        }
    }
    
    async updateQuantumVisualization() {
        try {
            const response = await fetch('/api/aria/quantum/state');
            const data = await response.json();
            
            if (data.enabled && data.bloch_vectors) {
                // Update Bloch sphere orientations
                data.bloch_vectors.forEach((vec, index) => {
                    const sphere = document.getElementById(`bloch-${vec.qubit}`);
                    if (sphere) {
                        const indicator = sphere.querySelector('div');
                        if (indicator) {
                            indicator.style.transform = `translate(-50%, -100%) 
                                rotateX(${vec.theta * 180 / Math.PI}deg) 
                                rotateZ(${vec.phi * 180 / Math.PI}deg)`;
                        }
                    }
                });
                
                this.updateMetrics(data);
            }
        } catch (error) {
            console.error('Quantum update error:', error);
        }
    }
    
    async predictBehavior() {
        this.updateStatus('Computing quantum prediction...');
        log('🔮 Requesting quantum behavior prediction');
        
        try {
            // Get current world context
            const context = {
                position: characterState.position,
                expression: characterState.mood,
                objects: activeObjects,
                held_object: characterState.heldObject
            };
            
            const response = await fetch('/api/aria/quantum/predict', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({context})
            });
            
            const result = await response.json();
            
            if (result.action) {
                log(`⚛️ Quantum prediction: ${result.action.action} (confidence: ${(result.quantum_confidence * 100).toFixed(1)}%)`);
                this.updateStatus(`Predicted: ${result.action.action}`);
                
                // Execute the predicted action
                if (result.action.action !== 'wait') {
                    await executeAction(result.action);
                }
                
                // Show quantum state
                if (result.quantum_state) {
                    this.visualizeQuantumState(result.quantum_state);
                }
            }
        } catch (error) {
            console.error('Quantum prediction error:', error);
            this.updateStatus('❌ Prediction failed');
        }
    }
    
    async generateQuantumWorld() {
        this.updateStatus('Generating quantum world...');
        log('🌌 Generating quantum-themed world');
        
        try {
            const theme = 'quantum';  // Can be made selectable
            
            const response = await fetch('/api/aria/world', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({theme, use_quantum: true})
            });
            
            const world = await response.json();
            
            if (world.objects) {
                log(`✓ Generated ${Object.keys(world.objects).length} quantum objects`);
                this.updateStatus(`Created ${world.theme} world`);
                
                // Apply the new world (integrate with existing world management)
                this.applyQuantumWorld(world);
            }
        } catch (error) {
            console.error('Quantum world generation error:', error);
            this.updateStatus('❌ Generation failed');
        }
    }
    
    applyQuantumWorld(world) {
        // Change background
        if (world.environment && world.environment.background_color) {
            this.stage.style.background = world.environment.background_color;
        }
        
        // Add quantum-specific effects
        if (world.effects && world.effects.includes('quantum_glow')) {
            this.stage.style.boxShadow = '0 0 50px rgba(0, 255, 255, 0.3) inset';
        }
        
        // Create new objects
        if (world.objects) {
            Object.entries(world.objects).forEach(([id, obj]) => {
                this.createQuantumObject(id, obj);
            });
        }
        
        log(`🌟 Quantum world "${world.theme}" applied (method: ${world.method})`);
    }
    
    createQuantumObject(id, objData) {
        // Remove existing object with same ID
        const existing = document.getElementById(id);
        if (existing) existing.remove();
        
        const obj = document.createElement('div');
        obj.id = id;
        obj.className = 'stage-object quantum-object';
        obj.textContent = this.getObjectEmoji(objData.type);
        
        obj.style.cssText = `
            position: absolute;
            left: ${objData.position.x}%;
            top: ${objData.position.y}%;
            font-size: ${24 * objData.scale}px;
            transform: rotate(${objData.rotation}deg) scale(${objData.scale});
            filter: drop-shadow(0 0 10px ${objData.color || '#00ffff'});
            transition: all 0.5s ease;
            animation: quantumFloat 4s infinite ease-in-out;
        `;
        
        this.stage.appendChild(obj);
    }
    
    getObjectEmoji(type) {
        const emojiMap = {
            'qubit_sphere': '⚛️',
            'entangled_pair': '🔗',
            'quantum_gate': '🚪',
            'superposition_cloud': '☁️',
            'cube': '🟦',
            'sphere': '🔵',
            'cylinder': '🥫',
            'pyramid': '🔺'
        };
        return emojiMap[type] || '✨';
    }
    
    visualizeQuantumState(state) {
        // Create temporary visualization of quantum state vector
        const viz = document.createElement('div');
        viz.style.cssText = `
            position: absolute;
            left: 50%;
            top: 30%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #00ffff;
            border-radius: 8px;
            padding: 10px;
            color: #00ffff;
            font-size: 11px;
            font-family: 'Courier New', monospace;
            z-index: 2000;
            max-width: 300px;
        `;
        
        const bars = state.map((val, i) => {
            const barWidth = Math.abs(val) * 100;
            return `
                <div style="margin: 3px 0;">
                    <span style="display: inline-block; width: 30px;">B${i}:</span>
                    <div style="display: inline-block; width: ${barWidth}%; height: 10px; 
                         background: linear-gradient(90deg, #00ffff, #ff00ff); 
                         border-radius: 2px;"></div>
                    <span style="margin-left: 5px;">${val.toFixed(3)}</span>
                </div>
            `;
        }).join('');
        
        viz.innerHTML = `<div style="font-weight: bold; margin-bottom: 5px;">Quantum State</div>${bars}`;
        this.stage.appendChild(viz);
        
        // Auto-remove after 3 seconds
        setTimeout(() => viz.remove(), 3000);
    }
    
    updateStatus(message) {
        const statusEl = document.getElementById('quantum-status');
        if (statusEl) {
            statusEl.textContent = message;
        }
    }
    
    updateMetrics(data) {
        const metricsEl = document.getElementById('quantum-metrics');
        if (!metricsEl) return;
        
        let html = '<div style="font-weight: bold; margin-bottom: 5px;">Metrics</div>';
        
        if (data.entanglement !== undefined) {
            html += `<div>Entanglement: ${(data.entanglement * 100).toFixed(1)}%</div>`;
        }
        
        if (data.measurement_probabilities) {
            const topProb = Math.max(...data.measurement_probabilities);
            html += `<div>Max Probability: ${(topProb * 100).toFixed(1)}%</div>`;
        }
        
        if (data.bloch_vectors) {
            html += `<div>Active Qubits: ${data.bloch_vectors.length}</div>`;
        }
        
        metricsEl.innerHTML = html;
    }
}

// Initialize quantum visualizer when page loads
let quantumVisualizer;

document.addEventListener('DOMContentLoaded', () => {
    // Wait for stage and aria to be available
    setTimeout(() => {
        const stage = document.getElementById('stage');
        const aria = document.getElementById('aria');
        
        if (stage && aria) {
            quantumVisualizer = new QuantumVisualizer(stage, aria);
        } else {
            console.warn('Stage or Aria not found, quantum visualizer not initialized');
        }
    }, 1000);
});

// Helper function to execute quantum-predicted actions
async function executeAction(action) {
    log(`🎬 Executing quantum action: ${action.action}`);
    
    switch(action.action) {
        case 'move':
            if (action.target) {
                moveToPosition(action.target.x, action.target.y, action.speed || 1.0);
            }
            break;
        case 'say':
            if (action.text) {
                speakText(action.text, action.emotion || 'neutral');
            }
            break;
        case 'pickup':
            if (action.object_id) {
                pickupObject(action.object_id);
            }
            break;
        case 'gesture':
            if (action.gesture_type) {
                performGesture(action.gesture_type);
            }
            break;
        default:
            log(`Unknown action: ${action.action}`);
    }
}
