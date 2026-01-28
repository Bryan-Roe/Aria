"""
Enhanced Avatar System for Aria
================================

Provides 3D-like avatar rendering with:
- Dynamic facial expressions
- Eye tracking and gaze
- Adaptive animations
- Breathing and idle effects
- Gesture system
- Real-time expression changes
"""

// CSS 3D Avatar Styles
const AvatarStyles = `
<style>
  /* 3D Avatar Container */
  .aria-avatar-3d {
    position: relative;
    width: 200px;
    height: 280px;
    perspective: 1000px;
    margin: 0 auto;
  }

  /* Head - Main avatar component */
  .avatar-head {
    position: relative;
    width: 100px;
    height: 120px;
    margin: 0 auto;
    background: linear-gradient(135deg, #fdbcb4 0%, #f8a896 50%, #f4a582 100%);
    border-radius: 50% 50% 45% 45%;
    box-shadow: 
      inset -20px -20px 30px rgba(0,0,0,0.1),
      inset 20px 20px 30px rgba(255,255,255,0.3),
      0 10px 30px rgba(0,0,0,0.2);
    transform-style: preserve-3d;
    animation: head-breathe 4s ease-in-out infinite;
  }

  @keyframes head-breathe {
    0%, 100% { transform: scaleY(1); }
    50% { transform: scaleY(1.02); }
  }

  /* Eyes */
  .avatar-eyes {
    display: flex;
    justify-content: space-around;
    gap: 15px;
    margin-top: 25px;
    padding: 0 15px;
  }

  .avatar-eye {
    width: 18px;
    height: 24px;
    background: white;
    border-radius: 50%;
    position: relative;
    box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
    overflow: hidden;
  }

  .avatar-pupil {
    width: 10px;
    height: 12px;
    background: #2c3e50;
    border-radius: 50%;
    position: absolute;
    top: 6px;
    left: 4px;
    transition: all 0.05s ease-out;
  }

  .avatar-eye.closed .avatar-pupil {
    display: none;
  }

  .avatar-eye.closed::after {
    content: '';
    position: absolute;
    width: 100%;
    height: 3px;
    background: #2c3e50;
    top: 50%;
    left: 0;
    transform: translateY(-50%);
    animation: eye-blink 0.3s ease;
  }

  @keyframes eye-blink {
    0%, 100% { height: 3px; }
    50% { height: 18px; }
  }

  /* Eye gaze tracking */
  .avatar-eye.looking-left .avatar-pupil { left: 2px; }
  .avatar-eye.looking-right .avatar-pupil { left: 6px; }
  .avatar-eye.looking-up .avatar-pupil { top: 3px; }
  .avatar-eye.looking-down .avatar-pupil { top: 9px; }

  /* Eyebrows */
  .avatar-eyebrows {
    display: flex;
    justify-content: space-around;
    gap: 15px;
    padding: 0 15px;
    margin-top: 5px;
  }

  .avatar-eyebrow {
    width: 20px;
    height: 5px;
    background: #8B4513;
    border-radius: 50%;
    transform-origin: center;
    transition: all 0.2s ease;
  }

  /* Eyebrow expressions */
  .avatar-head.surprised .avatar-eyebrow {
    transform: translateY(-5px) rotate(20deg);
  }

  .avatar-head.confused .avatar-eyebrow {
    transform: rotate(-15deg);
  }

  .avatar-head.happy .avatar-eyebrow {
    transform: rotate(15deg);
  }

  .avatar-head.angry .avatar-eyebrow {
    transform: rotate(-25deg);
  }

  /* Mouth */
  .avatar-mouth {
    position: absolute;
    bottom: 25px;
    left: 50%;
    transform: translateX(-50%);
    width: 30px;
    height: 15px;
    border: 2px solid #d4634f;
    border-top: none;
    border-radius: 0 0 30px 30px;
    transition: all 0.2s ease;
  }

  /* Mouth expressions */
  .avatar-head.neutral .avatar-mouth {
    border-radius: 0 0 30px 30px;
    height: 8px;
  }

  .avatar-head.happy .avatar-mouth {
    border-radius: 0 0 50px 50px;
    height: 18px;
    border-color: #c0392b;
  }

  .avatar-head.sad .avatar-mouth {
    transform: translateX(-50%) scaleY(-1);
    border-radius: 50px 50px 0 0;
    height: 12px;
  }

  .avatar-head.surprised .avatar-mouth {
    border-radius: 50%;
    width: 20px;
    height: 20px;
    bottom: 20px;
  }

  .avatar-head.confused .avatar-mouth {
    border-radius: 50% 50% 0 0;
    height: 12px;
  }

  /* Nose */
  .avatar-nose {
    position: absolute;
    top: 50px;
    left: 50%;
    transform: translateX(-50%);
    width: 8px;
    height: 12px;
    background: #d9a48a;
    border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
    box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
  }

  /* Blush */
  .avatar-blush {
    position: absolute;
    width: 20px;
    height: 15px;
    background: radial-gradient(circle at 30% 40%, rgba(255,0,0,0.3) 0%, transparent 70%);
    border-radius: 50%;
    top: 65px;
  }

  .avatar-blush.left {
    left: 12px;
  }

  .avatar-blush.right {
    right: 12px;
  }

  .avatar-head.happy .avatar-blush,
  .avatar-head.excited .avatar-blush,
  .avatar-head.shy .avatar-blush {
    opacity: 1;
  }

  .avatar-head.neutral .avatar-blush,
  .avatar-head.concerned .avatar-blush {
    opacity: 0.2;
  }

  /* Body */
  .avatar-body {
    position: relative;
    width: 80px;
    height: 100px;
    margin: 0 auto;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px 15px 30px 30px;
    margin-top: 10px;
    box-shadow: 
      inset -15px -15px 30px rgba(0,0,0,0.1),
      0 10px 20px rgba(0,0,0,0.2);
    transform-style: preserve-3d;
  }

  /* Arms */
  .avatar-arms {
    position: absolute;
    top: 10px;
    left: -25px;
    width: 130px;
    display: flex;
    justify-content: space-between;
    gap: 0;
  }

  .avatar-arm {
    width: 20px;
    height: 70px;
    background: linear-gradient(90deg, #fdbcb4 0%, #f8a896 100%);
    border-radius: 10px;
    box-shadow: 
      inset -5px 0 10px rgba(0,0,0,0.1),
      0 5px 10px rgba(0,0,0,0.15);
    transform-origin: top center;
    transition: transform 0.3s ease;
  }

  .avatar-arm.left {
    transform: rotate(0deg);
  }

  .avatar-arm.right {
    transform: rotate(0deg);
  }

  /* Arm gestures */
  .avatar-body.gesture-wave .avatar-arm.right {
    animation: wave 0.6s ease-in-out;
  }

  @keyframes wave {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(-30deg); }
    75% { transform: rotate(30deg); }
  }

  .avatar-body.gesture-raise-arms .avatar-arm {
    animation: raise-arms 0.4s ease-out;
  }

  @keyframes raise-arms {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(-45deg); }
  }

  .avatar-body.gesture-clap .avatar-arm {
    animation: clap 0.5s ease-in-out;
  }

  @keyframes clap {
    0%, 100% { transform: rotate(0deg); }
    50% { transform: rotate(20deg); }
  }

  /* Animation states */
  .avatar-head.talking {
    animation: head-nod 0.4s ease-in-out;
  }

  @keyframes head-nod {
    0%, 100% { transform: rotateX(0deg) scaleY(1); }
    50% { transform: rotateX(5deg) scaleY(0.98); }
  }

  .avatar-head.thinking {
    animation: head-think 2s ease-in-out infinite;
  }

  @keyframes head-think {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(-5deg); }
    75% { transform: rotate(5deg); }
  }

  /* Overall avatar container animations */
  .aria-avatar-3d.excited {
    animation: jump 0.6s ease-in-out;
  }

  @keyframes jump {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-30px); }
  }

  .aria-avatar-3d.confused {
    animation: tilt 1s ease-in-out;
  }

  @keyframes tilt {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(-8deg); }
    75% { transform: rotate(8deg); }
  }

  .aria-avatar-3d.concerned {
    animation: worry 1.5s ease-in-out infinite;
  }

  @keyframes worry {
    0%, 100% { transform: translateX(0); }
    50% { transform: translateX(-5px); }
  }

  /* LED/Glow effects for different states */
  .avatar-head::before {
    content: '';
    position: absolute;
    inset: -5px;
    background: transparent;
    border-radius: 50% 50% 45% 45%;
    transition: box-shadow 0.3s ease;
  }

  .avatar-head.happy::before {
    box-shadow: 0 0 20px rgba(76, 175, 80, 0.3);
  }

  .avatar-head.excited::before {
    box-shadow: 0 0 30px rgba(255, 193, 7, 0.4);
  }

  .avatar-head.concerned::before {
    box-shadow: 0 0 20px rgba(244, 67, 54, 0.3);
  }

  .avatar-head.thoughtful::before {
    box-shadow: 0 0 20px rgba(63, 81, 181, 0.3);
  }

  /* Accessibility: High contrast mode */
  @media (prefers-contrast: more) {
    .avatar-head {
      border: 2px solid #000;
    }
    .avatar-body {
      border: 2px solid #000;
    }
  }

  /* Reduced motion preferences */
  @media (prefers-reduced-motion: reduce) {
    .avatar-head,
    .avatar-arm,
    .avatar-mouth,
    .aria-avatar-3d {
      animation: none !important;
    }
  }
</style>
`;

/**
 * Enhanced Avatar Component
 * Manages visual representation and animations
 */
class EnhancedAvatar {
  constructor(containerId = 'avatar-container') {
    this.container = document.getElementById(containerId);
    this.currentExpression = 'neutral';
    this.currentGesture = null;
    this.eyeGazeTarget = null;
    this.isBlinking = false;
    this.isTalking = false;
    this.idleAnimationActive = false;
    
    this.init();
  }

  init() {
    // Inject styles
    const style = document.createElement('style');
    style.textContent = AvatarStyles.replace(/^<style>|<\/style>$/g, '');
    document.head.appendChild(style);

    // Create avatar HTML
    this.render();
    
    // Start idle animation
    this.startIdleAnimation();
  }

  render() {
    this.container.innerHTML = `
      <div class="aria-avatar-3d">
        <div class="avatar-head neutral" id="avatar-head">
          <div class="avatar-eyebrows">
            <div class="avatar-eyebrow"></div>
            <div class="avatar-eyebrow"></div>
          </div>
          <div class="avatar-eyes">
            <div class="avatar-eye" id="eye-left">
              <div class="avatar-pupil"></div>
            </div>
            <div class="avatar-eye" id="eye-right">
              <div class="avatar-pupil"></div>
            </div>
          </div>
          <div class="avatar-nose"></div>
          <div class="avatar-blush left"></div>
          <div class="avatar-blush right"></div>
          <div class="avatar-mouth"></div>
        </div>
        <div class="avatar-body" id="avatar-body">
          <div class="avatar-arms">
            <div class="avatar-arm left"></div>
            <div class="avatar-arm right"></div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Set facial expression
   */
  setExpression(expression) {
    const head = document.getElementById('avatar-head');
    
    // Remove previous expression classes
    head.className = head.className.replace(/\s+(neutral|happy|sad|surprised|confused|concerned|excited|thoughtful|angry)\b/g, '');
    
    // Add new expression
    head.classList.add(expression);
    this.currentExpression = expression;
  }

  /**
   * Control eye gaze/tracking
   */
  trackGaze(direction) {
    const eyeLeft = document.getElementById('eye-left');
    const eyeRight = document.getElementById('eye-right');
    const eyes = [eyeLeft, eyeRight];
    
    eyes.forEach(eye => {
      // Remove previous direction
      eye.className = eye.className.replace(/\s+looking-(left|right|up|down)\b/g, '');
      
      if (direction && direction !== 'center') {
        eye.classList.add(`looking-${direction}`);
      }
    });
    
    this.eyeGazeTarget = direction;
  }

  /**
   * Make avatar blink
   */
  blink() {
    if (this.isBlinking) return;
    
    this.isBlinking = true;
    const eyeLeft = document.getElementById('eye-left');
    const eyeRight = document.getElementById('eye-right');
    
    eyeLeft.classList.add('closed');
    eyeRight.classList.add('closed');
    
    setTimeout(() => {
      eyeLeft.classList.remove('closed');
      eyeRight.classList.remove('closed');
      this.isBlinking = false;
    }, 300);
  }

  /**
   * Play gesture animation
   */
  gesture(gestureName) {
    const body = document.getElementById('avatar-body');
    const head = document.getElementById('avatar-head');
    
    // Remove previous gesture
    if (this.currentGesture) {
      body.classList.remove(`gesture-${this.currentGesture}`);
    }
    
    // Add new gesture
    body.classList.add(`gesture-${gestureName}`);
    this.currentGesture = gestureName;
    
    // Gesture-specific head movements
    if (gestureName === 'wave') {
      head.classList.add('happy');
    } else if (gestureName === 'raise-arms') {
      head.classList.add('excited');
    }
  }

  /**
   * Show talking animation
   */
  startTalking() {
    if (this.isTalking) return;
    
    const head = document.getElementById('avatar-head');
    this.isTalking = true;
    head.classList.add('talking');
  }

  /**
   * Stop talking animation
   */
  stopTalking() {
    const head = document.getElementById('avatar-head');
    this.isTalking = false;
    head.classList.remove('talking');
  }

  /**
   * Start idle animation cycle
   */
  startIdleAnimation() {
    const idleAnimations = [
      () => this.blink(),
      () => this.trackGaze('left'),
      () => setTimeout(() => this.trackGaze('center'), 1000),
      () => this.trackGaze('right'),
      () => setTimeout(() => this.trackGaze('center'), 1000),
      () => this.trackGaze('up'),
      () => setTimeout(() => this.trackGaze('center'), 800),
    ];
    
    let animationIndex = 0;
    
    const runIdleAnimation = () => {
      if (!this.isTalking && this.idleAnimationActive) {
        const animation = idleAnimations[animationIndex % idleAnimations.length];
        animation();
        animationIndex++;
      }
      
      setTimeout(runIdleAnimation, 2000 + Math.random() * 3000);
    };
    
    this.idleAnimationActive = true;
    runIdleAnimation();
  }

  /**
   * Show thinking animation
   */
  think() {
    const head = document.getElementById('avatar-head');
    head.classList.add('thinking');
    this.trackGaze('up');
  }

  /**
   * Stop thinking animation
   */
  stopThinking() {
    const head = document.getElementById('avatar-head');
    head.classList.remove('thinking');
    this.trackGaze('center');
  }

  /**
   * Play reaction animation
   */
  react(reactionType) {
    const reactions = {
      'surprise': () => {
        this.setExpression('surprised');
        this.gesture('jump');
        setTimeout(() => this.setExpression('neutral'), 1000);
      },
      'confusion': () => {
        this.setExpression('confused');
        this.trackGaze('left');
        setTimeout(() => {
          this.trackGaze('center');
          this.setExpression('neutral');
        }, 1500);
      },
      'happiness': () => {
        this.setExpression('happy');
        this.gesture('wave');
        setTimeout(() => this.setExpression('neutral'), 1500);
      },
      'concern': () => {
        this.setExpression('concerned');
        this.trackGaze('down');
        setTimeout(() => {
          this.trackGaze('center');
          this.setExpression('neutral');
        }, 1200);
      },
    };
    
    if (reactions[reactionType]) {
      reactions[reactionType]();
    }
  }

  /**
   * Update avatar based on emotional response
   */
  updateFromEmotionalResponse(emotionalResponse) {
    // Set expression
    this.setExpression(emotionalResponse.expression);
    
    // Play gestures
    if (emotionalResponse.gestures && emotionalResponse.gestures.length > 0) {
      const gesture = emotionalResponse.gestures[0];
      this.gesture(gesture.name);
    }
    
    // Eye contact
    if (!emotionalResponse.eye_contact) {
      this.trackGaze('down');
    } else {
      this.trackGaze('center');
    }
  }

  /**
   * Get current visual state
   */
  getState() {
    return {
      expression: this.currentExpression,
      gesture: this.currentGesture,
      eyeGaze: this.eyeGazeTarget,
      isTalking: this.isTalking,
      isBlinking: this.isBlinking,
    };
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { EnhancedAvatar, AvatarStyles };
}
