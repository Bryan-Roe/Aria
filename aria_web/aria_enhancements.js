// Enhanced Aria Animations and Features
// Additional animations, particle effects, keyboard shortcuts, and voice commands

// ============================================
// NEW ANIMATIONS
// ============================================

// Spin animation
function performSpin() {
    const aria = document.getElementById('aria');
    aria.style.animation = 'spin360 1s ease-in-out';
    log('🌀 Spinning...');
    showFeedback('🌀 SPIN!', 'info');
    
    setTimeout(() => {
        aria.style.animation = '';
    }, 1000);
}

// Flip animation
function performFlip() {
    const aria = document.getElementById('aria');
    aria.style.animation = 'flip 0.8s ease-in-out';
    log('🤸 Flipping!');
    showFeedback('🤸 FLIP!', 'success');
    createEffect('sparkle', 50, 50);
    
    setTimeout(() => {
        aria.style.animation = '';
    }, 800);
}

// Bow animation
function performBow() {
    const aria = document.getElementById('aria');
    const ariaBody = aria.querySelector('.aria-body');
    
    ariaBody.style.transition = 'transform 0.6s ease-in-out';
    ariaBody.style.transform = 'rotateX(30deg) translateY(10px)';
    log('🙇 Bowing gracefully...');
    showFeedback('🙇 BOW', 'info');
    
    setTimeout(() => {
        ariaBody.style.transform = '';
    }, 1200);
}

// Celebrate animation with confetti
function performCelebrate() {
    log('🎉 Celebrating!');
    showFeedback('🎉 CELEBRATION!', 'success');
    
    // Trigger confetti burst
    for (let i = 0; i < 30; i++) {
        setTimeout(() => {
            const x = 30 + Math.random() * 40;
            const y = 20 + Math.random() * 30;
            createConfetti(x, y);
        }, i * 50);
    }
    
    // Jumping animation
    const aria = document.getElementById('aria');
    aria.style.animation = 'celebrate-jump 0.5s ease-in-out 3';
    setTimeout(() => {
        aria.style.animation = '';
    }, 1500);
}

// Shimmy/dance move
function performShimmy() {
    const aria = document.getElementById('aria');
    aria.style.animation = 'shimmy 1s ease-in-out';
    log('💃 Shimmy time!');
    showFeedback('💃 SHIMMY!', 'info');
    
    setTimeout(() => {
        aria.style.animation = '';
    }, 1000);
}

// ============================================
// PARTICLE EFFECTS SYSTEM
// ============================================

function createConfetti(xPercent, yPercent) {
    const confetti = document.createElement('div');
    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f7b731', '#5f27cd', '#00d2d3'];
    const shapes = ['●', '■', '▲', '★'];
    
    confetti.textContent = shapes[Math.floor(Math.random() * shapes.length)];
    confetti.style.cssText = `
        position: absolute;
        left: ${xPercent}%;
        bottom: ${yPercent}%;
        color: ${colors[Math.floor(Math.random() * colors.length)]};
        font-size: ${12 + Math.random() * 20}px;
        pointer-events: none;
        z-index: 1000;
        animation: confetti-fall ${1 + Math.random() * 2}s ease-out forwards;
    `;
    
    document.getElementById('stage').appendChild(confetti);
    setTimeout(() => confetti.remove(), 3000);
}

function createHeartParticles(xPercent, yPercent) {
    for (let i = 0; i < 5; i++) {
        setTimeout(() => {
            const heart = document.createElement('div');
            heart.textContent = '❤️';
            heart.style.cssText = `
                position: absolute;
                left: ${xPercent + (Math.random() - 0.5) * 10}%;
                bottom: ${yPercent}%;
                font-size: ${12 + Math.random() * 12}px;
                pointer-events: none;
                z-index: 1000;
                animation: heart-float ${2 + Math.random()}s ease-out forwards;
            `;
            document.getElementById('stage').appendChild(heart);
            setTimeout(() => heart.remove(), 3000);
        }, i * 100);
    }
}

function createSparkleTrail(xPercent, yPercent) {
    const sparkle = document.createElement('div');
    sparkle.textContent = '✨';
    sparkle.style.cssText = `
        position: absolute;
        left: ${xPercent}%;
        bottom: ${yPercent}%;
        font-size: 20px;
        pointer-events: none;
        z-index: 999;
        animation: sparkle-fade 0.8s ease-out forwards;
    `;
    document.getElementById('stage').appendChild(sparkle);
    setTimeout(() => sparkle.remove(), 800);
}

// ============================================
// EMOTION SYSTEM
// ============================================

const emotions = {
    happy: { emoji: '😊', color: '#f7b731', animation: 'bounce 0.5s ease-in-out 2' },
    sad: { emoji: '😢', color: '#778ca3', animation: 'droop 1s ease-in-out' },
    excited: { emoji: '🤩', color: '#ff6348', animation: 'vibrate 0.3s linear 5' },
    thinking: { emoji: '🤔', color: '#a29bfe', animation: 'tilt 1s ease-in-out infinite' },
    surprised: { emoji: '😲', color: '#fd79a8', animation: 'pop 0.4s ease-out' },
    love: { emoji: '😍', color: '#e84393', animation: 'pulse-love 0.6s ease-in-out 3' },
    angry: { emoji: '😠', color: '#d63031', animation: 'shake 0.3s linear 5' },
    sleepy: { emoji: '😴', color: '#636e72', animation: 'sway 2s ease-in-out infinite' }
};

function setEmotion(emotion) {
    if (!emotions[emotion]) {
        log(`⚠️ Unknown emotion: ${emotion}`, true);
        return;
    }
    
    const { emoji, color, animation } = emotions[emotion];
    const aria = document.getElementById('aria');
    
    // Update character mood
    characterState.mood = emotion;
    
    // Visual feedback
    showFeedback(`${emoji} ${emotion.toUpperCase()}`, 'info');
    log(`${emoji} Feeling ${emotion}...`);
    
    // Temporary animation
    aria.style.animation = animation;
    setTimeout(() => {
        aria.style.animation = '';
    }, 3000);
    
    // Show emotion bubble
    showEmotionBubble(emoji);
    
    // Special particle effects for certain emotions
    if (emotion === 'love') {
        const ariaRect = aria.getBoundingClientRect();
        const stageRect = document.getElementById('stage').getBoundingClientRect();
        const x = ((ariaRect.left + ariaRect.width / 2 - stageRect.left) / stageRect.width) * 100;
        const y = 100 - ((ariaRect.top - stageRect.top) / stageRect.height) * 100;
        createHeartParticles(x, y);
    } else if (emotion === 'excited') {
        performCelebrate();
    }
}

function showEmotionBubble(emoji) {
    const aria = document.getElementById('aria');
    const bubble = document.createElement('div');
    bubble.textContent = emoji;
    bubble.style.cssText = `
        position: absolute;
        top: -60px;
        left: 50%;
        transform: translateX(-50%) scale(0);
        font-size: 40px;
        background: white;
        border-radius: 50%;
        padding: 10px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        z-index: 100;
        animation: bubble-pop 2s ease-out forwards;
    `;
    aria.appendChild(bubble);
    setTimeout(() => bubble.remove(), 2000);
}

// ============================================
// KEYBOARD SHORTCUTS
// ============================================

const keyboardShortcuts = {
    'w': () => sendCommand('move up'),
    's': () => sendCommand('move down'),
    'a': () => sendCommand('move left'),
    'd': () => sendCommand('move right'),
    'j': () => sendCommand('jump'),
    'h': () => sendCommand('wave'),
    'b': () => performBow(),
    'f': () => performFlip(),
    'r': () => performSpin(),
    'c': () => performCelebrate(),
    'e': () => setEmotion('happy'),
    ' ': () => sendCommand('dance')
};

let keyboardEnabled = true;

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Don't trigger if typing in input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        if (!keyboardEnabled) return;
        
        const key = e.key.toLowerCase();
        if (keyboardShortcuts[key]) {
            e.preventDefault();
            keyboardShortcuts[key]();
        }
    });
    
    log('⌨️ Keyboard shortcuts enabled (W/A/S/D to move, J to jump, H to wave, etc.)');
}

function toggleKeyboard() {
    keyboardEnabled = !keyboardEnabled;
    log(keyboardEnabled ? '⌨️ Keyboard enabled' : '⌨️ Keyboard disabled');
    showFeedback(keyboardEnabled ? '⌨️ KEYBOARD ON' : '⌨️ KEYBOARD OFF', 'info');
}

// ============================================
// VOICE COMMANDS
// ============================================

let voiceRecognition = null;
let isListening = false;

function setupVoiceCommands() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        log('⚠️ Voice recognition not supported in this browser', true);
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    voiceRecognition = new SpeechRecognition();
    voiceRecognition.continuous = true;
    voiceRecognition.interimResults = false;
    voiceRecognition.lang = 'en-US';
    
    voiceRecognition.onresult = (event) => {
        const transcript = event.results[event.results.length - 1][0].transcript.trim();
        log(`🎤 Voice command: "${transcript}"`);
        document.getElementById('commandInput').value = transcript;
        sendCommand(transcript);
    };
    
    voiceRecognition.onerror = (event) => {
        log(`⚠️ Voice error: ${event.error}`, true);
        isListening = false;
        updateVoiceButton();
    };
    
    voiceRecognition.onend = () => {
        if (isListening) {
            voiceRecognition.start(); // Restart if still enabled
        }
    };
    
    log('🎤 Voice commands ready');
}

function toggleVoiceCommands() {
    if (!voiceRecognition) {
        setupVoiceCommands();
        if (!voiceRecognition) return;
    }
    
    isListening = !isListening;
    
    if (isListening) {
        try {
            voiceRecognition.start();
            log('🎤 Listening for voice commands...');
            showFeedback('🎤 LISTENING...', 'success');
        } catch (e) {
            log('⚠️ Could not start voice recognition', true);
            isListening = false;
        }
    } else {
        voiceRecognition.stop();
        log('🎤 Voice commands stopped');
        showFeedback('🎤 STOPPED', 'warning');
    }
    
    updateVoiceButton();
}

function updateVoiceButton() {
    const btn = document.getElementById('voiceBtn');
    if (btn) {
        btn.textContent = isListening ? '🎤 Stop' : '🎤 Voice';
        btn.style.background = isListening ? '#e74c3c' : '#27ae60';
    }
}

// ============================================
// GESTURE RECOGNITION (Mouse/Touch)
// ============================================

let gestureStart = null;

function setupGestureRecognition() {
    const stage = document.getElementById('stage');
    
    stage.addEventListener('mousedown', (e) => {
        if (e.target.id !== 'stage') return;
        gestureStart = { x: e.clientX, y: e.clientY, time: Date.now() };
    });
    
    stage.addEventListener('mouseup', (e) => {
        if (!gestureStart || e.target.id !== 'stage') return;
        
        const deltaX = e.clientX - gestureStart.x;
        const deltaY = e.clientY - gestureStart.y;
        const deltaTime = Date.now() - gestureStart.time;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        // Swipe gestures
        if (distance > 100 && deltaTime < 500) {
            if (Math.abs(deltaX) > Math.abs(deltaY)) {
                if (deltaX > 0) {
                    sendCommand('move right');
                    log('👉 Swipe right gesture');
                } else {
                    sendCommand('move left');
                    log('👈 Swipe left gesture');
                }
            } else {
                if (deltaY < 0) {
                    sendCommand('jump');
                    log('👆 Swipe up gesture');
                } else {
                    sendCommand('sit down');
                    log('👇 Swipe down gesture');
                }
            }
        }
        // Double-tap to celebrate
        else if (distance < 10 && deltaTime < 300) {
            performCelebrate();
            log('👏 Double-tap gesture');
        }
        
        gestureStart = null;
    });
    
    log('👆 Gesture recognition enabled (swipe to move, double-tap to celebrate)');
}

// ============================================
// ANIMATION CSS (to be added to HTML)
// ============================================

function injectEnhancedStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin360 {
            from { transform: translateX(-50%) rotateY(0deg); }
            to { transform: translateX(-50%) rotateY(360deg); }
        }
        
        @keyframes flip {
            0% { transform: translateX(-50%) rotateX(0deg); }
            50% { transform: translateX(-50%) rotateX(180deg) translateY(-30px); }
            100% { transform: translateX(-50%) rotateX(360deg); }
        }
        
        @keyframes shimmy {
            0%, 100% { transform: translateX(-50%) rotateZ(0deg); }
            25% { transform: translateX(-50%) rotateZ(-5deg) translateX(-5px); }
            75% { transform: translateX(-50%) rotateZ(5deg) translateX(5px); }
        }
        
        @keyframes celebrate-jump {
            0%, 100% { transform: translateX(-50%) translateY(0) scale(1); }
            50% { transform: translateX(-50%) translateY(-40px) scale(1.1); }
        }
        
        @keyframes confetti-fall {
            0% { transform: translateY(0) rotateZ(0deg); opacity: 1; }
            100% { transform: translateY(200px) rotateZ(720deg); opacity: 0; }
        }
        
        @keyframes heart-float {
            0% { transform: translateY(0) scale(1); opacity: 1; }
            100% { transform: translateY(-100px) scale(1.5); opacity: 0; }
        }
        
        @keyframes sparkle-fade {
            0% { transform: scale(1) rotate(0deg); opacity: 1; }
            100% { transform: scale(2) rotate(180deg); opacity: 0; }
        }
        
        @keyframes bubble-pop {
            0% { transform: translateX(-50%) scale(0); opacity: 0; }
            50% { transform: translateX(-50%) scale(1.2); opacity: 1; }
            100% { transform: translateX(-50%) scale(1); opacity: 0; }
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateX(-50%) translateY(0); }
            50% { transform: translateX(-50%) translateY(-20px); }
        }
        
        @keyframes droop {
            0% { transform: translateX(-50%); }
            100% { transform: translateX(-50%) translateY(5px) scaleY(0.95); }
        }
        
        @keyframes vibrate {
            0%, 100% { transform: translateX(-50%); }
            25% { transform: translateX(-50%) translateX(-3px); }
            75% { transform: translateX(-50%) translateX(3px); }
        }
        
        @keyframes tilt {
            0%, 100% { transform: translateX(-50%) rotateZ(0deg); }
            50% { transform: translateX(-50%) rotateZ(10deg); }
        }
        
        @keyframes pop {
            0% { transform: translateX(-50%) scale(1); }
            50% { transform: translateX(-50%) scale(1.2); }
            100% { transform: translateX(-50%) scale(1); }
        }
        
        @keyframes pulse-love {
            0%, 100% { transform: translateX(-50%) scale(1); filter: brightness(1); }
            50% { transform: translateX(-50%) scale(1.15); filter: brightness(1.3); }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(-50%); }
            25% { transform: translateX(-50%) translateX(-5px); }
            75% { transform: translateX(-50%) translateX(5px); }
        }
        
        @keyframes sway {
            0%, 100% { transform: translateX(-50%) rotateZ(-3deg); }
            50% { transform: translateX(-50%) rotateZ(3deg); }
        }
    `;
    document.head.appendChild(style);
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    injectEnhancedStyles();
    setupKeyboardShortcuts();
    setupGestureRecognition();
    log('✨ Enhanced features loaded!');
    log('💡 Try: Keyboard (W/A/S/D), Voice (click 🎤), Gestures (swipe stage)');
});
