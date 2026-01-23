# Aria Human-Like Character: Complete Working Example

*Practical implementation example integrating all systems*

## Overview

This example shows a complete, working implementation of Aria using:
- Personality engine for natural interactions
- Memory system for context awareness
- Enhanced avatar for visual feedback
- Voice personality for speech patterns
- Reasoning engine for transparency

## Complete Backend Implementation

### example_aria_service.py

```python
"""
Complete example of using Aria's human-like systems.
Run this to see personality, memory, emotion, and behavior in action.
"""

from datetime import datetime
from aria_core.human_like_system import (
    get_aria_core,
    EmotionState,
    PersonalityTrait
)
import json

class AriaExampleService:
    """Example service showing all Aria systems working together."""
    
    def __init__(self):
        self.aria = get_aria_core()
        self.conversation_id = "example_session"
    
    def simulate_conversation(self):
        """Simulate a complete conversation showing all features."""
        
        print("\n" + "="*60)
        print("ARIA HUMAN-LIKE CHARACTER - COMPLETE EXAMPLE")
        print("="*60 + "\n")
        
        # Scenario: New user learning about AI
        user_messages = [
            "Hello Aria! I'm new here.",
            "What can you do?",
            "Can you remember things about me?",
            "I'm interested in quantum computing.",
            "Tell me about quantum AI applications.",
            "That's interesting but I'm a bit confused.",
            "Can you explain it differently?",
        ]
        
        for i, message in enumerate(user_messages, 1):
            print(f"\n{'='*60}")
            print(f"TURN {i}: User Message")
            print(f"{'='*60}")
            self.process_user_message(message)
    
    def process_user_message(self, message):
        """Process a single user message through full pipeline."""
        
        print(f"\n📝 User: {message}\n")
        
        # Step 1: Add to memory
        self.aria.memory.add_turn(
            role="user",
            content=message,
            timestamp=datetime.now()
        )
        
        # Step 2: Analyze sentiment and generate emotion
        emotion = self.aria.emotions.generate_emotion(
            message,
            context=self.aria.memory.get_context_window()
        )
        print(f"💭 Aria's Emotion: {emotion.name} (intensity: {emotion.intensity:.2f})")
        
        # Step 3: Generate base response (simulated LLM)
        base_response = self.generate_response(message)
        
        # Step 4: Add personality touches
        personality_response = self.aria.voice.add_speech_patterns(
            base_response,
            traits=self.aria.personality.traits
        )
        
        # Step 5: Enhance with reasoning if complex
        if self.is_complex_topic(message):
            reasoning = self.aria.reasoning.generate_thinking_process(message)
            print(f"\n🧠 Aria's Thinking Process:")
            print(f"   Approach: {reasoning['approach']}")
            print(f"   Confidence: {reasoning['confidence']:.0%}")
            print(f"   Key Steps:")
            for step in reasoning['key_steps']:
                print(f"      • {step}")
        
        # Step 6: Get next behavior/gesture
        gesture = self.aria.behaviors.get_next_gesture(emotion)
        print(f"\n🎭 Gesture: {gesture}")
        
        # Step 7: Get voice parameters
        voice_params = self.aria.voice.get_params_for_emotion(emotion)
        print(f"\n🔊 Voice Parameters:")
        print(f"   Rate: {voice_params['rate']:.2f}x")
        print(f"   Pitch: {voice_params['pitch']:.2f}")
        print(f"   Warmth: {voice_params['warmth']:.0%}")
        
        # Step 8: Display response
        print(f"\n🤖 Aria: {personality_response}\n")
        
        # Step 9: Add response to memory
        self.aria.memory.add_turn(
            role="assistant",
            content=personality_response,
            emotion=emotion.name,
            timestamp=datetime.now()
        )
        
        # Step 10: Show personality drift
        print(f"\n📊 Aria's Current Personality State:")
        self.display_personality_state()
        
        # Step 11: Show memory state
        print(f"\n💾 Memory Status:")
        self.display_memory_state()
    
    def generate_response(self, user_message):
        """Generate base response (simulates LLM call)."""
        
        # Determine topic
        if "hello" in user_message.lower():
            return "Hello! It's great to meet you. I'm Aria, an AI assistant designed to be as human-like and personable as possible."
        elif "what can you do" in user_message.lower():
            return "I can chat with you, answer questions, remember our conversations, and express emotions based on what we discuss. I'm designed to be natural and engaging."
        elif "remember" in user_message.lower():
            return "Yes! I can remember what you tell me and use that context in our conversations. This helps me be more personable and relevant."
        elif "quantum" in user_message.lower() and "computing" in user_message.lower():
            return "Quantum computing uses quantum bits instead of regular bits. I'm particularly interested in how quantum ML can revolutionize AI applications."
        elif "quantum" in user_message.lower():
            if self.aria.reasoning.last_confidence < 0.6:
                return "Let me think about that more carefully... Quantum computing represents a fundamentally different approach to computation using quantum mechanics principles."
            return "Quantum AI applications include optimization problems, drug discovery simulation, and advanced machine learning models."
        elif "confused" in user_message.lower():
            return "I understand! Let me break it down more simply. The main idea is that quantum systems work differently from regular computers."
        else:
            return "That's an interesting question. Let me think about how best to explain that."
    
    def is_complex_topic(self, message):
        """Determine if topic requires visible thinking."""
        complex_keywords = ["quantum", "how", "why", "explain", "confused", "think"]
        return any(keyword in message.lower() for keyword in complex_keywords)
    
    def display_personality_state(self):
        """Show current personality traits."""
        traits = self.aria.personality.traits
        for trait, value in traits.items():
            bar = "█" * int(value * 10) + "░" * (10 - int(value * 10))
            print(f"   {trait:12} [{bar}] {value:.0%}")
    
    def display_memory_state(self):
        """Show current memory state."""
        print(f"   Short-term messages: {len(self.aria.memory.short_term)}")
        print(f"   Topics discussed: {list(self.aria.memory.topics.keys())}")
        print(f"   Dominant topic: {self.aria.memory.get_dominant_topic()}")
        if self.aria.memory.user_preferences:
            print(f"   Preferences learned: {len(self.aria.memory.user_preferences)}")
    
    def show_final_state(self):
        """Display final state after conversation."""
        print(f"\n{'='*60}")
        print("FINAL STATE - ARIA AFTER CONVERSATION")
        print(f"{'='*60}\n")
        
        print("Personality Evolution:")
        self.display_personality_state()
        
        print("\nLearned Information:")
        print(f"  - Total conversation turns: {len(self.aria.memory.long_term)}")
        print(f"  - Topics explored: {list(self.aria.memory.topics.keys())}")
        
        print("\nEmotional Journey:")
        emotions = [e.name for e in self.aria.emotions.emotion_history[-5:]]
        print(f"  - Last 5 emotions: {' → '.join(emotions)}")
        
        print("\nCurrent State:")
        print(f"  - Current emotion: {self.aria.emotions.current_emotion.name}")
        print(f"  - Current mood: {self.aria.behaviors.current_mood:.2f}")
        print(f"  - Confidence in responses: {self.aria.personality.traits['confidence']:.0%}")


def run_example():
    """Run the complete example."""
    service = AriaExampleService()
    service.simulate_conversation()
    service.show_final_state()


if __name__ == "__main__":
    run_example()
```

## Complete Frontend Implementation

### example_aria_chat.html

```html
<!DOCTYPE html>
<html>
<head>
    <title>Aria Human-Like Chat Example</title>
    <script src="/aria_core/enhanced_avatar.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            display: flex;
            height: 80vh;
            max-width: 1200px;
            width: 100%;
            overflow: hidden;
        }
        
        .avatar-panel {
            flex: 0 0 35%;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 30px;
            border-right: 1px solid #ddd;
        }
        
        #avatar-container {
            width: 100%;
            height: 300px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .avatar {
            width: 200px;
            height: 200px;
        }
        
        .avatar-info {
            margin-top: 30px;
            text-align: center;
            width: 100%;
        }
        
        .emotion-display {
            background: rgba(100, 150, 255, 0.1);
            border-left: 4px solid #6496ff;
            padding: 15px;
            border-radius: 4px;
            margin-top: 15px;
        }
        
        .emotion-display h4 {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .emotion-name {
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .intensity-bar {
            background: #ddd;
            height: 6px;
            border-radius: 3px;
            overflow: hidden;
        }
        
        .intensity-fill {
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            transition: width 0.3s ease;
        }
        
        .chat-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            background: #667eea;
            color: white;
            padding: 20px;
            font-size: 18px;
            font-weight: bold;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .message {
            display: flex;
            margin-bottom: 10px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message.aria {
            justify-content: flex-start;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 8px;
            line-height: 1.4;
        }
        
        .message.user .message-content {
            background: #667eea;
            color: white;
        }
        
        .message.aria .message-content {
            background: #f0f0f0;
            color: #333;
        }
        
        .reasoning-box {
            background: rgba(200, 200, 255, 0.05);
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 12px;
            margin: 10px 0;
            font-size: 13px;
            color: #666;
        }
        
        .reasoning-box h5 {
            font-size: 12px;
            text-transform: uppercase;
            color: #667eea;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .reasoning-box ol {
            margin-left: 20px;
            margin-top: 8px;
        }
        
        .reasoning-box li {
            margin-bottom: 4px;
        }
        
        .chat-input-area {
            padding: 20px;
            border-top: 1px solid #ddd;
            display: flex;
            gap: 10px;
        }
        
        #message-input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            font-family: inherit;
        }
        
        #message-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        #send-button {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.2s;
        }
        
        #send-button:hover {
            background: #764ba2;
        }
        
        #send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .thinking-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #999;
            font-size: 13px;
        }
        
        .dot {
            width: 4px;
            height: 4px;
            background: #999;
            border-radius: 50%;
            animation: bounce 1.4s infinite;
        }
        
        .dot:nth-child(1) {
            animation-delay: 0s;
        }
        .dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        .dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes bounce {
            0%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-8px);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Avatar Panel -->
        <div class="avatar-panel">
            <div id="avatar-container">
                <div class="avatar" id="aria-avatar"></div>
            </div>
            <div class="avatar-info">
                <div class="emotion-display">
                    <h4>Current Emotion</h4>
                    <div class="emotion-name" id="emotion-name">Neutral</div>
                    <div class="intensity-bar">
                        <div class="intensity-fill" id="intensity-fill" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Chat Panel -->
        <div class="chat-panel">
            <div class="chat-header">Aria - Human-Like AI Character</div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="message aria">
                    <div class="message-content">
                        Hello! I'm Aria. I can chat, remember our conversation, and express emotions. What would you like to talk about?
                    </div>
                </div>
            </div>
            
            <div class="chat-input-area">
                <input 
                    type="text" 
                    id="message-input" 
                    placeholder="Type your message..."
                    autocomplete="off"
                >
                <button id="send-button">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize avatar
        const avatar = new EnhancedAvatar();
        const avatarContainer = document.getElementById('avatar-container');
        avatarContainer.innerHTML = '<div class="avatar" id="aria-avatar"></div>';
        
        // Avatar expression mapping
        const emotionToExpression = {
            'HAPPY': 'happy',
            'EXCITED': 'excited',
            'SAD': 'sad',
            'CONCERNED': 'concerned',
            'CONFUSED': 'confused',
            'SURPRISED': 'surprised',
            'THOUGHTFUL': 'thinking',
            'ANGRY': 'angry',
            'NEUTRAL': 'neutral'
        };
        
        // DOM elements
        const messagesContainer = document.getElementById('chat-messages');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const emotionName = document.getElementById('emotion-name');
        const intensityFill = document.getElementById('intensity-fill');
        
        let isProcessing = false;
        
        // Send message
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message || isProcessing) return;
            
            // Add user message to UI
            addMessageToChat(message, 'user');
            messageInput.value = '';
            sendButton.disabled = true;
            isProcessing = true;
            
            try {
                // Show thinking indicator
                const thinkingEl = document.createElement('div');
                thinkingEl.className = 'thinking-indicator message aria';
                thinkingEl.innerHTML = '<span>Aria is thinking</span><span class="dot"></span><span class="dot"></span><span class="dot"></span>';
                messagesContainer.appendChild(thinkingEl);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                // Send to API
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });
                
                const data = await response.json();
                
                // Remove thinking indicator
                thinkingEl.remove();
                
                // Update emotion display
                updateEmotionDisplay(data.emotion, data.intensity);
                
                // Update avatar
                const expression = emotionToExpression[data.emotion] || 'neutral';
                avatar.setExpression(expression);
                
                // Execute animations
                if (data.animations) {
                    data.animations.forEach((anim, idx) => {
                        setTimeout(() => avatar.gesture(anim), idx * 300);
                    });
                }
                
                // Start talking animation
                avatar.startTalking();
                
                // Add message with reasoning
                addMessageToChat(data.message, 'aria');
                
                if (data.reasoning) {
                    addReasoningBox(data.reasoning);
                }
                
                // Stop talking
                setTimeout(() => avatar.stopTalking(), (data.message.length / 50) * 1000);
                
            } catch (error) {
                console.error('Error:', error);
                addMessageToChat('Sorry, I encountered an error.', 'aria');
            } finally {
                sendButton.disabled = false;
                isProcessing = false;
                messageInput.focus();
            }
        }
        
        function addMessageToChat(content, role) {
            const messageEl = document.createElement('div');
            messageEl.className = `message ${role}`;
            
            const contentEl = document.createElement('div');
            contentEl.className = 'message-content';
            contentEl.textContent = content;
            
            messageEl.appendChild(contentEl);
            messagesContainer.appendChild(messageEl);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function addReasoningBox(reasoning) {
            const reasoningEl = document.createElement('div');
            reasoningEl.className = 'message aria';
            
            const boxEl = document.createElement('div');
            boxEl.className = 'reasoning-box message-content';
            
            let html = '<h5>🧠 Thinking Process</h5>';
            html += `<p>Approach: ${reasoning.approach}</p>`;
            html += `<p>Confidence: ${Math.round(reasoning.confidence * 100)}%</p>`;
            html += '<ol>';
            reasoning.key_steps.forEach(step => {
                html += `<li>${step}</li>`;
            });
            html += '</ol>';
            
            boxEl.innerHTML = html;
            reasoningEl.appendChild(boxEl);
            messagesContainer.appendChild(reasoningEl);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function updateEmotionDisplay(emotion, intensity) {
            emotionName.textContent = emotion || 'Neutral';
            intensityFill.style.width = (intensity || 0) * 100 + '%';
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !isProcessing) sendMessage();
        });
        
        // Initial avatar setup
        avatar.setExpression('happy');
        updateEmotionDisplay('HAPPY', 0.7);
    </script>
</body>
</html>
```

## Running the Example

### Backend (Python)

```bash
# 1. Navigate to workspace
cd /workspaces/AI

# 2. Run the example service
python docs/example_aria_service.py

# Output shows complete conversation with:
# - Emotion generation
# - Personality adjustments
# - Memory formation
# - Voice parameter selection
# - Behavior planning
```

### Frontend (HTML)

```bash
# 1. Start the function app
func host start

# 2. Open the HTML in browser
# Navigate to: file:///workspaces/AI/docs/example_aria_chat.html
# Or deploy to a web server

# Features:
# - Animated avatar responds to emotions
# - Messages stream with thinking indicators
# - Reasoning displayed for complex questions
# - Real-time personality visualization
```

## Testing the Integration

```python
# test_aria_example.py
import pytest
from datetime import datetime
from aria_core.human_like_system import get_aria_core, EmotionState

def test_complete_conversation():
    """Test full conversation pipeline."""
    aria = get_aria_core()
    
    # Simulate conversation
    aria.memory.add_turn("user", "Hello Aria!")
    emotion = aria.emotions.generate_emotion("Hello Aria!", {})
    assert emotion is not None
    
    aria.memory.add_turn("assistant", "Hello! Nice to meet you.", emotion.name)
    context = aria.memory.get_context_window()
    assert len(context) >= 2
    
    # Verify personality consistency
    traits1 = aria.personality.traits.copy()
    aria.memory.add_turn("user", "Tell me about AI")
    traits2 = aria.personality.traits.copy()
    
    # Traits should evolve slightly, not dramatically change
    for trait in traits1:
        diff = abs(traits1[trait] - traits2[trait])
        assert diff < 0.2, f"Trait {trait} changed too much"


def test_emotion_generation():
    """Test emotion generation from context."""
    aria = get_aria_core()
    
    test_cases = [
        ("I'm sad", ["CONCERNED", "SAD"]),
        ("That's amazing!", ["HAPPY", "EXCITED"]),
        ("I'm confused", ["CONFUSED", "THOUGHTFUL"]),
    ]
    
    for message, expected_emotions in test_cases:
        emotion = aria.emotions.generate_emotion(message, {})
        assert emotion.name in expected_emotions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

## Key Features Demonstrated

✅ **Personality System**
- 6 adjustable traits
- Consistent character personality
- Dynamic personality drift

✅ **Memory System**
- Conversation history tracking
- Topic detection
- User preference learning

✅ **Emotion Engine**
- Context-aware emotions
- Emotion intensity scaling
- Emotional consistency

✅ **Avatar Visualization**
- Expression mapping
- Gesture animations
- Eye tracking
- Talking animations

✅ **Voice Integration**
- Speech parameter adjustment
- Speech pattern injection
- Emotion-based voice tuning

✅ **Reasoning System**
- Visible thinking processes
- Confidence scoring
- Uncertainty acknowledgment

---

**Example Version**: 1.0  
**Last Updated**: January 23, 2026  
**Status**: Complete & Ready to Run
