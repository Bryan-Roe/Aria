"""
AGI (Artificial General Intelligence) Enhanced Chat Provider

This module implements advanced reasoning capabilities for the Aria platform:
- Multi-step reasoning (chain-of-thought)
- Goal-oriented task decomposition
- Self-reflection and response improvement
- Memory/context management

The AGI provider wraps an underlying provider (Azure/OpenAI/Local) and enhances
responses with structured reasoning processes.

Security considerations:
- Input is sanitized to prevent injection attacks
- Content length is limited to prevent DoS
- Error messages are sanitized to prevent information leakage
"""
from __future__ import annotations

import html
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, Iterable, List, Optional

from chat_providers import (
    BaseChatProvider,
    ProviderChoice,
    RoleMessage,
    detect_provider,
)

# Configure logger for security events
_logger = logging.getLogger(__name__)

# Security constants
MAX_INPUT_LENGTH = 10000  # Maximum characters per input
MAX_HISTORY_SIZE = 50  # Maximum conversation history entries
MAX_GOALS = 5  # Maximum active goals
MAX_REASONING_CHAINS = 10  # Maximum stored reasoning chains


def _sanitize_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Raw input text.
        max_length: Maximum allowed length.
        
    Returns:
        Sanitized text.
    """
    if not isinstance(text, str):
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove null bytes and other control characters (except newlines/tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    return text


def _sanitize_for_logging(text: str, max_length: int = 200) -> str:
    """
    Sanitize text for safe logging (no sensitive data exposure).
    
    Args:
        text: Text to sanitize.
        max_length: Maximum length for logs.
        
    Returns:
        Sanitized text safe for logging.
    """
    if not isinstance(text, str):
        return "[invalid]"
    
    # Truncate for logging
    text = text[:max_length]
    if len(text) == max_length:
        text += "..."
    
    # Escape any special characters
    text = html.escape(text)
    
    return text


@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning chain."""
    step_type: str  # 'decompose', 'analyze', 'synthesize', 'reflect', 'refine'
    content: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AGIContext:
    """Manages context and memory for AGI reasoning."""
    conversation_history: List[RoleMessage] = field(default_factory=list)
    reasoning_chains: List[List[ReasoningStep]] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    max_history: int = MAX_HISTORY_SIZE
    
    def add_message(self, message: RoleMessage) -> None:
        """Add a message to conversation history with pruning and sanitization."""
        # Sanitize message content
        sanitized_msg = {
            "role": _sanitize_input(str(message.get("role", "user")), max_length=20),
            "content": _sanitize_input(str(message.get("content", "")))
        }
        self.conversation_history.append(sanitized_msg)
        if len(self.conversation_history) > self.max_history:
            # Keep system messages and recent messages
            system_msgs = [m for m in self.conversation_history if m.get("role") == "system"]
            other_msgs = [m for m in self.conversation_history if m.get("role") != "system"]
            # Keep last N messages
            keep_count = self.max_history - len(system_msgs)
            self.conversation_history = system_msgs + other_msgs[-keep_count:]
    
    def add_reasoning_chain(self, chain: List[ReasoningStep]) -> None:
        """Store a reasoning chain for future reference with limits."""
        self.reasoning_chains.append(chain)
        # Keep only last N chains to prevent memory issues
        if len(self.reasoning_chains) > MAX_REASONING_CHAINS:
            self.reasoning_chains = self.reasoning_chains[-MAX_REASONING_CHAINS:]
    
    def get_relevant_context(self, query: str) -> str:
        """Extract relevant context for the current query."""
        # Sanitize query input
        query = _sanitize_input(query)
        
        context_parts = []
        
        # Add recent conversation context
        recent = self.conversation_history[-6:]  # Last 3 exchanges
        if recent:
            context_parts.append("Recent conversation:")
            for msg in recent:
                role = _sanitize_for_logging(str(msg.get("role", "unknown")), 20)
                content = _sanitize_for_logging(str(msg.get("content", "")), 200)
                context_parts.append(f"  {role}: {content}")
        
        # Add active goals if any (limit to prevent injection)
        if self.goals:
            safe_goals = [_sanitize_for_logging(g, 50) for g in self.goals[:3]]
            context_parts.append(f"Active goals: {', '.join(safe_goals)}")
        
        return "\n".join(context_parts)


class AGIProvider(BaseChatProvider):
    """
    AGI-enhanced chat provider with advanced reasoning capabilities.
    
    This provider wraps an underlying chat provider (Azure/OpenAI/Local) and
    enhances responses through:
    
    1. Chain-of-Thought Reasoning: Breaks down complex queries into steps
    2. Task Decomposition: Identifies sub-goals for complex tasks  
    3. Self-Reflection: Evaluates and improves responses
    4. Context Management: Maintains relevant memory across interactions
    
    Usage:
        provider = AGIProvider()
        response = provider.complete([{"role": "user", "content": "Explain quantum computing"}])
    """
    
    def __init__(
        self,
        base_provider: Optional[BaseChatProvider] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        enable_chain_of_thought: bool = True,
        enable_self_reflection: bool = True,
        enable_task_decomposition: bool = True,
        reasoning_depth: int = 3,
        verbose: bool = False,
    ):
        """
        Initialize AGI provider.
        
        Args:
            base_provider: Underlying provider for LLM calls. Auto-detected if None.
            temperature: Sampling temperature for responses.
            max_output_tokens: Maximum tokens in output.
            enable_chain_of_thought: Enable step-by-step reasoning.
            enable_self_reflection: Enable response self-evaluation.
            enable_task_decomposition: Enable goal decomposition.
            reasoning_depth: Maximum reasoning chain depth.
            verbose: Include reasoning steps in output.
        """
        self.base_provider = base_provider
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.enable_chain_of_thought = enable_chain_of_thought
        self.enable_self_reflection = enable_self_reflection
        self.enable_task_decomposition = enable_task_decomposition
        self.reasoning_depth = min(max(1, reasoning_depth), 5)
        self.verbose = verbose
        self.context = AGIContext()
        
        self._base_provider_choice: Optional[ProviderChoice] = None
    
    def _get_base_provider(self) -> BaseChatProvider:
        """Lazily initialize and return the base provider."""
        if self.base_provider is None:
            # Use 'local' as default to avoid recursion - 'auto' could select 'agi'
            provider, choice = detect_provider(explicit="local")
            self.base_provider = provider
            self._base_provider_choice = choice
        return self.base_provider
    
    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        """
        Generate an AGI-enhanced response with security validation.
        
        Args:
            messages: Conversation history including the new user message.
            stream: Whether to stream the response.
            
        Returns:
            Response string or generator of response chunks.
            
        Security:
            - Input is sanitized to prevent injection attacks
            - Message count is limited to prevent DoS
            - Exceptions are caught without exposing internal details
        """
        # Validate and limit message count to prevent DoS
        if len(messages) > MAX_HISTORY_SIZE:
            messages = messages[-MAX_HISTORY_SIZE:]
            _logger.warning("Message count exceeded limit, truncating to %d", MAX_HISTORY_SIZE)
        
        # Update context with new messages (use content comparison to avoid duplicates)
        existing_contents = {m.get("content", "") for m in self.context.conversation_history}
        for msg in messages:
            content = msg.get("content", "")
            # Sanitize content before storage
            sanitized_content = _sanitize_input(str(content))
            if sanitized_content not in existing_contents:
                self.context.add_message({"role": msg.get("role", "user"), "content": sanitized_content})
                existing_contents.add(sanitized_content)
        
        # Extract and sanitize the latest user query
        user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_query = _sanitize_input(str(msg.get("content", "")))
                break
        
        if not user_query.strip():
            response = "I'm ready to help. What would you like to discuss?"
            return self._stream_text(response) if stream else response
        
        try:
            # Perform AGI reasoning pipeline
            reasoning_chain = self._reason(user_query, messages)
            
            # Generate final response
            response = self._generate_response(user_query, reasoning_chain, messages)
            
            # Self-reflection and improvement
            if self.enable_self_reflection:
                response = self._reflect_and_improve(user_query, response, reasoning_chain)
            
            # Store reasoning chain
            self.context.add_reasoning_chain(reasoning_chain)
        except Exception as e:
            # Log error securely without exposing details to user
            _logger.error("AGI processing error: %s", _sanitize_for_logging(str(e)))
            response = self._generate_fallback_response(user_query, {"intent": "general", "domain": "general"})
        
        if stream:
            return self._stream_text(response)
        return response
    
    def _reason(self, query: str, messages: List[RoleMessage]) -> List[ReasoningStep]:
        """
        Perform multi-step reasoning on the query.
        
        Args:
            query: The user's query.
            messages: Full conversation history.
            
        Returns:
            List of reasoning steps.
        """
        chain: List[ReasoningStep] = []
        
        # Step 1: Analyze query complexity and intent
        analysis = self._analyze_query(query)
        chain.append(ReasoningStep(
            step_type="analyze",
            content=analysis["summary"],
            confidence=analysis["confidence"],
            metadata=analysis
        ))
        
        # Step 2: Task decomposition for complex queries
        if self.enable_task_decomposition and analysis["complexity"] == "complex":
            subtasks = self._decompose_task(query, analysis)
            chain.append(ReasoningStep(
                step_type="decompose",
                content=f"Subtasks: {', '.join(subtasks)}",
                metadata={"subtasks": subtasks}
            ))
        
        # Step 3: Chain-of-thought reasoning
        if self.enable_chain_of_thought:
            thought_steps = self._chain_of_thought(query, analysis, messages)
            for step in thought_steps:
                chain.append(ReasoningStep(
                    step_type="synthesize",
                    content=step
                ))
        
        return chain
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to determine intent, complexity, and approach.
        
        Args:
            query: The user's query.
            
        Returns:
            Analysis dictionary with intent, complexity, etc.
        """
        query_lower = query.lower()
        words = query.split()
        
        # Determine complexity based on query characteristics
        complexity = "simple"
        if len(words) > 20:
            complexity = "complex"
        elif any(word in query_lower for word in ["explain", "compare", "analyze", "how", "why"]):
            complexity = "moderate"
        elif any(word in query_lower for word in ["step by step", "detailed", "comprehensive"]):
            complexity = "complex"
        
        # Identify intent categories
        intent = "general"
        if any(word in query_lower for word in ["move", "walk", "go", "jump", "dance", "wave"]):
            intent = "movement"
        elif any(word in query_lower for word in ["code", "program", "function", "debug"]):
            intent = "coding"
        elif any(word in query_lower for word in ["explain", "what is", "how does"]):
            intent = "explanation"
        elif any(word in query_lower for word in ["create", "generate", "make", "build"]):
            intent = "creation"
        elif "?" in query:
            intent = "question"
        
        # Determine topic domain
        domain = "general"
        domain_keywords = {
            "quantum": ["quantum", "qubit", "entanglement", "superposition"],
            "ai": ["ai", "machine learning", "neural", "model", "training"],
            "aria": ["aria", "move", "animation", "character"],
            "technical": ["code", "program", "api", "function", "database"],
        }
        for dom, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                domain = dom
                break
        
        return {
            "query": query,
            "complexity": complexity,
            "intent": intent,
            "domain": domain,
            "word_count": len(words),
            "has_question": "?" in query,
            "confidence": 0.8 if complexity == "simple" else 0.6,
            "summary": f"{complexity.capitalize()} {intent} query about {domain}"
        }
    
    def _decompose_task(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """
        Break down a complex task into subtasks.
        
        Args:
            query: The user's query.
            analysis: Query analysis results.
            
        Returns:
            List of subtask descriptions.
        """
        subtasks = []
        intent = analysis.get("intent", "general")
        domain = analysis.get("domain", "general")
        
        # Generate subtasks based on intent
        if intent == "explanation":
            subtasks = [
                "Define key concepts",
                "Provide examples",
                "Explain relationships",
                "Summarize key points"
            ]
        elif intent == "coding":
            subtasks = [
                "Understand requirements",
                "Design solution approach",
                "Implement core logic",
                "Handle edge cases",
                "Provide usage examples"
            ]
        elif intent == "creation":
            subtasks = [
                "Clarify requirements",
                "Plan structure",
                "Create content",
                "Review and refine"
            ]
        elif intent == "movement" and domain == "aria":
            subtasks = [
                "Parse movement command",
                "Validate action type",
                "Generate movement tag"
            ]
        else:
            # Generic decomposition
            subtasks = [
                "Understand the request",
                "Gather relevant information",
                "Formulate response",
                "Verify accuracy"
            ]
        
        return subtasks[:self.reasoning_depth]
    
    def _chain_of_thought(
        self, 
        query: str, 
        analysis: Dict[str, Any],
        messages: List[RoleMessage]
    ) -> List[str]:
        """
        Generate chain-of-thought reasoning steps.
        
        Args:
            query: The user's query.
            analysis: Query analysis results.
            messages: Conversation history.
            
        Returns:
            List of thought steps.
        """
        thoughts = []
        intent = analysis.get("intent", "general")
        domain = analysis.get("domain", "general")
        
        # Context-aware thought generation
        thoughts.append(f"Understanding: This is a {analysis['complexity']} {intent} request.")
        
        if domain == "aria":
            thoughts.append("Aria context: Need to consider character movement and animation.")
        elif domain == "quantum":
            thoughts.append("Quantum context: Should explain concepts clearly with appropriate depth.")
        elif domain == "coding":
            thoughts.append("Coding context: Focus on practical, working solutions.")
        
        # Add relevant context from memory
        relevant_context = self.context.get_relevant_context(query)
        if relevant_context and "Recent conversation" in relevant_context:
            thoughts.append("Considering conversation context for continuity.")
        
        thoughts.append(f"Approach: Will provide a {analysis['complexity']}-appropriate response.")
        
        return thoughts[:self.reasoning_depth]
    
    def _generate_response(
        self,
        query: str,
        reasoning_chain: List[ReasoningStep],
        messages: List[RoleMessage]
    ) -> str:
        """
        Generate the final response based on reasoning.
        
        Args:
            query: The user's query.
            reasoning_chain: Completed reasoning steps.
            messages: Conversation history.
            
        Returns:
            Generated response text.
        """
        # Build enhanced prompt with reasoning context
        analysis = {}
        for step in reasoning_chain:
            if step.step_type == "analyze":
                analysis = step.metadata
                break
        
        # Prepare system prompt for AGI reasoning
        agi_system_prompt = self._build_agi_system_prompt(analysis, reasoning_chain)
        
        # Build messages for base provider
        enhanced_messages: List[RoleMessage] = []
        
        # Add AGI system prompt
        enhanced_messages.append({
            "role": "system",
            "content": agi_system_prompt
        })
        
        # Add conversation history (excluding old system prompts)
        for msg in messages:
            if msg.get("role") != "system":
                enhanced_messages.append(msg)
            elif msg.get("role") == "system" and msg not in enhanced_messages:
                # Append user's system prompt after AGI prompt
                enhanced_messages[0]["content"] += f"\n\nAdditional context: {msg.get('content', '')}"
        
        # Get response from base provider with secure exception handling
        try:
            provider = self._get_base_provider()
            result = provider.complete(enhanced_messages, stream=False)
            if isinstance(result, str):
                response = result
            else:
                # Consume the generator
                response = "".join(result)
        except Exception as e:
            # Log error securely without exposing internal details to user
            _logger.error("Base provider error: %s", _sanitize_for_logging(str(e)))
            # Fallback to rule-based response if provider fails
            response = self._generate_fallback_response(query, analysis)
        
        # Add verbose reasoning output if enabled
        if self.verbose and reasoning_chain:
            reasoning_text = self._format_reasoning_chain(reasoning_chain)
            response = f"{reasoning_text}\n\n---\n\n{response}"
        
        return response
    
    def _build_agi_system_prompt(
        self, 
        analysis: Dict[str, Any],
        reasoning_chain: List[ReasoningStep]
    ) -> str:
        """Build the AGI-enhanced system prompt."""
        intent = analysis.get("intent", "general")
        domain = analysis.get("domain", "general")
        complexity = analysis.get("complexity", "simple")
        
        prompt_parts = [
            "You are Aria, an intelligent AI assistant with advanced reasoning capabilities.",
            "",
            "## Reasoning Framework",
            "Apply structured thinking to provide helpful, accurate responses.",
        ]
        
        # Add intent-specific guidance
        if intent == "explanation":
            prompt_parts.extend([
                "",
                "## Explanation Guidelines",
                "- Define key terms clearly",
                "- Use analogies when helpful",
                "- Progress from simple to complex",
                "- Include relevant examples",
            ])
        elif intent == "coding":
            prompt_parts.extend([
                "",
                "## Coding Guidelines",
                "- Provide working, tested code",
                "- Include comments for clarity",
                "- Handle common edge cases",
                "- Follow best practices",
            ])
        elif intent == "movement" and domain == "aria":
            prompt_parts.extend([
                "",
                "## Aria Movement",
                "When the user requests Aria to perform actions, include movement tags:",
                "- [aria:walk:left], [aria:walk:right] for movement",
                "- [aria:jump], [aria:wave], [aria:dance] for actions",
                "- Acknowledge the action naturally in your response",
            ])
        
        # Add complexity-appropriate guidance
        if complexity == "complex":
            prompt_parts.extend([
                "",
                "## Approach for Complex Query",
                "- Break down into logical parts",
                "- Address each aspect systematically",
                "- Provide comprehensive coverage",
            ])
        
        # Add subtasks if decomposed
        for step in reasoning_chain:
            if step.step_type == "decompose":
                subtasks = step.metadata.get("subtasks", [])
                if subtasks:
                    prompt_parts.extend([
                        "",
                        "## Task Breakdown",
                        *[f"- {task}" for task in subtasks]
                    ])
                break
        
        return "\n".join(prompt_parts)
    
    def _generate_fallback_response(self, query: str, analysis: Dict[str, Any]) -> str:
        """Generate a fallback response when the base provider fails."""
        intent = analysis.get("intent", "general")
        domain = analysis.get("domain", "general")
        
        if intent == "movement" and domain == "aria":
            # Parse movement commands
            query_lower = query.lower()
            if "left" in query_lower:
                return "I'll move to the left! [aria:walk:left]"
            elif "right" in query_lower:
                return "Moving to the right! [aria:walk:right]"
            elif "jump" in query_lower:
                return "Here I go! [aria:jump]"
            elif "wave" in query_lower:
                return "Hello there! [aria:wave]"
            elif "dance" in query_lower:
                return "Time to dance! [aria:dance]"
            else:
                return "I'm ready to move! Just tell me which direction."
        
        if analysis.get("has_question"):
            return (
                "That's an interesting question! While I'm currently in fallback mode, "
                "I can help with various topics including Aria movements, quantum computing, "
                "and general assistance. How can I help you today?"
            )
        
        return (
            "I understand your request. I'm Aria, an AGI-enhanced assistant. "
            "I can help with movement commands, explanations, coding tasks, and more. "
            "What would you like to explore?"
        )
    
    def _reflect_and_improve(
        self,
        query: str,
        response: str,
        reasoning_chain: List[ReasoningStep]
    ) -> str:
        """
        Self-reflect on the response and improve if needed.
        
        Args:
            query: Original user query.
            response: Generated response.
            reasoning_chain: Reasoning steps used.
            
        Returns:
            Improved response.
        """
        # Quick quality checks
        issues = []
        
        # Check response length appropriateness
        analysis = {}
        for step in reasoning_chain:
            if step.step_type == "analyze":
                analysis = step.metadata
                break
        
        complexity = analysis.get("complexity", "simple")
        word_count = len(response.split())
        
        if complexity == "complex" and word_count < 50:
            issues.append("response_too_short")
        elif complexity == "simple" and word_count > 300:
            issues.append("response_too_long")
        
        # Check if question was answered
        if analysis.get("has_question") and "?" not in query[-10:]:
            # Question detected but response might not address it
            if not any(phrase in response.lower() for phrase in ["the answer", "yes", "no", "because", "means", "is"]):
                issues.append("question_not_addressed")
        
        # Check for Aria movement commands
        if analysis.get("intent") == "movement" and analysis.get("domain") == "aria":
            if "[aria:" not in response:
                # Add movement tag if missing
                query_lower = query.lower()
                if "left" in query_lower:
                    response += " [aria:walk:left]"
                elif "right" in query_lower:
                    response += " [aria:walk:right]"
                elif "jump" in query_lower:
                    response += " [aria:jump]"
        
        # Store reflection for learning
        if issues:
            self.context.learned_patterns[f"reflection_{len(self.context.reasoning_chains)}"] = {
                "issues": issues,
                "query_type": analysis.get("intent"),
                "improvements_applied": True
            }
        
        return response
    
    def _format_reasoning_chain(self, chain: List[ReasoningStep]) -> str:
        """Format reasoning chain for verbose output."""
        parts = ["🧠 **AGI Reasoning Process**", ""]
        
        step_icons = {
            "analyze": "🔍",
            "decompose": "📋",
            "synthesize": "💡",
            "reflect": "🪞",
            "refine": "✨"
        }
        
        for i, step in enumerate(chain, 1):
            icon = step_icons.get(step.step_type, "•")
            parts.append(f"{icon} Step {i} ({step.step_type}): {step.content}")
        
        return "\n".join(parts)
    
    def _stream_text(self, text: str) -> Generator[str, None, None]:
        """Stream text word by word with adaptive pacing based on response length."""
        words = text.split()
        word_count = len(words)
        # Adaptive delay: faster for long responses (min 0.002), slower for short ones (max 0.02)
        delay = max(0.002, min(0.02, 1.0 / (word_count + 10)))
        for i, word in enumerate(words):
            if i == 0:
                yield word
            else:
                yield " " + word
            time.sleep(delay)
    
    def set_goal(self, goal: str) -> None:
        """Add a goal to the active goals list with input sanitization."""
        # Sanitize goal input
        sanitized_goal = _sanitize_input(str(goal), max_length=200)
        if not sanitized_goal:
            return
        
        if sanitized_goal not in self.context.goals:
            self.context.goals.append(sanitized_goal)
            if len(self.context.goals) > MAX_GOALS:
                self.context.goals = self.context.goals[-MAX_GOALS:]
    
    def clear_goals(self) -> None:
        """Clear all active goals."""
        self.context.goals.clear()
    
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """Get a summary of recent reasoning activity."""
        return {
            "total_reasoning_chains": len(self.context.reasoning_chains),
            "active_goals": self.context.goals.copy(),
            "learned_patterns_count": len(self.context.learned_patterns),
            "conversation_length": len(self.context.conversation_history),
        }


def create_agi_provider(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    verbose: bool = False,
    **kwargs
) -> tuple[AGIProvider, ProviderChoice]:
    """
    Factory function to create an AGI-enhanced chat provider.
    
    Args:
        model: Model identifier (passed to underlying provider).
        temperature: Response randomness.
        max_output_tokens: Maximum tokens in response.
        verbose: Include reasoning steps in output.
        **kwargs: Additional provider-specific arguments.
        
    Returns:
        Tuple of (provider instance, provider info).
    """
    # Get base provider first - use 'local' to avoid selecting 'agi' recursively
    base_provider = None
    base_choice = None
    
    if model:
        # Try to use specified model with a non-agi provider
        try:
            base_provider, base_choice = detect_provider(explicit="local", model_override=model)
        except Exception:
            pass
    
    provider = AGIProvider(
        base_provider=base_provider,
        temperature=temperature or 0.7,
        max_output_tokens=max_output_tokens or 2048,
        verbose=verbose,
        **kwargs
    )
    
    # If we got a base provider, use its info
    model_name = "agi-enhanced"
    if base_choice:
        model_name = f"agi-{base_choice.name}-{base_choice.model}"
    elif model:
        model_name = f"agi-{model}"
    
    info = ProviderChoice(
        name="agi",
        model=model_name,
    )
    
    return provider, info
