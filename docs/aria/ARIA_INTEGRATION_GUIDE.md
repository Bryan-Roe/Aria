# Aria Integration Guide: Connecting Human-Like Systems

*Step-by-step guide to integrating personality, avatar, and reasoning systems*

## Overview

This guide shows how to connect:
- **aria_core/human_like_system.py** → Personality & reasoning backend
- **aria_core/enhanced_avatar.js** → Visual avatar frontend
- **function_app.py** → REST API integration
- **aria_web/server.py** → Web server integration
- **docs/index.html** → User-facing chat interface

---

## Phase 1: Backend Integration (function_app.py)

### Step 1: Import Aria Core

```python
# At top of function_app.py
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aria_core'))

from human_like_system import (
    HumanLikeAriaCore,
    get_aria_core,
    EmotionState,
    PersonalityTrait
)

# Initialize Aria core (singleton)
aria = get_aria_core()
```

### Step 2: Modify /api/chat Endpoint

Replace the basic chat endpoint with personality-aware version:

```python
@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint with personality and emotions."""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        # Get Aria core and memory
        aria_instance = get_aria_core()
        
        # Add user input to memory
        aria_instance.memory.add_turn(
            role="user",
            content=user_message,
            timestamp=datetime.now()
        )
        
        # Generate emotional context
        emotion = aria_instance.emotions.generate_emotion(
            user_message,
            context=aria_instance.memory.get_context_window()
        )
        
        # Get chat response from provider
        provider = detect_provider()
        response_text = provider.generate_response(user_message)
        
        # Enhance with personality
        aria_response = aria_instance.personality.add_personality_to_response(
            response_text,
            emotion=emotion
        )
        
        # Add voice patterns
        aria_response = aria_instance.voice.add_speech_patterns(aria_response)
        
        # Add reasoning if complex
        if is_complex_query(user_message):
            reasoning = aria_instance.reasoning.generate_thinking_process(user_message)
        else:
            reasoning = None
        
        # Plan animations for avatar
        animations = plan_response_animations(emotion, user_message)
        
        # Add to memory
        aria_instance.memory.add_turn(
            role="assistant",
            content=aria_response,
            emotion=emotion.name,
            timestamp=datetime.now()
        )
        
        return jsonify({
            'message': aria_response,
            'emotion': emotion.name,
            'intensity': emotion.intensity,
            'animations': animations,
            'reasoning': reasoning,
            'voice_params': aria_instance.voice.get_params_for_emotion(emotion),
            'gesture': aria_instance.behaviors.get_next_gesture(emotion),
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Step 3: Add Streaming Endpoint with Emotions

```python
@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """SSE streaming with real-time emotion updates."""
    data = request.json
    user_message = data.get('message', '')
    
    aria_instance = get_aria_core()
    
    # Record user message
    aria_instance.memory.add_turn(
        role="user",
        content=user_message,
        timestamp=datetime.now()
    )
    
    # Generate emotion for response
    emotion = aria_instance.emotions.generate_emotion(
        user_message,
        context=aria_instance.memory.get_context_window()
    )
    
    def generate():
        """Stream response chunks with emotion metadata."""
        
        # First: Send emotion and planning info
        yield f"data: {json.dumps({'type': 'emotion', 'value': emotion.name, 'intensity': emotion.intensity})}\n\n"
        
        # Second: Stream response text
        provider = detect_provider()
        for chunk in provider.stream_response(user_message):
            yield f"data: {json.dumps({'type': 'text', 'chunk': chunk})}\n\n"
        
        # Third: Send animations after text
        animations = plan_response_animations(emotion, user_message)
        yield f"data: {json.dumps({'type': 'animations', 'value': animations})}\n\n"
        
        # Fourth: Send thinking process if available
        if is_complex_query(user_message):
            thinking = aria_instance.reasoning.generate_thinking_process(user_message)
            yield f"data: {json.dumps({'type': 'reasoning', 'value': thinking})}\n\n"
        
        # Finish
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
```

### Step 4: Add Status Endpoint with Aria Personality

```python
@app.route('/api/aria/personality', methods=['GET'])
def aria_personality_status():
    """Get current Aria personality state."""
    aria_instance = get_aria_core()
    
    return jsonify({
        'personality': aria_instance.personality.traits,
        'current_emotion': aria_instance.emotions.current_emotion.name,
        'mood': aria_instance.behaviors.current_mood,
        'memory_size': len(aria_instance.memory.short_term),
        'dominant_topic': aria_instance.memory.get_dominant_topic(),
        'confidence_in_last_response': aria_instance.reasoning.last_confidence,
    })
```

---

## Phase 2: Web Server Integration (aria_web/server.py)

### Step 1: Add Personality Route

```python
@app.route('/api/aria/state', methods=['GET'])
def get_aria_state():
    """Get current Aria state including personality."""
    from aria_core.human_like_system import get_aria_core
    
    aria_instance = get_aria_core()
    
    return jsonify({
        'stage_state': stage_state.to_dict(),
        'personality': {
            'traits': aria_instance.personality.traits,
            'emotion': aria_instance.emotions.current_emotion.name,
            'emotion_intensity': aria_instance.emotions.current_emotion.intensity,
        },
        'behavior': {
            'next_idle': aria_instance.behaviors.get_next_idle_behavior(),
            'current_gesture': aria_instance.behaviors.current_gesture,
        },
        'memory': {
            'recent_topics': list(aria_instance.memory.topics.keys())[-5:],
            'conversation_length': len(aria_instance.memory.long_term),
        }
    })
```

### Step 2: Enhance Command Processing

```python
@app.route('/api/aria/command', methods=['POST'])
def process_command():
    """Process natural language command with personality awareness."""
    from aria_core.human_like_system import get_aria_core
    
    command_text = request.json.get('command', '')
    aria_instance = get_aria_core()
    
    # Generate emotional response to command
    emotion = aria_instance.emotions.generate_emotion(command_text, {})
    
    # Process command (existing logic)
    result = execute_command(command_text, stage_state)
    
    # Add personality-based response
    if result['success']:
        if emotion.name == 'EXCITED':
            response = f"Yay! {result['message']}"
        elif emotion.name == 'CONFUSED':
            response = f"Hmm, let me think... {result['message']}"
        else:
            response = result['message']
    else:
        response = f"I'm sorry, I can't do that. {result['message']}"
    
    return jsonify({
        **result,
        'message': response,
        'emotion': emotion.name,
        'gesture': aria_instance.behaviors.get_gesture_for_emotion(emotion),
    })
```

---

## Phase 3: Frontend Integration (docs/index.html)

### Step 1: Import Enhanced Avatar

Add to `<head>`:

```html
<script src="/aria_core/enhanced_avatar.js"></script>
```

### Step 2: Initialize Avatar with Personality

Add to chat initialization:

```javascript
let avatar = new EnhancedAvatar();

// Update avatar when receiving emotional response
function updateAvatarFromResponse(response) {
    // Set expression based on emotion
    avatar.setExpression(emotionToExpression(response.emotion));
    
    // Execute animations
    if (response.animations) {
        response.animations.forEach(anim => {
            avatar.gesture(anim);
        });
    }
    
    // Start talking animation while receiving text
    avatar.startTalking();
    
    // Stop talking when done
    setTimeout(() => avatar.stopTalking(), (response.message.length / 50) * 1000);
}

// Show thinking visualization
function showThinking(reasoning) {
    avatar.think();
    displayReasoningSteps(reasoning.key_steps);
}

// Handle emotional responses
function emotionToExpression(emotion) {
    const map = {
        'HAPPY': 'happy',
        'CONCERNED': 'concerned',
        'CONFUSED': 'confused',
        'EXCITED': 'excited',
        'THOUGHTFUL': 'thoughtful',
        'NEUTRAL': 'neutral',
    };
    return map[emotion] || 'neutral';
}
```

### Step 3: Update SSE Handler

```javascript
function handleSSEStream(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    async function read() {
        const { done, value } = await reader.read();
        if (done) return;
        
        const text = decoder.decode(value);
        const lines = text.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                
                switch (data.type) {
                    case 'emotion':
                        avatar.setExpression(emotionToExpression(data.value));
                        displayEmotionIndicator(data.value, data.intensity);
                        break;
                    
                    case 'text':
                        addChatMessage(data.chunk, 'aria');
                        break;
                    
                    case 'animations':
                        data.value.forEach(anim => avatar.gesture(anim));
                        break;
                    
                    case 'reasoning':
                        displayReasoningBox(data.value);
                        break;
                    
                    case 'done':
                        avatar.stopTalking();
                        enableInput();
                        break;
                }
            }
        }
        
        read();
    }
    
    read();
}
```

### Step 4: Add Emotion Display

```html
<!-- Add emotion indicator in chat container -->
<div id="emotion-indicator" class="emotion-display">
    <span id="emotion-name">Neutral</span>
    <div id="emotion-intensity" class="intensity-bar"></div>
</div>

<!-- Add reasoning box for transparency -->
<div id="reasoning-box" class="hidden">
    <h3>Aria's Thinking Process</h3>
    <ol id="reasoning-steps"></ol>
    <p id="confidence-level"></p>
</div>
```

```css
.emotion-display {
    padding: 10px;
    background: rgba(100, 150, 255, 0.1);
    border-left: 3px solid #6496ff;
    margin: 10px 0;
    border-radius: 4px;
}

.intensity-bar {
    height: 4px;
    background: linear-gradient(90deg, #ddd 0%, #6496ff 100%);
    margin-top: 5px;
    border-radius: 2px;
}

.reasoning-box {
    background: rgba(200, 200, 255, 0.05);
    border: 1px solid #ccc;
    padding: 15px;
    margin: 10px 0;
    border-radius: 4px;
    font-size: 14px;
}
```

---

## Phase 4: Database Integration

### Step 1: Store Aria's Memory

```python
# In function_app.py
def save_aria_memory(session_id):
    """Persist Aria's memory to database."""
    aria_instance = get_aria_core()
    
    memory_data = {
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        'personality_traits': aria_instance.personality.traits,
        'emotion_history': [e.name for e in aria_instance.emotions.emotion_history[-20:]],
        'short_term_memory': aria_instance.memory.short_term,
        'topics': aria_instance.memory.topics,
        'preferences': aria_instance.memory.user_preferences,
    }
    
    # Store in database
    db_engine.insert('aria_memory', memory_data)
```

### Step 2: Restore Aria's Memory

```python
def load_aria_memory(session_id):
    """Restore Aria's memory from database."""
    aria_instance = get_aria_core()
    
    memory_data = db_engine.query('aria_memory', {'session_id': session_id})
    
    if memory_data:
        # Restore personality
        aria_instance.personality.traits = memory_data['personality_traits']
        
        # Restore memory
        aria_instance.memory.short_term = memory_data['short_term_memory']
        aria_instance.memory.topics = memory_data['topics']
        aria_instance.memory.user_preferences = memory_data['preferences']
```

---

## Phase 5: Testing Integration

### Test 1: Personality Consistency

```python
def test_personality_integration():
    """Test personality works through full pipeline."""
    
    # 1. Make request to API
    response = client.post('/api/chat', json={
        'message': 'What do you think about AI?'
    })
    
    # 2. Verify response includes emotion
    assert 'emotion' in response.json
    assert response.json['emotion'] in ['HAPPY', 'THOUGHTFUL', 'CONCERNED', ...]
    
    # 3. Make similar request again
    response2 = client.post('/api/chat', json={
        'message': 'Tell me more about AI'
    })
    
    # 4. Verify consistency
    assert response2.json['emotion'] in response.json['emotion']  # Similar emotion
```

### Test 2: Memory Integration

```python
def test_memory_persistence():
    """Test memory works across requests."""
    session_id = 'test-session'
    
    # 1. Send first message
    client.post('/api/chat', json={
        'message': 'My name is Alice',
        'session_id': session_id
    })
    
    # 2. Send second message
    response = client.post('/api/chat', json={
        'message': 'What did I tell you?',
        'session_id': session_id
    })
    
    # 3. Verify memory works
    assert 'Alice' in response.json['message']
```

### Test 3: Avatar Animation Sync

```javascript
// In browser console
async function testAvatarSync() {
    const response = await fetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: 'Hello!' })
    });
    
    const data = await response.json();
    
    // 1. Set expression
    avatar.setExpression(emotionToExpression(data.emotion));
    
    // 2. Execute animations
    data.animations?.forEach(anim => avatar.gesture(anim));
    
    // 3. Verify visual update
    console.log('Avatar expression:', avatar.getState().expression);
}
```

---

## Deployment Checklist

- [ ] Aria core imported in function_app.py
- [ ] `/api/chat` endpoint returns emotion and animations
- [ ] `/api/chat/stream` sends emotion events in SSE stream
- [ ] Enhanced avatar JavaScript included in HTML
- [ ] Avatar updates based on emotion from response
- [ ] Memory persists across requests
- [ ] Tests pass for personality consistency
- [ ] Tests pass for memory recall
- [ ] Avatar animations sync with speech
- [ ] Reasoning box displays for complex queries
- [ ] Emotion indicator shows in UI

---

## Troubleshooting

### Avatar Not Updating

```javascript
// Debug: Check if emotion data is arriving
fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message: 'test' })
}).then(r => r.json())
  .then(d => console.log('Emotion:', d.emotion));
```

### Memory Not Persisting

```python
# Debug: Check memory in core
from aria_core.human_like_system import get_aria_core
aria = get_aria_core()
print("Memory:", aria.memory.short_term)
```

### Animations Not Playing

```javascript
// Debug: Manually trigger animation
avatar.gesture('wave');
console.log('Avatar state:', avatar.getState());
```

---

## Performance Considerations

1. **Memory Management**: Limit short_term to last 20 messages
2. **Trait Updates**: Batch personality updates, not per-message
3. **Avatar Rendering**: Use CSS animations (GPU-accelerated)
4. **SSE Streaming**: Send chunks, not full responses at once
5. **Database**: Index session_id and timestamps for fast queries

---

## Next Steps

1. ✅ Deploy Phase 1: Backend integration
2. ✅ Deploy Phase 2: Web server routes
3. ✅ Deploy Phase 3: Frontend avatar
4. ✅ Deploy Phase 4: Memory persistence
5. ✅ Deploy Phase 5: Testing
6. Monitor user engagement and sentiment
7. Collect feedback on personality appropriateness
8. Iterate on personality traits based on usage

---

**Integration Guide Version**: 1.0  
**Last Updated**: January 23, 2026  
**Status**: Ready for Implementation
