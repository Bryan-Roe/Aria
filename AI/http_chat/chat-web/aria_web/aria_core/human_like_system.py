"""
Aria Human-Like Character System
=================================

This module provides advanced personality, memory, reasoning, and behavior
systems to make Aria feel more human-like and interactive.

Components:
  • PersonalityEngine - Dynamic personality traits and emotional states
  • MemorySystem - Short/long-term conversation memory
  • ReasoningEngine - Meta-cognitive abilities and explanations
  • BehaviorGenerator - Natural idle animations and expressions
  • VoicePersonality - Speech patterns and synthesis prep
"""

import json
import random
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math


class EmotionState(Enum):
    """Core emotional states Aria can exhibit."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    CURIOUS = "curious"
    THOUGHTFUL = "thoughtful"
    EXCITED = "excited"
    CONFUSED = "confused"
    CONCERNED = "concerned"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"


class PersonalityTrait(Enum):
    """Personality dimensions affecting responses."""
    EMPATHETIC = "empathetic"  # 0-1: How much Aria relates to emotions
    CURIOUS = "curious"        # 0-1: Interest in learning new things
    PLAYFUL = "playful"        # 0-1: Tendency to joke/play
    FORMAL = "formal"          # 0-1: Professional vs casual language
    VERBOSE = "verbose"        # 0-1: Long explanations vs brief
    CONFIDENT = "confident"    # 0-1: Certainty in responses


@dataclass
class Gesture:
    """Represents a gesture or animation."""
    name: str
    duration_ms: int
    intensity: float  # 0-1
    timestamp: float = 0.0
    
    def to_dict(self):
        return asdict(self)


@dataclass
class EmotionalResponse:
    """Structured emotional response for Aria."""
    primary_emotion: EmotionState
    secondary_emotion: Optional[EmotionState]
    intensity: float  # 0-1
    gestures: List[Gesture]
    expression: str  # "smile", "nod", "surprised", etc.
    eye_contact: bool = True
    
    def to_dict(self):
        return {
            "primary_emotion": self.primary_emotion.value,
            "secondary_emotion": self.secondary_emotion.value if self.secondary_emotion else None,
            "intensity": self.intensity,
            "gestures": [g.to_dict() for g in self.gestures],
            "expression": self.expression,
            "eye_contact": self.eye_contact,
        }


@dataclass
class ConversationTurn:
    """Single turn in conversation memory."""
    user_message: str
    aria_response: str
    timestamp: float
    emotion: EmotionState
    topic: str
    user_sentiment: str  # "positive", "negative", "neutral", "question"


class PersonalityEngine:
    """Manages Aria's dynamic personality traits and emotional states."""
    
    def __init__(self):
        """Initialize with balanced personality."""
        self.traits = {
            PersonalityTrait.EMPATHETIC: 0.8,
            PersonalityTrait.CURIOUS: 0.75,
            PersonalityTrait.PLAYFUL: 0.6,
            PersonalityTrait.FORMAL: 0.4,
            PersonalityTrait.VERBOSE: 0.65,
            PersonalityTrait.CONFIDENT: 0.7,
        }
        
        self.emotional_state = EmotionState.NEUTRAL
        self.emotional_intensity = 0.5
        self.mood_drift = 0.0  # -1 to 1, shifts based on conversation
        self.energy_level = 0.7  # Affects enthusiasm and response speed
        
        # Emotional memory (affects future emotions)
        self.recent_emotions: List[Tuple[EmotionState, float]] = []
        self.max_emotional_memory = 10
    
    def adjust_trait(self, trait: PersonalityTrait, delta: float):
        """Adjust a personality trait (normalize to 0-1)."""
        self.traits[trait] = max(0.0, min(1.0, self.traits[trait] + delta))
    
    def set_emotion(self, emotion: EmotionState, intensity: float = 0.7):
        """Set current emotional state."""
        self.emotional_state = emotion
        self.emotional_intensity = max(0.0, min(1.0, intensity))
        
        # Track emotional history for mood
        self.recent_emotions.append((emotion, intensity))
        if len(self.recent_emotions) > self.max_emotional_memory:
            self.recent_emotions.pop(0)
        
        # Mood shifts based on dominant recent emotions
        self._update_mood()
    
    def _update_mood(self):
        """Calculate mood from recent emotional states."""
        if not self.recent_emotions:
            return
        
        # Positive emotions boost mood, negative decrease it
        positive_emotions = {
            EmotionState.HAPPY, EmotionState.EXCITED, 
            EmotionState.CONFIDENT, EmotionState.CURIOUS
        }
        
        mood_shift = sum(
            intensity if emotion in positive_emotions else -intensity
            for emotion, intensity in self.recent_emotions
        ) / len(self.recent_emotions)
        
        # Gradually shift mood (not too fast)
        self.mood_drift = max(-1.0, min(1.0, self.mood_drift + mood_shift * 0.1))
    
    def get_emotional_response(self, user_input: str, user_sentiment: str) -> EmotionalResponse:
        """Generate an emotional response to user input."""
        
        # Determine primary emotion based on context and personality
        if "help" in user_input.lower() and self.traits[PersonalityTrait.EMPATHETIC] > 0.7:
            primary = EmotionState.CONCERNED
        elif "?" in user_input and self.traits[PersonalityTrait.CURIOUS] > 0.7:
            primary = EmotionState.CURIOUS
        elif user_sentiment == "positive" or user_sentiment == "question":
            primary = EmotionState.HAPPY if self.mood_drift > 0 else EmotionState.NEUTRAL
        elif user_sentiment == "negative":
            primary = EmotionState.CONCERNED if self.traits[PersonalityTrait.EMPATHETIC] > 0.6 else EmotionState.NEUTRAL
        else:
            primary = EmotionState.THOUGHTFUL
        
        # Determine secondary emotion
        secondary = None
        if random.random() < 0.3:  # 30% chance of secondary emotion
            emotions = [e for e in EmotionState if e != primary]
            secondary = random.choice(emotions)
        
        # Generate gestures based on emotion and personality
        gestures = self._generate_gestures(primary, secondary)
        
        # Determine expression
        expression = self._get_expression(primary)
        
        # Eye contact more likely when engaged
        eye_contact = random.random() < (0.8 if primary != EmotionState.CONFUSED else 0.4)
        
        response = EmotionalResponse(
            primary_emotion=primary,
            secondary_emotion=secondary,
            intensity=self.emotional_intensity,
            gestures=gestures,
            expression=expression,
            eye_contact=eye_contact,
        )
        
        self.set_emotion(primary, self.emotional_intensity)
        return response
    
    def _generate_gestures(self, primary: EmotionState, secondary: Optional[EmotionState]) -> List[Gesture]:
        """Generate gestures matching emotional state."""
        gesture_map = {
            EmotionState.HAPPY: ["smile", "nod", "thumbs_up"],
            EmotionState.CURIOUS: ["head_tilt", "lean_forward"],
            EmotionState.EXCITED: ["jump", "raise_arms", "spin"],
            EmotionState.THOUGHTFUL: ["chin_rest", "look_away"],
            EmotionState.CONFUSED: ["head_shake", "shrug"],
            EmotionState.CONCERNED: ["frown", "hands_together"],
            EmotionState.CONFIDENT: ["stand_tall", "nod"],
            EmotionState.UNCERTAIN: ["fidget", "look_down"],
            EmotionState.NEUTRAL: ["blink"],
        }
        
        gestures = []
        base_gestures = gesture_map.get(primary, ["nod"])
        
        # Primary gesture
        if base_gestures:
            gesture_name = random.choice(base_gestures)
            gestures.append(Gesture(
                name=gesture_name,
                duration_ms=500 + random.randint(0, 1000),
                intensity=0.6 + random.random() * 0.4,
            ))
        
        # Secondary gesture if secondary emotion present
        if secondary:
            sec_gestures = gesture_map.get(secondary, ["nod"])
            if sec_gestures:
                gesture_name = random.choice(sec_gestures)
                gestures.append(Gesture(
                    name=gesture_name,
                    duration_ms=300 + random.randint(0, 500),
                    intensity=0.3 + random.random() * 0.3,
                ))
        
        return gestures
    
    def _get_expression(self, emotion: EmotionState) -> str:
        """Map emotion to facial expression."""
        expressions = {
            EmotionState.HAPPY: "smile",
            EmotionState.CURIOUS: "thinking_eyes",
            EmotionState.EXCITED: "wide_eyes",
            EmotionState.THOUGHTFUL: "contemplative",
            EmotionState.CONFUSED: "confused",
            EmotionState.CONCERNED: "worried",
            EmotionState.CONFIDENT: "assured",
            EmotionState.UNCERTAIN: "unsure",
            EmotionState.NEUTRAL: "neutral",
        }
        return expressions.get(emotion, "neutral")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize personality state."""
        return {
            "traits": {t.value: v for t, v in self.traits.items()},
            "emotional_state": self.emotional_state.value,
            "emotional_intensity": self.emotional_intensity,
            "mood_drift": self.mood_drift,
            "energy_level": self.energy_level,
        }


class MemorySystem:
    """Manages Aria's conversation memory for context-aware responses."""
    
    def __init__(self, max_short_term: int = 10, max_long_term: int = 100):
        """Initialize memory system."""
        self.short_term: List[ConversationTurn] = []
        self.long_term: List[ConversationTurn] = []
        self.max_short_term = max_short_term
        self.max_long_term = max_long_term
        
        # Topic tracking
        self.active_topics: Dict[str, int] = {}  # topic -> recency score
        self.user_preferences: Dict[str, str] = {}  # key -> value
        self.mentioned_facts: Dict[str, str] = {}  # fact -> context
    
    def add_turn(self, user_msg: str, aria_response: str, emotion: EmotionState, 
                 topic: str = "general", user_sentiment: str = "neutral"):
        """Record a conversation turn."""
        turn = ConversationTurn(
            user_message=user_msg,
            aria_response=aria_response,
            timestamp=time.time(),
            emotion=emotion,
            topic=topic,
            user_sentiment=user_sentiment,
        )
        
        # Add to short-term
        self.short_term.append(turn)
        if len(self.short_term) > self.max_short_term:
            # Move oldest to long-term
            old_turn = self.short_term.pop(0)
            self.long_term.append(old_turn)
            if len(self.long_term) > self.max_long_term:
                self.long_term.pop(0)
        
        # Update topic tracking
        self.active_topics[topic] = self.active_topics.get(topic, 0) + 1
        # Decay other topics
        for t in list(self.active_topics.keys()):
            if t != topic:
                self.active_topics[t] *= 0.95
    
    def get_context_window(self, num_turns: int = 5) -> List[ConversationTurn]:
        """Get recent conversation context."""
        return self.short_term[-num_turns:] if self.short_term else []
    
    def get_relevant_memory(self, query: str, num_results: int = 3) -> List[ConversationTurn]:
        """Find relevant past conversations (simple keyword matching)."""
        query_words = set(query.lower().split())
        scored = []
        
        for turn in self.short_term + self.long_term:
            msg_words = set(turn.user_message.lower().split())
            response_words = set(turn.aria_response.lower().split())
            
            # Score based on word overlap
            user_overlap = len(query_words & msg_words)
            response_overlap = len(query_words & response_words)
            score = user_overlap + response_overlap * 0.5
            
            if score > 0:
                scored.append((score, turn))
        
        # Return top results
        scored.sort(reverse=True)
        return [turn for _, turn in scored[:num_results]]
    
    def get_dominant_topic(self) -> Optional[str]:
        """Get the most discussed topic."""
        if not self.active_topics:
            return None
        return max(self.active_topics, key=self.active_topics.get)
    
    def set_preference(self, key: str, value: str):
        """Record a user preference learned from conversation."""
        self.user_preferences[key] = value
    
    def get_preference(self, key: str) -> Optional[str]:
        """Retrieve a learned user preference."""
        return self.user_preferences.get(key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory state."""
        return {
            "short_term_size": len(self.short_term),
            "long_term_size": len(self.long_term),
            "active_topics": dict(self.active_topics),
            "user_preferences": dict(self.user_preferences),
            "dominant_topic": self.get_dominant_topic(),
        }


class ReasoningEngine:
    """Adds meta-cognitive abilities and reasoning explanations."""
    
    def __init__(self):
        """Initialize reasoning engine."""
        self.reasoning_depth = 0.5  # 0-1: How deep to reason
        self.explanation_style = "accessible"  # "simple", "accessible", "technical"
    
    def generate_thinking_process(self, question: str, confidence: float = 0.7) -> Dict[str, Any]:
        """Generate a visible thinking process."""
        return {
            "question": question,
            "approach": self._select_approach(question),
            "key_considerations": self._identify_considerations(question),
            "confidence": confidence,
            "reasoning_steps": self._generate_steps(question),
            "uncertainty_factors": self._identify_uncertainties(question),
        }
    
    def _select_approach(self, question: str) -> str:
        """Determine reasoning approach."""
        if "why" in question.lower():
            return "causal_analysis"
        elif "how" in question.lower():
            return "process_breakdown"
        elif "what" in question.lower():
            return "definition_exploration"
        elif "compare" in question.lower():
            return "comparative_analysis"
        else:
            return "general_reasoning"
    
    def _identify_considerations(self, question: str) -> List[str]:
        """Identify key things to consider."""
        considerations = []
        
        # Rule-based heuristics
        if any(word in question.lower() for word in ["should", "moral", "ethical"]):
            considerations.extend(["ethical implications", "consequences"])
        if any(word in question.lower() for word in ["how", "improve", "solve"]):
            considerations.extend(["constraints", "resources needed"])
        if any(word in question.lower() for word in ["why", "cause", "reason"]):
            considerations.extend(["root causes", "contributing factors"])
        
        return considerations or ["relevance", "accuracy", "context"]
    
    def _generate_steps(self, question: str) -> List[str]:
        """Generate reasoning steps."""
        steps = [
            "Break down the question",
            "Identify key information",
            "Consider different perspectives",
            "Draw conclusions",
        ]
        
        # Customize based on question type
        if "compare" in question.lower():
            steps = [
                "Identify comparison criteria",
                "Analyze similarities",
                "Analyze differences",
                "Draw conclusions",
            ]
        
        return steps
    
    def _identify_uncertainties(self, question: str) -> List[str]:
        """Identify areas of uncertainty."""
        return [
            "Incomplete information",
            "Changing contexts",
            "Individual variations",
        ]
    
    def generate_explanation(self, concept: str, audience: str = "general") -> str:
        """Generate an explanation at appropriate level."""
        explanations = {
            "simple": f"I see you're asking about {concept}. Think of it like...",
            "accessible": f"Let me break down {concept} into understandable parts.",
            "technical": f"Regarding {concept}, we should consider the mechanisms involved.",
        }
        return explanations.get(audience, explanations["accessible"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize reasoning state."""
        return {
            "reasoning_depth": self.reasoning_depth,
            "explanation_style": self.explanation_style,
        }


class BehaviorGenerator:
    """Generates natural idle behaviors and animations."""
    
    def __init__(self):
        """Initialize behavior generator."""
        self.idle_behaviors = [
            {"name": "breathe", "duration": 2000, "intensity": 0.3},
            {"name": "blink", "duration": 200, "intensity": 0.8},
            {"name": "look_around", "duration": 1500, "intensity": 0.5},
            {"name": "subtle_sway", "duration": 3000, "intensity": 0.2},
            {"name": "fidget", "duration": 1000, "intensity": 0.4},
            {"name": "stretch", "duration": 1500, "intensity": 0.6},
        ]
        
        self.last_behavior_time = 0
        self.behavior_interval = 3  # seconds between behaviors
    
    def get_next_idle_behavior(self) -> Optional[Dict[str, Any]]:
        """Get the next idle behavior if interval elapsed."""
        current_time = time.time()
        
        if current_time - self.last_behavior_time < self.behavior_interval:
            return None
        
        self.last_behavior_time = current_time
        behavior = random.choice(self.idle_behaviors)
        
        # Add randomness to duration
        behavior = dict(behavior)
        behavior["duration"] = int(behavior["duration"] * (0.7 + random.random() * 0.6))
        
        return behavior
    
    def get_speech_animation(self, text: str) -> Dict[str, Any]:
        """Generate speech-synchronized animation."""
        # Estimate speech duration (rough: ~150 WPM = 2.5 chars per ms)
        char_count = len(text)
        duration_ms = int(char_count / 2.5)
        
        return {
            "type": "talking",
            "duration": duration_ms,
            "mouth_movement": True,
            "head_nods": max(1, duration_ms // 1000),  # One nod per second
            "eyebrow_raises": random.randint(0, 2),
            "intensity": 0.7,
        }
    
    def generate_reaction(self, reaction_type: str) -> Dict[str, Any]:
        """Generate quick reaction animations."""
        reactions = {
            "surprised": {
                "gestures": ["jump", "raise_hands"],
                "expressions": ["wide_eyes", "open_mouth"],
                "duration": 800,
            },
            "confused": {
                "gestures": ["head_tilt", "shrug"],
                "expressions": ["confused"],
                "duration": 1200,
            },
            "excited": {
                "gestures": ["jump", "spin", "clap"],
                "expressions": ["smile", "wide_eyes"],
                "duration": 1500,
            },
            "thinking": {
                "gestures": ["chin_rest", "look_away"],
                "expressions": ["thoughtful"],
                "duration": 2000,
            },
        }
        
        return reactions.get(reaction_type, reactions["thinking"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize behavior state."""
        return {
            "idle_behavior_count": len(self.idle_behaviors),
            "behavior_interval": self.behavior_interval,
        }


class VoicePersonality:
    """Manages speech patterns and voice synthesis parameters."""
    
    def __init__(self):
        """Initialize voice personality."""
        self.speech_rate = 1.0  # 0.5-2.0: slow to fast
        self.voice_pitch = 1.0  # 0.8-1.2: lower to higher
        self.voice_warmth = 0.7  # 0-1: cold to warm tone
        self.accent = "neutral"
        
        # Speech patterns
        self.filler_words = ["um", "uh", "well", "actually"]
        self.use_filler_probability = 0.1
        
        self.punctuation_pattern = "varied"  # "varied", "formal", "casual"
    
    def adjust_for_emotion(self, emotion: EmotionState):
        """Adjust voice parameters based on emotion."""
        adjustments = {
            EmotionState.EXCITED: {"speech_rate": 1.3, "pitch": 1.1},
            EmotionState.THOUGHTFUL: {"speech_rate": 0.8, "pitch": 0.95},
            EmotionState.CONFUSED: {"speech_rate": 0.9, "pitch": 0.9},
            EmotionState.CONFIDENT: {"speech_rate": 1.0, "pitch": 1.05},
            EmotionState.CONCERNED: {"speech_rate": 0.85, "pitch": 0.9},
            EmotionState.HAPPY: {"speech_rate": 1.1, "pitch": 1.08},
        }
        
        if emotion in adjustments:
            adj = adjustments[emotion]
            self.speech_rate = adj.get("speech_rate", self.speech_rate)
            self.voice_pitch = adj.get("pitch", self.voice_pitch)
    
    def add_speech_patterns(self, text: str) -> str:
        """Add natural speech patterns to text."""
        # Occasionally add filler words at sentence starts
        sentences = text.split(". ")
        modified = []
        
        for sentence in sentences:
            if random.random() < self.use_filler_probability and sentence.strip():
                filler = random.choice(self.filler_words)
                sentence = f"{filler}, {sentence}"
            modified.append(sentence)
        
        result = ". ".join(modified)
        
        # Add punctuation variation
        if self.punctuation_pattern == "casual":
            if random.random() < 0.2:
                result = result.rstrip(".") + "!"
        elif self.punctuation_pattern == "varied":
            if random.random() < 0.1:
                result = result.rstrip(".") + "..."
        
        return result
    
    def get_voice_params(self) -> Dict[str, float]:
        """Get synthesis parameters."""
        return {
            "rate": self.speech_rate,
            "pitch": self.voice_pitch,
            "volume": 1.0,
            "warmth": self.voice_warmth,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize voice personality state."""
        return {
            "speech_rate": self.speech_rate,
            "voice_pitch": self.voice_pitch,
            "voice_warmth": self.voice_warmth,
            "accent": self.accent,
            "punctuation_pattern": self.punctuation_pattern,
        }


class HumanLikeAriaCore:
    """Unified core system for human-like Aria."""
    
    def __init__(self):
        """Initialize all personality systems."""
        self.personality = PersonalityEngine()
        self.memory = MemorySystem()
        self.reasoning = ReasoningEngine()
        self.behaviors = BehaviorGenerator()
        self.voice = VoicePersonality()
        
        self.session_start = time.time()
    
    def process_interaction(self, user_input: str, user_sentiment: str = "neutral",
                           topic: str = "general") -> Dict[str, Any]:
        """Process a user interaction and generate human-like response."""
        
        # Get emotional response
        emotional_response = self.personality.get_emotional_response(user_input, user_sentiment)
        
        # Adjust voice for emotion
        self.voice.adjust_for_emotion(emotional_response.primary_emotion)
        
        # Generate thinking process
        thinking = self.reasoning.generate_thinking_process(user_input)
        
        # Get next idle behavior
        idle_behavior = self.behaviors.get_next_idle_behavior()
        
        return {
            "emotional_response": emotional_response.to_dict(),
            "thinking_process": thinking,
            "voice_params": self.voice.get_voice_params(),
            "idle_behavior": idle_behavior,
            "state": self.to_dict(),
        }
    
    def add_memory_turn(self, user_msg: str, aria_response: str, 
                       emotion: EmotionState, topic: str = "general"):
        """Add conversation turn to memory."""
        self.memory.add_turn(user_msg, aria_response, emotion, topic)
    
    def get_state(self) -> Dict[str, Any]:
        """Get full current state."""
        return self.to_dict()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete state."""
        return {
            "personality": self.personality.to_dict(),
            "memory": self.memory.to_dict(),
            "reasoning": self.reasoning.to_dict(),
            "behaviors": self.behaviors.to_dict(),
            "voice": self.voice.to_dict(),
            "session_duration_seconds": time.time() - self.session_start,
        }


# Global instance
_aria_core = None


def get_aria_core() -> HumanLikeAriaCore:
    """Get or create global Aria core."""
    global _aria_core
    if _aria_core is None:
        _aria_core = HumanLikeAriaCore()
    return _aria_core


# Example usage
if __name__ == "__main__":
    aria = get_aria_core()
    
    # Simulate a user interaction
    result = aria.process_interaction(
        "I'm feeling sad today",
        user_sentiment="negative",
        topic="emotions"
    )
    
    print(json.dumps(result, indent=2, default=str))
    
    # Add to memory
    aria.add_memory_turn(
        "I'm feeling sad today",
        "I understand. It's okay to have difficult days.",
        result["emotional_response"]["primary_emotion"],
        "emotions"
    )
    
    # Show state
    print("\nAria's state:")
    print(json.dumps(aria.get_state(), indent=2, default=str))
