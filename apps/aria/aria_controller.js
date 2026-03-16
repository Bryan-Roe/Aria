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

// Track active objects
const activeObjects = {
    apple: true,
    book: true,
    cup: true,
    ball: true,
    flower: true
};

// Toggle object visibility
function toggleObject(objectId) {
    const obj = document.getElementById(objectId);
    const btn = document.getElementById('btn-' + objectId);
    
    if (!obj) {
        log(`❌ toggleObject: unknown object ${objectId}`, true);
        return;
    }
    // compute last-known position first
    const lastPos = objectPositionFromElement(obj);

    if (activeObjects[objectId]) {
        // Remove object
        obj.style.display = 'none';
        btn.classList.remove('active');
        btn.classList.add('inactive');
        activeObjects[objectId] = false;
        log('🗑️ Removed ' + objectId);
        // Sync change to backend
        sendObjectUpdate('update', objectId, { position: lastPos, state: 'hidden' }).catch(() => {});
    } else {
        // Add object back
        obj.style.display = 'block';
        btn.classList.add('active');
        btn.classList.remove('inactive');
        activeObjects[objectId] = true;
        log('➕ Added ' + objectId);
        // Sync change to backend (object is back on stage)
        sendObjectUpdate('update', objectId, { position: lastPos, state: 'on_table' }).catch(() => {});
    }
}

// Additional DOM references (used by idle/poses/expressive moves)
const ariaHead = document.querySelector('.aria-head');
const ariaBody = document.querySelector('.aria-body');
const ariaEyes = document.querySelectorAll('.aria-eye');
const ariaEyeLeft = ariaEyes[0];
const ariaEyeRight = ariaEyes[1];

// AI-Controlled Character State (single combined object)
let characterState = {
    mood: 'neutral',
    energy: 50,
    personality: 'balanced',
    colors: {
        hair: '#4a3728',
        skin: '#f5d4b8',
        body: '#4a90e2',
        legs: '#3d5a80',
        feet: '#f5f5f5'
    },
    size: 1.0,
    style: 'default',
    heldObject: null,
    heldObjectElement: null,
    position: { x: 20, y: 70, z: 0 },
    rotation: 0,
    isMoving: false,
    currentWaypoint: null
};

// Visual feedback function
function showFeedback(message) {
    // Use toast if available (defined in index.html), fall back to stage overlay
    if (typeof showToast === 'function') {
        showToast(message);
        return;
    }
    const feedback = document.createElement('div');
    feedback.textContent = message;
    feedback.style.cssText = 'position:absolute; top:20px; left:50%; transform:translateX(-50%); background:var(--accent, #667eea); color:white; padding:12px 24px; border-radius:12px; font-size:0.9em; font-weight:600; z-index:999; box-shadow:0 4px 16px rgba(0,0,0,0.2); animation:pulse 0.5s ease;';
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
        happy: { body: '#5fb3f5', hair: '#6b4f3d', accent: '#7ac5ff' },
        sad: { body: '#6C7A89', hair: '#4a3728', accent: '#95A5A6' },
        angry: { body: '#E74C3C', hair: '#4a3728', accent: '#ff6b6b' },
        calm: { body: '#4a90e2', hair: '#4a3728', accent: '#5a9fe5' },
        thinking: { body: '#5a7fa8', hair: '#4a3728', accent: '#6b8fb3' },
        neutral: { body: '#4a90e2', hair: '#4a3728', accent: '#5a9fe5' }
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
    if (isError) entry.classList.add('log-error');
    entry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
    logContainer.insertBefore(entry, logContainer.firstChild);
    
    // Keep only last 10 entries
    while (logContainer.children.length > 10) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

// Chat UI helpers
function addChatMessage(role, text) {
    try {
        const container = document.getElementById('chatMessages');
        if (!container) return;

        const msgWrap = document.createElement('div');
        msgWrap.className = 'chat-msg ' + (role === 'user' ? 'user' : (role === 'aria' ? 'aria' : 'system'));

        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.innerText = text;

        const sender = document.createElement('div');
        sender.className = 'sender';
        sender.innerText = role === 'user' ? 'You' : role === 'aria' ? 'Aria' : 'System';

        const inner = document.createElement('div');
        inner.appendChild(sender);
        inner.appendChild(bubble);

        msgWrap.appendChild(inner);

        container.appendChild(msgWrap);
        container.scrollTop = container.scrollHeight;
    } catch (e) {
        console.warn('addChatMessage failed', e);
    }
}

// Called when Aria reaches a waypoint or finishes a movement
function arrivalFeedback(waypointKey) {
    try {
        let msg = '';
        if (waypointKey && waypoints3D && waypoints3D[waypointKey]) {
            msg = `I've arrived at ${waypoints3D[waypointKey].name}.`;
        } else if (typeof waypointKey === 'string' && waypointKey.includes('%')) {
            msg = `Arrived at ${waypointKey}.`;
        } else if (waypointKey) {
            msg = `Arrived at ${waypointKey}.`;
        } else {
            msg = `Arrived.`;
        }

        // Friendly reply from Aria in chat — pick varied arrival messages
        const arrivalMessages = [
            `I'm here! 🎉`,
            `Made it — ${waypointKey ? waypoints3D[waypointKey]?.name || waypointKey : 'arrived'}!`,
            `Arrived and ready!`,
            `That was quick — I'm here.`,
            `All set. What should we do next?`,
        ];
        const chosen = arrivalMessages[Math.floor(Math.random() * arrivalMessages.length)];
        addChatMessage('aria', chosen);

        // Little celebratory effect and expression
        createEffect('sparkle');
        changeExpression('happy');

        // Short arrival animation (small bounce & glow)
        aria.classList.add('arrived');
        setTimeout(() => aria.classList.remove('arrived'), 900);

        // Clear current waypoint marker so we don't re-announce
        characterState.currentWaypoint = null;
    } catch (e) {
        console.warn('arrivalFeedback failed', e);
    }
}

// Try to resolve a freeform phrase to a waypoint key
function resolveWaypointFromPhrase(phrase) {
    if (!phrase || !waypoints3D) return null;
    const clean = phrase.toLowerCase().replace(/[^a-z0-9\s-]/g, '').trim();
    if (!clean) return null;

    // direct key match (e.g., front-left)
    const direct = clean.replace(/\s+/g, '-');
    if (waypoints3D[direct]) return direct;

    // check by names and partial matches
    for (const k in waypoints3D) {
        const v = waypoints3D[k];
        if (!v) continue;
        const name = String(v.name || '').toLowerCase();
        if (name === clean) return k;
        if (name.includes(clean) || clean.includes(k.replace('-', ' '))) return k;
    }

    // synonyms mapping for simple words
    const synonyms = {
        'front': 'front-center', 'back': 'back-center', 'left': 'stage-left', 'right': 'stage-right', 'center': 'center', 'table': 'table'
    };
    if (synonyms[clean]) return synonyms[clean];

    // try matching tokens
    const tokens = clean.split(/\s+/);
    for (const t of tokens) {
        if (synonyms[t]) return synonyms[t];
    }

    return null;
}

// Process chat input: supports slash commands and normal commands
async function sendChat() {
    const chatBox = document.getElementById('chatInput');
    if (!chatBox) return;

    const text = chatBox.value.trim();
    if (!text) return;

    // Show user's message
    addChatMessage('user', text);
    chatBox.value = '';

    // check for natural language movements (e.g., "go to front-right" or "walk to table")
    const nlMove = /(?:go to|move to|walk to|goto)\s+([a-z0-9\-\s]+)/i.exec(text);
    if (nlMove) {
        const targetPhrase = nlMove[1].trim();
        // try to match known waypoint keys or names
        const candidate = resolveWaypointFromPhrase(targetPhrase);
        if (candidate) {
            moveToWaypoint(candidate);
            addChatMessage('aria', `Moving to ${waypoints3D[candidate].name}`);
        } else {
            addChatMessage('aria', `I couldn't identify a waypoint for '${targetPhrase}'. Try /waypoints`);
        }
        return;
    }

    // /say command — speak directly as Aria
    if (text.startsWith('/say ')) {
        const sayText = text.slice(5).trim();
        if (sayText) {
            // Aria says it in the chat
            addChatMessage('aria', sayText);
            // small visual cue
            createEffect('sparkle');
            changeExpression('smile');
        }
        return;
    }

    // slash commands handled locally
    if (text.startsWith('/goto ') || text.startsWith('/move ') || text.startsWith('/moveTo ')) {
        const parts = text.split(/\s+/, 2);
        const waypoint = parts[1] ? parts[1].trim() : '';
        if (waypoints3D && waypoints3D[waypoint]) {
            moveToWaypoint(waypoint);
            addChatMessage('aria', `Moving to ${waypoints3D[waypoint].name}`);
        } else {
            addChatMessage('aria', `Unknown waypoint '${waypoint}'. Try /waypoints`);
        }
        return;
    }

    if (text === '/waypoints') {
        const entries = Object.entries(waypoints3D).map(([k, v]) => `${k} — ${v.name}`);
        addChatMessage('aria', `Available waypoints: ${entries.join(', ')}`);
        return;
    }

    if (text === '/circle' || text === '/circle3d') {
        moveInCircle3D();
        addChatMessage('aria', 'Starting 3D circle movement');
        return;
    }

    if (text === '/spiral' || text === '/spiral3d') {
        performSpiral3D();
        addChatMessage('aria', 'Starting 3D spiral');
        return;
    }

    if (text === '/stop') {
        // stop behaviors
        if (typeof stopContinuousDance === 'function') stopContinuousDance();
        addChatMessage('aria', 'Stopped continuous actions');
        return;
    }

    // Otherwise, send as a command to backend (and display response when available)
    commandInput.value = text;
    const result = await sendCommand();

    if (!result) {
        addChatMessage('aria', 'No response from backend (fallback executed)');
        return;
    }

    if (result.error) {
        addChatMessage('aria', `Error: ${result.error}`);
        return;
    }

    // Prefer textual response if available
    if (result.response) {
        addChatMessage('aria', result.response);
    } else if (result.tags && result.tags.length > 0) {
        addChatMessage('aria', `Executed tags: ${result.tags.join(' ')}`);
    } else if (result.stage_context) {
        // Keep stage context short
        const ctx = result.stage_context.split('\n').slice(0,4).join(' | ');
        addChatMessage('aria', ctx);
    } else {
        addChatMessage('aria', 'Done.');
    }
}

async function sendCommand() {
    const command = commandInput.value.trim();
    if (!command) return;
    
    log(`Command: "${command}"`);
    commandInput.value = '';
    
    try {
        // Gather current stage state for AI to see
        const stageRect = stage.getBoundingClientRect();
        const ariaRect = aria.getBoundingClientRect();
        
        // Calculate Aria's position as percentages
        const ariaX = ((ariaRect.left - stageRect.left) / stageRect.width) * 100;
        const ariaY = 100 - ((ariaRect.bottom - stageRect.top) / stageRect.height) * 100;
        
        // Gather object positions
        const objectPositions = {};
        ['apple', 'book', 'cup', 'ball', 'flower'].forEach(objId => {
            const obj = document.getElementById(objId);
            if (obj) {
                const objRect = obj.getBoundingClientRect();
                objectPositions[objId] = {
                    x: ((objRect.left - stageRect.left) / stageRect.width) * 100,
                    y: 100 - ((objRect.bottom - stageRect.top) / stageRect.height) * 100,
                    state: obj.classList.contains('held') ? 'held' : 'on_table'
                };
            }
        });
        
        const currentStageState = {
            aria: {
                position: { x: Math.round(ariaX), y: Math.round(ariaY) },
                expression: characterState.mood || 'neutral',
                held_object: characterState.heldObject,
                facing: 'right'
            },
            objects: objectPositions
        };
        
        // Call backend API with stage state
        const response = await fetch('/api/aria/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                command: command,
                stage_state: currentStageState
            })
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
        // Return the parsed result so callers (chat UI) can inspect tags / response
        return data;
    } catch (error) {
        log(`⚠️ Network error, using fallback`, true);
        // Fallback: parse command locally without AI
        executeLocalCommand(command);
        return { error: String(error) };
    }
}

function setPosition(xPercent, yPercent, zDepth = 0, rotateY = 0) {
    // AI-driven animated walking to position in 3D space (not teleporting)
    const stageRect = stage.getBoundingClientRect();
    const ariaRect = aria.getBoundingClientRect();
    
    // Get current position
    const currentX = ((ariaRect.left - stageRect.left) / stageRect.width) * 100;
    const currentY = 100 - ((ariaRect.bottom - stageRect.top) / stageRect.height) * 100;
    
    // Clamp target values
    xPercent = Math.max(5, Math.min(95, xPercent));
    yPercent = Math.max(5, Math.min(95, yPercent));
    zDepth = Math.max(-300, Math.min(200, zDepth)); // Z range: -300px (far) to 200px (near)
    
    // Calculate distance and direction
    const deltaX = xPercent - currentX;
    const deltaY = yPercent - currentY;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    
    // Don't move if already at target
    if (distance < 2) {
        log(`📍 Already at position (${Math.round(xPercent)}%, ${Math.round(yPercent)}%, Z:${Math.round(zDepth)}px)`);
        // If we were moving towards a known waypoint, confirm arrival
        if (characterState.currentWaypoint) {
            arrivalFeedback(characterState.currentWaypoint);
        }
        return;
    }
    
    // Determine walking speed and style based on distance
    let duration = Math.min(distance * 40, 2000); // 40ms per percent, max 2s
    let walkStyle = 'normal';
    
    if (distance > 50) {
        walkStyle = 'run';
        duration = distance * 20; // Faster for long distances
    } else if (distance > 30) {
        walkStyle = 'walk';
        duration = distance * 30;
    }
    
    // Face the direction of movement in 3D
    let rotationAngle = rotateY || 0;
    if (deltaX > 2) {
        rotationAngle = 0; // Face camera (right)
    } else if (deltaX < -2) {
        rotationAngle = 180; // Face away (left)
    }
    
    // Add walking animation
    aria.classList.add('walking');
    if (walkStyle === 'run') {
        aria.classList.add('running');
    }
    
    // Animate legs while moving
    const walkInterval = setInterval(() => {
        animateWalkCycle();
    }, 200);
    
    // Smooth 3D transition to target
    aria.style.transition = `left ${duration}ms ease-in-out, bottom ${duration}ms ease-in-out, transform ${duration}ms ease-in-out`;
    
    const leftPercent = xPercent;
    const bottomPercent = 100 - yPercent;  // Invert Y (CSS bottom increases upward)
    
    aria.style.left = leftPercent + '%';
    aria.style.bottom = bottomPercent + '%';
    
    // Apply 3D transform with Z-depth and rotation
    const scaleX = rotationAngle === 180 ? -1 : 1;
    aria.style.transform = `translateX(-50%) translateZ(${zDepth}px) rotateY(${rotationAngle}deg) scaleX(${scaleX})`;
    
    // Update character state
    characterState.position = { x: xPercent, y: yPercent, z: zDepth };
    characterState.rotation = rotationAngle;
    
    log(`🚶 Walking to (${Math.round(xPercent)}%, ${Math.round(yPercent)}%, Z:${Math.round(zDepth)}px, Rot:${Math.round(rotationAngle)}°) - ${walkStyle} style`);
    showFeedback(`🚶 3D WALK: X${Math.round(xPercent)}% Y${Math.round(yPercent)}% Z${Math.round(zDepth)}px`);
    
    // Stop walking animation when arrived
    setTimeout(() => {
        aria.classList.remove('walking', 'running');
        aria.style.transition = ''; // Reset transition
        clearInterval(walkInterval);
        resetWalkCycle();
        spawnDustCloud(); // landing dust
        log(`✅ Arrived at (${Math.round(xPercent)}%, ${Math.round(yPercent)}%)`);
        // If we were targeting a waypoint, announce in chat
        if (characterState.currentWaypoint) {
            arrivalFeedback(characterState.currentWaypoint);
        }
    }, duration);
}

// Walking animation cycle
function animateWalkCycle() {
    const leftLeg = document.querySelector('.aria-lower-leg.left');
    const rightLeg = document.querySelector('.aria-lower-leg.right');
    const leftArm = document.querySelector('.aria-lower-arm.left');
    const rightArm = document.querySelector('.aria-lower-arm.right');
    
    if (!leftLeg || !rightLeg) return;
    
    // Alternate leg swings
    if (leftLeg.style.transform.includes('rotate')) {
        leftLeg.style.transform = 'rotate(20deg)';
        rightLeg.style.transform = 'rotate(-20deg)';
        if (leftArm) leftArm.style.transform = 'rotate(-15deg)';
        if (rightArm) rightArm.style.transform = 'rotate(15deg)';
    } else {
        leftLeg.style.transform = 'rotate(-20deg)';
        rightLeg.style.transform = 'rotate(20deg)';
        if (leftArm) leftArm.style.transform = 'rotate(15deg)';
        if (rightArm) rightArm.style.transform = 'rotate(-15deg)';
    }
}

function resetWalkCycle() {
    const leftLeg = document.querySelector('.aria-lower-leg.left');
    const rightLeg = document.querySelector('.aria-lower-leg.right');
    const leftArm = document.querySelector('.aria-lower-arm.left');
    const rightArm = document.querySelector('.aria-lower-arm.right');
    
    if (leftLeg) leftLeg.style.transform = '';
    if (rightLeg) rightLeg.style.transform = '';
    if (leftArm) leftArm.style.transform = '';
    if (rightArm) rightArm.style.transform = '';
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
    
    // Effects - with intensity detection
    let effectIntensity = 'normal';
    if (cmd.includes('light') || cmd.includes('subtle') || cmd.includes('gentle')) {
        effectIntensity = 'light';
    } else if (cmd.includes('heavy') || cmd.includes('intense') || cmd.includes('lots') || cmd.includes('many')) {
        effectIntensity = 'heavy';
    }

    if (cmd.includes('sparkle') || cmd.includes('glitter') || cmd.includes('shimmer') || cmd.includes('shine')) {
        createEffect('sparkle', effectIntensity);
        executed = true;
    }
    if (cmd.includes('hearts') || cmd.includes('heart') || cmd.includes('love')) {
        createEffect('hearts', effectIntensity);
        executed = true;
    }
    if (cmd.includes('glow') || cmd.includes('glowing') || cmd.includes('radiate') || cmd.includes('illuminate')) {
        createEffect('glow', effectIntensity);
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
                case 'position':
                    console.log('Executing position:', action, param);
                    if (action && param) {
                        // Format: [aria:position:x:y] or [aria:position:x:y:z:rotation]
                        const parts = tag.match(/\[aria:position:([^:\]]+):([^:\]]+)(?::([^:\]]+))?(?::([^\]]+))?\]/);
                        if (parts) {
                            const x = parseInt(parts[1]);
                            const y = parseInt(parts[2]);
                            const z = parts[3] ? parseInt(parts[3]) : 0;
                            const rotation = parts[4] ? parseInt(parts[4]) : 0;
                            setPosition(x, y, z, rotation);
                        } else {
                            setPosition(parseInt(action), parseInt(param));
                        }
                    }
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
                    if (action === 'add') {
                        const [objectName, emoji] = param.split(':');
                        addObject(objectName, emoji || '🧸');
                    } else {
                        interactWithObject(action, param);
                    }
                    break;
                case 'effect':
                    createEffect(action, param || 'normal');
                    break;
                case 'camera':
                    if (action === 'center') centerAria();
                    break;
                case 'pose':
                    applyPose(action, param);
                    break;
                case 'say':
                    // Tag formats either [aria:say:Hello world] or [aria:say:utterance:extra]
                    const spoken = param || action;
                    if (spoken) {
                        addChatMessage('aria', String(spoken));
                    }
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
    ariaMouth.style.transform = '';
    
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

    // Emit mood-appropriate emoji particle
    const moodEmoji = { smile: '😊', happy: '😄', sad: '😢', surprised: '😲', confused: '🤔', thinking: '💭', wink: '😉' };
    const emoji = moodEmoji[emotion];
    if (emoji && stage && aria) {
        const rect = aria.getBoundingClientRect();
        const sr = stage.getBoundingClientRect();
        const cx = ((rect.left + rect.width / 2 - sr.left) / sr.width) * 100;
        const cy = ((rect.top - sr.top) / sr.height) * 100;
        const el = document.createElement('div');
        el.textContent = emoji;
        el.style.cssText = `position:absolute;left:${cx}%;top:${cy}%;font-size:22px;pointer-events:none;z-index:60;transition:all 0.8s ease-out;opacity:1;`;
        stage.appendChild(el);
        requestAnimationFrame(() => { el.style.transform = 'translateY(-30px) scale(1.3)'; el.style.opacity = '0'; });
        setTimeout(() => el.remove(), 900);
    }
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

// 3D Waypoint System - Fixed positions in 3D space
const waypoints3D = {
    'center': { x: 50, y: 50, z: 0, rotation: 0, name: 'Center Stage' },
    'front-left': { x: 25, y: 70, z: 150, rotation: 45, name: 'Front Left' },
    'front-right': { x: 75, y: 70, z: 150, rotation: -45, name: 'Front Right' },
    'back-left': { x: 25, y: 30, z: -200, rotation: 135, name: 'Back Left' },
    'back-right': { x: 75, y: 30, z: -200, rotation: -135, name: 'Back Right' },
    'front-center': { x: 50, y: 75, z: 180, rotation: 0, name: 'Front Center' },
    'back-center': { x: 50, y: 25, z: -250, rotation: 180, name: 'Back Center' },
    'stage-left': { x: 15, y: 50, z: -50, rotation: 90, name: 'Stage Left' },
    'stage-right': { x: 85, y: 50, z: -50, rotation: -90, name: 'Stage Right' },
    'table': { x: 60, y: 20, z: -100, rotation: 0, name: 'Near Table' }
};

function moveToWaypoint(waypointName) {
    const waypoint = waypoints3D[waypointName];
    if (!waypoint) {
        log(`❌ Unknown waypoint: ${waypointName}`, true);
        return false;
    }
    
    log(`📍 Moving to waypoint: ${waypoint.name}`);
    showFeedback(`📍 WAYPOINT: ${waypoint.name}`);
    // Notify in chat that Aria is moving
    addChatMessage('aria', `Heading to ${waypoint.name}...`);
    characterState.currentWaypoint = waypointName;
    setPosition(waypoint.x, waypoint.y, waypoint.z, waypoint.rotation);
    return true;
}

function moveInCircle3D(radius = 30, steps = 12, duration = 6000) {
    let currentStep = 0;
    const centerX = 50;
    const centerY = 50;
    const stepDuration = duration / steps;
    
    const circleInterval = setInterval(() => {
        if (currentStep >= steps) {
            clearInterval(circleInterval);
            log('🔄 Circle completed');
            addChatMessage('aria', 'Finished circular movement.');
            return;
        }
        
        const angle = (currentStep / steps) * Math.PI * 2;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        const z = 100 * Math.sin(angle * 2); // Wave in/out on Z-axis
        const rotation = (angle * 180 / Math.PI) + 90; // Face tangent to circle
        
        setPosition(x, y, z, rotation);
        currentStep++;
    }, stepDuration);
    
    log('🔄 Starting 3D circle movement');
    showFeedback('🔄 3D CIRCLE');
    addChatMessage('aria', 'Starting circular 3D movement');
}

function performSpiral3D() {
    const steps = 20;
    const duration = 8000;
    let currentStep = 0;
    const centerX = 50;
    const centerY = 50;
    
    const spiralInterval = setInterval(() => {
        if (currentStep >= steps) {
            clearInterval(spiralInterval);
            log('🌀 Spiral completed');
            addChatMessage('aria', 'Finished spiral movement.');
            return;
        }
        
        const progress = currentStep / steps;
        const radius = 40 * (1 - progress); // Shrink radius
        const angle = progress * Math.PI * 6; // Multiple rotations
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        const z = -200 + progress * 300; // Move from back to front
        const rotation = angle * 180 / Math.PI;
        
        setPosition(x, y, z, rotation);
        currentStep++;
    }, duration / steps);
    
    log('🌀 Starting 3D spiral movement');
    showFeedback('🌀 3D SPIRAL');
    addChatMessage('aria', 'Starting 3D spiral movement');
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
        setTimeout(() => {
            resetLimbs(200);
            isPerformingAction = false;
        }, 800);
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

function createEffect(type, intensity = 'normal') {
    const effects = {
        'sparkle': '✨',
        'glow': '💫',
        'hearts': '💕'
    };

    // Intensity configurations
    const intensityConfig = {
        'light': { count: 3, spread: 60, duration: 1200, delay: 150 },
        'normal': { count: 5, spread: 80, duration: 1500, delay: 100 },
        'heavy': { count: 10, spread: 90, duration: 1800, delay: 60 }
    };

    const config = intensityConfig[intensity] || intensityConfig['normal'];
    const emoji = effects[type] || '✨';

    // Color variations for sparkle effect
    const sparkleColors = ['#FFD700', '#FFA500', '#FFFF00', '#FFE4B5', '#FAFAD2'];

    // Use requestAnimationFrame for better performance
    let createdCount = 0;

    function createSingleEffect() {
        if (createdCount >= config.count) return;

        const effect = document.createElement('div');
        effect.className = `effect ${type}`;
        effect.textContent = emoji;

        // Random position within spread area
        const centerX = 50;
        const centerY = 50;
        const spreadRadius = config.spread / 2;
        effect.style.left = (centerX + (Math.random() - 0.5) * spreadRadius) + '%';
        effect.style.top = (centerY + (Math.random() - 0.5) * spreadRadius) + '%';

        // Add color variation for sparkle
        if (type === 'sparkle') {
            effect.style.filter = `hue-rotate(${Math.random() * 360}deg)`;
        }

        // Add random rotation for variety
        effect.style.transform = `rotate(${Math.random() * 360}deg)`;

        stage.appendChild(effect);

        // Remove after duration
        setTimeout(() => {
            if (effect.parentNode) {
                effect.remove();
            }
        }, config.duration);

        createdCount++;

        // Schedule next effect
        if (createdCount < config.count) {
            requestAnimationFrame(() => {
                setTimeout(createSingleEffect, config.delay);
            });
        }
    }

    // Start effect creation
    requestAnimationFrame(createSingleEffect);
}

// Dust cloud on landing / arrival
function spawnDustCloud() {
    if (!stage || !aria) return;
    const rect = aria.getBoundingClientRect();
    const stageRect = stage.getBoundingClientRect();
    const cx = ((rect.left + rect.width / 2 - stageRect.left) / stageRect.width) * 100;
    const cy = ((rect.bottom - stageRect.top) / stageRect.height) * 100;
    for (let i = 0; i < 6; i++) {
        const p = document.createElement('div');
        p.style.cssText = `position:absolute;left:${cx + (Math.random()-0.5)*8}%;top:${cy - Math.random()*3}%;width:${6+Math.random()*6}px;height:${6+Math.random()*6}px;background:rgba(160,140,120,${0.3+Math.random()*0.3});border-radius:50%;pointer-events:none;z-index:5;transition:all ${0.4+Math.random()*0.4}s ease-out;`;
        stage.appendChild(p);
        requestAnimationFrame(() => {
            p.style.transform = `translate(${(Math.random()-0.5)*30}px, ${-10-Math.random()*20}px) scale(${1.5+Math.random()})`;
            p.style.opacity = '0';
        });
        setTimeout(() => p.remove(), 900);
    }
}

// Ambient idle sparkles — gentle occasional twinkle near Aria
let _idleSparkleInterval = null;
function startIdleSparkles() {
    if (_idleSparkleInterval) return;
    _idleSparkleInterval = setInterval(() => {
        if (!aria || !stage) return;
        // Only sparkle when idle (not walking/dancing)
        if (aria.classList.contains('walking') || aria.classList.contains('dancing') || aria.classList.contains('running')) return;
        if (Math.random() > 0.35) return; // ~35% chance each tick
        const rect = aria.getBoundingClientRect();
        const stageRect = stage.getBoundingClientRect();
        const cx = ((rect.left + rect.width / 2 - stageRect.left) / stageRect.width) * 100;
        const cy = ((rect.top + rect.height * 0.3 - stageRect.top) / stageRect.height) * 100;
        const s = document.createElement('div');
        s.textContent = '✦';
        s.style.cssText = `position:absolute;left:${cx + (Math.random()-0.5)*10}%;top:${cy + (Math.random()-0.5)*8}%;font-size:${8+Math.random()*8}px;color:rgba(255,215,0,${0.4+Math.random()*0.4});pointer-events:none;z-index:50;transition:all ${0.6+Math.random()*0.6}s ease-out;`;
        stage.appendChild(s);
        requestAnimationFrame(() => {
            s.style.transform = `translateY(${-15-Math.random()*15}px) scale(0.3)`;
            s.style.opacity = '0';
        });
        setTimeout(() => s.remove(), 1400);
    }, 2000);
}
startIdleSparkles();

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

// Automatic character evolution disabled - keeping neutral human-like appearance
// setInterval(randomCharacterEvolution, 30000);

// Initialize
log('🎨 Aria Visual System Ready!');
log('🤖 AI Character Generation: ACTIVE');
log('Type commands or use quick buttons');

// Object Interaction System
// Helper: derive stage-relative percentage position from an element
function objectPositionFromElement(elem) {
    if (!elem) return null;
    const stageRect = stage.getBoundingClientRect();
    // Prefer explicit CSS left/bottom if present (percent strings)
    try {
        if (elem.style && elem.style.left && elem.style.bottom) {
            const left = parseFloat(elem.style.left || 0);
            const bottom = parseFloat(elem.style.bottom || 0);
            // The JS 'y' value used elsewhere equals the CSS bottom percent
            return { x: Math.round(left), y: Math.round(bottom) };
        }
    } catch (e) {
        // fallthrough to computed rect
    }

    const rect = elem.getBoundingClientRect();
    const x = ((rect.left - stageRect.left) / stageRect.width) * 100;
    const y = 100 - ((rect.bottom - stageRect.top) / stageRect.height) * 100;
    return { x: Math.round(x), y: Math.round(y) };
}

// Notify backend of object add/update/remove actions
async function sendObjectUpdate(action, objectId, extra = {}) {
    try {
        if (!objectId) return null;
        const objEl = document.getElementById(objectId);

        // resolve position and state
        let position = extra.position || null;
        if (!position && objEl) position = objectPositionFromElement(objEl);

        const state = extra.state || (objEl ? (objEl.classList.contains('held') ? 'held' : (objEl.style.display === 'none' ? 'hidden' : 'on_table')) : (extra.state || 'unknown'));
        const emoji = extra.emoji || (objEl ? objEl.textContent : undefined);

        const objPayload = { id: objectId };
        if (position !== null && position !== undefined) objPayload.position = position;
        if (state !== null && state !== undefined) objPayload.state = state;
        if (emoji !== null && emoji !== undefined) objPayload.emoji = emoji;
        const payload = { action: action, object: objPayload };

        const res = await fetch('/api/aria/object', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            console.warn('Object API returned non-OK status', res.status);
            return null;
        }

        const data = await res.json();
        console.log('object sync:', action, objectId, data);
        return data;
    } catch (err) {
        console.warn('sendObjectUpdate failed:', err);
        return null;
    }
}
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

    // Sync server side: mark object as held
    sendObjectUpdate('update', objectId, { state: 'held' }).catch(() => {});
    
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

    // Sync server side: update object's position/state
    const finalX = Math.round(dropLeft);
    const finalY = Math.round(dropBottom + 10);
    const tableX = 60; // server default table X
    const isOnTable = Math.abs(finalX - tableX) < 20 && Math.abs(finalY - 35) < 20;
    sendObjectUpdate('update', obj.id, { position: { x: finalX, y: finalY }, state: isOnTable ? 'on_table' : 'on_stage' }).catch(() => {});
    
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

    // Sync server side after throw completes
    setTimeout(() => {
        const left = Math.round(targetLeft);
        const bottom = Math.round(targetBottom);
        sendObjectUpdate('update', obj.id, { position: { x: left, y: bottom }, state: 'on_stage' }).catch(() => {});
    }, 900);
    
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
        // Prevent adding duplicate event listeners when called multiple times
        if (obj.__interactionInitialized) return;
        obj.__interactionInitialized = true;
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
                // Sync backend with final position
                const pos = objectPositionFromElement(obj);
                const state = obj.classList.contains('held') ? 'held' : 'on_table';
                sendObjectUpdate('update', obj.id, { position: pos, state: state }).catch(() => {});
            }
        });
    });
}

function addObject(objectName, emoji) {
    console.log('➕ Adding object:', objectName, emoji);
    
    // Check if object already exists
    const existingObj = document.getElementById(objectName);
    if (existingObj) {
        console.log('⚠️ Object already exists:', objectName);
        showFeedback('✅ ' + objectName + ' already on stage');
        return;
    }
    
    // Create new object element
    const newObj = document.createElement('div');
    newObj.id = objectName;
    newObj.className = 'object';
    newObj.textContent = emoji;
    
    // Position near Aria
    const ariaX = characterState.position.x;
    const ariaY = characterState.position.y;
    newObj.style.left = Math.max(10, Math.min(90, ariaX + 15)) + '%';
    newObj.style.bottom = Math.max(10, Math.min(90, ariaY + 5)) + '%';
    
    // Add to stage
    stage.appendChild(newObj);
    
    // Update tracking
    activeObjects[objectName] = true;
    
    // Add to object manager if button doesn't exist
    if (!document.querySelector(`[onclick="toggleObject('${objectName}')"]`)) {
        const objectManager = document.getElementById('object-manager');
        const btn = document.createElement('button');
        btn.className = 'object-btn active';
        btn.id = 'btn-' + objectName;
        btn.textContent = emoji + ' ' + objectName;
        btn.onclick = () => toggleObject(objectName);
        objectManager.appendChild(btn);
    }
    
    // Initialize interactions for new object (click/drag)
    initializeObjectInteractions();

    // Sync server: add new object to stage_state
    sendObjectUpdate('add', objectName, { position: objectPositionFromElement(newObj), state: 'on_stage', emoji: emoji }).catch(() => {});
    
    showFeedback('✨ Added ' + objectName + ' to stage!');
    console.log('✅ Object added successfully:', objectName);
}

// Initialize object interactions
initializeObjectInteractions();
log('🎮 Objects: apple, book, cup, ball, flower');
log('💡 Try: "pick up apple", "drop", "throw ball"');

// Auto-behaviors with random timing
function startAutoBehaviors() {
    // Random idle movements every 8-15 seconds
    setInterval(() => {
        if (Math.random() > 0.6) {
            const randomActions = ['shift weight', 'look around', 'adjust hair', 'stretch'];
            const action = randomActions[Math.floor(Math.random() * randomActions.length)];
            
            switch(action) {
                case 'shift weight':
                    animate('bouncing');
                    setTimeout(() => aria.style.animation = 'breathe 4s ease-in-out infinite', 800);
                    break;
                case 'look around':
                    const ariaHead = document.querySelector('.aria-head');
                    ariaHead.style.transform = 'translateX(-50%) rotate(10deg)';
                    setTimeout(() => ariaHead.style.transform = 'translateX(-50%) rotate(-10deg)', 600);
                    setTimeout(() => ariaHead.style.transform = 'translateX(-50%)', 1200);
                    break;
                case 'adjust hair':
                    const hand = document.getElementById('ariaHandRight');
                    hand.style.transform = 'translateY(-30px) rotate(-20deg)';
                    setTimeout(() => hand.style.transform = '', 1000);
                    break;
                case 'stretch':
                    ariaArmLeft.style.transform = 'rotate(-160deg)';
                    ariaArmRight.style.transform = 'rotate(160deg)';
                    setTimeout(() => {
                        ariaArmLeft.style.transform = '';
                        ariaArmRight.style.transform = '';
                    }, 1500);
                    break;
            }
        }
    }, 8000 + Math.random() * 7000);
    
    // Random expressions every 12-20 seconds
    setInterval(() => {
        if (Math.random() > 0.5) {
            const expressions = ['smile', 'thinking', 'neutral', 'surprised'];
            const expr = expressions[Math.floor(Math.random() * expressions.length)];
            changeExpression(expr);
            setTimeout(() => changeExpression('neutral'), 2000 + Math.random() * 3000);
        }
    }, 12000 + Math.random() * 8000);
    
    // Occasional sparkles every 20-30 seconds
    setInterval(() => {
        if (Math.random() > 0.7) {
            createEffect('sparkle');
        }
    }, 20000 + Math.random() * 10000);
}

// Initial appearance set to neutral human-like style
setTimeout(() => {
    log('🎨 Setting initial character appearance...');
    const neutralStyle = generateCharacterFromMood('neutral', 50);
    applyCharacterStyle(neutralStyle);
}, 100);

// Start idle animations
startIdleAnimation();
log('👀 Idle animations enabled - watch for breathing and blinking!');

// Start automatic behaviors
startAutoBehaviors();
log('✨ Auto-behaviors enabled - Aria will move and react on her own!');

// === Eye tracking (follows mouse cursor) ===
(function initEyeTracking() {
    const eyes = document.querySelectorAll('.aria-eye');
    if (!eyes.length || !stage) return;

    document.addEventListener('mousemove', function(e) {
        eyes.forEach(function(eye) {
            const rect = eye.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top + rect.height / 2;
            const angle = Math.atan2(e.clientY - cy, e.clientX - cx);
            const dist = Math.min(3, Math.hypot(e.clientX - cx, e.clientY - cy) / 50);
            const dx = Math.cos(angle) * dist;
            const dy = Math.sin(angle) * dist;
            // Shift the eye's radial gradient to simulate looking
            eye.style.backgroundPosition = `${50 + dx * 5}% ${50 + dy * 5}%`;
        });
    });

    log('👁️ Eye tracking active — Aria follows your cursor!');
})();

// === Natural blink cycle ===
(function initBlinkCycle() {
    function doBlink() {
        if (!ariaEyeLeft || !ariaEyeRight) return;
        // Skip if performing action or mid-expression
        if (isPerformingAction) return;
        const origL = ariaEyeLeft.style.height;
        const origR = ariaEyeRight.style.height;
        ariaEyeLeft.style.transition = 'height 0.06s';
        ariaEyeRight.style.transition = 'height 0.06s';
        ariaEyeLeft.style.height = '1px';
        ariaEyeRight.style.height = '1px';
        setTimeout(function() {
            ariaEyeLeft.style.height = origL || '';
            ariaEyeRight.style.height = origR || '';
            ariaEyeLeft.style.transition = '';
            ariaEyeRight.style.transition = '';
        }, 120);
    }
    // Natural blink interval: 3-6 seconds with occasional double-blink
    function scheduleBlink() {
        const delay = 3000 + Math.random() * 3000;
        setTimeout(function() {
            doBlink();
            // 20% chance of a double-blink
            if (Math.random() < 0.2) {
                setTimeout(doBlink, 250);
            }
            scheduleBlink();
        }, delay);
    }
    scheduleBlink();
})();

// Expose minimal testing helpers
window.ariaTest = {
    limb: (part, actionOrAngle, duration) => handleLimbTag(part, typeof actionOrAngle === 'number' ? `${actionOrAngle},${duration||500}` : `${actionOrAngle||''}${duration?','+duration:''}`),
    pose: (name) => applyPose(name)
};
window.simulateTags = (arr) => Array.isArray(arr) && executeTags(arr);

