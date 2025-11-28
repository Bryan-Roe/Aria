// Aria Visual Command Controller
const aria = document.getElementById('aria');
const ariaMouth = document.getElementById('ariaMouth');
const ariaArmLeft = document.getElementById('ariaArmLeft');
const ariaArmRight = document.getElementById('ariaArmRight');
const ariaLegLeft = document.getElementById('ariaLegLeft');
const ariaLegRight = document.getElementById('ariaLegRight');
const stage = document.getElementById('stage');
const commandInput = document.getElementById('commandInput');
const logContainer = document.getElementById('logContainer');

// Additional DOM references (used by idle/poses/expressive moves)
const ariaHead = document.querySelector('.aria-head');
const ariaBody = document.querySelector('.aria-body');
const ariaEyes = document.querySelectorAll('.aria-eye');
const ariaEyeLeft = ariaEyes[0];
const ariaEyeRight = ariaEyes[1];

// AI-Controlled Character State
let characterState = {
    mood: 'neutral',
    energy: 50,
    personality: 'balanced',
    colors: {
        hair: '#8B4513',
        skin: '#FFD4A3',
        body: '#667eea',
        legs: '#555',
        feet: '#8B4513'
    },
    size: 1.0,
    style: 'default',
    heldObject: null,
    heldObjectElement: null
};

// Visual feedback function
function showFeedback(message) {
    const feedback = document.createElement('div');
    feedback.textContent = message;
    feedback.style.cssText = 'position:absolute; top:20px; left:50%; transform:translateX(-50%); background:#e74c3c; color:white; padding:15px 30px; border-radius:15px; font-size:28px; font-weight:bold; z-index:999; box-shadow:0 5px 20px rgba(0,0,0,0.3); animation:pulse 0.5s ease;';
    stage.appendChild(feedback);
    setTimeout(() => feedback.remove(), 2500);
}

// AI-Driven Character Generation
function analyzeAIResponse(text) {
    const lowerText = text.toLowerCase();
    
    // Detect mood from response
    if (lowerText.includes('happy') || lowerText.includes('great') || lowerText.includes('wonderful') || lowerText.includes('excited')) {
        return { mood: 'happy', energy: 80 };
    } else if (lowerText.includes('sad') || lowerText.includes('sorry') || lowerText.includes('unfortunate')) {
        return { mood: 'sad', energy: 30 };
    } else if (lowerText.includes('angry') || lowerText.includes('frustrated')) {
        return { mood: 'angry', energy: 90 };
    } else if (lowerText.includes('calm') || lowerText.includes('peaceful') || lowerText.includes('relaxed')) {
        return { mood: 'calm', energy: 40 };
    } else if (lowerText.includes('think') || lowerText.includes('consider') || lowerText.includes('perhaps')) {
        return { mood: 'thinking', energy: 60 };
    }
    
    return { mood: 'neutral', energy: 50 };
}

function generateCharacterFromMood(mood, energy) {
    const moodColors = {
        happy: { body: '#FFD700', hair: '#FF6B6B', accent: '#4ECDC4' },
        sad: { body: '#6C7A89', hair: '#34495E', accent: '#95A5A6' },
        angry: { body: '#E74C3C', hair: '#C0392B', accent: '#8E44AD' },
        calm: { body: '#3498DB', hair: '#2ECC71', accent: '#1ABC9C' },
        thinking: { body: '#9B59B6', hair: '#8E44AD', accent: '#E67E22' },
        neutral: { body: '#667eea', hair: '#8B4513', accent: '#764ba2' }
    };
    
    const colors = moodColors[mood] || moodColors.neutral;
    const size = 0.8 + (energy / 100) * 0.4; // Scale from 0.8 to 1.2 based on energy
    
    return { colors, size, mood };
}

function applyCharacterStyle(style) {
    const ariaHead = document.querySelector('.aria-head');
    const ariaBody = document.querySelector('.aria-body');
    const ariaHair = document.querySelector('.aria-hair');
    const ariaLegs = document.querySelectorAll('.aria-leg');
    const ariaFeet = document.querySelectorAll('.aria-foot');
    
    // Create dramatic transformation sparkle effect
    for (let i = 0; i < 15; i++) {
        setTimeout(() => {
            createEffect('sparkle');
        }, i * 50);
    }
    
    // Add glow pulse during transformation
    aria.style.filter = 'drop-shadow(0 0 30px ' + style.colors.body + ') brightness(1.5)';
    setTimeout(() => {
        aria.style.filter = 'none';
    }, 1000);
    
    // Apply colors with smooth transition
    ariaHair.style.transition = 'background-color 1s ease, transform 1s ease';
    ariaHead.style.transition = 'background-color 1s ease';
    ariaBody.style.transition = 'background 1s ease, transform 1s ease';
    ariaLegs.forEach(leg => leg.style.transition = 'background-color 1s ease');
    ariaFeet.forEach(foot => foot.style.transition = 'background-color 1s ease');
    
    ariaHair.style.backgroundColor = style.colors.hair;
    ariaBody.style.background = `linear-gradient(135deg, ${style.colors.body}, ${style.colors.accent})`;
    
    // Apply size transformation
    aria.style.transform = `translateX(-50%) scale(${style.size})`;
    
    // Update character state
    characterState = { ...characterState, ...style };
    
    console.log('🎨 Character updated:', style.mood, 'Energy:', Math.round(style.size * 100) + '%');
    showFeedback('🎨 TRANSFORM: ' + style.mood.toUpperCase());
}

function autoGenerateCharacter(responseText) {
    const analysis = analyzeAIResponse(responseText);
    const newStyle = generateCharacterFromMood(analysis.mood, analysis.energy);
    applyCharacterStyle(newStyle);
    
    // Trigger automatic animation based on mood
    setTimeout(() => {
        if (analysis.mood === 'happy') {
            animate('jumping');
        } else if (analysis.mood === 'sad') {
            move('left', 'normal');
        } else if (analysis.mood === 'angry') {
            animate('spinning');
        } else if (analysis.mood === 'calm') {
            animate('waving');
        } else if (analysis.mood === 'thinking') {
            changeExpression('thinking');
        }
    }, 500);
}

const expressions = {
    'smile': '😊',
    'happy': '😃',
    'sad': '😢',
    'surprised': '😲',
    'confused': '😕',
    'thinking': '🤔',
    'wink': '😉'
};

function log(message, isError = false) {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.style.borderLeftColor = isError ? '#e74c3c' : '#667eea';
    entry.style.color = isError ? '#e74c3c' : '#555';
    entry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
    logContainer.insertBefore(entry, logContainer.firstChild);
    
    // Keep only last 10 entries
    while (logContainer.children.length > 10) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

async function sendCommand() {
    const command = commandInput.value.trim();
    if (!command) return;
    
    log(`Command: "${command}"`);
    commandInput.value = '';
    
    try {
        // Call backend API
        const response = await fetch('/api/aria/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // AI automatically generates character based on response
        if (data.response) {
            autoGenerateCharacter(data.response);
        }
        
        if (data.tags && data.tags.length > 0) {
            log(`✅ ${data.model}: ${data.tags.join(' ')}`);
            executeTags(data.tags);
        } else if (data.error) {
            log(`⚠️ API Error: ${data.error}`, true);
            executeLocalCommand(command);
        } else {
            log('⚠️ Using fallback parser');
            executeLocalCommand(command);
        }
    } catch (error) {
        log(`⚠️ Network error, using fallback`, true);
        // Fallback: parse command locally without AI
        executeLocalCommand(command);
    }
}

function executeLocalCommand(command) {
    // Simple local fallback without AI model
    const cmd = command.toLowerCase();
    let executed = false;
    
    // Check if this is a limb command to avoid movement conflicts
    const isLimbCommand = ['left arm', 'arm left', 'left hand', 'right arm', 'arm right', 'right hand',
                          'left leg', 'leg left', 'right leg', 'leg right'].some(k => cmd.includes(k));
    
    // Expressions
    if (cmd.includes('smile') || cmd.includes('happy')) {
        changeExpression('smile');
        executed = true;
    }
    if (cmd.includes('sad')) {
        changeExpression('sad');
        executed = true;
    }
    if (cmd.includes('surprised')) {
        changeExpression('surprised');
        executed = true;
    }
    if (cmd.includes('confused')) {
        changeExpression('confused');
        executed = true;
    }
    if (cmd.includes('thinking') || cmd.includes('think')) {
        changeExpression('thinking');
        executed = true;
    }
    if (cmd.includes('wink')) {
        changeExpression('wink');
        executed = true;
    }
    
    // Animations
    if (cmd.includes('jump')) {
        animate('jumping');
        executed = true;
    }
    if (cmd.includes('dance')) {
        animate('dancing');
        executed = true;
    }
    if (cmd.includes('spin')) {
        animate('spinning');
        executed = true;
    }
    if (cmd.includes('wave')) {
        animate('waving');
        executed = true;
    }
    
    // Effects
    if (cmd.includes('sparkle')) {
        createEffect('sparkle');
        executed = true;
    }
    if (cmd.includes('hearts')) {
        createEffect('hearts');
        executed = true;
    }
    if (cmd.includes('glow')) {
        createEffect('glow');
        executed = true;
    }
    
    // Movement - only if not a limb command
    if (!isLimbCommand) {
        // Determine movement style
        let movementSpeed = 'normal';
        if (cmd.includes('skip')) {
            movementSpeed = 'skip';
        } else if (cmd.includes('strut') || cmd.includes('swagger')) {
            movementSpeed = 'strut';
        } else if (cmd.includes('run')) {
            movementSpeed = 'run';
        }
        
        if (cmd.includes('left')) {
            move('left', movementSpeed);
            executed = true;
        }
        if (cmd.includes('right')) {
            move('right', movementSpeed);
            executed = true;
        }
        if (cmd.includes('up') || (cmd.includes('forward') && !cmd.includes('arm') && !cmd.includes('leg'))) {
            move('up', movementSpeed);
            executed = true;
        }
        if (cmd.includes('down') || (cmd.includes('back') && !cmd.includes('arm') && !cmd.includes('leg'))) {
            move('down', movementSpeed);
            executed = true;
        }
    }
    
    if (!executed) {
        log('❌ Command not recognized', true);
    }
}

function executeTags(tags) {
    console.log('📋 Executing tags:', tags);
    tags.forEach((tag, index) => {
        // Parse tag format: [aria:category:action:param]
        const match = tag.match(/\[aria:([^:]+):([^:\]]+)(?::([^\]]+))?\]/);
        if (!match) {
            console.log('⚠️ Failed to parse tag:', tag);
            return;
        }
        
        const [, categoryRaw, actionRaw, paramRaw] = match;
        // Normalize category/action
        const category = (categoryRaw || '').toLowerCase();
        const action = (actionRaw || '').toLowerCase();
        const param = typeof paramRaw === 'string' ? paramRaw.trim() : undefined;
        console.log(`✅ Parsed tag - Category: ${category}, Action: ${action}, Param: ${param}`);
        
        setTimeout(() => {
            switch (category) {
                case 'expression':
                    console.log('Executing expression:', action);
                    changeExpression(action);
                    break;
                case 'animate':
                    console.log('Executing animate:', action);
                    animate(getAnimationClass(action));
                    break;
                case 'gesture':
                    animate('waving');
                    break;
                case 'move':
                    move(action, param || 'normal');
                    break;
                case 'walk':
                    move(action, param || 'normal');
                    break;
                case 'run':
                    move(action, param || 'fast');
                    break;
                case 'skip':
                    move(action, 'skip');
                    break;
                case 'strut':
                case 'swagger':
                    move(action, 'strut');
                    break;
                case 'limb':
                    // Move individual limbs with tags like:
                    // [aria:limb:left_arm:raise] | [aria:limb:right_arm:-45] | [aria:limb:left_leg:kick]
                    handleLimbTag(action, param);
                    break;
                case 'interact':
                    console.log('Executing interact:', action, param);
                    interactWithObject(action, param);
                    break;
                case 'effect':
                    createEffect(action);
                    break;
                case 'camera':
                    if (action === 'center') centerAria();
                    break;
                case 'pose':
                    applyPose(action, param);
                    break;
            }
        }, index * 500); // Stagger multiple commands
    });
}

function changeExpression(emotion) {
    ariaMouth.className = 'aria-mouth';
    
    // Reset any previous expression modifications
    ariaMouth.style.borderRadius = '';
    ariaMouth.style.width = '';
    ariaMouth.style.height = '';
    ariaMouth.style.borderTop = '';
    
    switch(emotion) {
        case 'smile':
        case 'happy':
            ariaMouth.classList.add('smile');
            break;
        case 'sad':
            ariaMouth.classList.add('sad');
            break;
        case 'surprised':
            ariaMouth.style.borderRadius = '50%';
            ariaMouth.style.width = '15px';
            ariaMouth.style.height = '15px';
            ariaMouth.style.borderTop = '2px solid #333';
            break;
        case 'confused':
            // Wavy/uncertain mouth
            ariaMouth.style.width = '18px';
            ariaMouth.style.height = '6px';
            ariaMouth.style.borderRadius = '0 0 50% 50%';
            ariaMouth.style.transform = 'translateX(-50%) rotate(5deg)';
            break;
        case 'thinking':
            // Side mouth (pondering)
            ariaMouth.style.width = '12px';
            ariaMouth.style.height = '8px';
            ariaMouth.style.borderRadius = '0 0 50% 50%';
            ariaMouth.style.transform = 'translateX(-30%)';
            // Also raise one eyebrow (using eye height)
            if (ariaEyeLeft) {
                ariaEyeLeft.style.transform = 'translateY(-2px)';
                setTimeout(() => {
                    ariaEyeLeft.style.transform = '';
                }, 2000);
            }
            break;
        case 'wink':
            document.querySelectorAll('.aria-eye')[1].style.height = '4px';
            setTimeout(() => {
                document.querySelectorAll('.aria-eye')[1].style.height = '12px';
            }, 500);
            break;
        default:
            ariaMouth.classList.add('smile');
    }
    
    aria.style.transform = 'translateX(-50%) scale(1.1)';
    setTimeout(() => {
        aria.style.transform = 'translateX(-50%) scale(1)';
    }, 300);
}

// Idle animation state
let idleAnimationInterval = null;
let isPerformingAction = false;

// Start idle breathing animation
function startIdleAnimation() {
    if (idleAnimationInterval) return;
    
    idleAnimationInterval = setInterval(() => {
        if (!isPerformingAction) {
            // Subtle breathing effect
            ariaBody.style.transition = 'transform 2s ease-in-out';
            ariaBody.style.transform = 'scaleY(1.03)';
            
            // Occasional blink
            if (Math.random() > 0.7) {
                ariaEyeLeft.style.height = '2px';
                ariaEyeRight.style.height = '2px';
                setTimeout(() => {
                    ariaEyeLeft.style.height = '12px';
                    ariaEyeRight.style.height = '12px';
                }, 150);
            }
            
            // Slight head bob
            if (Math.random() > 0.8) {
                ariaHead.style.transition = 'transform 0.8s ease-in-out';
                ariaHead.style.transform = 'translateY(-3px)';
                setTimeout(() => {
                    ariaHead.style.transform = 'translateY(0)';
                }, 800);
            }
            
            setTimeout(() => {
                ariaBody.style.transform = 'scaleY(1)';
            }, 2000);
        }
    }, 4000);
}

// Stop idle animation
function stopIdleAnimation() {
    if (idleAnimationInterval) {
        clearInterval(idleAnimationInterval);
        idleAnimationInterval = null;
    }
}

// Limb movement helpers
function moveArm(arm, angle, duration = 500) {
    arm.style.transition = `transform ${duration}ms ease-in-out`;
    arm.style.transform = `rotate(${angle}deg)`;
}

function moveLeg(leg, angle, duration = 500) {
    leg.style.transition = `transform ${duration}ms ease-in-out`;
    leg.style.transform = `rotate(${angle}deg)`;
}

function resetLimbs(duration = 500) {
    moveArm(ariaArmLeft, 0, duration);
    moveArm(ariaArmRight, 0, duration);
    moveLeg(ariaLegLeft, 0, duration);
    moveLeg(ariaLegRight, 0, duration);
}

// Utility helpers for limb control
function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }

function parseAngleAndDuration(param) {
    // Accept patterns: "45", "45,600", "raise", "raise,800"
    if (!param) return { value: null, duration: 500 };
    const parts = String(param).split(',').map(s => s.trim());
    const first = parts[0];
    const dur = parts[1] ? parseInt(parts[1], 10) : 500;
    const asNum = Number(first);
    if (!Number.isNaN(asNum)) {
        return { value: asNum, duration: isFinite(dur) ? dur : 500 };
    }
    return { value: first.toLowerCase(), duration: isFinite(dur) ? dur : 500 };
}

function normalizeLimbPart(part) {
    const p = (part || '').toLowerCase().replace(/[-\s]/g, '_');
    const map = {
        'leftarm': 'left_arm', 'arm_left': 'left_arm', 'l_arm': 'left_arm', 'left_hand':'left_arm', 'hand_left':'left_arm',
        'rightarm': 'right_arm', 'arm_right': 'right_arm', 'r_arm': 'right_arm', 'right_hand':'right_arm', 'hand_right':'right_arm',
        'leftleg': 'left_leg', 'leg_left': 'left_leg', 'l_leg':'left_leg',
        'rightleg': 'right_leg', 'leg_right': 'right_leg', 'r_leg':'right_leg'
    };
    return map[p] || p;
}

function elementForPart(part) {
    switch (part) {
        case 'left_arm': return ariaArmLeft;
        case 'right_arm': return ariaArmRight;
        case 'left_leg': return ariaLegLeft;
        case 'right_leg': return ariaLegRight;
        default: return null;
    }
}

function waveArmElement(armEl, duration = 700) {
    if (!armEl) return;
    const step = Math.max(120, duration);
    moveArm(armEl, -60, step * 0.3);
    setTimeout(() => moveArm(armEl, -30, step * 0.25), step * 0.3);
    setTimeout(() => moveArm(armEl, -60, step * 0.25), step * 0.55);
    setTimeout(() => moveArm(armEl, -30, step * 0.2), step * 0.8);
    setTimeout(() => moveArm(armEl, 0, step * 0.2), step * 1.0);
}

function kickLegElement(legEl, duration = 500) {
    if (!legEl) return;
    moveLeg(legEl, 45, duration * 0.5);
    setTimeout(() => moveLeg(legEl, 0, duration * 0.5), duration * 0.5);
}

function handleLimbTag(partRaw, paramRaw) {
    const part = normalizeLimbPart(partRaw);
    const targetEl = elementForPart(part);
    if (!targetEl) {
        log(`❓ Unknown limb: ${partRaw}`);
        return;
    }
    const { value, duration } = parseAngleAndDuration(paramRaw);
    const isArm = part.includes('arm');
    const isLeg = part.includes('leg');
    // Pause idle while moving a limb
    isPerformingAction = true;

    if (typeof value === 'number') {
        const angle = isArm ? clamp(value, -130, 130) : clamp(value, -60, 60);
        if (isArm) moveArm(targetEl, angle, duration); else moveLeg(targetEl, angle, duration);
        setTimeout(() => { isPerformingAction = false; }, Math.max(300, duration));
        return;
    }

    const action = (value || '').toLowerCase();
    switch (action) {
        case 'raise':
        case 'up':
            if (isArm) moveArm(targetEl, -90, duration); else moveLeg(targetEl, -30, duration);
            break;
        case 'lower':
        case 'down':
            if (isArm) moveArm(targetEl, 0, duration); else moveLeg(targetEl, 0, duration);
            break;
        case 'forward':
            if (isArm) moveArm(targetEl, -45, duration); else moveLeg(targetEl, 30, duration);
            break;
        case 'back':
        case 'backward':
            if (isArm) moveArm(targetEl, 45, duration); else moveLeg(targetEl, -30, duration);
            break;
        case 'wave':
            if (isArm) waveArmElement(targetEl, duration);
            break;
        case 'kick':
            if (isLeg) kickLegElement(targetEl, duration);
            break;
        case 'rest':
        case 'neutral':
            if (isArm) moveArm(targetEl, 0, duration); else moveLeg(targetEl, 0, duration);
            break;
        default:
            // Try numeric fallback if action is numeric-like
            const num = Number(action);
            if (!Number.isNaN(num)) {
                const angle = isArm ? clamp(num, -130, 130) : clamp(num, -60, 60);
                if (isArm) moveArm(targetEl, angle, duration); else moveLeg(targetEl, angle, duration);
            } else {
                log(`❓ Unknown limb action: ${action}`);
            }
    }
    setTimeout(() => { isPerformingAction = false; }, Math.max(300, duration));
}

function walkCycle() {
    // Alternating leg movement
    moveLeg(ariaLegLeft, 25, 300);
    moveLeg(ariaLegRight, -25, 300);
    moveArm(ariaArmLeft, -15, 300);
    moveArm(ariaArmRight, 15, 300);
    
    setTimeout(() => {
        moveLeg(ariaLegLeft, -25, 300);
        moveLeg(ariaLegRight, 25, 300);
        moveArm(ariaArmLeft, 15, 300);
        moveArm(ariaArmRight, -15, 300);
    }, 300);
    
    setTimeout(() => resetLimbs(200), 600);
}

function strutWalk() {
    // Confident strut with head bob
    ariaHead.style.transition = 'transform 0.3s';
    
    moveLeg(ariaLegLeft, 35, 250);
    moveLeg(ariaLegRight, -35, 250);
    moveArm(ariaArmLeft, -25, 250);
    moveArm(ariaArmRight, 25, 250);
    ariaHead.style.transform = 'translateY(-5px) rotate(3deg)';
    
    setTimeout(() => {
        moveLeg(ariaLegLeft, -35, 250);
        moveLeg(ariaLegRight, 35, 250);
        moveArm(ariaArmLeft, 25, 250);
        moveArm(ariaArmRight, -25, 250);
        ariaHead.style.transform = 'translateY(-5px) rotate(-3deg)';
    }, 300);
    
    setTimeout(() => {
        moveLeg(ariaLegLeft, 20, 250);
        moveLeg(ariaLegRight, -20, 250);
        ariaHead.style.transform = 'translateY(0) rotate(0)';
    }, 600);
    
    setTimeout(() => resetLimbs(200), 850);
}

function skipMove() {
    // Playful skipping motion
    moveLeg(ariaLegLeft, -45, 200);
    moveLeg(ariaLegRight, 30, 200);
    moveArm(ariaArmLeft, -30, 200);
    moveArm(ariaArmRight, -30, 200);
    aria.style.transform = 'translateX(-50%) scale(1.1) translateY(-20px)';
    
    setTimeout(() => {
        moveLeg(ariaLegLeft, 30, 200);
        moveLeg(ariaLegRight, -45, 200);
        aria.style.transform = 'translateX(-50%) scale(1)';
    }, 250);
    
    setTimeout(() => {
        moveLeg(ariaLegLeft, -30, 200);
        moveLeg(ariaLegRight, 20, 200);
        aria.style.transform = 'translateX(-50%) scale(1.1) translateY(-20px)';
    }, 500);
    
    setTimeout(() => {
        resetLimbs(200);
        aria.style.transform = 'translateX(-50%) scale(1)';
    }, 750);
}

function danceLimbs() {
    // Arms up and down
    moveArm(ariaArmLeft, -45, 200);
    moveArm(ariaArmRight, -45, 200);
    moveLeg(ariaLegLeft, 15, 200);
    moveLeg(ariaLegRight, -15, 200);
    
    setTimeout(() => {
        moveArm(ariaArmLeft, -90, 200);
        moveArm(ariaArmRight, -90, 200);
        moveLeg(ariaLegLeft, -15, 200);
        moveLeg(ariaLegRight, 15, 200);
    }, 200);
    
    setTimeout(() => {
        moveArm(ariaArmLeft, -45, 200);
        moveArm(ariaArmRight, -45, 200);
        moveLeg(ariaLegLeft, 15, 200);
        moveLeg(ariaLegRight, -15, 200);
    }, 400);
    
    setTimeout(() => resetLimbs(200), 600);
}

function expressiveDance() {
    // More exaggerated dance moves
    moveArm(ariaArmLeft, -120, 150);
    moveArm(ariaArmRight, 60, 150);
    moveLeg(ariaLegLeft, 20, 150);
    moveLeg(ariaLegRight, -20, 150);
    ariaHead.style.transform = 'rotate(15deg)';
    
    setTimeout(() => {
        moveArm(ariaArmLeft, 60, 150);
        moveArm(ariaArmRight, -120, 150);
        moveLeg(ariaLegLeft, -20, 150);
        moveLeg(ariaLegRight, 20, 150);
        ariaHead.style.transform = 'rotate(-15deg)';
    }, 200);
    
    setTimeout(() => {
        moveArm(ariaArmLeft, -90, 150);
        moveArm(ariaArmRight, -90, 150);
        moveLeg(ariaLegLeft, 30, 150);
        moveLeg(ariaLegRight, -30, 150);
        ariaHead.style.transform = 'rotate(0)';
    }, 400);
    
    setTimeout(() => resetLimbs(200), 600);
}

let continuousDanceInterval = null;

function startContinuousDance() {
    if (continuousDanceInterval) return;
    
    isPerformingAction = true;
    showFeedback('🎉 PARTY MODE!');
    
    continuousDanceInterval = setInterval(() => {
        const danceType = Math.random();
        if (danceType > 0.5) {
            expressiveDance();
        } else {
            danceLimbs();
        }
    }, 700);
}

function stopContinuousDance() {
    if (continuousDanceInterval) {
        clearInterval(continuousDanceInterval);
        continuousDanceInterval = null;
        isPerformingAction = false;
        resetLimbs(300);
    }
}

function spinLimbs() {
    // Arms out during spin
    moveArm(ariaArmLeft, -90, 100);
    moveArm(ariaArmRight, -90, 100);
    setTimeout(() => resetLimbs(300), 900);
}

function animate(className) {
    console.log('🎬 Animating:', className);
    showFeedback('🎬 ' + className.toUpperCase() + '!');
    aria.classList.remove('jumping', 'dancing', 'spinning', 'waving');
    void aria.offsetWidth; // Force reflow
    
    // Mark as performing action
    isPerformingAction = true;
    
    // Get current scale from characterState
    const currentScale = characterState.size || 1.0;
    
    if (className === 'waving') {
        showFeedback('👋 WAVING!');
        console.log('Wave animation with arm movement');
        // Rapid wave motion
        moveArm(ariaArmRight, -60, 200);
        setTimeout(() => moveArm(ariaArmRight, -30, 150), 200);
        setTimeout(() => moveArm(ariaArmRight, -60, 150), 350);
        setTimeout(() => moveArm(ariaArmRight, -30, 150), 500);
        setTimeout(() => moveArm(ariaArmRight, -60, 150), 650);
        setTimeout(() => resetLimbs(200), 800);
    } else if (className === 'jumping') {
        console.log('Jumping animation triggered with leg bending');
        aria.classList.add(className);
        aria.style.filter = 'brightness(1.5)';
        
        // Pre-jump crouch
        moveLeg(ariaLegLeft, 45, 200);
        moveLeg(ariaLegRight, -45, 200);
        moveArm(ariaArmLeft, -20, 200);
        moveArm(ariaArmRight, -20, 200);
        
        // During jump - legs extend
        setTimeout(() => {
            moveLeg(ariaLegLeft, -35, 300);
            moveLeg(ariaLegRight, 35, 300);
            moveArm(ariaArmLeft, -60, 300);
            moveArm(ariaArmRight, -60, 300);
        }, 300);
        
        // Landing crouch
        setTimeout(() => {
            moveLeg(ariaLegLeft, 35, 300);
            moveLeg(ariaLegRight, -35, 300);
            moveArm(ariaArmLeft, -10, 300);
            moveArm(ariaArmRight, -10, 300);
            aria.style.filter = 'brightness(1)';
        }, 1500);
        
        // Return to normal
        setTimeout(() => {
            resetLimbs(400);
            aria.classList.remove(className);
            aria.style.transform = `translateX(-50%) scale(${currentScale})`;
        }, 2500);
    } else {
        console.log('Generic animation triggered:', className);
        aria.classList.add(className);
        
        // Add limb movements based on animation type
        if (className === 'dancing') {
            console.log('Adding dance limb movements');
            // Repeat dance limbs during 2s animation
            danceLimbs();
            setTimeout(() => danceLimbs(), 700);
            setTimeout(() => danceLimbs(), 1400);
        } else if (className === 'spinning') {
            console.log('Adding spin limb movements');
            spinLimbs();
        }
        
        setTimeout(() => {
            aria.classList.remove(className);
            resetLimbs(300);
            aria.style.transform = `translateX(-50%) scale(${currentScale})`;
            isPerformingAction = false;
        }, className === 'dancing' ? 2000 : 1000);
    }
}

function getAnimationClass(action) {
    const animations = {
        'jump': 'jumping',
        'dance': 'dancing',
        'spin': 'spinning',
        'wave': 'waving',
        'bow': 'waving',
        'flip': 'spinning',
        'backflip': 'spinning'
    };
    return animations[action] || 'jumping';
}

function move(direction, speed = 'normal') {
    console.log('🚶 Moving:', direction, 'at speed:', speed);
    
    isPerformingAction = true;
    
    const currentLeft = aria.style.left || '50%';
    const current = parseFloat(currentLeft);
    
    let newPos = current;
    let distance = 25;
    let movementStyle = walkCycle;
    let duration = '1s';
    
    // Choose movement style based on speed
    switch(speed) {
        case 'run':
        case 'fast':
            distance = 40;
            movementStyle = skipMove;
            duration = '0.7s';
            showFeedback('🏃 RUNNING!');
            break;
        case 'strut':
        case 'swagger':
            distance = 30;
            movementStyle = strutWalk;
            duration = '1.2s';
            showFeedback('😎 STRUTTING!');
            break;
        case 'skip':
            distance = 35;
            movementStyle = skipMove;
            duration = '0.9s';
            showFeedback('🎵 SKIPPING!');
            break;
        default:
            showFeedback('🚶 WALKING!');
    }
    
    // Animate movement style
    movementStyle();
    
    switch (direction) {
        case 'left':
            newPos = Math.max(5, current - distance);
            break;
        case 'right':
            newPos = Math.min(95, current + distance);
            break;
        case 'forward':
        case 'up':
            const currentTop = aria.style.top || '50%';
            const top = parseFloat(currentTop);
            aria.style.top = Math.max(10, top - distance) + '%';
            aria.style.transition = `top ${duration} ease`;
            setTimeout(() => { isPerformingAction = false; }, 1000);
            return;
        case 'back':
        case 'down':
            const currentTopBack = aria.style.top || '50%';
            const topBack = parseFloat(currentTopBack);
            aria.style.top = Math.min(80, topBack + distance) + '%';
            aria.style.transition = `top ${duration} ease`;
            setTimeout(() => { isPerformingAction = false; }, 1000);
            return;
    }
    
    aria.style.transition = `left ${duration} ease`;
    aria.style.left = newPos + '%';
    
    setTimeout(() => { isPerformingAction = false; }, 1000);
}

function createEffect(type) {
    const effects = {
        'sparkle': '✨',
        'glow': '💫',
        'hearts': '💕'
    };
    
    const emoji = effects[type] || '✨';
    
    for (let i = 0; i < 5; i++) {
        setTimeout(() => {
            const effect = document.createElement('div');
            effect.className = `effect ${type}`;
            effect.textContent = emoji;
            effect.style.left = (Math.random() * 80 + 10) + '%';
            effect.style.top = (Math.random() * 80 + 10) + '%';
            stage.appendChild(effect);
            
            setTimeout(() => effect.remove(), 1500);
        }, i * 100);
    }
}

function centerAria() {
    aria.style.left = '50%';
    aria.style.transform = 'translateX(-50%) scale(1)';
}

function applyPose(poseRaw, param) {
    const pose = (poseRaw || '').toLowerCase();
    // Body position presets
    const poses = {
        'sit': { bottom: '20px', transform: 'translateX(-50%) scale(0.8)' },
        'stand': { bottom: '50px', transform: 'translateX(-50%) scale(1)' },
        'crouch': { bottom: '30px', transform: 'translateX(-50%) scale(0.9)' },
        'lie': { bottom: '10px', transform: 'translateX(-50%) scale(0.7) rotate(90deg)' }
    };
    const poseStyle = poses[pose];
    if (poseStyle) {
        aria.style.bottom = poseStyle.bottom;
        aria.style.transform = poseStyle.transform;
    }
    // Limb presets
    switch (pose) {
        case 't-pose':
        case 'tpose':
            moveArm(ariaArmLeft, -90, 400);
            moveArm(ariaArmRight, -90, 400);
            resetLimbs(1000);
            break;
        case 'hands_up':
        case 'hands-up':
        case 'handsup':
            moveArm(ariaArmLeft, -120, 400);
            moveArm(ariaArmRight, -120, 400);
            break;
        case 'cross_arms':
        case 'cross-arms':
        case 'crossarms':
            moveArm(ariaArmLeft, -30, 400);
            moveArm(ariaArmRight, 30, 400);
            break;
        case 'hero':
            // Hands on hips (approximate)
            moveArm(ariaArmLeft, 45, 400);
            moveArm(ariaArmRight, -45, 400);
            break;
    }
}

function quickCommand(cmd) {
    commandInput.value = cmd;
    sendCommand();
}

// Random character evolution (simulates AI personality drift)
function randomCharacterEvolution() {
    const moods = ['happy', 'sad', 'calm', 'thinking', 'neutral'];
    const randomMood = moods[Math.floor(Math.random() * moods.length)];
    const randomEnergy = 30 + Math.floor(Math.random() * 70);
    
    log('✨ Character evolving to: ' + randomMood + ' (' + randomEnergy + '% energy)');
    
    const newStyle = generateCharacterFromMood(randomMood, randomEnergy);
    applyCharacterStyle(newStyle);
}

// Automatic character evolution every 30 seconds
let evolutionCountdown = 30;
const timerDisplay = document.getElementById('evolutionTimer');

setInterval(randomCharacterEvolution, 30000);

// Countdown timer
setInterval(() => {
    evolutionCountdown--;
    if (evolutionCountdown <= 0) {
        evolutionCountdown = 30;
    }
    
    // Update timer display
    if (timerDisplay) {
        timerDisplay.textContent = `⏰ Next evolution in: ${evolutionCountdown}s`;
        if (evolutionCountdown <= 5) {
            timerDisplay.style.color = '#e74c3c';
            timerDisplay.style.animation = 'pulse 0.5s ease infinite';
        } else {
            timerDisplay.style.color = '#667eea';
            timerDisplay.style.animation = 'none';
        }
    }
    
    if (evolutionCountdown <= 5 && evolutionCountdown > 0) {
        log(`⏰ Character evolving in ${evolutionCountdown} seconds...`);
    }
}, 1000);

// Initialize
log('🎨 Aria Visual System Ready!');
log('🤖 AI Character Generation: ACTIVE');
log('Type commands or use quick buttons');
log('⏰ Auto-evolution every 30 seconds');

// Object Interaction System
function pickUpObject(objectId) {
    const obj = document.getElementById(objectId);
    if (!obj) {
        console.log('❌ Object not found:', objectId);
        return false;
    }
    
    if (characterState.heldObject) {
        showFeedback('⚠️ Already holding ' + characterState.heldObject.toUpperCase() + '!');
        return false;
    }
    
    console.log('🤏 Picking up:', objectId);
    showFeedback('🤏 PICKED UP ' + objectId.toUpperCase() + '!');
    
    // Store held object
    characterState.heldObject = objectId;
    characterState.heldObjectElement = obj;
    
    // Visual feedback
    obj.classList.add('held');
    
    // Position object above character
    positionHeldObject();
    
    // Arm reaching animation
    moveArm(ariaArmRight, -90, 300);
    setTimeout(() => moveArm(ariaArmRight, -45, 200), 300);
    
    return true;
}

function dropObject() {
    if (!characterState.heldObject) {
        showFeedback('⚠️ Not holding anything!');
        return false;
    }
    
    console.log('📦 Dropping:', characterState.heldObject);
    showFeedback('📦 DROPPED ' + characterState.heldObject.toUpperCase() + '!');
    
    const obj = characterState.heldObjectElement;
    
    // Remove held state
    obj.classList.remove('held');
    
    // Drop at current Aria position
    const ariaRect = aria.getBoundingClientRect();
    const stageRect = stage.getBoundingClientRect();
    
    const dropLeft = ((ariaRect.left - stageRect.left) / stageRect.width) * 100;
    const dropBottom = ((stageRect.bottom - ariaRect.bottom) / stageRect.height) * 100;
    
    obj.style.left = dropLeft + '%';
    obj.style.bottom = (dropBottom + 10) + '%';
    
    // Arm dropping animation
    moveArm(ariaArmRight, -90, 200);
    setTimeout(() => resetLimbs(300), 200);
    
    // Clear held object
    characterState.heldObject = null;
    characterState.heldObjectElement = null;
    
    return true;
}

function throwObject(direction) {
    if (!characterState.heldObject) {
        showFeedback('⚠️ Not holding anything to throw!');
        return false;
    }
    
    console.log('🎯 Throwing:', characterState.heldObject, 'to', direction);
    showFeedback('🎯 THROWING ' + characterState.heldObject.toUpperCase() + '!');
    
    const obj = characterState.heldObjectElement;
    obj.classList.remove('held');
    
    // Throwing arm animation
    moveArm(ariaArmRight, -120, 150);
    setTimeout(() => {
        moveArm(ariaArmRight, -30, 200);
        setTimeout(() => resetLimbs(300), 100);
    }, 150);
    
    // Calculate throw trajectory
    const currentLeft = parseFloat(obj.style.left);
    const currentBottom = parseFloat(obj.style.bottom);
    
    let targetLeft = currentLeft;
    let targetBottom = currentBottom;
    
    switch(direction) {
        case 'left':
            targetLeft = Math.max(5, currentLeft - 40);
            break;
        case 'right':
            targetLeft = Math.min(95, currentLeft + 40);
            break;
        case 'up':
            targetBottom = Math.min(90, currentBottom + 30);
            break;
    }
    
    // Animate throw with arc
    obj.style.transition = 'all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
    obj.style.left = targetLeft + '%';
    obj.style.bottom = targetBottom + '%';
    obj.style.transform = 'rotate(360deg) scale(0.9)';
    
    // Reset after landing
    setTimeout(() => {
        obj.style.transition = 'all 0.3s ease';
        obj.style.transform = 'rotate(0deg) scale(1)';
    }, 800);
    
    // Clear held object
    characterState.heldObject = null;
    characterState.heldObjectElement = null;
    
    return true;
}

function positionHeldObject() {
    if (!characterState.heldObjectElement) return;
    
    // Position object above and slightly in front of character
    const ariaRect = aria.getBoundingClientRect();
    const stageRect = stage.getBoundingClientRect();
    
    const objLeft = ((ariaRect.left - stageRect.left + ariaRect.width * 0.6) / stageRect.width) * 100;
    const objBottom = ((stageRect.bottom - ariaRect.top + 20) / stageRect.height) * 100;
    
    characterState.heldObjectElement.style.left = objLeft + '%';
    characterState.heldObjectElement.style.bottom = objBottom + '%';
}

function interactWithObject(action, objectId) {
    console.log('🔧 Interacting:', action, 'with', objectId);
    
    switch(action) {
        case 'pickup':
        case 'grab':
        case 'take':
        case 'get':
            return pickUpObject(objectId);
        case 'drop':
        case 'place':
        case 'put':
            return dropObject();
        case 'throw':
        case 'toss':
            return throwObject('right');
        default:
            showFeedback('❓ Unknown action: ' + action);
            return false;
    }
}

// Make objects draggable and clickable
function initializeObjectInteractions() {
    const objects = document.querySelectorAll('.object');
    
    objects.forEach(obj => {
        obj.addEventListener('click', (e) => {
            e.stopPropagation();
            const objectId = obj.id;
            
            if (!characterState.heldObject) {
                pickUpObject(objectId);
            } else if (characterState.heldObject === objectId) {
                dropObject();
            }
        });
        
        // Drag functionality
        let isDragging = false;
        let startX, startY, startLeft, startBottom;
        
        obj.addEventListener('mousedown', (e) => {
            if (characterState.heldObject === obj.id) return;
            
            isDragging = true;
            obj.classList.add('grabbed');
            
            const rect = obj.getBoundingClientRect();
            const stageRect = stage.getBoundingClientRect();
            
            startX = e.clientX;
            startY = e.clientY;
            startLeft = ((rect.left - stageRect.left) / stageRect.width) * 100;
            startBottom = ((stageRect.bottom - rect.bottom) / stageRect.height) * 100;
            
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const stageRect = stage.getBoundingClientRect();
            const deltaX = ((e.clientX - startX) / stageRect.width) * 100;
            const deltaY = -((e.clientY - startY) / stageRect.height) * 100;
            
            obj.style.left = Math.max(0, Math.min(100, startLeft + deltaX)) + '%';
            obj.style.bottom = Math.max(0, Math.min(100, startBottom + deltaY)) + '%';
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                obj.classList.remove('grabbed');
            }
        });
    });
}

// Initialize object interactions
initializeObjectInteractions();
log('🎮 Objects: apple, book, cup, ball, flower');
log('💡 Try: "pick up apple", "drop", "throw ball"');

// Initial random appearance after 2 seconds
setTimeout(() => {
    log('🎨 Generating initial character...');
    randomCharacterEvolution();
}, 2000);

// Start idle animations
startIdleAnimation();
log('👀 Idle animations enabled - watch for breathing and blinking!');

// Expose minimal testing helpers
window.ariaTest = {
    limb: (part, actionOrAngle, duration) => handleLimbTag(part, typeof actionOrAngle === 'number' ? `${actionOrAngle},${duration||500}` : `${actionOrAngle||''}${duration?','+duration:''}`),
    pose: (name) => applyPose(name)
};
window.simulateTags = (arr) => Array.isArray(arr) && executeTags(arr);

