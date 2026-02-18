# Aria Enhancement Systems: Quick Reference

*Fast lookup for personality, memory, emotion, and animation systems*

## Core Objects

```python
# Get Aria instance
from aria_core.human_like_system import get_aria_core
aria = get_aria_core()

# Main systems
aria.personality      # PersonalityEngine - traits, emotional responses
aria.memory          # MemorySystem - conversations, preferences, topics
aria.emotions        # EmotionEngine - current emotion state
aria.reasoning       # ReasoningEngine - thinking processes
aria.behaviors       # BehaviorGenerator - animations, gestures
aria.voice           # VoicePersonality - speech patterns, synthesis
```

## Personality Traits

```python
traits = {
    "empathy": 0.0-1.0,      # Response to emotional content
    "curiosity": 0.0-1.0,    # Interest in learning
    "playfulness": 0.0-1.0,  # Likelihood of humor
    "formality": 0.0-1.0,    # Professional vs casual (0=casual, 1=formal)
    "verbosity": 0.0-1.0,    # Length of responses (0=brief, 1=verbose)
    "confidence": 0.0-1.0,   # Certainty expression (0=uncertain, 1=confident)
}

# Adjust traits
aria.personality.adjust_trait("empathy", +0.1)  # Increase by 10%
aria.personality.adjust_trait("playfulness", -0.05)  # Decrease by 5%

# Get current traits
current = aria.personality.traits
empathy_level = current["empathy"]
```

## Emotions

```python
from aria_core.human_like_system import EmotionState

# Available emotions
emotions = [
    "NEUTRAL",
    "HAPPY",
    "SAD",
    "SURPRISED",
    "CONFUSED",
    "CONCERNED",
    "EXCITED",
    "THOUGHTFUL",
    "ANGRY"
]

# Set emotion manually
aria.emotions.set_emotion(EmotionState.EXCITED)

# Get current emotion
current = aria.emotions.current_emotion
print(current.name)        # "EXCITED"
print(current.intensity)   # 0.0-1.0

# Generate emotion from context
emotion = aria.emotions.generate_emotion(user_message, context)
```

## Memory

```python
# Add conversation turn
aria.memory.add_turn(
    role="user",           # or "assistant"
    content="Hello Aria",
    timestamp=datetime.now()
)

# Get recent context
context = aria.memory.get_context_window(num_turns=5)

# Topics and preferences
aria.memory.topics  # {"ai": {"count": 3, "sentiment": 0.8}, ...}
aria.memory.user_preferences  # [{"preference": "...", "value": "..."}, ...]

# Add preference
aria.memory.add_preference("coffee", "likes cold brew")

# Get dominant topic
topic = aria.memory.get_dominant_topic()
```

## Animations & Gestures

```javascript
// Create avatar
let avatar = new EnhancedAvatar();

// Set expression (affects face appearance)
avatar.setExpression("happy");      // happy, sad, surprised, confused, etc.
avatar.setExpression("thinking");
avatar.setExpression("concerned");

// Perform gesture (animation)
avatar.gesture("wave");
avatar.gesture("raise_arms");
avatar.gesture("clap");
avatar.gesture("jump");

// Eye tracking
avatar.trackGaze({ x: 100, y: 200 });  // Track to coordinates

// Talking animations
avatar.startTalking();
avatar.stopTalking();

// Blink
avatar.blink();

// Thinking state
avatar.think();

// React to emotion
avatar.react("surprised");

// Get current state
state = avatar.getState();
// { expression: "happy", isBlinking: false, isTalking: true, ... }

// Update from emotion response
avatar.updateFromEmotionalResponse({
    primary: "HAPPY",
    intensity: 0.8,
    secondary: "EXCITED"
});
```

## Voice & Speech

```python
# Get voice parameters for emotion
params = aria.voice.get_params_for_emotion(current_emotion)
# Returns: { rate: 1.1, pitch: 1.05, energy: 0.9, warmth: 0.8 }

# Add speech patterns to text
text = "This is my response"
enhanced = aria.voice.add_speech_patterns(text, personality_traits)
# May add: "Um, well, this is my response!"

# Adjust speech for personality
voice_config = {
    "rate": 1.0,        # 0.5 (slow) to 2.0 (fast)
    "pitch": 1.0,       # 0.5 (low) to 2.0 (high)
    "warmth": 0.7,      # 0.0-1.0 (cold to warm)
    "energy": 0.8,      # 0.0-1.0 (calm to energetic)
}
```

## Reasoning & Thinking

```python
# Generate thinking process for complex queries
thinking = aria.reasoning.generate_thinking_process(question)
# Returns: {
#     "approach": "causal_analysis",
#     "key_steps": [...],
#     "confidence": 0.72,
#     "uncertainties": [...],
# }

# Get reasoning explanation
aria.reasoning.generate_explanation_for_response(response_text)
```

## Common Workflows

### Full Response with Personality

```python
# 1. Get context
context = aria.memory.get_context_window()

# 2. Generate emotion
emotion = aria.emotions.generate_emotion(user_message, context)

# 3. Generate base response
response_text = generate_from_llm(user_message)

# 4. Enhance with personality
response_text = aria.voice.add_speech_patterns(response_text)

# 5. Add memory
aria.memory.add_turn("assistant", response_text, emotion.name)

# 6. Plan animations
animations = aria.behaviors.get_gesture_for_emotion(emotion)

# 7. Get voice params
voice_params = aria.voice.get_params_for_emotion(emotion)

# Return all together
return {
    "message": response_text,
    "emotion": emotion.name,
    "animations": animations,
    "voice_params": voice_params,
}
```

### Avatar Visual Update

```javascript
// Receive response from API
const response = await fetch('/api/chat', {...}).then(r => r.json());

// Update avatar
avatar.setExpression(emotionToExpression(response.emotion));

// Play animations
response.animations?.forEach(anim => avatar.gesture(anim));

// Start talking (sync to speech)
avatar.startTalking();
displayMessage(response.message);
avatar.stopTalking();
```

### Memory-Based Context Awareness

```python
# Check what we know about user
recent_context = aria.memory.get_context_window(5)
dominant_topic = aria.memory.get_dominant_topic()
user_prefs = aria.memory.user_preferences

# If we've talked about this before
if dominant_topic == "coffee":
    response = f"Since you like {prefs['coffee_preference']}, ..."
```

## Testing Snippets

```python
# Test: Personality consistency
responses = [aria.generate_response("test") for _ in range(5)]
assert all(r['emotion'] in ['HAPPY', 'THOUGHTFUL'] for r in responses)

# Test: Memory recall
aria.memory.add_turn("user", "My name is Alice")
context = aria.memory.get_context_window()
assert "Alice" in context[-1]['content']

# Test: Emotion generation
emotion = aria.emotions.generate_emotion("I'm sad!", {})
assert emotion.name in ['CONCERNED', 'SAD', 'SYMPATHETIC']
```

## API Endpoints

```bash
# Get personality state
curl http://localhost:7071/api/aria/personality

# Chat with personality
curl -X POST http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "user1"}'

# Stream response with emotions
curl -X POST http://localhost:7071/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## Emotion to Expression Mapping

```javascript
const emotionMap = {
    "HAPPY": "happy",
    "EXCITED": "excited",
    "SAD": "sad",
    "CONCERNED": "concerned",
    "CONFUSED": "confused",
    "SURPRISED": "surprised",
    "THOUGHTFUL": "thinking",
    "ANGRY": "angry",
    "NEUTRAL": "neutral"
};

function emotionToExpression(emotion) {
    return emotionMap[emotion] || "neutral";
}
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Avatar not updating | Check `/api/aria/personality` returns valid emotion |
| Memory not growing | Verify `add_turn()` called after each message |
| Voice sounds robotic | Increase `warmth` in voice params |
| Emotions too random | Check personality traits, reduce randomness |
| Animations not syncing | Ensure speech duration matches animation timing |

## Files Reference

```
aria_core/
├── human_like_system.py      # All personality/memory/reasoning classes
└── enhanced_avatar.js        # All avatar/gesture/animation code

docs/
├── HUMAN_LIKE_AI_CHARACTER_GUIDE.md   # Comprehensive guide
├── ARIA_INTEGRATION_GUIDE.md           # Step-by-step integration
└── ARIA_QUICK_REFERENCE.md             # This file

function_app.py                # Chat endpoints (add emotion responses)
aria_web/
├── server.py                 # Web server endpoints
└── index.html               # UI (integrate avatar)
```

## Next Steps

1. Import `get_aria_core()` in your function_app.py
2. Integrate personality response in `/api/chat`
3. Add `enhanced_avatar.js` to HTML
4. Update avatar on emotional responses
5. Store/restore memory per session
6. Test personality consistency

---

**Quick Reference Version**: 1.0  
**Last Updated**: January 23, 2026
